# 日历 + ToDo List（Do-and-Done）

一个运行在 Ubuntu 桌面上的日历与待办管理软件，纯 Python + PySide6 编写。
界面采用「手绘涂鸦」风格：点阵纸背景、便签卡片、抖动铅笔线、硬边投影，
像一页被认真整理过的笔记本。

## 功能

- **悬浮便签按钮**：屏幕角落一张手绘小便签，可拖动、位置自动记忆；
- **两种日历形态**：点击便签展开滚动日历条（支持滚轮、拖动、无限滚动），再点“展开月历”变成完整月历；
- **ToDo List 模式**：按天添加待办，支持跨多日的大目标；任务页可勾选完成、删除、添加；
- **完成率染色**：蓝 100% / 绿 60%～100% / 黄 20%～60% / 红 0%～20%，
  只给“今天及过去且有任务”的日期染色，且只统计**结束日期在当天**的任务；
  颜色在滚动条、月历、纪念日模式中全部同步；
- **纪念日模式**：标题栏一键切换；展示内置节假日（元旦、春节、清明、端午、中秋等）
  和自定义纪念日；纪念日支持公历/农历、每年重复；
- **系统托盘**：常驻托盘，可显示/隐藏悬浮按钮、退出程序。

## 运行方法

```bash
cd /Data/Do_Done
source .venv/bin/activate        # 第一次需要先创建虚拟环境（见下）
python main.py
```

**一键启动（推荐）**：安装一次后，不需要打开终端——

- 在系统应用菜单里搜索“日历 ToDo”，点击即可启动；
- 或者双击桌面上的“日历 ToDo”图标（首次双击时如提示“信任”，选择允许）。

**开机自启动**：登录桌面后会自动启动悬浮按钮（延迟 3 秒）。
已安装到 `~/.config/autostart/`；想关闭时，在“启动应用程序”设置里关掉该项，
或删除 `Do-and-Done-autostart.desktop` 即可。

入口文件说明：`Do-and-Done.desktop` 是菜单/桌面入口，`run.sh` 是真正的启动脚本
（自动进入项目目录并使用虚拟环境）。如果移动了项目目录，需要重新安装入口：

```bash
chmod +x run.sh
cp Do-and-Done.desktop ~/.local/share/applications/
cp Do-and-Done-autostart.desktop ~/.config/autostart/
update-desktop-database ~/.local/share/applications
```

第一次运行前初始化环境：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

运行自动化测试（无需图形界面）：

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python scripts/smoke_test.py
```

## 目录结构

| 路径 | 作用 |
| --- | --- |
| main.py | 程序入口，只负责启动 |
| calendar_todo/app.py | 应用组装：悬浮按钮、面板、托盘、数据库 |
| calendar_todo/ui/ | 界面层（悬浮按钮、面板、月历、滚动条、任务页、纪念日页、主题） |
| calendar_todo/logic/ | 逻辑层（日期计算、完成率染色、节假日） |
| calendar_todo/data/ | 数据层（SQLite 读写） |
| docs/ | 需求文档、开发计划、UI 风格说明 |
| scripts/smoke_test.py | 冒烟测试 |
| requirements.txt | 依赖清单（PySide6、zhdate） |

## 技术栈

- Python 3.10+（开发环境为 3.13）
- PySide6（Qt 6，官方 Python 绑定）
- SQLite（Python 标准库，单文件数据库，位于 `~/.local/share/CalendarTodo/`）
- zhdate（农历换算）

## 已知限制

- 法定节假日的“调休上班日”需要每年的官方数据，暂未包含；
- 闰月农历日期暂不支持（zhdate 的限制）；
- 自定义纪念日目前都是每年重复，不支持一次性事件；
- 暂无提醒/通知功能；
- 界面交互为即时样式切换，300–500ms 弹性动画尚未实现。

## 开发路线

- [x] 阶段 0：环境搭建与项目骨架
- [x] 阶段 1：窗口形态（悬浮按钮、展开面板、系统托盘）
- [x] 阶段 2：日历核心（月历 + 无限滚动条）
- [x] 阶段 3：ToDo 与 SQLite 数据层
- [x] 阶段 4：完成率统计与颜色同步
- [x] 阶段 5：纪念日模式（农历、节假日）
- [x] UI 整体重设计（手绘涂鸦风格）
- [ ] 阶段 6：打磨与打包发布（设置、开机自启、AppImage、动画等）

详细计划见 [docs/开发计划.md](docs/开发计划.md)，确认过的需求见
[docs/需求文档.md](docs/需求文档.md)，界面风格见 [docs/UI风格.md](docs/UI风格.md)。
