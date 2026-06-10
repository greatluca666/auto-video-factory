"""
多源热点爬虫
整合微博、百度、头条、抖音热榜
"""
import time
import hashlib
import requests
from typing import List, Dict, Optional
from loguru import logger
from shared.config import config


class MultiSourceCrawler:
    """多平台热点采集器"""

    def __init__(self):
        self.sources = {
            'weibo': self._fetch_weibo,
            'baidu': self._fetch_baidu,
            'toutiao': self._fetch_toutiao,
        }

    def fetch_all_hotspots(self, limit_per_source: int = 20) -> List[Dict]:
        """
        采集所有平台热点

        Args:
            limit_per_source: 每个平台采集数量

        Returns:
            热点列表
        """
        all_hotspots = []

        for source_name, fetch_func in self.sources.items():
            try:
                logger.info(f"采集 {source_name} 热点")
                hotspots = fetch_func(limit=limit_per_source)
                all_hotspots.extend(hotspots)
                logger.info(f"{source_name}: {len(hotspots)} 条")
                time.sleep(2)  # 避免请求过快
            except Exception as e:
                logger.warning(f"{source_name} 采集失败: {e}")
                continue

        logger.info(f"总计采集 {len(all_hotspots)} 条热点")
        return all_hotspots

    def _fetch_weibo(self, limit: int = 20) -> List[Dict]:
        """采集微博热搜"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://weibo.com"
            }

            response = requests.get(
                "https://weibo.com/ajax/side/hotSearch",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if data.get("ok") != 1:
                return []

            hotspots = []
            realtime_list = data.get("data", {}).get("realtime", [])

            for idx, item in enumerate(realtime_list[:limit], 1):
                word = item.get('word', '')
                hotspot = {
                    "id": self._generate_id(f"weibo_{word}"),
                    "title": word,
                    "heat": item.get("num", 0),
                    "source": "weibo",
                    "category": item.get("category", "综合"),
                    "url": f"https://s.weibo.com/weibo?q=%23{word}%23",
                    "timestamp": int(time.time()),
                    "related_content": self._fetch_weibo_content(word)
                }
                hotspots.append(hotspot)

            return hotspots

        except Exception as e:
            logger.error(f"微博采集失败: {e}")
            return []

    def _fetch_weibo_content(self, keyword: str) -> str:
        """抓取微博相关内容（前3条微博摘要）"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://weibo.com"
            }

            # 搜索相关微博
            response = requests.get(
                f"https://m.weibo.cn/api/container/getIndex?containerid=100103type%3D1%26q%3D{keyword}",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            cards = data.get("data", {}).get("cards", [])
            contents = []

            for card in cards[:3]:  # 取前3条
                mblog = card.get("mblog", {})
                text = mblog.get("text", "")
                if text:
                    # 简单清理HTML标签
                    import re
                    text = re.sub(r'<[^>]+>', '', text)
                    contents.append(text[:200])  # 每条最多200字

            return " | ".join(contents) if contents else ""

        except Exception as e:
            logger.debug(f"微博内容抓取失败: {e}")
            return ""

    def _fetch_baidu(self, limit: int = 20) -> List[Dict]:
        """采集百度热搜"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(
                "https://top.baidu.com/api/board?platform=pc&tab=realtime",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            hotspots = []
            cards = data.get("data", {}).get("cards", [])

            for card in cards:
                items = card.get("content", [])
                if not isinstance(items, list):
                    continue
                for item in items[:limit]:
                    if not isinstance(item, dict):
                        continue
                    word = item.get("word", "")
                    if not word:
                        continue
                    hotspot = {
                        "id": self._generate_id(f"baidu_{word}"),
                        "title": word,
                        "heat": int(item.get("hotScore", 0) or 0),
                        "source": "baidu",
                        "category": item.get("hotTag", "综合"),
                        "url": item.get("url", ""),
                        "timestamp": int(time.time()),
                        "related_content": item.get("desc", "")  # 百度API自带简介
                    }
                    hotspots.append(hotspot)
                break

            return hotspots[:limit]

        except Exception as e:
            logger.error(f"百度采集失败: {e}")
            return []

    def _fetch_toutiao(self, limit: int = 20) -> List[Dict]:
        """采集头条热榜"""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(
                "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            hotspots = []
            items = data.get("data", [])

            for idx, item in enumerate(items[:limit], 1):
                hotspot = {
                    "id": self._generate_id(f"toutiao_{item.get('Title', '')}"),
                    "title": item.get("Title", ""),
                    "heat": int(item.get("HotValue", 0)),
                    "source": "toutiao",
                    "category": item.get("Label", "综合"),
                    "url": item.get("Url", ""),
                    "timestamp": int(time.time()),
                    "related_content": item.get("ClusterIdStr", "")  # 头条可能有简介字段
                }
                hotspots.append(hotspot)

            return hotspots

        except Exception as e:
            logger.error(f"头条采集失败: {e}")
            return []

    def _fetch_douyin(self, limit: int = 20) -> List[Dict]:
        """采集抖音热榜"""
        try:
            # 抖音热榜API需要cookie或token，这里提供基础框架
            # 实际使用需配置有效的认证信息
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(
                "https://api.vvhan.com/api/hotlist/douyinHot",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            hotspots = []
            items = data.get("data", [])

            for idx, item in enumerate(items[:limit], 1):
                title = item.get("title", "")
                if not title:
                    continue
                hot_str = str(item.get("hot", "0"))
                hot_num = ''.join(c for c in hot_str if c.isdigit())
                heat = int(hot_num) if hot_num else 0

                hotspot = {
                    "id": self._generate_id(f"douyin_{title}"),
                    "title": title,
                    "heat": heat,
                    "source": "douyin",
                    "category": "综合",
                    "url": item.get("url", f"https://www.douyin.com/search/{title}"),
                    "timestamp": int(time.time())
                }
                hotspots.append(hotspot)

            return hotspots

        except Exception as e:
            logger.error(f"抖音采集失败: {e}")
            return []

    def _generate_id(self, text: str) -> str:
        """生成热点唯一ID"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]


def main():
    """测试多源爬虫"""
    crawler = MultiSourceCrawler()
    hotspots = crawler.fetch_all_hotspots(limit_per_source=10)

    for h in hotspots[:20]:
        print(f"[{h['source']}] {h['title']} - 热度: {h['heat']}")


if __name__ == "__main__":
    main()
