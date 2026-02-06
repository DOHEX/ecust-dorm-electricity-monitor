"""显示辅助函数模块

提供格式化输出函数：
- 电量结果显示
- 告警信息显示
"""

from rich.panel import Panel

from ..models import AlertContext, ElectricityRecord
from .base import console


def display_power_result(record: ElectricityRecord, verbose: bool = False) -> None:
    """显示电量结果

    Args:
        record: 电量记录
        verbose: 是否显示详细信息
    """
    # 确定颜色
    if record.power < 20:
        color = "red"
        icon = "🔴"
    elif record.power < 50:
        color = "yellow"
        icon = "🟡"
    else:
        color = "green"
        icon = "🟢"

    console.print(
        Panel.fit(
            f"[bold {color}]{icon} {record.power:.2f} 度[/bold {color}]\n\n"
            f"[dim]时间: {record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}[/dim]",
            title="⚡ 当前电量",
        )
    )

    if verbose:
        console.print(f"\n[dim]详细信息:\n{record}[/dim]")


def display_alert_info(context: AlertContext) -> None:
    """显示告警信息

    Args:
        context: 告警上下文
    """
    icon = "🔴" if context.is_critical else "⚠️"
    level_text = "紧急告警" if context.is_critical else "低电量告警"

    info_lines = [
        f"[bold red]{icon} {level_text}[/bold red]\n",
        f"剩余电量: [bold]{context.current_record.power:.2f} 度[/bold]",
        f"告警阈值: {context.threshold} 度",
        f"告警等级: [yellow]{context.alert_level.upper()}[/yellow]",
    ]

    if context.trend is not None:
        trend_text = f"{context.trend:.2f} 度/天"
        trend_color = "red" if context.trend < -1 else "yellow"
        info_lines.append(f"用电趋势: [{trend_color}]{trend_text}[/{trend_color}]")

    if context.daily_consumption is not None:
        info_lines.append(f"日均消耗: {context.daily_consumption:.2f} 度/天")

    if context.estimated_days_remaining is not None:
        days = context.estimated_days_remaining
        days_color = "red" if days < 3 else "yellow"
        info_lines.append(f"预计可用: [{days_color}]{days} 天[/{days_color}]")

    console.print(Panel("\n".join(info_lines), title="⚠️ 告警信息"))
