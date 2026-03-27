# -*- coding: utf-8 -*-
"""
音乐驱动剪辑执行器
根据JSON方案自动剪辑，镜头服务节奏
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Dict, Optional

PROJECT_ROOT = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_ROOT / "素材"
BGM_DIR = PROJECT_ROOT / "BGM"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_segments"

FFMPEG = "ffmpeg"

def load_plan(plan_path: Path) -> dict:
    """加载剪辑方案"""
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_material(keyword: str) -> Optional[Path]:
    """根据关键词查找素材"""
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def extract_segment(video_path: Path, start: float, duration: float,
                    output_path: Path, effect: str = None) -> bool:
    """提取视频片段，支持特效"""

    # 基础视频滤镜：竖屏缩放
    vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"

    # 添加特效
    if effect and "闪白" in effect:
        vf += ",format=rgba,fade=t=in:st=0:d=0.15:c=white,format=yuv420p"
    elif effect and "震动" in effect:
        vf += ",crop=1060:1900:10:10"

    cmd = [
        FFMPEG, "-y",
        "-ss", str(start),
        "-i", str(video_path),
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0

def concat_with_bgm(video_list: List[Path], bgm_path: Path,
                    output_path: Path, total_duration: float) -> bool:
    """合并视频并添加BGM"""

    # 创建合并列表
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in video_list:
            f.write(f"file '{v}'\n")

    # 合并视频并添加BGM
    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-i", str(bgm_path),
        "-t", str(total_duration),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    concat_file.unlink(missing_ok=True)
    return result.returncode == 0

def main():
    print("=" * 60)
    print("    [音乐驱动剪辑] - 执行中")
    print("=" * 60)

    # 加载方案
    plan_path = OUTPUT_DIR / "剪辑方案_音乐驱动.json"
    plan = load_plan(plan_path)

    print(f"\n[主题] {plan['theme']}")
    print(f"[BGM] {plan['bgm']} ({plan['total_duration']}s)")
    print(f"[BPM] {plan['bpm']}")

    # 创建目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 收集所有片段
    all_segments = []
    segment_files = []

    for section_name, section in plan["structure"].items():
        print(f"\n[段落] {section['time']} - {section['description']}")
        all_segments.extend(section["segments"])

    print(f"\n[统计] 共 {len(all_segments)} 个片段需要处理\n")

    # 提取每个片段
    for i, seg in enumerate(all_segments, 1):
        keyword = seg["keyword"]
        start = seg["start"]
        duration = seg["duration"]
        effect = seg.get("effect", "")

        print(f"[{i}/{len(all_segments)}] {keyword[:25]}... ({duration}s)")

        # 查找素材
        material = find_material(keyword)
        if not material:
            print(f"  [跳过] 素材未找到")
            continue

        # 输出路径
        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"

        # 提取片段
        if extract_segment(material, start, duration, output_file, effect):
            segment_files.append(output_file)
            print(f"  [OK] {effect if effect else '无特效'}")
        else:
            print(f"  [失败] 提取失败")

    print(f"\n[完成] 成功提取 {len(segment_files)} 个片段")

    if not segment_files:
        print("[错误] 没有可用片段")
        return

    # 合并视频并添加BGM
    print("\n[BGM] 正在合成视频并添加BGM...")

    bgm_path = BGM_DIR / plan["bgm"]
    output_name = f"{plan['name']}.mp4"
    output_path = OUTPUT_DIR / output_name

    if concat_with_bgm(segment_files, bgm_path, output_path, plan["total_duration"]):
        # 获取输出信息
        file_size = output_path.stat().st_size / (1024 * 1024)

        print("\n" + "=" * 60)
        print("    [剪辑完成!]")
        print("=" * 60)
        print(f"\n[输出] {output_path}")
        print(f"[大小] {file_size:.1f} MB")
        print(f"[时长] {plan['total_duration']} 秒")
        print(f"[片段] {len(segment_files)} 个")
        print(f"[BGM] {plan['bgm']}")

        # 清理临时文件
        print("\n[清理] 临时文件...")
        for f in TEMP_DIR.glob("*.mp4"):
            f.unlink()
        TEMP_DIR.rmdir()

        print("\n[完成] 全部完成!")
    else:
        print("[错误] 合成失败")

if __name__ == "__main__":
    main()
