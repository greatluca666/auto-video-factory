"""
测试新功能：营销号片头 + TTS + 时长同步
"""
from plan_b_image_montage.script_generator import StoryboardGenerator
from plan_b_image_montage.image_generator import ImageGenerator
from plan_b_image_montage.video_editor import VideoEditor
from loguru import logger

def main():
    logger.info("=== 测试新功能 ===")

    # 1. 生成分镜脚本
    hotspot = {
        "title": "AI技术如何改变我们的生活",
        "heat": 1234567
    }

    script_gen = StoryboardGenerator(provider="openai")
    logger.info("生成分镜脚本...")
    storyboard = script_gen.generate_storyboard(hotspot, target_duration=30)

    if not storyboard:
        logger.error("分镜脚本生成失败")
        return

    logger.info(f"脚本生成成功: {storyboard['scene_count']} 个场景")

    # 2. 生成图片
    image_gen = ImageGenerator(provider="custom")
    logger.info("生成图片...")
    images = image_gen.generate_images(storyboard)

    if not images:
        logger.error("图片生成失败")
        return

    logger.info(f"图片生成成功: {len(images)} 张")

    # 3. 生成视频（含片头 + TTS + 时长同步）
    video_editor = VideoEditor()
    logger.info("生成视频（含营销号片头 + TTS旁白）...")
    result = video_editor.create_video(storyboard, images)

    if result:
        logger.info("=== 测试完成 ===")
        logger.info(f"视频路径: {result['video_path']}")
        logger.info(f"总时长: {result['duration']:.2f}秒")
        logger.info(f"文件大小: {result['size_mb']}MB")
    else:
        logger.error("视频生成失败")

if __name__ == "__main__":
    main()
