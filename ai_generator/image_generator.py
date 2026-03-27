#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI图片生成器 - 智谱CogView-4
"""

from pathlib import Path

from .zhipu_client import ZhipuClient

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
    client = ZhipuClient()
    size = size or ar_to_size(ar)

    print(f"生成图片: {prompt[:50]}...")
    print(f"  模型: {model or 'cogview-4'}, 尺寸: {size}")

    result = client.generate_image(prompt, model=model, size=size)

    if not result:
        raise RuntimeError("图片生成返回为空")

    saved = client.download_image(result[0], output_path)
    print(f"  已保存: {saved}")
    return saved
