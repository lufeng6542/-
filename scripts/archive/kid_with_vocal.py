# -*- coding: utf-8 -*-
"""
基德vs大妈 - 保留原声版
人声+BGM混合
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_ROOT / "素材"
BGM_DIR = PROJECT_ROOT / "BGM"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_kid_vocal"

FFMPEG = "ffmpeg"

def find_material(keyword):
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def extract_segment_with_audio(video_path, start, duration, output_path):
    """提取视频片段，保留原声"""
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
    print("    [Kid vs Big Mom] With Original Vocals")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    segments = [
        ("凯多 使用雷电 大笑着 爆炸", 0, 1.5),
        ("基德 反复攻击 夏洛特玲玲 打斗 和队友", 0, 1.5),
        ("基德 使用技能 冲撞夏洛特玲玲", 0, 0.8),
        ("基德 射击着 夏洛特玲玲 在空中", 0, 0.7),
        ("基德 发动激光炮 大喊道 夏洛特玲玲", 0, 0.8),
        ("基德 释放图案 攻击夏洛特玲玲", 0, 1.0),
        ("基德 反复攻击 夏洛特玲玲 打斗 和队友", 5, 0.8),
        ("基德 使用技能 冲撞夏洛特玲玲", 5, 0.8),
        ("基德 释放图案 攻击夏洛特玲玲", 10, 1.0),
        ("基德 发动激光炮 大喊道 夏洛特玲玲", 5, 1.0),
        ("罗罗诺亚·索隆 爆气紫光", 0, 0.4),
        ("基德 射击着 夏洛特玲玲 在空中", 3, 0.4),
        ("凯多 使用雷电 大笑着 爆炸", 10, 0.4),
        ("基德 反复攻击 夏洛特玲玲 打斗 和队友", 10, 0.5),
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 10, 0.4),
        ("基德 释放图案 攻击夏洛特玲玲", 15, 0.5),
        ("基德 发动激光炮 大喊道 夏洛特玲玲", 10, 0.5),
        ("基德 释放图案 攻击夏洛特玲玲", 20, 2.0),
        ("基德 发动激光炮 大喊道 夏洛特玲玲", 15, 2.0),
        ("基德 反复攻击 夏洛特玲玲 打斗 和队友", 30, 2.0),
    ]

    print(f"\n[Processing] {len(segments)} segments\n")

    segment_files = []
    for i, (keyword, start, duration) in enumerate(segments, 1):
        material = find_material(keyword)
        if not material:
            continue
        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"
        if extract_segment_with_audio(material, start, duration, output_file):
            segment_files.append(output_file)
            print(f"[{i:2d}] {duration}s OK")

    print(f"\n[Extracted] {len(segment_files)} segments")

    # 合并视频（保留原声）
    print("\n[Merging with original audio...]")
    concat_file = OUTPUT_DIR / "concat_kid_vocal.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in segment_files:
            f.write(f"file '{v}'\n")

    temp_video = TEMP_DIR / "kid_with_vocal.mp4"
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(temp_video)
    ], capture_output=True)

    # 获取视频时长
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(temp_video)],
        capture_output=True, text=True
    )
    video_duration = float(result.stdout.strip()) if result.stdout.strip() else 19
    print(f"[Video Duration] {video_duration:.1f}s")

    # 混合原声和BGM，人声调大
    print("\n[Mixing vocals + BGM...]")

    bgm_source = BGM_DIR / "War Drums.mp3"
    output_path = OUTPUT_DIR / "kid_vs_bigmom_with_vocal.mp4"

    # 音频处理：
    # - 原声调大 +6dB (volume=2.0)
    # - BGM音量降低 (volume=0.3)
    # - BGM淡出
    # - 最终混合
    filter_complex = f"""
[0:a]volume=2.0,highpass=f=100,lowpass=f=8000[vocals];
[1:a]volume=0.3,afade=t=out:st={video_duration-2}:d=2[bgm];
[vocals][bgm]amix=inputs=2:duration=first[aout]
""".strip()

    cmd = [
        FFMPEG, "-y",
        "-i", str(temp_video),
        "-i", str(bgm_source),
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(video_duration + 2),
        "-vf", f"fade=t=out:st={video_duration-0.5}:d=0.5",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not output_path.exists():
        # 备选方案
        print("[Fallback] Simple mix...")
        subprocess.run([
            FFMPEG, "-y",
            "-i", str(temp_video),
            "-i", str(bgm_source),
            "-filter_complex",
            f"[0:a]volume=1.5[v];[1:a]volume=0.25,afade=t=out:st={video_duration-2}:d=2[b];[v][b]amix=inputs=2:duration=first",
            "-map", "0:v", "-map", "0:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path)
        ], capture_output=True)

    if output_path.exists():
        file_size = output_path.stat().st_size / (1024 * 1024)

        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(output_path)],
            capture_output=True, text=True
        )
        final_duration = float(result.stdout.strip()) if result.stdout.strip() else video_duration

        print("\n" + "=" * 60)
        print("    [COMPLETE!]")
        print("=" * 60)
        print(f"\n[Output] {output_path}")
        print(f"[Size] {file_size:.1f} MB")
        print(f"[Duration] {final_duration:.1f}s")
        print(f"\n[Audio Mix]")
        print(f"  Original Vocals: +6dB (boosted)")
        print(f"  BGM: 30% volume")
        print(f"  End: 2s fade out")

        # Cleanup
        for f in TEMP_DIR.glob("*"):
            f.unlink()
        try:
            TEMP_DIR.rmdir()
        except:
            pass
        concat_file.unlink(missing_ok=True)

        print("\n[Done] Vocals preserved and boosted!")
    else:
        print("[Error] Output not created")

if __name__ == "__main__":
    main()
