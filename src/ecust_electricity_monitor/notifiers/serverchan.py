"""Server酱通知器

通过 Server酱 服务推送消息到微信。
"""

from datetime import datetime

import requests

from ..logger import logger
from ..models import AlertContext
from .base import BaseNotifier


class ServerChanNotifier(BaseNotifier):
    """Server酱通知器

    通过 Server酱 Turbo 版 API 将消息推送到微信。
    支持 Markdown 格式内容。
    """

    # Server酱 Turbo 版 API
    API_URL = "https://sctapi.ftqq.com/{sendkey}.send"

    def __init__(self, sendkey: str):
        """初始化 Server酱 通知器

        Args:
            sendkey: Server酱的SendKey
        """
        self.sendkey = sendkey

    @property
    def name(self) -> str:
        """通知器名称"""
        return "Server酱"

    def is_available(self) -> bool:
        """检查是否可用"""
        return bool(self.sendkey)

    def send_power_alert(self, context: AlertContext) -> bool:
        """发送电量告警

        Args:
            context: 告警上下文

        Returns:
            发送是否成功
        """
        if not self.is_available():
            logger.warning("Server酱未配置，跳过发送")
            return False

        level_emoji = "🔴" if context.is_critical else "⚠️"
        level_text = "紧急告警" if context.is_critical else "低电提醒"
        power = context.current_record.power
        threshold = context.threshold

        title = f"{level_emoji} 宿舍电量{level_text}"

        # 构建 Markdown 内容
        check_time = context.current_record.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        content_parts = [
            f"## ⚡ 当前电量：{power:.1f} 度",
            f"**告警阈值：** {threshold:.1f} 度",
            f"**检测时间：** {check_time}",
            "",
        ]

        # 添加趋势信息
        if context.trend is not None:
            trend_text = f"{context.trend:.2f} 度/天"
            if context.trend < -1:
                content_parts.append(f"📉 **电量趋势：** 快速下降 ({trend_text})")
            elif context.trend < 0:
                content_parts.append(f"📊 **电量趋势：** 下降 ({trend_text})")
            else:
                content_parts.append("📈 **电量趋势：** 稳定")

        # 添加日均消耗
        if context.daily_consumption:
            content_parts.append(
                f"💡 **日均消耗：** {context.daily_consumption:.2f} 度/天"
            )

        # 添加预计剩余天数
        if context.estimated_days_remaining:
            content_parts.append(
                f"⏱️ **预计剩余：** {context.estimated_days_remaining} 天"
            )

        # 添加提示信息
        if context.is_critical:
            content_parts.extend(["", "---", "**⚠️ 请及时充值，避免断电！**"])

        content = "\n\n".join(content_parts)
        return self._send_message(title, content)

    def send_system_alert(
        self, consecutive_failures: int, last_success_time: datetime | None
    ) -> bool:
        """发送系统异常告警

        Args:
            consecutive_failures: 连续失败次数
            last_success_time: 最后成功时间

        Returns:
            发送是否成功
        """
        if not self.is_available():
            logger.warning("Server酱未配置，跳过发送")
            return False

        title = "⚠️ 电量监控系统异常"

        content_parts = [
            f"## 系统连续失败 {consecutive_failures} 次",
            "",
            f"**告警时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ]

        if last_success_time:
            content_parts.append(
                f"**最后成功：** {last_success_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )

        content_parts.extend(
            [
                "",
                "**可能原因：**",
                "- 网络连接问题",
                "- ECUST API 服务异常",
                "- 配置参数错误",
                "",
                "请检查日志并及时处理！",
            ]
        )

        content = "\n\n".join(content_parts)
        return self._send_message(title, content)

    def _send_message(self, title: str, content: str) -> bool:
        """发送消息到微信

        Args:
            title: 消息标题
            content: 消息内容（支持Markdown）

        Returns:
            发送是否成功
        """
        try:
            url = self.API_URL.format(sendkey=self.sendkey)
            data = {"title": title, "desp": content}

            response = requests.post(url, data=data, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("code") == 0:
                logger.info(f"Server酱推送成功: {title}")
                return True
            else:
                error_msg = result.get("message", "未知错误")
                logger.error(f"Server酱推送失败: {error_msg}")
                return False

        except requests.RequestException as e:
            logger.error(f"Server酱推送请求失败: {e}")
            return False
        except Exception as e:
            logger.error(f"Server酱推送异常: {e}")
            return False
