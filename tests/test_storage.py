"""测试 CSV 存储仓储"""

from datetime import datetime, timedelta

from ecust_electricity_monitor.models import ElectricityRecord
from ecust_electricity_monitor.storage import CSVRepository


class TestCSVRepository:
    """测试 CSV 存储仓储功能"""

    def test_create_file(self, test_csv_path):
        """测试创建 CSV 文件"""
        CSVRepository(test_csv_path)
        assert test_csv_path.exists()

    def test_save_record(self, test_csv_path):
        """测试保存记录"""
        storage = CSVRepository(test_csv_path)

        record = ElectricityRecord(
            timestamp=datetime.now(),
            power=50.0,
            alert_sent=False,
        )

        storage.save(record)
        assert storage.count() == 1

    def test_find_latest(self, test_csv_path):
        """测试获取最新记录"""
        storage = CSVRepository(test_csv_path)

        # 添加两条记录
        record1 = ElectricityRecord(
            timestamp=datetime.now() - timedelta(hours=1),
            power=40.0,
            alert_sent=False,
        )
        record2 = ElectricityRecord(
            timestamp=datetime.now(),
            power=50.0,
            alert_sent=False,
        )

        storage.save(record1)
        storage.save(record2)

        latest = storage.find_latest()
        assert latest is not None
        assert latest.power == 50.0

    def test_find_recent(self, test_csv_path):
        """测试获取最近记录"""
        storage = CSVRepository(test_csv_path)

        # 添加多条记录
        for i in range(10):
            record = ElectricityRecord(
                timestamp=datetime.now() - timedelta(hours=i),
                power=50.0 - i,
                alert_sent=False,
            )
            storage.save(record)

        recent = storage.find_recent(days=1)
        assert len(recent) == 10

    def test_delete_before(self, test_csv_path):
        """测试删除指定时间之前的记录"""
        storage = CSVRepository(test_csv_path)

        # 添加旧记录
        old_record = ElectricityRecord(
            timestamp=datetime.now() - timedelta(days=100),
            power=30.0,
            alert_sent=False,
        )

        # 添加新记录
        new_record = ElectricityRecord(
            timestamp=datetime.now(),
            power=50.0,
            alert_sent=False,
        )

        storage.save(old_record)
        storage.save(new_record)

        # 删除 90 天前的记录
        cutoff_time = datetime.now() - timedelta(days=90)
        deleted = storage.delete_before(cutoff_time)

        assert deleted == 1
        assert storage.count() == 1
