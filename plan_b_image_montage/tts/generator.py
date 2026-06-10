"""
TTS语音生成模块 - edge-tts
"""
import asyncio
import edge_tts
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from shared.config import config


class TTSGenerator:
    """文本转语音生成器"""

    def __init__(self, voice: str = "zh-CN-XiaoxiaoNeural"):
        """
        初始化TTS生成器

        Args:
            voice: 语音角色 (edge-tts支持的中文角色)
        """
        self.voice = voice
        self.output_dir = config.working_dir / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def generate_audio(self, text: str, output_path: Path) -> bool:
        """
        生成单个音频文件

        Args:
            text: 文本内容
            output_path: 输出路径

        Returns:
            是否成功
        """
        try:
            communicate = edge_tts.Communicate(text, self.voice)
            await communicate.save(str(output_path))
            logger.info(f"音频生成成功: {output_path}")
            return True
        except Exception as e:
            logger.error(f"音频生成失败: {e}")
            return False

    def generate_scene_audios(self, storyboard: Dict) -> Optional[List[Dict]]:
        """
        批量生成场景旁白音频

        Args:
            storyboard: 分镜脚本

        Returns:
            音频列表 [{"scene_index": 0, "audio_path": "...", "duration": 3.5}]
        """
        audios = []

        for idx, scene in enumerate(storyboard['scenes']):
            narration = scene.get('narration', '')
            if not narration:
                logger.warning(f"场景{idx}无旁白文本，跳过")
                continue

            output_path = self.output_dir / f"scene_{idx}_{hash(narration) & 0x7FFFFFFF}.mp3"

            # 如果已存在，跳过
            if output_path.exists():
                duration = self._get_audio_duration(output_path)
                logger.info(f"场景{idx}音频已存在，时长: {duration:.2f}秒")
                audios.append({
                    "scene_index": idx,
                    "audio_path": str(output_path),
                    "duration": duration
                })
                continue

            # 生成音频
            logger.info(f"生成场景{idx+1}/{len(storyboard['scenes'])}音频")
            success = asyncio.run(self.generate_audio(narration, output_path))

            if success and output_path.exists():
                duration = self._get_audio_duration(output_path)
                audios.append({
                    "scene_index": idx,
                    "audio_path": str(output_path),
                    "duration": duration
                })
                logger.info(f"  -> 成功: {duration:.2f}秒")
            else:
                logger.warning(f"  -> 失败，跳过")

        logger.info(f"音频生成完成: {len(audios)}/{len(storyboard['scenes'])} 个")
        return audios if audios else None

    def _get_audio_duration(self, audio_path: Path) -> float:
        """
        获取音频时长

        Args:
            audio_path: 音频文件路径

        Returns:
            时长(秒)
        """
        try:
            from moviepy import AudioFileClip
            audio = AudioFileClip(str(audio_path))
            duration = audio.duration
            audio.close()
            return duration
        except Exception as e:
            logger.error(f"获取音频时长失败: {e}")
            return 3.0  # 默认3秒


def main():
    """测试TTS生成"""
    generator = TTSGenerator()

    test_storyboard = {
        "scenes": [
            {"narration": "大家好，今天给大家分享一个爆炸性的消息！"},
            {"narration": "AI技术正在以惊人的速度改变我们的生活。"}
        ]
    }

    audios = generator.generate_scene_audios(test_storyboard)

    if audios:
        print(f"\n成功生成 {len(audios)} 个音频:")
        for audio in audios:
            print(f"  场景{audio['scene_index']}: {audio['audio_path']} ({audio['duration']:.2f}秒)")


if __name__ == "__main__":
    main()
