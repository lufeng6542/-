# -*- coding: utf-8 -*-
"""
海贼王剪辑项目 - 自动剪辑整合脚本
功能流程：
1. 调用素材
2. 将素材分成对应片段
3. 进行人声分离后去除BGM
4. 询问用户选择BGM和素材
5. 进行剪辑合成
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# 添加FFmpeg到PATH
import imageio_ffmpeg
FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

# 确保ffmpeg.exe存在
ffmpeg_link = os.path.join(ffmpeg_dir, "ffmpeg.exe")
if not os.path.exists(ffmpeg_link):
    shutil.copy(FFMPEG_PATH, ffmpeg_link)

import librosa
import numpy as np

# ============ 配置区域 ============
PROJECT_DIR = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_DIR / "素材"
SEGMENTS_DIR = PROJECT_DIR / "素材片段"
BGM_DIR = PROJECT_DIR / "BGM"
OUTPUT_DIR = PROJECT_DIR / "输出"
SEPARATED_DIR = PROJECT_DIR / "分离音频"
MODELS_DIR = PROJECT_DIR / "models"

# MDX23C模型路径
MDX23C_MODEL = MODELS_DIR / "mdx23c" / "MDX23C-8KFFT-InstVoc_HQ.ckpt"

# 视频参数
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920
FPS = 30
SEGMENT_DURATION = 4  # 默认片段时长


# ============ 工具函数 ============

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_header(title: str = "海贼王自动剪辑系统"):
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_step(step: int, total: int, title: str):
    print(f"\n{'='*60}")
    print(f"  [步骤 {step}/{total}] {title}")
    print("=" * 60)


def get_video_duration(video_path: str) -> float:
    """获取视频时长"""
    import re
    cmd = [FFMPEG_PATH, "-i", video_path, "-f", "null", "-"]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, errors='ignore')
        match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', result.stderr)
        if match:
            hours, minutes, seconds = int(match.group(1)), int(match.group(2)), float(match.group(3))
            return hours * 3600 + minutes * 60 + seconds
    except:
        pass
    return 0


def format_duration(seconds: float) -> str:
    """格式化时长"""
    mins, secs = divmod(int(seconds), 60)
    return f"{mins:02d}:{secs:02d}"


# ============ 步骤1: 扫描素材 ============

def scan_materials() -> List[Path]:
    """扫描素材目录"""
    video_extensions = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
    videos = []

    MATERIAL_DIR.mkdir(parents=True, exist_ok=True)

    for ext in video_extensions:
        videos.extend(MATERIAL_DIR.glob(f"*{ext}"))
        videos.extend(MATERIAL_DIR.glob(f"**/*{ext}"))

    return sorted(set(videos))


def display_materials(videos: List[Path]) -> None:
    """显示素材列表"""
    print("\n【可用素材】")
    print("-" * 60)
    for i, v in enumerate(videos, 1):
        size = v.stat().st_size / (1024 * 1024)
        duration = get_video_duration(str(v))
        print(f"  {i:2d}. {v.name}")
        print(f"       大小: {size:.1f} MB | 时长: {format_duration(duration)}")
    print("-" * 60)


# ============ 步骤2: 分割素材 ============

def split_video(video_path: Path, segment_duration: int = SEGMENT_DURATION) -> List[Path]:
    """分割视频为片段"""
    video_name = video_path.stem
    segment_dir = SEGMENTS_DIR / video_name
    segment_dir.mkdir(parents=True, exist_ok=True)

    duration = get_video_duration(str(video_path))
    if duration == 0:
        print(f"  [错误] 无法读取视频: {video_path.name}")
        return []

    num_segments = int(duration // segment_duration)
    segments = []

    print(f"\n  分割 {video_name} ({format_duration(duration)}) -> {num_segments} 个片段")

    for i in range(num_segments):
        start_time = i * segment_duration
        output_file = segment_dir / f"素材{i+1:03d}.mp4"

        # 跳过已存在的文件
        if output_file.exists():
            segments.append(output_file)
            print(f"    [跳过] 素材{i+1:03d} (已存在)")
            continue

        cmd = [
            FFMPEG_PATH, "-y",
            "-ss", str(start_time),
            "-i", str(video_path),
            "-t", str(segment_duration),
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac",
            str(output_file)
        ]

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode == 0:
            segments.append(output_file)
            print(f"    [完成] 素材{i+1:03d}")
        else:
            print(f"    [失败] 素材{i+1:03d}")

    return segments


def scan_segments() -> List[Path]:
    """扫描已分割的片段"""
    segments = []
    if SEGMENTS_DIR.exists():
        for subdir in SEGMENTS_DIR.iterdir():
            if subdir.is_dir():
                segments.extend(subdir.glob("*.mp4"))
    return sorted(segments)


def display_segments(segments: List[Path]) -> None:
    """显示片段列表"""
    print("\n【已分割片段】")
    print("-" * 60)

    # 按视频分组
    groups = {}
    for seg in segments:
        parent = seg.parent.name
        if parent not in groups:
            groups[parent] = []
        groups[parent].append(seg)

    for video_name, segs in groups.items():
        print(f"\n  📁 {video_name} ({len(segs)} 个片段)")
        for seg in segs[:5]:  # 只显示前5个
            print(f"      - {seg.name}")
        if len(segs) > 5:
            print(f"      ... 还有 {len(segs)-5} 个片段")

    print("-" * 60)


# ============ 步骤3: 人声分离 ============

def separate_vocals_mdx23c(input_audio: str, output_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """
    使用MDX23C模型进行人声分离

    Returns:
        (vocals_path, instrumental_path) 或 (None, None)
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n  使用模型: MDX23C-8KFFT-InstVoc_HQ")

    # 检查模型是否存在
    if not MDX23C_MODEL.exists():
        print(f"  [错误] 模型文件不存在: {MDX23C_MODEL}")
        print("  请确保模型已下载到正确位置")
        return None, None

    try:
        # 使用audio_separator库
        from audio_separator.separator import Separator

        separator = Separator(
            output_dir=str(output_dir),
            output_format="WAV",
            model_file_dir=str(MODELS_DIR)
        )

        # 加载MDX23C模型
        print("  正在加载模型...")
        separator.load_model(model_filename=str(MDX23C_MODEL))

        print("  正在分离人声...")
        primary, secondary = separator.separate(input_audio)

        vocals_path = Path(primary) if primary else None
        instrumental_path = Path(secondary) if secondary else None

        print(f"  [完成] 人声: {vocals_path}")
        print(f"  [完成] 伴奏: {instrumental_path}")

        return vocals_path, instrumental_path

    except ImportError:
        print("  [警告] audio_separator未安装，尝试使用demucs...")
        return separate_vocals_demucs(input_audio, output_dir)
    except Exception as e:
        print(f"  [错误] 分离失败: {e}")
        return None, None


def separate_vocals_demucs(input_audio: str, output_dir: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """使用demucs作为备选方案"""
    try:
        import torch
        from demucs import separate
        from demucs.pretrained import get_model

        print("  使用Demucs进行分离...")

        # 加载模型
        model = get_model('htdemucs')
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model.to(device)

        # 分离
        separator = separate.Separator(model=model, device=device)
        origins = separator.separate_audio_file(input_audio)

        # 保存结果
        vocals_path = output_dir / "vocals.wav"
        instrumental_path = output_dir / "no_vocals.wav"

        import soundfile as sf
        if 'vocals' in origins:
            sf.write(str(vocals_path), origins['vocals'].numpy().T, 44100)
        if 'no_vocals' in origins:
            sf.write(str(instrumental_path), origins['no_vocals'].numpy().T, 44100)

        return vocals_path, instrumental_path

    except Exception as e:
        print(f"  [错误] Demucs分离失败: {e}")
        return None, None


def extract_audio_from_video(video_path: Path, output_audio: Path) -> bool:
    """从视频中提取音频"""
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "44100",
        "-ac", "2",
        str(output_audio)
    ]

    result = subprocess.run(cmd, capture_output=True)
    return result.returncode == 0


def process_segments_vocal_separation(segments: List[Path]) -> Dict[str, Path]:
    """批量处理片段的人声分离"""
    separated = {}

    print("\n【人声分离处理】")
    print("-" * 60)

    for i, seg in enumerate(segments, 1):
        print(f"\n[{i}/{len(segments)}] 处理: {seg.name}")

        # 输出目录
        output_subdir = SEPARATED_DIR / seg.parent.name / seg.stem
        output_subdir.mkdir(parents=True, exist_ok=True)

        # 提取音频
        audio_path = output_subdir / "audio.wav"
        if not audio_path.exists():
            print("  提取音频...")
            if not extract_audio_from_video(seg, audio_path):
                print("  [失败] 音频提取失败")
                continue

        # 检查是否已分离
        vocals_path = output_subdir / "vocals.wav"
        instrumental_path = output_subdir / "instrumental.wav"

        if vocals_path.exists() and instrumental_path.exists():
            print("  [跳过] 已存在分离结果")
            separated[str(seg)] = {"vocals": vocals_path, "instrumental": instrumental_path}
            continue

        # 人声分离
        v, inst = separate_vocals_mdx23c(str(audio_path), output_subdir)

        if v and inst:
            # 重命名为标准名称
            if v != vocals_path:
                shutil.move(str(v), str(vocals_path))
            if inst != instrumental_path:
                shutil.move(str(inst), str(instrumental_path))

            separated[str(seg)] = {"vocals": vocals_path, "instrumental": instrumental_path}

    return separated


# ============ 步骤4: 选择BGM和素材 ============

def scan_bgm() -> List[Path]:
    """扫描BGM文件"""
    audio_extensions = ['.mp3', '.wav', '.m4a', '.flac', '.aac']
    bgm_files = []

    BGM_DIR.mkdir(parents=True, exist_ok=True)

    for ext in audio_extensions:
        bgm_files.extend(BGM_DIR.glob(f"*{ext}"))

    return sorted(bgm_files)


def display_bgm(bgm_files: List[Path]) -> None:
    """显示BGM列表"""
    print("\n【可用BGM】")
    print("-" * 60)
    for i, bgm in enumerate(bgm_files, 1):
        size = bgm.stat().st_size / (1024 * 1024)
        print(f"  {i:2d}. {bgm.name} ({size:.1f} MB)")
    print("-" * 60)


def select_segments_interactive(segments: List[Path]) -> List[Path]:
    """交互式选择片段"""
    print("\n【选择素材片段】")
    print("-" * 60)
    print("  输入片段编号，用逗号分隔 (如: 1,3,5,7)")
    print("  输入 'all' 选择全部")
    print("  输入 'q' 跳过")
    print("-" * 60)

    # 显示片段
    for i, seg in enumerate(segments, 1):
        print(f"  {i:3d}. {seg.parent.name}/{seg.name}")

    choice = input("\n请选择: ").strip().lower()

    if choice == 'q':
        return []
    if choice == 'all':
        return segments

    try:
        indices = [int(x.strip()) - 1 for x in choice.split(',')]
        selected = [segments[i] for i in indices if 0 <= i < len(segments)]
        return selected
    except:
        print("  [错误] 无效输入")
        return []


def select_bgm_interactive(bgm_files: List[Path]) -> Optional[Path]:
    """交互式选择BGM"""
    if not bgm_files:
        print("  [警告] 没有可用的BGM文件")
        return None

    display_bgm(bgm_files)

    choice = input("\n选择BGM编号 (或按回车使用第一个): ").strip()

    if not choice:
        return bgm_files[0]

    try:
        index = int(choice) - 1
        if 0 <= index < len(bgm_files):
            return bgm_files[index]
    except:
        pass

    return bgm_files[0]


# ============ 步骤5: 剪辑合成 ============

def get_beat_times(bgm_path: str) -> List[float]:
    """分析BGM节拍"""
    print(f"  分析BGM节拍: {Path(bgm_path).name}")

    y, sr = librosa.load(bgm_path)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    if hasattr(tempo, '__iter__'):
        tempo = float(tempo[0]) if len(tempo) > 0 else 120.0
    else:
        tempo = float(tempo)

    print(f"  检测到BPM: {tempo:.1f}")

    return beat_times.tolist()


def edit_video(
    segments: List[Path],
    bgm_path: Path,
    use_vocals: bool = False,
    separated_audio: Dict = None,
    output_name: str = "最终合成"
) -> Optional[Path]:
    """
    剪辑合成视频

    Args:
        segments: 选择的片段列表
        bgm_path: BGM文件路径
        use_vocals: 是否保留原人声
        separated_audio: 人声分离结果
        output_name: 输出文件名
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print(f"\n【开始剪辑合成】")
    print(f"  片段数量: {len(segments)}")
    print(f"  BGM: {bgm_path.name}")
    print(f"  保留人声: {'是' if use_vocals else '否'}")

    # 分析BGM节拍
    beat_times = get_beat_times(str(bgm_path))

    # 生成concat文件
    concat_file = PROJECT_DIR / "脚本" / "concat_temp.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"file '{seg}'\n")

    # 输出路径
    output_path = OUTPUT_DIR / f"{output_name}.mp4"

    # 构建FFmpeg命令
    if use_vocals and separated_audio:
        # 混合原人声和新BGM
        # 先合成视频，再混合音频
        temp_video = OUTPUT_DIR / "temp_no_audio.mp4"

        cmd1 = [
            FFMPEG_PATH, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-an",
            str(temp_video)
        ]

        print("  步骤1: 合成视频轨道...")
        result = subprocess.run(cmd1, capture_output=True)
        if result.returncode != 0:
            print("  [失败] 视频合成失败")
            return None

        # 混合音频
        print("  步骤2: 混合音频...")
        vocals_files = []
        for seg in segments:
            seg_key = str(seg)
            if seg_key in separated_audio:
                vocals_files.append(separated_audio[seg_key]["vocals"])

        # 创建人声concat文件
        vocals_concat = PROJECT_DIR / "脚本" / "vocals_concat.txt"
        with open(vocals_concat, "w", encoding="utf-8") as f:
            for vf in vocals_files:
                f.write(f"file '{vf}'\n")

        # 混合人声和BGM
        cmd2 = [
            FFMPEG_PATH, "-y",
            "-i", str(temp_video),
            "-f", "concat", "-safe", "0", "-i", str(vocals_concat),
            "-i", str(bgm_path),
            "-filter_complex", "[1:a][2:a]amix=inputs=2:duration=longest:dropout_transition=0[aout]",
            "-map", "0:v", "-map", "[aout]",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            str(output_path)
        ]

        result = subprocess.run(cmd2, capture_output=True)
        temp_video.unlink(missing_ok=True)

        if result.returncode != 0:
            print("  [失败] 音频混合失败")
            return None

    else:
        # 简单模式：直接替换BGM
        cmd = [
            FFMPEG_PATH, "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_file),
            "-i", str(bgm_path),
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2",
            "-c:v", "libx264", "-preset", "fast", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-map", "0:v", "-map", "1:a",
            "-shortest",
            str(output_path)
        ]

        print("  正在合成...")
        result = subprocess.run(cmd, capture_output=True)

        if result.returncode != 0:
            print("  [失败] 合成失败")
            return None

    # 清理临时文件
    concat_file.unlink(missing_ok=True)

    size = output_path.stat().st_size / (1024 * 1024)
    print(f"\n  [完成] 输出文件: {output_path}")
    print(f"  文件大小: {size:.1f} MB")

    return output_path


# ============ 主流程 ============

def main():
    clear_screen()
    print_header("海贼王自动剪辑系统 - MDX23C人声分离版")

    # 检查模型
    print(f"\n检查MDX23C模型: ", end="")
    if MDX23C_MODEL.exists():
        print(f"✓ 已就绪 ({MDX23C_MODEL.stat().st_size / (1024*1024):.0f} MB)")
    else:
        print(f"✗ 未找到")
        print(f"  模型路径: {MDX23C_MODEL}")

    # ===== 步骤1: 扫描素材 =====
    print_step(1, 5, "扫描素材")
    videos = scan_materials()

    if not videos:
        print("\n  [提示] 素材文件夹为空")
        print(f"  请将视频素材放入: {MATERIAL_DIR}")
        input("\n  按回车键退出...")
        return

    display_materials(videos)

    # ===== 步骤2: 分割素材 =====
    print_step(2, 5, "分割素材")

    # 检查是否已有分割片段
    existing_segments = scan_segments()

    if existing_segments:
        print(f"\n  已有 {len(existing_segments)} 个分割片段")
        choice = input("  是否重新分割? (y/N): ").strip().lower()
        re_split = choice == 'y'
    else:
        re_split = True

    segments = existing_segments

    if re_split:
        duration = input(f"  输入片段时长(秒, 默认{SEGMENT_DURATION}): ").strip()
        segment_duration = int(duration) if duration.isdigit() else SEGMENT_DURATION

        for video in videos:
            new_segments = split_video(video, segment_duration)
            segments.extend(new_segments)

        segments = sorted(set(segments))

    display_segments(segments)

    # ===== 步骤3: 人声分离 =====
    print_step(3, 5, "人声分离 (可选)")

    do_separation = input("  是否进行人声分离? (y/N): ").strip().lower() == 'y'
    separated_audio = {}

    if do_separation:
        # 选择要处理的片段
        segments_to_process = select_segments_interactive(segments)
        if segments_to_process:
            separated_audio = process_segments_vocal_separation(segments_to_process)
    else:
        print("  跳过人声分离")

    # ===== 步骤4: 选择BGM和素材 =====
    print_step(4, 5, "选择BGM和素材")

    # 选择BGM
    bgm_files = scan_bgm()
    selected_bgm = select_bgm_interactive(bgm_files)

    if not selected_bgm:
        print("  [错误] 没有可用的BGM")
        input("\n  按回车键退出...")
        return

    print(f"\n  已选择BGM: {selected_bgm.name}")

    # 选择片段
    selected_segments = select_segments_interactive(segments)

    if not selected_segments:
        print("  [错误] 没有选择任何片段")
        input("\n  按回车键退出...")
        return

    print(f"\n  已选择 {len(selected_segments)} 个片段")

    # 是否保留人声
    use_vocals = False
    if separated_audio and do_separation:
        use_vocals = input("\n  是否保留原人声? (Y/n): ").strip().lower() != 'n'

    # ===== 步骤5: 剪辑合成 =====
    print_step(5, 5, "剪辑合成")

    output_name = input(f"  输出文件名 (默认: 最终合成): ").strip() or "最终合成"

    result = edit_video(
        segments=selected_segments,
        bgm_path=selected_bgm,
        use_vocals=use_vocals,
        separated_audio=separated_audio,
        output_name=output_name
    )

    # 完成
    print("\n" + "=" * 60)
    if result:
        print("  🎉 剪辑完成!")
        print(f"  输出文件: {result}")

        # 询问是否打开文件夹
        open_folder = input("\n  打开输出文件夹? (Y/n): ").strip().lower() != 'n'
        if open_folder:
            if os.name == 'nt':
                os.system(f'explorer "{OUTPUT_DIR}"')
    else:
        print("  ❌ 剪辑失败")

    print("=" * 60)
    input("\n  按回车键退出...")


if __name__ == "__main__":
    main()
