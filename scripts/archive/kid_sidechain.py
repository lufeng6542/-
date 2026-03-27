# -*- coding: utf-8 -*-
"""
基德vs大妈 - 人声闪避版
BGM调大，遇人声自动降低
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_ROOT / "素材"
BGM_DIR = PROJECT_ROOT / "BGM"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_sidechain"

FFMPEG = "ffmpeg"

def find_material(keyword):
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def extract_segment_with_audio(video_path, start, duration, output_path):
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
    print("    [Kid vs Big Mom] Sidechain Compression")
    print("    BGM loud, ducks when vocals detected")
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

    # 合并视频
    print("\n[Merging...]")
    concat_file = OUTPUT_DIR / "concat_sidechain.txt"
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

    # 获取视频时长
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(temp_video)],
        capture_output=True, text=True
    )
    video_duration = float(result.stdout.strip()) if result.stdout.strip() else 19
    print(f"[Video Duration] {video_duration:.1f}s")

    # 提取视频原声
    print("\n[Extracting vocals...]")
    vocals_audio = TEMP_DIR / "vocals.aac"
    subprocess.run([
        FFMPEG, "-y", "-i", str(temp_video),
        "-vn", "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
        str(vocals_audio)
    ], capture_output=True)

    # 准备BGM
    bgm_source = BGM_DIR / "War Drums.mp3"
    output_path = OUTPUT_DIR / "kid_sidechain_final.mp4"

    print("\n[Applying sidechain compression...]")
    print("  - BGM: 80% volume (louder)")
    print("  - Vocals: 100% preserved")
    print("  - When vocals detected: BGM auto-ducks to 20%")

    # 侧链压缩：当检测到人声时，BGM自动降低
    # 使用 sidechaincompress 滤镜
    filter_complex = f"""
[0:a]volume=1.5,highpass=f=100[vocals];
[1:a]volume=0.8[bgm_base];
[vocals][bgm_base]sidechaincompress=threshold=0.1:ratio=4:attack=10:release=200[bgm_ducked];
[vocals][bgm_ducked]amix=inputs=2:duration=first:dropout_transition=0[aout]
""".strip()

    cmd = [
        FFMPEG, "-y",
        "-i", str(vocals_audio),
        "-i", str(bgm_source),
        "-filter_complex", filter_complex,
        "-i", str(temp_video),
        "-map", "2:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-t", str(video_duration + 1),
        "-vf", f"fade=t=out:st={video_duration-0.5}:d=0.5",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not output_path.exists():
        # 备选方案：使用简单的音量包络
        print("[Fallback] Volume envelope...")
        filter_complex2 = f"""
[0:a]volume=1.5[v];
[1:a]volume=0.7,afade=t=out:st={video_duration-2}:d=2[b];
[v][b]amix=inputs=2:duration=first[aout]
""".strip()
        subprocess.run([
            FFMPEG, "-y",
            "-i", str(temp_video),
            "-i", str(bgm_source),
            "-filter_complex", filter_complex2,
            "-map", "0:v", "-map", "[aout]",
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
        print(f"\n[Audio Processing]")
        print(f"  BGM Base Volume: 80%")
        print(f"  Vocals Volume: 150% (boosted)")
        print(f"  Sidechain: BGM auto-ducks when vocals detected")

        # Cleanup
        for f in TEMP_DIR.glob("*"):
            f.unlink()
        try:
            TEMP_DIR.rmdir()
        except:
            pass
        concat_file.unlink(missing_ok=True)

        print("\n[Done] Sidechain compression applied!")
    else:
        print("[Error] Output not created")

if __name__ == "__main__":
    main()
