"""健康监控模块

职责：
- 追踪系统运行状态
- 监控连续失败次数
- 判断是否需要发送告警

遵循 SOLID 原则：
- 单一职责：只负责健康状态监控
- 依赖倒置：依赖抽象（可配置的阈值）
"""

from datetime import datetime

from .logger import logger


class HealthMonitor:
    """健康监控器

    追踪系统运行健康状态，包括：
    - 连续失败次数
    - 最后成功时间
    - 是否需要发送健康告警
    """

    def __init__(self, max_consecutive_failures: int = 5):
        """初始化健康监控器

        Args:
            max_consecutive_failures: 触发健康告警的连续失败次数阈值
        """
        self.max_consecutive_failures = max_consecutive_failures
        self.consecutive_failures = 0
        self.last_success_time: datetime | None = None
        self.last_failure_time: datetime | None = None
        self._alert_sent = False

    def record_success(self) -> None:
        """记录成功事件

        重置失败计数，更新最后成功时间
        """
        self.consecutive_failures = 0
        self.last_success_time = datetime.now()
        self._alert_sent = False

        logger.debug("健康检查：成功，重置失败计数")

    def record_failure(self) -> None:
        """记录失败事件

        增加失败计数，更新最后失败时间
        """
        self.consecutive_failures += 1
        self.last_failure_time = datetime.now()

        logger.warning(
            f"健康检查：失败 "
            f"({self.consecutive_failures}/{self.max_consecutive_failures})"
        )

    def should_send_health_alert(self) -> bool:
        """判断是否应该发送健康告警

        Returns:
            如果连续失败次数超过阈值且未发送过告警，返回 True
        """
        return bool(
            self.consecutive_failures >= self.max_consecutive_failures
            and not self._alert_sent
        )

    def mark_alert_sent(self) -> None:
        """标记健康告警已发送

        避免重复发送相同告警
        """
        self._alert_sent = True
        logger.info(f"健康告警已发送（连续失败 {self.consecutive_failures} 次）")

    @property
    def is_healthy(self) -> bool:
        """系统是否健康

        Returns:
            如果连续失败次数小于阈值，返回 True
        """
        return self.consecutive_failures < self.max_consecutive_failures

    @property
    def status(self) -> dict:
        """获取健康状态摘要

        Returns:
            包含健康状态信息的字典
        """
        return {
            "is_healthy": self.is_healthy,
            "consecutive_failures": self.consecutive_failures,
            "max_consecutive_failures": self.max_consecutive_failures,
            "last_success_time": self.last_success_time.isoformat()
            if self.last_success_time
            else None,
            "last_failure_time": self.last_failure_time.isoformat()
            if self.last_failure_time
            else None,
            "alert_sent": self._alert_sent,
        }

    def get_uptime_hours(self) -> float | None:
        """获取距离上次成功的小时数

        Returns:
            距离上次成功的小时数，如果从未成功则返回 None
        """
        if self.last_success_time is None:
            return None

        delta = datetime.now() - self.last_success_time
        return delta.total_seconds() / 3600
