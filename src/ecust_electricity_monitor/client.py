"""电量客户端模块

职责：
- 从 ECUST API 获取电量数据
- 解析 HTML 响应
- 重试机制和错误处理

遵循 SOLID 原则：
- 单一职责：只负责数据获取
- 开闭原则：可扩展支持不同的数据源
- 依赖倒置：返回 FetchResult 抽象模型
"""

import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .constants import (
    ELECTRICITY_API_URL,
)
from .constants import (
    MAX_RETRIES as DEFAULT_MAX_RETRIES,
)
from .constants import (
    RETRY_BACKOFF_FACTOR as DEFAULT_RETRY_BACKOFF_FACTOR,
)
from .exceptions import ClientError, ValidationError
from .logger import logger
from .models import FetchResult


class ElectricityClient:
    """电量数据客户端

    从 ECUST 电费查询系统获取宿舍剩余电量。
    支持重试和指数退避策略。
    """

    def __init__(
        self,
        sysid: str,
        roomid: str,
        areaid: str,
        buildid: str,
        timeout: int = 10,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_factor: float = DEFAULT_RETRY_BACKOFF_FACTOR,
    ):
        """初始化电量客户端

        Args:
            sysid: 系统 ID
            roomid: 房间 ID
            areaid: 区域 ID
            buildid: 建筑 ID
            timeout: 请求超时时间（秒）
            max_retries: 最大重试次数
            backoff_factor: 指数退避因子
        """
        self.sysid = sysid
        self.roomid = roomid
        self.areaid = areaid
        self.buildid = buildid
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def fetch(self) -> FetchResult:
        """获取电量数据

        使用指数退避重试策略。

        Returns:
            FetchResult 对象，包含电量值或错误信息
        """
        last_exception: Exception | None = None
        last_response_text: str | None = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"尝试获取电量数据 (第 {attempt + 1}/{self.max_retries + 1} 次)"
                )

                # 构造请求参数
                params = {
                    "sysid": self.sysid,
                    "roomid": self.roomid,
                    "areaid": self.areaid,
                    "buildid": self.buildid,
                }

                # 发送 GET 请求
                response = requests.get(
                    ELECTRICITY_API_URL,
                    params=params,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                last_response_text = response.text

                # 解析 HTML
                power = self._parse_power_from_html(response.text)

                # 验证电量值
                from .analytics import validate_power_value

                validate_power_value(power)

                # 成功返回
                logger.info(f"成功获取电量: {power} 度")
                return FetchResult(
                    power=power,
                    timestamp=datetime.now(),
                    source=ELECTRICITY_API_URL,
                    raw_response=response.text[:500],  # 只保存前500字符
                    success=True,
                )

            except (requests.RequestException, ValidationError, ValueError) as e:
                last_exception = e
                logger.warning(f"获取电量失败 (第 {attempt + 1} 次): {e}")

                # 如果还有重试机会，等待后重试
                if attempt < self.max_retries:
                    wait_time = self.backoff_factor * (2**attempt)
                    logger.debug(f"等待 {wait_time:.1f} 秒后重试...")
                    time.sleep(wait_time)
                else:
                    # 所有重试都失败，返回失败结果
                    logger.error(
                        f"获取电量失败，已达最大重试次数 ({self.max_retries + 1})"
                    )
                    raise ClientError(
                        message=f"获取电量失败: {last_exception}",
                        retry_count=self.max_retries + 1,
                        original_exception=last_exception,
                        response_text=last_response_text,
                    ) from last_exception

        # 理论上不会到达这里
        raise ClientError(
            message="未知错误",
            retry_count=self.max_retries + 1,
        )

    def _parse_power_from_html(self, html: str) -> float:
        """从 HTML 中解析电量值

        Args:
            html: HTML 响应文本

        Returns:
            电量值（度）

        Raises:
            ValueError: 解析失败
        """
        try:
            soup = BeautifulSoup(html, "lxml")

            # 查找 id="roomdef" 的 input 元素
            roomdef = soup.find("input", id="roomdef")

            if not roomdef:
                raise ValueError("未找到 id='roomdef' 的元素")

            # 获取 left-degree 属性
            left_degree = roomdef.get("left-degree")

            if left_degree is None:
                raise ValueError("未找到 'left-degree' 属性")

            # 转换为浮点数
            power = float(left_degree)

            return power

        except Exception as e:
            raise ValueError(f"解析 HTML 失败: {e}") from e

    def test_connection(self) -> bool:
        """测试 API 连接

        Returns:
            连接是否成功
        """
        try:
            result = self.fetch()
            return result.success
        except Exception:
            return False
