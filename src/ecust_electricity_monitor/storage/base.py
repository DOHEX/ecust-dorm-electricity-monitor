"""存储层抽象接口

定义电量数据仓储的抽象接口。
遵循依赖倒置原则（DIP），业务逻辑依赖抽象而非具体实现。
"""

from abc import ABC, abstractmethod
from datetime import datetime

from ..models import ElectricityRecord


class ElectricityRepository(ABC):
    """电量数据仓储抽象接口

    定义电量数据存储的标准操作接口。
    具体实现可以是 CSV、SQLite、PostgreSQL 等。
    """

    @abstractmethod
    def save(self, record: ElectricityRecord) -> None:
        """保存一条电量记录

        Args:
            record: 电量记录对象

        Raises:
            StorageError: 保存失败
        """
        pass

    @abstractmethod
    def find_latest(self) -> ElectricityRecord | None:
        """获取最新的电量记录

        Returns:
            最新记录，如果没有记录则返回 None

        Raises:
            StorageError: 查询失败
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def find_recent(self, days: int) -> list[ElectricityRecord]:
        """获取最近 N 天的记录

        Args:
            days: 天数

        Returns:
            电量记录列表（按时间降序）

        Raises:
            StorageError: 查询失败
        """
        pass

    @abstractmethod
    def count(self) -> int:
        """统计总记录数

        Returns:
            记录总数

        Raises:
            StorageError: 查询失败
        """
        pass

    @abstractmethod
    def delete_before(self, timestamp: datetime) -> int:
        """删除指定时间之前的记录

        Args:
            timestamp: 时间戳

        Returns:
            删除的记录数

        Raises:
            StorageError: 删除失败
        """
        pass
