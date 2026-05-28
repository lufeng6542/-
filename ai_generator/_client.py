#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Kimi AI 基础客户端 (原智谱 → 已迁移到 Kimi)
HTTP请求、API Key管理、错误翻译、进度条、信号处理
"""

import os
import sys
import json
import time
import signal
from pathlib import Path

import requests


# Ctrl+C中断时记录的任务ID，供后续查询
_interrupted_tasks = []


def _sigint_handler(signum, frame):
    if _interrupted_tasks:
        print(f"\n\n[中断] 任务仍在服务端运行，可稍后查询结果：")
        for tid in _interrupted_tasks:
            print(f"  任务ID: {tid}")
            print(f"  查询命令: python cli.py task-status {tid}")
    else:
        print("\n\n[中断] 已取消")
    sys.exit(0)


signal.signal(signal.SIGINT, _sigint_handler)


_ERROR_MESSAGES = {
    400: "请求参数有误，请检查输入",
    401: "API密钥无效或已过期，请检查 KIMI_API_KEY",
    403: "无权访问该模型，请检查账户权限和余额",
    404: "接口不存在，请检查API地址",
    429: "请求过于频繁，请稍后再试",
    500: "Kimi 服务器内部错误，请稍后重试",
    502: "Kimi 服务暂时不可用，请稍后重试",
    503: "Kimi 服务维护中，请稍后重试",
}


def translate_error(status_code, response_text):
    msg = _ERROR_MESSAGES.get(status_code)
    if msg:
        return f"[{status_code}] {msg}"
    try:
        data = json.loads(response_text)
        err = data.get("error", {})
        if isinstance(err, dict):
            detail = err.get("message", "")
            code = err.get("code", "")
            if detail:
                return f"[{status_code}] {detail}"
            if code:
                return f"[{status_code}] {code}"
    except (json.JSONDecodeError, AttributeError):
        pass
    return f"[{status_code}] {response_text[:200]}"


def progress_bar(current, total, width=30):
    ratio = min(current / total, 1.0) if total > 0 else 0
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {ratio:.0%}"


class KimiClient:
    """Kimi AI API 基础客户端"""

    DEFAULT_BASE_URL = "https://api.moonshot.cn/v1"
    DEFAULT_VISION_MODEL = "moonshot-v1-8k-vision-preview"
    DEFAULT_CHAT_MODEL = "moonshot-v1-8k"

    # ==== 以下模型仅在智谱(GLM)API下可用，已弃用 ====
    DEFAULT_IMAGE_MODEL = None   # Kimi 不支持图片生成
    DEFAULT_VIDEO_MODEL = None   # Kimi 不支持视频生成

    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or self._load_api_key()
        # Auto-detect ARK base URL when using ARK_API_KEY
        if not base_url and (os.environ.get("ARK_API_KEY") or
                             (self.api_key and self.api_key.startswith("ark-"))):
            default = "https://ark.cn-beijing.volces.com/api/v3"
        else:
            default = self.DEFAULT_BASE_URL
        self.base_url = (base_url or os.environ.get("KIMI_BASE_URL") or
                         os.environ.get("DASHSCOPE_BASE_URL") or
                         default).rstrip("/")

        if not self.api_key:
            raise ValueError(
                "KIMI_API_KEY 未设置。\n"
                "请设置环境变量: KIMI_API_KEY=你的密钥\n"
                "或编辑 ~/.baoyu-skills/.env 添加: KIMI_API_KEY=你的密钥"
            )

    @staticmethod
    def _load_api_key():
        # ARK_API_KEY (火山引擎)
        key = os.environ.get("ARK_API_KEY")
        if key:
            return key
        # KIMI_API_KEY
        key = os.environ.get("KIMI_API_KEY")
        if key:
            return key
        # DASHSCOPE_API_KEY
        key = os.environ.get("DASHSCOPE_API_KEY")
        if key:
            return key

        env_paths = [
            Path.cwd() / ".baoyu-skills" / ".env",
            Path.home() / ".baoyu-skills" / ".env",
        ]
        for p in env_paths:
            if p.exists():
                for line in p.read_text("utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        if k in ("ARK_API_KEY", "KIMI_API_KEY", "DASHSCOPE_API_KEY"):
                            return v.strip().strip("\"'")
        return None

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _post(self, endpoint, json_body, timeout=60):
        url = f"{self.base_url}{endpoint}"
        resp = requests.post(url, headers=self._headers(), json=json_body, timeout=timeout)
        if resp.status_code != 200:
            raise RuntimeError(translate_error(resp.status_code, resp.text))
        return resp

    def _get(self, endpoint, timeout=30):
        url = f"{self.base_url}{endpoint}"
        resp = requests.get(url, headers=self._headers(), timeout=timeout)
        if resp.status_code != 200:
            raise RuntimeError(translate_error(resp.status_code, resp.text))
        return resp

    def _download_file(self, url, output_path, chunk_size=65536, timeout=120):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        resp = requests.get(url, timeout=timeout, stream=True)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    sys.stdout.write(f"\r  {progress_bar(downloaded, total)} {downloaded / (1024*1024):.1f}/{total / (1024*1024):.1f}MB")
                    sys.stdout.flush()

        if total > 0:
            print()
        return str(output_path)


# 向后兼容别名
ZhipuClient = KimiClient
