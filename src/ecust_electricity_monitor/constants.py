"""常量定义 - Constants"""

from enum import Enum
from pathlib import Path

# API 端点
ELECTRICITY_API_URL = "https://ykt.ecust.edu.cn/epay/wxpage/wanxiao/eleresult"


# CSV 列名枚举
class CSVColumn(str, Enum):
    """CSV 文件列名"""

    TIMESTAMP = "timestamp"
    POWER = "power"
    ALERT_SENT = "alert_sent"


# 数据验证范围
MIN_POWER_VALUE = 0.0
MAX_POWER_VALUE = 999.0

# 默认目录路径（相对于项目根目录）
DEFAULT_DATA_DIR = Path("data")
DEFAULT_OUTPUT_DIR = Path("output/reports")
DEFAULT_LOG_DIR = Path("logs")

# 告警配置
DEFAULT_ALERT_THRESHOLD = 10.0  # 度

# 重试配置
MAX_RETRIES = 3
RETRY_BACKOFF_FACTOR = 2  # 指数退避因子

# 日志配置
DEFAULT_LOG_ROTATION = "500 MB"
DEFAULT_LOG_RETENTION = "7 days"

# 时间格式
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
ISO_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%S%z"
