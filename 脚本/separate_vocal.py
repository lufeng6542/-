# -*- coding: utf-8 -*-
"""
人声分离 + BGM替换脚本
功能：保留原视频的人声/音效，替换背景音乐
"""

import os
import subprocess
from pathlib import Path
import imageio_ffmpeg

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()

PROJECT_DIR = Path("D:/海贼王剪辑项目")
OUTPUT_DIR = PROJECT_DIR / "输出"

def separate_vocals(video_path: str, output_dir: Path = None):
    """
    使用Demucs分离人声和背景音乐

    返回: (vocals_path, no_vocals_path)
    """
    import torch

    if output_dir is None:
        output_dir = PROJECT_DIR / "分离音频"

    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("正在使用AI分离人声...")
    print("=" * 50)

    # 使用demucs命令行工具（使用mdx模型，不需要diffq）
    cmd = [
        "demucs",
        "-n", "mdx",  # 使用mdx模型，不需要diffq
        "-o", str(output_dir),
        "--two-stems=vocals",  # 只分离人声和伴奏
        video_path
    ]

    print(f"处理文件: {video_path}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"[ERROR] 分离失败: {result.stderr}")
        return None, None

    # 查找输出文件
    video_name = Path(video_path).stem
    separated_dir = output_dir / "htdemucs" / video_name

    vocals_path = separated_dir / "vocals.wav"
    no_vocals_path = separated_dir / "no_vocals.wav"

    if vocals_path.exists() and no_vocals_path.exists():
        print(f"[OK] 分离完成!")
        print(f"  人声: {vocals_path}")
        print(f"  伴奏: {no_vocals_path}")
        return str(vocals_path), str(no_vocals_path)
    else:
        print("[ERROR] 找不到分离后的文件")
        return None, None


def mix_audio(vocals_path: str, new_bgm_path: str, output_path: str,
              vocals_volume: float = 1.0, bgm_volume: float = 0.5):
    """
    混合人声和新BGM
    """
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", vocals_path,
        "-i", new_bgm_path,
        "-filter_complex",
        f"[0:a]volume={vocals_volume}[v];[1:a]volume={bgm_volume}[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def replace_bgm_with_vocals(video_path: str, new_bgm_path: str, output_path: str):
    """
    完整流程：分离人声 -> 混合新BGM -> 合成视频
    """
    print("\n" + "=" * 50)
    print("人声分离 + BGM替换 流程")
    print("=" * 50)

    # 1. 从视频中提取音频
    print("\n[步骤1] 提取音频...")
    temp_audio = PROJECT_DIR / "分离音频" / "temp_audio.wav"
    temp_audio.parent.mkdir(parents=True, exist_ok=True)

    cmd = [FFMPEG_PATH, "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le", str(temp_audio)]
    subprocess.run(cmd, capture_output=True)

    # 2. 分离人声
    print("\n[步骤2] AI分离人声...")
    vocals_path, no_vocals_path = separate_vocals(str(temp_audio))

    if not vocals_path:
        print("[ERROR] 人声分离失败")
        return False

    # 3. 混合人声和新BGM
    print("\n[步骤3] 混合人声和新BGM...")
    mixed_audio = PROJECT_DIR / "分离音频" / "mixed_audio.aac"

    if mix_audio(vocals_path, new_bgm_path, str(mixed_audio), vocals_volume=1.0, bgm_volume=0.4):
        print("[OK] 音频混合完成")
    else:
        print("[ERROR] 音频混合失败")
        return False

    # 4. 合成最终视频
    print("\n[步骤4] 合成最终视频...")
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path,
        "-i", str(mixed_audio),
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)

    if result.returncode == 0:
        print(f"\n[OK] 全部完成!")
        print(f"输出: {output_path}")
        return True
    else:
        print("[ERROR] 视频合成失败")
        return False


def main():
    import sys

    print("=" * 50)
    print("人声分离 + BGM替换工具")
    print("=" * 50)

    # 默认文件
    video = "D:/海贼王剪辑项目/输出/精选合成_抖音竖屏.mp4"
    bgm = "D:/海贼王剪辑项目/BGM/逆光.mp3"
    output = "D:/海贼王剪辑项目/输出/精选合成_保留人声_新BGM.mp4"

    if len(sys.argv) > 1:
        video = sys.argv[1]
    if len(sys.argv) > 2:
        bgm = sys.argv[2]
    if len(sys.argv) > 3:
        output = sys.argv[3]

    print(f"\n输入视频: {video}")
    print(f"新BGM: {bgm}")
    print(f"输出: {output}")

    # 检查文件是否存在
    if not os.path.exists(video):
        print(f"\n[ERROR] 视频文件不存在: {video}")
        return

    if not os.path.exists(bgm):
        print(f"\n[ERROR] BGM文件不存在: {bgm}")
        return

    # 执行
    replace_bgm_with_vocals(video, bgm, output)


if __name__ == "__main__":
    main()
