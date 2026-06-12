"""
方案B: 图文混剪中等成本方案
图片生成模块 - FLUX/Stable Diffusion
"""
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from shared.config import config


class ImageGenerator:
    """AI图片生成器"""

    def __init__(self, provider: str = None):
        """
        初始化图片生成器

        Args:
            provider: 图片生成提供商 (replicate, stability, custom)
        """
        self.provider = provider or config.image_generator.default_provider
        self.base_output_dir = config.working_dir / "images"
        self.base_output_dir.mkdir(parents=True, exist_ok=True)

        # task_id 用于按视频隔离图片输出和进度文件
        # None 时回退到 base_output_dir（兼容 intro/outro 等无 task 上下文的调用）
        self.task_id: Optional[str] = None
        self.output_dir = self.base_output_dir

        if self.provider == "replicate":
            self.api_token = config.image_generator.replicate_api_token
            self.base_url = "https://api.replicate.com/v1"
        elif self.provider == "stability":
            self.api_key = config.image_generator.stability_api_key
            self.base_url = "https://api.stability.ai/v2beta"
        elif self.provider == "custom":
            self.api_key = config.image_generator.custom_api_key
            self.base_url = config.image_generator.custom_base_url
            self.model = config.image_generator.custom_model
        else:
            raise ValueError(f"不支持的图片生成提供商: {self.provider}")

    def set_task_context(self, task_id: Optional[str]) -> None:
        """
        切换到指定 task 的输出目录，使图片和进度文件按视频隔离。

        Args:
            task_id: 视频任务 ID；None 时回退到全局 images/ 目录（用于 intro/outro 等无 task 场景）
        """
        self.task_id = task_id
        if task_id:
            self.output_dir = self.base_output_dir / task_id
        else:
            self.output_dir = self.base_output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_images(self, storyboard: Dict) -> Optional[List[Dict]]:
        """
        根据分镜脚本批量生成图片

        Args:
            storyboard: 分镜脚本 {"scenes": [...]}

        Returns:
            图片列表 [{"scene_index": 0, "image_path": "...", "prompt": "..."}]
        """
        import json

        # 进度文件路径
        progress_file = self.output_dir / "generation_progress.json"

        # 加载已生成图片
        existing_images = {}
        if progress_file.exists():
            try:
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                    existing_images = {img['scene_index']: img for img in progress_data.get('images', [])}
                logger.info(f"加载已生成图片: {len(existing_images)} 张")
            except Exception as e:
                logger.warning(f"加载进度文件失败: {e}")

        images = []

        for idx, scene in enumerate(storyboard['scenes']):
            # 检查是否已生成（必须 scene_index 和 prompt 同时匹配，避免跨视频复用旧图）
            if idx in existing_images:
                existing_path = Path(existing_images[idx]['image_path'])
                existing_prompt = existing_images[idx].get('prompt', '')
                current_prompt = scene.get('image_prompt', '')
                if existing_path.exists() and existing_prompt == current_prompt:
                    logger.info(f"场景 {idx+1}/{len(storyboard['scenes'])} 已存在，跳过")
                    images.append(existing_images[idx])
                    continue

            logger.info(f"生成场景 {idx+1}/{len(storyboard['scenes'])} 的图片")

            # 重试机制（最多3次）
            max_retries = 3
            image_info = None

            for retry in range(max_retries):
                try:
                    image_info = self._generate_single_image(
                        prompt=scene['image_prompt'],
                        scene_index=idx
                    )

                    if image_info:
                        images.append(image_info)
                        logger.info(f"  -> 成功: {image_info['image_path']}")

                        # 保存进度
                        try:
                            with open(progress_file, 'w', encoding='utf-8') as f:
                                json.dump({'images': images}, f, ensure_ascii=False, indent=2)
                        except Exception as e:
                            logger.warning(f"保存进度失败: {e}")

                        break  # 成功后跳出重试循环
                    else:
                        if retry < max_retries - 1:
                            logger.warning(f"  -> 失败，重试 {retry+1}/{max_retries-1}")
                            time.sleep(5)  # 失败后等待5秒再重试
                        else:
                            logger.error(f"  -> 失败，已重试{max_retries}次，跳过此场景")

                except Exception as e:
                    if retry < max_retries - 1:
                        logger.warning(f"  -> 异常: {e}，重试 {retry+1}/{max_retries-1}")
                        time.sleep(5)
                    else:
                        logger.error(f"  -> 生成失败: {e}，已重试{max_retries}次")

            # 避免频繁请求
            if image_info:
                time.sleep(2)

        logger.info(f"批量生成完成: {len(images)}/{len(storyboard['scenes'])} 张")
        return images if images else None

    def generate_images_from_prompts(self, prompts: List[str]) -> Optional[List[Dict]]:
        """
        从prompt列表直接生成图片（不依赖storyboard）

        Args:
            prompts: prompt字符串列表

        Returns:
            图片列表 [{"scene_index": 0, "image_path": "...", "prompt": "..."}]
        """
        images = []

        for idx, prompt in enumerate(prompts):
            logger.info(f"生成图片 {idx+1}/{len(prompts)}")

            # 重试机制（最多3次）
            max_retries = 3
            image_info = None

            for retry in range(max_retries):
                try:
                    image_info = self._generate_single_image(
                        prompt=prompt,
                        scene_index=idx
                    )

                    if image_info:
                        images.append(image_info)
                        logger.info(f"  -> 成功: {image_info['image_path']}")
                        break  # 成功后跳出重试循环
                    else:
                        if retry < max_retries - 1:
                            logger.warning(f"  -> 失败，重试 {retry+1}/{max_retries-1}")
                            time.sleep(5)
                        else:
                            logger.error(f"  -> 失败，已重试{max_retries}次")

                except Exception as e:
                    if retry < max_retries - 1:
                        logger.warning(f"  -> 异常: {e}，重试 {retry+1}/{max_retries-1}")
                        time.sleep(5)
                    else:
                        logger.error(f"  -> 生成失败: {e}，已重试{max_retries}次")

            # 避免频繁请求
            if image_info:
                time.sleep(2)

        logger.info(f"批量生成完成: {len(images)}/{len(prompts)} 张")
        return images if images else None

    def _generate_single_image(self, prompt: str, scene_index: int) -> Optional[Dict]:
        """生成单张图片"""
        try:
            if self.provider == "replicate":
                return self._generate_replicate(prompt, scene_index)
            elif self.provider == "stability":
                return self._generate_stability(prompt, scene_index)
            elif self.provider == "custom":
                return self._generate_custom(prompt, scene_index)
        except Exception as e:
            logger.error(f"生成图片失败: {e}")
            return None

    def _generate_replicate(self, prompt: str, scene_index: int) -> Optional[Dict]:
        """使用Replicate FLUX生成图片"""
        headers = {
            "Authorization": f"Token {self.api_token}",
            "Content-Type": "application/json"
        }

        # 优化提示词
        enhanced_prompt = self._enhance_prompt(prompt)

        # 创建预测任务
        payload = {
            "version": "black-forest-labs/flux-schnell",  # FLUX Schnell模型
            "input": {
                "prompt": enhanced_prompt,
                "width": 1080,
                "height": 1920,  # 竖屏9:16
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "num_inference_steps": 4  # Schnell只需4步
            }
        }

        try:
            # 提交任务
            response = requests.post(
                f"{self.base_url}/predictions",
                headers=headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            prediction_id = data["id"]
            logger.info(f"Replicate任务已提交: {prediction_id}")

            # 轮询任务状态
            image_url = self._poll_replicate_status(prediction_id)
            if not image_url:
                return None

            # 下载图片
            image_path = self._download_image(image_url, scene_index)
            if not image_path:
                return None

            return {
                "scene_index": scene_index,
                "image_path": str(image_path),
                "prompt": enhanced_prompt
            }

        except requests.RequestException as e:
            logger.error(f"Replicate API请求失败: {e}")
            return None

    def _poll_replicate_status(self, prediction_id: str, max_wait: int = 60) -> Optional[str]:
        """轮询Replicate任务状态"""
        headers = {"Authorization": f"Token {self.api_token}"}
        start_time = time.time()

        while time.time() - start_time < max_wait:
            try:
                response = requests.get(
                    f"{self.base_url}/predictions/{prediction_id}",
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                data = response.json()

                status = data["status"]

                if status == "succeeded":
                    return data["output"][0] if data.get("output") else None
                elif status == "failed":
                    logger.error(f"Replicate任务失败: {data.get('error')}")
                    return None

                time.sleep(2)

            except Exception as e:
                logger.error(f"查询Replicate状态失败: {e}")
                time.sleep(2)

        logger.error("Replicate任务超时")
        return None

    def _generate_stability(self, prompt: str, scene_index: int) -> Optional[Dict]:
        """使用Stability AI生成图片"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        enhanced_prompt = self._enhance_prompt(prompt)

        payload = {
            "prompt": enhanced_prompt,
            "output_format": "png",
            "aspect_ratio": "9:16"  # 竖屏
        }

        try:
            response = requests.post(
                f"{self.base_url}/stable-image/generate/core",
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            # Stability返回base64图片
            if "image" in data:
                import base64
                image_data = base64.b64decode(data["image"])

                timestamp = int(time.time())
                filename = f"scene_{scene_index}_{timestamp}.png"
                image_path = self.output_dir / filename

                with open(image_path, "wb") as f:
                    f.write(image_data)

                logger.info(f"图片已保存: {image_path}")

                return {
                    "scene_index": scene_index,
                    "image_path": str(image_path),
                    "prompt": enhanced_prompt
                }

        except Exception as e:
            logger.error(f"Stability AI生成失败: {e}")
            return None

    def _enhance_prompt(self, prompt: str) -> str:
        """优化提示词"""
        # 添加质量提升词
        quality_boost = "high quality, detailed, professional, cinematic lighting, 8k"

        # 添加风格词
        style = "modern, clean, vibrant colors"

        return f"{prompt}, {style}, {quality_boost}"

    def _download_image(self, image_url: str, scene_index: int) -> Optional[Path]:
        """下载图片"""
        try:
            timestamp = int(time.time())
            filename = f"scene_{scene_index}_{timestamp}.png"
            image_path = self.output_dir / filename

            response = requests.get(image_url, stream=True, timeout=30)
            response.raise_for_status()

            with open(image_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            logger.info(f"图片已下载: {image_path}")
            return image_path

        except Exception as e:
            logger.error(f"下载图片失败: {e}")
            return None

    def _generate_custom(self, prompt: str, scene_index: int) -> Optional[Dict]:
        """使用自定义API生成图片 (OpenAI兼容接口)"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        enhanced_prompt = self._enhance_prompt(prompt)

        payload = {
            "model": self.model,
            "prompt": enhanced_prompt,
            "n": 1,
            "size": "1024x1792",  # 竖屏接近9:16
            "quality": "standard",
            "response_format": "url"
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/images/generations",
                    headers=headers,
                    json=payload,
                    timeout=300  # 5分钟超时,避免API内部排队超时
                )

                # 记录请求详情
                logger.debug(f"请求URL: {self.base_url}/images/generations")
                logger.debug(f"请求payload: {payload}")

                # 检查致命错误(余额/认证)
                if response.status_code == 401:
                    logger.error(f"API认证失败(401): {response.text}")
                    logger.error("API Key无效或过期，程序停止")
                    import sys
                    sys.exit(1)

                if response.status_code == 402 or response.status_code == 429:
                    error_data = response.json() if response.text else {}
                    logger.error(f"API余额不足或限流({response.status_code}): {response.text}")
                    logger.error("程序停止")
                    import sys
                    sys.exit(1)

                # 捕获400错误并显示详细响应
                if response.status_code == 400:
                    logger.error(f"400错误详情: {response.text}")
                    logger.error(f"请求头: {headers}")
                    logger.error(f"请求体: {payload}")

                # 检查超时重试
                if response.status_code == 504 or "timeout" in response.text.lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"API超时，重试 {attempt + 1}/{max_retries}")
                        time.sleep(2)
                        continue
                    else:
                        logger.error("API超时次数过多，跳过该图片")
                        return None

                response.raise_for_status()

                # 记录原始响应用于调试
                response_text = response.text
                logger.debug(f"API响应: {response_text[:500]}")

                data = response.json()

                # 检测ModelScope任务模式 (有task_id就轮询)
                if "task_id" in data:
                    task_id = data["task_id"]
                    logger.info(f"检测到异步任务: {task_id}, 开始轮询")

                    # 轮询任务状态，最多等待5分钟
                    poll_start = time.time()
                    poll_timeout = 300
                    poll_interval = 5

                    while time.time() - poll_start < poll_timeout:
                        time.sleep(poll_interval)

                        try:
                            poll_headers = {
                                "Authorization": f"Bearer {self.api_key}",
                                "X-ModelScope-Task-Type": "image_generation"
                            }
                            poll_response = requests.get(
                                f"{self.base_url}/tasks/{task_id}",
                                headers=poll_headers,
                                timeout=30
                            )
                            poll_response.raise_for_status()
                            poll_data = poll_response.json()

                            logger.debug(f"任务状态: {poll_data.get('task_status')}")

                            if poll_data.get("task_status") == "SUCCEED":
                                # 任务成功，获取图片URL
                                if "output_images" in poll_data and len(poll_data["output_images"]) > 0:
                                    image_url = poll_data["output_images"][0]
                                    image_path = self._download_image(image_url, scene_index)

                                    if not image_path:
                                        return None

                                    return {
                                        "scene_index": scene_index,
                                        "image_path": str(image_path),
                                        "prompt": enhanced_prompt
                                    }
                                else:
                                    logger.error("异步任务成功但无output_images")
                                    return None

                            elif poll_data.get("task_status") == "FAILED":
                                logger.error(f"异步任务失败: {poll_data.get('message', '未知错误')}")
                                return None

                            # 其他状态继续轮询

                        except Exception as poll_error:
                            logger.warning(f"轮询任务状态失败: {poll_error}")
                            continue

                    logger.error(f"异步任务超时 ({poll_timeout}秒)")
                    return None

                if "data" in data and data["data"] is not None and len(data["data"]) > 0:
                    item = data["data"][0]

                    # 支持url、b64_json或data URI格式
                    if "url" in item:
                        image_url = item["url"]

                        # 检查是否是data URI
                        if image_url.startswith("data:image/"):
                            import base64
                            # 提取base64部分: data:image/png;base64,<data>
                            b64_data = image_url.split(",", 1)[1]
                            image_data = base64.b64decode(b64_data)

                            timestamp = int(time.time())
                            filename = f"scene_{scene_index}_{timestamp}.png"
                            image_path = self.output_dir / filename

                            with open(image_path, "wb") as f:
                                f.write(image_data)

                            logger.info(f"图片已保存: {image_path}")
                        else:
                            # 普通URL下载
                            image_path = self._download_image(image_url, scene_index)

                    elif "b64_json" in item:
                        import base64
                        image_data = base64.b64decode(item["b64_json"])

                        timestamp = int(time.time())
                        filename = f"scene_{scene_index}_{timestamp}.png"
                        image_path = self.output_dir / filename

                        with open(image_path, "wb") as f:
                            f.write(image_data)

                        logger.info(f"图片已保存: {image_path}")
                    else:
                        logger.error("响应无url或b64_json字段")
                        return None

                    if not image_path:
                        return None

                    return {
                        "scene_index": scene_index,
                        "image_path": str(image_path),
                        "prompt": enhanced_prompt
                    }
                else:
                    # API返回空data或None
                    logger.error(f"API响应无效: data={data.get('data')}, 完整响应: {response_text[:500]}")
                    if "error" in data:
                        logger.error(f"API错误信息: {data['error']}")
                    return None

                # 成功则跳出重试循环
                break

            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"网络超时，重试 {attempt + 1}/{max_retries}")
                    time.sleep(2)
                    continue
                else:
                    logger.error("网络超时次数过多，跳过该图片")
                    return None
            except Exception as e:
                logger.error(f"自定义API生成失败: {e}")
                return None

        return None


def main():
    """测试图片生成"""
    generator = ImageGenerator(provider="replicate")

    test_storyboard = {
        "scenes": [
            {
                "image_prompt": "A futuristic city with flying cars and neon lights",
                "narration": "未来的城市充满科技感",
                "duration": 5
            },
            {
                "image_prompt": "A person using AI hologram interface",
                "narration": "AI正在改变我们的生活方式",
                "duration": 5
            }
        ]
    }

    images = generator.generate_images(test_storyboard)

    if images:
        print(f"\n成功生成 {len(images)} 张图片:")
        for img in images:
            print(f"  场景{img['scene_index']}: {img['image_path']}")


if __name__ == "__main__":
    main()
