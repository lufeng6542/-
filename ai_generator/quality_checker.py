#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频质量验证器
生成视频 → FFmpeg提取关键帧 → 智谱视觉分析 → 与原提示词对比评分
"""

import json
import subprocess
import tempfile
from pathlib import Path

from .zhipu_client import ZhipuClient


def extract_frames(video_path, output_dir, count=4):
    """
    用FFmpeg从视频中提取关键帧

    Args:
        video_path: 视频文件路径
        output_dir: 帧输出目录
        count: 总帧数用于计算间隔（提取4个帧：首、1/3、2/3、末）

    Returns:
        list[str]: 提取的帧文件路径列表
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 先获取总帧数
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", str(video_path)],
        capture_output=True, text=True, timeout=30,
    )
    probe_data = json.loads(probe.stdout)
    video_stream = next((s for s in probe_data.get("streams", []) if s.get("codec_type") == "video"), {})
    total_frames = int(video_stream.get("nb_frames", 60))
    duration = video_stream.get("duration", "?")
    width = video_stream.get("width", "?")
    height = video_stream.get("height", "?")

    # 计算要提取的帧索引
    indices = [0, total_frames // 3, (total_frames * 2) // 3, max(0, total_frames - 1)]

    # 用select滤镜提取指定帧
    select_expr = "+".join(f"eq(n\\,{idx})" for idx in indices)
    frame_pattern = str(output_dir / "frame_%03d.png")

    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path),
         "-vf", f"select={select_expr}", "-vsync", "vfr", frame_pattern],
        capture_output=True, timeout=60,
    )

    # 收集生成的帧
    frames = sorted(output_dir.glob("frame_*.png"))
    return [str(f) for f in frames], {
        "total_frames": total_frames,
        "duration": duration,
        "resolution": f"{width}x{height}",
    }


def check(video_path, original_prompt, output_dir=None):
    """
    视频质量验证

    Args:
        video_path: 视频文件路径
        original_prompt: 原始提示词
        output_dir: 输出目录（报告和帧保存位置）

    Returns:
        dict: 验证报告
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"视频不存在: {video_path}")

    if output_dir:
        output_dir = Path(output_dir)
    else:
        output_dir = video_path.parent / "verify_output"

    frames_dir = output_dir / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  视频生成质量验证")
    print("=" * 60)
    print(f"\n  原始提示词: {original_prompt}\n")

    # Step 1: 提取关键帧
    print("  Step 1: 提取关键帧...")
    frames, video_info = extract_frames(video_path, frames_dir)
    print(f"  提取了 {len(frames)} 个帧 ({video_info['resolution']}, {video_info['duration']}s)")

    if not frames:
        raise RuntimeError("未能提取任何帧")

    # Step 2: 视觉分析
    print("\n  Step 2: 视觉分析...")
    client = ZhipuClient()
    descriptions = []
    for i, frame in enumerate(frames):
        print(f"  分析帧 {i + 1}/{len(frames)}...")
        desc = client.analyze_image(frame)
        descriptions.append(desc)
        print(f"  帧 {i + 1}: {desc[:60]}...")

    # Step 3: 对比评分
    print("\n  Step 3: 质量评估...")
    result = client.compare_prompts(original_prompt, descriptions)

    # 输出报告
    print("\n" + "=" * 60)
    print("  验证报告")
    print("=" * 60)
    print(f"\n  原始提示词: {original_prompt}")
    print(f"\n  综合评分: {result.get('score', 'N/A')}/100")
    if "subject_score" in result:
        print(f"    主体一致性: {result['subject_score']}/100")
        print(f"    场景还原度: {result['scene_score']}/100")
        print(f"    动作合理性: {result['action_score']}/100")
    print(f"\n  总结: {result.get('summary', 'N/A')}")
    print(f"\n  详细分析:\n{result.get('details', 'N/A')}")

    # 保存报告
    report = {
        "test_time": __import__("datetime").datetime.now().isoformat(),
        "original_prompt": original_prompt,
        "video_info": video_info,
        "extracted_frames": len(frames),
        "frame_descriptions": descriptions,
        "evaluation": result,
    }

    report_path = output_dir / "verify_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n  报告已保存: {report_path}")
    print(f"  帧已保存: {frames_dir}/")

    # 判定结果
    score = result.get("score", -1)
    print("\n" + "=" * 60)
    if score >= 70:
        print("  [通过] 视频内容与提示词匹配度良好")
    elif score >= 40:
        print("  [部分通过] 视频内容与提示词存在偏差")
    elif score > 0:
        print("  [失败] 视频内容与提示词差异较大")
    else:
        print("  [异常] 无法完成自动评分")
    print("=" * 60)

    return report
