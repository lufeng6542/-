#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智谱AI基础客户端
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
    """Ctrl+C 安全中断"""
    if _interrupted_tasks:
        print(f"\n\n[中断] 任务仍在服务端运行，可稍后查询结果：")
        for tid in _interrupted_tasks:
            print(f"  任务ID: {tid}")
            print(f"  查询命令: python cli.py task-status {tid}")
    else:
        print("\n\n[中断] 已取消")
    sys.exit(0)


signal.signal(signal.SIGINT, _sigint_handler)


# API错误码 → 中文翻译
_ERROR_MESSAGES = {
    400: "请求参数有误，请检查输入",
    401: "API密钥无效或已过期，请检查 ZHIPU_API_KEY",
    403: "无权访问该模型，请检查账户权限和余额",
    404: "接口不存在，请检查API地址",
    429: "请求过于频繁，请稍后再试",
    500: "智谱服务器内部错误，请稍后重试",
    502: "智谱服务暂时不可用，请稍后重试",
    503: "智谱服务维护中，请稍后重试",
}


def translate_error(status_code, response_text):
    """将API错误翻译为中文"""
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
    """简单进度条（ASCII兼容）"""
    ratio = min(current / total, 1.0) if total > 0 else 0
    filled = int(width * ratio)
    bar = "#" * filled + "-" * (width - filled)
    return f"[{bar}] {ratio:.0%}"


class ZhipuClient:
    """智谱AI API基础客户端"""

    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_IMAGE_MODEL = "cogview-4"
    DEFAULT_VIDEO_MODEL = "cogvideox-3"
    DEFAULT_VISION_MODEL = "glm-4.6v-flash"
    DEFAULT_CHAT_MODEL = "glm-4-flash"

    def __init__(self, api_key=None, base_url=None):
        self.api_key = api_key or self._load_api_key()
        self.base_url = (base_url or os.environ.get("ZHIPU_BASE_URL") or self.DEFAULT_BASE_URL).rstrip("/")

        if not self.api_key:
            raise ValueError(
                "ZHIPU_API_KEY 未设置。\n"
                "请编辑 ~/.baoyu-skills/.env 添加: ZHIPU_API_KEY=你的密钥"
            )

    @staticmethod
    def _load_api_key():
        """从环境变量或.env文件加载API Key"""
        key = os.environ.get("ZHIPU_API_KEY")
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
                        if k.strip() == "ZHIPU_API_KEY":
                            return v.strip().strip("\"'")
        return None

    def _headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

    def _post(self, endpoint, json_body, timeout=60):
        """发送POST请求，自动处理错误"""
        url = f"{self.base_url}{endpoint}"
        resp = requests.post(url, headers=self._headers(), json=json_body, timeout=timeout)
        if resp.status_code != 200:
            raise RuntimeError(translate_error(resp.status_code, resp.text))
        return resp

    def _get(self, endpoint, timeout=30):
        """发送GET请求，自动处理错误"""
        url = f"{self.base_url}{endpoint}"
        resp = requests.get(url, headers=self._headers(), timeout=timeout)
        if resp.status_code != 200:
            raise RuntimeError(translate_error(resp.status_code, resp.text))
        return resp

    def _download_file(self, url, output_path, chunk_size=65536, timeout=120):
        """下载文件并保存（带进度条）"""
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
