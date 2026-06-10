"""
方案B: 图文混剪中等成本方案
视频编辑模块 - MoviePy自动剪辑
"""
import time
from pathlib import Path
from typing import List, Dict, Optional
from moviepy import (
    ImageClip, AudioFileClip, CompositeVideoClip, VideoFileClip,
    concatenate_videoclips, TextClip
)
from loguru import logger
from shared.config import config
from plan_b_image_montage.tts.generator import TTSGenerator
from plan_b_image_montage.intro.generator import IntroGenerator
from plan_b_image_montage.outro.generator import OutroGenerator


class VideoEditor:
    """视频编辑器 - 图片+音频合成"""

    def __init__(self):
        self.output_dir = config.working_dir / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = config.working_dir / "temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.tts_generator = TTSGenerator()
        self.intro_generator = IntroGenerator()
        self.outro_generator = OutroGenerator()

    def create_video(self, storyboard: Dict, images: List[Dict],
                    audio_path: Optional[str] = None) -> Optional[Dict]:
        """
        创建视频

        Args:
            storyboard: 分镜脚本
            images: 图片列表
            audio_path: 音频文件路径（可选，已废弃，现用TTS）

        Returns:
            视频信息 {"video_path": "...", "duration": 45}
        """
        try:
            logger.info("开始视频编辑")

            # 1. 生成TTS音频
            logger.info("生成TTS旁白音频")
            scene_audios = self.tts_generator.generate_scene_audios(storyboard)
            if not scene_audios:
                logger.error("TTS音频生成失败")
                return None

            # 2. 生成营销号片头
            logger.info("生成营销号片头")
            intro_path = self.intro_generator.create_intro(
                storyboard.get('title', '热点视频'),
                duration=3.0
            )

            # 3. 创建图片片段（时长同步到音频）
            clips = []
            for scene_idx, scene in enumerate(storyboard['scenes']):
                # 查找对应图片
                image_info = next((img for img in images if img['scene_index'] == scene_idx), None)
                if not image_info:
                    logger.warning(f"场景{scene_idx}缺少图片，跳过")
                    continue

                # 查找对应音频
                audio_info = next((aud for aud in scene_audios if aud['scene_index'] == scene_idx), None)
                if not audio_info:
                    logger.warning(f"场景{scene_idx}缺少音频，跳过")
                    continue

                # 创建图片片段
                clip = ImageClip(image_info['image_path'])

                # 确保尺寸为偶数(libx264要求)
                w, h = clip.size
                if w % 2 != 0:
                    w = w - 1
                if h % 2 != 0:
                    h = h - 1
                clip = clip.resized((w, h))

                # 时长同步到音频
                clip = clip.with_duration(audio_info['duration'])

                # 添加音频
                audio_clip = AudioFileClip(audio_info['audio_path'])
                clip = clip.with_audio(audio_clip)

                clips.append(clip)
                logger.info(f"  -> 场景{scene_idx+1}: {audio_info['duration']:.2f}秒")

            if not clips:
                logger.error("没有可用的视频片段")
                return None

            # 检查最低图片数量（至少 6 张才是合格视频）
            if len(clips) < 6:
                logger.error(f"图片数量不足({len(clips)})，需要至少 6 个场景")
                return None

            # 4. 拼接正片
            logger.info("拼接视频片段")
            main_video = concatenate_videoclips(clips, method="compose")

            # 5. 添加片头
            if intro_path and Path(intro_path).exists():
                logger.info("添加片头")
                intro_clip = VideoFileClip(intro_path)
                final_video = concatenate_videoclips([intro_clip, main_video], method="compose")
            else:
                logger.warning("片头生成失败，跳过")
                final_video = main_video

            # 6. 生成结尾
            logger.info("生成营销号结尾")
            outro_path = self.outro_generator.create_outro(duration=3.0)

            # 7. 添加结尾
            if outro_path and Path(outro_path).exists():
                logger.info("添加结尾")
                outro_clip = VideoFileClip(outro_path)
                final_video = concatenate_videoclips([final_video, outro_clip], method="compose")
            else:
                logger.warning("结尾生成失败，跳过")

            # 4. 导出视频
            timestamp = int(time.time())
            filename = f"plan_b_{timestamp}.mp4"
            video_path = self.output_dir / filename

            logger.info(f"导出视频: {video_path}")
            final_video.write_videofile(
                str(video_path),
                fps=30,
                codec='libx264',
                audio_codec='aac',
                preset='medium',
                threads=4,
                bitrate='2000k',  # 添加码率保证编码兼容性
                ffmpeg_params=['-pix_fmt', 'yuv420p']  # 强制yuv420p像素格式,兼容所有播放器
            )

            # 5. 清理资源
            final_video.close()
            for clip in clips:
                clip.close()
            if intro_path and Path(intro_path).exists():
                intro_clip.close()

            # 计算实际时长（片头3秒 + 音频时长总和 + 结尾3秒）
            audio_duration = sum(aud['duration'] for aud in scene_audios)
            outro_duration = 3.0 if (outro_path and Path(outro_path).exists()) else 0.0
            total_duration = 3.0 + audio_duration + outro_duration
            size_mb = round(video_path.stat().st_size / 1024 / 1024, 2)

            logger.info(f"视频生成成功: {video_path}")
            logger.info(f"  时长: {total_duration:.2f}秒 (片头3秒 + 正片{audio_duration:.2f}秒 + 结尾{outro_duration:.2f}秒)")
            logger.info(f"  大小: {size_mb}MB")

            return {
                "video_path": str(video_path),
                "duration": total_duration,
                "size_mb": size_mb
            }

        except Exception as e:
            logger.error(f"视频编辑失败: {e}")
            return None

    def add_subtitles(self, video_path: str, storyboard: Dict) -> Optional[str]:
        """
        添加字幕

        Args:
            video_path: 视频路径
            storyboard: 分镜脚本

        Returns:
            带字幕的视频路径
        """
        try:
            from moviepy import VideoFileClip

            logger.info("添加字幕")
            video = VideoFileClip(video_path)

            subtitle_clips = []
            current_time = 0

            for scene in storyboard['scenes']:
                # 创建字幕
                txt_clip = TextClip(
                    scene['narration'],
                    font_size=40,
                    color='white',
                    font='Arial',
                    stroke_color='black',
                    stroke_width=2,
                    method='caption',
                    size=(video.w * 0.9, None)
                )

                txt_clip = txt_clip.with_position(('center', 'bottom'))
                txt_clip = txt_clip.with_start(current_time)
                txt_clip = txt_clip.with_duration(scene['duration'])

                subtitle_clips.append(txt_clip)
                current_time += scene['duration']

            # 合成字幕
            final_video = CompositeVideoClip([video] + subtitle_clips)

            # 导出
            output_path = video_path.replace('.mp4', '_subtitled.mp4')
            final_video.write_videofile(
                output_path,
                fps=30,
                codec='libx264',
                audio_codec='aac'
            )

            # 清理
            video.close()
            final_video.close()

            logger.info(f"字幕添加完成: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"添加字幕失败: {e}")
            return None


def main():
    """测试视频编辑"""
    editor = VideoEditor()

    # 模拟数据
    test_storyboard = {
        "title": "AI技术改变生活",
        "scenes": [
            {"image_prompt": "...", "narration": "场景1旁白", "duration": 5},
            {"image_prompt": "...", "narration": "场景2旁白", "duration": 5}
        ]
    }

    test_images = [
        {"scene_index": 0, "image_path": "./output/images/scene_0.png"},
        {"scene_index": 1, "image_path": "./output/images/scene_1.png"}
    ]

    result = editor.create_video(test_storyboard, test_images)
    if result:
        print(f"\n视频: {result['video_path']}")
        print(f"时长: {result['duration']}秒")
        print(f"大小: {result['size_mb']}MB")


if __name__ == "__main__":
    main()
