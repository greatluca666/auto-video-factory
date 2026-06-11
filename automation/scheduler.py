"""
智能调度器
每日30个视频任务规划与执行
"""
import json
import time
from pathlib import Path
from typing import List, Dict
from datetime import datetime
from loguru import logger
from shared.config import config

from automation.hotspot_sources import MultiSourceCrawler, HotspotDeduplicator
from automation.traffic_analyzer import TrafficAnalyzer
from automation.content_library import ContentLibrary
from plan_b_image_montage.main import PlanBWorkflow


class SmartScheduler:
    """智能调度器"""

    def __init__(self):
        self.daily_target = 30  # 每天30个视频
        self.publish_hours = [8, 12, 18, 22]  # 发布时段
        self.videos_per_slot = self.daily_target // len(self.publish_hours)

        # 模块初始化
        self.crawler = MultiSourceCrawler()
        self.deduplicator = HotspotDeduplicator(similarity_threshold=0.8)
        self.analyzer = TrafficAnalyzer()
        self.content_library = ContentLibrary()
        self.video_workflow = PlanBWorkflow()

        # 任务存储
        self.task_dir = config.working_dir / "tasks"
        self.task_dir.mkdir(parents=True, exist_ok=True)
        self.task_file = self.task_dir / f"tasks_{datetime.now().strftime('%Y%m%d')}.json"

    def plan_daily_tasks(self) -> List[Dict]:
        """
        规划当天30个任务

        Returns:
            任务列表
        """
        logger.info("=" * 60)
        logger.info("开始规划每日任务")
        logger.info("=" * 60)

        # 1. 爬取多源热点
        logger.info("步骤1: 爬取多平台热点")
        raw_hotspots = self.crawler.fetch_all_hotspots(limit_per_source=20)

        if not raw_hotspots:
            logger.warning("未获取到热点，将100%使用备选内容")

        # 2. 去重
        logger.info("步骤2: 热点去重")
        unique_hotspots = self.deduplicator.deduplicate(raw_hotspots)

        # 3. 流量分析
        logger.info("步骤3: 流量价值分析")
        analyzed_hotspots = self.analyzer.batch_analyze(unique_hotspots)

        # 筛选通过的热点
        selected_hotspots = [h for h in analyzed_hotspots if h.get('selected', False)]
        logger.info(f"通过筛选的热点: {len(selected_hotspots)} 条")

        # 4. 智能分配：热点 + 备选内容
        logger.info("步骤4: 智能内容分配")
        tasks = []

        if len(selected_hotspots) >= self.daily_target:
            # 热点够用：优先使用热点
            logger.info(f"热点充足，使用前{self.daily_target}个热点")
            for i, hotspot in enumerate(selected_hotspots[:self.daily_target]):
                tasks.append(self._create_task_from_hotspot(hotspot, i))

        else:
            # 热点不够：补充备选内容
            hotspot_count = len(selected_hotspots)
            backup_count = self.daily_target - hotspot_count

            logger.info(f"热点不足，使用 {hotspot_count} 个热点 + {backup_count} 个备选内容")

            # 添加热点任务
            for i, hotspot in enumerate(selected_hotspots):
                tasks.append(self._create_task_from_hotspot(hotspot, i))

            # 确保备选内容池充足
            self.content_library.ensure_pool_size()

            # 添加备选内容任务
            backup_contents = self.content_library.get_unused_content(limit=backup_count)
            for i, content in enumerate(backup_contents):
                tasks.append(self._create_task_from_backup(content, hotspot_count + i))

        # 5. 分配到时段
        logger.info("步骤5: 分配到发布时段")
        tasks = self._assign_time_slots(tasks)

        # 6. 保存任务
        self._save_tasks(tasks)

        logger.info(f"任务规划完成: 共 {len(tasks)} 个任务")
        logger.info("=" * 60)

        return tasks

    def execute_tasks(self, hour: int = None):
        """
        执行指定时段的任务

        Args:
            hour: 时段（8/12/18/22），None表示执行所有pending任务
        """
        logger.info(f"\n{'=' * 60}")
        if hour is None:
            logger.info("执行所有pending任务（CI模式）")
        else:
            logger.info(f"执行 {hour}点 时段任务")
        logger.info(f"{'=' * 60}")

        # 加载任务
        tasks = self._load_tasks()

        if hour is None:
            # CI模式：执行所有pending任务
            slot_tasks = [t for t in tasks if t['status'] == 'pending']
        else:
            # 定时模式：执行指定时段任务
            slot_tasks = [t for t in tasks if t['scheduled_hour'] == hour and t['status'] == 'pending']

        logger.info(f"待执行任务: {len(slot_tasks)} 个")

        for idx, task in enumerate(slot_tasks, 1):
            logger.info(f"\n任务 {idx}/{len(slot_tasks)}: {task['title']}")

            try:
                # 更新状态
                task['status'] = 'generating'
                self._save_tasks(tasks)

                # 生成视频（task_id 用于按视频隔离图片输出）
                if task['content_type'] == 'hotspot':
                    hotspot = {
                        "title": task['title'],
                        "heat": task.get('heat', 0)
                    }
                    result = self.video_workflow.run_single(hotspot['title'], task_id=task['task_id'])

                else:  # backup
                    # 备选内容转换为热点格式
                    hotspot = {
                        "title": task['title'],
                        "heat": 0
                    }
                    result = self.video_workflow.run_single(task['title'], task_id=task['task_id'])

                    # 标记内容已使用
                    self.content_library.mark_as_used(task['content_id'])

                if result:
                    task['status'] = 'completed'
                    task['video_path'] = str(result['video_info']['video_path'])
                    task['publish_results'] = result['publish_results']
                    logger.info(f"✓ 任务完成: {task['title']}")
                else:
                    task['status'] = 'failed'
                    logger.error(f"✗ 任务失败: {task['title']}")

            except Exception as e:
                task['status'] = 'failed'
                task['error'] = str(e)
                logger.error(f"✗ 任务异常: {task['title']} - {e}")

            finally:
                self._save_tasks(tasks)

        # 统计
        completed = sum(1 for t in slot_tasks if t['status'] == 'completed')
        logger.info(f"\n时段执行完成: {completed}/{len(slot_tasks)} 成功")

    def _create_task_from_hotspot(self, hotspot: Dict, index: int) -> Dict:
        """从热点创建任务"""
        return {
            "task_id": f"task_{datetime.now().strftime('%Y%m%d')}_{index:03d}",
            "content_type": "hotspot",
            "content_id": hotspot['id'],
            "title": hotspot['title'],
            "heat": hotspot.get('total_heat', hotspot.get('heat', 0)),
            "ai_score": hotspot.get('ai_score', 0),
            "priority": 10 - index // 3,  # 前面的热点优先级高
            "scheduled_hour": None,
            "status": "pending",
            "video_path": None,
            "publish_results": {},
            "created_at": int(time.time())
        }

    def _create_task_from_backup(self, content: Dict, index: int) -> Dict:
        """从备选内容创建任务"""
        return {
            "task_id": f"task_{datetime.now().strftime('%Y%m%d')}_{index:03d}",
            "content_type": "backup",
            "content_id": content['id'],
            "title": content['title'],
            "heat": 0,
            "ai_score": 7.0,  # 备选内容默认7分
            "priority": 5,  # 中等优先级
            "scheduled_hour": None,
            "status": "pending",
            "video_path": None,
            "publish_results": {},
            "created_at": int(time.time())
        }

    def _assign_time_slots(self, tasks: List[Dict]) -> List[Dict]:
        """分配任务到时段"""
        # 按优先级排序
        sorted_tasks = sorted(tasks, key=lambda x: x['priority'], reverse=True)

        # 均匀分配到4个时段
        for i, task in enumerate(sorted_tasks):
            slot_index = i % len(self.publish_hours)
            task['scheduled_hour'] = self.publish_hours[slot_index]

        return sorted_tasks

    def _load_tasks(self) -> List[Dict]:
        """加载任务"""
        if not self.task_file.exists():
            return []

        try:
            with open(self.task_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载任务失败: {e}")
            return []

    def _save_tasks(self, tasks: List[Dict]):
        """保存任务"""
        try:
            with open(self.task_file, 'w', encoding='utf-8') as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务失败: {e}")


def main():
    """测试调度器"""
    scheduler = SmartScheduler()

    # 规划任务
    tasks = scheduler.plan_daily_tasks()

    print(f"\n今日任务: {len(tasks)} 个")
    for t in tasks[:5]:
        print(f"  [{t['scheduled_hour']}点] {t['title']} - 类型:{t['content_type']} 优先级:{t['priority']}")

    # 执行某时段任务（示例：8点）
    # scheduler.execute_tasks(8)


if __name__ == "__main__":
    main()
