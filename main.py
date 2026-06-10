"""
全自动营销号短视频生成工厂 - 主入口
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from loguru import logger
from workflows import TaskScheduler


def setup_logger():
    """配置日志"""
    logger.remove()  # 移除默认handler

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        level="INFO"
    )

    # 文件输出
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        rotation="00:00",  # 每天午夜轮转
        retention="7 days",  # 保留7天
        level="DEBUG",
        encoding="utf-8"
    )


def main():
    """主函数"""
    setup_logger()

    logger.info("="*60)
    logger.info("全自动营销号短视频生成工厂")
    logger.info("="*60)
    logger.info("项目目录: " + str(project_root))
    logger.info("")

    # 启动定时任务调度器
    scheduler = TaskScheduler()
    scheduler.setup_jobs()
    scheduler.start()


if __name__ == "__main__":
    main()
