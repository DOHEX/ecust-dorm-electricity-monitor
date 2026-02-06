"""命令基础设施模块

提供所有命令共享的基础功能：
- Rich console 实例
- 配置检查函数
- 版本回调
"""

import typer
from rich.console import Console
from rich.panel import Panel

from .. import __version__
from ..config import ENV_FILE, config

# 全局 Rich console 实例
console = Console()


def check_api_config() -> None:
    """检查 API 配置是否完整

    Raises:
        typer.Exit: 如果配置不完整，显示错误信息并退出
    """
    if not config.api.is_configured:
        console.print(
            Panel.fit(
                "[bold red]⚠️  配置不完整[/bold red]\n\n"
                f"请先配置以下必需参数：\n"
                f"  • API__SYSID    - 系统ID\n"
                f"  • API__ROOMID   - 房间ID\n"
                f"  • API__AREAID   - 区域ID\n"
                f"  • API__BUILDID  - 建筑ID\n\n"
                f"[dim]配置方式（任选其一）：[/dim]\n"
                f"  1. 运行 [cyan]emon init[/cyan] 交互式配置\n"
                f"  2. 编辑 [cyan]{ENV_FILE}[/cyan] 文件\n"
                f"  3. 设置环境变量（推荐 CI/CD）\n\n"
                f"[dim]获取参数方法：[/dim]\n"
                f"  浏览器访问 ECUST 电费查询页面\n"
                f"  按 F12 打开开发者工具\n"
                f"  查看网络请求中的参数",
                title="配置错误",
                border_style="red",
            )
        )
        raise typer.Exit(1)


def version_callback(value: bool) -> None:
    """显示版本信息回调

    Args:
        value: 是否显示版本

    Raises:
        typer.Exit: 显示版本后退出
    """
    if value:
        console.print(
            f"[bold green]emon[/bold green] version [cyan]{__version__}[/cyan]"
        )
        raise typer.Exit()
