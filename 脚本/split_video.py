# -*- coding: utf-8 -*-
"""
视频素材分割脚本
功能：将长视频按指定时长分割成小片段，方便选择镜头
"""

import os
import subprocess
from pathlib import Path
import imageio_ffmpeg

# 设置FFmpeg路径
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

# ============ 配置区域 ============
PROJECT_DIR = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_DIR / "素材"
OUTPUT_DIR = PROJECT_DIR / "素材片段"

# 分割参数
SEGMENT_DURATION = 4  # 每个片段的时长（秒）

# ============ 核心功能 ============

def get_video_duration(video_path: str) -> float:
    """获取视频总时长（秒）- 使用ffmpeg"""
    cmd = [
        FFMPEG_PATH,
        "-i", video_path,
        "-f", "null",
        "-"
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        # 从stderr中解析时长，格式如: Duration: 00:01:23.45
        import re
        match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', result.stderr)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
        return 0
    except Exception as e:
        print(f"[DEBUG] 获取时长失败: {e}")
        return 0


def split_video(video_path: str, segment_duration: int = 3, output_dir: Path = None):
    """
    将视频分割成多个小片段

    Args:
        video_path: 视频文件路径
        segment_duration: 每个片段的时长（秒）
        output_dir: 输出目录
    """
    video_path = Path(video_path)
    if output_dir is None:
        output_dir = OUTPUT_DIR

    # 创建输出目录（以原视频名命名子文件夹）
    video_name = video_path.stem
    segment_dir = output_dir / video_name
    segment_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n处理视频: {video_name}")
    print(f"输出目录: {segment_dir}")

    # 获取视频时长
    duration = get_video_duration(str(video_path))
    if duration == 0:
        print(f"[ERROR] 无法读取视频时长: {video_path}")
        return

    print(f"视频时长: {duration:.1f}秒")

    # 计算片段数量
    num_segments = int(duration // segment_duration)
    remainder = duration % segment_duration

    print(f"将分割为: {num_segments} 个片段 (每个{segment_duration}秒)")

    # 分割视频
    for i in range(num_segments):
        start_time = i * segment_duration
        output_file = segment_dir / f"素材{i+1:03d}.mp4"

        cmd = [
            FFMPEG_PATH,
            "-ss", str(start_time),
            "-i", str(video_path),
            "-t", str(segment_duration),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-y",
            str(output_file)
        ]

        print(f"  生成 素材{i+1:03d}")

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            print(f"    [ERROR] 片段生成失败")

    # 处理剩余部分
    if remainder > 1:  # 如果剩余超过1秒
        start_time = num_segments * segment_duration
        output_file = segment_dir / f"素材{num_segments+1:03d}.mp4"

        cmd = [
            FFMPEG_PATH,
            "-ss", str(start_time),
            "-i", str(video_path),
            "-t", str(remainder),
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-y",
            str(output_file)
        ]

        print(f"  生成 素材{num_segments+1:03d}")
        subprocess.run(cmd, capture_output=True)

    print(f"[OK] 完成! 共生成 {num_segments + (1 if remainder > 1 else 0)} 个片段")


def split_video_by_scenes(video_path: str, threshold: float = 0.3, output_dir: Path = None):
    """
    按场景变化分割视频（检测画面切换点）

    Args:
        video_path: 视频文件路径
        threshold: 场景变化阈值（0-1，越小越敏感）
        output_dir: 输出目录
    """
    video_path = Path(video_path)
    if output_dir is None:
        output_dir = OUTPUT_DIR

    video_name = video_path.stem
    segment_dir = output_dir / f"{video_name}_场景分割"
    segment_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n按场景分割: {video_name}")

    # 使用FFmpeg的select过滤器检测场景变化
    # 这是一个简化版本，实际场景检测需要更复杂的处理
    output_pattern = segment_dir / "片段_%03d.mp4"

    cmd = [
        FFMPEG_PATH,
        "-i", str(video_path),
        "-vf", f"select='gt(scene,{threshold})'",
        "-vsync", "vfr",
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-y",
        str(output_pattern)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"[OK] 场景分割完成")


def scan_videos() -> list:
    """扫描素材文件夹中的所有视频"""
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
    videos = []

    for ext in video_extensions:
        videos.extend(MATERIAL_DIR.glob(f"*{ext}"))
        videos.extend(MATERIAL_DIR.glob(f"**/*{ext}"))

    return [str(v) for v in videos]


def main():
    import sys

    print("=" * 50)
    print("视频素材分割工具")
    print("=" * 50)

    # 扫描视频
    videos = scan_videos()

    if not videos:
        print("\n[ERROR] 素材文件夹为空!")
        print(f"请将视频放入: {MATERIAL_DIR}")
        return

    print(f"\n找到 {len(videos)} 个视频文件:")
    for i, v in enumerate(videos, 1):
        size = Path(v).stat().st_size / (1024 * 1024)
        print(f"  {i}. {Path(v).name} ({size:.1f} MB)")

    # 获取分割参数
    segment_duration = SEGMENT_DURATION

    if len(sys.argv) > 1:
        try:
            segment_duration = int(sys.argv[1])
        except:
            pass

    print(f"\n分割设置: 每个片段 {segment_duration} 秒")
    print("-" * 50)

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 分割所有视频
    for video in videos:
        split_video(video, segment_duration, OUTPUT_DIR)

    print("\n" + "=" * 50)
    print("[OK] 全部完成!")
    print("=" * 50)
    print(f"\n片段保存在: {OUTPUT_DIR}")
    print("\n使用方法:")
    print(f"  - 查看片段: 打开 {OUTPUT_DIR}")
    print(f"  - 自定义时长: python split_video.py 5  (每个片段5秒)")


if __name__ == "__main__":
    main()
