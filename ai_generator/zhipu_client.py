#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智谱AI API客户端
统一管理图片生成、视频生成、视觉分析接口
带进度反馈、Ctrl+C安全中断、重试退避
"""

import os
import sys
import json
import time
import re
import signal
import base64
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


def _progress_bar(current, total, width=30):
    """简单进度条"""
    ratio = min(current / total, 1.0) if total > 0 else 0
    filled = int(width * ratio)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {ratio:.0%}"


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


def _translate_error(status_code, response_text):
    """将API错误翻译为中文"""
    msg = _ERROR_MESSAGES.get(status_code)
    if msg:
        return f"[{status_code}] {msg}"
    # 尝试从响应JSON中提取error信息
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


class ZhipuClient:
    """智谱AI API客户端"""

    DEFAULT_BASE_URL = "https://open.bigmodel.cn/api/paas/v4"
    DEFAULT_IMAGE_MODEL = "cogview-4"
    DEFAULT_VIDEO_MODEL = "cogvideox-3"
    DEFAULT_VISION_MODEL = "glm-4v-flash"
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

    # ---- 图片生成 ----

    def generate_image(self, prompt, model=None, size="1024x1024"):
        """
        文生图
        返回图片URL列表
        """
        model = model or self.DEFAULT_IMAGE_MODEL
        url = f"{self.base_url}/images/generations"

        print(f"  提交图片生成请求...")
        resp = requests.post(url, headers=self._headers(), json={
            "model": model,
            "prompt": prompt,
            "size": size,
        }, timeout=60)

        if resp.status_code != 200:
            raise RuntimeError(f"图片生成失败: {_translate_error(resp.status_code, resp.text)}")

        data = resp.json()
        if not data.get("data"):
            raise RuntimeError("图片生成失败: 服务端未返回图片数据")
        return data["data"]

    def download_image(self, image_data, output_path):
        """下载图片（URL或base64）并保存"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if image_data.get("url"):
            resp = requests.get(image_data["url"], timeout=30, stream=True)
            resp.raise_for_status()
            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        sys.stdout.write(f"\r  下载中 {_progress_bar(downloaded, total)}")
                        sys.stdout.flush()
            if total > 0:
                print()
        elif image_data.get("b64_json"):
            output_path.write_bytes(base64.b64decode(image_data["b64_json"]))
        else:
            raise ValueError("图片下载失败: 服务端返回的数据格式异常")

        return str(output_path)

    # ---- 视频生成 ----

    def submit_video_task(self, prompt, model=None, size="1920x1080", quality="speed",
                          first_frame_image=None):
        """
        提交视频生成任务（文生视频 / 图生视频）
        返回任务ID
        """
        model = model or self.DEFAULT_VIDEO_MODEL
        url = f"{self.base_url}/videos/generations"

        body = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }

        if first_frame_image:
            img_path = Path(first_frame_image)
            if img_path.exists():
                b64 = base64.b64encode(img_path.read_bytes()).decode()
                body["image"] = f"data:image/png;base64,{b64}"

        max_retries = 5
        for attempt in range(max_retries):
            print(f"  提交视频生成请求{' (重试 ' + str(attempt + 1) + '/' + str(max_retries) + ')' if attempt > 0 else ''}...", end=" ")
            resp = requests.post(url, headers=self._headers(), json=body, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                task_id = data.get("id")
                if not task_id:
                    raise RuntimeError("视频生成失败: 服务端未返回任务ID")
                _interrupted_tasks.append(task_id)
                print(f"成功")
                return task_id

            if resp.status_code == 429:
                wait = 30 * (attempt + 1)
                print(f"\n  速率限制，{wait}s 后重试...")
                for s in range(wait, 0, -1):
                    sys.stdout.write(f"\r  等待 {s}s...  ")
                    sys.stdout.flush()
                    time.sleep(1)
                print()
                continue

            raise RuntimeError(f"视频生成提交失败: {_translate_error(resp.status_code, resp.text)}")

        raise RuntimeError("视频生成提交失败: 超过最大重试次数(5次)，请稍后再试")

    def poll_video_result(self, task_id, max_attempts=120, interval=5):
        """
        轮询视频生成结果（带进度条和时间预估）
        返回 {"video_url": str, "cover_url": str}
        """
        url = f"{self.base_url}/async-result/{task_id}"
        # 视频生成通常需要2-5分钟，用3分钟作为预估基准
        estimated_time = 180

        start_time = time.time()
        last_status = None

        for i in range(max_attempts):
            resp = requests.get(url, headers=self._headers(), timeout=30)

            if resp.status_code != 200:
                raise RuntimeError(f"查询任务状态失败: {_translate_error(resp.status_code, resp.text)}")

            data = resp.json()
            status = data.get("task_status")

            if status == "SUCCESS":
                videos = data.get("video_result", [])
                if not videos:
                    raise RuntimeError("视频生成失败: 服务端返回空结果")
                # 从跟踪列表中移除
                if task_id in _interrupted_tasks:
                    _interrupted_tasks.remove(task_id)
                return {
                    "video_url": videos[0]["url"],
                    "cover_url": videos[0].get("cover_image_url", ""),
                }

            if status == "FAIL":
                if task_id in _interrupted_tasks:
                    _interrupted_tasks.remove(task_id)
                raise RuntimeError("视频生成失败: 服务端处理出错，请调整提示词后重试")

            elapsed = int(time.time() - start_time)
            remaining = max(0, estimated_time - elapsed)
            bar = _progress_bar(i + 1, max_attempts)

            # 状态变化时打印提示
            status_display = {
                "PROCESSING": "处理中",
                "PENDING": "排队中",
            }
            status_text = status_display.get(status, status)

            if status != last_status:
                print(f"\n  状态: {status_text}")
                last_status = status

            sys.stdout.write(f"\r  {bar} 已等待 {elapsed}s | 预计剩余 {remaining}s  ")
            sys.stdout.flush()
            time.sleep(interval)

        print()
        raise RuntimeError("视频生成超时: 等待超过10分钟，请用 task-status 查询任务是否完成")

    def download_video(self, video_url, output_path):
        """下载视频并保存（带进度条）"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print(f"  下载视频中...")
        resp = requests.get(video_url, timeout=120, stream=True)
        resp.raise_for_status()

        total = int(resp.headers.get("content-length", 0))
        downloaded = 0
        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(65536):
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    mb_down = downloaded / (1024 * 1024)
                    mb_total = total / (1024 * 1024)
                    sys.stdout.write(f"\r  {_progress_bar(downloaded, total)} {mb_down:.1f}/{mb_total:.1f}MB")
                    sys.stdout.flush()

        if total > 0:
            print()
        return str(output_path)

    # ---- 任务状态查询 ----

    def query_task_status(self, task_id):
        """查询异步任务状态"""
        url = f"{self.base_url}/async-result/{task_id}"
        resp = requests.get(url, headers=self._headers(), timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"查询任务失败: {_translate_error(resp.status_code, resp.text)}")
        return resp.json()

    # ---- 视觉分析 ----

    def analyze_image(self, image_path, prompt="请详细描述这个视频帧中的画面内容，包括：主体对象、场景环境、动作状态、色彩风格。用中文回答。"):
        """
        视觉分析（glm-4v-flash）
        传入图片路径，返回描述文本
        """
        model = self.DEFAULT_VISION_MODEL
        url = f"{self.base_url}/chat/completions"

        img_path = Path(image_path)
        b64 = base64.b64encode(img_path.read_bytes()).decode()

        resp = requests.post(url, headers=self._headers(), json={
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }],
        }, timeout=60)

        if resp.status_code != 200:
            raise RuntimeError(f"视觉分析失败: {_translate_error(resp.status_code, resp.text)}")

        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def compare_prompts(self, original_prompt, frame_descriptions):
        """
        对比原始提示词与帧描述，返回评分JSON
        """
        model = self.DEFAULT_CHAT_MODEL
        url = f"{self.base_url}/chat/completions"

        frames_text = "\n\n---\n\n".join(
            f"帧 {i + 1}:\n{desc}" for i, desc in enumerate(frame_descriptions)
        )

        system_prompt = """你是一个视频内容质量评估专家。你的任务是：
1. 分析原始提示词的意图
2. 对比视频帧描述与原始提示词的匹配程度
3. 从以下维度评分（每项 0-100）：
   - 主体一致性：视频中的主体是否与提示词描述一致
   - 场景还原度：场景环境是否匹配
   - 动作合理性：动作状态是否合理（如有描述）
   - 整体评分：综合评估

请严格按以下 JSON 格式输出（不要输出其他内容）：
{"summary":"一句话总结","score":85,"subject_score":90,"scene_score":80,"action_score":85,"details":"详细分析说明"}"""

        resp = requests.post(url, headers=self._headers(), json={
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"原始提示词：{original_prompt}\n\n视频帧描述：\n{frames_text}"},
            ],
        }, timeout=60)

        if resp.status_code != 200:
            raise RuntimeError(f"质量评分失败: {_translate_error(resp.status_code, resp.text)}")

        text = resp.json()["choices"][0]["message"]["content"]

        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"summary": text, "score": -1, "details": text}
