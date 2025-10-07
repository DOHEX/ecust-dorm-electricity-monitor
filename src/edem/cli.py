import typer
from .monitor import ElectricityMonitor
from rich import print
from rich.panel import Panel


app = typer.Typer()
monitor_app = typer.Typer()
app.add_typer(monitor_app, name="monitor", help="电量监控")

monitor = ElectricityMonitor()


@monitor_app.command()
def start() -> None:
    """启动监控服务（持续输出日志，支持 Ctrl+C 退出）"""
    global monitor
    monitor = ElectricityMonitor()
    try:
        monitor.start()
    except (KeyboardInterrupt, SystemExit):
        monitor.stop()


@monitor_app.command()
def stop() -> None:
    """停止监控服务"""
    global monitor
    monitor.stop()


@app.command()
def query() -> None:
    """查询电量"""
    from .fetcher import get_electricity

    remain = get_electricity()
    if remain is None:
        print(
            Panel(
                "查询失败，请稍后重试",
                title="电费查询",
                subtitle="ECUST",
                style="bold red",
            )
        )
    else:
        print(
            Panel(
                f"当前剩余电量：{remain}",
                title="电费查询",
                subtitle="ECUST",
                style="bold cyan",
            )
        )


@app.command()
def webpanel(host: str = "127.0.0.1", port: int = 8000) -> None:
    """启动在线管理面板 (FastAPI)"""
    import uvicorn

    uvicorn.run("edem.webpanel:app", host=host, port=port, reload=True)
