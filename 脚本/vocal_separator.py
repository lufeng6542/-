# -*- coding: utf-8 -*-
"""
使用audio-separator库分离人声
"""

import os
import sys

# 添加FFmpeg到PATH
import imageio_ffmpeg
ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# 复制ffmpeg并重命名为ffmpeg.exe
import shutil
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_link = os.path.join(ffmpeg_dir, "ffmpeg.exe")
if not os.path.exists(ffmpeg_link):
    shutil.copy(ffmpeg_exe, ffmpeg_link)
    print(f"[INFO] 已复制FFmpeg到: {ffmpeg_link}")

from audio_separator.separator import Separator

def separate_vocals(input_audio: str, output_dir: str):
    """
    分离人声和伴奏

    Args:
        input_audio: 输入音频文件路径
        output_dir: 输出目录
    """
    print("=" * 50)
    print("AI人声分离")
    print("=" * 50)

    os.makedirs(output_dir, exist_ok=True)

    # 初始化分离器
    separator = Separator(
        output_dir=output_dir,
        output_format="WAV",
        model_file_dir=os.path.join(output_dir, "models")
    )

    # 加载模型（使用MDX模型，效果更好）
    print("\n[步骤1] 下载/加载AI模型...")
    # 使用 UVR-MDX-NET-Inst_HQ_3 模型，自动下载
    separator.load_model(model_filename="UVR-MDX-NET-Inst_HQ_3.onnx")

    # 执行分离
    print("\n[步骤2] AI分离人声...")
    primary_stem_path, secondary_stem_path = separator.separate(input_audio)

    print(f"\n[OK] 分离完成!")
    print(f"  人声: {primary_stem_path}")
    print(f"  伴奏: {secondary_stem_path}")

    return primary_stem_path, secondary_stem_path


if __name__ == "__main__":
    input_file = "D:/海贼王剪辑项目/分离音频/original_audio.wav"
    output_folder = "D:/海贼王剪辑项目/分离音频/separated"

    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_folder = sys.argv[2]

    separate_vocals(input_file, output_folder)
