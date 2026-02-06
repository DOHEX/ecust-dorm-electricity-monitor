"""电量数据分析模块

提供电量数据分析功能：
- 数据验证
- 趋势分析
- 消耗计算
- 统计分析
- 时间处理

核心组件:
    PowerAnalyzer: 面向对象的数据分析器，提供完整的分析功能
    validate_power_value: 电量值验证
    时间工具: format_timestamp, get_date_range, parse_timestamp

示例:
    from ecust_electricity_monitor.analytics import PowerAnalyzer

    analyzer = PowerAnalyzer(records)
    trend = analyzer.calculate_trend()
    daily = analyzer.calculate_daily_consumption()
    stats = analyzer.get_statistics()
    remaining_days = analyzer.estimate_remaining_days()
"""

from .datetime_utils import format_timestamp, get_date_range, parse_timestamp
from .power_analyzer import PowerAnalyzer
from .validators import validate_power_value

__all__ = [
    "PowerAnalyzer",
    "validate_power_value",
    "format_timestamp",
    "get_date_range",
    "parse_timestamp",
]
