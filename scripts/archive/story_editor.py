# -*- coding: utf-8 -*-
"""
剧情完整版剪辑器
三幕式叙事：压迫-觉醒-爆发-胜利
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_ROOT / "素材"
BGM_DIR = PROJECT_ROOT / "BGM"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_story"

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
    print("    [Story Mode] Three-Act Narrative")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 三幕式剪辑方案
    story_segments = [
        # ===== 第一幕：压迫与觉醒 (0-5s) =====
        ("凯多 使用雷电 大笑着 爆炸", 0, 1.5, "敌人压迫"),
        ("罗罗诺亚·索隆 被紫色气息包裹住 痛苦", 0, 1.5, "承受压力"),
        ("罗罗诺亚·索隆 爆气紫光", 0, 2.0, "觉醒爆气"),

        # ===== 第二幕：激战交锋 (5-15s) =====
        ("罗罗诺亚·索隆 拔起刀 举起双刀 冲过去", 3, 1.0, "发起进攻"),
        ("罗罗诺亚·索隆 和 武士 对砍", 0, 0.5, "交锋1"),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 5, 0.6, "连击1"),
        ("罗罗诺亚·索隆 和 武士 对砍", 2, 0.5, "交锋2"),
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 5, 0.7, "重击"),
        ("罗罗诺亚·索隆 被击飞 闪躲", 0, 0.5, "闪避"),
        ("罗罗诺亚·索隆 和 武士 对砍", 3, 0.5, "交锋3"),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 10, 0.7, "连击2"),
        ("罗罗诺亚·索隆 和 武士 混打着", 5, 0.8, "混战"),
        ("罗罗诺亚·索隆 绿色的刀 劈砍 从中间", 5, 0.8, "绿光斩"),
        ("罗罗诺亚·索隆 爆气紫光 跳出去 砍击", 5, 1.0, "跳斩"),

        # ===== 第三幕：爆发与胜利 (15-25s) =====
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 20, 2.0, "合刀蓄力"),
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 40, 2.5, "奥义释放"),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 25, 1.5, "爆发连击"),
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 15, 1.5, "终结一击"),
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 60, 2.5, "背对爆炸"),
    ]

    print(f"\n[Story Structure]")
    print(f"  Act 1: Oppression & Awakening (0-5s)")
    print(f"  Act 2: Fierce Battle (5-15s)")
    print(f"  Act 3: Explosion & Victory (15-25s)")
    print(f"\n[Total] {len(story_segments)} segments\n")

    segment_files = []
    for i, (keyword, start, duration, note) in enumerate(story_segments, 1):
        material = find_material(keyword)
        if not material:
            print(f"[{i:2d}] Skip: {note}")
            continue

        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"
        if extract_segment(material, start, duration, output_file):
            segment_files.append(output_file)
            act = "A1" if i <= 3 else ("A2" if i <= 13 else "A3")
            print(f"[{i:2d}][{act}] {duration}s - {note}")

    print(f"\n[Extracted] {len(segment_files)} segments")

    # 合并视频
    print("\n[Merging Video...]")
    concat_file = OUTPUT_DIR / "concat_story.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in segment_files:
            f.write(f"file '{v}'\n")

    temp_video = TEMP_DIR / "story_merged.mp4"
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
    video_duration = float(result.stdout.strip())
    print(f"[Video Duration] {video_duration:.1f}s")

    # 从Legendary BGM截取25秒
    print("\n[Preparing BGM...]")
    bgm_source = BGM_DIR / "31_Legendary.mp3"
    bgm_cut = TEMP_DIR / "bgm_25s.mp3"
    subprocess.run([
        FFMPEG, "-y", "-i", str(bgm_source),
        "-t", "25", "-c:a", "libmp3lame", "-q:a", "2",
        str(bgm_cut)
    ], capture_output=True)

    # 添加BGM和结尾效果
    print("\n[Final Composition...]")

    # 计算定格参数
    freeze_start = video_duration - 0.1
    freeze_frames = 60  # 2秒定格
    fade_start = video_duration + 2 - 0.5

    output_path = OUTPUT_DIR / "zoro_story_complete.mp4"

    # 使用filter_complex实现定格+淡出
    filter_complex = f"""
[0:v]split=3[v1][v2][v3];
[v1]trim=0:{video_duration},setpts=PTS-STARTPTS[main];
[v2]trim={freeze_start}:{video_duration},setpts=PTS-STARTPTS,loop={freeze_frames}:1:0[freeze];
[main][freeze]concat=n=2:v=1:a=0,format=yuv420p,fade=t=out:st={video_duration+1.5}:d=0.5[vout];
[1:a]atrim=0:{video_duration+2},afade=t=out:st={video_duration-1}:d=3[aout]
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
        # 备选方案：简单合并
        print("[Fallback] Using simple merge...")
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
        final_duration = float(result.stdout.strip())

        print("\n" + "=" * 60)
        print("    [STORY COMPLETE!]")
        print("=" * 60)
        print(f"\n[Output] {output_path}")
        print(f"[Size] {file_size:.1f} MB")
        print(f"[Duration] {final_duration:.1f}s")
        print(f"\n[Narrative Arc]")
        print(f"  0-5s:  Oppression -> Awakening")
        print(f"  5-15s: Fierce Battle")
        print(f"  15-{final_duration:.0f}s: Explosion -> Victory")

        # Cleanup
        for f in TEMP_DIR.glob("*"):
            f.unlink()
        try:
            TEMP_DIR.rmdir()
        except:
            pass
        concat_file.unlink(missing_ok=True)

        print("\n[Done] Story has beginning, middle, and end!")
    else:
        print("[Error] Output not created")

if __name__ == "__main__":
    main()
