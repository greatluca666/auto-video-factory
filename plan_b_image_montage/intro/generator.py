"""
营销号片头生成模块
"""
import time
from pathlib import Path
from typing import Optional
from moviepy import ImageClip, AudioFileClip
from loguru import logger
from shared.config import config


class IntroGenerator:
    """营销号片头生成器"""

    def __init__(self):
        self.output_dir = config.working_dir / "intros"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 延迟导入避免循环依赖
        from plan_b_image_montage.image_generator.generator import ImageGenerator
        self.image_gen = ImageGenerator()

    def create_intro(self, title: str, duration: float = 3.0) -> Optional[str]:
        """
        创建营销号片头 (AI生图 + TTS音频)

        Args:
            title: 视频标题
            duration: 片头时长(秒)

        Returns:
            片头视频路径
        """
        try:
            timestamp = int(time.time())
            intro_path = self.output_dir / f"intro_{timestamp}.mp4"

            if intro_path.exists():
                logger.info(f"片头已存在: {intro_path}")
                return str(intro_path)

            logger.info("生成营销号片头")

            # 1. 生成片头旁白TTS
            from plan_b_image_montage.tts.generator import TTSGenerator
            tts_gen = TTSGenerator()
            intro_text = f"重磅消息！{title}，马上为您揭秘！"
            intro_audio_path = self.output_dir / f"intro_audio_{timestamp}.mp3"

            import asyncio
            success = asyncio.run(tts_gen.generate_audio(intro_text, intro_audio_path))
            if not success or not intro_audio_path.exists():
                logger.warning("片头音频生成失败，使用静音")
                intro_audio_path = None

            # 2. AI生成片头图片
            intro_prompt = (
                f"Bold Chinese text '{title}' in large golden yellow font, "
                f"crimson red gradient background, "
                f"text '🔥 重磅消息 🔥' at top in white, "
                f"text '👇 接下来更精彩 👇' at bottom in yellow, "
                f"modern marketing style poster, 9:16 vertical format, "
                f"high contrast, professional design"
            )

            intro_images = self.image_gen.generate_images_from_prompts([intro_prompt])
            if not intro_images or not intro_images[0].get('image_path'):
                logger.error("片头图片生成失败")
                return None

            intro_image_path = intro_images[0]['image_path']
            logger.info(f"片头图片生成: {intro_image_path}")

            # 3. 图片转视频
            clip = ImageClip(intro_image_path)

            # 确保尺寸偶数
            w, h = clip.size
            if w % 2 != 0:
                w = w - 1
            if h % 2 != 0:
                h = h - 1
            clip = clip.resized((w, h))
            clip = clip.with_duration(duration)

            # 4. 添加音频
            if intro_audio_path:
                from moviepy import AudioFileClip
                audio_clip = AudioFileClip(str(intro_audio_path))
                clip = clip.with_audio(audio_clip)
                logger.info(f"片头音频添加: {intro_audio_path}")

            # 5. 导出
            clip.write_videofile(
                str(intro_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                bitrate='2000k',
                ffmpeg_params=['-pix_fmt', 'yuv420p']
            )

            clip.close()
            if intro_audio_path:
                audio_clip.close()

            logger.info(f"片头生成成功: {intro_path}")
            return str(intro_path)

        except Exception as e:
            logger.error(f"片头生成失败: {e}")
            return None


def main():
    """测试片头生成"""
    generator = IntroGenerator()
    intro_path = generator.create_intro("AI技术改变世界", duration=3.0)

    if intro_path:
        print(f"\n片头生成成功: {intro_path}")


if __name__ == "__main__":
    main()
