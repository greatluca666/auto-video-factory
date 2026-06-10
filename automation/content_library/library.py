"""
备选内容库管理
知乎爬虫 + Claude生成名人故事/历史知识
"""
import os
import json
import time
import requests
from pathlib import Path
from typing import List, Dict, Optional
from anthropic import Anthropic
from openai import OpenAI
from loguru import logger
from shared.config import config


class ContentLibrary:
    """备选内容库"""

    def __init__(self, provider: str = None):
        self.storage_dir = config.working_dir / "content_library"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.pool_file = self.storage_dir / "content_pool.json"

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

        self.min_pool_size = 50  # 最少保持50个备选内容

    def get_unused_content(self, limit: int = 10) -> List[Dict]:
        """
        获取未使用的备选内容

        Args:
            limit: 获取数量

        Returns:
            备选内容列表
        """
        pool = self._load_pool()

        # 按使用次数和最后使用时间排序（优先未使用的）
        sorted_pool = sorted(
            pool,
            key=lambda x: (x['used_count'], x['last_used'] or 0)
        )

        result = sorted_pool[:limit]
        logger.info(f"获取备选内容: {len(result)}/{len(pool)}")

        return result

    def mark_as_used(self, content_id: str):
        """标记内容已使用"""
        pool = self._load_pool()

        for item in pool:
            if item['id'] == content_id:
                item['used_count'] += 1
                item['last_used'] = int(time.time())
                break

        self._save_pool(pool)

    def ensure_pool_size(self):
        """确保内容池有足够内容"""
        pool = self._load_pool()
        current_size = len(pool)

        if current_size >= self.min_pool_size:
            logger.info(f"内容池充足: {current_size}/{self.min_pool_size}")
            return

        need_count = self.min_pool_size - current_size
        logger.info(f"内容池不足，需补充 {need_count} 个")

        # 混合策略：70% Claude生成 + 30% 知乎爬取
        claude_count = int(need_count * 0.7)
        zhihu_count = need_count - claude_count

        # 知乎爬取（可能失败）
        new_contents = []
        zhihu_results = self.fetch_from_zhihu(zhihu_count)
        new_contents.extend(zhihu_results)

        # Claude生成（补齐知乎不足的部分）
        claude_actual = claude_count + (zhihu_count - len(zhihu_results))
        new_contents.extend(self._generate_with_claude(claude_actual))

        # 添加到池中
        pool.extend(new_contents)
        self._save_pool(pool)

        logger.info(f"内容池补充完成: {len(pool)}/{self.min_pool_size}")

    def fetch_from_zhihu(self, limit: int = 10) -> List[Dict]:
        """
        爬取知乎故事话题高赞回答

        Args:
            limit: 爬取数量

        Returns:
            内容列表
        """
        try:
            # 知乎API需要认证，这里提供基础框架
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "authorization": "Bearer " + config.hotspot.zhihu_token if hasattr(config.hotspot, 'zhihu_token') else ""
            }

            # 示例：爬取"故事"话题
            response = requests.get(
                "https://www.zhihu.com/api/v4/topics/19550517/feeds/top_activity",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            contents = []
            for item in data.get('data', [])[:limit]:
                target = item.get('target', {})
                if target.get('type') == 'answer':
                    content = {
                        "id": f"zhihu_{target['id']}",
                        "title": target.get('question', {}).get('title', ''),
                        "type": "story",
                        "source": "zhihu",
                        "content": target.get('excerpt', ''),
                        "url": f"https://www.zhihu.com/question/{target.get('question', {}).get('id')}/answer/{target['id']}",
                        "used_count": 0,
                        "last_used": None,
                        "timestamp": int(time.time())
                    }
                    contents.append(content)

            logger.info(f"知乎爬取成功: {len(contents)} 条")
            return contents

        except Exception as e:
            logger.error(f"知乎爬取失败: {e}")
            return []

    def _generate_with_claude(self, count: int = 10) -> List[Dict]:
        """
        用Claude生成名人故事/历史知识

        Args:
            count: 生成数量

        Returns:
            内容列表
        """
        topics = [
            ("celebrity", "名人励志故事", "马斯克/乔布斯/比尔盖茨等名人的创业/成功故事"),
            ("history", "历史冷知识", "有趣的历史事件/人物轶事"),
            ("knowledge", "实用生活知识", "健康/理财/职场技巧")
        ]

        contents = []

        for i in range(count):
            topic_type, topic_name, topic_desc = topics[i % len(topics)]
            try:
                content = self._generate_single_story(topic_type, topic_name, topic_desc)
                if content:
                    contents.append(content)
                    time.sleep(1)  # 避免请求过快
            except Exception as e:
                logger.error(f"生成失败: {e}")

        logger.info(f"Claude生成成功: {len(contents)} 条")
        return contents

    def _generate_single_story(self, topic_type: str, topic_name: str, topic_desc: str) -> Optional[Dict]:
        """生成单个故事"""
        prompt = f"""生成一个适合短视频的{topic_name}:

要求:
1. 标题吸引人（15字内）
2. 内容完整（200-300字）
3. 有情节/有悬念
4. 适合配图呈现
5. 主题: {topic_desc}

格式:
标题: xxx
内容: xxx
"""

        if self.provider == "anthropic":
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text.strip()
        else:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.choices[0].message.content
            if content is None:
                raise ValueError("AI返回空内容")
            response_text = content.strip()

        # 解析响应
        try:
            lines = response_text.split('\n')
            title = ""
            content_lines = []

            for line in lines:
                if line.startswith('标题:'):
                    title = line.replace('标题:', '').strip()
                elif line.startswith('内容:'):
                    content_lines.append(line.replace('内容:', '').strip())
                elif content_lines:
                    content_lines.append(line.strip())

            content_text = '\n'.join(content_lines).strip()

            if not title or not content_text:
                logger.warning(f"解析失败: {response_text[:100]}")
                return None

            return {
                "id": f"claude_{topic_type}_{int(time.time())}_{hash(title) % 10000}",
                "title": title,
                "type": topic_type,
                "source": "claude",
                "content": content_text,
                "url": "",
                "used_count": 0,
                "last_used": None,
                "timestamp": int(time.time())
            }

        except Exception as e:
            logger.error(f"解析Claude响应失败: {e}")
            return None

    def _load_pool(self) -> List[Dict]:
        """加载内容池"""
        if not self.pool_file.exists():
            return []

        try:
            with open(self.pool_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载内容池失败: {e}")
            return []

    def _save_pool(self, pool: List[Dict]):
        """保存内容池"""
        try:
            with open(self.pool_file, 'w', encoding='utf-8') as f:
                json.dump(pool, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存内容池失败: {e}")


def main():
    """测试内容库"""
    library = ContentLibrary()

    # 确保内容池充足
    library.ensure_pool_size()

    # 获取10个未使用的内容
    contents = library.get_unused_content(limit=10)

    for c in contents:
        print(f"[{c['type']}] {c['title']} - 来源:{c['source']} 使用次数:{c['used_count']}")


if __name__ == "__main__":
    main()
