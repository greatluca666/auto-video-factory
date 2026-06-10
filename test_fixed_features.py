"""
测试修复后的3个功能:
1. AI生图片头（替代TextClip乱码）
2. 画面与旁白匹配（脚本prompt优化）
3. AI生图结尾
"""
from plan_b_image_montage.script_generator.generator import StoryboardGenerator
from plan_b_image_montage.image_generator.generator import ImageGenerator
from plan_b_image_montage.video_editor.editor import VideoEditor
from loguru import logger


def main():
    logger.info("=== 测试修复后功能 ===")

    # 1. 生成脚本（含画面旁白匹配约束）
    logger.info("生成分镜脚本（画面与旁白严格对应）")
    script_gen = StoryboardGenerator()
    test_hotspot = {
        "title": "2026年AI技术改变生活方式",
        "heat": 9876543
    }
    storyboard = script_gen.generate_storyboard(test_hotspot, target_duration=45)

    if not storyboard:
        logger.error("脚本生成失败")
        return

    logger.info(f"脚本生成成功: {len(storyboard['scenes'])}个场景")
    for idx, scene in enumerate(storyboard['scenes']):
        logger.info(f"  场景{idx+1}: 旁白='{scene['narration'][:20]}...' 画面='{scene['image_prompt'][:30]}...'")

    # 2. 生成图片
    logger.info("生成场景图片")
    image_gen = ImageGenerator()
    images = image_gen.generate_images(storyboard)

    if not images:
        logger.error("图片生成失败")
        return

    logger.info(f"图片生成成功: {len(images)}张")

    # 3. 生成视频（含AI片头+AI结尾）
    logger.info("生成完整视频（AI片头 + 正片 + AI结尾）")
    editor = VideoEditor()
    result = editor.create_video(storyboard, images)

    if result:
        logger.info("=== 测试完成 ===")
        logger.info(f"视频路径: {result['video_path']}")
        logger.info(f"总时长: {result['duration']:.2f}秒")
        logger.info(f"文件大小: {result['size_mb']}MB")
    else:
        logger.error("视频生成失败")


if __name__ == "__main__":
    main()
