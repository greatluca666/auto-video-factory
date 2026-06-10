# 自动化视频工厂使用指南

## 功能特性

✅ **多源热点采集** - 微博/百度/头条/抖音热榜  
✅ **AI流量分析** - 100万热度阈值 + Claude评分  
✅ **智能内容池** - 知乎爬虫 + Claude生成备选内容  
✅ **自动调度** - 每天30个视频，分4个时段发布  
✅ **批量生成** - Plan B图文混剪流程  
✅ **多平台发布** - B站/抖音/快手并发上传  

## 快速开始

### 1. 启动自动化系统

```bash
python automation/main.py
```

系统会自动执行：
- **01:00** - 规划全天30个任务
- **08:00** - 生成并发布7-8个视频
- **12:00** - 生成并发布7-8个视频
- **18:00** - 生成并发布7-8个视频
- **22:00** - 生成并发布7-8个视频

### 2. 手动测试单个模块

#### 测试多源爬虫
```bash
python automation/hotspot_sources/multi_crawler.py
```

#### 测试流量分析
```bash
python automation/traffic_analyzer/analyzer.py
```

#### 测试备选内容库
```bash
python automation/content_library/library.py
```

#### 测试完整调度
```bash
python automation/scheduler.py
```

## 工作流程

```
[凌晨1点] 规划任务
    ↓
爬取热点（微博/百度/头条/抖音）
    ↓
去重合并（相似度>80%）
    ↓
流量分析（热度>=100万 + AI评分>=7）
    ↓
智能分配（热点优先，不够用备选内容补充）
    ↓
分配到4个时段（8/12/18/22点）
    ↓
[8/12/18/22点] 执行任务
    ↓
生成视频（Plan B图文混剪）
    ↓
并发发布（B站/抖音/快手）
    ↓
更新任务状态
```

## 核心配置

### 热度阈值
```python
# automation/traffic_analyzer/analyzer.py
self.heat_threshold = 1000000  # 100万
```

### AI评分标准
```python
# automation/traffic_analyzer/analyzer.py
self.ai_score_min = 7.0  # 最低7分
```

### 每日视频数量
```python
# automation/scheduler.py
self.daily_target = 30  # 每天30个
```

### 发布时段
```python
# automation/scheduler.py
self.publish_hours = [8, 12, 18, 22]
```

### 备选内容池大小
```python
# automation/content_library/library.py
self.min_pool_size = 50  # 最少50个
```

## 目录结构

```
automation/
├── main.py                      # 主入口（定时任务）
├── scheduler.py                 # 智能调度器
├── hotspot_sources/            # 多源热点采集
│   ├── multi_crawler.py        # 微博/百度/头条/抖音爬虫
│   └── deduplicator.py         # 去重合并
├── traffic_analyzer/           # 流量分析
│   └── analyzer.py             # 热度筛选 + AI评分
└── content_library/            # 备选内容库
    └── library.py              # 知乎爬虫 + Claude生成

output/
├── tasks/                      # 任务记录
│   └── tasks_20260607.json    # 当天任务列表
└── content_library/            # 备选内容池
    └── content_pool.json       # 50+个备选内容
```

## 数据格式

### 热点对象
```json
{
  "id": "hotspot_20260607_001",
  "title": "AI技术突破",
  "heat": 1500000,
  "source": "weibo",
  "category": "科技",
  "ai_score": 8.5,
  "selected": true
}
```

### 任务对象
```json
{
  "task_id": "task_20260607_001",
  "content_type": "hotspot",
  "title": "AI技术突破",
  "scheduled_hour": 8,
  "status": "completed",
  "video_path": "output/videos/xxx.mp4",
  "publish_results": {
    "bilibili": true,
    "douyin": true,
    "kuaishou": true
  }
}
```

## 变现策略

### 1. 平台收益
- **B站** - 创作激励（播放量）
- **抖音** - 中视频计划（播放时长）
- **快手** - 光合计划（播放量）

### 2. 带货变现
- 视频中植入产品链接
- 橱窗商品推广
- 直播带货引流

### 3. 私域引流
- 评论区引导加微信
- 简介留联系方式
- 建立社群矩阵

### 4. 预期收入
**保守估算**（30个视频/天）：
- 单视频平均播放：5000次
- 单个播放收益：0.01元
- 日收入：30 × 5000 × 0.01 = 1500元
- 月收入：1500 × 30 = 45000元

**成本**：
- Claude API：30条 × 5元 = 150元/天
- 图片生成：30条 × 20元 = 600元/天
- 服务器：100元/天
- **日成本**：850元
- **日净利**：650元
- **月净利**：19500元

## 常见问题

### Q: 爬虫被反爬怎么办？
A: 系统设计了降级策略，单平台失败不影响其它。全失败时100%使用备选内容。

### Q: 如何调整热点筛选标准？
A: 修改 `automation/traffic_analyzer/analyzer.py`：
- `heat_threshold` 调整热度阈值
- `ai_score_min` 调整AI评分最低标准

### Q: 如何增加每日视频数量？
A: 修改 `automation/scheduler.py`：
```python
self.daily_target = 50  # 改为50个
```

### Q: 发布失败怎么办？
A: 系统会记录失败任务，可手动重试：
```python
from automation.scheduler import SmartScheduler
scheduler = SmartScheduler()
scheduler.execute_tasks(8)  # 重新执行8点时段
```

### Q: 如何查看任务执行情况？
A: 查看任务文件：
```bash
cat output/tasks/tasks_20260607.json
```

## 注意事项

1. **API费用** - Claude + 图片生成每天约750元
2. **平台规则** - 遵守各平台内容规范
3. **敏感话题** - AI会自动过滤低分话题
4. **账号安全** - 分散多账号发布降低风险
5. **内容质量** - 定期检查视频质量和用户反馈

## 高级优化

### 1. A/B测试
修改 `scheduler.py` 添加测试逻辑：
- 同一内容生成多个版本
- 先发小样本测试
- 数据好的版本批量发

### 2. 数据分析
接入平台API获取数据：
- 播放量、完播率
- 点赞、评论、转发
- 用户画像分析

### 3. 动态调整
根据历史数据优化：
- 热点类型偏好
- 发布时间优化
- 内容风格调整

## 技术支持

问题反馈：查看日志 `logs/automation_*.log`
