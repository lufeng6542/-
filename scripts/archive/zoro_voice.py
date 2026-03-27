# -*- coding: utf-8 -*-
"""
索隆意志版 - 带台词配音
简化版：分步骤执行
"""

import subprocess
import asyncio
import edge_tts
from pathlib import Path

# 路径
PROJECT = Path("D:/海贼王剪辑项目")
MATERIAL = PROJECT / "素材"
BGM = PROJECT / "BGM"
OUTPUT = PROJECT / "输出" / "高燃剪辑"
TEMP = OUTPUT / "temp_voice"

FFMPEG = "ffmpeg"

def find(keyword):
    for f in MATERIAL.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None

def main():
    print("=" * 50)
    print("  Zoro's Will - With Voice")
    print("=" * 50)

    OUTPUT.mkdir(parents=True, exist_ok=True)
    TEMP.mkdir(parents=True, exist_ok=True)

    # 1. 生成台词配音
    print("\n[1/5] Generating voice...")
    quote = "我发誓，我再也不会输了！"
    voice_file = TEMP / "voice.mp3"

    async def gen_voice():
        tts = edge_tts.Communicate(quote, "zh-CN-YunxiNeural")
        await tts.save(str(voice_file))
    asyncio.run(gen_voice())

    # 获取配音时长
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(voice_file)],
        capture_output=True, text=True
    )
    voice_dur = float(r.stdout.strip())
    print(f"  Quote: {quote}")
    print(f"  Duration: {voice_dur:.1f}s")

    # 2. 提取开场特写
    print("\n[2/5] Extracting opening close-up...")
    opening_mp4 = TEMP / "01_opening.mp4"
    face_src = find("罗罗诺亚·索隆 被紫色气息包裹住")
    subprocess.run([
        FFMPEG, "-y", "-ss", "0", "-i", str(face_src),
        "-t", str(voice_dur),
        "-vf", "scale=2160:3840:force_original_aspect_ratio=decrease,crop=1080:1920:540:650",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-an", "-r", "30",
        str(opening_mp4)
    ], capture_output=True)
    print(f"  -> 01_opening.mp4")

    # 3. 提取其他片段
    print("\n[3/5] Extracting segments...")
    clips = [
        ("罗罗诺亚·索隆 被敲头 输了", 0, 1.2),
        ("罗罗诺亚·索隆 小时候 躺在地上不甘心", 0, 1.2),
        ("罗罗诺亚·索隆 在夜晚 小时候 切磋", 0, 1.2),
        ("罗罗诺亚·索隆 被紫色气息包裹住", 0, 1.5),
        ("罗罗诺亚·索隆 被击飞 闪躲", 0, 0.8),
        ("罗罗诺亚·索隆 被撞到 墙上", 0, 0.8),
        ("罗罗诺亚·索隆 被武士 冲击 刀被震飞", 0, 0.8),
        ("罗罗诺亚·索隆 振刀 努力抵挡攻击", 0, 1.0),
        ("罗罗诺亚·索隆 和 武士 混打着 后被击飞 抬头", 0, 1.0),
        ("罗罗诺亚·索隆 爆气紫光", 0, 1.5),
        ("罗罗诺亚·索隆 拔起刀 举起双刀 冲过去", 3, 1.0),
        ("罗罗诺亚·索隆 绿色的刀 劈砍", 5, 0.8),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 10, 0.8),
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 20, 2.0),
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 40, 1.5),
    ]

    files = [opening_mp4]
    for i, (kw, st, dur) in enumerate(clips, 2):
        src = find(kw)
        if not src:
            continue
        out = TEMP / f"{i:02d}_clip.mp4"
        subprocess.run([
            FFMPEG, "-y", "-ss", str(st), "-i", str(src),
            "-t", str(dur),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
            "-c:v", "libx264", "-preset", "fast", "-crf", "18",
            "-an", "-r", "30",
            str(out)
        ], capture_output=True)
        files.append(out)
        print(f"  -> {i:02d}_clip.mp4")

    print(f"  Total: {len(files)} clips")

    # 4. 合并视频
    print("\n[4/5] Merging video...")
    concat_txt = OUTPUT / "concat.txt"
    with open(concat_txt, "w") as f:
        for v in files:
            f.write(f"file '{v}'\n")

    merged = TEMP / "merged.mp4"
    subprocess.run([
        FFMPEG, "-y", "-f", "concat", "-safe", "0",
        "-i", str(concat_txt),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-an",
        str(merged)
    ], capture_output=True)

    # 获取时长
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(merged)],
        capture_output=True, text=True
    )
    video_dur = float(r.stdout.strip())
    print(f"  Duration: {video_dur:.1f}s")

    # 5. 合成最终视频（配音 + BGM）
    print("\n[5/5] Final composition...")
    bgm_file = BGM / "31_Legendary.mp3"
    if not bgm_file.exists():
        bgm_file = list(BGM.glob("*.mp3"))[0]

    output = OUTPUT / "索隆封神_意志觉醒版.mp4"

    # 配音放前3秒，BGM全程40%音量
    subprocess.run([
        FFMPEG, "-y",
        "-i", str(merged),
        "-i", str(voice_file),
        "-i", str(bgm_file),
        "-filter_complex",
        f"[1:a]volume=1.5[voice];[2:a]volume=0.35,afade=t=out:st={video_dur-2}:d=2[bgm];[voice][bgm]amix=inputs=2:duration=longest[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        "-vf", f"fade=t=out:st={video_dur-0.5}:d=0.5",
        str(output)
    ], capture_output=True)

    if output.exists() and output.stat().st_size > 0:
        size = output.stat().st_size / (1024 * 1024)
        print(f"\n{'=' * 50}")
        print("  COMPLETE!")
        print(f"{'=' * 50}")
        print(f"\n  File: {output.name}")
        print(f"  Size: {size:.1f} MB")
        print(f"  Duration: {video_dur:.1f}s")
        print(f"\n  Voice: '{quote}'")
        print(f"  Voice duration: {voice_dur:.1f}s")

        # 清理
        for f in TEMP.glob("*"):
            f.unlink()
        TEMP.rmdir()
        concat_txt.unlink()
    else:
        print("  Error: Output failed")

if __name__ == "__main__":
    main()
