#!/usr/bin/env bash
# 一键启动入口：双击桌面图标，或在应用菜单里点“日历 ToDo”即可。
# 如果双击没有反应，检查文件权限后重新运行：chmod +x run.sh

cd "$(dirname "$0")" || exit 1

if [ ! -x ".venv/bin/python" ]; then
    if command -v zenity >/dev/null 2>&1; then
        zenity --error --title="日历 ToDo" --text="虚拟环境不存在，请先安装依赖：\npython3 -m venv .venv\n.venv/bin/pip install -r requirements.txt"
    else
        echo "缺少虚拟环境 .venv，请先安装依赖。" >&2
    fi
    exit 1
fi

exec .venv/bin/python main.py
