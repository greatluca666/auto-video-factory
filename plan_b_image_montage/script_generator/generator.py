"""
方案B: 图文混剪中等成本方案
分镜脚本生成模块 - AI生成结构化分镜脚本
"""
import os
from typing import List, Dict, Optional
from anthropic import Anthropic
from openai import OpenAI
from loguru import logger
from shared.config import config


class StoryboardGenerator:
    """分镜脚本生成器"""

    def __init__(self, provider: str = None):
        """
        初始化分镜脚本生成器

        Args:
            provider: LLM提供商 (anthropic, openai, qwen)
        """
        self.provider = provider or config.llm.default_provider

        if self.provider == "anthropic":
            self.client = Anthropic(api_key=config.llm.anthropic_api_key)
            self.model = "claude-3-5-sonnet-20241022"
        elif self.provider == "openai":
            self.client = OpenAI(
                api_key=config.llm.openai_api_key,
                base_url=config.llm.openai_base_url
            )
            self.model = os.getenv("OPENAI_MODEL", "deepseek-v3.2")
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

    def generate_storyboard(self, hotspot: Dict, target_duration: int = 45) -> Optional[Dict]:
        """
        根据热点生成分镜脚本

        Args:
            hotspot: 热点数据 {"title": "...", "heat": 123, ...}
            target_duration: 目标时长(秒)

        Returns:
            分镜脚本 {"title": "...", "scenes": [...], "total_duration": 45}
        """
        try:
            prompt = self._build_prompt(hotspot, target_duration)

            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=2048,
                    messages=[{"role": "user", "content": prompt}]
                )
                script_text = response.content[0].text.strip()

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=2048
                )
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("AI返回空内容")
                script_text = content.strip()

            # 解析分镜脚本
            logger.debug(f"AI返回脚本:\n{script_text}")
            storyboard = self._parse_storyboard(script_text, hotspot)
            if not storyboard:
                logger.error("分镜脚本解析失败")
                return None

            logger.info(f"成功生成分镜脚本: {len(storyboard['scenes'])} 个场景")
            return storyboard

        except Exception as e:
            logger.error(f"生成分镜脚本失败: {e}")
            return None

    def _build_prompt(self, hotspot: Dict, target_duration: int) -> str:
        """构建提示词"""
        # 获取相关内容上下文
        related = hotspot.get('related_content', '')
        context_info = f"\n相关讨论: {related[:400]}\n" if related else ""

        return f"""
你是一个短视频分镜脚本专家。根据以下热点话题，创作一个图文混剪视频的分镜脚本。

热点话题：{hotspot['title']}
热度：{hotspot.get('heat', '未知')}{context_info}
目标时长：{target_duration}秒

**强制要求**：
1. **必须生成 6-8 个场景**（少于 6 个直接废弃）
2. 每个场景 5-8 秒
3. 每个场景包含：
   - 画面描述（用于AI生图）
   - 旁白文案（用于配音）
   - 时长（秒）
4. **画面与旁白必须严格对应**：
   - 画面描述必须直接视觉化旁白内容
   - 旁白说"AI算法"，画面就要描述算法相关视觉元素
   - 旁白说"用户体验提升"，画面要展现用户使用场景
   - 禁止画面与旁白主题不一致
5. 画面描述要具体、视觉化，适合FLUX/Stable Diffusion生成
6. 旁白要口语化、有节奏感
7. 前3秒必须有强钩子吸引注意力
8. 结尾引导互动（点赞/收藏/关注）
9. **参考相关讨论内容，提炼最有流量潜力的角度和话题点**

输出格式（严格按此格式，必须包含全部 6-8 个场景）：
---
标题：[视频标题]
---
场景1：
画面：[画面描述]
旁白：[旁白文案]
时长：[X]秒
---
场景2：
画面：[画面描述]
旁白：[旁白文案]
时长：[X]秒
---
...

请直接输出分镜脚本，不要有任何前缀或解释。
"""

    def _parse_storyboard(self, script_text: str, hotspot: Dict) -> Optional[Dict]:
        """解析分镜脚本"""
        try:
            lines = script_text.strip().split('\n')

            # 提取标题
            title = hotspot['title']
            for line in lines:
                if line.startswith('标题：'):
                    title = line.replace('标题：', '').strip()
                    break

            # 提取场景
            scenes = []
            current_scene = {}

            for line in lines:
                line = line.strip()

                if line.startswith('场景') and '：' in line:
                    if current_scene:
                        scenes.append(current_scene)
                    current_scene = {}

                elif line.startswith('画面：'):
                    current_scene['image_prompt'] = line.replace('画面：', '').strip()

                elif line.startswith('旁白：'):
                    current_scene['narration'] = line.replace('旁白：', '').strip()

                elif line.startswith('时长：'):
                    duration_str = line.replace('时长：', '').replace('秒', '').strip()
                    try:
                        current_scene['duration'] = int(duration_str)
                    except ValueError:
                        current_scene['duration'] = 5

            # 添加最后一个场景
            if current_scene:
                scenes.append(current_scene)

            # 验证场景
            valid_scenes = []
            for scene in scenes:
                if 'image_prompt' in scene and 'narration' in scene and 'duration' in scene:
                    valid_scenes.append(scene)

            if len(valid_scenes) < 6:
                logger.error(f"场景数量不足: {len(valid_scenes)}/6，需要至少 6 个场景")
                return None

            total_duration = sum(s['duration'] for s in valid_scenes)

            return {
                'title': title,
                'hotspot_title': hotspot['title'],
                'scenes': valid_scenes,
                'total_duration': total_duration,
                'scene_count': len(valid_scenes)
            }

        except Exception as e:
            logger.error(f"解析分镜脚本失败: {e}")
            return None


def main():
    """测试分镜脚本生成"""
    generator = StoryboardGenerator()

    test_hotspot = {
        "title": "AI技术如何改变我们的生活",
        "heat": 1234567
    }

    storyboard = generator.generate_storyboard(test_hotspot, target_duration=45)

    if storyboard:
        print(f"\n标题: {storyboard['title']}")
        print(f"总时长: {storyboard['total_duration']}秒")
        print(f"场景数: {storyboard['scene_count']}\n")

        for idx, scene in enumerate(storyboard['scenes'], 1):
            print(f"场景{idx} ({scene['duration']}秒):")
            print(f"  画面: {scene['image_prompt']}")
            print(f"  旁白: {scene['narration']}\n")


if __name__ == "__main__":
    main()
