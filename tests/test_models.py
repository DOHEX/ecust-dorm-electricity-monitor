"""测试数据模型"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from ecust_electricity_monitor.models import (
    AlertContext,
    ElectricityRecord,
    FetchResult,
    ReportData,
)


class TestElectricityRecord:
    """测试 ElectricityRecord 模型"""

    def test_valid_record(self):
        """测试有效记录"""
        record = ElectricityRecord(
            timestamp=datetime.now(),
            power=50.5,
            alert_sent=False,
        )
        assert record.power == 50.5
        assert record.alert_sent is False

    def test_power_validation_min(self):
        """测试电量最小值验证"""
        with pytest.raises(ValidationError):
            ElectricityRecord(
                timestamp=datetime.now(),
                power=-1,
                alert_sent=False,
            )

    def test_power_validation_max(self):
        """测试电量最大值验证"""
        with pytest.raises(ValidationError):
            ElectricityRecord(
                timestamp=datetime.now(),
                power=1000,
                alert_sent=False,
            )


class TestFetchResult:
    """测试 FetchResult 模型"""

    def test_success_result(self):
        """测试成功结果"""
        result = FetchResult(
            power=50.0,
            timestamp=datetime.now(),
            source="test",
            success=True,
        )
        assert result.success is True
        assert result.power == 50.0

    def test_failure_result(self):
        """测试失败结果"""
        result = FetchResult(
            power=0.0,
            timestamp=datetime.now(),
            source="test",
            success=False,
            error_message="Test error",
        )
        assert result.success is False
        assert result.error_message == "Test error"


class TestAlertContext:
    """测试 AlertContext 模型"""

    def test_critical_alert(self):
        """测试紧急告警"""
        record = ElectricityRecord(
            timestamp=datetime.now(),
            power=5.0,
            alert_sent=False,
        )

        context = AlertContext(
            current_record=record,
            threshold=30.0,
            history=[record],
        )

        assert context.is_critical is True
        assert context.alert_level == "critical"

    def test_warning_alert(self):
        """测试普通告警"""
        record = ElectricityRecord(
            timestamp=datetime.now(),
            power=20.0,
            alert_sent=False,
        )

        context = AlertContext(
            current_record=record,
            threshold=30.0,
            history=[record],
        )

        assert context.is_critical is False
        assert context.alert_level == "warning"


class TestReportData:
    """测试 ReportData 模型"""

    def test_statistics(self):
        """测试统计计算"""
        records = [
            ElectricityRecord(timestamp=datetime.now(), power=50.0, alert_sent=False),
            ElectricityRecord(timestamp=datetime.now(), power=40.0, alert_sent=False),
            ElectricityRecord(timestamp=datetime.now(), power=30.0, alert_sent=False),
        ]

        report = ReportData(
            records=records,
            statistics={"current_power": 50.0, "avg_power": 40.0},
            metadata={"threshold": "30.0", "analysis_period": "7"},
        )

        assert report.total_records == 3
        assert report.average_power == 40.0
        assert report.min_power == 30.0
        assert report.max_power == 50.0
