# -*- coding: utf-8 -*-
"""
索隆的意志 - 成长历程压缩版
开场：面部特写 + TTS台词配音
"""

import subprocess
import asyncio
import edge_tts
from pathlib import Path

PROJECT_ROOT = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_ROOT / "素材"
BGM_DIR = PROJECT_ROOT / "BGM"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_will"

FFMPEG = "ffmpeg"

def find_material(keyword):
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def generate_voice(text, output_path):
    """同步生成TTS配音"""
    async def _gen():
        communicate = edge_tts.Communicate(text, "zh-CN-YunxiNeural")
        await communicate.save(str(output_path))
    asyncio.run(_gen())

def extract_segment(video_path, start, duration, output_path, zoom=False, slow=False):
    """提取片段（无声）"""
    filters = []
    if zoom:
        filters.append("scale=1620:2880:force_original_aspect_ratio=decrease")
        filters.append("pad=1620:2880:(ow-iw)/2:(oh-ih)/2:black")
        filters.append("crop=1080:1920:270:480")
    else:
        filters.append("scale=1080:1920:force_original_aspect_ratio=decrease")
        filters.append("pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black")
    if slow:
        filters.append("setpts=1.5*PTS")

    vf = ",".join(filters)
    t = duration / 1.5 if slow else duration

    cmd = [
        FFMPEG, "-y", "-ss", str(start), "-i", str(video_path),
        "-t", str(t), "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an", "-r", "30",
        str(output_path)
    ]
    return subprocess.run(cmd, capture_output=True).returncode == 0

def main():
    print("=" * 60)
    print("    [Zoro's Will] With TTS Voice Acting")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    # 开场台词
    opening_quote = "我发誓，我再也不会输了！"
    voice_path = TEMP_DIR / "opening_voice.mp3"

    # 生成TTS配音
    print(f'\n[Generating Voice] "{opening_quote}"')
    try:
        generate_voice(opening_quote, voice_path)
        print(f"  -> {voice_path.name} OK")
    except Exception as e:
        print(f"  -> Error: {e}")
        return

    # 获取配音时长
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(voice_path)],
        capture_output=True, text=True
    )
    voice_duration = float(result.stdout.strip()) if result.stdout.strip() else 3.0
    print(f"  -> Duration: {voice_duration:.1f}s")

    # 素材片段（不含开场）
    segments = [
        # 第一幕：童年挫折
        ("罗罗诺亚·索隆 被敲头 输了", 0, 1.2, "童年失败", False, True),
        ("罗罗诺亚·索隆 小时候 躺在地上不甘心", 0, 1.2, "不甘心", False, True),
        ("罗罗诺亚·索隆 在夜晚 小时候 切磋", 0, 1.2, "夜晚苦练", False, False),
        # 第二幕：承受磨难
        ("罗罗诺亚·索隆 被紫色气息包裹住", 0, 1.5, "承受伤害", False, False),
        ("罗罗诺亚·索隆 被击飞 闪躲", 0, 0.8, "被击飞", False, False),
        ("罗罗诺亚·索隆 被撞到 墙上", 0, 0.8, "撞墙", False, False),
        ("罗罗诺亚·索隆 被武士 冲击 刀被震飞", 0, 0.8, "刀震飞", False, False),
        ("罗罗诺亚·索隆 振刀 努力抵挡攻击", 0, 1.0, "努力抵挡", False, False),
        ("罗罗诺亚·索隆 和 武士 混打着 后被击飞 抬头", 0, 1.0, "抬头不屈", False, False),
        # 第三幕：觉醒爆发
        ("罗罗诺亚·索隆 爆气紫光", 0, 1.5, "觉醒爆气", True, False),
        ("罗罗诺亚·索隆 拔起刀 举起双刀 冲过去", 3, 1.0, "拔刀冲锋", False, False),
        ("罗罗诺亚·索隆 绿色的刀 劈砍", 5, 0.8, "绿光斩", True, False),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 10, 0.8, "双刀连击", False, False),
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 15, 0.5, "合刀蓄力", True, False),
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 20, 2.0, "阎王三刀流", True, False),
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 40, 1.5, "背对爆炸", False, False),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 25, 1.0, "胜利定格", True, False),
    ]

    print(f"\n[Extracting Segments]")

    # 提取开场特写视频（无声）
    opening_video = TEMP_DIR / "opening_face.mp4"
    face_material = find_material("罗罗诺亚·索隆 被紫色气息包裹住")
    if face_material:
        cmd = [
            FFMPEG, "-y", "-ss", "0", "-i", str(face_material),
            "-t", str(voice_duration),
            "-vf", "scale=2160:3840:force_original_aspect_ratio=decrease,crop=1080:1920:540:650",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-r", "30",
            str(opening_video)
        ]
        subprocess.run(cmd, capture_output=True)
        print(f"  [OP] Opening face close-up")

    # 提取其他片段
    segment_files = [opening_video] if opening_video.exists() else []
    for i, (keyword, start, duration, note, zoom, slow) in enumerate(segments, 1):
        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"
        material = find_material(keyword)
        if not material:
            continue
        if extract_segment(material, start, duration, output_file, zoom, slow):
            segment_files.append(output_file)
            act = "A1" if i <= 3 else ("A2" if i <= 9 else "A3")
            print(f"  [{i:2d}][{act}] {duration}s - {note}")

    print(f"\n[Total] {len(segment_files)} segments")

    # 合并视频
    print("\n[Merging Video...]")
    concat_file = OUTPUT_DIR / "concat_will.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in segment_files:
            f.write(f"file '{v}'\n")

    temp_video = TEMP_DIR / "will_merged.mp4"
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        str(temp_video)
    ], capture_output=True)

    # 获取视频时长
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(temp_video)],
        capture_output=True, text=True
    )
    video_duration = float(result.stdout.strip()) if result.stdout.strip() else 20
    print(f"[Video Duration] {video_duration:.1f}s")

    # 选择BGM
    bgm_source = BGM_DIR / "31_Legendary.mp3"
    if not bgm_source.exists():
        bgm_files = list(BGM_DIR.glob("*.mp3"))
        if bgm_files:
            bgm_source = bgm_files[0]

    output_path = OUTPUT_DIR / "索隆封神_意志觉醒版.mp4"

    print("\n[Final Composition...]")
    print("  - Voice: TTS opening quote (100%)")
    print("  - BGM: Background music (40%)")

    # 最终合成：视频 + 台词配音 + BGM
    # 开场前3秒有配音，后面只有BGM
    filter_complex = f"""
[1:a]volume=1.5,adelay=0|0[voice];
[2:a]volume=0.4,afade=t=out:st={video_duration-2}:d=2[bgm];
[voice][bgm]amix=inputs=2:duration=longest:dropout_transition=0[aout]
""".strip()

    cmd = [
        FFMPEG, "-y",
        "-i", str(temp_video),
        "-i", str(voice_path),
        "-i", str(bgm_source),
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-vf", f"fade=t=out:st={video_duration-0.5}:d=0.5",
        "-t", str(video_duration),
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if not output_path.exists() or output_path.stat().st_size == 0:
        print("[Fallback] Voice only...")
        # 备选：只有配音
        cmd2 = [
            FFMPEG, "-y",
            "-i", str(temp_video),
            "-i", str(voice_path),
            "-map", "0:v", "-map", "1:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path)
        ]
        subprocess.run(cmd2, capture_output=True)

    if output_path.exists() and output_path.stat().st_size > 0:
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
        print(f"\n[Voice Acting]")
        print(f'  Quote: "{opening_quote}"')
        print(f"  Voice: TTS zh-CN-YunxiNeural (Male)")
        print(f"  Duration: {voice_duration:.1f}s")

        # Cleanup
        for f in TEMP_DIR.glob("*"):
            try:
                f.unlink()
            except:
                pass
        try:
            TEMP_DIR.rmdir()
        except:
            pass
        concat_file.unlink(missing_ok=True)

        print("\n[Done] Video with voice acting complete!")
    else:
        print("[Error] Output not created")

if __name__ == "__main__":
    main()
