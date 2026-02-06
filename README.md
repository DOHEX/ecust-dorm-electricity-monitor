# ⚡ ECUST 宿舍电量监控系统

一个现代化的 Python 电量监控工具，专为华东理工大学（ECUST）宿舍设计。支持自动数据采集、智能告警、可视化报告和多种部署方式。

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

## ✨ 特性

- 📊 **自动数据采集** - 定时从 ECUST API 获取电量并存储到 CSV
- 🔔 **智能告警系统** - 支持邮件/Server酱微信推送，趋势分析，剩余天数预测
- 📈 **可视化报告** - 基于 Plotly 的交互式 HTML 报告
- 🛠️ **现代化 CLI** - Typer + Rich 提供友好的命令行界面
- 🔧 **灵活配置** - 支持 `.env` 文件和环境变量
- 🚀 **多种部署** - GitHub Actions（免费）、服务器 cron、本地运行
- 🧪 **高质量代码** - 遵循 SOLID 原则，完整类型注解，100% 测试通过

## 📦 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/DOHEX/ecust-dorm-electricity-monitor.git
cd ecust-dorm-electricity-monitor

# 安装（推荐使用 uv）
pip install uv
uv pip install -e .

# 验证安装
emon --version
```

### 配置

**推荐配置方式：config.toml + .env**

项目支持灵活的配置方式，配置优先级：**环境变量 > .env > config.toml > 代码默认值**

#### 方式一：交互式配置（推荐新手）

```bash
emon init
```

#### 方式二：手动配置（推荐）

**步骤 1：创建 config.toml（应用配置）**

```bash
cp config.toml.example config.toml
```

编辑 `config.toml`，调整非敏感配置：

```toml
[app]
alert_threshold = 10.0  # 告警阈值（度）
check_interval_seconds = 3600  # 检查间隔（秒）

[notification]
methods = "email,serverchan"  # 推送方式
```

**步骤 2：创建 .env（敏感信息）**

```bash
cp .env.example .env
```

编辑 `.env`，填写必需的敏感信息：

```bash
# 必填：ECUST API 参数
CLIENT_SYSID=your_sysid
CLIENT_ROOMID=your_roomid
CLIENT_AREAID=your_areaid
CLIENT_BUILDID=your_buildid

# 可选：邮件密码
NOTIFICATION_SMTP_PASSWORD=your_app_password

# 可选：Server酱 SendKey
NOTIFICATION_SERVERCHAN_SENDKEY=your_sendkey
```

#### GitHub Actions 用户特别提示

**无需 config.toml 和 .env！** 直接在仓库设置 Secrets：

1. Settings → Secrets and variables → Actions
2. 添加 Secrets（会作为环境变量）：
   - `CLIENT_SYSID`
   - `CLIENT_ROOMID`
   - `CLIENT_AREAID`
   - `CLIENT_BUILDID`
   - `NOTIFICATION_SMTP_PASSWORD`（可选）
   - `NOTIFICATION_SERVERCHAN_SENDKEY`（可选）
3. 非敏感配置可直接在工作流中设置：
   ```yaml
   env:
     APP_ALERT_THRESHOLD: 10.0
     NOTIFICATION_METHODS: serverchan
   ```

<details>
<summary>📝 如何获取 ECUST API 参数？</summary>

1. 浏览器访问 ECUST 电费查询页面
2. 按 F12 打开开发者工具 → Network 标签
3. 查询电量，找到请求 URL：
   ```
   https://ykt.ecust.edu.cn/epay/wxpage/wanxiao/eleresult?sysid=XXX&roomid=YYY&areaid=ZZZ&buildid=WWW
   ```
4. 提取四个参数填入配置

</details>

<details>
<summary>📱 如何配置 Server酱微信推送？</summary>

1. 访问 [Server酱官网](https://sct.ftqq.com/) 并登录
2. 获取 SendKey
3. 关注「Server酱Turbo」公众号
4. 将 SendKey 填入 `.env` 文件
5. 设置 `NOTIFICATION_METHODS=serverchan`

详见 [Server酱配置指南](docs/SERVERCHAN_GUIDE.md)

</details>

### 使用

```bash
# 获取当前电量
emon fetch

# 检查并发送告警
emon alert

# 生成分析报告（需要历史数据）
emon report

# 启动定时监控
emon schedule

# 查看配置信息
emon info
```

## 📖 命令详解

### `emon init` - 初始化配置

交互式配置向导，适合首次使用：

```bash
emon init              # 引导式配置
emon init --force      # 强制重新配置
```

### `emon fetch` - 获取电量

```bash
emon fetch             # 获取并保存
emon fetch --no-save   # 只查询不保存
emon fetch --verbose   # 显示详细信息
```

### `emon alert` - 检查告警

```bash
emon alert                  # 检查并发送告警
emon alert --threshold 20   # 自定义阈值
emon alert --verbose        # 显示详细信息
```

### `emon report` - 生成报告

```bash
emon report                      # 最近 7 天
emon report --days 30            # 最近 30 天
emon report --output report.html # 指定输出文件
emon report --no-open            # 不自动打开浏览器
```

### `emon schedule` - 定时监控

```bash
emon schedule                 # 使用配置文件中的间隔
emon schedule --interval 1800 # 每 30 分钟（秒）
```

### `emon info` - 查看状态

```bash
emon info  # 显示配置和数据统计
```

## 🚀 部署方式

### GitHub Actions（推荐）

1. Fork 本仓库
2. 在仓库设置添加 Secrets：
   - `CLIENT_SYSID`
   - `CLIENT_ROOMID`
   - `CLIENT_AREAID`
   - `CLIENT_BUILDID`
   - （可选）邮件/Server酱配置
3. 启用 Actions（Settings → Actions → General → Allow all actions）
4. 自动运行：每小时采集数据，低电量告警

### 服务器部署

**方式一：后台运行**

```bash
# Linux/macOS
nohup emon schedule > scheduler.log 2>&1 &

# Windows
start /B emon schedule
```

**方式二：systemd（推荐）**

创建服务文件 `/etc/systemd/system/emon-monitor.service`：

```ini
[Unit]
Description=ECUST Electricity Monitor
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/project
ExecStart=/path/to/venv/bin/emon schedule
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl enable emon-monitor
sudo systemctl start emon-monitor
sudo systemctl status emon-monitor
```

**方式三：cron**

```bash
crontab -e

# 每小时执行
0 * * * * cd /path/to/project && /path/to/venv/bin/emon fetch
```

## 🏗️ 项目架构

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
- ✅ **SOLID 原则** - Repository Pattern、依赖倒置、单一职责
- ✅ **模块化** - CLI 655 行 → 54 行主文件 + 9 个命令模块
- ✅ **OOP 设计** - PowerAnalyzer 类替代零散的工具函数
- ✅ **类型安全** - 100% 类型注解，Python 3.10+ 现代语法
- ✅ **可测试** - 19 个测试，覆盖核心功能

## 🔧 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest                    # 运行所有测试
pytest -v                # 详细输出
pytest --cov             # 覆盖率报告
```

### 代码质量检查

```bash
ruff check src/          # 代码检查
ruff check --fix src/    # 自动修复
ruff format src/         # 代码格式化
```

## 📚 文档

- [Server酱配置指南](docs/SERVERCHAN_GUIDE.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE)

## 🙏 致谢

- [Typer](https://typer.tiangolo.com/) - 现代化 CLI 框架
- [Loguru](https://loguru.readthedocs.io/) - 优雅的日志库
- [Pydantic](https://docs.pydantic.dev/) - 数据验证
- [Plotly](https://plotly.com/python/) - 交互式图表库

---

<div align="center">
Made with ❤️ for ECUST students
</div>


## ✨ 特性

- 📊 **自动数据采集**: 定时从 ECUST API 获取电量数据并存储到 CSV
- 🔔 **智能告警系统**: 多种推送方式（邮件/Server酱微信） + 趋势分析 + 剩余天数预测
- 📈 **可视化报告**: 基于 Plotly 的交互式 HTML 报告
- 🛠 **现代化 CLI**: Typer + Rich 提供友好的命令行界面
- 🔧 **灵活配置**: 支持环境变量、`.env` 文件和 `config.toml`
- 🚀 **多种部署**: GitHub Actions（免费）、服务器 cron、本地运行
- 🧪 **高质量代码**: 遵循 SOLID 原则，完整类型注解，pytest 测试

## 📦 安装

### 方式 1: pip 安装（推荐）

```bash
# 克隆仓库
git clone https://github.com/yourusername/ecust-dorm-electricity-monitor.git
cd ecust-dorm-electricity-monitor

# 安装（开发模式）
pip install -e .

# 或者安装发布版本
pip install .
```

### 方式 2: uv 安装（更快）

```bash
# 安装 uv (如果还没有)
pip install uv

# 安装项目
uv pip install -e .
```

### 验证安装

```bash
emon --version
```

## 🚀 快速开始

### 1. 配置

**方式一：交互式配置（推荐新手）**

运行初始化向导，跟随提示填写参数：

```bash
emon init
```

**方式二：手动创建配置文件**

创建 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写你的 ECUST 账号信息：

```bash
# 必填：ECUST API 参数
CLIENT_SYSID=your_sysid_here
CLIENT_ROOMID=your_roomid_here
CLIENT_AREAID=your_areaid_here
CLIENT_BUILDID=your_buildid_here

# 可选：推送通知
# 推送方式：email（邮件）、serverchan（Server酱）或 email,serverchan（两者都用）
NOTIFICATION_METHODS=email,serverchan

# 邮件通知配置
NOTIFICATION_SMTP_HOST=smtp.gmail.com
NOTIFICATION_SMTP_PORT=587
NOTIFICATION_SMTP_USE_TLS=true
NOTIFICATION_SMTP_USER=your_email@gmail.com
NOTIFICATION_SMTP_PASSWORD=your_app_password
NOTIFICATION_RECIPIENTS=recipient@example.com

# Server酱（微信推送）配置
# 获取 SendKey：访问 https://sct.ftqq.com/ 注册并获取
NOTIFICATION_SERVERCHAN_SENDKEY=your_sendkey_here
```

<details>
<summary>📝 如何获取 ECUST API 参数？</summary>

1. 打开浏览器开发者工具（F12）
2. 访问 ECUST 电费查询页面
3. 查看网络请求，找到类似以下 URL：
   ```
   https://ykt.ecust.edu.cn/epay/wxpage/wanxiao/eleresult?sysid=XXX&roomid=YYY&areaid=ZZZ&buildid=WWW
   ```
4. 提取参数值填入 `.env` 文件

</details>

<details>
<summary>📱 如何配置 Server酱（微信推送）？</summary>

1. 访问 [Server酱官网](https://sct.ftqq.com/)
2. 使用微信扫码登录
3. 在「发送消息」页面获取 SendKey
4. 将 SendKey 填入 `.env` 文件的 `NOTIFICATION_SERVERCHAN_SENDKEY`
5. 设置 `NOTIFICATION_METHODS=serverchan` 或 `email,serverchan`
6. 关注 Server酱 公众号即可接收推送

**优势：**
- ✅ 配置简单，只需 SendKey
- ✅ 推送到微信，及时性高
- ✅ 免费版每天可推送 5 条消息
- ✅ 支持 Markdown 格式

</details>

### 2. 基本使用

```bash
# 获取一次电量
emon fetch

# 检查并发送告警
emon alert

# 生成分析报告
emon report

# 查看配置信息
emon info

# 启动定时监控（前台运行）
emon schedule
```

### 3. GitHub Actions 自动化（推荐）

1. Fork 本仓库
2. 在仓库设置中添加 Secrets（Settings → Secrets and variables → Actions）：
   - `FETCHER_SYSID`
   - `FETCHER_ROOMID`
   - `FETCHER_AREAID`
   - `FETCHER_BUILDID`
   - （可选）邮件相关的 Secrets

3. 工作流会自动运行：
   - 每小时获取一次电量数据
   - 自动提交数据到 `data/electricity.csv`
   - 低电量时发送邮件告警

4. 查看历史数据：访问仓库的 `data/electricity.csv` 文件

## 📖 详细使用

### CLI 命令

#### `emon init` - 初始化配置

交互式配置向导，帮助首次使用的用户快速设置：

```bash
# 初次配置
emon init

# 强制重新配置
emon init --force
```

#### `emon fetch` - 获取电量

```bash
# 基本使用
emon fetch

# 只查询不保存
emon fetch --no-save

# 显示详细信息
emon fetch --verbose
```

#### `emon alert` - 告警检查

```bash
# 检查并发送邮件
emon alert

# 只检查不发送
emon alert --no-send

# 自定义阈值
emon alert --threshold 20
```

#### `emon report` - 生成报告

```bash
# 生成最近 7 天的报告
emon report

# 分析最近 30 天
emon report --days 30

# 指定输出文件
emon report --output my_report.html

# 生成后不打开浏览器
emon report --no-open
```

#### `emon schedule` - 定时任务

```bash
# 使用默认间隔（配置文件中的值）
emon schedule

# 自定义间隔（每 30 分钟）
emon schedule --interval 1800

# 后台运行（Linux/macOS）
nohup emon schedule > scheduler.log 2>&1 &

# 后台运行（Windows）
start /B emon schedule
```

#### `emon info` - 查看信息

```bash
# 显示配置和统计信息
emon info
```

### 配置优先级

配置项按以下顺序读取（优先级从高到低）：

1. **环境变量**: `FETCHER_SYSID`
2. **`.env` 文件**: 推荐用于敏感信息
3. **`config.toml` 文件**: 可选，适合非敏感配置
4. **代码默认值**

### 项目结构

```
.
├── src/ecust_electricity_monitor/     # 源代码
│   ├── __init__.py
│   ├── __version__.py           # 版本号
│   ├── cli.py                   # CLI 入口
│   ├── client.py                # API 客户端
│   ├── config.py                # 配置管理
│   ├── constants.py             # 常量定义
│   ├── exceptions.py            # 自定义异常
│   ├── health.py                # 健康监控
│   ├── logger.py                # 日志配置
│   ├── models.py                # 数据模型
│   ├── notifier.py              # 推送通知（邮件/Server酱）
│   ├── reporter.py              # 报告生成
│   ├── scheduler.py             # 任务调度
│   ├── storage.py               # CSV 存储
│   ├── templates/               # Jinja2 模板
│   └── utils.py                 # 工具函数
├── data/                        # 数据目录
│   ├── electricity.csv          # 电量数据
│   └── logs/                    # 日志文件
├── reports/                     # 报告输出
├── tests/                       # 测试代码
├── .env.example                 # 环境变量示例
├── config.toml.example          # 配置文件示例
├── pyproject.toml               # 项目配置
└── README.md                    # 本文件
```

## 🔧 高级配置

### 邮件服务器配置

<details>
<summary>Gmail</summary>

```bash
NOTIFICATION_SMTP_HOST=smtp.gmail.com
NOTIFICATION_SMTP_PORT=587
NOTIFICATION_SMTP_USE_TLS=true
NOTIFICATION_SMTP_USER=your_email@gmail.com
NOTIFICATION_SMTP_PASSWORD=your_app_password  # 需要生成应用专用密码
```

应用专用密码生成：https://myaccount.google.com/apppasswords

</details>

<details>
<summary>QQ 邮箱</summary>

```bash
NOTIFICATION_SMTP_HOST=smtp.qq.com
NOTIFICATION_SMTP_PORT=587
NOTIFICATION_SMTP_USE_TLS=true
NOTIFICATION_SMTP_USER=your_qq@qq.com
NOTIFICATION_SMTP_PASSWORD=your_authorization_code  # QQ 邮箱授权码
```

授权码获取：https://service.mail.qq.com/cgi-bin/help?subtype=1&&id=28&&no=1001256

</details>

<details>
<summary>163 邮箱</summary>

```bash
NOTIFICATION_SMTP_HOST=smtp.163.com
NOTIFICATION_SMTP_PORT=465
NOTIFICATION_SMTP_USE_TLS=false  # 163 使用 SSL
NOTIFICATION_SMTP_USER=your_email@163.com
NOTIFICATION_SMTP_PASSWORD=your_authorization_code
```

</details>

### 服务器部署

使用 cron 定时任务（Linux/macOS）：

```bash
# 编辑 crontab
crontab -e

# 每小时执行一次
0 * * * * cd /path/to/project && /path/to/venv/bin/emon fetch >> /var/log/emon.log 2>&1
```

或者使用 systemd timer（推荐）：

```bash
# 创建服务文件
sudo nano /etc/systemd/system/emon-monitor.service

# 创建定时器文件
sudo nano /etc/systemd/system/emon-monitor.timer

# 启用并启动
sudo systemctl enable emon-monitor.timer
sudo systemctl start emon-monitor.timer
```

## 🧪 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
# Lint 和自动修复
ruff check src/ --fix

# 格式化代码
ruff format src/
```

### 类型检查

```bash
mypy src/
```

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Typer](https://typer.tiangolo.com/) - 现代化 CLI 框架
- [Loguru](https://loguru.readthedocs.io/) - 优雅的日志库
- [Pydantic](https://docs.pydantic.dev/) - 数据验证
- [Plotly](https://plotly.com/python/) - 交互式图表

## 📧 联系方式

有问题或建议？欢迎通过以下方式联系：

- 提交 [Issue](https://github.com/yourusername/ecust-dorm-electricity-monitor/issues)
- 发送邮件至: your.email@example.com

---

<div align="center">
Made with ❤️ for ECUST students
</div>
