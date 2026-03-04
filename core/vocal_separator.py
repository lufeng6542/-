# -*- coding: utf-8 -*-
"""
人声分离器
使用AI模型分离人声和伴奏
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Tuple, Optional, Dict
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from utils.ffmpeg_utils import FFMPEG_PATH, extract_audio
from config.settings import MDX23C_MODEL, MODELS_DIR


@dataclass
class SeparatedAudio:
    """分离后的音频"""
    original: Path
    vocals: Optional[Path]
    instrumental: Optional[Path]


class VocalSeparator:
    """人声分离器"""

    def __init__(self, model_path: Path = None):
        self.model_path = model_path or MDX23C_MODEL
        self.separator = None

    def check_model(self) -> bool:
        """检查模型是否存在"""
        return self.model_path.exists()

    def separate(
        self,
        input_audio: Path,
        output_dir: Path
    ) -> SeparatedAudio:
        """
        分离人声和伴奏

        Args:
            input_audio: 输入音频/视频路径
            output_dir: 输出目录

        Returns:
            分离结果
        """
        input_audio = Path(input_audio)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        result = SeparatedAudio(original=input_audio, vocals=None, instrumental=None)

        # 如果是视频，先提取音频
        if input_audio.suffix.lower() in ['.mp4', '.mkv', '.avi', '.mov']:
            audio_path = output_dir / "temp_audio.wav"
            if not audio_path.exists():
                print("  提取音频...")
                if not extract_audio(str(input_audio), str(audio_path)):
                    print("  [失败] 音频提取失败")
                    return result
            input_audio = audio_path

        # 尝试使用 audio_separator
        try:
            from audio_separator.separator import Separator

            print("  使用 audio_separator 分离...")
            separator = Separator(
                output_dir=str(output_dir),
                output_format="WAV",
                model_file_dir=str(MODELS_DIR)
            )

            # 加载模型
            if self.check_model():
                print(f"  加载模型: {self.model_path.name}")
                separator.load_model(model_filename=str(self.model_path))
            else:
                print("  使用默认模型...")
                separator.load_model(model_filename="UVR-MDX-NET-Inst_HQ_3.onnx")

            # 分离
            primary, secondary = separator.separate(str(input_audio))

            if primary:
                result.vocals = Path(primary)
            if secondary:
                result.instrumental = Path(secondary)

            print(f"  [完成] 人声: {result.vocals.name if result.vocals else 'N/A'}")
            print(f"  [完成] 伴奏: {result.instrumental.name if result.instrumental else 'N/A'}")

            return result

        except ImportError:
            print("  [警告] audio_separator 未安装，使用FFmpeg简单方法")
            return self._simple_separate(input_audio, output_dir)
        except Exception as e:
            print(f"  [错误] {e}")
            return self._simple_separate(input_audio, output_dir)

    def _simple_separate(
        self,
        input_audio: Path,
        output_dir: Path
    ) -> SeparatedAudio:
        """使用FFmpeg简单方法分离"""
        result = SeparatedAudio(original=input_audio, vocals=None, instrumental=None)

        vocals_path = output_dir / "vocals_center.wav"
        instrumental_path = output_dir / "instrumental.wav"

        # 使用中心声道提取人声
        cmd_vocals = [
            FFMPEG_PATH, "-y",
            "-i", str(input_audio),
            "-af", "pan=1|c=2|pan=2|c=1",
            "-vn",
            str(vocals_path)
        ]

        result_v = subprocess.run(cmd_vocals, capture_output=True)

        # 提取伴奏
        cmd_inst = [
            FFMPEG_PATH, "-y",
            "-i", str(input_audio),
            "-af", "pan=1|c=1|pan=2|c=2",
            "-vn",
            str(instrumental_path)
        ]

        result_inst = subprocess.run(cmd_inst, capture_output=True)

        if result_v.returncode == 0 and result_inst.returncode == 0:
            result.vocals = vocals_path
            result.instrumental = instrumental_path
            print("  [完成] 使用FFmpeg简单分离")
        else:
            print("  [警告] 分离效果可能不理想")

        return result

    def batch_separate(
        self,
        video_paths: list,
        output_base_dir: Path
    ) -> Dict[str, SeparatedAudio]:
        """批量分离"""
        results = {}
        for i, video in enumerate(video_paths, 1):
            video = Path(video)
            print(f"\n[{i}/{len(video_paths)}] {video.name}")

            output_dir = output_base_dir / video.parent.name / video.stem
            results[str(video)] = self.separate(video, output_dir)

        return results
