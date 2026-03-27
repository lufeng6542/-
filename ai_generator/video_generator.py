#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI视频生成器 - 智谱CogVideoX-3
支持文生视频和图生视频
"""

import time
from pathlib import Path

from .zhipu_client import ZhipuClient
from .output_manager import resolve_output_path, save_record

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
    if not prompt or not prompt.strip():
        raise ValueError("提示词不能为空，请描述你想要生成的视频内容")
    if quality not in ("speed", "quality"):
        raise ValueError(f"质量参数错误: '{quality}'，只能是 speed 或 quality")

    client = ZhipuClient()
    model = model or "cogvideox-3"
    size = VIDEO_SIZES.get(ar, "1920x1080")

    # 自动归档到 ai_output/
    output_path = Path(output_path)
    if not output_path.is_absolute() and str(output_path).startswith("素材/"):
        output_path = resolve_output_path(output_path.name, subdir="videos")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n生成视频: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    print(f"  模型: {model}, 尺寸: {size}, 质量: {quality}")
    print(f"  按 Ctrl+C 可中断（任务仍在服务端运行）\n")

    t0 = time.time()

    # 1. 提交任务
    task_id = client.submit_video_task(prompt, model=model, size=size, quality=quality)
    print(f"  任务ID: {task_id}")

    # 2. 轮询结果
    result = client.poll_video_result(task_id)

    # 3. 下载
    saved = client.download_video(result["video_url"], output_path)
    elapsed = time.time() - t0
    print(f"  已保存: {saved} ({elapsed:.1f}s)")

    # 4. 保存生成记录
    save_record("video", prompt, saved, model=model, size=size, ar=ar, quality=quality,
                task_id=task_id, elapsed_seconds=round(elapsed, 1))

    # 5. 自动验证
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
    if not prompt or not prompt.strip():
        raise ValueError("提示词不能为空，请描述你想要生成的视频内容")

    client = ZhipuClient()
    model = model or "cogvideox-3"
    size = VIDEO_SIZES.get(ar, "1920x1080")

    img = Path(image_path)
    if not img.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    if img.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        raise ValueError(f"不支持的图片格式: {img.suffix}，请使用 png/jpg/jpeg/webp")

    # 自动归档到 ai_output/
    output_path = Path(output_path)
    if not output_path.is_absolute() and str(output_path).startswith("素材/"):
        output_path = resolve_output_path(output_path.name, subdir="videos")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n图生视频: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    print(f"  首帧: {image_path}")
    print(f"  模型: {model}, 尺寸: {size}, 质量: {quality}")
    print(f"  按 Ctrl+C 可中断（任务仍在服务端运行）\n")

    t0 = time.time()

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
    elapsed = time.time() - t0
    print(f"  已保存: {saved} ({elapsed:.1f}s)")

    # 4. 保存生成记录
    save_record("img2video", prompt, saved, model=model, size=size, ar=ar, quality=quality,
                source_image=str(image_path), task_id=task_id, elapsed_seconds=round(elapsed, 1))

    # 5. 自动验证
    if auto_verify:
        _run_verify(saved, prompt)

    return saved
