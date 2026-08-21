"""数据层：SQLite 数据库，负责任务和每日完成状态的读写。

SQLite 把整个数据库存在一个文件里，Python 标准库自带支持，不用额外安装。
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QStandardPaths


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
            """
        )
        self._conn.commit()

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
        """某一天的完成统计：(已完成数量, 总数量)。"""
        row = self._conn.execute(
            "SELECT COUNT(*) AS total, COALESCE(SUM(done), 0) AS done "
            "FROM task_daily WHERE date = ?",
            (day.isoformat(),),
        ).fetchone()
        return row["done"], row["total"]
