#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI漫剧Pipeline - 一键从剧本到成片

用法:
    python -m comic_drama.pipeline --story "故事大纲或小说片段" --output output/ep01.mp4
    python -m comic_drama.pipeline --script script.json --output output/ep01.mp4
"""

import argparse
import json
import sys
import time
from pathlib import Path

# 添加项目根目录到path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from ai_generator.image_generator import generate as generate_image
from comic_drama.tts_engine import generate_scene_audio
from comic_drama.composer import compose_episode


# 默认漫剧风格prompt前缀
COMIC_STYLE_PROMPT = (
    "Chinese comic manhua style, dramatic lighting, cinematic composition, "
    "detailed linework, vibrant colors, vertical format manga panel, "
)

# 角色描述模板（用于保持一致性）
CHARACTER_TEMPLATES = {
    "男主": "a handsome young Chinese man in his mid-20s, short black hair, sharp eyes, wearing {outfit}",
    "女主": "a beautiful young Chinese woman in her early 20s, long black hair, gentle eyes, wearing {outfit}",
    "反派": "a middle-aged Chinese man, stern face, wearing an expensive suit, intimidating presence",
    "配角男": "a friendly Chinese man in his 30s, casual clothes",
    "配角女": "a sweet Chinese woman in her 20s, wearing {outfit}",
}

OUTFIT_MAP = {
    "日常": "casual t-shirt and jeans",
    "正装": "formal black suit and tie",
    "奢华": "designer luxury outfit, gold watch",
    "休闲": "smart casual outfit",
    "礼服": "elegant evening dress",
    "校服": "school uniform",
}


def build_prompt(scene_desc: str, characters: list[str] = None,
                 style: str = "comic", mood: str = "dramatic") -> str:
    """构建生图prompt"""
    parts = [COMIC_STYLE_PROMPT]

    if mood:
        mood_map = {
            "dramatic": "dramatic tension, intense atmosphere",
            "romantic": "soft romantic lighting, warm atmosphere",
            "dark": "dark moody atmosphere, low key lighting",
            "bright": "bright optimistic atmosphere, warm sunlight",
            "tense": "suspenseful atmosphere, sharp contrasts",
        }
        parts.append(mood_map.get(mood, mood))

    if characters:
        for char in characters:
            if char in CHARACTER_TEMPLATES:
                parts.append(CHARACTER_TEMPLATES[char].format(outfit="casual outfit"))

    parts.append(scene_desc)
    return ", ".join(parts)


# --- I2V prompt 构建 ---

MOOD_I2V_MAP = {
    "dramatic": "dramatic tension building, shadows deepening, cinematic lighting shift",
    "tense": "suspenseful atmosphere, flickering light, subtle tension in the air",
    "dark": "dark moody atmosphere, dim lighting slowly shifting, oppressive silence",
    "romantic": "soft warm glow, romantic haze, gentle swaying movement",
    "bright": "bright sunlight streaming, warm breeze, peaceful ambiance",
}

I2V_SHOT_TEMPLATES = {
    "close_up": "Subtle camera movement, {action}, soft lighting shift, cinematic depth of field",
    "wide_shot": "Slow cinematic dolly, {action}, atmospheric fog and light rays, epic scale",
    "action": "Dynamic camera tracking, {action}, motion blur on fast elements, dramatic timing",
    "emotion": "Gentle push-in on face, {action}, eyes glistening with emotion, breathing visible",
    "atmosphere": "Ambient scene, {action}, dust particles floating, light slowly shifting",
}


def _infer_shot_type(scene: str) -> str:
    scene_lower = scene.lower()
    if any(w in scene_lower for w in ["close-up", "extreme close", "face", "eyes", "hand"]):
        return "close_up"
    if any(w in scene_lower for w in ["wide", "panoramic", "doorway", "walking", "street", "city"]):
        return "wide_shot"
    if any(w in scene_lower for w in ["gripping", "pushing", "lifting", "running", "strapping", "punch", "fight"]):
        return "action"
    if any(w in scene_lower for w in ["tears", "crying", "grief", "silent", "kneeling", "shock"]):
        return "emotion"
    return "atmosphere"


def _extract_action(scene: str) -> str:
    action_keywords = [
        "pressing", "pushing", "holding", "reaching", "turning",
        "walking", "lifting", "strapping", "kneeling", "wiping",
        "gripping", "carrying", "peeking", "looking", "dissolving",
        "spreading", "streaming", "clutching", "checking", "staring",
    ]
    clauses = [c.strip() for c in scene.split(",")]
    found = [c for c in clauses if any(kw in c.lower() for kw in action_keywords)]
    return "; ".join(found[:2]) if found else scene[:120]


def build_i2v_prompt(frame: dict) -> str:
    """从分镜 frame 字段构建 I2V 动画提示词"""
    if frame.get("i2v_prompt"):
        return frame["i2v_prompt"]

    scene = frame.get("scene", "")
    mood = frame.get("mood", "dramatic")

    mood_atmosphere = MOOD_I2V_MAP.get(mood, "cinematic atmosphere")
    shot_type = _infer_shot_type(scene)
    action = _extract_action(scene)

    template = I2V_SHOT_TEMPLATES.get(shot_type, I2V_SHOT_TEMPLATES["atmosphere"])
    prompt = template.format(action=action)

    parts = [prompt, mood_atmosphere]

    if frame.get("dialogue"):
        parts.append("character's lips subtly move as if speaking softly")

    parts.append("smooth continuous motion, no scene cuts, maintaining original art style")

    return ", ".join(parts)


def generate_images(frames: list[dict], output_dir: str,
                    ar: str = "9:16", size: str = None) -> list[dict]:
    """为每帧生成图片"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    total = len(frames)
    for i, frame in enumerate(frames):
        if frame.get("image_path") and Path(frame["image_path"]).exists():
            print(f"  [{i + 1}/{total}] 图片已存在，跳过")
            continue

        prompt = frame.get("prompt") or build_prompt(
            frame.get("scene", ""),
            frame.get("characters"),
            mood=frame.get("mood", "dramatic")
        )
        frame["prompt"] = prompt

        img_path = output_dir / f"frame_{i:03d}.png"
        print(f"  [{i + 1}/{total}] 生成图片: {frame.get('scene', '')[:40]}...")

        t0 = time.time()
        try:
            generate_image(
                prompt=prompt,
                output_path=str(img_path),
                ar=ar,
                size=size,
            )
            frame["image_path"] = str(img_path)
            print(f"    完成 ({time.time() - t0:.1f}s)")
        except Exception as e:
            print(f"    失败: {e}")
            frame["image_path"] = None

    return frames


def run_pipeline(
    story: str = None,
    script_path: str = None,
    output_path: str = None,
    ar: str = "9:16",
    bgm_path: str = None,
    resolution: str = "1080x1920",
    skip_gen_images: bool = False,
    mode: str = "zoompan",
    i2v_quality: str = "quality",
    i2v_fallback: bool = True,
):
    """
    运行完整漫剧pipeline

    Args:
        story: 故事文本（自动生成分镜）
        script_path: 预写好的分镜JSON文件
        output_path: 输出视频路径
        ar: 图片宽高比
        bgm_path: BGM路径
        resolution: 视频分辨率
        skip_gen_images: 跳过生图步骤（用于调试）
        mode: "zoompan" 或 "i2v"
        i2v_quality: I2V 生成质量 speed/quality
        i2v_fallback: I2V 失败时是否回退 zoompan
    """
    output_path = Path(output_path or ROOT / "漫剧输出" / "episode.mp4")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    work_dir = output_path.parent / "work"
    work_dir.mkdir(exist_ok=True)

    # Step 1: 加载或生成分镜
    if script_path:
        print("=" * 50)
        print("Step 1: 加载分镜脚本")
        print("=" * 50)
        with open(script_path, "r", encoding="utf-8") as f:
            frames = json.load(f)
    elif story:
        print("=" * 50)
        print("Step 1: 故事文本已收到，请先准备分镜脚本")
        print("  提示: 可以让AI帮你将故事拆成分镜JSON")
        print("  格式: [{scene, dialogue, role, characters, mood}, ...]")
        print("=" * 50)
        print(f"\n故事: {story[:100]}...\n")
        print("请将分镜JSON保存到文件后用 --script 参数指定")
        return
    else:
        print("错误: 请提供 --story 或 --script 参数")
        return

    print(f"  共 {len(frames)} 帧分镜\n")

    # Step 2: 生成图片
    if not skip_gen_images:
        print("=" * 50)
        print("Step 2: 生成分镜图片")
        print("=" * 50)
        frames = generate_images(frames, work_dir / "images", ar=ar)
        print()

    # Step 3: 生成配音
    print("=" * 50)
    print("Step 3: 生成配音")
    print("=" * 50)
    frames = generate_scene_audio(frames, work_dir / "audio")
    print()

    # Step 3.5: 构建 I2V prompts（仅 I2V 模式）
    i2v_prompts = None
    if mode == "i2v":
        print("=" * 50)
        print("Step 3.5: 构建 I2V 动画提示词")
        print("=" * 50)
        i2v_prompts = []
        for i, frame in enumerate(frames):
            prompt = build_i2v_prompt(frame)
            i2v_prompts.append(prompt)
            print(f"  帧 {i + 1}: {prompt[:80]}...")
        print()

    # Step 4: 合成视频
    print("=" * 50)
    print("Step 4: 合成视频")
    print("=" * 50)
    compose_episode(
        frames=frames,
        output_path=str(output_path),
        bgm_path=bgm_path,
        resolution=resolution,
        mode=mode,
        i2v_prompts=i2v_prompts,
        i2v_quality=i2v_quality,
        i2v_fallback=i2v_fallback,
    )

    # 保存分镜数据
    script_save = output_path.parent / (output_path.stem + "_script.json")
    with open(script_save, "w", encoding="utf-8") as f:
        json.dump(frames, f, ensure_ascii=False, indent=2)

    print(f"\n{'=' * 50}")
    print(f"完成！成片: {output_path}")
    print(f"分镜数据: {script_save}")
    print(f"{'=' * 50}")


def main():
    parser = argparse.ArgumentParser(description="AI漫剧Pipeline - 从剧本到成片")
    parser.add_argument("--story", type=str, help="故事文本")
    parser.add_argument("--script", type=str, help="分镜JSON文件路径")
    parser.add_argument("--output", "-o", type=str, help="输出视频路径")
    parser.add_argument("--ar", type=str, default="9:16", help="图片宽高比 (默认9:16竖屏)")
    parser.add_argument("--bgm", type=str, help="背景音乐路径")
    parser.add_argument("--resolution", type=str, default="1080x1920", help="视频分辨率")
    parser.add_argument("--skip-images", action="store_true", help="跳过生图步骤")
    parser.add_argument("--mode", type=str, default="zoompan",
                        choices=["zoompan", "i2v"],
                        help="视频生成模式: zoompan(运镜模拟) 或 i2v(图生视频动画)")
    parser.add_argument("--i2v-quality", type=str, default="quality",
                        choices=["speed", "quality"],
                        help="I2V 生成质量 (默认 quality)")
    parser.add_argument("--no-i2v-fallback", action="store_true",
                        help="I2V 失败时不回退到 zoompan")

    args = parser.parse_args()
    run_pipeline(
        story=args.story,
        script_path=args.script,
        output_path=args.output,
        ar=args.ar,
        bgm_path=args.bgm,
        resolution=args.resolution,
        skip_gen_images=args.skip_images,
        mode=args.mode,
        i2v_quality=args.i2v_quality,
        i2v_fallback=not args.no_i2v_fallback,
    )


if __name__ == "__main__":
    main()
