#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI全自动视频创作流水线
用户输入主题 → 大纲规划 → 关键帧生成+质检 → 视频生成+质检 → 输出
"""

import json
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from .zhipu_client import ZhipuClient
from .image_generator import ar_to_size
from .video_generator import VIDEO_SIZES
from .output_manager import save_record


# ============================================================
# 数据结构
# ============================================================

@dataclass
class Scene:
    """单个场景"""
    index: int
    description: str
    image_prompt: str = ""
    image_path: Optional[str] = None
    image_score: int = -1
    image_retries: int = 0
    passed_image_qc: bool = False
    video_prompt: str = ""
    video_path: Optional[str] = None
    video_score: int = -1
    video_retries: int = 0
    passed_video_qc: bool = False


@dataclass
class PipelineConfig:
    """流水线配置"""
    ar: str = "16:9"
    quality: str = "speed"
    image_max_retries: int = 2
    video_max_retries: int = 2
    image_qc_threshold: int = 70
    video_qc_threshold: int = 70
    scene_count: Optional[int] = None
    with_audio: bool = False
    fps: Optional[int] = None
    output_dir: Optional[str] = None


# ============================================================
# 核心流水线
# ============================================================

class VideoPipeline:
    """AI全自动视频创作流水线"""

    def __init__(self, config: PipelineConfig = None):
        self.config = config or PipelineConfig()
        self.client: ZhipuClient = None
        self.scenes: List[Scene] = []
        self.work_dir: Path = None
        self._user_request: str = ""
        self._start_time: float = 0

    # ---- 主入口 ----

    def run(self, user_request: str) -> Dict:
        """
        运行完整流水线

        Args:
            user_request: 用户创作要求

        Returns:
            dict: 运行结果（scenes、视频路径列表、报告路径）
        """
        self._user_request = user_request
        self._start_time = time.time()
        self.client = ZhipuClient()
        self.work_dir = self._init_work_dir()

        self._print_banner()

        try:
            self._step_plan_outline()
            self._step_generate_image_prompts()
            self._step_generate_images()
            self._step_generate_video_prompts()
            self._step_generate_videos()

            report_path = self._save_pipeline_report()
            self._print_summary()
            return self._build_result(report_path)

        except KeyboardInterrupt:
            print("\n\n[中断] 用户取消，已保存进度")
            self._save_pipeline_report()
            return self._build_result(None)
        except Exception as e:
            print(f"\n[错误] {e}")
            self._save_pipeline_report()
            raise

    # ---- 步骤1: 大纲规划 ----

    def _step_plan_outline(self):
        self._print_header("步骤1/5: 大纲规划")

        system = """你是一个专业的视频编剧。用户会给你一个视频创作主题，你需要将其拆分为多个场景。
每个场景应该：
1. 有清晰的视觉描述（画面内容、色彩、光线、构图）
2. 场景之间有合理的过渡和叙事逻辑
3. 总共3-6个场景

请严格按以下 JSON 数组格式输出（不要输出其他内容）：
[{"index": 1, "description": "场景的详细视觉描述"}, ...]"""

        hint = f"\n请生成恰好 {self.config.scene_count} 个场景。" if self.config.scene_count else ""

        response = self.client.chat(
            messages=[{"role": "user", "content": f"创作主题：{self._user_request}{hint}"}],
            system_prompt=system, temperature=0.8,
        )

        parsed = self._parse_json_array(response)
        self.scenes = [Scene(index=s["index"], description=s["description"]) for s in parsed]

        print(f"  生成 {len(self.scenes)} 个场景:")
        for s in self.scenes:
            print(f"    场景{s.index}: {s.description[:60]}...")

    # ---- 步骤2: 生成图片提示词 ----

    def _step_generate_image_prompts(self):
        self._print_header("步骤2/5: 生成图片提示词")

        system = """你是一个专业的AI图片提示词工程师。你需要为视频场景生成高质量的图片提示词。
要求：
1. 提示词用英文编写（AI图片生成模型对英文理解更好）
2. 包含主体、环境、光线、构图、风格等细节
3. 提示词长度在50-150个英文单词
4. 风格统一，所有场景保持一致的视觉风格
5. 适合作为视频关键帧

只输出提示词本身，不要输出其他内容。"""

        context = "\n".join(f"场景{s.index}: {s.description}" for s in self.scenes)

        for i, scene in enumerate(self.scenes):
            self._print_progress(i + 1, len(self.scenes), "生成图片提示词")

            prompt = self.client.chat(
                messages=[{"role": "user", "content":
                    f"所有场景概览：\n{context}\n\n"
                    f"请为场景{scene.index}生成图片提示词。\n"
                    f"场景描述：{scene.description}"}],
                system_prompt=system, temperature=0.7,
            )
            scene.image_prompt = prompt.strip()
            print(f"    场景{scene.index}: {scene.image_prompt[:60]}...")

    # ---- 步骤3: 生成关键帧图片（含质检+重试） ----

    def _step_generate_images(self):
        self._print_header("步骤3/5: 生成关键帧图片（含质检）")

        for i, scene in enumerate(self.scenes):
            self._print_progress(i + 1, len(self.scenes), "生成关键帧")
            print(f"\n  --- 场景{scene.index} ---")

            for attempt in range(self.config.image_max_retries + 1):
                # 生成图片
                size = ar_to_size(self.config.ar)
                result = self.client.generate_image(scene.image_prompt, size=size)

                image_path = self.work_dir / f"keyframe_{scene.index:02d}.png"
                self.client.download_image(result[0], image_path)
                scene.image_path = str(image_path)
                scene.image_retries = attempt

                # 质检
                qc_result = self._step_qc_image(scene)
                scene.passed_image_qc = scene.image_score >= self.config.image_qc_threshold

                if scene.passed_image_qc:
                    print(f"  [通过] 评分: {scene.image_score}/100")
                    break

                print(f"  [未通过] 评分: {scene.image_score}/100 (重试 {attempt + 1}/{self.config.image_max_retries})")

                if attempt < self.config.image_max_retries:
                    scene.image_prompt = self._step_refine_image_prompt(scene, qc_result)

            if not scene.passed_image_qc:
                print(f"  [警告] 场景{scene.index}图片质检未通过，使用当前结果")

    def _step_qc_image(self, scene: Scene) -> dict:
        """图片质检：analyze_image 对比图片与场景描述"""
        prompt = f"""你是一个图片质量评估专家。请分析以下图片是否与目标场景描述匹配。

目标场景描述：{scene.description}
图片生成提示词：{scene.image_prompt}

请从以下维度评分（每项 0-100）：
- subject_score（主体一致性）
- scene_score（场景还原度）
- action_score（画面质量）
- score（整体评分）

请严格按以下 JSON 格式输出：
{{"summary":"一句话总结","score":85,"subject_score":90,"scene_score":80,"action_score":85,"details":"详细分析"}}"""

        result_text = self.client.analyze_image(scene.image_path, prompt=prompt)
        return self._parse_qc_result(result_text, scene, "image")

    def _step_refine_image_prompt(self, scene: Scene, qc_result: dict) -> str:
        """LLM 根据质检反馈修改图片提示词"""
        system = """你是一个专业的AI图片提示词优化师。之前生成的图片质量不达标，你需要根据质检反馈修改提示词。
要求：1. 英文提示词 2. 针对问题改进 3. 保留正确部分 4. 只输出修改后的提示词"""

        feedback = f"总结：{qc_result.get('summary', '')}\n详情：{qc_result.get('details', '')}"

        new_prompt = self.client.chat(
            messages=[{"role": "user", "content":
                f"原始提示词：{scene.image_prompt}\n\n"
                f"质检反馈：\n{feedback}\n  评分：{scene.image_score}/100\n\n"
                f"请修改提示词以提升图片质量。"}],
            system_prompt=system, temperature=0.7,
        )
        scene.image_prompt = new_prompt.strip()
        print(f"  修改后: {scene.image_prompt[:60]}...")
        return scene.image_prompt

    # ---- 步骤4: 生成视频提示词 ----

    def _step_generate_video_prompts(self):
        self._print_header("步骤4/5: 生成视频提示词")

        system = """你是一个专业的AI视频提示词工程师。你需要为视频场景生成视频提示词。
要求：
1. 提示词用英文
2. 描述期望的镜头运动、主体动作、光影变化等动态元素
3. 提示词长度在30-100个英文单词
4. 注意：该视频将以指定关键帧图片为首帧，提示词应描述从该帧开始的动态内容

只输出提示词本身，不要输出其他内容。"""

        for i, scene in enumerate(self.scenes):
            self._print_progress(i + 1, len(self.scenes), "生成视频提示词")

            prompt = self.client.chat(
                messages=[{"role": "user", "content":
                    f"场景描述：{scene.description}\n"
                    f"图片提示词（首帧）：{scene.image_prompt}\n"
                    f"请生成视频提示词，描述从首帧开始的动态内容。"}],
                system_prompt=system, temperature=0.7,
            )
            scene.video_prompt = prompt.strip()
            print(f"    场景{scene.index}: {scene.video_prompt[:60]}...")

    # ---- 步骤5: 生成视频片段（含质检+重试） ----

    def _step_generate_videos(self):
        self._print_header("步骤5/5: 生成视频片段（含质检）")

        size = VIDEO_SIZES.get(self.config.ar, "1920x1080")

        for i, scene in enumerate(self.scenes):
            self._print_progress(i + 1, len(self.scenes), "生成视频")
            print(f"\n  --- 场景{scene.index} ---")

            for attempt in range(self.config.video_max_retries + 1):
                # 图生视频
                task_id = self.client.submit_video_task(
                    scene.video_prompt,
                    size=size,
                    quality=self.config.quality,
                    first_frame_image=scene.image_path,
                    with_audio=self.config.with_audio,
                    fps=self.config.fps,
                )

                result = self.client.poll_video_result(task_id)

                video_path = self.work_dir / f"scene_{scene.index:02d}.mp4"
                self.client.download_video(result["video_url"], video_path)
                scene.video_path = str(video_path)
                scene.video_retries = attempt

                # 质检
                qc_result = self._step_qc_video(scene)
                scene.passed_video_qc = scene.video_score >= self.config.video_qc_threshold

                if scene.passed_video_qc:
                    print(f"  [通过] 评分: {scene.video_score}/100")
                    break

                print(f"  [未通过] 评分: {scene.video_score}/100 (重试 {attempt + 1}/{self.config.video_max_retries})")

                if attempt < self.config.video_max_retries:
                    scene.video_prompt = self._step_refine_video_prompt(scene, qc_result)

            if not scene.passed_video_qc:
                print(f"  [警告] 场景{scene.index}视频质检未通过，使用当前结果")

    def _step_qc_video(self, scene: Scene) -> dict:
        """视频质检：GLM-4.6V 原生视频理解"""
        result = self.client.verify_video_native(
            scene.video_path, scene.video_prompt,
            model=None, thinking=True,
        )
        scene.video_score = result.get("score", -1)
        return result

    def _step_refine_video_prompt(self, scene: Scene, qc_result: dict) -> str:
        """LLM 根据质检反馈修改视频提示词"""
        system = """你是一个专业的AI视频提示词优化师。之前生成的视频质量不达标，你需要根据质检反馈修改提示词。
要求：1. 英文提示词 2. 针对问题改进 3. 保留正确部分 4. 只输出修改后的提示词"""

        feedback = f"总结：{qc_result.get('summary', '')}\n详情：{qc_result.get('details', '')}"

        new_prompt = self.client.chat(
            messages=[{"role": "user", "content":
                f"原始提示词：{scene.video_prompt}\n\n"
                f"质检反馈：\n{feedback}\n  评分：{scene.video_score}/100\n\n"
                f"请修改提示词以提升视频质量。"}],
            system_prompt=system, temperature=0.7,
        )
        scene.video_prompt = new_prompt.strip()
        print(f"  修改后: {scene.video_prompt[:60]}...")
        return scene.video_prompt

    # ---- 辅助方法 ----

    def _init_work_dir(self) -> Path:
        """初始化工作目录"""
        if self.config.output_dir:
            work_dir = Path(self.config.output_dir)
            work_dir.mkdir(parents=True, exist_ok=True)
            return work_dir

        base = Path("ai_output")
        today = datetime.now().strftime("%Y-%m-%d")
        date_dir = base / today
        date_dir.mkdir(parents=True, exist_ok=True)

        existing = sorted(date_dir.glob("pipeline_*"))
        next_num = 1
        if existing:
            last = existing[-1].name
            nums = re.findall(r'\d+', last)
            if nums:
                next_num = int(nums[-1]) + 1

        work_dir = date_dir / f"pipeline_{next_num:03d}"
        work_dir.mkdir(parents=True, exist_ok=True)
        return work_dir

    def _save_pipeline_report(self) -> Path:
        """保存流水线报告"""
        report = {
            "user_request": self._user_request,
            "created_at": datetime.now().isoformat(),
            "config": {
                "ar": self.config.ar,
                "quality": self.config.quality,
                "scene_count": self.config.scene_count,
                "with_audio": self.config.with_audio,
                "fps": self.config.fps,
            },
            "scenes": [
                {
                    "index": s.index,
                    "description": s.description,
                    "image_prompt": s.image_prompt,
                    "image_path": s.image_path,
                    "image_score": s.image_score,
                    "image_retries": s.image_retries,
                    "passed_image_qc": s.passed_image_qc,
                    "video_prompt": s.video_prompt,
                    "video_path": s.video_path,
                    "video_score": s.video_score,
                    "video_retries": s.video_retries,
                    "passed_video_qc": s.passed_video_qc,
                }
                for s in self.scenes
            ],
            "elapsed_seconds": round(time.time() - self._start_time, 1),
        }

        report_path = self.work_dir / "pipeline_report.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

        # 保存生成记录
        save_record("pipeline", self._user_request, str(report_path),
                    scenes=len(self.scenes),
                    elapsed_seconds=round(time.time() - self._start_time, 1))

        return report_path

    def _build_result(self, report_path) -> Dict:
        """构建返回结果"""
        videos = [s.video_path for s in self.scenes if s.video_path]
        return {
            "user_request": self._user_request,
            "scenes": self.scenes,
            "video_paths": videos,
            "work_dir": str(self.work_dir),
            "report_path": str(report_path) if report_path else None,
        }

    # ---- 输出格式 ----

    def _print_banner(self):
        print("\n" + "=" * 60)
        print("    AI 全自动视频创作流水线")
        print("=" * 60)
        print(f"  主题: {self._user_request}")
        print(f"  输出: {self.work_dir}\n")

    def _print_header(self, title):
        print("-" * 60)
        print(f"  【{title}】")
        print("-" * 60)

    def _print_progress(self, current, total, label=""):
        print(f"  [{current}/{total}] {label}")

    def _print_summary(self):
        elapsed = time.time() - self._start_time
        img_passed = sum(1 for s in self.scenes if s.passed_image_qc)
        vid_passed = sum(1 for s in self.scenes if s.passed_video_qc)
        total = len(self.scenes)

        print("\n" + "=" * 60)
        print("    流水线完成!")
        print("=" * 60)
        print(f"  总耗时: {elapsed:.1f}s ({elapsed / 60:.1f}分钟)")
        print(f"  场景: {total} 个")
        print(f"  图片质检通过: {img_passed}/{total}")
        print(f"  视频质检通过: {vid_passed}/{total}")

        if vid_passed < total:
            print(f"  ({total - vid_passed}个使用重试后的结果)")

        print(f"\n  输出文件:")
        print(f"    报告: {self.work_dir / 'pipeline_report.json'}")
        for s in self.scenes:
            if s.image_path:
                print(f"    关键帧{s.index}: {s.image_path}")
            if s.video_path:
                status = "通过" if s.passed_video_qc else "重试后"
                print(f"    场景{s.index}: {s.video_path} [{status}]")

        print("=" * 60)

    # ---- JSON 解析工具 ----

    @staticmethod
    def _parse_json_array(text: str) -> list:
        """从文本中提取 JSON 数组"""
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise RuntimeError(f"无法解析LLM返回的JSON数组:\n{text[:300]}")

    @staticmethod
    def _parse_qc_result(text: str, scene: Scene, kind: str) -> dict:
        """解析质检结果JSON，并设置对应分数"""
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                result = json.loads(match.group())
                score = result.get("score", -1)
                if kind == "image":
                    scene.image_score = score
                else:
                    scene.video_score = score
                return result
            except json.JSONDecodeError:
                pass

        # 解析失败
        if kind == "image":
            scene.image_score = -1
        else:
            scene.video_score = -1
        return {"summary": text[:100], "score": -1, "details": text}
