#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI视频生成器 - 智谱CogVideoX-3
支持文生视频、图生视频、首尾帧生成
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
    "4K": "3840x2160",
}


def _run_verify(video_path, prompt):
    """生成后自动验证"""
    from .quality_checker import check
    print("\n[自动验证] 生成完成，开始质量评估...\n")
    return check(video_path, prompt)


def _resolve_output(output_path, subdir="videos"):
    """统一处理输出路径和归档"""
    output_path = Path(output_path)
    if not output_path.is_absolute() and str(output_path).startswith("素材/"):
        output_path = resolve_output_path(output_path.name, subdir=subdir)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def generate_from_text(prompt, output_path, ar="16:9", quality="speed", model=None,
                        auto_verify=False, with_audio=False, fps=None):
    """
    文生视频

    Args:
        prompt: 提示词
        output_path: 输出文件路径 (.mp4)
        ar: 宽高比 (1:1, 16:9, 9:16, 4:3, 3:4, 4K)
        quality: 生成质量 (speed / quality)
        model: 模型名称 (默认 cogvideox-3)
        auto_verify: 生成后自动验证质量
        with_audio: 是否生成带音频的视频
        fps: 帧率 (30 或 60)

    Returns:
        str: 保存的文件路径
    """
    if not prompt or not prompt.strip():
        raise ValueError("提示词不能为空，请描述你想要生成的视频内容")
    if quality not in ("speed", "quality"):
        raise ValueError(f"质量参数错误: '{quality}'，只能是 speed 或 quality")

    client = ZhipuClient()
    model = model or "cogvideox-3"
    size = VIDEO_SIZES.get(ar, ar if "x" in ar else "1920x1080")

    output_path = _resolve_output(output_path)

    audio_str = "，带音频" if with_audio else ""
    fps_str = f"，{fps}fps" if fps else ""
    print(f"\n生成视频: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    print(f"  模型: {model}, 尺寸: {size}, 质量: {quality}{audio_str}{fps_str}")
    print(f"  按 Ctrl+C 可中断（任务仍在服务端运行）\n")

    t0 = time.time()

    task_id = client.submit_video_task(prompt, model=model, size=size, quality=quality,
                                       with_audio=with_audio, fps=fps)
    print(f"  任务ID: {task_id}")

    result = client.poll_video_result(task_id)
    saved = client.download_video(result["video_url"], output_path)
    elapsed = time.time() - t0
    print(f"  已保存: {saved} ({elapsed:.1f}s)")

    save_record("video", prompt, saved, model=model, size=size, ar=ar, quality=quality,
                with_audio=with_audio, fps=fps,
                task_id=task_id, elapsed_seconds=round(elapsed, 1))

    if auto_verify:
        _run_verify(saved, prompt)

    return saved


def generate_from_image(image_path, prompt, output_path, ar="16:9", quality="speed",
                         model=None, auto_verify=False, with_audio=False, fps=None):
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
        with_audio: 是否生成带音频的视频
        fps: 帧率 (30 或 60)

    Returns:
        str: 保存的文件路径
    """
    if not prompt or not prompt.strip():
        raise ValueError("提示词不能为空，请描述你想要生成的视频内容")

    client = ZhipuClient()
    model = model or "cogvideox-3"
    size = VIDEO_SIZES.get(ar, ar if "x" in ar else "1920x1080")

    img = Path(image_path)
    if not img.exists():
        raise FileNotFoundError(f"图片文件不存在: {image_path}")
    if img.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        raise ValueError(f"不支持的图片格式: {img.suffix}，请使用 png/jpg/jpeg/webp")

    output_path = _resolve_output(output_path)

    audio_str = "，带音频" if with_audio else ""
    fps_str = f"，{fps}fps" if fps else ""
    print(f"\n图生视频: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    print(f"  首帧: {image_path}")
    print(f"  模型: {model}, 尺寸: {size}, 质量: {quality}{audio_str}{fps_str}")
    print(f"  按 Ctrl+C 可中断（任务仍在服务端运行）\n")

    t0 = time.time()

    task_id = client.submit_video_task(
        prompt, model=model, size=size, quality=quality,
        first_frame_image=str(img), with_audio=with_audio, fps=fps,
    )
    print(f"  任务ID: {task_id}")

    result = client.poll_video_result(task_id)
    saved = client.download_video(result["video_url"], output_path)
    elapsed = time.time() - t0
    print(f"  已保存: {saved} ({elapsed:.1f}s)")

    save_record("img2video", prompt, saved, model=model, size=size, ar=ar, quality=quality,
                source_image=str(image_path), with_audio=with_audio, fps=fps,
                task_id=task_id, elapsed_seconds=round(elapsed, 1))

    if auto_verify:
        _run_verify(saved, prompt)

    return saved


def generate_from_frames(first_frame, last_frame, prompt, output_path, ar="16:9",
                          quality="speed", model=None, auto_verify=False,
                          with_audio=False, fps=None):
    """
    首尾帧生成视频（指定首帧和尾帧，AI生成过渡动画）

    Args:
        first_frame: 首帧图片路径
        last_frame: 尾帧图片路径
        prompt: 提示词（描述过渡动画内容）
        output_path: 输出文件路径 (.mp4)
        ar: 宽高比
        quality: 生成质量
        model: 模型名称
        auto_verify: 生成后自动验证质量
        with_audio: 是否生成带音频的视频
        fps: 帧率 (30 或 60)

    Returns:
        str: 保存的文件路径
    """
    if not prompt or not prompt.strip():
        raise ValueError("提示词不能为空，请描述你想要的过渡动画内容")

    client = ZhipuClient()
    model = model or "cogvideox-3"
    size = VIDEO_SIZES.get(ar, ar if "x" in ar else "1920x1080")

    first = Path(first_frame)
    last = Path(last_frame)
    for img, name in [(first, "首帧"), (last, "尾帧")]:
        if not img.exists():
            raise FileNotFoundError(f"{name}图片不存在: {img}")
        if img.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
            raise ValueError(f"不支持的图片格式: {img.suffix}，请使用 png/jpg/jpeg/webp")

    output_path = _resolve_output(output_path)

    audio_str = "，带音频" if with_audio else ""
    fps_str = f"，{fps}fps" if fps else ""
    print(f"\n首尾帧生成: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    print(f"  首帧: {first_frame}")
    print(f"  尾帧: {last_frame}")
    print(f"  模型: {model}, 尺寸: {size}, 质量: {quality}{audio_str}{fps_str}")
    print(f"  按 Ctrl+C 可中断（任务仍在服务端运行）\n")

    t0 = time.time()

    task_id = client.submit_video_task(
        prompt, model=model, size=size, quality=quality,
        first_frame_image=str(first), last_frame_image=str(last),
        with_audio=with_audio, fps=fps,
    )
    print(f"  任务ID: {task_id}")

    result = client.poll_video_result(task_id)
    saved = client.download_video(result["video_url"], output_path)
    elapsed = time.time() - t0
    print(f"  已保存: {saved} ({elapsed:.1f}s)")

    save_record("frames2video", prompt, saved, model=model, size=size, ar=ar, quality=quality,
                first_frame=str(first_frame), last_frame=str(last_frame),
                with_audio=with_audio, fps=fps,
                task_id=task_id, elapsed_seconds=round(elapsed, 1))

    if auto_verify:
        _run_verify(saved, prompt)

    return saved
