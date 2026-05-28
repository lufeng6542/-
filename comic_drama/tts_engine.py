#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""TTS配音模块 - 基于edge-tts，支持角色音色差异化"""

import asyncio
import edge_tts
from pathlib import Path

# 角色语音配置：voice + rate + pitch + volume + display_name
ROLE_CONFIG = {
    "陈默": {
        "voice": "zh-CN-YunjianNeural",      # 有力深沉，用快语速体现紧迫
        "rate": "+5%",                        # 略快，紧急但不慌
        "display": "陈默",
        "style": "低沉有力，前急诊医生",
    },
    "苏晴": {
        "voice": "zh-CN-XiaoxiaoNeural",     # 温暖柔美
        "rate": "-5%",                        # 略慢，虚弱但清醒
        "display": "苏晴",
        "style": "温暖虚弱，临终告别",
    },
    "陈念": {
        "voice": "zh-CN-XiaoyiNeural",       # 活泼卡通风
        "rate": "+20%",                       # 快，童声感
        "display": "念念",
        "style": "童声，简短，过早点懂事",
    },
    "旁白": {
        "voice": "zh-CN-YunxiNeural",        # 阳光磁性
        "rate": "-5%",
        "display": None,                       # 旁白不显示角色名
        "style": "磁性旁白，有距离感",
    },
    "反派": {
        "voice": "zh-CN-YunjianNeural",      # 激情有力
        "rate": "-5%",
        "display": None,
        "style": "压迫感强",
    },
    "配角男": {
        "voice": "zh-CN-YunyangNeural",
        "rate": "+0%",
        "display": None,
        "style": "普通男性",
    },
    "配角女": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "+0%",
        "display": None,
        "style": "普通女性",
    },
    "男主": {
        "voice": "zh-CN-YunyangNeural",
        "rate": "-15%",
        "display": None,
        "style": "默认男主配置",
    },
    "女主": {
        "voice": "zh-CN-XiaoxiaoNeural",
        "rate": "-10%",
        "display": None,
        "style": "默认女主配置",
    },
}

# 兼容旧代码
VOICE_MAP = {k: v["voice"] for k, v in ROLE_CONFIG.items()}
RATE_MAP = {k: v["rate"] for k, v in ROLE_CONFIG.items()}


async def _generate_single(text: str, output_path: str, voice: str, rate: str = "+0%"):
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(output_path)


def generate_tts(
    text: str,
    output_path: str,
    role: str = "旁白",
    voice: str = None,
    rate: str = None,
) -> str:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    config = ROLE_CONFIG.get(role, ROLE_CONFIG["旁白"])
    v = voice or config["voice"]
    r = rate or config["rate"]

    asyncio.run(_generate_single(text, str(output_path), v, r))
    return str(output_path)


def get_role_display(role: str) -> str:
    """获取角色显示名（用于字幕前缀）"""
    config = ROLE_CONFIG.get(role, {})
    return config.get("display") or ""


def generate_scene_audio(frames: list[dict], output_dir: str) -> list[dict]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for i, frame in enumerate(frames):
        text = frame.get("dialogue") or frame.get("text") or frame.get("narration", "")
        if not text:
            frame["audio_path"] = None
            continue

        role = frame.get("role", "旁白")
        audio_path = output_dir / f"frame_{i:03d}_{role}.mp3"

        for attempt in range(3):
            try:
                generate_tts(text, str(audio_path), role=role)
                frame["audio_path"] = str(audio_path)
                break
            except Exception:
                if attempt == 2:
                    frame["audio_path"] = None

        # 加角色显示名到字幕
        display = get_role_display(role)
        if display:
            frame["subtitle_text"] = f"【{display}】{text}"
        else:
            frame["subtitle_text"] = text

    return frames


def list_voices():
    return {k: {"voice": v["voice"], "rate": v["rate"], "style": v["style"]} for k, v in ROLE_CONFIG.items()}
