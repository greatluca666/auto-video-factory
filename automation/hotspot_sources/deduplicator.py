"""
热点去重模块
基于标题相似度合并同一事件
"""
from typing import List, Dict
from difflib import SequenceMatcher
from loguru import logger


class HotspotDeduplicator:
    """热点去重器"""

    def __init__(self, similarity_threshold: float = 0.8):
        """
        Args:
            similarity_threshold: 相似度阈值（0-1）
        """
        self.threshold = similarity_threshold

    def deduplicate(self, hotspots: List[Dict]) -> List[Dict]:
        """
        去重合并热点

        Args:
            hotspots: 原始热点列表

        Returns:
            去重后的热点列表（保留热度最高的）
        """
        if not hotspots:
            return []

        # 按热度降序排序
        sorted_hotspots = sorted(hotspots, key=lambda x: x['heat'], reverse=True)

        deduplicated = []
        used_indices = set()

        for i, hotspot in enumerate(sorted_hotspots):
            if i in used_indices:
                continue

            # 找相似的热点
            similar_group = [hotspot]
            for j in range(i + 1, len(sorted_hotspots)):
                if j in used_indices:
                    continue

                similarity = self._calculate_similarity(
                    hotspot['title'],
                    sorted_hotspots[j]['title']
                )

                if similarity >= self.threshold:
                    similar_group.append(sorted_hotspots[j])
                    used_indices.add(j)

            # 合并：保留热度最高的，记录来源
            merged = self._merge_group(similar_group)
            deduplicated.append(merged)
            used_indices.add(i)

        logger.info(f"去重前: {len(hotspots)} 条，去重后: {len(deduplicated)} 条")
        return deduplicated

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算两个标题的相似度"""
        return SequenceMatcher(None, text1, text2).ratio()

    def _merge_group(self, group: List[Dict]) -> Dict:
        """
        合并相似热点组
        保留热度最高的，记录多平台来源
        """
        if len(group) == 1:
            return group[0]

        # 热度最高的作为主记录
        primary = group[0].copy()

        # 合并来源
        sources = [h['source'] for h in group]
        primary['sources'] = sources
        primary['cross_platform'] = len(set(sources)) > 1

        # 累加总热度
        primary['total_heat'] = sum(h['heat'] for h in group)

        return primary


def main():
    """测试去重"""
    test_hotspots = [
        {"id": "1", "title": "AI技术突破", "heat": 1000000, "source": "weibo"},
        {"id": "2", "title": "AI技术重大突破", "heat": 800000, "source": "baidu"},
        {"id": "3", "title": "某明星结婚", "heat": 500000, "source": "weibo"},
    ]

    deduplicator = HotspotDeduplicator(similarity_threshold=0.8)
    result = deduplicator.deduplicate(test_hotspots)

    for h in result:
        print(f"{h['title']} - 热度: {h.get('total_heat', h['heat'])} - 来源: {h.get('sources', [h['source']])}")


if __name__ == "__main__":
    main()
