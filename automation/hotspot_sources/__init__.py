"""
多源热点采集模块
支持：微博、百度、头条、抖音
"""
from .multi_crawler import MultiSourceCrawler
from .deduplicator import HotspotDeduplicator

__all__ = ['MultiSourceCrawler', 'HotspotDeduplicator']
