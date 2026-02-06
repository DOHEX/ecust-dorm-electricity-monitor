"""report 命令模块

职责：生成电量分析报告
"""

from pathlib import Path
from typing import Annotated

import typer

from ..analytics import PowerAnalyzer
from ..config import config
from ..models import ReportData
from ..reporter import HTMLReporter
from ..storage import CSVRepository
from .base import console


def report_command(
    days: Annotated[int, typer.Option("--days", "-d", help="分析最近 N 天的数据")] = 7,
    output: Annotated[
        Path | None, typer.Option("--output", "-o", help="输出文件路径")
    ] = None,
    open_browser: Annotated[
        bool, typer.Option("--open/--no-open", help="生成后是否打开浏览器")
    ] = True,
) -> None:
    """生成电量分析报告"""
    try:
        # 读取数据
        storage = CSVRepository(config.storage.csv_path)
        records = storage.find_recent(days=days)

        if not records:
            console.print("[yellow]⚠ 没有数据，请先运行 `emon fetch`[/yellow]")
            raise typer.Exit(0)

        console.print(
            f"[yellow]正在分析最近 {days} 天的数据 ({len(records)} 条记录)...[/yellow]"
        )

        # 准备报告数据
        analyzer = PowerAnalyzer(records)
        statistics = analyzer.get_statistics()

        report_data = ReportData(
            records=records,
            statistics=statistics,
            metadata={
                "threshold": str(config.app.alert_threshold_kwh),
                "analysis_period": str(days),
            },
        )

        # 生成报告
        reporter = HTMLReporter(config.report.output_path)

        filename = output.name if output else None
        report_path = reporter.generate(report_data, filename=filename)

        console.print(f"[green]✓ 报告已生成: {report_path}[/green]")

        # 打开浏览器
        if open_browser:
            import webbrowser

            webbrowser.open(report_path.as_uri())

    except Exception as e:
        console.print(f"[red]✗ 生成报告失败: {e}[/red]")
        raise typer.Exit(1) from e
