# ⚡ ECUST 宿舍电量监控

华东理工大学宿舍电量监控工具。

[![Python Version](https://img.shields.io/badge/python-3.14-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## ✨ 特性

- 📊 自动数据采集并存储 CSV
- 🔔 低电量告警（邮件/Server酱微信）
- 📈 交互式 HTML 报告（Plotly）
- 🚀 多种部署（GitHub Actions/cron/本地）

## 📦 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/DOHEX/ecust-dorm-electricity-monitor.git
cd ecust-dorm-electricity-monitor

# 2. 安装 uv（如未安装）
# Linux/macOS: curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 3. 同步依赖（自动安装 Python 3.14）
uv sync

# 4. 初始化配置
uv run emon init

# 5. 开始使用
uv run emon fetch
```

## ⚙️ 配置

配置优先级：**环境变量 > .env.local > .env > config.toml**

### 方式一：交互式（推荐）

```bash
uv run emon init
```

### 方式二：手动配置

创建 `.env.local`（本地开发）或 `.env`（生产环境）：

```bash
# 必填：ECUST API 参数（F12 开发者工具抓包获取）
API__SYSID=your_sysid
API__ROOMID=your_roomid
API__AREAID=your_areaid
API__BUILDID=your_buildid

# 可选：告警配置
APP__ALERT_THRESHOLD_KWH=10.0
NOTIFICATION__CHANNELS=["email"]  # 或 ["serverchan"] 或 ["email","serverchan"]

# 可选：邮件推送
NOTIFICATION__SMTP_HOST=smtp.gmail.com
NOTIFICATION__SMTP_PORT=587
NOTIFICATION__SMTP_STARTTLS=true
NOTIFICATION__SMTP_USER=your_email@gmail.com
NOTIFICATION__SMTP_PASSWORD=your_app_password
NOTIFICATION__RECIPIENTS=["recipient@example.com"]

# 可选：Server酱微信推送（https://sct.ftqq.com/ 获取 SendKey）
NOTIFICATION__SERVERCHAN_SENDKEY=your_sendkey
```

### GitHub Actions 配置

在仓库 Settings → Secrets and variables → Actions 添加：
- `API__SYSID`、`API__ROOMID`、`API__AREAID`、`API__BUILDID`
- 可选：`NOTIFICATION__SMTP_PASSWORD`、`NOTIFICATION__SERVERCHAN_SENDKEY`

非敏感配置直接在 workflow 文件中设置 `env` 变量。

## 📖 命令

```bash
uv run emon fetch                      # 获取电量
uv run emon fetch --verbose            # 显示详细信息
uv run emon fetch --no-save            # 不保存到 CSV

uv run emon alert                      # 检查并发送告警
uv run emon alert --threshold 20       # 自定义阈值

uv run emon report                     # 生成报告（最近 7 天）
uv run emon report --days 30           # 最近 30 天
uv run emon report --no-open           # 不打开浏览器

uv run emon schedule                   # 定时监控（前台）
uv run emon schedule --interval 1800   # 每 30 分钟

uv run emon info                       # 查看配置和统计
uv run emon init --force               # 重新配置
```

## 🚀 部署

### GitHub Actions（推荐）

1. Fork 仓库
2. 添加 Secrets（见上方配置）
3. 自动运行：每小时采集，低电量告警

### 服务器部署

**systemd 服务：**

```ini
# /etc/systemd/system/emon-monitor.service
[Unit]
Description=ECUST Electricity Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/usr/local/bin/uv run emon schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable emon-monitor
sudo systemctl start emon-monitor
```

**cron 任务：**

```bash
0 * * * * cd /path/to/project && uv run emon fetch
```

**后台运行：**

```bash
# Linux/macOS
nohup uv run emon schedule > scheduler.log 2>&1 &

# Windows
start /B uv run emon schedule
```

## 🏗️ 架构

```
src/ecust_electricity_monitor/
├── analytics/          # 数据分析模块
│   ├── power_analyzer.py    # PowerAnalyzer 类（OOP 设计）
│   ├── validators.py         # 数据验证
│   └── datetime_utils.py     # 时间工具
├── commands/           # CLI 命令模块（高度模块化）
│   ├── fetch.py        # 获取电量
│   ├── alert.py        # 告警检查
│   ├── report.py       # 报告生成
│   ├── schedule.py     # 定时任务
│   ├── info.py         # 信息查看
│   └── init.py         # 初始化配置
├── storage/            # 存储层（Repository Pattern）
│   ├── base.py         # ElectricityRepository 抽象接口
│   ├── csv_repository.py    # CSV 实现
│   └── __init__.py     # 工厂函数
├── notifiers/          # 通知系统
│   ├── base.py         # 抽象基类
│   ├── email.py        # 邮件推送
│   ├── serverchan.py   # Server酱推送
│   └── manager.py      # 通知管理器
├── cli.py              # CLI 入口（54 行，高度精简）
├── client.py           # API 客户端
├── config.py           # 配置管理（Pydantic）
├── models.py           # 数据模型
├── reporter.py         # HTML 报告生成器
├── scheduler.py        # 任务调度器
├── health.py           # 健康监控
└── logger.py           # 日志配置

data/
├── electricity.csv     # 电量数据
└── logs/              # 日志文件

output/                # 报告输出目录
tests/                 # 单元测试（100% 通过）
```

**设计亮点：**
- SOLID 原则，Repository Pattern
- 完整类型注解（Python 3.10+）
- 高度模块化（CLI 54 行主文件）
- pytest 测试覆盖

## 🔧 开发

```bash
# 安装所有依赖（包括开发依赖）
uv sync --all-extras

# 添加依赖
uv add requests
uv add --dev pytest-asyncio

# 测试
uv run pytest
uv run pytest --cov

# 代码检查
uv run ruff check src/
uv run ruff check --fix src/
uv run ruff format src/
```

## 📚 常见问题

**Q: 如何获取 API 参数？**  
A: 浏览器 F12 → Network → 访问电费查询页面 → 找到 `eleresult` 请求 → 提取 URL 参数

**Q: Gmail 应用密码在哪生成？**  
A: https://myaccount.google.com/apppasswords

**Q: QQ 邮箱授权码？**  
A: QQ 邮箱设置 → 账户 → POP3/SMTP 服务 → 生成授权码

**Q: Server酱免费吗？**  
A: 免费版每天 5 条消息，访问 https://sct.ftqq.com/

## 🤝 贡献

欢迎 Issue 和 PR！

## 📄 许可证

MIT License

---

<div align="center">
Made with ❤️ for ECUST students
</div>
