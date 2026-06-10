# GitHub Actions 自动化部署指南

## 1. 配置 Secrets

进入仓库 Settings → Secrets and variables → Actions → New repository secret

添加以下密钥：

| Name | Value | 说明 |
|------|-------|------|
| `ANTHROPIC_API_KEY` | `sk-ant-xxx` | Claude API Key（可选） |
| `OPENAI_API_KEY` | `sk-xxx` | DeepSeek API Key |
| `OPENAI_BASE_URL` | `https://api.deepseek.com` | DeepSeek API 地址 |
| `REPLICATE_API_TOKEN` | `r8_xxx` | Replicate API Token（生图） |

## 2. 调整定时时间

编辑 `.github/workflows/daily-video-generation.yml`：

```yaml
on:
  schedule:
    - cron: '0 1 * * *'  # 每天 UTC 1:00 (北京时间 9:00)
```

Cron 格式：`分 时 日 月 周`

常见时间：
- `0 1 * * *` - 每天 UTC 1:00 (北京 9:00)
- `0 */6 * * *` - 每 6 小时一次
- `0 1,13 * * *` - 每天 1:00 和 13:00 两次

## 3. 手动触发

Actions 页面 → Daily Video Generation → Run workflow

## 4. 查看结果

运行完成后：
- 点击 workflow run
- 滚动到底部 "Artifacts"
- 下载 `generated-videos-xxx.zip`

## 5. 限制说明

**免费额度（GitHub Free）**：
- 2000 分钟/月 (约 33 小时)
- 单次任务最长 6 小时
- 500MB artifact 存储

**当前配置**：
- 单次运行约 30-60 分钟
- 每天运行一次 = 30-60 分钟/天 = 900-1800 分钟/月
- **刚好在免费额度内**

## 6. 成本优化建议

如需降低运行时间：

1. **减少分析量**：`automation/traffic_analyzer/analyzer.py:17`
   ```python
   self.heat_threshold = 2000000  # 提高到 200万（只分析高热度）
   ```

2. **减少爬取量**：`automation/scheduler.py`
   ```python
   hotspots = crawler.fetch_all_hotspots(limit_per_source=10)  # 改为 10
   ```

3. **只生成一个视频**：`automation/scheduler.py`
   ```python
   for hotspot in selected[:1]:  # 改为 [:1]
   ```

## 7. 故障排查

**任务失败？**
1. 查看 Actions 页面的日志
2. 检查 Secrets 是否配置正确
3. 检查 API Key 余额

**视频质量不满意？**
- 修改 `plan_b_image_montage/script_generator/generator.py` 的 prompt
- Push 后自动生效

**想立即测试？**
- Actions → Daily Video Generation → Run workflow → 手动触发
