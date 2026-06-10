"""
流量价值分析器
热度筛选 + AI评分
"""
import os
from typing import Dict, Optional
from anthropic import Anthropic
from openai import OpenAI
from loguru import logger
from shared.config import config


class TrafficAnalyzer:
    """流量价值分析器"""

    def __init__(self, provider: str = None):
        self.heat_threshold = 1000000  # 100万热度阈值
        self.ai_score_min = 7.0  # AI评分最低7分
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

    def analyze(self, hotspot: Dict) -> Dict:
        """
        分析热点流量价值

        Args:
            hotspot: 热点数据

        Returns:
            {
                "pass_threshold": bool,  # 是否通过热度阈值
                "ai_score": float,  # AI评分 (0-10)
                "reason": str,  # 评分理由
                "selected": bool  # 是否最终入选
            }
        """
        result = {
            "pass_threshold": False,
            "ai_score": 0.0,
            "reason": "",
            "selected": False
        }

        # 1. 热度硬过滤
        heat = hotspot.get('total_heat', hotspot.get('heat', 0))
        if heat < self.heat_threshold:
            result["reason"] = f"热度{heat}低于阈值{self.heat_threshold}"
            logger.debug(f"过滤: {hotspot['title']} - {result['reason']}")
            return result

        result["pass_threshold"] = True

        # 2. AI评分
        try:
            ai_score, reason = self._get_ai_score(hotspot)
            result["ai_score"] = ai_score
            result["reason"] = reason

            # 3. 综合判断
            if ai_score >= self.ai_score_min:
                result["selected"] = True
                logger.info(f"✓ {hotspot['title']} - 热度:{heat} 评分:{ai_score:.1f}")
            else:
                logger.debug(f"✗ {hotspot['title']} - 评分过低:{ai_score:.1f}")

        except Exception as e:
            # AI分析失败时降级：热度>=200万自动通过
            logger.warning(f"AI分析失败: {e}，使用降级规则")
            fallback_score = 7.5 if heat >= 2000000 else 5.0
            result["ai_score"] = fallback_score
            result["reason"] = "AI分析失败，基于热度判断"
            result["selected"] = fallback_score >= self.ai_score_min

        return result

    def _get_ai_score(self, hotspot: Dict) -> tuple[float, str]:
        """
        调用Claude分析话题质量

        Returns:
            (评分, 理由)
        """
        # 获取相关内容上下文
        related = hotspot.get('related_content', '')
        context_info = f"\n相关内容: {related[:300]}" if related else ""

        prompt = f"""请评估这个热点话题是否适合做短视频内容:

标题: {hotspot['title']}
热度: {hotspot.get('total_heat', hotspot.get('heat', 0))}
分类: {hotspot.get('category', '综合')}{context_info}

评估标准:
1. 受众广泛性 (年轻人是否关注)
2. 情绪共鸣度 (能否触发强烈情绪)
3. 内容可塑性 (是否有视觉呈现空间)
4. 时效性 (话题新鲜度)
5. 平台友好性 (是否涉及敏感话题)
6. 流量潜力 (根据相关讨论判断话题角度和热度趋势)

请给出0-10分评分，并简要说明理由（50字内）。
格式: 评分|理由
例如: 8.5|科技话题受众广，有视觉呈现空间，适合知识科普类短视频"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        ) if self.provider == "anthropic" else None

        if self.provider == "anthropic":
            response_text = message.content[0].text.strip()
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )
            # 防御性检查：某些异常情况 API 可能返回字符串
            if isinstance(response, str):
                raise ValueError(f"API返回异常格式: {response}")
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("AI返回空内容")
            response_text = content.strip()

        # 解析响应
        try:
            parts = response_text.split('|', 1)
            score = float(parts[0].strip())
            reason = parts[1].strip() if len(parts) > 1 else "无理由"
            return score, reason
        except Exception as e:
            logger.error(f"解析AI响应失败: {response_text} - {e}")
            raise

    def batch_analyze(self, hotspots: list[Dict]) -> list[Dict]:
        """
        批量分析热点

        Args:
            hotspots: 热点列表

        Returns:
            分析结果列表
        """
        import time
        results = []
        for idx, hotspot in enumerate(hotspots):
            analysis = self.analyze(hotspot)
            result = hotspot.copy()
            result.update(analysis)
            results.append(result)

            # 每个请求间隔 2 秒，避免 429 限流
            if idx < len(hotspots) - 1:
                time.sleep(2)

        selected_count = sum(1 for r in results if r['selected'])
        logger.info(f"批量分析完成: {len(hotspots)} 条热点，{selected_count} 条入选")

        return results


def main():
    """测试流量分析"""
    analyzer = TrafficAnalyzer()

    test_hotspots = [
        {"title": "AI技术重大突破", "heat": 1500000, "category": "科技"},
        {"title": "某明星恋情曝光", "heat": 800000, "category": "娱乐"},
        {"title": "新能源汽车降价", "heat": 1200000, "category": "财经"},
    ]

    results = analyzer.batch_analyze(test_hotspots)

    for r in results:
        status = "✓" if r['selected'] else "✗"
        print(f"{status} {r['title']} - 热度:{r['heat']} 评分:{r['ai_score']:.1f} - {r['reason']}")


if __name__ == "__main__":
    main()
