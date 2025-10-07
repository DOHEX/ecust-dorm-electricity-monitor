from loguru import logger
from playwright.sync_api import sync_playwright, Error, Page
from .config import settings
from types import SimpleNamespace


def fill_dorm_info(page: Page, dorm: SimpleNamespace) -> float | None:
    """自动填写宿舍信息并查询电量"""
    try:
        page.get_by_text("华理电控").click()
        for sel, val in [
            ("#elcarea", dorm.area),
            ("#elcdistrict", dorm.district),
            ("#elcbuis", dorm.building),
            ("#elcfloor", dorm.floor),
            ("#elcroom", dorm.room),
        ]:
            page.locator(sel).select_option(str(val))
            page.wait_for_timeout(500)
        page.locator("#queryBill").click()
        page.wait_for_timeout(500)
        remain = page.locator("#dumpEnergy").input_value()
        logger.success(f"查询成功，剩余电量：{remain}")
        return float(remain)
    except Exception as e:
        logger.error(f"填写宿舍信息或查询失败: {e}")
        return None


def get_electricity(settings=settings) -> float | None:
    """主流程：自动登录并查询电量，失败返回 None"""
    account = settings.account
    dorm = settings.dorm
    remain: float | None = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            if settings.vpn.enable:
                logger.info("使用VPN访问校园网...")
                page.goto(
                    "https://ykt-ecust-edu-cn-s.sslvpn.ecust.edu.cn:8118/epay/",
                    wait_until="networkidle",
                )
                logger.info(f"当前URL: {page.url}")
                if page.url.startswith("https://sslvpn.ecust.edu.cn"):
                    logger.info("sslvpn未登录，正在登录...")
                    page.locator("input.input-txt[tabindex='1']").fill(
                        str(settings.vpn.username)
                    )
                    page.locator("input.input-txt[tabindex='2']").fill(
                        str(settings.vpn.password)
                    )
                    page.locator(".checkbox__mark").click()
                    page.get_by_role("button", name="登录").click()
                    page.goto(
                        "https://ykt-ecust-edu-cn-s.sslvpn.ecust.edu.cn:8118/epay/",
                        wait_until="networkidle",
                    )
                    logger.info(f"登录后URL: {page.url}")
                if page.url.startswith(
                    "https://sso-ecust-edu-cn-s.sslvpn.ecust.edu.cn"
                ):
                    logger.info("统一认证未登录，正在登录...")
                    page.get_by_placeholder("用户名").fill(str(account.username))
                    page.get_by_placeholder("密码").fill(str(account.password))
                    page.get_by_role("button", name="登录").click()
                    page.wait_for_url(
                        "https://ykt-ecust-edu-cn-s.sslvpn.ecust.edu.cn:8118/epay/**"
                    )
                page.goto(
                    "https://ykt-ecust-edu-cn-s.sslvpn.ecust.edu.cn:8118/epay/electric/load4electricindex"
                )
            else:
                logger.info("直接访问校园网...")
                page.goto("https://ykt.ecust.edu.cn/epay/", wait_until="networkidle")
                logger.info(f"当前URL: {page.url}")
                if page.url.startswith("https://sso.ecust.edu.cn"):
                    logger.info("统一认证未登录，正在登录...")
                    page.get_by_placeholder("用户名").fill(str(account.username))
                    page.get_by_placeholder("密码").fill(str(account.password))
                    page.get_by_role("button", name="登录").click()
                    page.wait_for_url("https://ykt.ecust.edu.cn/epay/**")
                page.goto("https://ykt.ecust.edu.cn/epay/electric/load4electricindex")
            remain = fill_dorm_info(page, dorm)
        except Error:
            logger.error("无法打开校园网，请尝试使用vpn")
        except Exception as e:
            logger.error(f"查询电量流程异常: {e}")
    return remain
