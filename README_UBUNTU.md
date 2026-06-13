# Ubuntu 部署指南

## 系统要求

- Ubuntu 20.04 / 22.04 / 24.04
- Python 3.11+
- FFmpeg
- 至少 4GB RAM
- 至少 10GB 磁盘空间

## 快速开始

### 1. 安装系统依赖

```bash
# 更新软件源
sudo apt update && sudo apt upgrade -y

# 安装 Python 3.11
sudo apt install -y python3.11 python3.11-venv python3-pip

# 安装 FFmpeg
sudo apt install -y ffmpeg

# 安装其他依赖
sudo apt install -y git curl wget
```

### 2. 克隆项目

```bash
cd ~
git clone https://github.com/greatluca666/auto-video-factory.git
cd auto-video-factory
```

### 3. 创建虚拟环境

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 4. 安装 Python 依赖

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 配置环境变量

```bash
# 复制配置模板
cp .env.example .env

# 编辑配置文件
nano .env
```

**必填配置**：

```bash
# LLM 配置
OPENAI_API_KEY=your_openai_api_key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# 图片生成配置
IMAGE_GEN_API_KEY=your_image_api_key
IMAGE_GEN_BASE_URL=https://api.example.com/v1
IMAGE_GEN_MODEL=gpt-image-2

# 可选：微博热点
WEIBO_COOKIE=your_weibo_cookie

# 可选：发布平台
DOUYIN_CLIENT_KEY=
DOUYIN_CLIENT_SECRET=
DOUYIN_ACCESS_TOKEN=
```

保存退出：`Ctrl+X` → `Y` → `Enter`

### 6. 测试运行

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行测试
python -m automation.main
```

按 `Ctrl+C` 停止。

## 自动化部署（定时任务）

### 方式一：使用 systemd (推荐)

#### 1. 创建服务文件

```bash
sudo nano /etc/systemd/system/auto-video-factory.service
```

**内容**：

```ini
[Unit]
Description=Auto Video Factory
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/auto-video-factory
Environment="PATH=/home/YOUR_USERNAME/auto-video-factory/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/YOUR_USERNAME/auto-video-factory/venv/bin/python -m automation.main
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**替换**：
- `YOUR_USERNAME` → 你的用户名（运行 `whoami` 查看）

#### 2. 启动服务

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动服务
sudo systemctl start auto-video-factory

# 设置开机自启
sudo systemctl enable auto-video-factory

# 查看状态
sudo systemctl status auto-video-factory

# 查看日志
sudo journalctl -u auto-video-factory -f
```

#### 3. 管理服务

```bash
# 停止服务
sudo systemctl stop auto-video-factory

# 重启服务
sudo systemctl restart auto-video-factory

# 禁用开机自启
sudo systemctl disable auto-video-factory
```

### 方式二：使用 cron (简单)

```bash
# 编辑 crontab
crontab -e

# 添加定时任务（每天 9:00 执行）
0 9 * * * cd /home/YOUR_USERNAME/auto-video-factory && /home/YOUR_USERNAME/auto-video-factory/venv/bin/python -m automation.main >> /home/YOUR_USERNAME/auto-video-factory/logs/cron.log 2>&1
```

**替换** `YOUR_USERNAME` 为你的用户名。

## 手动运行

```bash
cd ~/auto-video-factory
source venv/bin/activate
python -m automation.main
```

## 查看输出

```bash
# 生成的视频
ls -lh output/videos/

# 日志文件
ls -lh logs/

# 查看最新日志
tail -f logs/automation_$(date +%Y-%m-%d).log
```

## 常见问题

### 1. FFmpeg 未安装

```bash
sudo apt install -y ffmpeg
ffmpeg -version
```

### 2. Python 版本不对

```bash
# 检查版本
python3.11 --version

# 如果没有 3.11，安装
sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.11 python3.11-venv
```

### 3. 权限错误

```bash
# 确保项目目录有写权限
chmod -R 755 ~/auto-video-factory
```

### 4. 虚拟环境激活失败

```bash
# 重新创建虚拟环境
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. 查看详细错误

```bash
# 启用 DEBUG 日志
export LOG_LEVEL=DEBUG
python -m automation.main
```

## 目录结构

```
auto-video-factory/
├── automation/          # 自动化逻辑
├── plan_b_image_montage/  # 视频生成
├── output/              # 输出目录（自动创建）
│   ├── videos/          # 生成的视频
│   ├── images/          # 临时图片
│   └── logs/            # 运行日志
├── logs/                # 主日志目录
├── .env                 # 环境变量配置
├── requirements.txt     # Python 依赖
└── README_UBUNTU.md     # 本文件
```

## 更新项目

```bash
cd ~/auto-video-factory
git pull
source venv/bin/activate
pip install -r requirements.txt --upgrade

# 如果使用 systemd
sudo systemctl restart auto-video-factory
```

## 卸载

```bash
# 停止服务
sudo systemctl stop auto-video-factory
sudo systemctl disable auto-video-factory
sudo rm /etc/systemd/system/auto-video-factory.service
sudo systemctl daemon-reload

# 删除项目
rm -rf ~/auto-video-factory

# 删除 cron 任务
crontab -e  # 然后删除相关行
```

## 技术支持

- GitHub Issues: https://github.com/greatluca666/auto-video-factory/issues
- 文档: 查看项目 README.md
