#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频创作工具 - 统一命令行入口
AI视频生成 + AI图片生成 + 视频剪辑一站式工具
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
from ai_generator.image_generator import generate as gen_image
from ai_generator.video_generator import generate_from_text as gen_video, generate_from_image as gen_img2video, generate_from_frames as gen_frames2video
from ai_generator.quality_checker import check as verify_video
from ai_generator.pipeline import VideoPipeline, PipelineConfig


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


def cmd_gen_image(args):
    """AI生成图片"""
    output = args.output or "素材/ai_generated.png"
    gen_image(args.prompt, output, ar=args.ar, size=args.size)


def cmd_gen_video(args):
    """AI生成视频（文生视频）"""
    output = args.output or "素材/ai_generated.mp4"
    gen_video(args.prompt, output, ar=args.ar, quality=args.quality,
              auto_verify=args.auto_verify, with_audio=args.audio, fps=args.fps)


def cmd_gen_img2video(args):
    """AI生成视频（图生视频）"""
    output = args.output or "素材/ai_generated.mp4"
    gen_img2video(args.image, args.prompt, output, ar=args.ar, quality=args.quality,
                  auto_verify=args.auto_verify, with_audio=args.audio, fps=args.fps)


def cmd_gen_frames2video(args):
    """AI生成视频（首尾帧生成）"""
    output = args.output or "素材/ai_generated.mp4"
    gen_frames2video(args.first_frame, args.last_frame, args.prompt, output,
                     ar=args.ar, quality=args.quality,
                     auto_verify=args.auto_verify, with_audio=args.audio, fps=args.fps)


def cmd_verify(args):
    """视频质量验证"""
    verify_video(args.input, args.prompt, output_dir=args.output,
                 mode=args.mode, vision_model=args.model)


def cmd_pipeline(args):
    """AI全自动视频创作流水线"""
    config = PipelineConfig(
        ar=args.ar,
        quality=args.quality,
        image_max_retries=args.image_retries,
        video_max_retries=args.video_retries,
        scene_count=args.scenes,
        with_audio=args.audio,
        fps=args.fps,
        output_dir=args.output,
    )
    pipeline = VideoPipeline(config)
    pipeline.run(args.prompt)


def cmd_task_status(args):
    """查询异步任务状态"""
    from ai_generator.zhipu_client import ZhipuClient
    client = ZhipuClient()
    result = client.query_task_status(args.task_id)

    status = result.get("task_status", "未知")
    print(f"\n  任务ID: {args.task_id}")
    print(f"  状态: {status}")

    if status == "SUCCESS":
        videos = result.get("video_result", [])
        if videos:
            print(f"  视频URL: {videos[0]['url']}")
            print(f"  封面URL: {videos[0].get('cover_image_url', '无')}")
    elif status == "FAIL":
        print(f"  失败原因: {result}")


def cmd_history(args):
    """查看AI生成历史记录"""
    from ai_generator.output_manager import list_records
    records = list_records(record_type=args.type, limit=args.limit)

    if not records:
        print("\n  暂无生成记录")
        return

    type_labels = {"image": "图片", "video": "视频", "img2video": "图生视频", "frames2video": "首尾帧生成", "verify": "验证"}
    print(f"\n  最近 {len(records)} 条生成记录:\n")
    for i, r in enumerate(records, 1):
        label = type_labels.get(r.get("type", ""), r.get("type", ""))
        elapsed = r.get("elapsed_seconds", "")
        time_str = f" ({elapsed}s)" if elapsed else ""
        print(f"  {i}. [{label}] {r['time']}")
        print(f"     提示词: {r['prompt'][:60]}{'...' if len(r['prompt']) > 60 else ''}")
        print(f"     文件: {r['output']}{time_str}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="视频创作工具 - AI生成 + 视频剪辑一站式命令行"
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

    # gen 命令组
    gen_parser = subparsers.add_parser("gen", help="AI生成（图片/视频）")
    gen_subparsers = gen_parser.add_subparsers(dest="gen_command", help="生成类型")

    # gen image
    gen_image_parser = gen_subparsers.add_parser("image", help="AI生成图片")
    gen_image_parser.add_argument("prompt", help="提示词")
    gen_image_parser.add_argument("--ar", default="1:1", help="宽高比 (1:1, 16:9, 9:16, 4:3, 3:4)")
    gen_image_parser.add_argument("--size", help="指定尺寸 (如 1280x720)")
    gen_image_parser.add_argument("--output", "-o", help="输出路径")

    # gen video
    gen_video_parser = gen_subparsers.add_parser("video", help="AI生成视频（文生视频）")
    gen_video_parser.add_argument("prompt", help="提示词")
    gen_video_parser.add_argument("--ar", default="16:9", help="宽高比 (1:1, 16:9, 9:16, 4:3, 3:4, 4K)")
    gen_video_parser.add_argument("--quality", "-q", default="speed", choices=["speed", "quality"], help="生成质量")
    gen_video_parser.add_argument("--audio", action="store_true", help="生成带音频的视频")
    gen_video_parser.add_argument("--fps", type=int, choices=[30, 60], help="帧率 (30 或 60)")
    gen_video_parser.add_argument("--auto-verify", action="store_true", help="生成后自动验证质量")
    gen_video_parser.add_argument("--output", "-o", help="输出路径")

    # gen img2video
    gen_img2video_parser = gen_subparsers.add_parser("img2video", help="AI生成视频（图生视频）")
    gen_img2video_parser.add_argument("image", help="首帧图片路径")
    gen_img2video_parser.add_argument("prompt", help="提示词")
    gen_img2video_parser.add_argument("--ar", default="16:9", help="宽高比")
    gen_img2video_parser.add_argument("--quality", "-q", default="speed", choices=["speed", "quality"], help="生成质量")
    gen_img2video_parser.add_argument("--audio", action="store_true", help="生成带音频的视频")
    gen_img2video_parser.add_argument("--fps", type=int, choices=[30, 60], help="帧率 (30 或 60)")
    gen_img2video_parser.add_argument("--auto-verify", action="store_true", help="生成后自动验证质量")
    gen_img2video_parser.add_argument("--output", "-o", help="输出路径")

    # gen frames2video
    gen_frames2video_parser = gen_subparsers.add_parser("frames2video", help="AI生成视频（首尾帧生成）")
    gen_frames2video_parser.add_argument("first_frame", help="首帧图片路径")
    gen_frames2video_parser.add_argument("last_frame", help="尾帧图片路径")
    gen_frames2video_parser.add_argument("prompt", help="提示词")
    gen_frames2video_parser.add_argument("--ar", default="16:9", help="宽高比")
    gen_frames2video_parser.add_argument("--quality", "-q", default="speed", choices=["speed", "quality"], help="生成质量")
    gen_frames2video_parser.add_argument("--audio", action="store_true", help="生成带音频的视频")
    gen_frames2video_parser.add_argument("--fps", type=int, choices=[30, 60], help="帧率 (30 或 60)")
    gen_frames2video_parser.add_argument("--auto-verify", action="store_true", help="生成后自动验证质量")
    gen_frames2video_parser.add_argument("--output", "-o", help="输出路径")

    # verify 命令
    verify_parser = subparsers.add_parser("verify", help="视频质量验证")
    verify_parser.add_argument("--input", "-i", required=True, help="视频文件")
    verify_parser.add_argument("prompt", help="原始提示词")
    verify_parser.add_argument("--output", "-o", help="输出目录")
    verify_parser.add_argument("--mode", "-m", default="auto", choices=["auto", "native", "frames"],
                               help="验证模式: auto(自动), native(GLM-4.6V直接分析), frames(抽帧分析)")
    verify_parser.add_argument("--model", help="视觉模型名称 (默认 glm-4.6v-flash)")

    # pipeline 命令
    pipeline_parser = subparsers.add_parser("pipeline", help="AI全自动视频创作流水线")
    pipeline_parser.add_argument("prompt", help="创作要求（如 '做一个关于海浪的视频'）")
    pipeline_parser.add_argument("--ar", default="16:9", help="宽高比 (1:1, 16:9, 9:16, 4:3, 3:4)")
    pipeline_parser.add_argument("--quality", "-q", default="speed", choices=["speed", "quality"], help="视频生成质量")
    pipeline_parser.add_argument("--scenes", "-s", type=int, help="场景数量 (3-6, 默认由AI决定)")
    pipeline_parser.add_argument("--image-retries", type=int, default=2, help="图片生成最大重试次数 (默认2)")
    pipeline_parser.add_argument("--video-retries", type=int, default=2, help="视频生成最大重试次数 (默认2)")
    pipeline_parser.add_argument("--audio", action="store_true", help="生成带音频的视频")
    pipeline_parser.add_argument("--fps", type=int, choices=[30, 60], help="视频帧率")
    pipeline_parser.add_argument("--output", "-o", help="输出目录 (默认自动归档到 ai_output/)")

    # task-status 命令
    task_parser = subparsers.add_parser("task-status", help="查询AI生成任务状态")
    task_parser.add_argument("task_id", help="任务ID")

    # history 命令
    history_parser = subparsers.add_parser("history", help="查看AI生成历史记录")
    history_parser.add_argument("--type", "-t", choices=["image", "video", "img2video", "frames2video", "verify"], help="筛选类型")
    history_parser.add_argument("--limit", "-n", type=int, default=10, help="显示条数")

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
    elif args.command == "gen":
        if args.gen_command == "image":
            cmd_gen_image(args)
        elif args.gen_command == "video":
            cmd_gen_video(args)
        elif args.gen_command == "img2video":
            cmd_gen_img2video(args)
        elif args.gen_command == "frames2video":
            cmd_gen_frames2video(args)
        else:
            print("用法: python cli.py gen {image|video|img2video|frames2video}")
    elif args.command == "verify":
        cmd_verify(args)
    elif args.command == "task-status":
        cmd_task_status(args)
    elif args.command == "history":
        cmd_history(args)
    elif args.command == "pipeline":
        cmd_pipeline(args)
    else:
        # 显示快速菜单
        show_quick_menu()


def show_quick_menu():
    """显示快速菜单"""
    print("\n" + "=" * 50)
    print("    视频创作工具 - 快速菜单")
    print("=" * 50)
    print("\n剪辑命令:")
    print("  split      分割视频素材")
    print("  separate   人声分离 (去除BGM)")
    print("  edit       视频编辑合成")
    print("  analyze    爆点分析")
    print("  auto       自动剪辑流程")
    print("\nAI生成命令:")
    print("  gen image          AI生成图片")
    print("  gen video          AI生成视频（文生视频）")
    print("  gen img2video      AI生成视频（图生视频）")
    print("  gen frames2video   AI生成视频（首尾帧生成）")
    print("  verify             视频质量验证（支持GLM-4.6V原生视频理解）")
    print("  pipeline           AI全自动视频创作流水线")
    print("  task-status      查询AI生成任务状态")
    print("  history          查看AI生成历史记录")
    print("\n示例:")
    print("  python cli.py split -i 视频.mp4 -d 4")
    print("  python cli.py edit -i 片段目录 -b BGM.mp3")
    print("  python cli.py gen image \"一只猫\" --ar 16:9")
    print("  python cli.py gen video \"海浪拍打沙滩\" --ar 16:9 --audio --fps 60")
    print("  python cli.py gen img2video 首帧.png \"猫咪奔跑\" --ar 9:16")
    print("  python cli.py gen frames2video 首帧.png 尾帧.png \"镜头推近\" --ar 16:9")
    print("  python cli.py verify -i 视频.mp4 \"海浪拍打沙滩\"")
    print("  python cli.py verify -i 视频.mp4 \"海浪拍打沙滩\" --mode native")
    print("  python cli.py pipeline \"做一个关于海浪的视频\"")
    print("  python cli.py pipeline \"城市夜景\" --scenes 5 --quality quality")
    print("  python cli.py task-status <任务ID>")
    print("  python cli.py history")


if __name__ == "__main__":
    main()
