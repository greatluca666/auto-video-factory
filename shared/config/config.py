"""
配置管理模块
从环境变量加载配置
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 加载.env文件
load_dotenv()

class LLMConfig(BaseModel):
    """LLM配置"""
    anthropic_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    openai_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    openai_base_url: str = Field(default_factory=lambda: os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    qwen_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("QWEN_API_KEY"))

    # 默认使用的LLM提供商
    default_provider: str = "openai"  # anthropic, openai, qwen

class HotspotConfig(BaseModel):
    """热点采集配置"""
    weibo_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("WEIBO_API_KEY"))
    weibo_cookie: Optional[str] = Field(default_factory=lambda: os.getenv("WEIBO_COOKIE"))

    # 热点采集间隔(秒)
    fetch_interval: int = 7200  # 2小时

class VideoGeneratorConfig(BaseModel):
    """视频生成配置"""
    heygen_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("HEYGEN_API_KEY"))
    azure_tts_key: Optional[str] = Field(default_factory=lambda: os.getenv("AZURE_TTS_KEY"))
    azure_tts_region: str = Field(default_factory=lambda: os.getenv("AZURE_TTS_REGION", "eastus"))

    # 视频参数
    video_quality: str = Field(default_factory=lambda: os.getenv("VIDEO_QUALITY", "1080p"))
    video_fps: int = Field(default_factory=lambda: int(os.getenv("VIDEO_FPS", "30")))
    video_duration_min: int = 15  # 最短15秒
    video_duration_max: int = 60  # 最长60秒

class ImageGeneratorConfig(BaseModel):
    """图片生成配置"""
    replicate_api_token: Optional[str] = Field(default_factory=lambda: os.getenv("REPLICATE_API_TOKEN"))
    stability_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("STABILITY_API_KEY"))

    # 自定义图片生成API
    custom_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("IMAGE_GEN_API_KEY"))
    custom_base_url: Optional[str] = Field(default_factory=lambda: os.getenv("IMAGE_GEN_BASE_URL"))
    custom_model: str = Field(default_factory=lambda: os.getenv("IMAGE_GEN_MODEL", "gpt-image-2"))

    # 默认使用的图片生成器
    default_provider: str = "custom"  # replicate, stability, custom

class PublisherConfig(BaseModel):
    """发布平台配置"""
    # 抖音
    douyin_client_key: Optional[str] = Field(default_factory=lambda: os.getenv("DOUYIN_CLIENT_KEY"))
    douyin_client_secret: Optional[str] = Field(default_factory=lambda: os.getenv("DOUYIN_CLIENT_SECRET"))
    douyin_access_token: Optional[str] = Field(default_factory=lambda: os.getenv("DOUYIN_ACCESS_TOKEN"))

    # 快手
    kuaishou_app_id: Optional[str] = Field(default_factory=lambda: os.getenv("KUAISHOU_APP_ID"))
    kuaishou_app_secret: Optional[str] = Field(default_factory=lambda: os.getenv("KUAISHOU_APP_SECRET"))

    # 视频号
    weixin_app_id: Optional[str] = Field(default_factory=lambda: os.getenv("WEIXIN_APP_ID"))
    weixin_app_secret: Optional[str] = Field(default_factory=lambda: os.getenv("WEIXIN_APP_SECRET"))

    # 发布策略
    auto_publish: bool = True  # 是否自动发布
    publish_platforms: list[str] = ["douyin", "kuaishou", "weixin"]  # 发布平台列表

class AppConfig(BaseModel):
    """应用配置"""
    working_dir: Path = Field(default_factory=lambda: Path(os.getenv("WORKING_DIR", "./output")))
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    max_workers: int = Field(default_factory=lambda: int(os.getenv("MAX_WORKERS", "5")))

    # 子配置
    llm: LLMConfig = Field(default_factory=LLMConfig)
    hotspot: HotspotConfig = Field(default_factory=HotspotConfig)
    video_generator: VideoGeneratorConfig = Field(default_factory=VideoGeneratorConfig)
    image_generator: ImageGeneratorConfig = Field(default_factory=ImageGeneratorConfig)
    publisher: PublisherConfig = Field(default_factory=PublisherConfig)

    def __init__(self, **data):
        super().__init__(**data)
        # 确保工作目录存在
        self.working_dir.mkdir(parents=True, exist_ok=True)

# 全局配置实例
config = AppConfig()
