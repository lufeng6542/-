# -*- coding: utf-8 -*-
"""
索隆专属高燃剪辑 - 剑豪之魂
"我可是要成为世界第一大剑豪的男人！"
十年铁粉信仰版 - 抖音9:16竖屏
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "utils"))

from ffmpeg_utils import FFMPEG_PATH, get_video_duration

MATERIAL_DIR = Path("E:/海贼王临时素材库")
OUTPUT_DIR = PROJECT_ROOT / "输出" / "索隆专属"
TEMP_DIR = OUTPUT_DIR / "temp"

# ═══════════════════════════════════════════════════════════════
# 索隆专属剪辑方案 - 剑豪之魂 (25秒抖音黄金版)
# 以信仰为核心的镜头设计
# ═══════════════════════════════════════════════════════════════
ZORO_EDITION = {
    "name": "索隆_剑豪之魂_信仰版",
    "duration": 25,
    "segments": [
        # ===== 【0-2.5s】 开局爆点 - 必须震撼 =====
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 35, 1.0, "三刀流奥义"),
        ("罗罗诺亚·索隆 爆气紫光 跳出去 砍击", 0, 1.5, "霸气紫光"),

        # ===== 【2.5-5s】 狂傲本色 - 索隆的性格 =====
        ("罗罗诺亚·索隆 伸舌头 挑衅老头 练刀", 0, 1.0, "狂傲挑衅"),
        ("罗罗诺亚·索隆 拔起刀 举起双刀 冲过去", 0, 1.5, "拔刀冲刺"),

        # ===== 【5-12s】 连击爆发 - 卡点核心区 =====
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 5, 0.8, "绿光斩1"),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 15, 0.8, "绿光斩2"),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 25, 0.8, "绿光斩3"),
        ("罗罗诺亚·索隆 和 武士 对砍", 0, 0.5, "对砍1"),
        ("罗罗诺亚·索隆 和 武士 对砍", 4, 0.5, "对砍2"),
        ("罗罗诺亚·索隆 和 武士 对砍", 8, 0.5, "对砍3"),
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 8, 1.5, "鬼气斩"),
        ("罗罗诺亚·索隆 爆气紫光 跳出去 砍击", 15, 1.0, "紫光连击"),

        # ===== 【12-15s】 承受 - 真男人的证明 =====
        ("罗罗诺亚·索隆 被紫色气息包裹住 痛苦", 10, 1.0, "承受痛苦"),
        ("罗罗诺亚·索隆 被撞到 墙上 打斗 刀柄掉下来", 5, 1.0, "被撞"),
        ("罗罗诺亚·索隆 抵挡 武士攻击 被震开", 5, 1.0, "硬扛站着"),

        # ===== 【15-20s】 王者归来 - 反杀时刻 =====
        ("罗罗诺亚·索隆 攻击武士 振刀 抵挡住", 10, 1.5, "振刀反击"),
        ("罗罗诺亚·索隆 和 武士 混打着 后被击飞 抬头", 20, 1.5, "抬头不屈"),
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 15, 2.0, "反杀大招"),

        # ===== 【20-25s】 终局定格 - 信仰收尾 =====
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 38, 2.5, "从不看爆炸"),
        ("罗罗诺亚·索隆 小时候 躺在地上不甘心", 5, 1.5, "初心"),
    ]
}

# 燃点字幕 (配合时间轴)
ZORO_QUOTES = [
    (1.0, "世界第一大剑豪"),
    (5.0, "三刀流"),
    (9.0, "鬼气"),
    (14.0, "站着"),
    (18.0, "绝不后退"),
    (22.0, "我从不看爆炸"),
]

# 封面标题候选
COVER_TITLES = [
    "索隆：我从不看爆炸",
    "站着死，也不跪着活",
    "三刀流·世界第一大剑豪",
    "受了伤也要站着",
    "这就是索隆的浪漫",
]


def find_material(keyword: str) -> Path:
    """查找素材"""
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None


def extract_segment(video_path: Path, start: float, duration: float, output_path: Path, add_flash: bool = False) -> bool:
    """提取片段 - 竖屏格式 9:16"""
    # 构建滤镜
    vf_filters = ["scale=1080:1920:force_original_aspect_ratio=decrease",
                  "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black"]

    # 开场镜头加闪白效果
    if add_flash:
        vf_filters.append("format=rgba")
        vf_filters.append("fade=t=in:st=0:d=0.1:c=white")
        vf_filters.append("format=yuv420p")

    vf = ",".join(vf_filters)

    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", str(start),
        "-i", str(video_path),
        "-t", str(duration),
        "-vf", vf,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def concat_videos(video_list: List[Path], output_path: Path) -> bool:
    """合并视频"""
    concat_file = OUTPUT_DIR / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for v in video_list:
            f.write(f"file '{v}'\n")

    cmd = [
        FFMPEG_PATH, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    concat_file.unlink(missing_ok=True)
    return result.returncode == 0


def print_edition_info():
    """打印剪辑方案信息"""
    print("\n" + "=" * 50)
    print("   [剑豪之魂] - 剪辑结构")
    print("=" * 50)
    print("""
    [0-2.5s]   开局爆点   三刀流奥义+霸气紫光
    [2.5-5s]   狂傲本色   挑衅+拔刀冲刺
    [5-12s]    连击爆发   六刀连斩+鬼气斩
    [12-15s]   承受硬扛   痛但站着
    [15-20s]   王者归来   振刀反击+反杀大招
    [20-25s]   终局定格   从不看爆炸+初心
    """)
    print("=" * 50)


def main():
    print("\n" + "=" * 60)
    print("    [*] 索隆专属 - 剑豪之魂")
    print("    '我可是要成为世界第一大剑豪的男人！'")
    print("=" * 60)

    print_edition_info()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    segments = ZORO_EDITION["segments"]
    segment_files = []

    print(f"\n共 {len(segments)} 个精选片段")
    print("-" * 50)

    # 阶段标记
    phases = [
        ("开局爆点", 0, 2),
        ("狂傲本色", 2, 4),
        ("连击爆发", 4, 11),
        ("承受硬扛", 11, 14),
        ("王者归来", 14, 17),
        ("终局定格", 17, 19)
    ]

    for i, (keyword, start, duration, desc) in enumerate(segments, 1):
        material = find_material(keyword)
        if not material:
            print(f"  [{i:2d}] [跳过] {desc}")
            continue

        output_file = TEMP_DIR / f"zoro_{i:03d}.mp4"

        # 第一个镜头加闪白
        add_flash = (i == 1)

        if extract_segment(material, start, duration, output_file, add_flash):
            segment_files.append(output_file)

            # 标记名场面
            highlight = ""
            if "从不看爆炸" in desc:
                highlight = "← 经典名场面"
            elif "霸气" in desc or "紫光" in desc:
                highlight = "← 霸气觉醒"
            elif "鬼气" in desc:
                highlight = "← 大招"
            elif "初心" in desc:
                highlight = "← 信仰"

            print(f"  [{i:2d}] {desc} ({duration}s) {highlight}")

    print(f"\n[OK] 成功提取 {len(segment_files)} 个片段")

    # 合并
    print("\n正在合成索隆专属视频...")
    output_path = OUTPUT_DIR / f"{ZORO_EDITION['name']}.mp4"

    if concat_videos(segment_files, output_path):
        duration = get_video_duration(str(output_path))
        size = output_path.stat().st_size / (1024 * 1024)

        print("\n" + "=" * 60)
        print("    [完成] 索隆专属剪辑完成！")
        print("=" * 60)
        print(f"\n[输出] {output_path}")
        print(f"[大小] {size:.1f} MB")
        print(f"[时长] {duration:.1f} 秒")

        print("\n" + "-" * 50)
        print("   [字幕] 推荐字幕:")
        for t, text in ZORO_QUOTES:
            print(f"   [{t:.1f}s] {text}")

        print("\n" + "-" * 50)
        print("   [封面] 封面标题候选:")
        for i, title in enumerate(COVER_TITLES, 1):
            print(f"   {i}. {title}")

        print("\n" + "-" * 50)
        print("   [BGM] 建议BGM: adamas.mp3 (卡点强)")

        # 清理
        for f in TEMP_DIR.glob("*.mp4"):
            f.unlink()
        if TEMP_DIR.exists():
            TEMP_DIR.rmdir()

        print("\n[*] 以剑豪之名，致敬索隆！")
        return output_path

    return None


if __name__ == "__main__":
    main()
