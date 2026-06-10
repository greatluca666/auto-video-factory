"""
定时任务调度器
使用APScheduler实现自动化触发
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from loguru import logger
from datetime import datetime

from plan_a_text_video import PlanAWorkflow
from shared.config import config


class TaskScheduler:
    """任务调度器"""

    def __init__(self):
        self.scheduler = BlockingScheduler()
        self.plan_a = PlanAWorkflow()

    def setup_jobs(self):
        """配置定时任务"""

        # 任务1: 每2小时采集热点并生成视频 (方案A)
        # 执行时间: 00:00, 02:00, 04:00, ..., 22:00
        self.scheduler.add_job(
            func=self.run_plan_a_batch,
            trigger=CronTrigger(hour="*/2"),
            id="plan_a_batch",
            name="方案A批量生成",
            max_instances=1,
            replace_existing=True
        )
        logger.info("已添加任务: 方案A批量生成 (每2小时)")

        # 任务2: 每天固定时段生成视频 (高峰期)
        # 执行时间: 08:00, 12:00, 18:00, 22:00
        peak_hours = [8, 12, 18, 22]
        for hour in peak_hours:
            self.scheduler.add_job(
                func=self.run_plan_a_peak,
                trigger=CronTrigger(hour=hour, minute=0),
                id=f"plan_a_peak_{hour}",
                name=f"方案A高峰期生成 ({hour}:00)",
                max_instances=1,
                replace_existing=True
            )
        logger.info(f"已添加任务: 方案A高峰期生成 ({peak_hours})")

        # 任务3: 每天凌晨清理旧文件
        self.scheduler.add_job(
            func=self.cleanup_old_files,
            trigger=CronTrigger(hour=3, minute=0),
            id="cleanup",
            name="清理旧文件",
            max_instances=1,
            replace_existing=True
        )
        logger.info("已添加任务: 清理旧文件 (每天03:00)")

    def run_plan_a_batch(self):
        """方案A批量生成 (常规)"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"定时任务触发: 方案A批量生成")
            logger.info(f"触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}\n")

            # 采集10条热搜，生成情绪共鸣风格视频
            stats = self.plan_a.run(
                hotspot_limit=10,
                styles=["情绪共鸣"]
            )

            logger.info(f"\n任务完成: {stats}")

        except Exception as e:
            logger.error(f"方案A批量生成失败: {e}")

    def run_plan_a_peak(self):
        """方案A高峰期生成 (多风格)"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"定时任务触发: 方案A高峰期生成")
            logger.info(f"触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}\n")

            # 采集15条热搜，生成3种风格视频
            stats = self.plan_a.run(
                hotspot_limit=15,
                styles=["情绪共鸣", "干货清单", "故事悬念"]
            )

            logger.info(f"\n任务完成: {stats}")

        except Exception as e:
            logger.error(f"方案A高峰期生成失败: {e}")

    def cleanup_old_files(self):
        """清理7天前的视频文件"""
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"定时任务触发: 清理旧文件")
            logger.info(f"触发时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"{'='*60}\n")

            import time
            from pathlib import Path

            video_dir = config.working_dir / "videos"
            if not video_dir.exists():
                logger.info("视频目录不存在，跳过清理")
                return

            now = time.time()
            seven_days_ago = now - (7 * 24 * 60 * 60)
            deleted_count = 0

            for video_file in video_dir.glob("*.mp4"):
                if video_file.stat().st_mtime < seven_days_ago:
                    video_file.unlink()
                    deleted_count += 1
                    logger.info(f"删除旧文件: {video_file.name}")

            logger.info(f"清理完成，删除 {deleted_count} 个文件")

        except Exception as e:
            logger.error(f"清理旧文件失败: {e}")

    def start(self):
        """启动调度器"""
        logger.info("\n" + "="*60)
        logger.info("定时任务调度器启动")
        logger.info("="*60)

        # 打印所有任务
        jobs = self.scheduler.get_jobs()
        logger.info(f"\n已配置 {len(jobs)} 个定时任务:")
        for job in jobs:
            logger.info(f"  - {job.name} (ID: {job.id})")
            logger.info(f"    触发器: {job.trigger}")

        logger.info("\n调度器运行中... (按Ctrl+C停止)\n")

        try:
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("\n调度器已停止")


def main():
    """启动调度器"""
    scheduler = TaskScheduler()
    scheduler.setup_jobs()
    scheduler.start()


if __name__ == "__main__":
    main()
