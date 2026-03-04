#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
剪辑大师 - 快速启动器
一键执行高燃剪辑流程
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "utils"))

from ffmpeg_utils import get_video_duration

# 默认配置
DEFAULT_CONFIG = {
    "material_dir": "E:/海贼王临时素材库",
    "bgm_dir": str(PROJECT_ROOT / "BGM"),
    "output_dir": str(PROJECT_ROOT / "输出" / "高燃剪辑"),
    "default_bgm": "adamas.mp3",
    "video_duration": 25,
}


def check_environment():
    """检查环境"""
    print("=" * 60)
    print("    剪辑大师 - 环境检查")
    print("=" * 60)

    checks = []

    # 检查素材目录
    material_dir = Path(DEFAULT_CONFIG["material_dir"])
    if material_dir.exists():
        videos = list(material_dir.glob("*.mp4"))
        checks.append(f"[OK] 素材库: {len(videos)} 个视频")
    else:
        checks.append("[X] 素材库目录不存在")

    # 检查BGM目录
    bgm_dir = Path(DEFAULT_CONFIG["bgm_dir"])
    if bgm_dir.exists():
        bgms = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.m4a"))
        checks.append(f"[OK] BGM库: {len(bgms)} 个音频")
    else:
        checks.append("[X] BGM目录不存在")

    # 检查输出目录
    output_dir = Path(DEFAULT_CONFIG["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    checks.append(f"[OK] 输出目录: {output_dir}")

    # 检查FFmpeg
    try:
        from ffmpeg_utils import FFMPEG_PATH
        checks.append(f"[OK] FFmpeg: {FFMPEG_PATH}")
    except:
        checks.append("[X] FFmpeg未配置")

    for check in checks:
        print(f"  {check}")

    return all("[X]" not in c for c in checks)


def list_materials():
    """列出素材"""
    material_dir = Path(DEFAULT_CONFIG["material_dir"])
    if not material_dir.exists():
        print("[错误] 素材目录不存在")
        return []

    videos = sorted(material_dir.glob("*.mp4"))
    print(f"\n素材列表 ({len(videos)} 个):")

    for i, v in enumerate(videos[:15], 1):
        dur = get_video_duration(str(v))
        print(f"  {i:2d}. [{dur:.0f}s] {v.name[:40]}")

    if len(videos) > 15:
        print(f"  ... 还有 {len(videos) - 15} 个素材")

    return videos


def list_bgms():
    """列出BGM"""
    bgm_dir = Path(DEFAULT_CONFIG["bgm_dir"])
    if not bgm_dir.exists():
        print("[错误] BGM目录不存在")
        return []

    bgms = list(bgm_dir.glob("*.mp3")) + list(bgm_dir.glob("*.m4a"))
    print(f"\nBGM列表 ({len(bgms)} 个):")

    for i, bgm in enumerate(bgms, 1):
        dur = get_video_duration(str(bgm))
        print(f"  {i}. [{dur:.0f}s] {bgm.stem}")

    return bgms


def run_edit():
    """执行剪辑"""
    print("\n正在执行高燃剪辑...")

    import subprocess
    script_path = PROJECT_ROOT / "scripts" / "high_energy_editor.py"

    if script_path.exists():
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT)
        )
        return result.returncode == 0
    else:
        print(f"[错误] 脚本不存在: {script_path}")
        return False


def run_bgm_match(bgm_name=None):
    """执行配乐"""
    print("\n正在执行配乐...")

    import subprocess
    script_path = PROJECT_ROOT / "scripts" / "bgm_matcher.py"

    if script_path.exists():
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT)
        )
        return result.returncode == 0
    else:
        print(f"[错误] 脚本不存在: {script_path}")
        return False


def main():
    print("\n" + "=" * 60)
    print("    剪辑大师 - 高燃卡点视频剪辑")
    print("=" * 60)

    # 环境检查
    if not check_environment():
        print("\n[警告] 环境检查未通过，部分功能可能不可用")

    while True:
        print("\n" + "-" * 40)
        print("操作菜单:")
        print("  1. 查看素材列表")
        print("  2. 查看BGM列表")
        print("  3. 执行高燃剪辑")
        print("  4. 执行配乐")
        print("  5. 一键完成 (剪辑+配乐)")
        print("  0. 退出")

        choice = input("\n请选择: ").strip()

        if choice == "1":
            list_materials()
        elif choice == "2":
            list_bgms()
        elif choice == "3":
            run_edit()
        elif choice == "4":
            run_bgm_match()
        elif choice == "5":
            if run_edit():
                run_bgm_match()
                print("\n全部完成!")

            # 打开输出目录
            output_dir = Path(DEFAULT_CONFIG["output_dir"])
            if output_dir.exists():
                os.startfile(output_dir)
        elif choice == "0":
            print("再见!")
            break
        else:
            print("无效选择")


if __name__ == "__main__":
    main()
