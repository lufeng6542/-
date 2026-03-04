# -*- coding: utf-8 -*-
"""
爆款片段分析器
分析视频逐字稿，识别爆款片段
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "utils"))
from config.settings import (
    HIGH_VALUE_WORDS, EMOTION_WORDS, ACTION_WORDS, REVERSAL_WORDS, HOOK_TEMPLATES
)


@dataclass
class ExplosionPoint:
    """爆点"""
    start_time: float
    end_time: float
    text: str
    score: int
    reasons: List[str]


class ExplosionAnalyzer:
    """爆款分析器"""

    # 分析关键词
    HIGH_VALUE_WORDS = ['万', '赚', '月入', '零成本', '免费', '简单', '倍', '收入', '利润', '财富']
    EMOTION_WORDS = ['不信', '吹牛', '关键', '最可怕', '别犹豫', '机会', '震惊', '真相', '秘密', '竟然']
    ACTION_WORDS = ['扣', '评论', '发你', '教程', '关注', '点赞', '收藏', '转发', '领取', '私信']
    REVERSAL_WORDS = ['但', '其实', '实际上', '然而', '却', '没想到', '原来']

    def __init__(self):
        self.model = None

    def load_whisper(self, model_size: str = "base"):
        """加载Whisper模型"""
        import whisper
        print(f"加载Whisper模型 ({model_size})...")
        self.model = whisper.load_model(model_size)
        print("模型加载完成")

    def transcribe(self, video_path: str, language: str = "zh") -> List[Dict]:
        """
        转写视频

        Args:
            video_path: 视频文件路径
            language: 语言代码 (zh/en)

        Returns:
            转写片段列表
        """
        if not self.model:
            self.load_whisper()

        print(f"转写视频: {Path(video_path).name}")
        result = self.model.transcribe(video_path, language=language, verbose=False)

        segments = []
        for seg in result['segments']:
            text = seg['text'].strip()
            if text and len(text) > 1:
                segments.append({
                    'start': round(seg['start'], 1),
                    'end': round(seg['end'], 1),
                    'text': text
                })

        print(f"转写完成: {len(segments)} 个片段")
        return segments

    def analyze_segment(self, text: str, position: float, total_duration: float) -> Tuple[int, List[str]]:
        """
        分析单个片段

        Args:
            text: 文本内容
            position: 片段开始时间
            total_duration: 视频总时长

        Returns:
            (评分, 原因列表)
        """
        score = 50
        reasons = []

        # 检查高价值词
        for word in self.HIGH_VALUE_WORDS:
            if word in text:
                score += 8
                reasons.append(f'高价值词"{word}"')

        # 检查情绪词
        for word in self.EMOTION_WORDS:
            if word in text:
                score += 6
                reasons.append(f'情绪触发"{word}"')

        # 检查行动引导词
        for word in self.ACTION_WORDS:
            if word in text:
                score += 10
                reasons.append(f'行动引导"{word}"')

        # 检查数字
        numbers = re.findall(r'\d+[万千百]?[万亿]?', text)
        if numbers:
            score += 7
            reasons.append(f'具体数字"{"".join(numbers)}"')

        # 检查反转
        for word in self.REVERSAL_WORDS:
            if word in text:
                score += 5
                reasons.append('反转结构')
                break

        # 位置加分
        if position < 3:  # 开头3秒
            score += 15
            reasons.append('开头黄金3秒')
        elif position > total_duration - 10:  # 结尾10秒
            score += 10
            reasons.append('结尾转化区')

        # 争议/冲突加分
        if '不信' in text or '吹牛' in text or '骗' in text:
            score += 5
            reasons.append('制造争议')

        # 成功案例加分
        if ('学员' in text or '朋友' in text or '粉丝' in text) and ('万' in text or '赚' in text):
            score += 10
            reasons.append('成功案例背书')

        # 强CTA加分
        if '评论' in text and ('扣' in text or '666' in text or '发' in text):
            score += 12
            reasons.append('强CTA转化点')

        return min(score, 100), reasons

    def analyze(self, segments: List[Dict]) -> List[ExplosionPoint]:
        """
        分析所有片段

        Args:
            segments: 转写片段列表

        Returns:
            爆点列表
        """
        if not segments:
            return []

        total_duration = segments[-1]['end']

        results = []
        for seg in segments:
            score, reasons = self.analyze_segment(
                seg['text'],
                seg['start'],
                total_duration
            )

            results.append(ExplosionPoint(
                start_time=seg['start'],
                end_time=seg['end'],
                text=seg['text'],
                score=score,
                reasons=reasons
            ))

        # 按分数排序
        results.sort(key=lambda x: x.score, reverse=True)
        return results

    def analyze_video(self, video_path: str) -> List[ExplosionPoint]:
        """
        分析视频（转写+分析）

        Args:
            video_path: 视频路径

        Returns:
            爆点列表
        """
        segments = self.transcribe(video_path)
        return self.analyze(segments)

    def generate_report(self, results: List[ExplosionPoint], output_path: str = None) -> str:
        """
        生成分析报告

        Args:
            results: 分析结果
            output_path: 输出路径

        Returns:
            报告文本
        """
        report = []
        report.append("=" * 60)
        report.append("爆款潜力分析报告")
        report.append("=" * 60)
        report.append("")

        # TOP片段
        report.append("【TOP 爆款片段】")
        report.append("")

        for i, seg in enumerate(results[:5], 1):
            report.append(f"{i}. [{seg.start_time}s-{seg.end_time}s] 评分:{seg.score}")
            report.append(f"   内容: {seg.text}")
            report.append(f"   理由: {' | '.join(seg.reasons) if seg.reasons else '普通过渡'}")
            report.append("")

        # 剪辑建议
        report.append("【剪辑建议】")
        report.append("")

        high_score = [r for r in results if r.score >= 80]
        mid_score = [r for r in results if 60 <= r.score < 80]

        if high_score:
            report.append("高潜力片段 (80分以上):")
            for seg in high_score:
                report.append(f"  - {seg.start_time}s-{seg.end_time}s: {seg.text[:20]}...")
            report.append("")

        if mid_score:
            report.append("中等潜力片段 (60-80分):")
            for seg in mid_score[:3]:
                report.append(f"  - {seg.start_time}s-{seg.end_time}s: {seg.text[:20]}...")
            report.append("")

        report_text = "\n".join(report)

        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(report_text)
            print(f"报告已保存: {output_path}")

        return report_text

    def save_json(self, results: List[ExplosionPoint], output_path: str):
        """保存JSON结果"""
        output = []
        for r in results:
            output.append({
                'start_time': f"{r.start_time}s",
                'end_time': f"{r.end_time}s",
                'text': r.text,
                'reason': ' | '.join(r.reasons) if r.reasons else '普通过渡',
                'score': str(r.score)
            })

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"JSON已保存: {output_path}")
