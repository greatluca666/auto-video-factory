"""
方案A: 低成本文字口播流水线
主流程编排 - 热点采集 -> 文案生成 -> 视频生成 -> 发布
"""
from typing import List, Dict, Optional
from loguru import logger
from pathlib import Path

from plan_a_text_video.hotspot_crawler import WeiboHotspotCrawler
from plan_a_text_video.script_generator import ScriptGenerator
from plan_a_text_video.video_generator import VideoGenerator
from plan_a_text_video.publisher import Publisher
from shared.config import config


class PlanAWorkflow:
    """方案A工作流"""

    def __init__(self):
        self.crawler = WeiboHotspotCrawler()
        self.script_generator = ScriptGenerator()
        self.video_generator = VideoGenerator(provider="heygen")
        self.publisher = Publisher()

        # 输出目录
        self.output_dir = config.working_dir / "plan_a"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, hotspot_limit: int = 10, styles: List[str] = None) -> Dict:
        """
        执行完整流程

        Args:
            hotspot_limit: 采集热搜数量
            styles: 文案风格列表

        Returns:
            执行结果统计
        """
        logger.info("=" * 50)
        logger.info("方案A流程启动")
        logger.info("=" * 50)

        stats = {
            "hotspots_fetched": 0,
            "scripts_generated": 0,
            "videos_generated": 0,
            "videos_published": 0,
            "failed": 0
        }

        # 1. 采集热点
        logger.info("步骤1: 采集微博热搜")
        hotspots = self.crawler.fetch_hotspots(limit=hotspot_limit)
        if not hotspots:
            logger.error("未获取到热搜数据")
            return stats

        stats["hotspots_fetched"] = len(hotspots)
        logger.info(f"成功获取 {len(hotspots)} 条热搜")

        # 2. 过滤热点 (可选)
        # hotspots = self.crawler.filter_hotspots(
        #     hotspots,
        #     keywords=["科技", "AI", "互联网"],
        #     exclude_keywords=["明星", "娱乐"]
        # )

        # 3. 批量生成视频
        for idx, hotspot in enumerate(hotspots, 1):
            logger.info(f"\n处理热搜 {idx}/{len(hotspots)}: {hotspot['title']}")

            try:
                # 3.1 生成文案
                logger.info("  -> 生成文案")
                scripts = self.script_generator.generate_scripts(hotspot, styles=styles)
                if not scripts:
                    logger.warning(f"  -> 文案生成失败，跳过")
                    stats["failed"] += 1
                    continue

                stats["scripts_generated"] += len(scripts)
                logger.info(f"  -> 生成 {len(scripts)} 条文案")

                # 3.2 选择最佳文案 (这里简单取第一条)
                best_script = scripts[0]
                logger.info(f"  -> 选择风格: {best_script['style']}")

                # 3.3 生成视频
                logger.info("  -> 生成视频")
                video_info = self.video_generator.generate_video(best_script)
                if not video_info:
                    logger.warning(f"  -> 视频生成失败，跳过")
                    stats["failed"] += 1
                    continue

                stats["videos_generated"] += 1
                logger.info(f"  -> 视频生成成功: {video_info['video_path']}")

                # 3.4 发布视频
                logger.info("  -> 发布视频")
                publish_results = self.publisher.publish_video(video_info, best_script)

                success_count = sum(1 for v in publish_results.values() if v)
                if success_count > 0:
                    stats["videos_published"] += 1
                    logger.info(f"  -> 发布成功 {success_count}/{len(publish_results)} 个平台")
                else:
                    logger.warning(f"  -> 所有平台发布失败")

            except Exception as e:
                logger.error(f"  -> 处理失败: {e}")
                stats["failed"] += 1

        # 4. 输出统计
        logger.info("\n" + "=" * 50)
        logger.info("方案A流程完成")
        logger.info("=" * 50)
        logger.info(f"热搜采集: {stats['hotspots_fetched']} 条")
        logger.info(f"文案生成: {stats['scripts_generated']} 条")
        logger.info(f"视频生成: {stats['videos_generated']} 条")
        logger.info(f"视频发布: {stats['videos_published']} 条")
        logger.info(f"失败数量: {stats['failed']} 条")

        return stats

    def run_single(self, hotspot_title: str, style: str = "情绪共鸣") -> Optional[Dict]:
        """
        单条热点处理 (用于测试)

        Args:
            hotspot_title: 热点标题
            style: 文案风格

        Returns:
            视频信息
        """
        logger.info(f"单条处理: {hotspot_title}")

        # 构造热点数据
        hotspot = {
            "title": hotspot_title,
            "heat": 0,
            "rank": 1
        }

        # 生成文案
        scripts = self.script_generator.generate_scripts(hotspot, styles=[style])
        if not scripts:
            logger.error("文案生成失败")
            return None

        # 生成视频
        video_info = self.video_generator.generate_video(scripts[0])
        if not video_info:
            logger.error("视频生成失败")
            return None

        # 发布视频
        publish_results = self.publisher.publish_video(video_info, scripts[0])

        return {
            "video_info": video_info,
            "publish_results": publish_results
        }


def main():
    """测试主流程"""
    workflow = PlanAWorkflow()

    # 方式1: 批量处理热搜
    # stats = workflow.run(hotspot_limit=5, styles=["情绪共鸣", "干货清单"])
    # print(f"\n执行结果: {stats}")

    # 方式2: 单条测试
    result = workflow.run_single(
        hotspot_title="AI技术如何改变我们的生活",
        style="情绪共鸣"
    )
    if result:
        print(f"\n视频: {result['video_info']['video_path']}")
        print(f"发布: {result['publish_results']}")


if __name__ == "__main__":
    main()
