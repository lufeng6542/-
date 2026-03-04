#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
海贼王剪辑项目 - 统一命令行入口
统一管理所有功能
"""

import sys
import json
import argparse
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "utils"))
sys.path.insert(0, str(Path(__file__).parent / "core"))
sys.path.insert(0, str(Path(__file__).parent / "config"))

from core.video_splitter import VideoSplitter
from core.vocal_separator import VocalSeparator
from core.explosion_analyzer import ExplosionAnalyzer
from core.video_editor import VideoEditor


def cmd_split(args):
    """分割视频"""
    splitter = VideoSplitter()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"[错误] 文件不存在: {input_path}")
        return

    segments = splitter.split_by_duration(input_path, args.duration)
    print(f"\n[完成] 生成 {len(segments)} 个片段")


def cmd_separate(args):
    """人声分离"""
    separator = VocalSeparator()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"[错误] 文件不存在: {input_path}")
        return

    result = separator.separate(input_path, args.output)
    if result:
        print(f"\n[完成] 人声: {result.vocals}")
        print(f"[完成] 伴奏: {result.instrumental}")


def cmd_edit(args):
    """视频编辑"""
    editor = VideoEditor()

    if args.input:
        input_path = Path(args.input)
        if input_path.is_dir():
            segments = list(input_path.glob("*.mp4"))
        else:
            segments = [input_path]
    else:
        print("[错误] 请指定输入文件或目录")
        return

    if not args.bgm:
        print("[错误] 请指定BGM文件")
        return

    bgm_path = Path(args.bgm)
    output_name = args.name or "输出"
    output_path = Path(args.output) / f"{output_name}.mp4"

    result = editor.concat_segments(segments, bgm_path, output_path)

    if args.vertical and result:
        editor.to_vertical(result)


def cmd_analyze(args):
    """爆点分析"""
    analyzer = ExplosionAnalyzer()
    input_path = Path(args.input)

    if not input_path.exists():
        print(f"[错误] 文件不存在: {input_path}")
        return

    points = analyzer.analyze_video(input_path)
    print(f"\n[完成] 发现 {len(points)} 个爆点")

    if args.save:
        analyzer.save_results(points, Path(args.save))


def cmd_auto(args):
    """自动剪辑流程"""
    from scripts.auto_editor import AutoEditor
    editor = AutoEditor()
    editor.run()


def main():
    parser = argparse.ArgumentParser(
        description="海贼王剪辑项目 - 统一命令行工具"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # split 命令
    split_parser = subparsers.add_parser("split", help="分割视频")
    split_parser.add_argument("--input", "-i", required=True, help="输入视频")
    split_parser.add_argument("--duration", "-d", type=int, default=4, help="片段时长(秒)")
    split_parser.add_argument("--output", "-o", default="输出", help="输出目录")

    # separate 命令
    separate_parser = subparsers.add_parser("separate", help="人声分离")
    separate_parser.add_argument("--input", "-i", required=True, help="输入视频")
    separate_parser.add_argument("--output", "-o", default="输出", help="输出目录")

    # edit 命令
    edit_parser = subparsers.add_parser("edit", help="视频编辑")
    edit_parser.add_argument("--input", "-i", help="输入片段或目录")
    edit_parser.add_argument("--bgm", "-b", help="BGM文件")
    edit_parser.add_argument("--name", "-n", help="输出文件名")
    edit_parser.add_argument("--output", "-o", default="输出", help="输出目录")
    edit_parser.add_argument("--vertical", "-v", action="store_true", help="转为竖屏")

    # analyze 命令
    analyze_parser = subparsers.add_parser("analyze", help="爆点分析")
    analyze_parser.add_argument("--input", "-i", required=True, help="输入视频")
    analyze_parser.add_argument("--save", "-s", help="保存结果到文件")

    # auto 命令
    auto_parser = subparsers.add_parser("auto", help="自动剪辑流程")

    args = parser.parse_args()

    if args.command == "split":
        cmd_split(args)
    elif args.command == "separate":
        cmd_separate(args)
    elif args.command == "edit":
        cmd_edit(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "auto":
        cmd_auto(args)
    else:
        # 显示快速菜单
        show_quick_menu()


def show_quick_menu():
    """显示快速菜单"""
    print("\n" + "=" * 50)
    print("    海贼王剪辑项目 - 快速菜单")
    print("=" * 50)
    print("\n可用命令:")
    print("  split      分割视频素材")
    print("  separate   人声分离 (去除BGM)")
    print("  edit       视频编辑合成")
    print("  analyze    爆点分析")
    print("  auto       自动剪辑流程")
    print("\n示例:")
    print("  python cli.py split -i 视频.mp4 -d 4")
    print("  python cli.py separate -i 视频.mp4")
    print("  python cli.py edit -i 片段目录 -b BGM.mp3")
    print("  python cli.py analyze -i 视频.mp4")
    print("  python cli.py auto")


if __name__ == "__main__":
    main()
