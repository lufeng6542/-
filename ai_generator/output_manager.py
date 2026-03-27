#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI生成产出管理器
统一管理所有AI生成的图片和视频，按日期归档，记录生成参数
"""

import json
import time
from datetime import datetime
from pathlib import Path

DEFAULT_OUTPUT_DIR = "ai_output"


def get_output_dir(base_dir=None):
    """获取当前日期的输出目录"""
    base = Path(base_dir) if base_dir else Path(DEFAULT_OUTPUT_DIR)
    today = datetime.now().strftime("%Y-%m-%d")
    return base / today


def resolve_output_path(filename, base_dir=None, subdir=None):
    """
    根据文件名生成完整输出路径，自动归档到日期子目录

    Args:
        filename: 文件名 (如 "cat.png" 或 "wave.mp4")
        base_dir: 基础目录 (默认 ai_output/)
        subdir: 额外子目录 (如 "images" 或 "videos")

    Returns:
        Path: 完整输出路径
    """
    output_dir = get_output_dir(base_dir)
    if subdir:
        output_dir = output_dir / subdir
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir / filename


def save_record(record_type, prompt, output_path, **kwargs):
    """
    保存一条生成记录到JSON日志

    Args:
        record_type: "image" / "video" / "img2video" / "verify"
        prompt: 提示词
        output_path: 输出文件路径
        **kwargs: 额外参数 (model, size, ar, quality, score, elapsed_seconds 等)

    Returns:
        Path: 记录文件路径
    """
    output_dir = get_output_dir()
    log_file = output_dir / "生成记录.jsonl"

    record = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": record_type,
        "prompt": prompt,
        "output": str(output_path),
        **kwargs,
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    return log_file


def list_records(base_dir=None, record_type=None, limit=20):
    """
    查询最近的生成记录

    Args:
        base_dir: 基础目录
        record_type: 筛选类型 (None=全部)
        limit: 返回条数

    Returns:
        list[dict]: 生成记录列表
    """
    base = Path(base_dir) if base_dir else Path(DEFAULT_OUTPUT_DIR)
    records = []

    for log_file in sorted(base.glob("*/生成记录.jsonl"), reverse=True):
        with open(log_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    if record_type and rec.get("type") != record_type:
                        continue
                    records.append(rec)
                except json.JSONDecodeError:
                    continue

    return records[:limit]
