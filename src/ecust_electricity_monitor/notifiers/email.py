"""邮件通知器

通过 SMTP 发送电量告警邮件。
"""

import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ..config import NotificationConfig
from ..exceptions import NotificationError
from ..logger import logger
from ..models import AlertContext
from .base import BaseNotifier


class EmailNotifier(BaseNotifier):
    """邮件通知器

    使用 SMTP 协议发送 HTML 格式的告警邮件。
    使用 Jinja2 模板渲染邮件内容。
    """

    def __init__(self, config: NotificationConfig):
        """初始化邮件通知器

        Args:
            config: 通知配置对象
        """
        self.config = config

        # 初始化 Jinja2 环境
        template_dir = Path(__file__).parent.parent / "templates"
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            autoescape=select_autoescape(["html", "xml"]),
        )

    @property
    def name(self) -> str:
        """通知器名称"""
        return "邮件"

    def is_available(self) -> bool:
        """检查是否可用"""
        return self.config.is_email_configured

    def send_power_alert(self, context: AlertContext) -> bool:
        """发送电量低电告警

        Args:
            context: 告警上下文

        Returns:
            发送是否成功
        """
        if not self.is_available():
            logger.warning("邮件未配置，跳过发送")
            return False

        try:
            subject = self._build_alert_subject(context)
            body = self._build_alert_body(context)

            self._send_email(subject, body)

            logger.info(f"邮件发送成功: {subject}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def send_system_alert(
        self, consecutive_failures: int, last_success_time: datetime | None
    ) -> bool:
        """发送系统健康告警

        Args:
            consecutive_failures: 连续失败次数
            last_success_time: 最后成功时间

        Returns:
            发送是否成功
        """
        if not self.is_available():
            logger.warning("邮件未配置，跳过发送")
            return False

        try:
            subject = f"⚠️ 电量监控系统异常 - 连续失败 {consecutive_failures} 次"

            # 准备模板数据
            template_data = {
                "consecutive_failures": consecutive_failures,
                "last_success_time": last_success_time,
                "alert_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }

            # 渲染模板
            template = self.jinja_env.get_template("system_alert_email.html")
            body = template.render(**template_data)

            self._send_email(subject, body)
            logger.info(f"系统告警邮件已发送: {consecutive_failures} 次失败")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False

    def _build_alert_subject(self, context: AlertContext) -> str:
        """构建告警邮件主题"""
        level_emoji = "🔴" if context.is_critical else "⚠️"
        level_text = "紧急" if context.is_critical else "告警"
        power = context.current_record.power

        return f"{level_emoji} 电量{level_text} - 剩余 {power:.1f} 度"

    def _build_alert_body(self, context: AlertContext) -> str:
        """构建告警邮件正文（HTML格式）"""
        # 准备趋势信息
        trend_text = "未知"
        trend_color = "gray"
        if context.trend is not None:
            if context.trend < -1:
                trend_text = f"快速下降 ({context.trend:.2f} 度/天)"
                trend_color = "red"
            elif context.trend < 0:
                trend_text = f"下降 ({context.trend:.2f} 度/天)"
                trend_color = "orange"
            else:
                trend_text = "稳定"
                trend_color = "green"

        # 准备剩余天数信息
        days_color = (
            "red"
            if context.estimated_days_remaining and context.estimated_days_remaining < 3
            else "orange"
        )

        # 准备模板数据
        template_data = {
            "level_emoji": "🔴" if context.is_critical else "⚠️",
            "level_text": "紧急" if context.is_critical else "告警",
            "alert_title": f"电量告警 - {context.alert_level.upper()}",
            "current_power": context.current_record.power,
            "threshold": context.threshold,
            "check_time": context.current_record.timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "trend": context.trend,
            "trend_text": trend_text,
            "trend_color": trend_color,
            "daily_consumption": context.daily_consumption,
            "estimated_days": context.estimated_days_remaining,
            "days_color": days_color,
            "history": context.history[:5],  # 最近5条记录
            "is_critical": context.is_critical,
        }

        # 渲染模板
        template = self.jinja_env.get_template("alert_email.html")
        return template.render(**template_data)

    def _send_email(self, subject: str, body: str) -> None:
        """发送邮件

        Args:
            subject: 邮件主题
            body: 邮件正文(HTML格式)

        Raises:
            NotificationError: 发送失败
        """
        try:
            # 创建邮件
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.config.smtp_user
            msg["To"] = ", ".join(self.config.recipients)

            # 添加 HTML 正文
            html_part = MIMEText(body, "html", "utf-8")
            msg.attach(html_part)

            # 连接 SMTP 服务器
            logger.debug(
                f"连接到 SMTP 服务器: {self.config.smtp_host}:{self.config.smtp_port}"
            )

            if self.config.smtp_use_tls:
                server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)

            # 登录
            server.login(self.config.smtp_user, self.config.smtp_password)

            # 发送邮件
            server.sendmail(
                self.config.smtp_user, self.config.recipients, msg.as_string()
            )

            server.quit()

        except smtplib.SMTPException as e:
            raise NotificationError(f"SMTP 错误: {e}") from e
        except Exception as e:
            raise NotificationError(f"发送邮件失败: {e}") from e
