# -*- coding: utf-8 -*-
"""
视频编辑器
视频剪辑合成功能
"""

import os
import json
import subprocess
from pathlib import Path
from typing import List, Optional, Dict
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from utils.ffmpeg_utils import FFMPEG_PATH, format_duration
from config.settings import VIDEO_WIDTH, VIDEO_HEIGHT


@dataclass
class EditTask:
    """编辑任务"""
    segments: List[Path]
    bgm_path: Path
    output_path: Path
    use_vocals: bool = False
    output_name: str = "输出"


class VideoEditor:
    """视频编辑器"""

    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir

    def concat_segments(
        self,
        segments: List[Path],
        bgm_path: Path,
        output_path: Path,
        use_vocals: bool = False,
        vocal_files: Dict = None
    ) -> Optional[Path]:
        """
        合成片段

        Args:
            segments: 片段列表
            bgm_path: BGM路径
            output_path: 输出路径
            use_vocals: 是否保留原人声
            vocal_files: 人声文件字典

        Returns:
            输出文件路径
        """
        if not segments:
            print("[错误] 没有片段")
            return None

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"\n【开始合成】")
        print(f"  片段: {len(segments)} 个")
        print(f"  BGM: {bgm_path.name}")
        print(f"  保留人声: {'是' if use_vocals else '否'}")

        # 生成concat文件
        concat_file = output_path.parent / "concat_temp.txt"
        with open(concat_file, "w", encoding="utf-8") as f:
            for seg in segments:
                f.write(f"file '{seg}'\n")

        if use_vocals and vocal_files:
            # 夷合人声版本
            return self._edit_with_vocals(segments, bgm_path, output_path, vocal_files, concat_file)
        else:
            # 简单版本
            return self._edit_simple(concat_file, bgm_path, output_path)

    def _edit_simple(self, concat_file: Path, bgm_path: Path, output_path: Path) -> Optional[Path]:
        """简单合成"""
        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-i", str(bgm_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            str(output_path)
        ]

        print("  正在合成...")
        result = subprocess.run(cmd, capture_output=True)

        # 清理
        concat_file.unlink(missing_ok=True)

        if result.returncode == 0:
            size = output_path.stat().st_size / (1024 * 1024)
            print(f"  [完成] {output_path.name} ({size:.1f} MB)")
            return output_path
        else:
            print(f"  [失败] 合成失败")
            return None

    def _edit_with_vocals(
        self,
        segments: List[Path],
        bgm_path: Path,
        output_path: Path,
        vocal_files: Dict,
        concat_file: Path
    ) -> Optional[Path]:
        """带人声合成"""
        # 先合成无声视频
        temp_video = output_path.parent / "temp_no_audio.mp4"

        cmd1 = [
            FFMPEG_PATH, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            str(temp_video)
        ]

        print("  步骤1: 合成视频轨道...")
        result = subprocess.run(cmd1, capture_output=True)
        if result.returncode != 0:
            print("  [失败] 视频合成失败")
            concat_file.unlink(missing_ok=True)
            return None

        # 创建人声concat文件
        vocals_concat = output_path.parent / "vocals_concat.txt"
        with open(vocals_concat, "w", encoding="utf-8") as f:
            for seg in segments:
                seg_key = str(seg)
                if seg_key in vocal_files:
                    f.write(f"file '{vocal_files[seg_key]['vocals']}'\n")

        # 混合音频
        print("  步骤2: 混合音频...")
        cmd2 = [
            FFMPEG_PATH, "-y",
            "-i", str(temp_video),
            "-f", "concat", "-safe", "0", "-i", str(vocals_concat),
            "-i", str(bgm_path),
            "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest:dropout_transition=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path)
        ]

        result = subprocess.run(cmd2, capture_output=True)

        # 清理
        concat_file.unlink(missing_ok=True)
        vocals_concat.unlink(missing_ok=True)
        temp_video.unlink(missing_ok=True)

        if result.returncode == 0:
            size = output_path.stat().st_size / (1024 * 1024)
            print(f"  [完成] {output_path.name} ({size:.1f} MB)")
            return output_path
        else:
            print("  [失败] 音频混合失败")
            return None

    def to_vertical(self, video_path: Path, output_path: Path = None) -> Optional[Path]:
        """
        转为抖音竖屏

        Args:
            video_path: 输入视频
            output_path: 输出路径

        Returns:
            输出文件
        """
        video_path = Path(video_path)
        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_竖屏.mp4"
        else:
            output_path = Path(output_path)

        print(f"\n转为竖屏: {video_path.name}")

        cmd = [
            FFMPEG_PATH, "-y",
            "-i", str(video_path),
            "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "copy",
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode == 0:
            size = output_path.stat().st_size / (1024 * 1024)
            print(f"  [完成] {output_path.name} ({size:.1f} MB)")
            return output_path
        else:
            print("  [失败]")
            return None

    def replace_bgm(
        self,
        video_path: Path,
        new_bgm_path: Path,
        output_path: Path = None
    ) -> Optional[Path]:
        """
        替换BGM

        Args:
            video_path: 输入视频
            new_bgm_path: 新BGM
            output_path: 输出路径

        Returns:
            输出文件
        """
        video_path = Path(video_path)
        new_bgm_path = Path(new_bgm_path)

        if output_path is None:
            output_path = video_path.parent / f"{video_path.stem}_新BGM.mp4"
        else:
            output_path = Path(output_path)

        print(f"\n替换BGM: {video_path.name}")
        print(f"  新BGM: {new_bgm_path.name}")

        cmd = [
            FFMPEG_PATH, "-y",
            "-i", str(video_path),
            "-i", str(new_bgm_path),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True)

        if result.returncode == 0:
            size = output_path.stat().st_size / (1024 * 1024)
            print(f"  [完成] {output_path.name} ({size:.1f} MB)")
            return output_path
        else:
            print("  [失败]")
            return None
