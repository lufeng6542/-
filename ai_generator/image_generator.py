#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI图片生成器 - 智谱CogView-4
"""

import time
from pathlib import Path

from .zhipu_client import ZhipuClient
from .output_manager import resolve_output_path, save_record

# 智谱支持的图片尺寸（1024-2048px，32的倍数）
STANDARD_SIZES = [
    [1024, 1024],
    [768, 1344],
    [864, 1152],
    [1344, 768],
    [1152, 864],
    [1440, 720],
    [720, 1440],
    [1024, 576],
    [576, 1024],
    [1280, 720],
    [720, 1280],
]

# 比例 → 默认尺寸映射
AR_TO_SIZE = {
    "1:1": "1024x1024",
    "16:9": "1280x720",
    "9:16": "720x1280",
    "4:3": "1152x864",
    "3:4": "864x1152",
}


def parse_ar(ar_str):
    """解析比例字符串，返回 (width_ratio, height_ratio)"""
    parts = ar_str.split(":")
    if len(parts) != 2:
        return None
    try:
        w, h = float(parts[0]), float(parts[1])
        return (w, h) if w > 0 and h > 0 else None
    except ValueError:
        return None


def ar_to_size(ar_str):
    """将比例字符串转换为最接近的标准尺寸"""
    if ar_str in AR_TO_SIZE:
        return AR_TO_SIZE[ar_str]

    parsed = parse_ar(ar_str)
    if not parsed:
        return "1024x1024"

    target_ratio = parsed[0] / parsed[1]
    best = "1024x1024"
    best_diff = float("inf")

    for w, h in STANDARD_SIZES:
        diff = abs(w / h - target_ratio)
        if diff < best_diff:
            best_diff = diff
            best = f"{w}x{h}"

    return best


def generate(prompt, output_path, ar="1:1", size=None, model=None):
    """
    AI生成图片

    Args:
        prompt: 提示词
        output_path: 输出文件路径
        ar: 宽高比 (1:1, 16:9, 9:16, 4:3, 3:4)
        size: 指定尺寸 (如 "1280x720")，优先于ar
        model: 模型名称 (默认 cogview-4)

    Returns:
        str: 保存的文件路径
    """
    # 输入校验
    if not prompt or not prompt.strip():
        raise ValueError("提示词不能为空，请描述你想要生成的图片内容")

    client = ZhipuClient()
    size = size or ar_to_size(ar)
    model = model or "cogview-4"

    # 如果用户没有指定输出路径，自动归档到 ai_output/
    output_path = Path(output_path)
    if not output_path.is_absolute() and str(output_path).startswith("素材/"):
        output_path = resolve_output_path(output_path.name, subdir="images")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"生成图片: {prompt[:50]}{'...' if len(prompt) > 50 else ''}")
    print(f"  模型: {model}, 尺寸: {size}")

    t0 = time.time()
    result = client.generate_image(prompt, model=model, size=size)
    saved = client.download_image(result[0], output_path)
    elapsed = time.time() - t0

    print(f"  已保存: {saved} ({elapsed:.1f}s)")

    # 保存生成记录
    save_record("image", prompt, saved, model=model, size=size, ar=ar, elapsed_seconds=round(elapsed, 1))
    return saved
