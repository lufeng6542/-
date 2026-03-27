# -*- coding: utf-8 -*-
"""
高燃剪辑执行脚本
根据预设方案自动剪辑海贼王素材
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "utils"))

from ffmpeg_utils import FFMPEG_PATH, get_video_duration

# 素材库路径
MATERIAL_DIR = PROJECT_ROOT / "素材"
OUTPUT_DIR = PROJECT_ROOT / "输出" / "高燃剪辑"
TEMP_DIR = OUTPUT_DIR / "temp_segments"

# 剪辑方案配置
EDIT_PLAN = {
    "name": "海贼王高燃卡点_25秒版",
    "duration": 25,
    "segments": [
        # (素材名关键词, 开始秒, 时长秒, 描述)
        ("凯多 使用雷电 大笑着 爆炸", 0, 1.5, "开场雷电"),
        ("罗罗诺亚·索隆 爆气紫光", 0, 1.5, "爆气紫光"),
        ("罗罗诺亚·索隆 拔起刀 举起双刀 冲过去", 0, 1.0, "拔刀冲刺"),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 5, 1.0, "双刀连击1"),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 10, 1.0, "双刀连击2"),
        ("基德 使用技能 冲撞夏洛特玲玲", 5, 1.0, "基德冲撞"),
        ("罗罗诺亚·索隆 和 武士 对砍", 0, 0.5, "对砍1"),
        ("罗罗诺亚·索隆 和 武士 对砍", 3, 0.5, "对砍2"),
        ("罗罗诺亚·索隆 和 武士 对砍", 6, 0.5, "对砍3"),
        ("基德 释放图案 攻击夏洛特玲玲", 10, 2.0, "基德大招"),
        ("罗罗诺亚·索隆 努力挥砍 往武士肚子上 爆炸", 5, 2.0, "挥砍爆炸"),
        ("罗罗诺亚·索隆 手持双刀 反复攻击 绿色特效", 15, 2.0, "绿特效连击"),
        ("罗罗诺亚·索隆 爆气紫光", 10, 1.0, "爆气收尾"),
        ("罗罗诺亚·索隆 和 武士 对砍", 5, 1.0, "对砍4"),
        ("罗罗诺亚·索隆 和 武士 混打着", 10, 1.0, "混打"),
        ("基德 使用技能 冲撞夏洛特玲玲", 15, 1.0, "冲撞2"),
        ("罗罗诺亚·索隆 被击飞 闪躲", 0, 1.0, "闪躲"),
        ("凯多 使用雷电 大笑着 爆炸", 20, 2.0, "雷电收尾"),
        ("罗罗诺亚·索隆 合刀 绿色刀刃", 20, 2.0, "合刀大招"),
        ("罗罗诺亚·索隆 合刀 绿色刀刃 从不看爆炸", 35, 1.5, "不看爆炸"),
    ]
}


def find_material(keyword: str) -> Path:
    """根据关键词查找素材"""
    for f in MATERIAL_DIR.glob("*.mp4"):
        if keyword in f.name:
            return f
    return None


def extract_segment(video_path: Path, start: float, duration: float, output_path: Path) -> bool:
    """提取视频片段"""
    cmd = [
        FFMPEG_PATH, "-y",
        "-ss", str(start),
        "-i", str(video_path),
        "-t", str(duration),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-r", "30",
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def add_flash_effect(input_path: Path, output_path: Path, flash_at_start: bool = True) -> bool:
    """添加闪白效果"""
    if flash_at_start:
        # 开头闪白
        filter_complex = "format=rgba,fade=t=in:st=0:d=0.1:c=white,format=yuv420p"
    else:
        filter_complex = "format=rgba,fade=t=out:st=0.4:d=0.1:c=white,format=yuv420p"

    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(input_path),
        "-vf", filter_complex,
        "-c:v", "libx264", "-preset", "fast", "-crf", "18",
        "-c:a", "copy",
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


def main():
    print("=" * 60)
    print("    海贼王高燃剪辑 - 执行中")
    print("=" * 60)

    # 创建目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)

    segments = EDIT_PLAN["segments"]
    segment_files = []

    print(f"\n共 {len(segments)} 个片段需要处理\n")

    # 提取每个片段
    for i, (keyword, start, duration, desc) in enumerate(segments, 1):
        print(f"[{i}/{len(segments)}] {desc}")

        # 查找素材
        material = find_material(keyword)
        if not material:
            print(f"  [跳过] 素材未找到: {keyword[:30]}...")
            continue

        # 输出路径
        output_file = TEMP_DIR / f"seg_{i:03d}.mp4"

        # 提取片段
        if extract_segment(material, start, duration, output_file):
            segment_files.append(output_file)
            print(f"  [OK] {material.name[:35]}...")
            print(f"    时长: {duration}s | 开始: {start}s")
        else:
            print(f"  [失败] 提取失败")

    print(f"\n成功提取 {len(segment_files)} 个片段")

    if not segment_files:
        print("[错误] 没有可用片段")
        return

    # 合并视频
    print("\n正在合成视频...")
    output_path = OUTPUT_DIR / f"{EDIT_PLAN['name']}.mp4"

    if concat_videos(segment_files, output_path):
        # 获取输出信息
        total_duration = get_video_duration(str(output_path))
        file_size = output_path.stat().st_size / (1024 * 1024)

        print("\n" + "=" * 60)
        print("    剪辑完成!")
        print("=" * 60)
        print(f"\n输出文件: {output_path}")
        print(f"文件大小: {file_size:.1f} MB")
        print(f"视频时长: {total_duration:.1f} 秒")
        print(f"片段数量: {len(segment_files)}")

        # 清理临时文件
        print("\n清理临时文件...")
        for f in TEMP_DIR.glob("*.mp4"):
            f.unlink()
        TEMP_DIR.rmdir()

        # 保存剪辑信息
        info = {
            "name": EDIT_PLAN["name"],
            "output": str(output_path),
            "duration": total_duration,
            "segments_count": len(segment_files),
            "segments": [
                {"desc": s[3], "duration": s[2]} for s in segments
            ]
        }
        with open(OUTPUT_DIR / "剪辑信息.json", "w", encoding="utf-8") as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        print("\n[完成] 剪辑信息已保存")

    else:
        print("[错误] 合成失败")


if __name__ == "__main__":
    main()
