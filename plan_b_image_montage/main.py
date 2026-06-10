"""
方案B: 图文混剪中等成本方案
主流程编排 - 热点采集 -> 分镜脚本 -> 图片生成 -> 视频剪辑 -> 发布
"""
from typing import Dict, Optional
from loguru import logger
from pathlib import Path

from plan_a_text_video.hotspot_crawler import WeiboHotspotCrawler
from plan_b_image_montage.script_generator import StoryboardGenerator
from plan_b_image_montage.image_generator import ImageGenerator
from plan_b_image_montage.video_editor import VideoEditor
from plan_a_text_video.publisher import Publisher
from shared.config import config


class PlanBWorkflow:
    """方案B工作流"""

    def __init__(self):
        self.crawler = WeiboHotspotCrawler()
        self.script_generator = StoryboardGenerator()
        self.image_generator = ImageGenerator(provider="custom")
        self.video_editor = VideoEditor()
        self.publisher = Publisher()

        self.output_dir = config.working_dir / "plan_b"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, hotspot_limit: int = 5) -> Dict:
        """
        执行完整流程

        Args:
            hotspot_limit: 采集热搜数量

        Returns:
            执行结果统计
        """
        logger.info("=" * 50)
        logger.info("方案B流程启动")
        logger.info("=" * 50)

        stats = {
            "hotspots_fetched": 0,
            "storyboards_generated": 0,
            "images_generated": 0,
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

        # 2. 批量生成视频
        for idx, hotspot in enumerate(hotspots, 1):
            logger.info(f"\n处理热搜 {idx}/{len(hotspots)}: {hotspot['title']}")

            try:
                # 为每条热点切换图片输出目录，避免跨视频复用旧图
                import time as _time
                import re
                safe_title = re.sub(r'[^\w一-鿿]+', '_', hotspot['title'])[:30].strip('_')
                task_id = f"{safe_title}_{int(_time.time())}"
                self.image_generator.set_task_context(task_id)

                # 2.1 生成分镜脚本
                logger.info("  -> 生成分镜脚本")
                storyboard = self.script_generator.generate_storyboard(hotspot, target_duration=45)
                if not storyboard:
                    logger.warning("  -> 分镜脚本生成失败，跳过")
                    stats["failed"] += 1
                    continue

                stats["storyboards_generated"] += 1
                logger.info(f"  -> 分镜脚本: {storyboard['scene_count']} 个场景")

                # 2.2 生成图片
                logger.info("  -> 生成图片")
                images = self.image_generator.generate_images(storyboard)
                if not images:
                    logger.warning("  -> 图片生成失败，跳过")
                    stats["failed"] += 1
                    continue

                stats["images_generated"] += len(images)
                logger.info(f"  -> 生成 {len(images)} 张图片")

                # 2.3 剪辑视频
                logger.info("  -> 剪辑视频")
                video_info = self.video_editor.create_video(storyboard, images)
                if not video_info:
                    logger.warning("  -> 视频剪辑失败，跳过")
                    stats["failed"] += 1
                    continue

                stats["videos_generated"] += 1
                logger.info(f"  -> 视频生成成功: {video_info['video_path']}")

                # 2.4 发布视频
                logger.info("  -> 发布视频")
                # 构造文案信息用于发布
                script_info = {
                    "style": "图文混剪",
                    "script": storyboard['scenes'][0]['narration'] if storyboard['scenes'] else "",
                    "hotspot_title": hotspot['title']
                }
                publish_results = self.publisher.publish_video(video_info, script_info)

                success_count = sum(1 for v in publish_results.values() if v)
                if success_count > 0:
                    stats["videos_published"] += 1
                    logger.info(f"  -> 发布成功 {success_count}/{len(publish_results)} 个平台")
                else:
                    logger.warning("  -> 所有平台发布失败")

            except Exception as e:
                logger.error(f"  -> 处理失败: {e}")
                stats["failed"] += 1

        # 3. 输出统计
        logger.info("\n" + "=" * 50)
        logger.info("方案B流程完成")
        logger.info("=" * 50)
        logger.info(f"热搜采集: {stats['hotspots_fetched']} 条")
        logger.info(f"分镜脚本: {stats['storyboards_generated']} 条")
        logger.info(f"图片生成: {stats['images_generated']} 张")
        logger.info(f"视频生成: {stats['videos_generated']} 条")
        logger.info(f"视频发布: {stats['videos_published']} 条")
        logger.info(f"失败数量: {stats['failed']} 条")

        return stats

    def run_single(self, hotspot_title: str, task_id: Optional[str] = None) -> Optional[Dict]:
        """
        单条热点处理 (用于测试)

        Args:
            hotspot_title: 热点标题
            task_id: 可选的任务 ID，用于按视频隔离图片输出目录；缺省时按时间戳自动生成

        Returns:
            视频信息
        """
        import time as _time
        import re

        if not task_id:
            safe_title = re.sub(r'[^\w一-鿿]+', '_', hotspot_title)[:30].strip('_')
            task_id = f"{safe_title}_{int(_time.time())}"

        logger.info(f"单条处理: {hotspot_title} (task_id={task_id})")

        self.image_generator.set_task_context(task_id)

        hotspot = {
            "title": hotspot_title,
            "heat": 0,
            "rank": 1
        }

        # 生成分镜脚本
        storyboard = self.script_generator.generate_storyboard(hotspot)
        if not storyboard:
            logger.error("分镜脚本生成失败")
            return None

        # 生成图片
        images = self.image_generator.generate_images(storyboard)
        if not images:
            logger.error("图片生成失败")
            return None

        # 剪辑视频
        video_info = self.video_editor.create_video(storyboard, images)
        if not video_info:
            logger.error("视频剪辑失败")
            return None

        # 发布视频
        script_info = {
            "style": "图文混剪",
            "script": storyboard['scenes'][0]['narration'],
            "hotspot_title": hotspot_title
        }
        publish_results = self.publisher.publish_video(video_info, script_info)

        return {
            "video_info": video_info,
            "publish_results": publish_results,
            "task_id": task_id
        }


def main():
    """测试主流程"""
    workflow = PlanBWorkflow()

    # 方式1: 批量处理热搜
    # stats = workflow.run(hotspot_limit=3)
    # print(f"\n执行结果: {stats}")

    # 方式2: 单条测试
    result = workflow.run_single(hotspot_title="AI技术如何改变我们的生活")
    if result:
        print(f"\n视频: {result['video_info']['video_path']}")
        print(f"发布: {result['publish_results']}")


if __name__ == "__main__":
    main()
