"""init 命令模块

职责：交互式初始化配置文件
"""

from typing import Annotated

import typer
from rich.panel import Panel

from ..config import ENV_FILE, config
from .base import console


def init_command(
    force: Annotated[
        bool, typer.Option("--force", "-f", help="强制覆盖已有配置")
    ] = False,
) -> None:
    """交互式初始化配置文件"""

    # 检查配置文件是否已存在
    if ENV_FILE.exists() and not force:
        console.print(f"[yellow]⚠️  配置文件已存在: {ENV_FILE}[/yellow]")

        # 检查是否已完整配置
        if config.api.is_configured:
            console.print("[green]✓ 配置已完整，可以直接使用 `emon fetch` 测试[/green]")

            # 显示当前配置
            console.print("\n[dim]当前配置：[/dim]")
            console.print(f"  API__SYSID:   [cyan]{config.api.sysid}[/cyan]")
            console.print(f"  API__ROOMID:  [cyan]{config.api.roomid}[/cyan]")
            console.print(f"  API__AREAID:  [cyan]{config.api.areaid}[/cyan]")
            console.print(f"  API__BUILDID: [cyan]{config.api.buildid}[/cyan]")

            console.print("\n[dim]使用 [cyan]emon init --force[/cyan] 可重新配置[/dim]")
            raise typer.Exit(0)
        else:
            console.print("[yellow]配置不完整，继续引导...[/yellow]\n")

    # 显示欢迎信息
    console.print(
        Panel.fit(
            "[bold green]⚡ ECUST 电量监控系统初始化向导[/bold green]\n\n"
            "本向导将帮助你配置系统所需的参数。\n\n"
            "[dim]如何获取参数：[/dim]\n"
            "  1. 浏览器访问 ECUST 电费查询页面\n"
            "  2. 按 F12 打开开发者工具\n"
            "  3. 切换到 Network（网络）标签\n"
            "  4. 查询电费，观察请求中的参数",
            title="欢迎使用",
            border_style="green",
        )
    )

    console.print()

    # 交互式输入
    try:
        sysid = typer.prompt("系统ID (sysid)", default=config.api.sysid or "")
        roomid = typer.prompt("房间ID (roomid)", default=config.api.roomid or "")
        areaid = typer.prompt("区域ID (areaid)", default=config.api.areaid or "")
        buildid = typer.prompt("建筑ID (buildid)", default=config.api.buildid or "")

        # 验证输入
        if not all([sysid.strip(), roomid.strip(), areaid.strip(), buildid.strip()]):
            console.print("[red]✗ 所有参数都不能为空[/red]")
            raise typer.Exit(1)

        # 生成配置内容
        current_time = __import__("datetime").datetime.now()
        env_content = f"""# ⚡ ECUST 电量监控系统配置文件
# 由 emon init 自动生成于 {current_time.strftime("%Y-%m-%d %H:%M:%S")}

# =============================================================================
# ECUST API 配置（必填）
# =============================================================================

API__SYSID={sysid.strip()}
API__ROOMID={roomid.strip()}
API__AREAID={areaid.strip()}
API__BUILDID={buildid.strip()}

# =============================================================================
# 应用配置（可选）
# =============================================================================

# APP__ALERT_THRESHOLD_KWH=30.0
# APP__CHECK_INTERVAL_SECONDS=3600
# APP__LOG_LEVEL=INFO

# =============================================================================
# 邮件通知配置（可选）
# =============================================================================

# NOTIFICATION__CHANNELS=["email", "serverchan"]
# NOTIFICATION__SMTP_HOST=smtp.gmail.com
# NOTIFICATION__SMTP_PORT=587
# NOTIFICATION__SMTP_STARTTLS=true
# NOTIFICATION__SMTP_USER=your_email@gmail.com
# NOTIFICATION__SMTP_PASSWORD=your_app_password
# NOTIFICATION__RECIPIENTS=["recipient@example.com"]
"""

        # 写入文件
        ENV_FILE.write_text(env_content, encoding="utf-8")

        console.print()
        console.print(
            Panel.fit(
                f"[bold green]✓ 配置文件已创建[/bold green]\n\n"
                f"文件位置: [cyan]{ENV_FILE}[/cyan]\n\n"
                f"[dim]下一步：[/dim]\n"
                f"  1. 运行 [cyan]emon fetch[/cyan] 测试获取电量\n"
                f"  2. 运行 [cyan]emon info[/cyan] 查看系统状态\n"
                f"  3. （可选）配置邮件通知参数",
                title="配置完成",
                border_style="green",
            )
        )

    except KeyboardInterrupt as e:
        console.print("\n[yellow]配置已取消[/yellow]")
        raise typer.Exit(0) from e
    except Exception as e:
        console.print(f"[red]✗ 初始化失败: {e}[/red]")
        raise typer.Exit(1) from e
