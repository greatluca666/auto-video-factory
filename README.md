# 全自动营销号短视频生成工厂

全程无人工干预的短视频生成流水线，定时采集热点、生成文案、制作视频、自动发布。

## 📋 项目特点

- ✅ **全自动化**: 定时任务自动触发，无需人工干预
- ✅ **多平台发布**: 支持抖音、快手、视频号同步发布
- ✅ **AI驱动**: Claude/GPT生成爆款文案，HeyGen数字人口播
- ✅ **热点追踪**: 实时采集微博热搜，紧跟流量
- ✅ **多风格文案**: 情绪共鸣、干货清单、故事悬念三种风格

## 🏗️ 架构设计

### 方案A: 低成本文字口播流水线 (5-10元/条)

```
微博热搜 → AI文案生成 → HeyGen数字人 → 多平台发布
```

**成本**: 5-10元/条  
**产量**: 50-100条/天  
**适用**: 快速起号、批量测试

### 方案B: 图文混剪中等成本方案 (20-50元/条)

```
热点采集 → AI分镜脚本 → FLUX图片生成 → MoviePy剪辑 → 多平台发布
```

**成本**: 20-50元/条  
**产量**: 20-30条/天  
**适用**: 精品内容、长期运营

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env`，填入API密钥:

```bash
cp .env.example .env
```

必填配置:
- `ANTHROPIC_API_KEY` - Claude API密钥 (文案生成)
- `HEYGEN_API_KEY` - HeyGen API密钥 (数字人视频)
- `DOUYIN_ACCESS_TOKEN` - 抖音开放平台令牌
- `KUAISHOU_APP_ID` - 快手开放平台ID
- `WEIXIN_APP_ID` - 视频号开放平台ID

### 3. 启动定时任务

```bash
python main.py
```

调度器会自动执行:
- **每2小时**: 采集热搜并生成10条视频
- **高峰期** (8/12/18/22点): 生成15条多风格视频
- **凌晨3点**: 清理7天前的旧文件

### 4. 手动测试

测试单条视频生成:

```bash
python plan_a_text_video/main.py
```

## 📁 项目结构

```
auto-video-factory/
├── main.py                          # 主入口
├── requirements.txt                 # 依赖列表
├── .env.example                     # 环境变量模板
├── README.md                        # 项目文档
│
├── shared/                          # 共享模块
│   ├── config/                      # 配置管理
│   │   ├── config.py               # Pydantic配置类
│   │   └── __init__.py
│   └── utils/                       # 工具函数
│
├── plan_a_text_video/              # 方案A: 文字口播
│   ├── hotspot_crawler/            # 热点采集
│   │   ├── crawler.py              # 微博热搜爬虫
│   │   └── __init__.py
│   ├── script_generator/           # 文案生成
│   │   ├── generator.py            # AI文案生成器
│   │   └── __init__.py
│   ├── video_generator/            # 视频生成
│   │   ├── generator.py            # HeyGen数字人
│   │   └── __init__.py
│   ├── publisher/                  # 多平台发布
│   │   ├── publisher.py            # 抖音/快手/视频号
│   │   └── __init__.py
│   ├── main.py                     # 方案A主流程
│   └── __init__.py
│
├── plan_b_image_montage/           # 方案B: 图文混剪 (待实现)
│   ├── script_generator/           # 分镜脚本
│   ├── image_generator/            # FLUX图片生成
│   ├── video_editor/               # MoviePy剪辑
│   ├── publisher/                  # 多平台发布
│   └── main.py
│
├── workflows/                       # 工作流编排
│   ├── scheduler.py                # APScheduler定时任务
│   └── __init__.py
│
├── output/                          # 输出目录
│   ├── videos/                     # 生成的视频
│   └── plan_a/                     # 方案A输出
│
└── logs/                            # 日志目录
    └── app_2026-06-02.log
```

## ⚙️ 配置说明

### LLM配置

支持多个LLM提供商:

```python
# Claude (推荐)
ANTHROPIC_API_KEY=sk-ant-xxx
default_provider=anthropic

# OpenAI (备选)
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.openai.com/v1

# 通义千问 (国内)
QWEN_API_KEY=sk-xxx
```

### 视频生成配置

```python
# HeyGen数字人
HEYGEN_API_KEY=xxx
VIDEO_QUALITY=1080p
VIDEO_FPS=30

# Azure TTS (备选)
AZURE_TTS_KEY=xxx
AZURE_TTS_REGION=eastus
```

### 发布平台配置

```python
# 抖音
DOUYIN_CLIENT_KEY=xxx
DOUYIN_CLIENT_SECRET=xxx
DOUYIN_ACCESS_TOKEN=xxx

# 快手
KUAISHOU_APP_ID=xxx
KUAISHOU_APP_SECRET=xxx

# 视频号
WEIXIN_APP_ID=xxx
WEIXIN_APP_SECRET=xxx
```

## 📊 定时任务说明

### 任务1: 常规批量生成 (每2小时)

- 采集10条微博热搜
- 生成"情绪共鸣"风格文案
- 生成数字人视频
- 发布到3个平台

### 任务2: 高峰期生成 (8/12/18/22点)

- 采集15条微博热搜
- 生成3种风格文案 (情绪共鸣、干货清单、故事悬念)
- 生成数字人视频
- 发布到3个平台

### 任务3: 清理旧文件 (凌晨3点)

- 删除7天前的视频文件
- 释放磁盘空间

## 🎯 文案风格说明

### 1. 情绪共鸣型

- 前3秒强钩子 (反问/冲突/痛点)
- 触发用户情绪 (愤怒/震惊/后怕)
- 结尾引导互动
- 适合: 社会热点、争议话题

### 2. 干货清单型

- 数字标题 ("3个技巧""5步搞定")
- 每8-10秒新信息点
- 实用性强
- 适合: 知识科普、技能教学

### 3. 故事悬念型

- 开头设置悬念
- 第一人称叙事
- 中间有反转
- 适合: 个人经历、情感故事

## 💰 成本估算

### 方案A (文字口播)

| 项目 | 单价 | 说明 |
|------|------|------|
| Claude API | 2-3元/条 | 文案生成 |
| HeyGen数字人 | 3-5元/条 | 视频生成 |
| 平台API | 免费 | 发布接口 |
| **总计** | **5-10元/条** | 50-100条/天 |

### 方案B (图文混剪)

| 项目 | 单价 | 说明 |
|------|------|------|
| Claude API | 3-5元/条 | 分镜脚本 |
| FLUX图片 | 10-20元/条 | 5-10张图 |
| MoviePy剪辑 | 免费 | 本地处理 |
| Azure TTS | 2-5元/条 | 语音合成 |
| **总计** | **20-50元/条** | 20-30条/天 |

## 🔧 常见问题

### Q: 如何修改定时任务时间?

编辑 `workflows/scheduler.py`:

```python
# 修改为每4小时执行
self.scheduler.add_job(
    func=self.run_plan_a_batch,
    trigger=CronTrigger(hour="*/4"),  # 改这里
    ...
)
```

### Q: 如何过滤特定热点?

编辑 `plan_a_text_video/main.py`:

```python
# 只保留科技类热点
hotspots = self.crawler.filter_hotspots(
    hotspots,
    keywords=["科技", "AI", "互联网"],
    exclude_keywords=["明星", "娱乐"]
)
```

### Q: 如何关闭自动发布?

修改 `.env`:

```bash
# 在shared/config/config.py中设置
auto_publish = False
```

### Q: 如何更换数字人形象?

编辑 `plan_a_text_video/video_generator/generator.py`:

```python
"avatar_id": "Angela-inblackskirt-20220820",  # 改为其他ID
```

查看HeyGen可用形象: https://docs.heygen.com/reference/list-avatars-v2

## 📈 2026算法优化建议

根据2026年短视频算法偏好:

1. **收藏率 (35%)**: 结尾引导"建议收藏反复看"
2. **复看率 (25%)**: 信息密度高，值得二刷
3. **5秒完播 (20%)**: 前3秒强钩子，留住用户
4. **互动率 (20%)**: 评论区引导讨论

## 📝 开发计划

- [x] 方案A: 低成本文字口播流水线
- [ ] 方案B: 图文混剪中等成本方案
- [ ] 数据分析: 视频表现追踪
- [ ] A/B测试: 自动优选高转化文案
- [ ] 智能调度: 根据平台流量动态调整发布时间

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request!

---

**注意**: 使用本项目需遵守各平台的内容规范和API使用协议。
