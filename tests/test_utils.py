"""测试分析工具函数"""

from datetime import datetime, timedelta

import pytest

from ecust_electricity_monitor.analytics import PowerAnalyzer, validate_power_value
from ecust_electricity_monitor.exceptions import ValidationError
from ecust_electricity_monitor.models import ElectricityRecord


class TestValidation:
    """测试验证函数"""

    def test_validate_power_valid(self):
        """测试有效电量值"""
        assert validate_power_value(50.0) == 50.0
        assert validate_power_value(0) == 0
        assert validate_power_value(999) == 999

    def test_validate_power_invalid(self):
        """测试无效电量值"""
        with pytest.raises(ValidationError):
            validate_power_value(-1)

        with pytest.raises(ValidationError):
            validate_power_value(1000)


class TestPowerAnalyzer:
    """测试 PowerAnalyzer 类"""

    def test_calculate_trend(self):
        """测试趋势计算"""
        records = [
            ElectricityRecord(
                timestamp=datetime.now(),
                power=40.0,
                alert_sent=False,
            ),
            ElectricityRecord(
                timestamp=datetime.now() - timedelta(hours=24),
                power=50.0,
                alert_sent=False,
            ),
        ]

        analyzer = PowerAnalyzer(records)
        trend = analyzer.calculate_trend()
        assert trend is not None
        assert trend < 0  # 电量在降低

    def test_calculate_daily_consumption(self):
        """测试日均消耗计算"""
        records = [
            ElectricityRecord(
                timestamp=datetime.now(),
                power=30.0,
                alert_sent=False,
            ),
            ElectricityRecord(
                timestamp=datetime.now() - timedelta(days=7),
                power=100.0,
                alert_sent=False,
            ),
        ]

        analyzer = PowerAnalyzer(records)
        consumption = analyzer.calculate_daily_consumption(days=7)
        assert consumption is not None
        assert consumption == pytest.approx(10.0, rel=0.1)  # 约 10度/天

    def test_estimate_remaining_days(self):
        """测试剩余天数估算"""
        records = [
            ElectricityRecord(
                timestamp=datetime.now(),
                power=30.0,
                alert_sent=False,
            ),
            ElectricityRecord(
                timestamp=datetime.now() - timedelta(days=7),
                power=100.0,
                alert_sent=False,
            ),
        ]
        
        analyzer = PowerAnalyzer(records)
        days = analyzer.estimate_remaining_days()
        assert days is not None
        assert days > 0

    def test_get_statistics(self):
        """测试统计计算"""
        records = [
            ElectricityRecord(timestamp=datetime.now(), power=50.0, alert_sent=False),
            ElectricityRecord(timestamp=datetime.now(), power=40.0, alert_sent=False),
            ElectricityRecord(timestamp=datetime.now(), power=30.0, alert_sent=False),
        ]

        analyzer = PowerAnalyzer(records)
        stats = analyzer.get_statistics()

        assert stats["total_records"] == 3
        assert stats["min_power"] == 30.0
        assert stats["max_power"] == 50.0
        assert stats["average_power"] == 40.0
