"""电量数据分析器

提供面向对象的数据分析功能：
- 趋势分析
- 消耗计算
- 统计分析
- 剩余天数估算
"""

from datetime import timedelta

from ..models import ElectricityRecord


class PowerAnalyzer:
    """电量数据分析器

    提供电量数据的分析功能，包括趋势、消耗、统计等。

    使用方式:
        analyzer = PowerAnalyzer(records)
        trend = analyzer.calculate_trend()
        daily = analyzer.calculate_daily_consumption()
        stats = analyzer.get_statistics()
    """

    def __init__(self, records: list[ElectricityRecord]):
        """初始化分析器

        Args:
            records: 电量记录列表（按时间降序排序）
        """
        self.records = records

    def calculate_trend(self, window_size: int = 5) -> float | None:
        """计算电量变化趋势（单位：度/天）

        使用简单线性回归计算趋势。正值表示增加，负值表示减少。

        Args:
            window_size: 用于计算趋势的记录数量

        Returns:
            电量变化趋势（度/天），如果数据不足则返回 None
        """
        if len(self.records) < 2:
            return None

        # 取最近的 N 条记录
        recent = self.records[:window_size]
        if len(recent) < 2:
            return None

        # 计算时间跨度（天）
        time_span = (recent[0].timestamp - recent[-1].timestamp).total_seconds() / 86400
        if time_span == 0:
            return None

        # 计算电量变化
        power_change = recent[0].power - recent[-1].power

        # 返回每天的变化率
        return power_change / time_span

    def calculate_daily_consumption(self, days: int = 7) -> float | None:
        """计算日均电量消耗

        Args:
            days: 统计天数

        Returns:
            日均消耗（度/天），如果数据不足则返回 None
        """
        if not self.records:
            return None

        # 找到 N 天前的记录
        cutoff_time = self.records[0].timestamp - timedelta(days=days)

        # 过滤出时间范围内的记录
        period_records = [r for r in self.records if r.timestamp >= cutoff_time]

        if len(period_records) < 2:
            return None

        # 计算实际时间跨度
        time_span = (
            period_records[0].timestamp - period_records[-1].timestamp
        ).total_seconds() / 86400
        if time_span == 0:
            return None

        # 计算消耗
        consumption = period_records[-1].power - period_records[0].power

        return abs(consumption) / time_span

    def estimate_remaining_days(self, current_power: float | None = None) -> int | None:
        """估算剩余可用天数

        Args:
            current_power: 当前剩余电量（不提供则使用最新记录）

        Returns:
            估算剩余天数，如果无法估算则返回 None
        """
        # 获取当前电量
        if current_power is None:
            if not self.records:
                return None
            current_power = self.records[0].power

        # 计算日均消耗
        daily_consumption = self.calculate_daily_consumption()

        if daily_consumption is None or daily_consumption <= 0:
            return None

        return int(current_power / daily_consumption)

    def get_statistics(self) -> dict:
        """计算电量统计信息

        Returns:
            统计信息字典
        """
        if not self.records:
            return {
                "total_records": 0,
                "min_power": None,
                "max_power": None,
                "average_power": None,
                "current_power": None,
            }

        powers = [r.power for r in self.records]

        return {
            "total_records": len(self.records),
            "min_power": min(powers),
            "max_power": max(powers),
            "average_power": sum(powers) / len(powers),
            "current_power": self.records[0].power,
        }
