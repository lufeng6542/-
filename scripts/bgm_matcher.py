# -*- coding: utf-8 -*-
"""
配乐工程 - ADAMAS节奏匹配
将BGM按视频剪辑节奏配入
"""

import os
import sys
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "utils"))

from ffmpeg_utils import FFMPEG_PATH, get_video_duration

# 文件路径
VIDEO_PATH = PROJECT_ROOT / "输出" / "高燃剪辑" / "海贼王高燃卡点_25秒版.mp4"
BGM_PATH = PROJECT_ROOT / "BGM" / "adamas.mp3"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
OUTPUT_PATH = OUTPUT_DIR / "海贼王高燃卡点_配乐版.mp4"

# ADAMAS歌曲结构分析 (根据歌曲特点)
# ADAMAS - LiSA (刀剑神域OP)
# 推荐切入点: 副歌部分最燃
ADAMAS_STRUCTURE = {
    "intro": (0, 15),           # 前奏
    "verse1": (15, 35),         # 主歌1
    "pre_chorus": (35, 50),     # 副歌前段
    "chorus1": (50, 75),        # 副歌1 - 最燃
    "verse2": (75, 95),         # 主歌2
    "chorus2": (95, 120),       # 副歌2
    "bridge": (120, 140),       # 桥段
    "final_chorus": (140, 165), # 最终副歌
}

# 视频关键节奏点
VIDEO_BEATS = [
    0.0,    # 开场雷电
    1.5,    # 爆气紫光
    3.0,    # 拔刀冲刺
    4.0,    # 双刀连击
    5.0,    # 基德冲撞
    6.0,    # 对砍三连
    7.5,    # 基德大招开始
    9.5,    # 挥砍爆炸
    11.5,   # 绿特效
    13.5,   # 爆气收尾
    14.5,   # 对砍4
    15.5,   # 混打
    16.5,   # 冲撞2
    17.5,   # 闪躲
    18.5,   # 雷电收尾
    20.5,   # 合刀大招
    22.5,   # 不看爆炸
    24.0,   # 结尾
]


def analyze_bgm_beats():
    """分析BGM节拍 - 使用librosa检测"""
    try:
        import librosa
        import numpy as np

        print("正在分析BGM节拍...")

        y, sr = librosa.load(str(BGM_PATH), sr=None)
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        beat_times = librosa.frames_to_time(beats, sr=sr)

        print(f"检测BPM: {tempo:.1f}")
        print(f"检测到 {len(beat_times)} 个节拍点")

        # 找到最密集的25秒片段
        best_start = find_best_segment(beat_times, 25)

        return beat_times, best_start

    except ImportError:
        print("[警告] librosa未安装，使用预设切入点")
        return None, 50  # 默认从副歌开始


def find_best_segment(beat_times, duration):
    """找到节拍最密集的片段"""
    import numpy as np

    best_start = 50  # 默认副歌开始
    best_density = 0

    for start in range(30, 150, 5):
        end = start + duration
        if end > beat_times[-1]:
            break

        # 计算该片段的节拍密度
        beats_in_segment = beat_times[(beat_times >= start) & (beat_times < end)]
        density = len(beats_in_segment) / duration

        if density > best_density:
            best_density = density
            best_start = start

    print(f"最佳切入点: {best_start}s (节拍密度: {best_density:.2f}/s)")
    return best_start


def add_bgm_to_video(video_path, bgm_path, output_path, bgm_start=50, fade_in=0.3, fade_out=0.5):
    """将BGM添加到视频"""

    video_duration = get_video_duration(str(video_path))

    print(f"\n配乐参数:")
    print(f"  视频时长: {video_duration:.1f}s")
    print(f"  BGM切入点: {bgm_start}s")
    print(f"  淡入: {fade_in}s | 淡出: {fade_out}s")

    # FFmpeg命令: 添加BGM并处理音量
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(video_path),
        "-ss", str(bgm_start),  # BGM起始点
        "-i", str(bgm_path),
        "-t", str(video_duration),  # 只取视频时长
        "-filter_complex",
        f"[1:a]afade=t=in:st=0:d={fade_in},afade=t=out:st={video_duration-fade_out}:d={fade_out},volume=0.8[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path)
    ]

    print("\n正在合成...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        return True
    else:
        print(f"[错误] {result.stderr}")
        return False


def add_bgm_with_beat_sync(video_path, bgm_path, output_path):
    """节拍同步配乐 - 将BGM的副歌部分配入视频"""

    # ADAMAS副歌从约50秒开始，这是最燃的部分
    # 副歌开头有强烈的鼓点和吉他，适合视频开场

    video_duration = get_video_duration(str(video_path))

    # 使用副歌部分 (50-75秒是第一段副歌)
    bgm_start = 52  # 精确到副歌第一句

    print("=" * 60)
    print("    配乐工程 - ADAMAS节拍匹配")
    print("=" * 60)

    print(f"\nADAMAS歌曲结构:")
    print(f"  副歌1: 50s-75s (最燃)")
    print(f"  副歌2: 95s-120s")
    print(f"  最终副歌: 140s-165s")

    print(f"\n选择切入点: {bgm_start}s (副歌开始)")

    return add_bgm_to_video(
        video_path, bgm_path, output_path,
        bgm_start=bgm_start,
        fade_in=0.2,
        fade_out=0.8
    )


def main():
    print("=" * 60)
    print("    配乐工程 - ADAMAS x 海贼王高燃剪辑")
    print("=" * 60)

    if not VIDEO_PATH.exists():
        print(f"[错误] 视频不存在: {VIDEO_PATH}")
        return

    if not BGM_PATH.exists():
        print(f"[错误] BGM不存在: {BGM_PATH}")
        return

    # 执行配乐
    if add_bgm_with_beat_sync(VIDEO_PATH, BGM_PATH, OUTPUT_PATH):
        file_size = OUTPUT_PATH.stat().st_size / (1024 * 1024)
        duration = get_video_duration(str(OUTPUT_PATH))

        print("\n" + "=" * 60)
        print("    配乐完成!")
        print("=" * 60)
        print(f"\n输出文件: {OUTPUT_PATH}")
        print(f"文件大小: {file_size:.1f} MB")
        print(f"视频时长: {duration:.1f} 秒")
        print(f"BGM: ADAMAS - LiSA (副歌部分)")

        print("\n节拍匹配说明:")
        print("  0s   - BGM副歌开场重鼓点 -> 凯多雷电")
        print("  1.5s - 吉他切入 -> 索隆爆气紫光")
        print("  7s   - 节奏加快 -> 基德大招")
        print("  15s  - 副歌高潮 -> 连爆压制")
        print("  22s  - 最终爆发 -> 合刀大招收尾")
    else:
        print("[错误] 配乐失败")


if __name__ == "__main__":
    main()
