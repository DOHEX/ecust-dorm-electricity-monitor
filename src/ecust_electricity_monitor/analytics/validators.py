"""数据验证模块

提供电量数据验证功能。
"""

from ..constants import MAX_POWER_VALUE, MIN_POWER_VALUE
from ..exceptions import ValidationError


def validate_power_value(power: float) -> float:
    """验证电量值是否在合理范围内

    Args:
        power: 电量值

    Returns:
        验证后的电量值

    Raises:
        ValidationError: 电量值超出范围
    """
    if not MIN_POWER_VALUE <= power <= MAX_POWER_VALUE:
        raise ValidationError(
            f"电量值 {power} 不在有效范围 [{MIN_POWER_VALUE}, {MAX_POWER_VALUE}] 内"
        )
    return power
