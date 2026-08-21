"""数据层：SQLite 数据库，负责任务和每日完成状态的读写。

SQLite 把整个数据库存在一个文件里，Python 标准库自带支持，不用额外安装。
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QStandardPaths
from zhdate import ZhDate


def default_db_path() -> Path:
    """数据库文件的默认位置：~/.local/share/CalendarTodo/calendar.db"""
    base = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.AppDataLocation
    )
    if not base:
        base = str(Path.home() / ".local" / "share" / "CalendarTodo")
    return Path(base) / "calendar.db"


class TodoRepository:
    """任务数据库的“仓库”：所有对数据的增删改查都走这里。"""

    def __init__(self, db_path):
        self.db_path = str(db_path)
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        # 外键约束默认是关的；打开后“删除任务”才会自动级联删除它的每日记录
        self._conn.execute("PRAGMA foreign_keys = ON")
        self._create_tables()

    def close(self):
        self._conn.close()

    def _create_tables(self):
        self._conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS task_daily (
                task_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0,
                PRIMARY KEY (task_id, date),
                FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS memorials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                month INTEGER NOT NULL,
                day INTEGER NOT NULL,
                is_lunar INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            );
            """
        )
        self._conn.commit()

    # ---------- 纪念日 ----------

    def add_memorial(self, name: str, month: int, day: int, is_lunar: bool = False) -> int:
        """添加纪念日。纪念日每年重复：is_lunar=True 表示按农历。"""
        cursor = self._conn.execute(
            "INSERT INTO memorials (name, month, day, is_lunar) VALUES (?, ?, ?, ?)",
            (name, month, day, 1 if is_lunar else 0),
        )
        self._conn.commit()
        return cursor.lastrowid

    def delete_memorial(self, memorial_id: int):
        self._conn.execute("DELETE FROM memorials WHERE id = ?", (memorial_id,))
        self._conn.commit()

    def memorials_on(self, day: date) -> list[dict]:
        """某一天会遇到的纪念日（农历纪念日会换算到对应公历日）。"""
        return self.memorials_for_range(day, day).get(day, [])

    def memorial_rows_on(self, day: date) -> list[dict]:
        """某一天会遇到的纪念日明细（含 id，供展示和删除使用）。"""
        rows = self._conn.execute(
            "SELECT id, name, month, day, is_lunar FROM memorials ORDER BY id"
        ).fetchall()
        result = []
        for row in rows:
            if self._memorial_matches(dict(row), day):
                result.append(dict(row))
        return result

    def memorials_for_range(self, start: date, end: date) -> dict[date, list[str]]:
        """一段日期范围内每天会遇到的纪念日：{日期: [名称, ...]}。"""
        rows = self._conn.execute(
            "SELECT id, name, month, day, is_lunar FROM memorials ORDER BY id"
        ).fetchall()
        result: dict[date, list[str]] = {}
        day = start
        while day <= end:
            for row in rows:
                if self._memorial_matches(dict(row), day):
                    result.setdefault(day, []).append(row["name"])
            day += timedelta(days=1)
        return result

    @staticmethod
    def _memorial_matches(memorial: dict, day: date) -> bool:
        """判断某个纪念日是否落在 day 这一天。"""
        if memorial["is_lunar"]:
            # 农历纪念日：把当年这个农历日期换算成公历再比较
            try:
                solar = (
                    ZhDate(day.year, memorial["month"], memorial["day"])
                    .to_datetime()
                    .date()
                )
            except (ValueError, TypeError):
                return False
            return solar == day
        return memorial["month"] == day.month and memorial["day"] == day.day

    def add_task(self, title: str, start_date: date, end_date: date) -> int:
        """添加任务。跨几天，就在 task_daily 里为每一天插一行。"""
        cursor = self._conn.execute(
            "INSERT INTO tasks (title, start_date, end_date) VALUES (?, ?, ?)",
            (title, start_date.isoformat(), end_date.isoformat()),
        )
        task_id = cursor.lastrowid
        day = start_date
        while day <= end_date:
            self._conn.execute(
                "INSERT INTO task_daily (task_id, date, done) VALUES (?, ?, 0)",
                (task_id, day.isoformat()),
            )
            day += timedelta(days=1)
        self._conn.commit()
        return task_id

    def tasks_on(self, day: date) -> list[dict]:
        """某一天要做的所有任务（跨日任务会在它覆盖的每一天都出现）。"""
        rows = self._conn.execute(
            """
            SELECT t.id, t.title, t.start_date, t.end_date, d.done
            FROM tasks t
            JOIN task_daily d ON t.id = d.task_id
            WHERE d.date = ?
            ORDER BY d.done, t.id
            """,
            (day.isoformat(),),
        ).fetchall()
        return [dict(row) for row in rows]

    def set_done(self, task_id: int, day: date, done: bool):
        """把某一天里某个任务的完成状态改成 done。"""
        self._conn.execute(
            "UPDATE task_daily SET done = ? WHERE task_id = ? AND date = ?",
            (1 if done else 0, task_id, day.isoformat()),
        )
        self._conn.commit()

    def delete_task(self, task_id: int):
        """删除整个任务（关联的每日记录会被外键级联删除）。"""
        self._conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()

    def stats_for_date(self, day: date) -> tuple[int, int]:
        """某一天“到期”的任务完成统计：(已完成数量, 总数量)。

        只统计结束日期就是这一天的任务：跨多日任务只算它的最后一天，
        中间的天数只是展示进度，不影响当天的完成率。
        """
        row = self._conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(d.done), 0) AS done "
            "FROM task_daily d "
            "JOIN tasks t ON d.task_id = t.id "
            "WHERE d.date = ? AND t.end_date = d.date",
            (day.isoformat(),),
        ).fetchone()
        return row["done"], row["total"]

    def stats_for_range(self, start: date, end: date) -> dict[date, tuple[int, int]]:
        """一段日期范围内每天“到期”任务的完成统计：{日期: (已完成, 总数量)}。

        一次查完整个月/整条滚动条的颜色数据，避免每个格子单独查一次数据库。
        """
        rows = self._conn.execute(
            "SELECT d.date, COUNT(*) AS total, COALESCE(SUM(d.done), 0) AS done "
            "FROM task_daily d "
            "JOIN tasks t ON d.task_id = t.id "
            "WHERE d.date BETWEEN ? AND ? AND t.end_date = d.date "
            "GROUP BY d.date",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return {
            date.fromisoformat(row["date"]): (row["done"], row["total"])
            for row in rows
        }
