"""schedule 命令模块

职责：启动定时监控任务
"""

from typing import Annotated

import typer
from rich.panel import Panel

from ..analytics import PowerAnalyzer
from ..client import ElectricityClient
from ..config import config
from ..health import HealthMonitor
from ..logger import logger
from ..models import AlertContext, ElectricityRecord
from ..notifiers import NotificationManager
from ..scheduler import SchedulerService
from ..storage import CSVRepository
from .base import check_client_config, console


def schedule_command(
    interval: Annotated[
        int | None, typer.Option("--interval", "-i", help="检查间隔（秒，覆盖配置）")
    ] = None,
    daemon: Annotated[
        bool, typer.Option("--daemon", "-d", help="后台运行（需配合 nohup 等工具）")
    ] = False,
) -> None:
    """启动定时监控任务"""
    # 检查配置
    check_client_config()

    try:
        check_interval = interval or config.app.check_interval_seconds

        console.print(
            Panel.fit(
                f"[bold green]电量监控任务已启动[/bold green]\n\n"
                f"检查间隔: [cyan]{check_interval}[/cyan] 秒\n"
                f"告警阈值: [cyan]{config.app.alert_threshold}[/cyan] 度\n"
                f"数据存储: [cyan]{config.storage.csv_path}[/cyan]\n\n"
                f"按 [red]Ctrl+C[/red] 停止",
                title="⚡ emon scheduler",
            )
        )

        # 创建组件
        client = ElectricityClient(
            sysid=config.client.sysid,
            roomid=config.client.roomid,
            areaid=config.client.areaid,
            buildid=config.client.buildid,
            timeout=config.client.timeout_seconds,
            max_retries=config.client.max_retries,
        )
        storage = CSVRepository(config.storage.csv_path)
        notifier = NotificationManager(config.notification)
        health_monitor = HealthMonitor(max_consecutive_failures=5)

        def monitoring_task() -> None:
            """监控任务：获取、存储、告警"""
            try:
                # 获取电量
                result = client.fetch()

                if result.success:
                    # 记录成功
                    health_monitor.record_success()

                    # 创建记录
                    record = ElectricityRecord(
                        timestamp=result.timestamp,
                        power=result.power,
                        alert_sent=False,
                    )

                    # 存储
                    storage.save(record)

                    # 检查告警
                    if record.power < config.app.alert_threshold:
                        records = storage.find_recent(days=7)
                        analyzer = PowerAnalyzer(records)
                        trend = analyzer.calculate_trend()
                        daily = analyzer.calculate_daily_consumption()
                        days_left = analyzer.estimate_remaining_days()

                        alert_ctx = AlertContext(
                            current_record=record,
                            threshold=config.app.alert_threshold,
                            trend=trend,
                            history=records[:10],
                            daily_consumption=daily,
                            estimated_days_remaining=days_left,
                        )

                        if (
                            config.notification.is_configured
                            and notifier.should_send_alert(alert_ctx)
                        ):
                            notifier.send_power_alert(alert_ctx)
                else:
                    health_monitor.record_failure()

                    # 检查是否需要发送健康告警
                    if (
                        health_monitor.should_send_health_alert()
                        and config.notification.is_configured
                    ):
                        notifier.send_system_alert(
                            health_monitor.consecutive_failures,
                            health_monitor.last_success_time,
                        )
                        health_monitor.mark_alert_sent()

            except Exception as e:
                logger.error(f"监控任务失败: {e}")
                health_monitor.record_failure()

        # 创建调度器
        scheduler = SchedulerService()
        scheduler.schedule_job(
            job_func=monitoring_task,
            interval_seconds=check_interval,
            run_immediately=True,
        )

        # 启动
        scheduler.start()

    except KeyboardInterrupt as e:
        console.print("\n[yellow]✓ 调度器已停止[/yellow]")
        raise typer.Exit(0) from e
    except Exception as e:
        console.print(f"[red]✗ 调度器启动失败: {e}[/red]")
        raise typer.Exit(1) from e
