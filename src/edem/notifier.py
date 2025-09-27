import requests
from loguru import logger
from .config import settings


def notify(title: str, content: str, settings=settings) -> bool:
    """多渠道通知，任一成功即返回 True"""
    methods = getattr(settings.notify, "methods", [])
    if not methods:
        logger.warning("未配置通知方式，无法推送消息")
        return False
    success = False
    for method in methods:
        try:
            if method == "pushplus":
                token = getattr(settings.notify.pushplus, "token", None)
                if not token:
                    logger.warning("未配置 pushplus token，无法推送")
                    continue
                if pushplus_notify(token=token, title=title, content=content):
                    success = True
            else:
                logger.warning(f"未知通知方式: {method}")
        except Exception as e:
            logger.error(f"通知方式 {method} 推送异常: {e}")
    return success


def pushplus_notify(token: str, title: str, content: str) -> bool:
    """通过 pushplus 推送消息"""
    url = "https://www.pushplus.plus/send"
    data = {
        "token": token,
        "title": title,
        "content": content,
    }
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        logger.success("📢 PushPlus 推送成功")
        return True
    except Exception as e:
        logger.error(f"PushPlus 推送失败: {e}")
        return False
