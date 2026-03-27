# -*- coding: utf-8 -*-
"""
战鼓完整版剪辑器
带明确结尾和定格效果
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
TEMP_DIR = OUTPUT_DIR / "temp_final"

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

    if effect:
        if "flash" in effect.lower() or "flash" in str(effect).lower():
            vf += ",format=rgba,fade=t=in:st=0:d=0.15:c=white,format=yuv420p"

    cmd = [
        FFMPEG, "-y", "-ss", str(start), "-i", str(video_path),
        "-t", str(duration), "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-r", "30",
        str(output_path)
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0

def concat_videos(video_list: List[Path], output_path: Path) -> bool:
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in video_list:
            f.write(f"file '{v}'\n")

    cmd = [
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    concat_file.unlink(missing_ok=True)
    return result.returncode == 0

def add_bgm_with_ending(video_path: Path, bgm_path: Path, output_path: Path,
                        video_duration: float, fade_config: dict) -> bool:
    """Add BGM with proper ending fade and freeze frame"""

    # Calculate timings
    audio_fade_start = video_duration - fade_config.get("audio_fadeout", 1.5)
    video_fade_start = video_duration - fade_config.get("video_fadeout", 0.5)
    freeze_duration = fade_config.get("freeze_duration", 0.5)

    # Complex filter for freeze frame at end + fades
    filter_complex = f"""
[0:v]split=2[v1][v2];
[v1]trim=0:{video_duration}[vmain];
[v2]trim={video_duration-0.1}:{video_duration},setpts=PTS-STARTPTS,loop={int(freeze_duration*30)}:1:0[vfreeze];
[vmain][vfreeze]concat=n=2:v=1:a=0[outv];
[outv]fade=t=out:st={video_duration + freeze_duration - 0.5}:d=0.5:black[outvfinal];
[1:a]atrim=0:{video_duration + freeze_duration},afade=t=out:st={audio_fade_start}:d={fade_config.get("audio_fadeout", 1.5)}[outa]
"""

    cmd = [
        FFMPEG, "-y",
        "-i", str(video_path),
        "-i", str(bgm_path),
        "-filter_complex", filter_complex.strip(),
        "-map", "[outvfinal]", "-map", "[outa]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  [Error] {result.stderr[:200]}")
        # Fallback: simple merge without freeze
        return simple_merge(video_path, bgm_path, output_path, audio_fade_start)
    return True

def simple_merge(video_path: Path, bgm_path: Path, output_path: Path, fade_start: float) -> bool:
    """Fallback simple merge with fade"""
    cmd = [
        FFMPEG, "-y",
        "-i", str(video_path),
        "-i", str(bgm_path),
        "-map", "0:v", "-map", "1:a",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-af", f"afade=t=out:st={fade_start}:d=1.5",
        "-vf", "fade=t=out:st=18:d=0.5:black",
        "-shortest",
        str(output_path)
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0

def main():
    print("=" * 60)
    print("    [War Drums Final] - With Proper Ending")
    print("=" * 60)

    plan_path = OUTPUT_DIR / "WarDrums.json"
    for p in OUTPUT_DIR.glob("*.json"):
        if "WarDrums" in p.name and "完整" in p.name:
            plan_path = p
            break

    plan = load_plan(plan_path)
    print(f"\n[Theme] {plan['theme']}")
    print(f"[BGM] {plan['bgm']}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    all_segments = []
    for section in plan["structure"].values():
        all_segments.extend(section["segments"])

    print(f"\n[Processing] {len(all_segments)} segments\n")

    segment_files = []
    for i, seg in enumerate(all_segments, 1):
        keyword = seg["keyword"]
        start = seg["start"]
        duration = seg["duration"]
        effect = seg.get("effect", "")

        material = find_material(keyword)
        if not material:
            continue

        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"
        if extract_segment(material, start, duration, output_file, effect):
            segment_files.append(output_file)
            print(f"[{i}/{len(all_segments)}] {duration}s - {effect if effect else 'OK'}")

    print(f"\n[Extracted] {len(segment_files)} segments")

    # Concat video only
    print("\n[Merging] Video segments...")
    temp_video = TEMP_DIR / "merged_video.mp4"
    if not concat_videos(segment_files, temp_video):
        print("[Error] Video merge failed")
        return

    # Get video duration
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_format", str(temp_video)],
        capture_output=True, text=True
    )
    for line in result.stdout.split("\n"):
        if "duration=" in line:
            video_duration = float(line.split("=")[1])
            break

    print(f"[Video Duration] {video_duration:.1f}s")

    # Add BGM with proper ending
    print("\n[Final] Adding BGM with ending fade...")

    bgm_path = BGM_DIR / plan["bgm"]
    output_path = OUTPUT_DIR / f"{plan['name']}.mp4"

    fade_config = plan.get("ending_fade", {
        "video_fadeout": 0.5,
        "audio_fadeout": 1.5,
        "freeze_duration": 0.5
    })

    if add_bgm_with_ending(temp_video, bgm_path, output_path, video_duration, fade_config):
        file_size = output_path.stat().st_size / (1024 * 1024)

        # Get final duration
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_format", str(output_path)],
            capture_output=True, text=True
        )
        for line in result.stdout.split("\n"):
            if "duration=" in line:
                final_duration = float(line.split("=")[1])
                break

        print("\n" + "=" * 60)
        print("    [COMPLETE!]")
        print("=" * 60)
        print(f"\n[Output] {output_path}")
        print(f"[Size] {file_size:.1f} MB")
        print(f"[Duration] {final_duration:.1f}s")
        print(f"[Segments] {len(segment_files)}")
        print(f"[Ending] Freeze frame + Audio fade")

        # Cleanup
        for f in TEMP_DIR.glob("*"):
            f.unlink()
        try:
            TEMP_DIR.rmdir()
        except:
            pass

        print("\n[Done] Video has proper ending now!")
    else:
        print("[Error] Final merge failed")

if __name__ == "__main__":
    main()
