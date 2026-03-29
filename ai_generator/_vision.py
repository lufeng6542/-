#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
视觉分析功能 - GLM-4.6V / glm-4v-flash / glm-4-flash
ZhipuClient 的视觉分析 mixin

支持：
- 图片理解（image_url）
- 视频理解（video_url，GLM-4.6V 原生支持）
- 提示词对比评分
"""

import json
import re
import base64
from pathlib import Path


class VisionMixin:
    """视觉分析功能（混入 ZhipuClient）"""

    def chat(self, messages, model=None, system_prompt=None, temperature=0.7, timeout=60):
        """
        通用文本对话（GLM-4-Flash）

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}, ...]
            model: 模型名称（默认 DEFAULT_CHAT_MODEL）
            system_prompt: 系统提示词（可选）
            temperature: 温度参数（0-1）
            timeout: 请求超时秒数

        Returns:
            str: 模型回复文本
        """
        model = model or self.DEFAULT_CHAT_MODEL
        if system_prompt:
            msgs = [{"role": "system", "content": system_prompt}] + list(messages)
        else:
            msgs = list(messages)

        resp = self._post("/chat/completions", {
            "model": model,
            "messages": msgs,
            "temperature": temperature,
        }, timeout=timeout)

        return resp.json()["choices"][0]["message"]["content"]

    def analyze_image(self, image_path, prompt=None, model=None, thinking=False):
        """
        图片视觉分析

        Args:
            image_path: 图片路径（本地文件）
            prompt: 分析提示词（默认详细描述画面内容）
            model: 模型名称（默认 DEFAULT_VISION_MODEL）
            thinking: 是否开启推理模式

        Returns:
            str: 分析结果文本
        """
        model = model or self.DEFAULT_VISION_MODEL
        if prompt is None:
            prompt = "请详细描述这个视频帧中的画面内容，包括：主体对象、场景环境、动作状态、色彩风格。用中文回答。"

        img_path = Path(image_path)
        b64 = base64.b64encode(img_path.read_bytes()).decode()

        body = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }],
        }
        if thinking:
            body["thinking"] = {"type": "enabled"}

        resp = self._post("/chat/completions", body, timeout=120)

        data = resp.json()
        message = data["choices"][0]["message"]
        # GLM-4.6V thinking 模式下 reasoning_content 在 message 中
        reasoning = message.get("reasoning_content", "")
        content = message["content"]
        if reasoning and thinking:
            return f"[推理过程]\n{reasoning}\n\n[分析结果]\n{content}"
        return content

    def analyze_video(self, video_path, prompt=None, model=None, thinking=False):
        """
        视频视觉分析（GLM-4.6V 原生支持）

        Args:
            video_path: 视频路径（本地文件）或视频URL
            prompt: 分析提示词（默认详细描述视频内容）
            model: 模型名称（默认 DEFAULT_VISION_MODEL）
            thinking: 是否开启推理模式

        Returns:
            str: 分析结果文本

        Note:
            GLM-4.6V 原生支持视频理解，无需手动抽帧。
            本地视频会自动转为 base64 传入。
        """
        model = model or self.DEFAULT_VISION_MODEL
        if prompt is None:
            prompt = "请详细描述这个视频的内容，包括：主体对象、场景环境、动作变化、色彩风格、镜头运动。用中文回答。"

        # 判断是URL还是本地文件
        path_str = str(video_path)
        if path_str.startswith("http://") or path_str.startswith("https://"):
            video_url = path_str
        else:
            video_file = Path(video_path)
            if not video_file.exists():
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            # 获取MIME类型
            ext = video_file.suffix.lower()
            mime_map = {".mp4": "video/mp4", ".mov": "video/quicktime",
                        ".avi": "video/x-msvideo", ".webm": "video/webm"}
            mime = mime_map.get(ext, "video/mp4")
            b64 = base64.b64encode(video_file.read_bytes()).decode()
            video_url = f"data:{mime};base64,{b64}"

        body = {
            "model": model,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "video_url", "video_url": {"url": video_url}},
                    {"type": "text", "text": prompt},
                ],
            }],
        }
        if thinking:
            body["thinking"] = {"type": "enabled"}

        print(f"  调用 {model} 分析视频...")
        resp = self._post("/chat/completions", body, timeout=300)

        data = resp.json()
        message = data["choices"][0]["message"]
        reasoning = message.get("reasoning_content", "")
        content = message["content"]
        if reasoning and thinking:
            return f"[推理过程]\n{reasoning}\n\n[分析结果]\n{content}"
        return content

    def compare_prompts(self, original_prompt, frame_descriptions, model=None):
        """
        对比原始提示词与帧描述，返回评分JSON

        Args:
            original_prompt: 原始生成提示词
            frame_descriptions: 帧描述列表
            model: 模型名称（默认 DEFAULT_CHAT_MODEL）
        """
        model = model or self.DEFAULT_CHAT_MODEL

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

        resp = self._post("/chat/completions", {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"原始提示词：{original_prompt}\n\n视频帧描述：\n{frames_text}"},
            ],
        }, timeout=60)

        text = resp.json()["choices"][0]["message"]["content"]

        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"summary": text, "score": -1, "details": text}

    def verify_video_native(self, video_path, original_prompt, model=None, thinking=True):
        """
        使用 GLM-4.6V 原生视频理解进行质量验证（无需抽帧）

        Args:
            video_path: 视频路径
            original_prompt: 原始生成提示词
            model: 视觉模型名称（默认 DEFAULT_VISION_MODEL）
            thinking: 是否开启推理模式

        Returns:
            dict: 评分结果 {"summary", "score", "subject_score", "scene_score", "action_score", "details"}
        """
        model = model or self.DEFAULT_VISION_MODEL

        verify_prompt = f"""你是一个视频内容质量评估专家。请分析以下视频是否与原始提示词匹配。

原始提示词：{original_prompt}

请从以下维度评分（每项 0-100）：
- subject_score（主体一致性）：视频中的主体是否与提示词描述一致
- scene_score（场景还原度）：场景环境是否匹配
- action_score（动作合理性）：动作状态是否合理
- score（整体评分）：综合评估

请严格按以下 JSON 格式输出（不要输出其他内容）：
{{"summary":"一句话总结","score":85,"subject_score":90,"scene_score":80,"action_score":85,"details":"详细分析说明"}}"""

        result_text = self.analyze_video(video_path, prompt=verify_prompt, model=model, thinking=thinking)

        # 从结果中提取JSON
        json_match = re.search(r'\{[\s\S]*\}', result_text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        return {"summary": result_text, "score": -1, "details": result_text}
