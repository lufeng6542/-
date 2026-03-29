#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片生成功能 - CogView-4
ZhipuClient 的图片生成 mixin
"""

import sys
import base64
from pathlib import Path


class ImageMixin:
    """图片生成功能（混入 ZhipuClient）"""

    def generate_image(self, prompt, model=None, size="1024x1024"):
        """
        文生图
        返回图片URL列表
        """
        model = model or self.DEFAULT_IMAGE_MODEL
        url = f"{self.base_url}/images/generations"

        print("  提交图片生成请求...")
        resp = self._post("/images/generations", {
            "model": model,
            "prompt": prompt,
            "size": size,
        }, timeout=60)

        data = resp.json()
        if not data.get("data"):
            raise RuntimeError("图片生成失败: 服务端未返回图片数据")
        return data["data"]

    def download_image(self, image_data, output_path):
        """下载图片（URL或base64）并保存"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if image_data.get("url"):
            resp = self._download_file(image_data["url"], output_path, chunk_size=8192)
            return resp
        elif image_data.get("b64_json"):
            output_path.write_bytes(base64.b64decode(image_data["b64_json"]))
            return str(output_path)
        else:
            raise ValueError("图片下载失败: 服务端返回的数据格式异常")
