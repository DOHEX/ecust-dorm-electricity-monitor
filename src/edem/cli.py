import typer
from .monitor import ElectricityMonitor

app = typer.Typer()
monitor_app = typer.Typer()
app.add_typer(monitor_app, name="monitor", help="电量监控")

monitor = ElectricityMonitor()


@monitor_app.command()
def start():
    """启动监控服务（持续输出日志，支持 Ctrl+C 退出）"""
    global monitor
    monitor = ElectricityMonitor()
    try:
        monitor.start()
    except (KeyboardInterrupt, SystemExit):
        monitor.stop()


@monitor_app.command()
def stop():
    """停止监控服务"""
    global monitor
    monitor.stop()


@app.command()
def query():
    """查询电量"""
    from .fetcher import get_electricity

    remain = get_electricity()
    print(f"剩余电量：{remain}")
