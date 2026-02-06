"""通知器抽象基类

定义所有通知器的统一接口规范。
"""

from abc import ABC, abstractmethod
from datetime import datetime

from ..models import AlertContext


class BaseNotifier(ABC):
    """通知器抽象基类

    所有通知器必须实现此接口。
    遵循策略模式，确保接口一致性。
    """

    @abstractmethod
    def send_power_alert(self, context: AlertContext) -> bool:
        """发送电量告警

        Args:
            context: 告警上下文

        Returns:
            发送是否成功
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查通知器是否可用

        Returns:
            是否已正确配置且可用
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """通知器名称

        Returns:
            通知器的友好名称（用于日志）
        """
        pass
