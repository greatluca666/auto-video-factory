"""
方案A: 低成本文字口播流水线
视频生成模块 - HeyGen数字人 + Azure TTS
"""
import time
import requests
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from shared.config import config


class VideoGenerator:
    """视频生成器 - 数字人口播"""

    def __init__(self, provider: str = "heygen"):
        """
        初始化视频生成器

        Args:
            provider: 视频生成提供商 (heygen, azure_tts)
        """
        self.provider = provider
        self.output_dir = config.working_dir / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if provider == "heygen":
            self.api_key = config.video_generator.heygen_api_key
            self.base_url = "https://api.heygen.com/v2"
        elif provider == "azure_tts":
            self.api_key = config.video_generator.azure_tts_key
            self.region = config.video_generator.azure_tts_region
        else:
            raise ValueError(f"不支持的视频生成提供商: {provider}")

    def generate_video(self, script: Dict) -> Optional[Dict]:
        """
        生成视频

        Args:
            script: 文案数据 {"style": "...", "script": "...", "duration": 45}

        Returns:
            视频信息 {"video_path": "...", "duration": 45, "size_mb": 12.3}
        """
        try:
            if self.provider == "heygen":
                return self._generate_heygen_video(script)
            elif self.provider == "azure_tts":
                return self._generate_azure_video(script)
        except Exception as e:
            logger.error(f"生成视频失败: {e}")
            return None

    def _generate_heygen_video(self, script: Dict) -> Optional[Dict]:
        """使用HeyGen生成数字人视频"""
        headers = {
            "X-Api-Key": self.api_key,
            "Content-Type": "application/json"
        }

        # 创建视频任务
        payload = {
            "video_inputs": [{
                "character": {
                    "type": "avatar",
                    "avatar_id": "Angela-inblackskirt-20220820",  # 默认数字人
                    "avatar_style": "normal"
                },
                "voice": {
                    "type": "text",
                    "input_text": script["script"],
                    "voice_id": "zh-CN-XiaoxiaoNeural",  # 中文女声
                    "speed": 1.0
                },
                "background": {
                    "type": "color",
                    "value": "#FFFFFF"
                }
            }],
            "dimension": {
                "width": 1080,
                "height": 1920  # 竖屏9:16
            },
            "aspect_ratio": "9:16"
        }

        try:
            # 提交任务
            response = requests.post(
                f"{self.base_url}/video/generate",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            if data.get("code") != 100:
                logger.error(f"HeyGen API错误: {data}")
                return None

            video_id = data["data"]["video_id"]
            logger.info(f"HeyGen任务已提交: {video_id}")

            # 轮询任务状态
            video_url = self._poll_heygen_status(video_id)
            if not video_url:
                return None

            # 下载视频
            video_path = self._download_video(video_url, script)
            if not video_path:
                return None

            return {
                "video_path": str(video_path),
                "duration": script["duration"],
                "size_mb": round(video_path.stat().st_size / 1024 / 1024, 2)
            }

        except requests.RequestException as e:
            logger.error(f"HeyGen API请求失败: {e}")
            return None

    def _poll_heygen_status(self, video_id: str, max_wait: int = 300) -> Optional[str]:
        """轮询HeyGen任务状态"""
        headers = {"X-Api-Key": self.api_key}
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.base_url}/video/status/{video_id}",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                status = data["data"]["status"]
                logger.info(f"HeyGen任务状态: {status}")

                if status == "completed":
                    return data["data"]["video_url"]
                elif status == "failed":
                    logger.error(f"HeyGen任务失败: {data}")
                    return None

                time.sleep(10)  # 每10秒查询一次

            except Exception as e:
                logger.error(f"查询HeyGen状态失败: {e}")
                time.sleep(10)

        logger.error("HeyGen任务超时")
        return None

    def _generate_azure_video(self, script: Dict) -> Optional[Dict]:
        """使用Azure TTS生成音频 + 静态图片合成视频"""
        # TODO: 实现Azure TTS + MoviePy合成
        logger.warning("Azure TTS方案待实现")
        return None

    def _download_video(self, video_url: str, script: Dict) -> Optional[Path]:
        """下载视频文件"""
        try:
            timestamp = int(time.time())
            filename = f"{script['style']}_{timestamp}.mp4"
            video_path = self.output_dir / filename

            response = requests.get(video_url, stream=True, timeout=60)
            response.raise_for_status()

            with open(video_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"视频已下载: {video_path}")
            return video_path

        except Exception as e:
            logger.error(f"下载视频失败: {e}")
            return None


def main():
    """测试视频生成"""
    generator = VideoGenerator(provider="heygen")

    test_script = {
        "style": "情绪共鸣",
        "script": "你知道吗？AI技术正在悄悄改变我们的生活。从智能手机到自动驾驶，从医疗诊断到教育辅导，AI已经无处不在。但你有没有想过，这背后意味着什么？",
        "duration": 20
    }

    result = generator.generate_video(test_script)
    if result:
        print(f"视频生成成功: {result['video_path']}")
        print(f"时长: {result['duration']}秒")
        print(f"大小: {result['size_mb']}MB")


if __name__ == "__main__":
    main()
