# -*- coding: utf-8 -*-
"""
战鼓版剪辑执行器
20秒高燃快节奏版本
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
TEMP_DIR = OUTPUT_DIR / "temp_wardrums"

FFMPEG = "ffmpeg"

def load_plan(plan_path: Path) -> dict:
    with open(plan_path, "r", encoding="utf-8") as f:
        return json.load(f)

def find_material(keyword: str) -> Optional[Path]:
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def extract_segment(video_path: Path, start: float, duration: float,
                    output_path: Path, effect: str = None) -> bool:
    vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"

    if effect and "flash" in effect.lower():
        vf += ",format=rgba,fade=t=in:st=0:d=0.1:c=white,format=yuv420p"

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

    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0

def concat_with_bgm(video_list: List[Path], bgm_path: Path,
                    output_path: Path) -> bool:
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in video_list:
            f.write(f"file '{v}'\n")

    cmd = [
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-i", str(bgm_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-af", "afade=t=out:st=18:d=2",
        "-shortest",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True)
    concat_file.unlink(missing_ok=True)
    return result.returncode == 0

def main():
    print("=" * 60)
    print("    [War Drums] - 20s")
    print("=" * 60)

    plan_path = OUTPUT_DIR / "clipping_plan_wardrums.json"
    if not plan_path.exists():
        plan_path = OUTPUT_DIR / "s方案_WarDrums版.json"

    for p in OUTPUT_DIR.glob("*.json"):
        if "WarDrums" in p.name or "wardrums" in p.name.lower():
            plan_path = p
            break

    plan = load_plan(plan_path)

    print(f"\n[Theme] {plan['theme']}")
    print(f"[BGM] {plan['bgm']} ({plan['total_duration']}s)")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    all_segments = []
    segment_files = []

    for section_name, section in plan["structure"].items():
        print(f"\n[Section] {section['time']} - {section['description']}")
        all_segments.extend(section["segments"])

    print(f"\n[Total] {len(all_segments)} segments\n")

    for i, seg in enumerate(all_segments, 1):
        keyword = seg["keyword"]
        start = seg["start"]
        duration = seg["duration"]
        effect = seg.get("effect", "")

        print(f"[{i}/{len(all_segments)}] {keyword[:25]}... ({duration}s)")

        material = find_material(keyword)
        if not material:
            print(f"  [Skip] Not found")
            continue

        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"

        if extract_segment(material, start, duration, output_file, effect):
            segment_files.append(output_file)
            print(f"  [OK] {effect if effect else 'No FX'}")
        else:
            print(f"  [Fail]")

    print(f"\n[Done] {len(segment_files)} segments extracted")

    if not segment_files:
        print("[Error] No segments")
        return

    print("\n[Merging] Adding BGM...")

    bgm_path = BGM_DIR / plan["bgm"]
    output_path = OUTPUT_DIR / f"{plan['name']}.mp4"

    if concat_with_bgm(segment_files, bgm_path, output_path):
        file_size = output_path.stat().st_size / (1024 * 1024)

        print("\n" + "=" * 60)
        print("    [Complete!]")
        print("=" * 60)
        print(f"\n[Output] {output_path}")
        print(f"[Size] {file_size:.1f} MB")
        print(f"[Duration] ~{plan['total_duration']}s")
        print(f"[Segments] {len(segment_files)}")
        print(f"[BGM] {plan['bgm']}")

        print("\n[Cleanup] Temp files...")
        for f in TEMP_DIR.glob("*.mp4"):
            f.unlink()
        try:
            TEMP_DIR.rmdir()
        except:
            pass

        print("\n[Done] All complete!")
    else:
        print("[Error] Merge failed")

if __name__ == "__main__":
    main()
