"""
自动化视频工厂 - 主入口
每日自动：爬取热点 → AI分析 → 生成30个视频 → 发布
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from automation.scheduler import SmartScheduler


def setup_logger():
    """配置日志"""
    logger.remove()

    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "automation_{time:YYYY-MM-DD}.log",
        rotation="00:00",
        retention="7 days",
        level="DEBUG",
        encoding="utf-8"
    )


class AutomationFactory:
    """自动化工厂"""

    def __init__(self):
        self.scheduler = SmartScheduler()
        self.aps_scheduler = BlockingScheduler()

    def setup_jobs(self):
        """设置定时任务"""
        # 每天凌晨1点：规划全天任务
        self.aps_scheduler.add_job(
            func=self.plan_daily,
            trigger=CronTrigger(hour=1, minute=0),
            id="plan_daily",
            name="规划每日30个视频任务",
            replace_existing=True
        )

        # 每天8/12/18/22点：执行对应时段任务
        for hour in [8, 12, 18, 22]:
            self.aps_scheduler.add_job(
                func=lambda h=hour: self.execute_slot(h),
                trigger=CronTrigger(hour=hour, minute=0),
                id=f"execute_{hour}",
                name=f"执行{hour}点时段任务",
                replace_existing=True
            )

        logger.info("定时任务设置完成")
        logger.info("- 01:00 规划全天任务")
        logger.info("- 08:00 执行上午时段")
        logger.info("- 12:00 执行中午时段")
        logger.info("- 18:00 执行傍晚时段")
        logger.info("- 22:00 执行晚间时段")

    def plan_daily(self):
        """凌晨规划任务"""
        try:
            logger.info("\n" + "=" * 80)
            logger.info("触发：每日任务规划")
            logger.info("=" * 80)

            tasks = self.scheduler.plan_daily_tasks()

            logger.info(f"✓ 规划完成: {len(tasks)} 个任务")

        except Exception as e:
            logger.error(f"✗ 规划失败: {e}", exc_info=True)

    def execute_slot(self, hour: int):
        """执行时段任务"""
        try:
            logger.info("\n" + "=" * 80)
            logger.info(f"触发：{hour}点时段执行")
            logger.info("=" * 80)

            self.scheduler.execute_tasks(hour)

        except Exception as e:
            logger.error(f"✗ 执行失败: {e}", exc_info=True)

    def start(self):
        """启动自动化工厂"""
        logger.info("\n" + "=" * 80)
        logger.info("自动化视频工厂启动")
        logger.info("=" * 80)
        logger.info(f"项目目录: {project_root}")
        logger.info("模式: 每日30个视频，8/12/18/22点发布")
        logger.info("")

        self.setup_jobs()

        logger.info("\n调度器已启动，等待定时触发...")
        logger.info("按 Ctrl+C 停止\n")

        try:
            self.aps_scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("\n调度器已停止")


def main():
    """主函数"""
    import os
    setup_logger()

    factory = AutomationFactory()

    # CI环境：立即执行一次完整流程
    if os.getenv("CI") == "true":
        logger.info("\n" + "=" * 80)
        logger.info("CI模式：立即执行完整流程")
        logger.info("=" * 80)

        try:
            # 1. 规划任务
            logger.info("\n[步骤1/2] 规划任务...")
            tasks = factory.scheduler.plan_daily_tasks()
            logger.info(f"✓ 规划完成: {len(tasks)} 个任务")

            # 2. 立即执行（不等待定时）
            logger.info("\n[步骤2/2] 执行任务...")
            factory.scheduler.execute_tasks(hour=None)  # None表示执行所有任务

            logger.info("\n" + "=" * 80)
            logger.info("CI执行完成")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"✗ CI执行失败: {e}", exc_info=True)
            sys.exit(1)
    else:
        # 本地环境：启动调度器
        factory.start()


if __name__ == "__main__":
    main()
