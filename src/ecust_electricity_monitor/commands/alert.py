"""alert 命令模块

职责：检查电量并发送告警
"""

from typing import Annotated

import typer

from ..analytics import PowerAnalyzer
from ..config import config
from ..models import AlertContext
from ..notifiers import NotificationManager
from ..storage import CSVRepository
from .base import console
from .display import display_alert_info


def alert_command(
    send_email: Annotated[
        bool, typer.Option("--send/--no-send", help="是否发送邮件告警")
    ] = True,
    threshold: Annotated[
        float | None, typer.Option("--threshold", "-t", help="告警阈值（覆盖配置）")
    ] = None,
) -> None:
    """检查电量并发送告警"""
    try:
        # 读取历史数据
        storage = CSVRepository(config.storage.csv_path)
        records = storage.find_recent(days=7)

        if not records:
            console.print("[yellow]⚠ 没有历史数据，请先运行 `emon fetch`[/yellow]")
            return

        current_record = records[0]
        alert_threshold = threshold or config.app.alert_threshold_kwh

        # 检查是否需要告警
        if current_record.power > alert_threshold:
            console.print(
                f"[green]✓ 电量充足: {current_record.power:.1f} 度 "
                f"(阈值: {alert_threshold} 度)[/green]"
            )
            return  # ✅ 改为 return

        # 计算告警上下文
        analyzer = PowerAnalyzer(records)
        trend = analyzer.calculate_trend()
        daily_consumption = analyzer.calculate_daily_consumption()
        estimated_days = analyzer.estimate_remaining_days()

        alert_context = AlertContext(
            current_record=current_record,
            threshold=alert_threshold,
            trend=trend,
            history=records[:10],
            daily_consumption=daily_consumption,
            estimated_days_remaining=estimated_days,
        )

        # 显示告警信息
        display_alert_info(alert_context)

        # 发送告警通知
        if send_email and config.notification.is_configured:
            try:
                notifier = NotificationManager(config.notification)

                if notifier.should_send_alert(alert_context):
                    console.print("[yellow]正在发送告警通知...[/yellow]")
                    notifier.send_power_alert(alert_context)
                    console.print("[green]✓ 告警通知已发送[/green]")
                else:
                    console.print("[dim]ℹ 在冷却时间内，跳过通知发送[/dim]")
            except Exception as notify_error:
                console.print(f"[yellow]⚠ 通知发送失败: {notify_error}[/yellow]")
                # 不中断主流程，只记录警告
        elif not config.notification.is_configured:
            console.print("[yellow]⚠ 通知未配置，跳过发送[/yellow]")

    except Exception as e:
        console.print(f"[red]✗ 告警检查失败: {e}[/red]")
        import traceback

        console.print(f"[dim]调试信息:\n{traceback.format_exc()}[/dim]")
        raise typer.Exit(1) from e
