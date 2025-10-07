from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import polars as pl
import os
from .config import settings

from .fetcher import get_electricity

app = FastAPI()

static_dir = os.path.join(os.path.dirname(__file__), "static")
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=templates_dir)


def find_project_root(marker: str = "pyproject.toml") -> str:
    path = os.path.abspath(os.path.dirname(__file__))
    while True:
        if os.path.exists(os.path.join(path, marker)):
            return path
        new_path = os.path.dirname(path)
        if new_path == path:
            break
        path = new_path
    raise RuntimeError("项目根目录未找到")


project_root = find_project_root()
csv_path = os.path.join(project_root, "electricity_snapshot.csv")


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request) -> HTMLResponse:
    usage_data = []
    if os.path.exists(csv_path):
        df = pl.read_csv(csv_path)
        df = df.sort_values("date")
        df["usage"] = df["electricity"].shift(1) - df["electricity"]
        df["usage"] = df["usage"].apply(lambda x: x if x > 0 else 0)
        usage_data = df[["date", "usage"]].dropna().values.tolist()
    recharge_url = (
        "https://ykt-ecust-edu-cn-s.sslvpn.ecust.edu.cn:8118/epay/"
        if settings.vpn.enable
        else "https://ykt.ecust.edu.cn/epay/"
    )
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "usage_data": usage_data,
            "recharge_url": recharge_url,
        },
    )


@app.get("/api/remain")
def api_remain() -> dict:
    try:
        remain = get_electricity()
        return {"success": True, "remain": remain}
    except Exception as e:
        return {"success": False, "msg": str(e), "remain": None}
