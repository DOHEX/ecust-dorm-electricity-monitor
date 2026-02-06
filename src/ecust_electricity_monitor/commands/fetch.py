"""fetch 命令模块

职责：获取当前电量
"""

from typing import Annotated

import typer

from ..client import ElectricityClient
from ..config import config
from ..exceptions import ClientError
from ..logger import logger
from ..models import ElectricityRecord
from ..storage import CSVRepository
from .base import check_api_config, console
from .display import display_power_result


def fetch_command(
    save: Annotated[
        bool, typer.Option("--save/--no-save", help="是否保存到 CSV 文件")
    ] = True,
    verbose: Annotated[
        bool, typer.Option("--verbose", "-v", help="显示详细信息")
    ] = False,
) -> None:
    """获取当前电量"""
    # 检查配置
    check_api_config()

    try:
        # 创建客户端
        client = ElectricityClient(
            sysid=config.api.sysid,
            roomid=config.api.roomid,
            areaid=config.api.areaid,
            buildid=config.api.buildid,
            timeout=config.api.timeout_seconds,
            max_retries=config.api.max_retries,
        )

        console.print("[yellow]正在获取电量数据...[/yellow]")

        # 获取数据
        result = client.fetch()

        if not result.success:
            console.print(f"[red]✗ 获取失败: {result.error_message}[/red]")
            raise typer.Exit(1)

        # 创建记录
        record = ElectricityRecord(
            timestamp=result.timestamp,
            power=result.power,
            alert_sent=False,
        )

        # 保存到 CSV
        if save:
            storage = CSVRepository(config.storage.csv_path)
            storage.save(record)
            console.print("[green]✓ 数据已保存到 CSV[/green]")

        # 显示结果
        display_power_result(record, verbose)

    except ClientError as e:
        console.print(f"[red]✗ 获取电量失败: {e}[/red]")
        if verbose:
            logger.exception("详细错误信息:")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[red]✗ 发生错误: {e}[/red]")
        if verbose:
            logger.exception("详细错误信息:")
        raise typer.Exit(1) from e
