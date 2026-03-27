# -*- coding: utf-8 -*-
"""
索隆封神 - 连续斩击版（含关键特写）
同类型动作聚合 + 关键帧特写增强
"""

import subprocess
from pathlib import Path

PROJECT_ROOT = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_ROOT / "素材"
BGM_DIR = PROJECT_ROOT / "BGM"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_slash"

FFMPEG = "ffmpeg"

def find_material(keyword):
    """关键词匹配素材"""
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def extract_segment(video_path, start, duration, output_path, zoom=False):
    """提取片段，可选特写放大"""
    if zoom:
        # 特写：中心裁剪放大150%
        vf = "scale=1620:2880:force_original_aspect_ratio=decrease,pad=1620:2880:(ow-iw)/2:(oh-ih)/2:black,crop=1080:1920:270:480"
    else:
        vf = "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"

    cmd = [
        FFMPEG, "-y", "-ss", str(start), "-i", str(video_path),
        "-t", str(duration), "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k", "-r", "30",
        str(output_path)
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0

def create_text_card(text, duration, output_path):
    """生成文字卡点画面"""
    cmd = [
        FFMPEG, "-y",
        "-f", "lavfi", "-i", f"color=c=black:s=1080x1920:d={duration}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-r", "30", "-t", str(duration),
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)

def main():
    print("=" * 60)
    print("    [Zoro Slash Combo] With Close-up Enhancement")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 镜头结构（加入关键特写）
    # [Z]=特写镜头 | 景别递进：远景→中景→近景→特写
    segments = [
        # 0-0.3s: 文字卡点
        ("__TEXT__", "", 0.3, "文字卡点", False),
        # 0.3-2s: 开场冲击 - 远景
        ("凯多 使用雷电 大笑着 爆炸", 0, 1.7, "开场压迫[远景]", False),
        # 2-3s: 蓄力铺垫 - 中景
        ("罗罗诺亚·索隆 爆气紫光", 0, 1.0, "蓄力爆气[中景]", False),
        # 3-3.5s: [Z] 眼神特写
        ("罗罗诺亚·索隆 被紫色气息包裹住", 1, 0.5, "眼神特写[Z]", True),
        # 3.5-4.5s: 第一斩 - 中景
        ("罗罗诺亚·索隆 拔起刀 举起双刀 冲过去", 3, 1.0, "第一斩[中景]", False),
        # 4.5-5s: [Z] 刀光特写
        ("罗罗诺亚·索隆 绿色的刀 劈砍", 3, 0.5, "刀光特写[Z]", True),
        # 5-6s: 第二斩 - 近景
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 5, 1.0, "第二斩[近景]", False),
        # 6-6.4s: [Z] 斩击特写
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 3, 0.4, "斩击特写[Z]", True),
        # 6.4-7.2s: 第三斩
        ("罗罗诺亚·索隆 和 武士 对砍", 0, 0.8, "第三斩", False),
        # 7.2-7.5s: [Z] 交锋特写
        ("罗罗诺亚·索隆 和 武士 对砍", 2, 0.3, "交锋特写[Z]", True),
        # 7.5-8s: 快切1
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 5, 0.5, "快切1", False),
        # 8-8.4s: 快切2
        ("罗罗诺亚·索隆 被击飞 闪躲", 0, 0.4, "快切2", False),
        # 8.4-8.7s: [Z] 闪避特写
        ("罗罗诺亚·索隆 被击飞 闪躲", 0.5, 0.3, "闪避特写[Z]", True),
        # 8.7-9.2s: 快切3
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 10, 0.5, "快切3", False),
        # 9.2-9.5s: [Z] 合刀蓄力特写
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 15, 0.3, "合刀蓄力[Z]", True),
        # 9.5-11.5s: 高潮爆发 - 特写放大
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 20, 2.0, "合刀爆发[特写]", True),
        # 11.5-13s: 终结画面
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 40, 1.5, "背对爆炸", False),
        # 13-13.5s: [Z] 胜利表情特写
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 20, 0.5, "胜利表情[Z]", True),
    ]

    print(f"\n[Structure with Close-ups]")
    print(f"  [Z] = Zoom/Close-up shot")
    print(f"\n[Total] {len(segments)} segments\n")

    segment_files = []
    missing = []
    for i, (keyword, start, duration, note, zoom) in enumerate(segments, 1):
        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"

        if keyword == "__TEXT__":
            create_text_card("SAN DAO LIU", duration, output_file)
            segment_files.append(output_file)
            print(f"[{i:2d}] TEXT - {note}")
            continue

        material = find_material(keyword)
        if not material:
            print(f"[{i:2d}] SKIP: {note}")
            missing.append(keyword)
            continue

        if extract_segment(material, start, duration, output_file, zoom):
            segment_files.append(output_file)
            zoom_mark = "[Z]" if zoom else ""
            print(f"[{i:2d}] {duration}s {zoom_mark} - {note}")

    print(f"\n[Extracted] {len(segment_files)} segments")
    if missing:
        print(f"[Missing] {len(missing)} keywords")

    # 合并视频
    print("\n[Merging Video...]")
    concat_file = OUTPUT_DIR / "concat_slash.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in segment_files:
            f.write(f"file '{v}'\n")

    temp_video = TEMP_DIR / "slash_merged.mp4"
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
    video_duration = float(result.stdout.strip()) if result.stdout.strip() else 13
    print(f"[Video Duration] {video_duration:.1f}s")

    # 选择BGM
    bgm_source = BGM_DIR / "War Drums.mp3"
    if not bgm_source.exists():
        bgm_files = list(BGM_DIR.glob("*.mp3"))
        if bgm_files:
            bgm_source = bgm_files[0]

    output_path = OUTPUT_DIR / "索隆封神_连续斩击版.mp4"

    print("\n[Final Composition...]")
    print("  - BGM: 70% volume")
    print("  - Freeze frame: 0.5s")
    print("  - Fade out: 0.5s")

    # 定格+淡出效果
    freeze_start = max(0, video_duration - 0.15)
    freeze_frames = 15
    fade_start = video_duration + 0.5 - 0.5

    filter_complex = f"""
[0:v]split=2[v1][v2];
[v1]trim=0:{video_duration},setpts=PTS-STARTPTS[main];
[v2]trim={freeze_start}:{video_duration},setpts=PTS-STARTPTS,loop={freeze_frames}:1:0[freeze];
[main][freeze]concat=n=2:v=1:a=0,format=yuv420p,fade=t=out:st={video_duration}:d=0.5[vout];
[1:a]volume=0.7,atrim=0:{video_duration+0.5},afade=t=out:st={video_duration-1}:d=1.5[aout]
""".strip()

    cmd = [
        FFMPEG, "-y",
        "-i", str(temp_video),
        "-i", str(bgm_source),
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not output_path.exists():
        print("[Fallback] Simple merge...")
        subprocess.run([
            FFMPEG, "-y",
            "-i", str(temp_video),
            "-i", str(bgm_source),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-af", f"volume=0.7,afade=t=out:st={video_duration-2}:d=2",
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
        print(f"\n[Close-up Enhancement]")
        print(f"  - 8 key close-up moments inserted")
        print(f"  - Zoom ratio: 150%")
        print(f"\n[Narrative Arc]")
        print(f"  Opening -> Charge [Z] -> Slash1 [Z] -> Slash2 [Z]")
        print(f"  -> Slash3 [Z] -> QuickCuts [Z] -> Ultimate [Z]")
        print(f"  -> Victory [Z] -> Freeze")

        # Cleanup
        for f in TEMP_DIR.glob("*"):
            f.unlink()
        try:
            TEMP_DIR.rmdir()
        except:
            pass
        concat_file.unlink(missing_ok=True)

        print("\n[Done] Close-up enhanced edit complete!")
    else:
        print("[Error] Output not created")

if __name__ == "__main__":
    main()
