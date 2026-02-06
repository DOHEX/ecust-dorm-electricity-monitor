"""测试配置加载与优先级"""

from __future__ import annotations

from pydantic_settings import SettingsConfigDict

from ecust_electricity_monitor.config import NotificationConfig, Settings


def test_settings_priority_env_over_dotenv_over_toml(tmp_path, monkeypatch):
    toml_path = tmp_path / "config.toml"
    toml_path.write_text(
        """
[app]
alert_threshold_kwh = 5.0

[api]
sysid = "toml"
roomid = "room"
areaid = "area"
buildid = "build"

[notification]
channels = ["serverchan"]
smtp_starttls = false
""".strip()
    )

    env_path = tmp_path / ".env"
    env_path.write_text(
        """
APP__ALERT_THRESHOLD_KWH=6.0
API__SYSID=envfile
NOTIFICATION__CHANNELS=["email"]
NOTIFICATION__SMTP_STARTTLS=true
""".strip()
    )

    monkeypatch.setenv("API__SYSID", "env")
    monkeypatch.setenv("APP__ALERT_THRESHOLD_KWH", "7.0")

    class TestSettings(Settings):
        model_config = SettingsConfigDict(
            env_file=str(env_path),
            env_file_encoding="utf-8",
            toml_file=str(toml_path),
            env_nested_delimiter="__",
            nested_model_default_partial_update=True,
            extra="ignore",
            case_sensitive=False,
        )

    settings = TestSettings()

    assert settings.api.sysid == "env"
    assert settings.app.alert_threshold_kwh == 7.0
    assert settings.notification.channels == ["email"]
    assert settings.notification.smtp_starttls is True


def test_notification_channels_normalize():
    config = NotificationConfig(channels=["Email", " serverchan "])
    assert config.enabled_channels == ["email", "serverchan"]
