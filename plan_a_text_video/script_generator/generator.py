"""
方案A: 低成本文字口播流水线
AI文案生成模块 - 基于Claude/GPT生成爆款文案
"""
from typing import List, Dict, Optional
from anthropic import Anthropic
from openai import OpenAI
from loguru import logger
from shared.config import config


class ScriptGenerator:
    """AI文案生成器"""

    def __init__(self, provider: str = None):
        """
        初始化文案生成器

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
            self.model = "gpt-4o"
        else:
            raise ValueError(f"不支持的LLM提供商: {self.provider}")

    def generate_scripts(self, hotspot: Dict, styles: List[str] = None) -> List[Dict]:
        """
        根据热点生成多种风格的文案

        Args:
            hotspot: 热点数据 {"title": "...", "heat": 123, ...}
            styles: 文案风格列表 ["情绪共鸣", "干货清单", "故事悬念"]

        Returns:
            文案列表 [{"style": "情绪共鸣", "script": "...", "duration": 45}]
        """
        if styles is None:
            styles = ["情绪共鸣", "干货清单", "故事悬念"]

        scripts = []

        for style in styles:
            try:
                script_text = self._generate_single_script(hotspot, style)
                if script_text:
                    scripts.append({
                        "style": style,
                        "script": script_text,
                        "duration": self._estimate_duration(script_text),
                        "hotspot_title": hotspot["title"]
                    })
                    logger.info(f"成功生成 {style} 风格文案")
            except Exception as e:
                logger.error(f"生成 {style} 风格文案失败: {e}")

        return scripts

    def _generate_single_script(self, hotspot: Dict, style: str) -> Optional[str]:
        """生成单个风格的文案"""
        prompt = self._build_prompt(hotspot, style)

        try:
            if self.provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()

            elif self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1024
                )
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("AI返回空内容")
                return content.strip()

        except Exception as e:
            logger.error(f"调用LLM API失败: {e}")
            return None

    def _build_prompt(self, hotspot: Dict, style: str) -> str:
        """构建提示词"""
        style_prompts = {
            "情绪共鸣": """
你是一个短视频文案专家。根据以下热点话题，创作一段情绪共鸣型文案。

要求：
1. 时长控制在15-60秒（约150-600字）
2. 前3秒必须有强钩子（反问/冲突/痛点）
3. 触发目标用户的情绪（愤怒/震惊/后怕/庆幸）
4. 结尾引导互动（"你遇到过吗？评论区告诉我"）
5. 口语化表达，避免书面语

热点话题：{title}
热度：{heat}

请直接输出文案内容，不要有任何前缀或解释。
""",
            "干货清单": """
你是一个短视频文案专家。根据以下热点话题，创作一段干货清单型文案。

要求：
1. 时长控制在15-60秒（约150-600字）
2. 使用数字标题（"3个技巧""5步搞定"）
3. 每8-10秒必须有新信息点
4. 实用性强，让用户觉得"学到东西"
5. 结尾引导收藏（"建议收藏反复看"）

热点话题：{title}
热度：{heat}

请直接输出文案内容，不要有任何前缀或解释。
""",
            "故事悬念": """
你是一个短视频文案专家。根据以下热点话题，创作一段故事悬念型文案。

要求：
1. 时长控制在15-60秒（约150-600字）
2. 开头设置悬念（"我当时真的气炸了"）
3. 用第一人称叙事，真实情绪复盘
4. 中间有反转或冲突
5. 结尾引导关注（"关注我持续更新"）

热点话题：{title}
热度：{heat}

请直接输出文案内容，不要有任何前缀或解释。
"""
        }

        template = style_prompts.get(style, style_prompts["情绪共鸣"])
        return template.format(title=hotspot["title"], heat=hotspot.get("heat", "未知"))

    def _estimate_duration(self, script: str) -> int:
        """
        估算文案时长（秒）
        中文平均语速: 4-5字/秒
        """
        char_count = len(script)
        duration = int(char_count / 4.5)
        return max(15, min(60, duration))  # 限制在15-60秒


def main():
    """测试文案生成"""
    generator = ScriptGenerator()

    # 测试热点
    test_hotspot = {
        "title": "AI技术如何改变我们的生活",
        "heat": 1234567
    }

    # 生成3种风格文案
    scripts = generator.generate_scripts(test_hotspot)

    for script in scripts:
        print(f"\n{'='*50}")
        print(f"风格: {script['style']}")
        print(f"时长: {script['duration']}秒")
        print(f"文案:\n{script['script']}")


if __name__ == "__main__":
    main()
