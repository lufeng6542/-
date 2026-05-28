#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""图片生成 — 火山ARK / 智谱 / 百炼 三后端"""

import base64
from pathlib import Path


class ImageMixin:
    """图片生成（混入 KimiClient）"""

    def _is_ark(self):
        return "volces.com" in self.base_url

    def _is_dashscope(self):
        return "dashscope" in self.base_url

    def generate_image(self, prompt, model=None, size="1024x1024"):
        if self._is_ark():
            return self._generate_ark(prompt, model, size)
        if self._is_dashscope():
            return self._generate_dashscope(prompt, model, size)
        return self._generate_zhipu(prompt, model, size)

    def _generate_ark(self, prompt, model, size):
        if not model or "cogview" in str(model).lower():
            model = "doubao-seedream-4-5"
        body = {"model": model, "prompt": prompt, "size": size, "n": 1}
        resp = self._post("/images/generations", body, timeout=120)
        return resp.get("data", [])

    def _generate_zhipu(self, prompt, model, size):
        model = model or "cogview-4"
        body = {"model": model, "prompt": prompt}
        if size:
            body["size"] = size
        resp = self._post("/images/generations", body, timeout=120)
        return resp.get("data", [])

    def _generate_dashscope(self, prompt, model, size):
        if not model or "cogview" in str(model).lower():
            model = "wan2.1-t2i-large"
        dash_size = size.replace("x", "*") if size else "1024*1024"
        body = {
            "model": model,
            "input": {"prompt": prompt},
            "parameters": {"size": dash_size, "n": 1},
        }
        resp = self._post(
            "/api/v1/services/aigc/text2image/image-synthesis",
            body, timeout=120
        )
        output = resp.get("output", {})
        if output.get("task_status") != "SUCCEEDED":
            raise RuntimeError(f"图片生成失败: {resp}")
        return [{"url": r.get("url")} for r in output.get("results", [])]

    def download_image(self, image_data, output_path):
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if image_data.get("url"):
            return self._download_file(image_data["url"], output_path, chunk_size=8192)
        elif image_data.get("b64_json"):
            output_path.write_bytes(base64.b64decode(image_data["b64_json"]))
            return str(output_path)
        else:
            raise ValueError(f"图片下载失败: {list(image_data.keys())}")
