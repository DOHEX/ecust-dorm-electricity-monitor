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
            elif method == "serverchan":
                sendkey = getattr(settings.notify.serverchan, "sendkey", None)
                if not sendkey:
                    logger.warning("未配置 server酱 sendkey，无法推送")
                    continue
                if serverchan_notify(sendkey=sendkey, title=title, content=content):
                    success = True
            else:
                logger.warning(f"未知通知方式: {method}")
        except Exception as e:
            logger.error(f"通知方式 {method} 推送异常: {e}")
    return success


def pushplus_notify(token: str, title: str, content: str) -> bool:
    """通过 pushplus 推送消息"""
    url = "https://www.pushplus.plus/send"
    data = {"token": token, "title": title, "content": content}
    try:
        resp = requests.post(url, json=data, timeout=10)
        resp.raise_for_status()
        logger.success("📢 PushPlus 推送成功")
        return True
    except Exception as e:
        logger.error(f"PushPlus 推送失败: {e}")
        return False


def serverchan_notify(sendkey: str, title: str, content: str) -> bool:
    """通过 server酱 推送消息"""
    url = f"https://sctapi.ftqq.com/{sendkey}.send"
    data = {"title": title, "desp": content}
    try:
        resp = requests.post(url, data=data, timeout=10)
        resp.raise_for_status()
        if resp.json().get("code", -1) == 0:
            logger.success("📢 Server酱推送成功")
            return True
        else:
            logger.error(f"Server酱推送失败: {resp.text}")
            return False
    except Exception as e:
        logger.error(f"Server酱推送异常: {e}")
        return False


def email_notify(
    user: str,
    password: str,
    host: str,
    port: int,
    to: str,
    subject: str,
    body: str,
) -> bool:
    """发送邮件通知"""
    import yagmail

    try:
        yag = yagmail.SMTP(user=user, password=password, host=host, port=port)
        yag.send(to=to, subject=subject, contents=body)
        logger.success("📧 邮件发送成功")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {e}")
        return False
