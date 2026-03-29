#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视频生成功能 - CogVideoX-3
ZhipuClient 的视频生成 mixin
"""

import sys
import time
import base64
from pathlib import Path

from . import _client


def _image_mime(ext):
    """根据扩展名返回图片 MIME 类型"""
    return {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(ext, "image/png")


class VideoMixin:
    """视频生成功能（混入 ZhipuClient）"""

    def submit_video_task(self, prompt, model=None, size="1920x1080", quality="speed",
                          first_frame_image=None, last_frame_image=None,
                          with_audio=False, fps=None):
        """
        提交视频生成任务（文生视频 / 图生视频 / 首尾帧生成）

        Args:
            prompt: 提示词
            model: 模型名称（默认 cogvideox-3）
            size: 视频尺寸
            quality: 生成质量 (speed / quality)
            first_frame_image: 首帧图片路径
            last_frame_image: 尾帧图片路径（与首帧配合使用）
            with_audio: 是否生成带音频的视频
            fps: 帧率 (30 或 60)

        Returns:
            str: 任务ID
        """
        model = model or self.DEFAULT_VIDEO_MODEL

        body = {
            "model": model,
            "prompt": prompt,
            "size": size,
            "quality": quality,
        }

        if with_audio:
            body["with_audio"] = True

        if fps:
            if fps not in (30, 60):
                raise ValueError(f"帧率只支持 30 或 60，当前: {fps}")
            body["fps"] = fps

        # 首帧图片
        if first_frame_image:
            first_path = Path(first_frame_image)
            if first_path.exists():
                b64_first = base64.b64encode(first_path.read_bytes()).decode()
                mime = _image_mime(first_path.suffix.lower())
                body["image"] = f"data:{mime};base64,{b64_first}"

        # 尾帧图片（首尾帧模式，image 传数组）
        if last_frame_image:
            last_path = Path(last_frame_image)
            if last_path.exists():
                b64_last = base64.b64encode(last_path.read_bytes()).decode()
                mime = _image_mime(last_path.suffix.lower())
                last_url = f"data:{mime};base64,{b64_last}"
                if "image" in body:
                    body["image"] = [body["image"], last_url]
                else:
                    body["image"] = last_url

        import requests as _req

        url = self.base_url + "/videos/generations"
        max_retries = 5
        for attempt in range(max_retries):
            retry_msg = f" (重试 {attempt + 1}/{max_retries})" if attempt > 0 else ""
            print(f"  提交视频生成请求{retry_msg}...", end=" ")
            resp = _req.post(url, headers=self._headers(), json=body, timeout=60)

            if resp.status_code == 200:
                data = resp.json()
                task_id = data.get("id")
                if not task_id:
                    raise RuntimeError("视频生成失败: 服务端未返回任务ID")
                _client._interrupted_tasks.append(task_id)
                print("成功")
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

            raise RuntimeError(f"视频生成提交失败: {_client.translate_error(resp.status_code, resp.text)}")

        raise RuntimeError("视频生成提交失败: 超过最大重试次数(5次)，请稍后再试")

    def poll_video_result(self, task_id, max_attempts=120, interval=5):
        """
        轮询视频生成结果（带进度条和时间预估）
        返回 {"video_url": str, "cover_url": str}
        """
        estimated_time = 180
        start_time = time.time()
        last_status = None

        for i in range(max_attempts):
            resp = self._get(f"/async-result/{task_id}", timeout=30)
            data = resp.json()
            status = data.get("task_status")

            if status == "SUCCESS":
                videos = data.get("video_result", [])
                if not videos:
                    raise RuntimeError("视频生成失败: 服务端返回空结果")
                if task_id in _client._interrupted_tasks:
                    _client._interrupted_tasks.remove(task_id)
                return {
                    "video_url": videos[0]["url"],
                    "cover_url": videos[0].get("cover_image_url", ""),
                }

            if status == "FAIL":
                if task_id in _client._interrupted_tasks:
                    _client._interrupted_tasks.remove(task_id)
                raise RuntimeError("视频生成失败: 服务端处理出错，请调整提示词后重试")

            elapsed = int(time.time() - start_time)
            remaining = max(0, estimated_time - elapsed)
            bar = _client.progress_bar(i + 1, max_attempts)

            status_display = {"PROCESSING": "处理中", "PENDING": "排队中"}
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
        print("  下载视频中...")
        return self._download_file(video_url, output_path)

    def query_task_status(self, task_id):
        """查询异步任务状态"""
        resp = self._get(f"/async-result/{task_id}", timeout=30)
        return resp.json()
