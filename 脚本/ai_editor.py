# -*- coding: utf-8 -*-
"""
海贼王超燃卡点混剪 - AI自动剪辑脚本
功能：自动检测BGM节拍，将视频素材卡点剪辑
"""

import os
import json
import subprocess
from pathlib import Path
import librosa
import numpy as np
import imageio_ffmpeg

# 设置FFmpeg路径（使用imageio自带的）
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
os.environ["IMAGEIO_FFMPEG_EXE"] = FFMPEG_PATH

# ============ 配置区域 ============
PROJECT_DIR = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_DIR / "素材"
BGM_DIR = PROJECT_DIR / "BGM"
OUTPUT_DIR = PROJECT_DIR / "输出"

# 视频参数（抖音竖屏）
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30

# ============ 核心功能 ============

def get_beat_times(bgm_path: str) -> list:
    """
    使用librosa分析BGM，提取节拍时间点
    返回：节拍时间列表（秒）
    """
    print(f"正在分析BGM节拍: {bgm_path}")

    y, sr = librosa.load(bgm_path)

    # 获取节拍
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    # tempo可能是数组，取标量值
    if hasattr(tempo, '__iter__'):
        tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
    else:
        tempo = float(tempo)

    print(f"检测到BPM: {tempo:.1f}")
    print(f"节拍点数量: {len(beat_times)}")

    return beat_times.tolist()


def scan_video_materials() -> list:
    """
    扫描素材文件夹，返回所有视频文件
    """
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv']
    videos = []

    for ext in video_extensions:
        videos.extend(MATERIAL_DIR.glob(f"*{ext}"))
        videos.extend(MATERIAL_DIR.glob(f"**/*{ext}"))

    print(f"找到 {len(videos)} 个视频素材")
    return [str(v) for v in videos]


def generate_edit_plan(beat_times: list, videos: list, clip_duration: float = 2.0) -> dict:
    """
    生成剪辑计划
    beat_times: 节拍时间点
    videos: 视频素材列表
    clip_duration: 每个片段默认时长
    """
    edit_plan = {
        "total_duration": beat_times[-1] if beat_times else 60,
        "clips": []
    }

    # 每隔N个节拍切换一个片段
    beat_interval = 4  # 每4个节拍切换

    for i, beat_time in enumerate(beat_times):
        if i % beat_interval == 0:
            video_index = (i // beat_interval) % len(videos) if videos else 0

            clip = {
                "start_time": beat_time,
                "end_time": beat_times[i + beat_interval] if i + beat_interval < len(beat_times) else beat_time + clip_duration,
                "source": videos[video_index] if videos else "placeholder.mp4",
                "source_start": 0,  # 从素材的什么位置开始截取
                "effects": []
            }

            # 添加转场效果
            if i > 0:
                clip["effects"].append("fade_in_0.3s")

            edit_plan["clips"].append(clip)

    return edit_plan


def create_ffmpeg_command(edit_plan: dict, bgm_path: str, output_path: str) -> str:
    """
    生成FFmpeg剪辑命令
    """
    clips = edit_plan["clips"]

    # 生成concat文件内容
    concat_content = ""
    for clip in clips:
        concat_content += f"file '{clip['source']}'\n"
        concat_content += f"inpoint {clip['source_start']}\n"
        concat_content += f"outpoint {clip['end_time'] - clip['start_time']}\n"

    concat_file = PROJECT_DIR / "脚本" / "concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        f.write(concat_content)

    # FFmpeg命令（使用imageio_ffmpeg路径）
    cmd = f'''
"{FFMPEG_PATH}" -y \\
    -f concat -safe 0 -i "{concat_file}" \\
    -i "{bgm_path}" \\
    -vf "scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2" \\
    -c:v libx264 -preset fast -crf 23 \\
    -c:a aac -b:a 192k \\
    -map 0:v -map 1:a \\
    -shortest \\
    "{output_path}"
'''
    return cmd


def run_edit(edit_plan: dict, bgm_path: str, output_path: str):
    """
    直接执行剪辑
    """
    clips = edit_plan["clips"]

    # 生成concat文件
    concat_content = ""
    for clip in clips:
        concat_content += f"file '{clip['source']}'\n"
        concat_content += f"inpoint {clip['source_start']}\n"
        concat_content += f"outpoint {clip['end_time'] - clip['start_time']}\n"

    concat_file = PROJECT_DIR / "脚本" / "concat.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        f.write(concat_content)

    print("\n正在执行FFmpeg剪辑...")

    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-i", bgm_path,
        "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-map", "0:v", "-map", "1:a",
        "-shortest",
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"[OK] 剪辑完成: {output_path}")
    else:
        print(f"[ERROR] 剪辑失败: {result.stderr}")

    return result.returncode == 0


def add_subtitles(video_path: str, subtitles: list, output_path: str):
    """
    添加字幕
    subtitles: [{"start": 0, "end": 5, "text": "我是要成为海贼王的男人!"}, ...]
    """
    # 生成SRT字幕文件
    srt_content = ""
    for i, sub in enumerate(subtitles, 1):
        srt_content += f"{i}\n"
        srt_content += f"{format_time(sub['start'])} --> {format_time(sub['end'])}\n"
        srt_content += f"{sub['text']}\n\n"

    srt_path = PROJECT_DIR / "脚本" / "subtitles.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        f.write(srt_content)

    # 使用FFmpeg烧录字幕
    cmd = f'ffmpeg -y -i "{video_path}" -vf "subtitles={srt_path}" "{output_path}"'
    return cmd


def format_time(seconds: float) -> str:
    """将秒数转换为SRT时间格式"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


# ============ 主程序 ============

def main():
    import sys

    print("=" * 50)
    print("海贼王超燃卡点混剪 - AI剪辑系统")
    print("=" * 50)

    # 1. 检查素材
    videos = scan_video_materials()
    if not videos:
        print("\n⚠️  素材文件夹为空！")
        print(f"请将视频素材放入: {MATERIAL_DIR}")
        return

    # 2. 检查BGM（支持mp3, wav, m4a格式）
    bgm_files = list(BGM_DIR.glob("*.mp3")) + list(BGM_DIR.glob("*.wav")) + list(BGM_DIR.glob("*.m4a"))
    if not bgm_files:
        print("\n⚠️  BGM文件夹为空！")
        print(f"请将背景音乐放入: {BGM_DIR}")
        return

    # 优先选择"逆光"
    bgm_path = None
    for f in bgm_files:
        if "逆光" in str(f):
            bgm_path = str(f)
            break

    if not bgm_path:
        bgm_path = str(bgm_files[0])

    print(f"\n使用BGM: {bgm_path}")

    # 3. 分析节拍
    beat_times = get_beat_times(bgm_path)

    # 4. 生成剪辑计划
    edit_plan = generate_edit_plan(beat_times, videos)
    print(f"\n生成剪辑计划: {len(edit_plan['clips'])} 个片段")

    # 5. 保存剪辑计划
    plan_path = PROJECT_DIR / "脚本" / "edit_plan.json"
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(edit_plan, f, ensure_ascii=False, indent=2)
    print(f"剪辑计划已保存: {plan_path}")

    # 6. 执行剪辑
    output_path = OUTPUT_DIR / "海贼王卡点混剪_输出.mp4"

    # 检查是否有--run参数
    if "--run" in sys.argv or "-r" in sys.argv:
        success = run_edit(edit_plan, bgm_path, str(output_path))
        if success:
            print(f"\n🎉 成片已生成: {output_path}")
        else:
            print("\n❌ 剪辑失败，请检查素材格式")
    else:
        # 生成命令文件
        ffmpeg_cmd = create_ffmpeg_command(edit_plan, bgm_path, str(output_path))
        cmd_path = PROJECT_DIR / "脚本" / "run_edit.bat"
        with open(cmd_path, "w", encoding="utf-8") as f:
            f.write(ffmpeg_cmd)
        print(f"\nFFmpeg命令已生成: {cmd_path}")

        print("\n" + "=" * 50)
        print("✅ 准备完成！")
        print("=" * 50)
        print(f"\n下一步:")
        print(f"1. 检查剪辑计划: {plan_path}")
        print(f"2. 直接运行: python ai_editor.py --run")
        print(f"3. 或执行bat: {cmd_path}")
        print(f"4. 输出文件: {output_path}")


if __name__ == "__main__":
    main()
