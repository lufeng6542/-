# -*- coding: utf-8 -*-
"""
FFmpeg工具模块
统一管理FFmpeg路径和常用命令
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple

import imageio_ffmpeg

# ============ FFmpeg路径设置 ============
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
FFMPEG_DIR = os.path.dirname(FFMPEG_PATH)

# 添加到PATH
os.environ["PATH"] = FFMPEG_DIR + os.pathsep + os.environ.get("PATH", "")

# 确保ffmpeg.exe存在
FFMPEG_LINK = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
if not os.path.exists(FFMPEG_LINK):
    shutil.copy(FFMPEG_PATH, FFMPEG_LINK)


def get_video_duration(video_path: str) -> float:
    """
    获取视频时长（秒）

    Args:
        video_path: 视频文件路径

    Returns:
        视频时长（秒）
    """
    import re
    cmd = [FFMPEG_PATH, "-i", video_path, "-f", "null", "-"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', result.stderr)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            seconds = float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
        return 0
    except Exception:
        return 0


def get_video_info(video_path: str) -> dict:
    """
    获取视频详细信息

    Args:
        video_path: 视频文件路径

    Returns:
        包含时长、分辨率、帧率等信息的字典
    """
    import re
    cmd = [FFMPEG_PATH, "-i", video_path]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        info = {'duration': 0, 'width': 0, 'height': 0, 'fps': 0, 'size_mb': 0}

        # 时长
        match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', result.stderr)
        if match:
            info['duration'] = int(match.group(1)) * 3600 + int(match.group(2)) * 60 + float(match.group(3))

        # 分辨率
        match = re.search(r'(\d+)x(\d+)', result.stderr)
        if match:
            info['width'] = int(match.group(1))
            info['height'] = int(match.group(2))

        # 帧率
        match = re.search(r'(\d+\.?\d*) fps', result.stderr)
        if match:
            info['fps'] = float(match.group(1))

        # 文件大小
        if os.path.exists(video_path):
            info['size_mb'] = os.path.getsize(video_path) / (1024 * 1024)

        return info
    except Exception:
        return {'duration': 0, 'width': 0, 'height': 0, 'fps': 0, 'size_mb': 0}


def extract_audio(video_path: str, output_audio: str) -> bool:
    """
    从视频中提取音频

    Args:
        video_path: 视频文件路径
        output_audio: 输出音频路径

    Returns:
        是否成功
    """
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path,
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        output_audio
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def concat_videos(video_list: List[str], output_path: str) -> bool:
    """
    合并多个视频

    Args:
        video_list: 视频路径列表
        output_path: 输出路径

    Returns:
        是否成功
    """
    import tempfile

    # 创建concat文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        for video in video_list:
            f.write(f"file '{video}'\n")
        concat_file = f.name

    try:
        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "concat", "-safe", "0",
            "-i", concat_file,
            "-c", "copy",
            output_path
        ]
        result = subprocess.run(cmd, capture_output=True)
        return result.returncode == 0
    finally:
        os.unlink(concat_file)


def add_bgm(video_path: str, bgm_path: str, output_path: str, volume: float = 1.0) -> bool:
    """
    添加背景音乐

    Args:
        video_path: 视频路径
        bgm_path: BGM路径
        output_path: 输出路径
        volume: BGM音量 (0-2)

    Returns:
        是否成功
    """
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path,
        "-i", bgm_path,
        "-filter_complex", f"[1:a]volume={volume}[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        output_path
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def format_duration(seconds: float) -> str:
    """
    格式化时长为 mm:ss 格式
    """
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"
