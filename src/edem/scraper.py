from playwright.sync_api import sync_playwright
from .config import settings


def get_electricity(settings=settings) -> float:
    account = settings.account
    dorm = settings.dorm

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        try:
            page.goto("https://ykt.ecust.edu.cn/epay/", wait_until="networkidle")
            final_url = page.url
            if final_url.startswith("https://sso.ecust.edu.cn"):
                page.get_by_placeholder("用户名").fill(account.username)
                page.get_by_placeholder("密码").fill(account.password)
                page.get_by_role("button", name="登录").click()
                page.wait_for_url("https://ykt.ecust.edu.cn/epay/**")
            page.goto("https://ykt.ecust.edu.cn/epay/electric/load4electricindex")
            page.get_by_text('华理电控').click()
            page.locator("#elcarea").select_option(str(dorm.area))
            page.wait_for_timeout(1000)
            page.locator("#elcdistrict").select_option(str(dorm.district))
            page.wait_for_timeout(1000)
            page.locator("#elcbuis").select_option(str(dorm.building))
            page.wait_for_timeout(1000)
            page.locator("#elcfloor").select_option(str(dorm.floor))
            page.wait_for_timeout(1000)
            page.locator("#elcroom").select_option(str(dorm.room))
            page.wait_for_timeout(1000)
            page.locator("#queryBill").click()
            page.wait_for_timeout(1000)
            remain = page.locator("#dumpEnergy").input_value()
        except Exception as e:
            print(e)
    return float(remain)
