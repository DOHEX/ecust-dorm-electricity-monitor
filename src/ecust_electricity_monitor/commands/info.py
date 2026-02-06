"""info 命令模块

职责：显示配置和状态信息
"""

import sys

from rich.table import Table

from .. import __version__
from ..config import config
from ..storage import CSVRepository
from .base import console


def info_command() -> None:
    """显示配置和状态信息"""
    try:
        # 配置信息
        config_table = Table(
            title="⚙️  配置信息", show_header=True, header_style="bold cyan"
        )
        config_table.add_column("配置项", style="dim")
        config_table.add_column("值")

        config_table.add_row("告警阈值", f"{config.app.alert_threshold_kwh} 度")
        config_table.add_row("检查间隔", f"{config.app.check_interval_seconds} 秒")
        config_table.add_row("日志级别", config.app.log_level)
        config_table.add_row("数据目录", str(config.storage.data_dir))
        config_table.add_row("CSV 文件", str(config.storage.csv_path))
        config_table.add_row(
            "邮件通知", "已配置" if config.notification.is_configured else "未配置"
        )

        console.print(config_table)

        # 数据统计
        try:
            storage = CSVRepository(config.storage.csv_path)
            total_count = storage.count()
            latest = storage.find_latest()

            stats_table = Table(
                title="📊 数据统计", show_header=True, header_style="bold green"
            )
            stats_table.add_column("统计项", style="dim")
            stats_table.add_column("值")

            stats_table.add_row("总记录数", str(total_count))

            if latest:
                stats_table.add_row("最新电量", f"{latest.power:.2f} 度")
                stats_table.add_row(
                    "最新时间", latest.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                )

                # 状态
                status = (
                    "🔴 低电量"
                    if latest.power < config.app.alert_threshold_kwh
                    else "🟢 正常"
                )
                stats_table.add_row("当前状态", status)

            console.print(stats_table)

        except Exception as e:
            console.print(f"[yellow]⚠ 读取数据失败: {e}[/yellow]")

        # 系统信息
        sys_table = Table(
            title="🖥️  系统信息", show_header=True, header_style="bold magenta"
        )
        sys_table.add_column("信息项", style="dim")
        sys_table.add_column("值")

        sys_table.add_row("版本", __version__)
        sys_table.add_row(
            "Python",
            f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )

        console.print(sys_table)

    except Exception as e:
        console.print(f"[red]✗ 显示信息失败: {e}[/red]")
        import typer

        raise typer.Exit(1) from e
