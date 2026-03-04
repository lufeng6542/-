# -*- coding: utf-8 -*-
"""
简单人声提取脚本
使用FFmpeg音频滤波器尝试提取人声（中心声道）
效果不如AI分离，但不需要下载模型
"""

import os
import subprocess
from pathlib import Path
import imageio_ffmpeg

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
PROJECT_DIR = Path("D:/海贼王剪辑项目")

def extract_vocal_center(input_audio: str, output_vocals: str, output_bgm: str):
    """
    使用FFmpeg的pan滤波器提取中心声道（人声通常在中心）

    Args:
        input_audio: 输入音频文件
        output_vocals: 输出人声文件
        output_bgm: 输出伴奏文件
    """
    print("=" * 50)
    print("FFmpeg人声提取（中心声道分离）")
    print("=" * 50)

    # 方法1: 使用pan滤波器提取中心声道
    # 人声通常混音在中心，伴奏在两侧
    print("\n[方法] 使用中心声道提取...")

    # 提取中心声道（人声）
    cmd_vocals = [
        FFMPEG_PATH, "-y",
        "-i", input_audio,
        "-af", "pan=mono|c0=0.5*c0+0.5*c1",  # 混合左右声道提取中心
        "-ac", "2",  # 转回立体声
        "-c:a", "pcm_s16le",
        output_vocals
    ]

    print("  提取人声（中心声道）...")
    result = subprocess.run(cmd_vocals, capture_output=True)
    if result.returncode != 0:
        print(f"  [ERROR] 人声提取失败")
        return False

    # 提取伴奏（左右声道差异）
    cmd_bgm = [
        FFMPEG_PATH, "-y",
        "-i", input_audio,
        "-af", "pan=stereo|c0=c0-c1|c1=c1-c0",  # 提取声道差异
        "-c:a", "pcm_s16le",
        output_bgm
    ]

    print("  提取伴奏（侧声道）...")
    result = subprocess.run(cmd_bgm, capture_output=True)
    if result.returncode != 0:
        print(f"  [ERROR] 伴奏提取失败")
        return False

    print(f"\n[OK] 分离完成!")
    print(f"  人声: {output_vocals}")
    print(f"  伴奏: {output_bgm}")
    return True


def mix_with_new_bgm(vocals_path: str, new_bgm_path: str, output_path: str,
                     vocals_vol: float = 1.5, bgm_vol: float = 0.3):
    """
    混合提取的人声和新BGM

    Args:
        vocals_path: 人声文件
        new_bgm_path: 新BGM文件
        output_path: 输出文件
        vocals_vol: 人声音量
        bgm_vol: BGM音量
    """
    print("\n" + "=" * 50)
    print("混合人声和新BGM")
    print("=" * 50)

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", vocals_path,
        "-i", new_bgm_path,
        "-filter_complex",
        f"[0:a]volume={vocals_vol}[v];[1:a]volume={bgm_vol}[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2",
        "-c:a", "aac", "-b:a", "192k",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)
    if result.returncode == 0:
        print(f"[OK] 混合完成: {output_path}")
        return True
    else:
        print(f"[ERROR] 混合失败")
        return False


def create_final_video(video_path: str, audio_path: str, output_path: str):
    """
    合成最终视频
    """
    print("\n[步骤] 合成最终视频...")

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-shortest",
        output_path
    ]

    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def main():
    import sys

    print("=" * 50)
    print("简单人声提取 + BGM替换")
    print("=" * 50)
    print("\n注意: 此方法使用FFmpeg音频滤波器")
    print("效果不如AI分离，但不需要下载模型")

    # 默认文件
    video = "D:/海贼王剪辑项目/输出/精选合成_抖音竖屏.mp4"
    new_bgm = "D:/海贼王剪辑项目/BGM/逆光.mp3"
    output_dir = PROJECT_DIR / "分离音频"
    output_dir.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1:
        video = sys.argv[1]
    if len(sys.argv) > 2:
        new_bgm = sys.argv[2]

    print(f"\n输入视频: {video}")
    print(f"新BGM: {new_bgm}")

    # 检查文件
    if not os.path.exists(video):
        print(f"\n[ERROR] 视频文件不存在")
        return

    if not os.path.exists(new_bgm):
        print(f"\n[ERROR] BGM文件不存在")
        return

    # 1. 从视频提取音频
    print("\n[步骤1] 提取音频...")
    temp_audio = output_dir / "temp_full_audio.wav"
    cmd = [FFMPEG_PATH, "-y", "-i", video, "-vn", "-acodec", "pcm_s16le", str(temp_audio)]
    subprocess.run(cmd, capture_output=True)

    # 2. 分离人声
    print("\n[步骤2] 分离人声...")
    vocals_path = output_dir / "vocals_center.wav"
    bgm_path = output_dir / "bgm_sides.wav"

    if not extract_vocal_center(str(temp_audio), str(vocals_path), str(bgm_path)):
        print("[ERROR] 人声分离失败")
        return

    # 3. 混合人声和新BGM
    print("\n[步骤3] 混合人声和新BGM...")
    mixed_audio = output_dir / "mixed_vocals_new_bgm.aac"

    if not mix_with_new_bgm(str(vocals_path), new_bgm, str(mixed_audio)):
        print("[ERROR] 音频混合失败")
        return

    # 4. 合成最终视频
    print("\n[步骤4] 合成最终视频...")
    output_video = PROJECT_DIR / "输出" / "精选合成_保留人声_新BGM_简单版.mp4"

    if create_final_video(video, str(mixed_audio), str(output_video)):
        print(f"\n[OK] 全部完成!")
        print(f"输出: {output_video}")
    else:
        print("[ERROR] 视频合成失败")


if __name__ == "__main__":
    main()
