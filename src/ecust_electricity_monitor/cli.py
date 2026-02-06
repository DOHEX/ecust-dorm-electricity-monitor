"""命令行接口主入口

职责：
- 定义 Typer 应用实例
- 注册所有命令
- 提供全局回调和初始化

由 commands 包提供所有命令实现，遵循模块化和单一职责原则。
"""

from typing import Annotated

import typer

from .commands import (
    alert_command,
    fetch_command,
    info_command,
    init_command,
    report_command,
    schedule_command,
    version_callback,
)
from .config import ROOT_DIR, config
from .logger import setup_logging

# 创建 Typer 应用
app = typer.Typer(
    name="emon",
    help="⚡ ECUST 宿舍电量监控系统",
    add_completion=False,
)


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="显示版本信息",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
) -> None:
    """⚡ ECUST 宿舍电量监控系统"""
    # 初始化日志
    setup_logging(
        log_level=config.app.log_level,
        log_dir=ROOT_DIR / config.storage.data_dir / "logs",
    )


# 注册命令
app.command(name="fetch")(fetch_command)
app.command(name="alert")(alert_command)
app.command(name="report")(report_command)
app.command(name="schedule")(schedule_command)
app.command(name="init")(init_command)
app.command(name="info")(info_command)


if __name__ == "__main__":
    app()
