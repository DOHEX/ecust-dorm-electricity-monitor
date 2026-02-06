"""配置管理 - Configuration Management using Pydantic Settings

配置优先级（从高到低）：
1. 环境变量
2. .env 文件
3. config.toml 文件
4. 代码默认值

最佳实践架构：
- 顶层使用 BaseSettings（只在这里配置文件源）
- 嵌套配置使用 BaseModel（避免重复读取文件）
- env_nested_delimiter 支持扁平化环境变量
- nested_model_default_partial_update 支持部分更新

示例:
    # config.toml
    [app]
    alert_threshold_kwh = 10.0

    [api]
    sysid = "xxx"

    # .env（敏感信息）
    API__SYSID=secret_value
    NOTIFICATION__SMTP_PASSWORD=password

    # 环境变量（最高优先级，支持嵌套）
    export APP__ALERT_THRESHOLD_KWH=15.0
    export API__SYSID=override_value
"""

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

from .constants import DEFAULT_ALERT_THRESHOLD, MAX_RETRIES

# 项目根目录
if __package__:  # 已安装的包
    ROOT_DIR = Path(__file__).parent.parent.parent
else:  # 开发模式
    ROOT_DIR = Path(__file__).parent.parent

CONFIG_FILE = ROOT_DIR / "config.toml"
ENV_FILE = ROOT_DIR / ".env"


class AppConfig(BaseModel):
    """应用通用配置"""

    alert_threshold_kwh: float = Field(
        default=DEFAULT_ALERT_THRESHOLD, description="告警阈值（度/kWh）"
    )
    check_interval_seconds: int = Field(
        default=86400, description="检查间隔（秒），默认每天1次"
    )
    log_level: str = Field(default="INFO", description="日志级别")


class StorageConfig(BaseModel):
    """存储配置"""

    data_dir: str = Field(default="data", description="数据目录")
    csv_filename: str = Field(default="electricity.csv", description="CSV文件名")

    @property
    def csv_path(self) -> Path:
        """完整的CSV文件路径"""
        return ROOT_DIR / self.data_dir / self.csv_filename


class ApiConfig(BaseModel):
    """电量 API 配置"""

    sysid: str | None = Field(default=None, description="系统ID")
    roomid: str | None = Field(default=None, description="房间ID")
    areaid: str | None = Field(default=None, description="区域ID")
    buildid: str | None = Field(default=None, description="建筑ID")
    timeout_seconds: int = Field(default=10, description="请求超时（秒）")
    max_retries: int = Field(default=MAX_RETRIES, description="最大重试次数")

    @property
    def is_configured(self) -> bool:
        """检查是否已配置所有必需字段"""
        return all([self.sysid, self.roomid, self.areaid, self.buildid])


class NotificationConfig(BaseModel):
    """通知配置"""

    # 推送方式: email, serverchan, 或 email,serverchan（多个用逗号分隔）
    channels: list[str] = Field(default_factory=list, description="推送方式列表")

    # 邮件配置
    smtp_host: str | None = Field(default=None, description="SMTP服务器")
    smtp_port: int = Field(default=587, description="SMTP端口")
    smtp_starttls: bool = Field(default=True, description="是否使用STARTTLS")
    smtp_user: str | None = Field(default=None, description="SMTP用户名")
    smtp_password: str | None = Field(
        default=None, description="SMTP密码（仅从环境变量）"
    )
    recipients: list[str] = Field(default_factory=list, description="收件人列表")

    # Server酱配置
    serverchan_sendkey: str | None = Field(default=None, description="Server酱SendKey")

    @property
    def enabled_channels(self) -> list[str]:
        """获取启用的推送方式列表"""
        return [c.strip().lower() for c in self.channels if c.strip()]

    @property
    def is_email_configured(self) -> bool:
        """检查邮件通知是否已配置"""
        return bool(
            self.smtp_host and self.smtp_user and self.smtp_password and self.recipients
        )

    @property
    def is_serverchan_configured(self) -> bool:
        """检查Server酱是否已配置"""
        return bool(self.serverchan_sendkey)

    @property
    def is_configured(self) -> bool:
        """检查是否至少配置了一种推送方式"""
        channels = self.enabled_channels
        if "email" in channels and not self.is_email_configured:
            return False
        if "serverchan" in channels and not self.is_serverchan_configured:
            return False
        return len(channels) > 0


class ReportConfig(BaseModel):
    """报告生成配置"""

    days_to_analyze: int = Field(default=30, description="生成报告的数据天数")
    output_dir: str = Field(default="output/reports", description="报告输出目录")

    @property
    def output_path(self) -> Path:
        """报告输出路径"""
        return ROOT_DIR / self.output_dir


class Settings(BaseSettings):
    """全局配置 - 遵循 Pydantic Settings 最佳实践

    最佳实践：
    1. 顶层使用 BaseSettings，且只在这里配置文件源
    2. 嵌套配置使用 BaseModel，避免重复读取配置文件
    3. 使用 env_nested_delimiter 支持扁平环境变量访问嵌套字段
    4. 使用 nested_model_default_partial_update 支持部分更新

    示例：
        # 环境变量访问嵌套字段（使用双下划线）
        export APP__ALERT_THRESHOLD_KWH=15.0
        export API__SYSID=xxx
        export NOTIFICATION__SMTP_HOST=smtp.gmail.com
    """

    app: AppConfig = Field(default_factory=AppConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    api: ApiConfig = Field(default_factory=ApiConfig)
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    report: ReportConfig = Field(default_factory=ReportConfig)

    model_config = SettingsConfigDict(
        # 配置文件源（只在顶层配置一次）
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        toml_file=str(CONFIG_FILE),
        # 嵌套配置支持
        env_nested_delimiter="__",
        nested_model_default_partial_update=True,
        # 额外选项
        extra="ignore",
        case_sensitive=False,
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            TomlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )

    def __repr__(self) -> str:
        return (
            f"Settings(\n"
            f"  alert_threshold_kwh={self.app.alert_threshold_kwh},\n"
            f"  data_dir={self.storage.data_dir},\n"
            f"  notification_channels={self.notification.channels}\n"
            f")"
        )


def create_env_template() -> str:
    """创建 .env 配置文件模板

    注意：环境变量现在支持两种格式：
    - 嵌套格式（推荐）: API__SYSID, NOTIFICATION__SMTP_HOST, APP__ALERT_THRESHOLD_KWH
    """
    template = """# ⚡ ECUST 电量监控系统配置文件
# 
# 使用说明：
# 1. 填写你的 ECUST API 参数（必填）
# 2. 保存此文件为 .env
# 3. 运行 emon fetch 测试

# =============================================================================
# ECUST API 配置（必填）
# =============================================================================
# 获取方法：浏览器访问 ECUST 电费查询页面，按 F12 查看网络请求中的参数

API__SYSID=your_sysid_here
API__ROOMID=your_roomid_here
API__AREAID=your_areaid_here
API__BUILDID=your_buildid_here

# =============================================================================
# 应用配置（可选）
# =============================================================================

# APP__ALERT_THRESHOLD_KWH=30.0
# APP__CHECK_INTERVAL_SECONDS=3600
# APP__LOG_LEVEL=INFO

# =============================================================================
# 通知配置（可选）
# =============================================================================
# 推送方式：email（邮件）、serverchan（Server酱）或 email,serverchan（两者都用）

# NOTIFICATION__CHANNELS=["email", "serverchan"]

# --- 邮件通知 ---
# NOTIFICATION__SMTP_HOST=smtp.gmail.com
# NOTIFICATION__SMTP_PORT=587
# NOTIFICATION__SMTP_STARTTLS=true
# NOTIFICATION__SMTP_USER=your_email@gmail.com
# NOTIFICATION__SMTP_PASSWORD=your_app_password
# NOTIFICATION__RECIPIENTS=["recipient@example.com"]

# --- Server酱（微信推送）---
# 获取SendKey：https://sct.ftqq.com/
# NOTIFICATION__SERVERCHAN_SENDKEY=your_sendkey_here
"""
    return template


def ensure_config_exists() -> bool:
    """确保配置文件存在，如果不存在则创建模板

    Returns:
        True if config exists, False if template was created
    """
    if ENV_FILE.exists():
        return True

    # 创建 .env 模板
    ENV_FILE.write_text(create_env_template(), encoding="utf-8")
    return False


# 全局配置实例
settings = Settings()
config = settings


__all__ = [
    "settings",
    "config",
    "Settings",
    "AppConfig",
    "StorageConfig",
    "ApiConfig",
    "NotificationConfig",
    "ReportConfig",
    "ROOT_DIR",
    "CONFIG_FILE",
    "ENV_FILE",
    "create_env_template",
    "ensure_config_exists",
]
