#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""视频合成模块 - FFmpeg合成漫剧视频"""

import subprocess
import json
from pathlib import Path


def get_audio_duration(audio_path: str) -> float:
    """获取音频文件时长（秒）"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json", audio_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def get_image_duration(frame: dict, default: float = 3.0) -> float:
    """计算单帧图片应展示的时长"""
    if frame.get("audio_path"):
        try:
            return get_audio_duration(frame["audio_path"])
        except Exception:
            pass
    return frame.get("duration", default)


def create_frame_video(
    image_path: str,
    output_path: str,
    duration: float = 3.0,
    resolution: str = "1080x1920",
    zoom_effect: str = "slow_zoom_in",
) -> str:
    """
    将单张图片生成为视频片段（带Ken Burns效果）

    Args:
        image_path: 输入图片路径
        output_path: 输出视频路径
        duration: 时长（秒）
        resolution: 分辨率（宽x高），竖屏漫剧默认1080x1920
        zoom_effect: 运镜效果 (slow_zoom_in, slow_zoom_out, pan_left, pan_right, none)
    """
    w, h = resolution.split("x")
    w, h = int(w), int(h)

    total_frames = round(duration * 30)

    # 先缩放到2倍目标尺寸，让zoompan有足够空间运镜
    sw, sh = w * 2, h * 2

    if zoom_effect == "slow_zoom_in":
        vf = f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},zoompan=z='min(zoom+0.0008,1.3)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30"
    elif zoom_effect == "slow_zoom_out":
        vf = f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},zoompan=z='if(eq(on,1),1.3,max(zoom-0.0008,1.0))':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30"
    elif zoom_effect == "pan_left":
        vf = f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},zoompan=z='1.08':d={total_frames}:x='(iw-iw/zoom)*on/{total_frames}':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30"
    elif zoom_effect == "pan_right":
        vf = f"scale={sw}:{sh}:force_original_aspect_ratio=increase,crop={sw}:{sh},zoompan=z='1.08':d={total_frames}:x='(iw-iw/zoom)*(1-on/{total_frames})':y='ih/2-(ih/zoom/2)':s={w}x{h}:fps=30"
    else:
        vf = f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},zoompan=z='1':d={total_frames}:x='iw/2':y='ih/2':s={w}x{h}:fps=30"

    image_path_resolved = str(Path(image_path).resolve())
    output_path_resolved = str(Path(output_path).resolve())

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path_resolved,
        "-vf", vf,
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-an",
        output_path_resolved
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # 降级：不用zoompan，直接静态图
        print(f"    zoompan失败，降级为静态帧")
        cmd_simple = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", image_path_resolved,
            "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}",
            "-t", str(duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-an",
            output_path_resolved
        ]
        subprocess.run(cmd_simple, capture_output=True, check=True)
    return output_path


def get_video_duration(video_path: str) -> float:
    """获取视频文件时长（秒）"""
    cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "json", video_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data["format"]["duration"])


def trim_video(video_path: str, output_path: str, duration: float) -> str:
    """裁切视频到指定时长"""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(Path(video_path).resolve()),
        "-t", f"{duration:.3f}",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        str(Path(output_path).resolve())
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def create_i2v_frame_video(
    image_path: str,
    output_path: str,
    prompt: str,
    ar: str = "9:16",
    quality: str = "quality",
    duration_target: float = None,
    max_retries: int = 2,
) -> str:
    """
    用 CogVideoX I2V 将单张图片生成动画视频片段

    Args:
        image_path: 输入图片路径
        output_path: 输出视频路径
        prompt: I2V 动画描述提示词（英文）
        ar: 宽高比
        quality: speed / quality
        duration_target: 目标时长（裁切），None 保留原始时长
        max_retries: 最大重试次数
    """
    from ai_generator.video_generator import generate_from_image

    saved = None
    for attempt in range(1 + max_retries):
        try:
            saved = generate_from_image(
                image_path=image_path,
                prompt=prompt,
                output_path=output_path,
                ar=ar,
                quality=quality,
                with_audio=False,
                fps=30,
            )
            break
        except Exception as e:
            if attempt < max_retries:
                print(f"    I2V 重试 ({attempt + 1}/{max_retries}): {e}")
                continue
            raise RuntimeError(f"I2V 生成失败: {e}")

    if duration_target is not None and saved:
        actual = get_video_duration(saved)
        if actual > duration_target + 0.1:
            trimmed = Path(output_path).parent / f"{Path(output_path).stem}_trimmed.mp4"
            trim_video(saved, str(trimmed), duration_target)
            return str(trimmed)

    return output_path


def add_audio_to_video(video_path: str, audio_path: str, output_path: str, duration: float = None) -> str:
    """将音频叠加到视频上"""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(Path(video_path).resolve()),
        "-i", str(Path(audio_path).resolve()),
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "128k",
    ]
    if duration is not None:
        cmd.extend(["-t", f"{duration:.6f}"])
    else:
        cmd.append("-shortest")
    cmd.append(str(Path(output_path).resolve()))
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def add_subtitle_to_video(video_path: str, subtitle_path: str, output_path: str) -> str:
    """将字幕烧录到视频上"""
    sub_path_escaped = str(Path(subtitle_path).resolve()).replace("\\", "/").replace(":", "\\\\:")

    cmd = [
        "ffmpeg", "-y",
        "-i", str(Path(video_path).resolve()),
        "-vf", f"subtitles={sub_path_escaped}:force_style='FontSize=13,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=1,Alignment=2,MarginV=30'",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "copy",
        str(Path(output_path).resolve())
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return output_path


def concat_videos(video_paths: list[str], output_path: str) -> str:
    """拼接多个视频片段"""
    concat_file = Path(output_path).parent / "concat_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for vp in video_paths:
            p = Path(vp).resolve()
            f.write(f"file '{p}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_file.resolve()),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        str(Path(output_path).resolve())
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    concat_file.unlink(missing_ok=True)
    return output_path


def generate_srt(frames: list[dict], output_path: str) -> str:
    """
    根据分镜帧信息生成SRT字幕文件

    Args:
        frames: 带 audio_path 和 dialogue/narration 的帧列表
        output_path: SRT文件输出路径
    """
    subtitles = []
    current_time = 0.0

    for i, frame in enumerate(frames):
        text = frame.get("subtitle_text") or frame.get("dialogue") or frame.get("narration") or frame.get("text", "")
        if not text:
            duration = frame.get("duration", 3.0)
            current_time += duration
            continue

        if frame.get("audio_path"):
            try:
                duration = get_audio_duration(frame["audio_path"])
            except Exception:
                duration = max(len(text) * 0.15, 2.0)  # 按字数估算
        else:
            duration = max(len(text) * 0.15, 2.0)

        start = current_time
        end = current_time + duration

        h1, m1, s1, ms1 = int(start // 3600), int(start % 3600 // 60), int(start % 60), int((start % 1) * 1000)
        h2, m2, s2, ms2 = int(end // 3600), int(end % 3600 // 60), int(end % 60), int((end % 1) * 1000)

        subtitles.append(
            f"{i + 1}\n"
            f"{h1:02d}:{m1:02d}:{s1:02d},{ms1:03d} --> {h2:02d}:{m2:02d}:{s2:02d},{ms2:03d}\n"
            f"{text}\n"
        )
        current_time = end

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(subtitles))
    return output_path


def generate_srt_with_durations(frames: list[dict], durations: list[float], output_path: str) -> str:
    """根据实际视频时长生成SRT字幕（I2V模式用）"""
    subtitles = []
    current_time = 0.0
    sub_idx = 1

    for i, frame in enumerate(frames):
        text = frame.get("subtitle_text") or frame.get("dialogue") or frame.get("narration") or frame.get("text", "")
        dur = durations[i] if i < len(durations) else frame.get("duration", 3.0)

        if text:
            start = current_time
            end = current_time + dur

            h1, m1, s1, ms1 = int(start // 3600), int(start % 3600 // 60), int(start % 60), int((start % 1) * 1000)
            h2, m2, s2, ms2 = int(end // 3600), int(end % 3600 // 60), int(end % 60), int((end % 1) * 1000)

            subtitles.append(
                f"{sub_idx}\n"
                f"{h1:02d}:{m1:02d}:{s1:02d},{ms1:03d} --> {h2:02d}:{m2:02d}:{s2:02d},{ms2:03d}\n"
                f"{text}\n"
            )
            sub_idx += 1

        current_time += dur

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(subtitles))
    return output_path


def compose_episode(
    frames: list[dict],
    output_path: str,
    bgm_path: str = None,
    resolution: str = "1080x1920",
    zoom_effects: list[str] = None,
    mode: str = "zoompan",
    i2v_prompts: list[str] = None,
    i2v_quality: str = "quality",
    i2v_fallback: bool = True,
) -> str:
    """
    合成一集漫剧视频

    Args:
        frames: 分镜帧列表，每项含 image_path, audio_path, dialogue/narration
        output_path: 最终视频输出路径
        bgm_path: 背景音乐路径（可选）
        resolution: 视频分辨率
        zoom_effects: 每帧的运镜效果列表
        mode: "zoompan" 或 "i2v"
        i2v_prompts: I2V 模式下每帧的动画提示词
        i2v_quality: I2V 生成质量 speed/quality
        i2v_fallback: I2V 失败时是否回退 zoompan
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_dir = output_path.parent / "tmp_frames"
    tmp_dir.mkdir(exist_ok=True)

    if not zoom_effects:
        effects_cycle = ["slow_zoom_in", "slow_zoom_out", "pan_left", "pan_right", "slow_zoom_in"]
        zoom_effects = [effects_cycle[i % len(effects_cycle)] for i in range(len(frames))]

    # 从 resolution 推导 I2V 宽高比
    res_parts = resolution.split("x")
    if len(res_parts) == 2 and int(res_parts[1]) > int(res_parts[0]):
        ar = "9:16"  # 竖屏
    else:
        ar = "16:9"  # 横屏

    # Step 1: 每帧图片生成视频片段
    frame_videos = []
    actual_durations = []
    for i, frame in enumerate(frames):
        img = frame.get("image_path")
        if not img:
            # 无图片帧也要记录时长，保持索引对齐
            actual_durations.append(frame.get("duration", 3.0))
            continue

        duration = get_image_duration(frame)
        effect = zoom_effects[i] if i < len(zoom_effects) else "slow_zoom_in"
        frame_video = tmp_dir / f"frame_{i:03d}.mp4"

        if mode == "i2v" and i2v_prompts and i < len(i2v_prompts):
            # I2V 模式
            prompt = i2v_prompts[i]
            print(f"  合成帧 {i + 1}/{len(frames)}: I2V [{prompt[:50]}...]")
            try:
                create_i2v_frame_video(
                    image_path=img,
                    output_path=str(frame_video),
                    prompt=prompt,
                    ar=ar,
                    quality=i2v_quality,
                    duration_target=duration,
                )
            except Exception as e:
                if i2v_fallback:
                    print(f"    I2V 失败，回退 zoompan: {e}")
                    create_frame_video(img, str(frame_video), duration, resolution, effect)
                else:
                    raise
        else:
            # zoompan 模式
            print(f"  合成帧 {i + 1}/{len(frames)}: {duration:.1f}s [{effect}]")
            create_frame_video(img, str(frame_video), duration, resolution, effect)

        # 叠加配音
        if frame.get("audio_path"):
            frame_with_audio = tmp_dir / f"frame_{i:03d}_audio.mp4"
            if mode == "i2v":
                video_dur = get_video_duration(str(frame_video))
                final_duration = min(video_dur, duration)
            else:
                final_duration = round(duration * 30) / 30
            add_audio_to_video(str(frame_video), frame["audio_path"], str(frame_with_audio), duration=final_duration)
            actual_durations.append(final_duration)
            frame_videos.append(str(frame_with_audio))
        else:
            video_dur = get_video_duration(str(frame_video)) if mode == "i2v" else round(duration * 30) / 30
            actual_durations.append(video_dur)
            frame_videos.append(str(frame_video))

    if not frame_videos:
        raise ValueError("没有可用的帧视频")

    # Step 2: 拼接所有帧
    print("  拼接视频片段...")
    concat_output = tmp_dir / "concat_raw.mp4"
    concat_videos(frame_videos, str(concat_output))

    # Step 3: 叠加字幕（用实际时长生成 SRT）
    srt_path = tmp_dir / "subtitles.srt"
    generate_srt_with_durations(frames, actual_durations, str(srt_path))

    subbed_output = tmp_dir / "concat_subtitled.mp4"
    try:
        add_subtitle_to_video(str(concat_output), str(srt_path), str(subbed_output))
        final_source = str(subbed_output)
    except Exception:
        print("  字幕烧录失败，使用无字幕版本")
        final_source = str(concat_output)

    # Step 4: 叠加BGM（可选）
    if bgm_path and Path(bgm_path).exists():
        print("  叠加背景音乐...")
        cmd = [
            "ffmpeg", "-y",
            "-i", str(Path(final_source).resolve()),
            "-i", str(Path(bgm_path).resolve()),
            "-filter_complex", "[1:a]volume=0.15[bgm];[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            str(output_path.resolve())
        ]
        subprocess.run(cmd, capture_output=True, check=True)
    else:
        import shutil
        shutil.copy2(final_source, str(output_path))

    # 清理临时文件
    import shutil
    shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"  成片输出: {output_path}")
    return str(output_path)
