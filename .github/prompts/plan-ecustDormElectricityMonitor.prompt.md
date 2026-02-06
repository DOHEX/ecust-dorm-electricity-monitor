# Plan: 宿舍电量监控系统完整重设计（Modern Stack）

> **版本：** 2.0 | **最后更新：** 2026-02-05

---

## 目录

1. [核心目标与决策](#核心目标与决策)
2. [技术栈总结](#技术栈总结)
3. [实现步骤](#实现步骤)
   - [阶段1：核心数据层](#阶段1核心数据层重构)
   - [阶段2：业务逻辑层](#阶段2业务逻辑层)
   - [阶段3：调度层](#阶段3调度层支持多部署方式)
   - [阶段4：Web看板](#阶段4web-看板可选本地部署)
   - [阶段5：项目结构](#阶段5项目结构和配置)
   - [阶段6：部署配置](#阶段6部署配置和文档)
4. [CLI命令参考](#cli-命令参考)
5. [验证清单](#验证清单)
6. [设计原则](#关键设计原则)
7. [部署决策树](#部署决策树)
8. [实现优先级](#实现优先级)
9. [优化总览](#优化总览)

---

## 核心目标与决策

### 项目目标
将单一的电量查询脚本改造成完整的**数据采集 → 存储 → 分析 → 告警**系统，支持多种部署方式（GitHub Actions / 服务器 / 本地开发）。

### 关键决策
| 方面 | 选择 | 理由 |
|------|------|------|
| **项目结构** | `src/` 布局 | PyPA 标准，测试隔离，打包友好 |
| **CLI 命令** | `emon` (4字符) | 简短易记，Unix 风格 |
| **数据存储** | CSV + Pydantic | 简单可靠，类型安全 |
| **图表展示** | Plotly + GitHub Pages | 交互式，免费托管 |
| **告警通知** | 邮件 + 健康检查 | 标准化，可扩展 |
| **CLI 框架** | Typer | 现代、简洁、类型安全 |
| **日志系统** | Loguru | 配置简单，自动轮换 |
| **任务调度** | schedule | 轻量级，足够简单需求 |
| **配置管理** | Pydantic Settings | 类型验证，环境变量支持 |
| **代码质量** | pre-commit + ruff | 自动化检查 |

---

## 技术栈总结

| 组件 | 技术 | 版本要求 |
|------|------|----------|
| **Python** | CPython | >=3.9 |
| **CLI** | Typer[all] | >=0.10.0 |
| **日志** | Loguru | >=0.7.0 |
| **配置** | Pydantic Settings | >=2.12.0 |
| **HTTP** | Requests | >=2.32.5 |
| **HTML解析** | BeautifulSoup4 + lxml | >=4.14.3 |
| **数据可视化** | Plotly | >=5.18.0 |
| **调度** | schedule | >=1.2.0 |
| **Web框架** | Flask (可选) | >=3.0.0 |
| **测试** | pytest + pytest-cov | >=7.0 |
| **代码质量** | black + ruff | latest |

---

## 实现步骤

### 阶段1：核心数据层重构

1. **cli.py** - 应用入口（单一命令入口点）
   - 使用 Typer 框架构建子命令
   - CLI 命令名：`emon`（electricity monitor 缩写，4字符）
   - 子命令：`fetch`、`alert`、`report`、`schedule`
   - 支持 `--version` 显示版本号
   - 自动生成帮助文档

2. **config.py** - 配置管理系统
   - 使用 Pydantic BaseSettings 管理配置
   - 配置级联：环境变量 > config.toml > 代码默认值
   - 分离：数据配置 + 获取配置 + 邮件配置
   - 敏感信息（SMTP 密码）仅从环境变量读取

3. **storage.py** - 数据持久化（单一职责：仅负责CSV读写）
   - `CSVStorage` 类，操作 CSV 文件
   - `append_record(record: ElectricityRecord) -> None` - 新增记录（原子操作）
   - `get_records(start_date: datetime, end_date: datetime) -> List[ElectricityRecord]` - 按时间范围查询
   - `get_recent_records(count: int = 100) -> List[ElectricityRecord]` - 获取最近N条
   - `get_latest() -> Optional[ElectricityRecord]` - 获取最新记录
   - CSV 格式：`timestamp, power, alert_sent`

4. **models.py** - 数据模型（新增）
   - `ElectricityRecord` - 电量记录 Pydantic 模型
     - 字段：`timestamp`, `power`, `alert_sent`
     - 数据验证：电量范围 0-999，时间戳格式
   - `FetchResult` - 获取结果模型
     - 字段：`power`, `timestamp`, `source`, `raw_response`
   - `AlertContext` - 告警上下文模型
     - 字段：`current_record`, `trend`, `threshold`, `history`
   - `ReportData` - 报告数据模型
     - 字段：`records`, `statistics`, `metadata`
   - 类型安全的序列化/反序列化

---

### 阶段2：业务逻辑层

5. **fetcher.py** - 电量获取模块（单一职责：仅负责API调用）
   - `ElectricityFetcher` 类封装获取逻辑
   - `fetch() -> FetchResult` - 获取电量并返回结构化结果
     - 返回 `FetchResult` 对象（包含 power, timestamp, metadata）
   - `_make_request() -> Response` - 私有方法：发起 HTTP 请求
   - `_parse_response(html: str) -> float` - 私有方法：解析 HTML
   - 增强错误处理：网络异常自动重试（指数退避）
   - 异常处理：`FetchError` 捕获网络异常

6. **notifier.py** - 告警通知模块（单一职责：仅负责发送通知）
   - `EmailNotifier` 类封装邮件逻辑
   - `should_send_alert(record: ElectricityRecord) -> bool` - 判断是否需要告警（纯函数）
   - `send_power_alert(context: AlertContext) -> None` - 发送电量告警
   - `send_system_alert(message: str, details: Dict) -> None` - 发送系统告警
   - `_build_email_content(context: AlertContext) -> str` - 私有方法：构建邮件内容
   - `_send_email(to: str, subject: str, body: str) -> None` - 私有方法：SMTP发送
   - 支持可选邮件服务（`smtp_enabled` 配置控制）

7. **reporter.py** - 报告生成模块（单一职责：仅负责渲染）
   - `HTMLReporter` 类封装报告逻辑
   - `generate(data: ReportData) -> str` - 生成 HTML 报告（依赖注入）
     - 接收 `ReportData` 对象，不直接查询数据库
   - `_create_power_chart(records: List[ElectricityRecord]) -> go.Figure` - 私有：生成折线图
   - `_create_statistics_table(records: List[ElectricityRecord]) -> str` - 私有：生成统计表
   - `_render_template(charts, tables, metadata) -> str` - 私有：渲染 HTML
   - 使用 Plotly 生成交互式图表

8. **exceptions.py** - 自定义异常
   - `ElectricityMonitorError` - 基础异常
   - `FetchError(message, retry_count, original_exception, response_text)` - 获取失败
   - `StorageError` - CSV 存储失败
   - `NotificationError` - 邮件发送失败
   - `ConfigurationError` - 配置错误

9. **logger.py** - 日志配置
   - 使用 Loguru 替代标准 logging
   - 环境自适应：CI 环境简化格式，本地详细格式
   - 自动配置：控制台 + 文件输出
   - 日志文件轮换：500MB 自动备份，保留 7 天

10. **constants.py** - 常量定义
    - API 端点：`ELECTRICITY_API_URL`
    - CSV 列名枚举：`CSVColumn`
    - 数据验证范围：`MIN_POWER_VALUE`, `MAX_POWER_VALUE`
    - 默认目录路径：`DEFAULT_DATA_DIR`, `DEFAULT_OUTPUT_DIR`
    - 告警阈值：`DEFAULT_ALERT_THRESHOLD`
    - 重试配置：`MAX_RETRIES`, `RETRY_BACKOFF_FACTOR`

11. **utils.py** - 工具函数模块（新增）
    - `calculate_trend(records: List[ElectricityRecord]) -> str` - 计算趋势（上升/下降/稳定）
    - `calculate_daily_consumption(records: List[ElectricityRecord]) -> float` - 计算日均消耗
    - `get_date_range(days: int) -> Tuple[datetime, datetime]` - 获取日期范围
    - `format_timestamp(dt: datetime) -> str` - 格式化时间戳
    - `validate_power_value(power: float) -> bool` - 验证电量值

12. **health.py** - 健康检查模块（新增）
    - `HealthMonitor` 类管理系统健康状态
    - `record_success() -> None` - 记录成功执行
    - `record_failure(error: Exception) -> None` - 记录失败
    - `get_failure_count() -> int` - 获取连续失败次数
    - `should_send_system_alert() -> bool` - 判断是否需要系统告警
    - `reset() -> None` - 重置健康状态

13. **__version__.py** - 版本管理
    - `__version__ = "2.0.0"`
    - 供 CLI `--version` 使用

---

### 阶段3：调度层（支持多部署方式）

14. **scheduler.py** - 本地调度器（使用 schedule 库）
   - `SchedulerService` 类管理定时任务
    - `setup_jobs()` - 定义任务：08:00 执行完整流程
    - `run_full_workflow() -> None` - 执行完整流程（fetch → save → alert → report）
    - `start() -> None` - 启动调度循环（阻塞式）

15. **Cron 支持** - 标准系统 Cron
    - 提供现成命令供用户 crontab 配置
    - 单次执行模式支持：`emon fetch && emon alert`

16. **.github/workflows/monitor.yml** - GitHub Actions 工作流
    - 触发条件：每日 UTC 8:00 定时运行
    - 包含两个 Job：
      - **test**：运行测试、代码检查、依赖缓存
      - **fetch**：实际数据采集（仅定时触发或手动）
    - 步骤流程：
      1. Checkout 仓库
      2. 设置 Python 环境（带依赖缓存）
      3. 安装依赖
      4. 执行 `emon fetch`
      5. 执行 `emon alert`
      6. 执行 `emon report`
      7. 健康检查（连续失败告警）
      8. 部署报告到 GitHub Pages（`output/reports/`）
    - 敏感信息通过 GitHub Secrets 传递

---

### 阶段4：Web 看板（可选本地部署）

17. **web/app.py** - Flask Web 应用
    - 路由 `/` - 主页显示最新电量和趋势
    - 路由 `/dashboard` - 展示交互式 Plotly 图表（嵌入 HTML）
    - 路由 `/api/data` - JSON API 接口，返回最近7天数据
    - 路由 `/health` - 健康检查端点

18. **templates/dashboard.html** - Web 前端模板
    - 简单 HTML/CSS 布局（无框架）
    - 使用 Plotly.js 实现交互式图表
    - 显示：当前电量 + 7日趋势 + 月度统计
    - 自上次更新时间

---

### 阶段5：项目结构和配置

19. **创建完整目录结构（src/ 布局 - PyPA 标准）**
    ```
    ecust-dorm-electricity-monitor/
    ├── src/                              # ← 源代码目录
    │   └── electricity_monitor/          # 核心应用包
    │       ├── __init__.py             # 包初始化
    │       ├── __version__.py          # 版本号
    │       ├── cli.py                  # Typer CLI 入口（emon 命令）
    │       ├── config.py               # Pydantic 配置管理
    │       ├── logger.py               # Loguru 日志配置
    │       ├── exceptions.py           # 自定义异常
    │       ├── constants.py            # 常量定义
    │       ├── models.py               # Pydantic 数据模型
    │       ├── fetcher.py              # 电量获取逻辑
    │       ├── storage.py              # CSV 数据存储
    │       ├── notifier.py             # 邮件告警模块
    │       ├── reporter.py             # HTML 报告生成
    │       ├── scheduler.py            # schedule 调度服务
    │       ├── utils.py                # 工具函数
    │       ├── health.py               # 健康检查
    │       └── web/                    # Web 应用（可选）
    │           ├── __init__.py
    │           ├── app.py              # Flask 应用实例
    │           └── routes.py           # 路由定义
    ├── config/                         # 配置模板目录
    │   ├── default.toml                # 默认配置模板
    │   └── .env.example                # 环境变量模板
    ├── config.toml                     # 用户配置（根目录，gitignore）
    ├── .env                            # 环境变量（根目录，gitignore）
    ├── data/                           # 数据目录（.gitignore）
    │   └── .gitkeep
    ├── output/                         # 输出目录（.gitignore）
    │   ├── reports/                    # HTML 报告目录
    │   └── .gitkeep
    ├── logs/                           # 日志目录（.gitignore）
    │   └── .gitkeep
    ├── templates/                      # Web 模板
    │   └── dashboard.html
    ├── tests/                          # 单元和集成测试
    │   ├── conftest.py                 # pytest fixtures
    │   ├── test_fetcher.py
    │   ├── test_storage.py
    │   └── test_notifier.py
    ├── docs/                           # 文档
    │   ├── DEPLOY_GITHUB_ACTIONS.md
    │   ├── DEPLOY_LOCAL.md
    │   ├── DEPLOY_DOCKER.md            # 可选 Docker 部署
    │   └── API.md
    ├── .github/workflows/
    │   └── monitor.yml                 # GitHub Actions 工作流
    ├── .pre-commit-config.yaml         # Git hooks 配置
    ├── .gitignore
    ├── pyproject.toml                  # 项目配置和依赖
    ├── requirements.txt                # 依赖锁定文件
    ├── README.md                       # 项目说明
    └── LICENSE
    ```

20. **pyproject.toml** - 项目配置和依赖管理
    ```toml
    [build-system]
    requires = ["setuptools>=61.0", "wheel"]
    build-backend = "setuptools.build_meta"
    
    [project]
    name = "ecust-dorm-electricity-monitor"
    version = "2.0.0"
    description = "宿舍用电监控系统"
    authors = [{name = "Your Name", email = "your@email.com"}]
    readme = "README.md"
    license = {text = "MIT"}
    requires-python = ">=3.9"
    classifiers = [
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ]
    
    dependencies = [
        # HTML 解析
        "requests>=2.32.5",
        "beautifulsoup4>=4.14.3",
        "lxml>=6.0.2",
        
        # 配置管理
        "pydantic-settings>=2.12.0",
        "pydantic>=2.0.0",
        "pyyaml>=6.0",
        
        # 现代 CLI
        "typer[all]>=0.10.0",  # 包含 rich 输出
        
        # 日志
        "loguru>=0.7.0",
        
        # 数据和图表
        "plotly>=5.18.0",
        
        # 任务调度
        "schedule>=1.2.0",
        
        # 环境变量管理
        "python-dotenv>=1.0.0",
    ]
    
    [project.optional-dependencies]
    dev = [
        "pytest>=7.0",
        "pytest-cov>=4.0",
        "pytest-mock>=3.10.0",
        "black>=23.0",
        "ruff>=0.1.0",
    ]
    web = ["flask>=3.0.0", "flask-httpauth>=4.8.0"]  # Web 看板 + 认证
    
    [project.scripts]
    emon = "electricity_monitor.cli:app"  # 简短命令
    
    [tool.setuptools.packages.find]
    where = ["src"]
    
    [tool.pytest.ini_options]
    testpaths = ["tests"]
    addopts = "-v --cov=electricity_monitor --cov-report=term-missing"
    
    [tool.black]
    line-length = 100
    target-version = ['py39']
    
    [tool.ruff]
    line-length = 100
    target-version = "py39"
    ```

21. **config.toml** - 应用配置（用户自定义）
    ```toml
    # 应用配置
    [app]
    alert_threshold = 10.0              # 告警阈值（度）
    check_interval_seconds = 86400      # 本地检查间隔（秒）
    log_level = "INFO"
    
    # 存储配置
    [storage]
    data_dir = "data"
    csv_filename = "electricity.csv"
    
    # 获取配置（可被环境变量覆盖）
    [fetcher]
    timeout_seconds = 10
    max_retries = 3
    
    # 报告配置
    [report]
    days_to_analyze = 30                # 生成报告的数据范围
    output_dir = "output/reports"
    ```

22. **.env.example** - 环境变量模板
    ```bash
    # ===========================================
    # 电量获取配置（必需）
    # ===========================================
    API__SYSID=1
    API__ROOMID=511
    API__AREAID=2
    API__BUILDID=46
    
    # ===========================================
    # 邮件通知配置（可选）
    # ===========================================
    NOTIFICATION__CHANNELS=["email"]
    NOTIFICATION__SMTP_HOST=smtp.gmail.com
    NOTIFICATION__SMTP_PORT=587
    NOTIFICATION__SMTP_STARTTLS=true
    NOTIFICATION__SMTP_USER=your-email@gmail.com
    NOTIFICATION__SMTP_PASSWORD=your-app-password  # Gmail App Password
    NOTIFICATION__RECIPIENTS=["recipient@gmail.com"]
    
    # ===========================================
    # 应用配置（可选，覆盖 config.toml）
    # ===========================================
    APP__ALERT_THRESHOLD_KWH=10.0
    APP__LOG_LEVEL=INFO
    
    # ===========================================
    # Web 看板认证（可选）
    # ===========================================
    WEB_USER=admin
    WEB_PASSWORD=secure-password-here
    ```

---

### 阶段6：部署配置和文档

23. **.gitignore** - 忽略文件配置
    ```
    # Python
    __pycache__/
    *.py[cod]
    *$py.class
    venv/
    .venv/
    
    # 项目数据
    data/
    !data/.gitkeep
    output/
    !output/.gitkeep
    logs/
    !logs/.gitkeep
    
    # 配置文件
    config.toml
    .env
    .env.local
    
    # IDE
    .vscode/
    .idea/
    *.swp
    
    # 测试
    .pytest_cache/
    .coverage
    htmlcov/
    ```

24. **requirements.txt** - 依赖锁定文件（生产环境）
    ```bash
    # 生成方式：pip freeze > requirements.txt
    # 或使用 pip-tools：pip-compile pyproject.toml
    ```

25. **.pre-commit-config.yaml** - Git hooks 配置
    ```yaml
    repos:
      - repo: https://github.com/psf/black
        rev: 23.0.0
        hooks:
          - id: black
      
      - repo: https://github.com/astral-sh/ruff-pre-commit
        rev: v0.1.0
        hooks:
          - id: ruff
            args: [--fix]
      
      - repo: https://github.com/pre-commit/pre-commit-hooks
        rev: v4.5.0
        hooks:
          - id: trailing-whitespace
          - id: end-of-file-fixer
          - id: check-yaml
          - id: check-toml
    ```

26. **README.md** - 项目说明文档
    - 功能概述
    - 快速开始（本地开发）
    - 部署指南（GitHub Actions / Cron / Docker）
    - API 命令文档
    - 故障排查

27. **部署文档（在 docs/ 目录）**
    - `DEPLOY_GITHUB_ACTIONS.md` - GitHub Actions 部署（推荐）
    - `DEPLOY_LOCAL.md` - 本地 Cron 部署
    - `DEPLOY_DOCKER.md` - Docker 容器部署（可选）
    - `API.md` - CLI 命令和配置参考

28. **Dockerfile**（可选）
    ```dockerfile
    FROM python:3.11-slim
    
    WORKDIR /app
    
    # 安装依赖
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    # 复制代码
    COPY . .
    RUN pip install --no-cache-dir -e .
    
    # 创建目录
    RUN mkdir -p data output/reports logs
    
    # 运行调度器
    CMD ["emon", "schedule"]
    ```

29. **systemd service 配置**（Linux 服务器）
    ```ini
    # /etc/systemd/system/emon.service
    [Unit]
    Description=Electricity Monitor Service
    After=network.target
    
    [Service]
    Type=simple
    User=your-user
    WorkingDirectory=/path/to/ecust-dorm-electricity-monitor
    Environment="PATH=/path/to/venv/bin"
    ExecStart=/path/to/venv/bin/emon schedule
    Restart=on-failure
    RestartSec=10
    
    [Install]
    WantedBy=multi-user.target
    ```

---

## CLI 命令参考

```bash
# 显示版本
emon --version

# 显示帮助
emon --help

# 获取当前电量并保存
emon fetch

# 检查并发送告警（如需）
emon alert

# 生成 HTML 报告
emon report

# 启动本地调度器（阻塞式）
emon schedule

# 完整流程（用于 cron）
emon fetch && emon alert && emon report
```

---

## 验证清单

### 本地开发验证

1. **环境设置**
   ```bash
   # 复制环境模板
   cp config/.env.example .env
   # 编辑 .env 填入宿舍信息和邮箱配置
   
   # 创建虚拟环境并安装
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   ```

2. **单元测试**
   ```bash
   pytest tests/ -v --cov
   ```

3. **数据层测试**
   ```bash
   # 一次性获取电量
   emon fetch
   # 验证 data/electricity.csv 是否创建并有数据
   ```

4. **告警功能测试**
   ```bash
   # 修改配置中 alert_threshold 为 100（确保会告警）
   emon alert
   # 验证是否收到邮件
   ```

5. **报告生成测试**
   ```bash
   emon report
   # 用浏览器打开 output/reports/report.html 验证图表
   ```

6. **本地调度测试**
   ```bash
   # 启动本地调度器（仅用于开发测试）
   emon schedule
   # 观察日志输出验证定时功能
   ```

7. **Web 看板测试**
   ```bash
   # 以 Flask 应用启动（可选）
   python -m electricity_monitor.web.app
   # 访问 http://localhost:5000/dashboard 验证界面
   ```

### GitHub Actions 验证

1. 将项目推送到 GitHub
2. Settings → Secrets → 配置敏感信息：
   - `FETCHER_SYSID`, `FETCHER_ROOMID`, `FETCHER_AREAID`, `FETCHER_BUILDID`
   - `NOTIFICATION_SMTP_PASSWORD`, `NOTIFICATION_EMAIL_TO` 等
3. Actions 选项卡中验证工作流运行状态
4. GitHub Pages 设置中启用，验证报告是否发布到 `https://<username>.github.io/<repo>/`

---

## 关键设计原则

### 1. 配置管理（零硬编码）
- **优先级链路**：环境变量 > .env 文件 > config.toml > 代码默认值
- **安全隐私**：SMTP 密码等敏感信息仅从环境变量读取
- **类型安全**：使用 Pydantic 验证配置类型和必填字段

### 2. 错误处理（可恢复）
- **分层异常**：FetchError（获取）、StorageError（存储）、NotificationError（通知）
- **重试机制**：网络异常采用指数退避重试
- **错误隔离**：邮件发送失败不应中断数据保存

### 3. 日志记录（溯源友好）
- **使用 Loguru**：自动日志轮换、多处理器支持
- **日志级别**：DEBUG（开发）、INFO（生产）、ERROR（告警）
- **日志保留**：500MB 自动备份，保留 7 天

### 4. 数据持久化（简单可靠）
- **CSV 格式**：易于备份、版本控制、人工审查
- **追加式写入**：原子操作，防止数据丢失
- **时间戳标准**：ISO 8601 格式（`2024-02-05T08:00:00+08:00`）

### 5. 模块独立性（可测试）
- 每个模块单一职责，可独立测试
- 业务逻辑与框架解耦（Typer CLI、Flask Web 可替换）
- 使用 pytest fixtures 共享测试数据

### 6. 调度灵活性（多部署支持）
- **本地开发**：Typer CLI + schedule 库
- **服务器**：Cron + 脚本
- **云端**：GitHub Actions（推荐，无需维护）

---

## 技术栈总结

| 组件 | 技术 | 理由 |
|------|------|------|
| **CLI** | Typer | 现代、简洁、类型安全 |
| **日志** | Loguru | 配置简单，自动轮换 |
| **配置** | Pydantic | 类型验证，环境变量支持 |
| **数据存储** | CSV + Python | 简单可靠，便于版本控制 |
| **数据分析** | Plotly | 交互式图表，无需 JavaScript |
| **Web 框架** | Flask | 轻量，适合可选模块 |
| **本地调度** | schedule | 轻量，足够简单需求 |
| **云端调度** | GitHub Actions | 免费，无需维护服务器 |
| **测试** | pytest | Python 标准测试框架 |

---

## 部署决策树

```
┌─ 想要完全免费部署？
│  └─► GitHub Actions（推荐）
│      - 免费的云端运行
│      - GitHub Pages 托管报告
│      - 敏感信息用 Secrets 保管
│
├─ 想在自己的服务器运行？
│  └─► Linux Cron（简单）
│      - 安装依赖后，添加 crontab
│      - 日志保存在本地
│      - 可选：Flask 运行看板
│
└─ 想要本地开发调试？
   └─► schedule 库 + Typer CLI
       - 完整功能在本地测试
       - 便于调整参数
```

---

## 实现优先级

### Phase 1（核心基础）- Week 1
- [ ] 项目结构搭建（src/ 布局 + pyproject.toml）
- [ ] 常量定义（constants.py）
- [ ] 数据模型（models.py - 4个模型）
  - [ ] ElectricityRecord
  - [ ] FetchResult
  - [ ] AlertContext
  - [ ] ReportData
- [ ] 配置管理（config.py）
- [ ] 日志系统（logger.py + Loguru）
- [ ] 异常处理（exceptions.py + ConfigurationError）
- [ ] 数据存储（storage.py - 单一职责）

### Phase 2（业务逻辑）- Week 2
- [ ] 电量获取（fetcher.py - 返回 FetchResult 对象）
- [ ] 工具函数（utils.py - 趋势计算、日期处理）
- [ ] 健康检查（health.py - 独立模块）
- [ ] 邮件告警（notifier.py - 职责分离）
  - [ ] should_send_alert() - 判断逻辑
  - [ ] send_power_alert() - 发送逻辑
- [ ] CLI 入口（cli.py + Typer，命令名 `emon`）
- [ ] 单元测试（tests/）

### Phase 3（报告和调度）- Week 3
- [ ] 报告生成（reporter.py - 依赖注入设计）
- [ ] 本地调度（scheduler.py）
- [ ] GitHub Actions 工作流（.github/workflows/monitor.yml - 双 job）
- [ ] 依赖锁定（requirements.txt）
- [ ] 文档编写（README.md + docs/）

### Phase 4（可选增强）- Week 4+
- [ ] Flask Web 看板（web/ + flask-httpauth 认证）
- [ ] Docker 容器化
- [ ] pre-commit hooks
- [ ] systemd service 配置
- [ ] 集成测试增强

---

## 优化总览

本 plan 基于 **SOLID 原则**和 Python 最佳实践进行了全面优化：

### ✅ 项目结构优化
- **采用 src/ 布局**（PyPA 标准）- 测试隔离、打包友好
- **配置文件路径规范** - config.toml 和 .env 在根目录
- **完整的 build-system 配置** - 支持标准打包工具

### ✅ CLI 命令优化
- **`emon` 替代 `electricity-monitor`** - 超短命令（4个字符 vs 21个字符）
- **子命令简化** - `fetch`, `alert`, `report`, `schedule`
- **Unix 风格** - 类似 `grep`, `sudo`, `cron`
- **支持 `--version`** - 通过 `__version__.py` 管理版本

### ✅ 函数命名和职责优化（符合 SOLID）

#### **单一职责原则（SRP）**
| 模块 | 原设计问题 | 优化后 |
|------|----------|--------|
| `storage.py` | ❌ 混合健康检查 | ✅ 仅负责 CSV 读写 |
| `notifier.py` | ❌ `check_and_alert()` 做两件事 | ✅ 分离为 `should_send_alert()` + `send_alert()` |
| `reporter.py` | ❌ 自己查询数据 | ✅ 接收数据作为参数（依赖注入） |
| `fetcher.py` | ❌ 返回原始 float | ✅ 返回结构化 `FetchResult` 对象 |

#### **新增模块**
- **`utils.py`** - 工具函数（趋势计算、日期处理）
- **`health.py`** - 健康检查独立模块
- **`models.py`** - 扩充多个数据模型（`FetchResult`, `AlertContext`, `ReportData`）

### ✅ 数据验证强化
- **Pydantic 数据模型** - 多个模型类型安全
- **数据范围验证** - 电量值 0-999，时间戳格式检查
- **constants.py 完整定义** - API 端点、列名、默认值、重试配置

### ✅ 错误处理增强
- **详细异常上下文** - `FetchError` 包含 retry_count, original_exception, response_text
- **新增 ConfigurationError** - 配置错误专用异常
- **健康检查机制** - 独立 `HealthMonitor` 类管理连续失败

### ✅ 函数参数优化（避免 Primitive Obsession）
```python
# 原设计（不好）
def send_alert_email(power: float, trend: str)  # ❌ 原始类型

# 优化后（面向对象）
def send_power_alert(context: AlertContext)     # ✅ 封装对象
```

### ✅ 依赖管理完善
- **依赖锁定** - requirements.txt 锁定生产版本
- **Flask 归类到 optional** - 仅 Web 看板需要
- **typer[all]** - 包含 rich 美化输出
- **pre-commit hooks** - 代码质量自动检查

### ✅ CI/CD 增强
- **完整的 GitHub Actions** - test job + fetch job 分离
- **依赖缓存** - 加速 CI 运行
- **代码质量检查** - ruff + black 自动化

### ✅ 部署配置完善
- **systemd service 配置** - Linux 标准服务管理
- **Dockerfile 优化** - 正确的安装流程和入口命令
- **多环境支持** - 开发/生产环境隔离

### ✅ 安全性提升
- **Web 看板认证** - flask-httpauth 基本认证
- **敏感信息分离** - 所有密码仅从环境变量读取
- **.gitignore 完善** - config.toml 和 .env 都被忽略

---

## 核心改进对比

| 方面 | 原方案 | 优化后 |
|------|-------|--------|
| **项目结构** | 扁平 | src/ 布局（PyPA 标准） |
| **CLI 命令** | `electricity-monitor` (21字符) | `emon` (4字符) |
| **函数职责** | 混合职责（违反 SRP） | 单一职责（符合 SOLID） |
| **数据模型** | 仅 `ElectricityRecord` | 4个模型（Record, FetchResult, AlertContext, ReportData） |
| **fetcher 返回** | `float` | `FetchResult` 对象 |
| **notifier 设计** | `check_and_alert()` 做两件事 | 分离为独立函数 |
| **reporter 依赖** | 直接查询 storage | 依赖注入 |
| **健康检查** | 混在 storage 中 | 独立 `health.py` 模块 |
| **工具函数** | 散落各处 | 集中在 `utils.py` |
| **函数参数** | 原始类型（float, str） | 对象类型（AlertContext） |
| **配置管理** | 路径混乱 | 标准化（根目录） |
| **日志格式** | 固定 | 环境自适应 |
| **依赖管理** | 版本范围 | 锁定文件 |
| **CI/CD** | 单 job | 双 job（test + fetch） |
| **版本管理** | 无 | `__version__.py` |
| **代码质量** | 无 | pre-commit + ruff |

---

## SOLID 原则应用

| 原则 | 体现 |
|------|------|
| **S - 单一职责** | storage 仅存储，notifier 仅通知，reporter 仅渲染 |
| **O - 开闭原则** | 通过抽象类扩展（如新增其他通知方式） |
| **L - 里氏替换** | 数据模型继承 BaseModel |
| **I - 接口隔离** | 小而精的接口（函数单一职责） |
| **D - 依赖倒置** | reporter 接收数据参数（不依赖 storage） |

---

**本 plan 现已完全符合 Python 2020+ 最佳实践和 SOLID 原则**，可直接开始实施。
