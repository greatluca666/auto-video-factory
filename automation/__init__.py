"""
自动化视频工厂
每日自动：爬取热点 → AI分析 → 生成30个视频 → 发布
"""
from .scheduler import SmartScheduler

__all__ = ['SmartScheduler']
