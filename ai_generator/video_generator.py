#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI视频生成器 - 智谱CogVideoX-3
支持文生视频和图生视频
"""

from pathlib import Path

from .zhipu_client import ZhipuClient

# 视频尺寸映射
VIDEO_SIZES = {
    "1:1": "1080x1080",
    "16:9": "1920x1080",
    "9:16": "1080x1920",
    "4:3": "1440x1080",
    "3:4": "1080x1440",
}


def _run_verify(video_path, prompt):
    """生成后自动验证"""
    from .quality_checker import check
    print("\n[自动验证] 生成完成，开始质量评估...\n")
    return check(video_path, prompt)


def generate_from_text(prompt, output_path, ar="16:9", quality="speed", model=None,
                        auto_verify=False):
    """
    文生视频

    Args:
        prompt: 提示词
        output_path: 输出文件路径 (.mp4)
        ar: 宽高比 (1:1, 16:9, 9:16, 4:3, 3:4)
        quality: 生成质量 (speed / quality)
        model: 模型名称 (默认 cogvideox-3)
        auto_verify: 生成后自动验证质量

    Returns:
        str: 保存的文件路径
    """
    client = ZhipuClient()
    size = VIDEO_SIZES.get(ar, "1920x1080")

    print(f"\n生成视频: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    print(f"  模型: {model or 'cogvideox-3'}, 尺寸: {size}, 质量: {quality}")
    print(f"  按 Ctrl+C 可中断（任务仍在服务端运行）\n")

    # 1. 提交任务
    task_id = client.submit_video_task(prompt, model=model, size=size, quality=quality)
    print(f"  任务ID: {task_id}")

    # 2. 轮询结果
    result = client.poll_video_result(task_id)

    # 3. 下载
    saved = client.download_video(result["video_url"], output_path)
    print(f"  已保存: {saved}")

    # 4. 自动验证
    if auto_verify:
        _run_verify(saved, prompt)

    return saved


def generate_from_image(image_path, prompt, output_path, ar="16:9", quality="speed",
                         model=None, auto_verify=False):
    """
    图生视频（以图片为首帧生成视频）

    Args:
        image_path: 首帧图片路径
        prompt: 提示词（描述视频内容）
        output_path: 输出文件路径 (.mp4)
        ar: 宽高比
        quality: 生成质量
        model: 模型名称
        auto_verify: 生成后自动验证质量

    Returns:
        str: 保存的文件路径
    """
    client = ZhipuClient()
    size = VIDEO_SIZES.get(ar, "1920x1080")

    img = Path(image_path)
    if not img.exists():
        raise FileNotFoundError(f"图片不存在: {image_path}")

    print(f"\n图生视频: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    print(f"  首帧: {image_path}")
    print(f"  模型: {model or 'cogvideox-3'}, 尺寸: {size}, 质量: {quality}")
    print(f"  按 Ctrl+C 可中断（任务仍在服务端运行）\n")

    # 1. 提交任务（带首帧图片）
    task_id = client.submit_video_task(
        prompt, model=model, size=size, quality=quality,
        first_frame_image=str(img),
    )
    print(f"  任务ID: {task_id}")

    # 2. 轮询结果
    result = client.poll_video_result(task_id)

    # 3. 下载
    saved = client.download_video(result["video_url"], output_path)
    print(f"  已保存: {saved}")

    # 4. 自动验证
    if auto_verify:
        _run_verify(saved, prompt)

    return saved
