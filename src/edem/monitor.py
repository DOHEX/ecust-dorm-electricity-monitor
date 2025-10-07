import csv
import os
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from apscheduler.triggers.cron import CronTrigger
import threading
from .fetcher import get_electricity
from .notifier import notify
from .config import settings
from loguru import logger


class ElectricityMonitor:
    def __init__(self, settings=settings):
        self.settings = settings
        self.scheduler = BackgroundScheduler()
        self._exit_event = threading.Event()
        self.setup_scheduler()

    def setup_scheduler(self) -> None:
        """设置调度器事件监听"""
        self.scheduler.add_listener(self.job_success_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self.job_error_listener, EVENT_JOB_ERROR)

    def job_success_listener(self, event) -> None:
        """任务成功监听，并输出下次任务执行时间"""
        logger.success(f"✅ 任务执行成功，任务ID: {event.job_id}")
        job = self.scheduler.get_job(event.job_id)
        if job and job.next_run_time:
            logger.info(f"⏰ 下次任务执行时间: {job.next_run_time}")
        else:
            logger.warning("⚠️ 无下次任务执行时间（可能为一次性任务或已被移除）")

    def job_error_listener(self, event) -> None:
        """任务失败监听"""
        logger.error(
            f"❌ 任务执行失败，任务ID: {event.job_id}，错误: {event.exception}"
        )

    def check_electricity(self) -> float | None:
        """带重试机制的电费查询，并在低于阈值时推送通知"""
        import time

        for attempt in range(self.settings.query.max_retries):
            try:
                result = get_electricity()
                if result is not None:
                    logger.success(f"✅ 电费查询成功: {result}")
                    threshold = float(getattr(self.settings.monitor, "threshold", 10.0))
                    if result < threshold:
                        title = "电费预警"
                        content = f"当前剩余电量：{result}，已低于阈值 {threshold}，请及时充值。"
                        notify(title, content)
                    return result
                else:
                    logger.warning(f"⚠️ 第{attempt + 1}次查询结果为空")
            except Exception as e:
                logger.error(f"❌ 第{attempt + 1}次查询失败: {e}")
            if attempt < self.settings.query.max_retries - 1:
                time.sleep(self.settings.query.retry_delay)
        return None

    def record_electricity_snapshot(self) -> None:
        """记录当前剩余电量快照到 CSV 文件"""
        value = get_electricity()
        now = datetime.now()
        file = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "../../electricity_snapshot.csv")
        )
        is_new = not os.path.exists(file)
        with open(file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if is_new:
                writer.writerow(["date", "electricity"])
            writer.writerow([now.date(), value])
        logger.info(f"📊 已记录电量快照: {now.date()} {value}")

    def add_job(self, cron_expr: str) -> None:
        """添加定时任务"""
        trigger = CronTrigger.from_crontab(cron_expr)
        self.scheduler.add_job(self.check_electricity, trigger=trigger)
        logger.success(f"🗓️  已添加定时任务，cron 表达式: {cron_expr}")

    def setup_default_schedules(self) -> None:
        """设置默认调度任务"""
        cron_expr = self.settings.monitor.cron
        self.add_job(cron_expr=cron_expr)
        # 如果开启了每日快照，额外添加每天0点快照任务
        if getattr(self.settings.monitor, "record_daily_snapshot", False):
            self.scheduler.add_job(
                self.record_electricity_snapshot, trigger=CronTrigger(hour=0, minute=0)
            )
            logger.success("🗓️  已添加每日0点电量快照任务")

    def start(self) -> None:
        """启动监控"""
        import time

        if not self.scheduler.running:
            self.setup_default_schedules()
            logger.success("🚀 电费监控服务已启动")
            self.scheduler.start()
            try:
                while not self._exit_event.is_set():
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                self.stop()
        else:
            logger.warning("⚠️ 监控服务已经在运行中")

    def stop(self) -> None:
        """停止监控"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self._exit_event.set()
            logger.success("🛑 电费监控服务已停止")
        else:
            logger.warning("⚠️ 监控服务未在运行")
