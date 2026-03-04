# -*- coding: utf-8 -*-
"""
海贼王素材下载脚本 - 使用 yt-dlp
支持：B站、YouTube、抖音等平台
"""

import subprocess
import sys
from pathlib import Path

# 素材保存路径
OUTPUT_DIR = Path("D:/海贼王剪辑项目/素材")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def download_video(url: str, format_option: str = "best"):
    """
    下载视频
    url: 视频链接
    format_option: 格式选项
        - "best": 最佳质量
        - "best[height<=1080]": 限制1080p
        - "best[height<=720]": 限制720p
    """
    cmd = [
        "yt-dlp",
        "-f", format_option,
        "-o", str(OUTPUT_DIR / "%(title)s.%(ext)s"),
        "--no-playlist",  # 不下载播放列表
        "--concurrent-fragments", "4",  # 多线程下载
        url
    ]

    print(f"正在下载: {url}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("✅ 下载完成!")
    else:
        print("❌ 下载失败")

def download_bilibili(url: str):
    """下载B站视频（最佳质量）"""
    cmd = [
        "yt-dlp",
        "-f", "bestvideo+bestaudio/best",
        "-o", str(OUTPUT_DIR / "%(title)s.%(ext)s"),
        "--no-playlist",
        "--concurrent-fragments", "4",
        url
    ]

    print(f"正在从B站下载: {url}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("✅ 下载完成!")
    else:
        print("❌ 下载失败")

def download_audio_only(url: str):
    """仅下载音频（用于提取BGM）"""
    bgm_dir = Path("D:/海贼王剪辑项目/BGM")
    bgm_dir.mkdir(parents=True, exist_ok=True)

    cmd = [
        "yt-dlp",
        "-x",  # 仅提取音频
        "--audio-format", "mp3",
        "--audio-quality", "0",  # 最佳质量
        "-o", str(bgm_dir / "%(title)s.%(ext)s"),
        url
    ]

    print(f"正在下载音频: {url}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("✅ 音频下载完成!")
    else:
        print("❌ 下载失败")

def batch_download(urls: list):
    """批量下载"""
    for url in urls:
        download_video(url)

# ============ 预设的海贼王素材链接 ============

# B站海贼王素材合集（示例，需要替换为真实链接）
ONEPIECE_MATERIALS = {
    "B站素材": [
        # 在这里添加B站链接
        # "https://www.bilibili.com/video/BVxxxxxx",
    ],
    "BGM": [
        # 海贼王BGM链接
        # "https://www.bilibili.com/video/BVxxxxxx",
    ]
}

# ============ 主程序 ============

def main():
    print("=" * 50)
    print("海贼王素材下载器 (yt-dlp)")
    print("=" * 50)
    print()
    print("使用方法:")
    print("1. 下载单个视频: python download_materials.py <URL>")
    print("2. 仅下载音频:   python download_materials.py --audio <URL>")
    print("3. 批量下载:     编辑脚本中的 ONEPIECE_MATERIALS 字典")
    print()
    print("支持平台:")
    print("  - B站 (bilibili.com)")
    print("  - YouTube (youtube.com)")
    print("  - 抖音 (douyin.com)")
    print("  - 其他1000+网站")
    print()

    if len(sys.argv) > 1:
        if sys.argv[1] == "--audio" and len(sys.argv) > 2:
            download_audio_only(sys.argv[2])
        elif sys.argv[1] == "--batch":
            print("批量下载预设素材...")
            for category, urls in ONEPIECE_MATERIALS.items():
                print(f"\n分类: {category}")
                for url in urls:
                    if category == "BGM":
                        download_audio_only(url)
                    else:
                        download_video(url)
        else:
            download_video(sys.argv[1])
    else:
        print("示例命令:")
        print('  python download_materials.py "https://www.bilibili.com/video/BV1xxx"')
        print('  python download_materials.py --audio "https://www.bilibili.com/video/BV1xxx"')

if __name__ == "__main__":
    main()
