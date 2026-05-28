#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""视频生成 — 火山ARK Seedance / 智谱 CogVideoX / 百炼 三后端"""

import os
import time
import base64
from pathlib import Path

import requests


def _image_mime(ext):
    return {
        ".png": "image/png", ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg", ".webp": "image/webp",
    }.get(ext, "image/png")


class VideoMixin:
    """视频生成（混入 KimiClient）"""

    def _is_ark(self):
        return "volces.com" in self.base_url

    def _is_dashscope(self):
        return "dashscope" in self.base_url

    # ── 提交任务 ──────────────────────────────────────────────

    def submit_video_task(self, prompt, model=None, size="1920x1080", quality="speed",
                          first_frame_image=None, last_frame_image=None,
                          with_audio=False, fps=None):
        if self._is_ark():
            return self._submit_ark(prompt, model, first_frame_image, size)
        if self._is_dashscope():
            return self._submit_dashscope(prompt, model, first_frame_image)
        return self._submit_zhipu(prompt, model, size, quality,
                                  first_frame_image, with_audio, fps)

    def _submit_ark(self, prompt, model, first_frame_image, size):
        model = model or os.environ.get("VIDEO_MODEL", "doubao-seedance-2-0-260128")
        content = [{"type": "text", "text": prompt}]
        # Add reference image if provided (I2V mode)
        if first_frame_image:
            img = Path(first_frame_image)
            b64 = base64.b64encode(img.read_bytes()).decode()
            mime = _image_mime(img.suffix.lower())
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:{mime};base64,{b64}"},
                "role": "reference_image",
            })
        # Determine ratio from size
        w, h = 1080, 1920
        if "x" in size:
            parts = size.split("x")
            w, h = int(parts[0]), int(parts[1])
        ratio = "9:16" if h > w else "16:9"
        body = {
            "model": model,
            "content": content,
            "ratio": ratio,
            "watermark": False,
        }
        resp = self._post("/contents/generations/tasks", body, timeout=60)
        task_id = resp.get("id", "")
        if not task_id:
            raise RuntimeError(f"ARK 视频任务提交失败: {resp}")
        print(f"  任务ID: {task_id}")
        return task_id

    def _submit_zhipu(self, prompt, model, size, quality, first_frame_image, with_audio, fps):
        model = model or "cogvideox-3"
        body = {"model": model, "prompt": prompt, "size": size, "quality": quality}
        if with_audio:
            body["with_audio"] = True
        if fps:
            body["fps"] = fps
        if first_frame_image:
            img = Path(first_frame_image)
            b64 = base64.b64encode(img.read_bytes()).decode()
            body["image_url"] = f"data:{_image_mime(img.suffix.lower())};base64,{b64}"
        resp = self._post("/videos/generations", body, timeout=60)
        task_id = resp.get("id", "")
        if not task_id:
            raise RuntimeError(f"视频任务提交失败: {resp}")
        print(f"  任务ID: {task_id}")
        return task_id

    def _submit_dashscope(self, prompt, model, first_frame_image):
        if not model or "cogvideo" in str(model).lower():
            model = os.environ.get("VIDEO_MODEL", "wan2.1-i2v-plus")
        inp = {"prompt": prompt}
        if first_frame_image:
            img = Path(first_frame_image)
            b64 = base64.b64encode(img.read_bytes()).decode()
            mime = _image_mime(img.suffix.lower())
            inp["img_url"] = f"data:{mime};base64,{b64}"
        body = {"model": model, "input": inp}
        resp = self._post(
            "/api/v1/services/aigc/video-generation/video-synthesis",
            body, timeout=60
        )
        task_id = resp.get("output", {}).get("task_id", "")
        if not task_id:
            raise RuntimeError(f"视频任务提交失败: {resp}")
        print(f"  任务ID: {task_id}")
        return task_id

    # ── 轮询结果 ──────────────────────────────────────────────

    def poll_video_result(self, task_id, max_attempts=120, interval=5):
        if self._is_ark():
            return self._poll_ark(task_id, max_attempts, interval)
        if self._is_dashscope():
            return self._poll_dashscope(task_id, max_attempts, interval)
        return self._poll_zhipu(task_id, max_attempts, interval)

    def _poll_ark(self, task_id, max_attempts, interval):
        url = f"{self.base_url}/contents/generations/tasks/{task_id}"
        headers = self._headers()
        for i in range(max_attempts):
            resp = requests.get(url, headers=headers, timeout=20).json()
            status = resp.get("status", "unknown")
            if status == "succeeded":
                content = resp.get("content", {})
                video_url = content.get("video_url", "")
                if video_url:
                    return {"video_url": video_url}
                raise RuntimeError(f"ARK 视频完成但无URL: {resp}")
            elif status == "failed":
                err = resp.get("error", {})
                raise RuntimeError(f"ARK 视频失败: {err.get('message', resp)}")
            elif status in ("queued", "running"):
                elapsed = (i + 1) * interval
                print(f"  [{status}] {elapsed}s/{max_attempts * interval}s")
                time.sleep(interval)
            else:
                time.sleep(interval)
        raise TimeoutError(f"ARK 视频任务超时 ({max_attempts * interval}s)")

    def _poll_zhipu(self, task_id, max_attempts, interval):
        endpoint = f"/videos/async-result/{task_id}"
        for i in range(max_attempts):
            resp = self._post(endpoint, {}, timeout=20)
            status = resp.get("task_status", "UNKNOWN")
            if status == "SUCCESS":
                videos = resp.get("video_result", [])
                if videos:
                    return {"video_url": videos[0].get("url", "")}
                raise RuntimeError(f"视频任务完成但无结果: {resp}")
            elif status == "FAIL":
                raise RuntimeError(f"视频生成失败: {resp}")
            elif status in ("PROCESSING", "PREPARING", "PENDING", "WAIT"):
                print(f"  [{status}] {(i+1)*interval}s")
                time.sleep(interval)
            else:
                time.sleep(interval)
        raise TimeoutError(f"视频任务超时")

    def _poll_dashscope(self, task_id, max_attempts, interval):
        url = f"{self.base_url}/api/v1/tasks/{task_id}"
        headers = self._headers()
        for i in range(max_attempts):
            resp = requests.get(url, headers=headers, timeout=20).json()
            output = resp.get("output", {})
            status = output.get("task_status", "UNKNOWN")
            if status == "SUCCEEDED":
                video_url = output.get("video_url", "")
                if video_url:
                    return {"video_url": video_url}
                raise RuntimeError(f"视频完成但无URL: {resp}")
            elif status == "FAILED":
                raise RuntimeError(f"视频生成失败: {resp}")
            elif status in ("PENDING", "RUNNING"):
                print(f"  [{status}] {(i+1)*interval}s")
                time.sleep(interval)
            else:
                time.sleep(interval)
        raise TimeoutError(f"视频任务超时")

    def download_video(self, video_url, output_path):
        print("  下载视频中...")
        return self._download_file(video_url, output_path)

    def query_task_status(self, task_id):
        if self._is_ark():
            url = f"{self.base_url}/contents/generations/tasks/{task_id}"
            resp = requests.get(url, headers=self._headers(), timeout=20).json()
            return resp.get("status", "UNKNOWN")
        if self._is_dashscope():
            url = f"{self.base_url}/api/v1/tasks/{task_id}"
            resp = requests.get(url, headers=self._headers(), timeout=20).json()
            return resp.get("output", {}).get("task_status", "UNKNOWN")
        resp = self._post(f"/videos/async-result/{task_id}", {}, timeout=20)
        return resp.get("task_status", "UNKNOWN")
