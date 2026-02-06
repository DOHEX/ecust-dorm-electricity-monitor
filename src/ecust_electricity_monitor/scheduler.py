"""调度器模块

职责：
- 周期性执行数据采集任务
- 管理后台运行的定时任务
- 支持本地和服务器部署

遵循 SOLID 原则：
- 单一职责：只负责任务调度
- 依赖倒置：依赖抽象的回调函数
"""

import signal
import sys
from collections.abc import Callable
from datetime import datetime

import schedule

from .logger import logger


class SchedulerService:
    """调度器服务

    使用 schedule 库实现轻量级的定时任务调度。
    支持优雅退出和信号处理。
    """

    def __init__(self):
        """初始化调度器服务"""
        self._running = False
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """设置信号处理器

        捕获 SIGINT 和 SIGTERM，实现优雅退出
        """

        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，准备退出...")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def schedule_job(
        self,
        job_func: Callable[[], None],
        interval_seconds: int,
        run_immediately: bool = True,
    ) -> None:
        """调度任务

        Args:
            job_func: 要执行的函数
            interval_seconds: 执行间隔（秒）
            run_immediately: 是否立即执行一次
        """
        # 立即执行一次
        if run_immediately:
            logger.info("立即执行首次任务...")
            try:
                job_func()
            except Exception as e:
                logger.error(f"首次任务执行失败: {e}")

        # 设置周期性任务
        schedule.every(interval_seconds).seconds.do(self._wrap_job(job_func))

        logger.info(f"已调度任务: 每 {interval_seconds} 秒执行一次")

    def _wrap_job(self, job_func: Callable[[], None]) -> Callable[[], None]:
        """包装任务函数，添加异常处理和日志

        Args:
            job_func: 原始任务函数

        Returns:
            包装后的任务函数
        """

        def wrapped():
            start_time = datetime.now()
            logger.info(f"开始执行定时任务: {job_func.__name__}")

            try:
                job_func()

                duration = (datetime.now() - start_time).total_seconds()
                logger.info(f"定时任务执行成功，耗时 {duration:.2f} 秒")

            except Exception as e:
                duration = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"定时任务执行失败 (耗时 {duration:.2f} 秒): {e}", exc_info=True
                )

        return wrapped

    def start(self) -> None:
        """启动调度器

        开始运行调度循环，直到调用 stop() 或收到退出信号
        """
        if self._running:
            logger.warning("调度器已经在运行中")
            return

        self._running = True
        logger.info("调度器已启动，等待任务执行...")

        try:
            while self._running:
                # 运行所有待执行的任务
                schedule.run_pending()

                # 休眠 1 秒
                import time

                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到键盘中断，停止调度器")
        finally:
            self._running = False
            logger.info("调度器已停止")

    def stop(self) -> None:
        """停止调度器"""
        if self._running:
            logger.info("正在停止调度器...")
            self._running = False
        else:
            logger.warning("调度器未在运行")

    def clear_all(self) -> None:
        """清除所有已调度的任务"""
        schedule.clear()
        logger.info("已清除所有调度任务")

    @property
    def is_running(self) -> bool:
        """调度器是否正在运行"""
        return self._running

    @property
    def jobs_count(self) -> int:
        """当前调度的任务数量"""
        return len(schedule.jobs)

    def get_next_run_time(self) -> datetime | None:
        """获取下次任务执行时间

        Returns:
            下次执行时间，如果没有任务则返回 None
        """
        if not schedule.jobs:
            return None

        next_job = schedule.next_run()
        return next_job


def create_monitoring_job(
    fetch_func: Callable[[], float],
    storage_func: Callable[[float], None],
    alert_func: Callable[[float], None] | None = None,
) -> Callable[[], None]:
    """创建监控任务

    工厂函数，用于创建组合的监控任务。

    Args:
        fetch_func: 获取电量的函数
        storage_func: 存储数据的函数
        alert_func: 告警检查函数（可选）

    Returns:
        组合后的任务函数
    """

    def monitoring_job():
        """监控任务：获取 -> 存储 -> 告警"""
        try:
            # 1. 获取电量
            power = fetch_func()
            logger.debug(f"获取到电量: {power} 度")

            # 2. 存储数据
            storage_func(power)
            logger.debug("数据已存储")

            # 3. 检查告警
            if alert_func:
                alert_func(power)
                logger.debug("告警检查完成")

        except Exception as e:
            logger.error(f"监控任务执行失败: {e}")
            raise

    return monitoring_job
