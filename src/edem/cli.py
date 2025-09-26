import typer
from .config import settings
app=typer.Typer()

@app.command()
def start():
    pass

@app.command()
def query():
    """查询电量"""
    from .scraper import get_electricity
    remain=get_electricity(settings)
    print(f"剩余电量：{remain}")