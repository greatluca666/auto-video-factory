"""
方案A: 低成本文字口播流水线
热点采集模块 - 微博热搜爬虫
"""
import time
import requests
from typing import List, Dict
from loguru import logger
from shared.config import config


class WeiboHotspotCrawler:
    """微博热搜爬虫"""

    def __init__(self):
        self.api_key = config.hotspot.weibo_api_key
        self.cookie = config.hotspot.weibo_cookie
        self.base_url = "https://weibo.com/ajax/side/hotSearch"

    def fetch_hotspots(self, limit: int = 10) -> List[Dict]:
        """
        获取微博热搜

        Args:
            limit: 获取热搜数量

        Returns:
            热搜列表 [{"rank": 1, "title": "热搜标题", "heat": 1234567, "url": "..."}]
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Cookie": self.cookie,
                "Referer": "https://weibo.com"
            }

            response = requests.get(self.base_url, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get("ok") != 1:
                logger.error(f"微博API返回错误: {data}")
                return []

            hotspots = []
            realtime_list = data.get("data", {}).get("realtime", [])

            for idx, item in enumerate(realtime_list[:limit], 1):
                hotspot = {
                    "rank": idx,
                    "title": item.get("word", ""),
                    "heat": item.get("num", 0),
                    "url": f"https://s.weibo.com/weibo?q=%23{item.get('word', '')}%23",
                    "category": item.get("category", ""),
                    "timestamp": int(time.time())
                }
                hotspots.append(hotspot)

            logger.info(f"成功获取 {len(hotspots)} 条微博热搜")
            return hotspots

        except requests.RequestException as e:
            logger.error(f"请求微博热搜失败: {e}")
            return []
        except Exception as e:
            logger.error(f"解析微博热搜数据失败: {e}")
            return []

    def filter_hotspots(self, hotspots: List[Dict], keywords: List[str] = None,
                       exclude_keywords: List[str] = None) -> List[Dict]:
        """
        过滤热搜

        Args:
            hotspots: 热搜列表
            keywords: 包含关键词列表(任一匹配即保留)
            exclude_keywords: 排除关键词列表(任一匹配即排除)

        Returns:
            过滤后的热搜列表
        """
        if not hotspots:
            return []

        filtered = hotspots

        # 包含关键词过滤
        if keywords:
            filtered = [
                h for h in filtered
                if any(kw in h["title"] for kw in keywords)
            ]

        # 排除关键词过滤
        if exclude_keywords:
            filtered = [
                h for h in filtered
                if not any(kw in h["title"] for kw in exclude_keywords)
            ]

        logger.info(f"过滤后剩余 {len(filtered)} 条热搜")
        return filtered


def main():
    """测试热点采集"""
    crawler = WeiboHotspotCrawler()

    # 获取前10条热搜
    hotspots = crawler.fetch_hotspots(limit=10)

    for hotspot in hotspots:
        print(f"#{hotspot['rank']} {hotspot['title']} - 热度: {hotspot['heat']}")

    # 过滤示例: 只保留包含"科技"或"AI"的热搜
    # filtered = crawler.filter_hotspots(hotspots, keywords=["科技", "AI"])
    # print(f"\n过滤后: {len(filtered)} 条")


if __name__ == "__main__":
    main()
