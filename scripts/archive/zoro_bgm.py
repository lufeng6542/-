# -*- coding: utf-8 -*-
"""
索隆专属配乐 - 剑豪之路
"""

import sys
from pathlib import Path
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "utils"))

from ffmpeg_utils import FFMPEG_PATH, get_video_duration

VIDEO_PATH = PROJECT_ROOT / "输出" / "索隆专属" / "索隆_剑豪之魂_信仰版.mp4"
BGM_PATH = PROJECT_ROOT / "BGM" / "adamas.mp3"
OUTPUT_PATH = PROJECT_ROOT / "输出" / "索隆专属" / "索隆_剑豪之魂_成品.mp4"

# 索隆视频节奏点
ZORO_BEATS = {
    "三刀流奥义": 0.0,
    "霸气爆发": 2.0,
    "挑衅": 3.5,
    "拔刀冲刺": 4.5,
    "绿光连斩": 6.0,
    "对砍三连": 8.5,
    "鬼气斩": 10.0,
    "紫光连击": 12.0,
    "承受痛苦": 16.0,
    "反击": 19.0,
    "抬头不屈": 20.5,
    "背影传说": 22.0,
    "初心": 25.0,
}

def add_bgm_zoro():
    """为索隆视频配乐"""

    print("=" * 60)
    print("    索隆专属配乐 - 剑豪之路")
    print("=" * 60)

    if not VIDEO_PATH.exists():
        print(f"[错误] 视频不存在: {VIDEO_PATH}")
        return

    video_duration = get_video_duration(str(VIDEO_PATH))
    print(f"\n视频时长: {video_duration:.1f}s")

    # ADAMAS副歌最燃部分，配合索隆霸气
    # 从52秒切入，正好对应副歌高潮
    bgm_start = 52

    print(f"BGM切入点: {bgm_start}s (ADAMAS副歌)")
    print(f"\n节奏匹配:")
    print(f"  0s   - 副歌重鼓 -> 三刀流奥义")
    print(f"  2s   - 吉他爆发 -> 霸气觉醒")
    print(f"  10s  - 节奏加快 -> 鬼气斩")
    print(f"  22s  - 最终高潮 -> 从不看爆炸")

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(VIDEO_PATH),
        "-ss", str(bgm_start),
        "-i", str(BGM_PATH),
        "-t", str(video_duration),
        "-filter_complex",
        "[1:a]afade=t=in:st=0:d=0.2,afade=t=out:st=23:d=1.0,volume=0.85[aout]",
        "-map", "0:v",
        "-map", "[aout]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(OUTPUT_PATH)
    ]

    print("\n正在合成...")
    result = subprocess.run(cmd, capture_output=True)

    if result.returncode == 0:
        size = OUTPUT_PATH.stat().st_size / (1024 * 1024)
        duration = get_video_duration(str(OUTPUT_PATH))

        print("\n" + "=" * 60)
        print("    配乐完成！")
        print("=" * 60)
        print(f"\n输出: {OUTPUT_PATH}")
        print(f"大小: {size:.1f} MB")
        print(f"时长: {duration:.1f}s")
        print(f"\nBGM: ADAMAS - LiSA")
        print("\n索隆经典台词:")
        print("  '我可是要成为世界第一大剑豪的男人！'")
        print("  '我从不看爆炸'")
        print("  '没什么能让我倒下'")
    else:
        print("[错误] 配乐失败")


if __name__ == "__main__":
    add_bgm_zoro()
