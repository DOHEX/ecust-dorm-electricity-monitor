"""CSV 存储实现

基于 CSV 文件的电量数据仓储实现。
"""

import csv
from datetime import datetime, timedelta
from pathlib import Path

from ..constants import TIMESTAMP_FORMAT, CSVColumn
from ..exceptions import StorageError
from ..logger import logger
from ..models import ElectricityRecord
from .base import ElectricityRepository


class CSVRepository(ElectricityRepository):
    """CSV 文件存储实现

    实现 ElectricityRepository 接口，使用 CSV 文件作为存储后端。
    """

    def __init__(self, csv_path: Path):
        """初始化 CSV 存储

        Args:
            csv_path: CSV 文件路径
        """
        self.csv_path = Path(csv_path)
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        """确保 CSV 文件和目录存在

        如果文件不存在，创建目录和文件并写入表头
        """
        try:
            # 创建父目录
            self.csv_path.parent.mkdir(parents=True, exist_ok=True)

            # 如果文件不存在，创建并写入表头
            if not self.csv_path.exists():
                with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                        [
                            CSVColumn.TIMESTAMP.value,
                            CSVColumn.POWER.value,
                            CSVColumn.ALERT_SENT.value,
                        ]
                    )
                logger.info(f"创建新的 CSV 文件: {self.csv_path}")
        except Exception as e:
            raise StorageError(f"创建 CSV 文件失败: {e}") from e

    def save(self, record: ElectricityRecord) -> None:
        """保存一条电量记录

        Args:
            record: 电量记录对象

        Raises:
            StorageError: 写入失败
        """
        try:
            with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(
                    [
                        record.timestamp.strftime(TIMESTAMP_FORMAT),
                        record.power,
                        record.alert_sent,
                    ]
                )
            logger.debug(f"记录已保存: {record.power} 度 @ {record.timestamp}")
        except Exception as e:
            raise StorageError(f"写入 CSV 文件失败: {e}") from e

    def find_latest(self) -> ElectricityRecord | None:
        """获取最新的电量记录

        Returns:
            最新记录，如果没有记录则返回 None

        Raises:
            StorageError: 查询失败
        """
        records = self.find_all(limit=1)
        return records[0] if records else None

    def find_all(
        self,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int | None = None,
    ) -> list[ElectricityRecord]:
        """查询电量记录

        Args:
            start_time: 开始时间（包含）
            end_time: 结束时间（包含）
            limit: 返回记录数量限制

        Returns:
            电量记录列表（按时间降序）

        Raises:
            StorageError: 查询失败
        """
        records = []

        try:
            if not self.csv_path.exists():
                return records

            with open(self.csv_path, encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    try:
                        # 解析时间
                        timestamp = datetime.strptime(
                            row[CSVColumn.TIMESTAMP.value], TIMESTAMP_FORMAT
                        )

                        # 时间过滤
                        if start_time and timestamp < start_time:
                            continue
                        if end_time and timestamp > end_time:
                            continue

                        # 创建记录对象
                        record = ElectricityRecord(
                            timestamp=timestamp,
                            power=float(row[CSVColumn.POWER.value]),
                            alert_sent=row[CSVColumn.ALERT_SENT.value].lower()
                            == "true",
                        )
                        records.append(record)

                    except (ValueError, KeyError) as e:
                        logger.warning(f"跳过无效记录: {row} - {e}")
                        continue

            # 按时间降序排序
            records.sort(key=lambda r: r.timestamp, reverse=True)

            # 应用数量限制
            if limit:
                records = records[:limit]

            logger.debug(f"读取了 {len(records)} 条记录")
            return records

        except Exception as e:
            raise StorageError(f"读取 CSV 文件失败: {e}") from e

    def find_recent(self, days: int) -> list[ElectricityRecord]:
        """获取最近 N 天的记录

        Args:
            days: 天数

        Returns:
            电量记录列表（按时间降序）

        Raises:
            StorageError: 查询失败
        """
        start_time = datetime.now() - timedelta(days=days)
        return self.find_all(start_time=start_time)

    def count(self) -> int:
        """统计总记录数

        Returns:
            记录总数

        Raises:
            StorageError: 查询失败
        """
        try:
            if not self.csv_path.exists():
                return 0

            with open(self.csv_path, encoding="utf-8") as f:
                # 减 1 是因为有表头行
                return sum(1 for _ in f) - 1
        except Exception as e:
            logger.error(f"统计记录数失败: {e}")
            return 0

    def delete_before(self, timestamp: datetime) -> int:
        """删除指定时间之前的记录

        Args:
            timestamp: 时间戳

        Returns:
            删除的记录数

        Raises:
            StorageError: 删除失败
        """
        try:
            # 读取所有记录
            all_records = self.find_all()

            # 过滤出要保留的记录
            records_to_keep = [r for r in all_records if r.timestamp >= timestamp]

            deleted_count = len(all_records) - len(records_to_keep)

            if deleted_count > 0:
                # 重写文件
                with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    # 写入表头
                    writer.writerow(
                        [
                            CSVColumn.TIMESTAMP.value,
                            CSVColumn.POWER.value,
                            CSVColumn.ALERT_SENT.value,
                        ]
                    )
                    # 写入保留的记录
                    for record in records_to_keep:
                        writer.writerow(
                            [
                                record.timestamp.strftime(TIMESTAMP_FORMAT),
                                record.power,
                                record.alert_sent,
                            ]
                        )

                logger.info(f"删除了 {deleted_count} 条记录（{timestamp} 之前）")

            return deleted_count

        except Exception as e:
            raise StorageError(f"删除记录失败: {e}") from e
