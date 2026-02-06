"""存储层包

基于 Repository Pattern 的电量数据存储抽象层。

架构设计：
- ElectricityRepository: 抽象仓储接口，定义标准操作
- CSVRepository: CSV 文件存储实现
- get_repository: 工厂函数，动态创建仓储实例

SOLID 原则：
- 依赖倒置 (DIP): 业务逻辑依赖抽象接口而非具体实现
- 开闭原则 (OCP): 扩展新存储后端无需修改现有代码
- 单一职责 (SRP): 每个仓储实现专注一种存储方式

使用示例:
    from ecust_electricity_monitor.storage import CSVRepository

    # 直接使用具体实现
    repo = CSVRepository(csv_path)
    repo.save(record)
    records = repo.find_all()
    latest = repo.find_latest()

    # 或使用工厂函数
    from ecust_electricity_monitor.storage import get_repository
    repo = get_repository("csv", csv_path=csv_path)
"""

from pathlib import Path
from typing import Literal

from .base import ElectricityRepository
from .csv_repository import CSVRepository


def get_repository(
    storage_type: Literal["csv"] = "csv", csv_path: Path | None = None
) -> ElectricityRepository:
    """创建存储仓储实例（工厂函数）

    Args:
        storage_type: 存储类型，目前支持 "csv"
        csv_path: CSV 文件路径（storage_type="csv" 时必需）

    Returns:
        存储仓储实例

    Raises:
        ValueError: 不支持的存储类型或缺少必需参数

    Example:
        >>> repo = get_repository("csv", csv_path=Path("data/records.csv"))
        >>> repo.save(record)
    """
    if storage_type == "csv":
        if csv_path is None:
            raise ValueError("CSV storage requires csv_path parameter")
        return CSVRepository(csv_path)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")


__all__ = [
    "ElectricityRepository",
    "CSVRepository",
    "get_repository",
]
