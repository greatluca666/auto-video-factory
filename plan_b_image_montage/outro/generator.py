"""
营销号结尾生成模块
"""
import time
from pathlib import Path
from typing import Optional
from moviepy import ImageClip
from loguru import logger
from shared.config import config


class OutroGenerator:
    """营销号结尾生成器"""

    def __init__(self):
        self.output_dir = config.working_dir / "outros"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 延迟导入避免循环依赖
        from plan_b_image_montage.image_generator.generator import ImageGenerator
        self.image_gen = ImageGenerator()

    def create_outro(self, duration: float = 3.0) -> Optional[str]:
        """
        创建营销号结尾 (AI生图)

        Args:
            duration: 结尾时长(秒)

        Returns:
            结尾视频路径
        """
        try:
            timestamp = int(time.time())
            outro_path = self.output_dir / f"outro_{timestamp}.mp4"

            if outro_path.exists():
                logger.info(f"结尾已存在: {outro_path}")
                return str(outro_path)

            logger.info("生成营销号结尾")

            # 1. AI生成结尾图片
            outro_prompt = (
                "Call-to-action poster with Chinese text, "
                "large thumbs up icon 👍, heart icon ❤️, "
                "text '点赞 关注 不迷路' in bold yellow font, "
                "gradient background red to orange, "
                "subscribe button design, "
                "modern social media style, "
                "9:16 vertical format, "
                "clean and professional"
            )

            outro_images = self.image_gen.generate_images_from_prompts([outro_prompt])
            if not outro_images or not outro_images[0].get('image_path'):
                logger.error("结尾图片生成失败")
                return None

            outro_image_path = outro_images[0]['image_path']
            logger.info(f"结尾图片生成: {outro_image_path}")

            # 2. 图片转视频
            clip = ImageClip(outro_image_path)

            # 确保尺寸偶数
            w, h = clip.size
            if w % 2 != 0:
                w = w - 1
            if h % 2 != 0:
                h = h - 1
            clip = clip.resized((w, h))
            clip = clip.with_duration(duration)

            # 3. 导出
            clip.write_videofile(
                str(outro_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                bitrate='2000k',
                ffmpeg_params=['-pix_fmt', 'yuv420p']
            )

            clip.close()

            logger.info(f"结尾生成成功: {outro_path}")
            return str(outro_path)

        except Exception as e:
            logger.error(f"结尾生成失败: {e}")
            return None


def main():
    """测试结尾生成"""
    generator = OutroGenerator()
    outro_path = generator.create_outro(duration=3.0)

    if outro_path:
        print(f"\n结尾生成成功: {outro_path}")


if __name__ == "__main__":
    main()
