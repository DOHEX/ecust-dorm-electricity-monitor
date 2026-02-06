"""自定义异常类 - Custom Exceptions"""



class ElectricityMonitorError(Exception):
    """基础异常类 - Base exception for all electricity monitor errors"""

    pass


class ClientError(ElectricityMonitorError):
    """电量客户端异常"""

    def __init__(
        self,
        message: str,
        retry_count: int = 0,
        original_exception: Exception | None = None,
        response_text: str | None = None,
    ):
        self.retry_count = retry_count
        self.original_exception = original_exception
        self.response_text = response_text
        super().__init__(message)

    def __str__(self):
        base_msg = super().__str__()
        if self.retry_count > 0:
            base_msg += f" (重试次数: {self.retry_count})"
        if self.original_exception:
            base_msg += f" | 原始错误: {str(self.original_exception)}"
        return base_msg


class StorageError(ElectricityMonitorError):
    """CSV 存储失败异常"""

    pass


class NotificationError(ElectricityMonitorError):
    """通知发送失败异常（不应中断数据保存）"""

    pass


class ConfigurationError(ElectricityMonitorError):
    """配置错误异常"""

    pass


class ValidationError(ElectricityMonitorError):
    """数据验证失败异常"""

    pass
