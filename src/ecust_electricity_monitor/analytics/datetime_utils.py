"""时间处理工具模块

提供时间格式化、解析等功能。
"""

from datetime import datetime, timedelta

from ..constants import TIMESTAMP_FORMAT
from ..exceptions import ValidationError


def get_date_range(days: int) -> tuple[datetime, datetime]:
    """获取日期范围

    Args:
        days: 过去的天数

    Returns:
        (开始时间, 结束时间)
    """
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    return start_time, end_time


def format_timestamp(dt: datetime, format_str: str = TIMESTAMP_FORMAT) -> str:
    """格式化时间戳

    Args:
        dt: 时间对象
        format_str: 格式字符串

    Returns:
        格式化后的时间字符串
    """
    return dt.strftime(format_str)


def parse_timestamp(timestamp_str: str, format_str: str = TIMESTAMP_FORMAT) -> datetime:
    """解析时间字符串

    Args:
        timestamp_str: 时间字符串
        format_str: 格式字符串

    Returns:
        时间对象

    Raises:
        ValidationError: 时间格式错误
    """
    try:
        return datetime.strptime(timestamp_str, format_str)
    except ValueError as e:
        raise ValidationError(f"无效的时间格式: {timestamp_str}") from e
