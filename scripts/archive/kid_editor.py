# -*- coding: utf-8 -*-
"""
超新星崛起 - 基德vs大妈
音乐驱动剪辑执行器
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_ROOT / "素材"
BGM_DIR = PROJECT_ROOT / "BGM"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_kid"

FFMPEG = "ffmpeg"

def find_material(keyword):
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def extract_segment(video_path, start, duration, output_path):
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
    print("    [Kid vs Big Mom] Music-Driven Edit")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 音乐驱动剪辑方案
    segments = [
        # 0-3s: 开场压迫
        ("凯多 使用雷电 大笑着 爆炸", 0, 1.5, "四皇压迫"),
        ("基德 反复攻击 夏洛特玲玲 打斗 和队友", 0, 1.5, "迎战姿态"),
        # 3-10s: 战鼓连击
        ("基德 使用技能 冲撞夏洛特玲玲", 0, 0.8, "冲撞1"),
        ("基德 射击着 夏洛特玲玲 在空中", 0, 0.7, "射击"),
        ("基德 发动激光炮 大喊道 夏洛特玲玲", 0, 0.8, "激光炮1"),
        ("基德 释放图案 攻击夏洛特玲玲", 0, 1.0, "图案攻击1"),
        ("基德 反复攻击 夏洛特玲玲 打斗 和队友", 5, 0.8, "连击1"),
        ("基德 使用技能 冲撞夏洛特玲玲", 5, 0.8, "冲撞2"),
        ("基德 释放图案 攻击夏洛特玲玲", 10, 1.0, "图案攻击2"),
        ("基德 发动激光炮 大喊道 夏洛特玲玲", 5, 1.0, "激光炮2"),
        # 10-14s: 快切堆积
        ("罗罗诺亚·索隆 爆气紫光", 0, 0.4, "索隆爆气"),
        ("基德 射击着 夏洛特玲玲 在空中", 3, 0.4, "射击2"),
        ("凯多 使用雷电 大笑着 爆炸", 10, 0.4, "雷电"),
        ("基德 反复攻击 夏洛特玲玲 打斗 和队友", 10, 0.5, "连击2"),
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 10, 0.4, "索隆合刀"),
        ("基德 释放图案 攻击夏洛特玲玲", 15, 0.5, "图案攻击3"),
        ("基德 发动激光炮 大喊道 夏洛特玲玲", 10, 0.5, "激光炮3"),
        # 14-18s: DROP爆发
        ("基德 释放图案 攻击夏洛特玲玲", 20, 2.0, "大招1"),
        ("基德 发动激光炮 大喊道 夏洛特玲玲", 15, 2.0, "大招2"),
        # 18-20s: 定格收尾
        ("基德 反复攻击 夏洛特玲玲 打斗 和队友", 30, 2.0, "胜利定格"),
    ]

    print(f"\n[Music-Driven Structure]")
    print(f"  0-3s:  Opening - Four Emperor Pressure")
    print(f"  3-10s: Buildup - Battle Rhythm")
    print(f"  10-14s: Acceleration - Quick Cuts")
    print(f"  14-18s: DROP - Maximum Explosion")
    print(f"  18-20s: Finale - Victory Freeze")
    print(f"\n[Total] {len(segments)} segments\n")

    segment_files = []
    for i, (keyword, start, duration, note) in enumerate(segments, 1):
        material = find_material(keyword)
        if not material:
            print(f"[{i:2d}] Skip: {note}")
            continue

        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"
        if extract_segment(material, start, duration, output_file):
            segment_files.append(output_file)
            print(f"[{i:2d}] {duration}s - {note}")

    print(f"\n[Extracted] {len(segment_files)} segments")

    # 合并视频
    print("\n[Merging Video...]")
    concat_file = OUTPUT_DIR / "concat_kid.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in segment_files:
            f.write(f"file '{v}'\n")

    temp_video = TEMP_DIR / "kid_merged.mp4"
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
    video_duration = float(result.stdout.strip()) if result.stdout.strip() else 15
    print(f"[Video Duration] {video_duration:.1f}s")

    # 截取BGM前20秒
    print("\n[Preparing BGM...]")
    bgm_source = BGM_DIR / "War Drums.mp3"
    bgm_cut = TEMP_DIR / "bgm_20s.mp3"
    subprocess.run([
        FFMPEG, "-y", "-i", str(bgm_source),
        "-t", "20", "-c:a", "libmp3lame", "-q:a", "2",
        str(bgm_cut)
    ], capture_output=True)

    # 添加BGM和结尾效果
    print("\n[Final Composition...]")

    output_path = OUTPUT_DIR / "kid_vs_bigmom_final.mp4"

    # 添加定格结尾效果
    freeze_start = max(0, video_duration - 0.1)
    fade_start = video_duration + 2 - 0.5

    filter_complex = f"""
[0:v]split=2[v1][v2];
[v1]trim=0:{video_duration},setpts=PTS-STARTPTS[main];
[v2]trim={freeze_start}:{video_duration},setpts=PTS-STARTPTS,loop=60:1:0[freeze];
[main][freeze]concat=n=2:v=1:a=0,format=yuv420p,fade=t=out:st={fade_start}:d=0.5[vout];
[1:a]atrim=0:{video_duration+2},afade=t=out:st={video_duration-1}:d=2[aout]
""".strip()

    cmd = [
        FFMPEG, "-y",
        "-i", str(temp_video),
        "-i", str(bgm_cut),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not output_path.exists():
        # 备选方案
        print("[Fallback] Simple merge...")
        subprocess.run([
            FFMPEG, "-y",
            "-i", str(temp_video),
            "-i", str(bgm_cut),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-af", f"afade=t=out:st={video_duration-2}:d=2",
            "-vf", f"fade=t=out:st={video_duration-0.5}:d=0.5",
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
        print(f"[BGM] War Drums")
        print(f"\n[Narrative Arc]")
        print(f"  0-3s:  Four Emperor Pressure")
        print(f"  3-10s: Kid Counterattack")
        print(f"  10-14s: Quick Cut Buildup")
        print(f"  14-18s: DROP Explosion")
        print(f"  18-{final_duration:.0f}s: Victory Freeze")

        # Cleanup
        for f in TEMP_DIR.glob("*"):
            f.unlink()
        try:
            TEMP_DIR.rmdir()
        except:
            pass
        concat_file.unlink(missing_ok=True)

        print("\n[Done] Music-driven edit complete!")
    else:
        print("[Error] Output not created")

if __name__ == "__main__":
    main()
