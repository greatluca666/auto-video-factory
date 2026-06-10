"""
方案A: 低成本文字口播流水线
多平台发布模块 - 抖音/快手/视频号
"""
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger
from shared.config import config


class Publisher:
    """多平台视频发布器"""

    def __init__(self):
        self.platforms = config.publisher.publish_platforms
        self.auto_publish = config.publisher.auto_publish

    def publish_video(self, video_info: Dict, script: Dict) -> Dict[str, bool]:
        """
        发布视频到多个平台

        Args:
            video_info: 视频信息 {"video_path": "...", "duration": 45}
            script: 文案信息 {"style": "...", "script": "...", "hotspot_title": "..."}

        Returns:
            发布结果 {"douyin": True, "kuaishou": False, "weixin": True}
        """
        if not self.auto_publish:
            logger.info("自动发布已关闭")
            return {}

        results = {}
        video_path = Path(video_info["video_path"])

        if not video_path.exists():
            logger.error(f"视频文件不存在: {video_path}")
            return results

        # 生成标题和描述
        title = self._generate_title(script)
        description = self._generate_description(script)
        tags = self._generate_tags(script)

        for platform in self.platforms:
            try:
                if platform == "douyin":
                    success = self._publish_douyin(video_path, title, description, tags)
                elif platform == "kuaishou":
                    success = self._publish_kuaishou(video_path, title, description, tags)
                elif platform == "weixin":
                    success = self._publish_weixin(video_path, title, description, tags)
                else:
                    logger.warning(f"不支持的平台: {platform}")
                    success = False

                results[platform] = success
                logger.info(f"{platform} 发布{'成功' if success else '失败'}")

                # 避免频繁请求
                time.sleep(2)

            except Exception as e:
                logger.error(f"{platform} 发布异常: {e}")
                results[platform] = False

        return results

    def _publish_douyin(self, video_path: Path, title: str, description: str, tags: List[str]) -> bool:
        """发布到抖音"""
        try:
            # 1. 上传视频
            upload_url = "https://open.douyin.com/video/upload/"
            headers = {
                "access-token": config.publisher.douyin_access_token
            }

            with open(video_path, "rb") as f:
                files = {"video": f}
                data = {
                    "open_id": "user_open_id"  # 需要从授权流程获取
                }
                response = requests.post(upload_url, headers=headers, files=files, data=data, timeout=60)
                response.raise_for_status()
                upload_data = response.json()

            if upload_data.get("data", {}).get("error_code") != 0:
                logger.error(f"抖音上传失败: {upload_data}")
                return False

            video_id = upload_data["data"]["video"]["video_id"]

            # 2. 创建视频
            create_url = "https://open.douyin.com/video/create/"
            payload = {
                "open_id": "user_open_id",
                "video_id": video_id,
                "text": f"{title}\n\n{description}",
                "micro_app_id": config.publisher.douyin_client_key,
                "micro_app_title": title,
                "cover_tsp": 0,  # 封面时间戳
                "poi_id": "",
                "poi_name": "",
                "at_users": []
            }

            response = requests.post(create_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            create_data = response.json()

            return create_data.get("data", {}).get("error_code") == 0

        except Exception as e:
            logger.error(f"抖音发布失败: {e}")
            return False

    def _publish_kuaishou(self, video_path: Path, title: str, description: str, tags: List[str]) -> bool:
        """发布到快手"""
        try:
            # 快手开放平台API
            upload_url = "https://open.kuaishou.com/openapi/photo/upload"
            headers = {
                "Content-Type": "application/json"
            }

            # 1. 获取上传token
            token_payload = {
                "app_id": config.publisher.kuaishou_app_id,
                "app_secret": config.publisher.kuaishou_app_secret,
                "access_token": "user_access_token"  # 需要从授权流程获取
            }

            # 2. 上传视频 (简化示例)
            with open(video_path, "rb") as f:
                files = {"file": f}
                data = {
                    "caption": f"{title}\n{description}",
                    "tags": ",".join(tags)
                }
                response = requests.post(upload_url, headers=headers, files=files, data=data, timeout=60)
                response.raise_for_status()
                result = response.json()

            return result.get("result") == 1

        except Exception as e:
            logger.error(f"快手发布失败: {e}")
            return False

    def _publish_weixin(self, video_path: Path, title: str, description: str, tags: List[str]) -> bool:
        """发布到视频号"""
        try:
            # 视频号开放平台API
            # 1. 获取access_token
            token_url = "https://api.weixin.qq.com/cgi-bin/token"
            params = {
                "grant_type": "client_credential",
                "appid": config.publisher.weixin_app_id,
                "secret": config.publisher.weixin_app_secret
            }
            response = requests.get(token_url, params=params, timeout=10)
            response.raise_for_status()
            token_data = response.json()

            if "access_token" not in token_data:
                logger.error(f"获取微信access_token失败: {token_data}")
                return False

            access_token = token_data["access_token"]

            # 2. 上传视频 (简化示例)
            upload_url = f"https://api.weixin.qq.com/cgi-bin/media/upload?access_token={access_token}&type=video"

            with open(video_path, "rb") as f:
                files = {"media": f}
                response = requests.post(upload_url, files=files, timeout=60)
                response.raise_for_status()
                upload_data = response.json()

            if "media_id" not in upload_data:
                logger.error(f"视频号上传失败: {upload_data}")
                return False

            # 3. 发布视频
            publish_url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"
            payload = {
                "touser": "user_openid",
                "msgtype": "video",
                "video": {
                    "media_id": upload_data["media_id"],
                    "title": title,
                    "description": description
                }
            }

            response = requests.post(publish_url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()

            return result.get("errcode") == 0

        except Exception as e:
            logger.error(f"视频号发布失败: {e}")
            return False

    def _generate_title(self, script: Dict) -> str:
        """生成视频标题"""
        hotspot = script.get("hotspot_title", "热点话题")
        style = script.get("style", "")

        # 根据风格生成标题
        if style == "情绪共鸣":
            return f"#{hotspot}# 这件事让我破防了..."
        elif style == "干货清单":
            return f"#{hotspot}# 3个关键点必须知道!"
        elif style == "故事悬念":
            return f"#{hotspot}# 我当时真的气炸了"
        else:
            return f"#{hotspot}#"

    def _generate_description(self, script: Dict) -> str:
        """生成视频描述"""
        # 截取文案前100字作为描述
        script_text = script.get("script", "")
        return script_text[:100] + "..." if len(script_text) > 100 else script_text

    def _generate_tags(self, script: Dict) -> List[str]:
        """生成视频标签"""
        hotspot = script.get("hotspot_title", "")
        style = script.get("style", "")

        tags = [hotspot, style, "热点", "短视频"]
        return [tag for tag in tags if tag]


def main():
    """测试发布"""
    publisher = Publisher()

    test_video = {
        "video_path": "./output/videos/test.mp4",
        "duration": 30,
        "size_mb": 5.2
    }

    test_script = {
        "style": "情绪共鸣",
        "script": "测试文案内容...",
        "hotspot_title": "AI技术发展"
    }

    results = publisher.publish_video(test_video, test_script)
    print(f"发布结果: {results}")


if __name__ == "__main__":
    main()
