"""数据模型 - Data Models using Pydantic"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .constants import MAX_POWER_VALUE, MIN_POWER_VALUE


class ElectricityRecord(BaseModel):
    """电量记录模型"""

    timestamp: datetime = Field(description="记录时间戳")
    power: float = Field(
        ge=MIN_POWER_VALUE, le=MAX_POWER_VALUE, description="剩余电量（度）"
    )
    alert_sent: bool = Field(default=False, description="是否已发送告警")

    @field_validator("power")
    @classmethod
    def validate_power(cls, v: float) -> float:
        """验证电量值"""
        if v < MIN_POWER_VALUE:
            raise ValueError(f"电量不能小于 {MIN_POWER_VALUE}")
        if v > MAX_POWER_VALUE:
            raise ValueError(f"电量不能大于 {MAX_POWER_VALUE}")
        return round(v, 2)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "timestamp": "2024-02-05T08:00:00",
                "power": 25.5,
                "alert_sent": False,
            }
        }
    )


class FetchResult(BaseModel):
    """电量获取结果模型"""

    power: float = Field(description="获取到的电量值")
    timestamp: datetime = Field(description="获取时间")
    source: str = Field(default="ecust-api", description="数据来源")
    raw_response: str | None = Field(default=None, description="原始响应（调试用）")
    success: bool = Field(default=True, description="是否成功")
    error_message: str | None = Field(default=None, description="错误消息")

    @field_validator("power")
    @classmethod
    def validate_power(cls, v: float) -> float:
        """验证电量值"""
        if v < MIN_POWER_VALUE or v > MAX_POWER_VALUE:
            raise ValueError(
                f"电量值 {v} 超出有效范围 [{MIN_POWER_VALUE}, {MAX_POWER_VALUE}]"
            )
        return round(v, 2)


class AlertContext(BaseModel):
    """告警上下文模型"""

    current_record: ElectricityRecord = Field(description="当前电量记录")
    threshold: float = Field(description="告警阈值")
    trend: float | None = Field(default=None, description="电量趋势（度/天）")
    history: list[ElectricityRecord] = Field(
        default_factory=list, description="历史记录"
    )
    daily_consumption: float | None = Field(default=None, description="日均消耗")
    estimated_days_remaining: float | None = Field(
        default=None, description="预估剩余天数"
    )

    @property
    def is_critical(self) -> bool:
        """是否为严重告警（低于阈值的50%）"""
        return self.current_record.power < (self.threshold * 0.5)

    @property
    def alert_level(self) -> str:
        """告警级别"""
        if self.is_critical:
            return "critical"
        elif self.current_record.power < self.threshold:
            return "warning"
        return "normal"


class ReportData(BaseModel):
    """报告数据模型"""

    records: list[ElectricityRecord] = Field(description="电量记录列表")
    statistics: dict[str, float] = Field(default_factory=dict, description="统计数据")
    metadata: dict[str, str] = Field(default_factory=dict, description="元数据")
    start_date: datetime | None = Field(default=None, description="开始日期")
    end_date: datetime | None = Field(default=None, description="结束日期")

    @property
    def total_records(self) -> int:
        """总记录数"""
        return len(self.records)

    @property
    def average_power(self) -> float:
        """平均电量"""
        if not self.records:
            return 0.0
        return round(sum(r.power for r in self.records) / len(self.records), 2)

    @property
    def min_power(self) -> float:
        """最低电量"""
        if not self.records:
            return 0.0
        return min(r.power for r in self.records)

    @property
    def max_power(self) -> float:
        """最高电量"""
        if not self.records:
            return 0.0
        return max(r.power for r in self.records)
