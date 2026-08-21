"""程序入口：在终端运行 `.venv/bin/python main.py` 启动日历应用。"""

import sys

from calendar_todo.app import main

if __name__ == "__main__":
    sys.exit(main())
