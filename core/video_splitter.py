# -*- coding: utf-8 -*-
"""
视频分割器
将视频按时间或场景分割成片段
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from utils.ffmpeg_utils import FFMPEG_PATH, get_video_duration, format_duration


@dataclass
class VideoSegment:
    """视频片段"""
    index: int
    path: Path
    start_time: float
    end_time: float
    duration: float


class VideoSplitter:
    """视频分割器"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir

    def split_by_duration(
        self,
        video_path: Path,
        segment_duration: int = 4,
        output_dir: Path = None
    ) -> List[VideoSegment]:
        """
        按时长分割视频

        Args:
            video_path: 视频文件路径
            segment_duration: 每个片段时长（秒）
            output_dir: 输出目录

        Returns:
            片段列表
        """
        video_path = Path(video_path)
        if output_dir is None:
            output_dir = self.output_dir or video_path.parent

        # 创建输出目录
        video_name = video_path.stem
        segment_dir = Path(output_dir) / video_name
        segment_dir.mkdir(parents=True, exist_ok=True)

        # 获取视频时长
        duration = get_video_duration(str(video_path))
        if duration == 0:
            print(f"[错误] 无法读取视频: {video_path}")
            return []

        # 计算片段数量
        num_segments = int(duration // segment_duration)
        remainder = duration % segment_duration

        print(f"\n分割 {video_name}")
        print(f"  时长: {format_duration(duration)}")
        print(f"  片段: {num_segments} 个 (每个{segment_duration}秒)")

        segments = []

        for i in range(num_segments):
            start_time = i * segment_duration
            output_file = segment_dir / f"素材{i+1:03d}.mp4"

            # 跳过已存在的文件
            if output_file.exists():
                segments.append(VideoSegment(
                    index=i + 1,
                    path=output_file,
                    start_time=start_time,
                    end_time=start_time + segment_duration,
                    duration=segment_duration
                ))
                print(f"  [跳过] 素材{i+1:03d}")
                continue

            cmd = [
                FFMPEG_PATH, "-y",
                "-ss", str(start_time),
                "-i", str(video_path),
                "-t", str(segment_duration),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac",
                str(output_file)
            ]

            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                segments.append(VideoSegment(
                    index=i + 1,
                    path=output_file,
                    start_time=start_time,
                    end_time=start_time + segment_duration,
                    duration=segment_duration
                ))
                print(f"  [完成] 素材{i+1:03d}")
            else:
                print(f"  [失败] 素材{i+1:03d}")

        # 处理剩余部分
        if remainder > 1:
            start_time = num_segments * segment_duration
            output_file = segment_dir / f"素材{num_segments+1:03d}.mp4"

            cmd = [
                FFMPEG_PATH, "-y",
                "-ss", str(start_time),
                "-i", str(video_path),
                "-t", str(remainder),
                "-c:v", "libx264", "-preset", "fast", "-crf", "23",
                "-c:a", "aac",
                str(output_file)
            ]

            result = subprocess.run(cmd, capture_output=True)
            if result.returncode == 0:
                segments.append(VideoSegment(
                    index=num_segments + 1,
                    path=output_file,
                    start_time=start_time,
                    end_time=duration,
                    duration=remainder
                ))
                print(f"  [完成] 素材{num_segments+1:03d}")

        print(f"\n[OK] 共生成 {len(segments)} 个片段")
        return segments

    def scan_segments(self, directory: Path) -> List[Path]:
        """
        扫描目录中的片段
        """
        segments = []
        directory = Path(directory)
        if directory.exists():
            for f in sorted(directory.glob("**/*.mp4")):
                segments.append(f)
        return segments

    def list_segments(self, directory: Path) -> None:
        """
        列出片段信息
        """
        segments = self.scan_segments(directory)
        print(f"\n找到 {len(segments)} 个片段")
        for seg in segments[:10]:
            size = seg.stat().st_size / (1024 * 1024)
            print(f"  {seg.name} ({size:.1f} MB)")
        if len(segments) > 10:
            print(f"  ... 还有 {len(segments) - 10} 个")
