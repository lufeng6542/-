# -*- coding: utf-8 -*-
"""
战鼓完整版剪辑器 - 简化版
带明确结尾效果
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import List, Optional

PROJECT_ROOT = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_ROOT / "素材"
BGM_DIR = PROJECT_ROOT / "BGM"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_v3"

FFMPEG = "ffmpeg"

def find_material(keyword: str) -> Optional[Path]:
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def extract_segment(video_path: Path, start: float, duration: float, output_path: Path) -> bool:
    vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"
    cmd = [
        FFMPEG, "-y", "-ss", str(start), "-i", str(video_path),
        "-t", str(duration), "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-r", "30",
        str(output_path)
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0

def main():
    print("=" * 60)
    print("    [War Drums Final]")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 剪辑方案
    segments = [
        # 开场 (0-3s)
        ("罗罗诺亚·索隆 爆气紫光", 0, 1.5),
        ("罗罗诺亚·索隆 爆气紫光 跳出去 砍击", 0, 1.5),
        # 连击 (3-9s)
        ("罗罗诺亚·索隆 和 武士 对砍", 0, 0.6),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 5, 0.7),
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 5, 0.7),
        ("罗罗诺亚·索隆 和 武士 对砍", 3, 0.5),
        ("罗罗诺亚·索隆 拔起刀 举起双刀 冲过去", 5, 0.8),
        ("罗罗诺亚·索隆 和 武士 混打着", 8, 0.8),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 12, 0.8),
        ("罗罗诺亚·索隆 绿色的刀 劈砍 从中间", 3, 0.8),
        # 加速 (9-14s)
        ("罗罗诺亚·索隆 被击飞 闪躲", 0, 0.5),
        ("罗罗诺亚·索隆 和 武士 对砍", 2, 0.4),
        ("罗罗诺亚·索隆 爆气紫光", 10, 0.5),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 15, 0.5),
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 10, 0.6),
        ("凯多 使用雷电 大笑着 爆炸", 15, 0.6),
        ("罗罗诺亚·索隆 爆气紫光 跳出去 砍击", 8, 0.8),
        ("罗罗诺亚·索隆 被紫色气息包裹住 痛苦", 5, 0.8),
        # 高潮 (14-17s)
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 30, 1.5),
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 45, 1.5),
        # 结尾 (17-20s) - 明确的收束
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 60, 2.5),
        ("罗罗诺亚·索隆 爆气紫光", 15, 1.0),
    ]

    print(f"\n[Processing] {len(segments)} segments\n")

    segment_files = []
    for i, (keyword, start, duration) in enumerate(segments, 1):
        material = find_material(keyword)
        if not material:
            print(f"[{i}] Skip: {keyword[:20]}...")
            continue

        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"
        if extract_segment(material, start, duration, output_file):
            segment_files.append(output_file)
            print(f"[{i}/{len(segments)}] {duration}s OK")

    print(f"\n[Done] {len(segment_files)} segments")

    # 合并
    print("\n[Merging]...")
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in segment_files:
            f.write(f"file '{v}'\n")

    temp_video = TEMP_DIR / "merged.mp4"
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(temp_video)
    ], capture_output=True)

    # 添加BGM和结尾效果
    print("\n[Adding BGM + Ending]...")
    output_path = OUTPUT_DIR / "s隆封神_战鼓完整版.mp4"
    bgm_path = BGM_DIR / "war_drums_20s.mp3"

    # 使用简单方式：添加BGM + 音频淡出 + 视频淡出
    subprocess.run([
        FFMPEG, "-y",
        "-i", str(temp_video),
        "-i", str(bgm_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-af", "afade=t=out:st=18:d=2",
        "-vf", "fade=t=out:st=19:d=0.5:black",
        "-shortest",
        str(output_path)
    ], capture_output=True)

    if output_path.exists():
        file_size = output_path.stat().st_size / (1024 * 1024)
        print("\n" + "=" * 60)
        print("    [COMPLETE!]")
        print("=" * 60)
        print(f"\n[Output] {output_path}")
        print(f"[Size] {file_size:.1f} MB")
        print(f"[Ending] Audio fade + Video fade")

        # Cleanup
        for f in TEMP_DIR.glob("*"):
            f.unlink()
        try:
            TEMP_DIR.rmdir()
        except:
            pass
        concat_file.unlink(missing_ok=True)

        print("\n[Success] Video has proper ending!")
    else:
        print("[Error] Output not created")

if __name__ == "__main__":
    main()
