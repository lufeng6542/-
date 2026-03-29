#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智谱AI API客户端 - 兼容层
组合基础客户端 + 图片/视频/视觉分析 mixin
"""

from ._client import ZhipuClient as _Base, translate_error, progress_bar, _interrupted_tasks
from ._image import ImageMixin
from ._video import VideoMixin
from ._vision import VisionMixin


class ZhipuClient(ImageMixin, VideoMixin, VisionMixin, _Base):
    """
    智谱AI API客户端（完整版）

    组合了：
    - _client: HTTP请求、API Key管理、错误翻译、进度条、信号处理
    - _image: 图片生成（CogView-4）
    - _video: 视频生成（CogVideoX-3）+ 任务轮询
    - _vision: 视觉分析（glm-4v-flash）+ 提示词对比评分（glm-4-flash）
    """
    pass


__all__ = ["ZhipuClient", "translate_error", "progress_bar", "_interrupted_tasks"]
