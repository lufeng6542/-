# -*- coding: utf-8 -*-
"""
自动剪辑器
完整流程：素材选择 -> 视频分割 -> 人声分离 -> BGM选择 -> 视频合成
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "core"))
sys.path.insert(0, str(PROJECT_ROOT / "utils"))
sys.path.insert(0, str(PROJECT_ROOT / "config"))

from core.video_splitter import VideoSplitter
from core.vocal_separator import VocalSeparator
from core.video_editor import VideoEditor
from config.settings import PROJECT_DIR, OUTPUT_DIR, BGM_DIR, MATERIAL_DIR


class AutoEditor:
    """自动剪辑器"""

    def __init__(self):
        self.splitter = VideoSplitter()
        self.separator = VocalSeparator()
        self.editor = VideoEditor()

        self.current_material = None
        self.segments = []
        self.vocal_files = {}
        self.selected_bgm = None
        self.selected_segments = []

    def run(self):
        """运行完整流程"""
        print("\n" + "=" * 60)
        print("    海贼王剪辑 - 自动剪辑流程")
        print("=" * 60)

        try:
            # 步骤1: 选择素材
            if not self.step_select_material():
                return

            # 步骤2: 视频分割
            if not self.step_split_video():
                return

            # 步骤3: 人声分离
            if not self.step_separate_vocals():
                return

            # 步骤4: 选择BGM
            if not self.step_select_bgm():
                return

            # 步骤5: 选择片段
            if not self.step_select_segments():
                return

            # 步骤6: 视频合成
            self.step_edit_video()

            print("\n" + "=" * 60)
            print("    剪辑完成!")
            print("=" * 60)

        except KeyboardInterrupt:
            print("\n\n[取消] 用户中断操作")
        except Exception as e:
            print(f"\n[错误] {e}")

    def step_select_material(self) -> bool:
        """步骤1: 选择素材"""
        print("\n【步骤1】选择素材")
        print("-" * 40)

        # 扫描素材目录
        materials = self._scan_materials()

        if not materials:
            print("\n[提示] 素材目录为空，请手动输入路径")
            print(f"素材目录: {MATERIAL_DIR}")

            custom_path = input("\n输入视频路径 (或回车退出): ").strip()
            if not custom_path:
                return False

            custom_path = Path(custom_path)
            if custom_path.exists():
                self.current_material = custom_path
                return True
            else:
                print(f"[错误] 文件不存在: {custom_path}")
                return False

        # 显示可用素材
        print("\n可用素材:")
        for i, m in enumerate(materials, 1):
            size = m.stat().st_size / (1024 * 1024)
            print(f"  {i}. {m.name} ({size:.1f} MB)")

        print(f"  0. 手动输入路径")
        print(f"  q. 退出")

        choice = input("\n选择素材 (输入编号): ").strip().lower()

        if choice == 'q':
            return False
        elif choice == '0':
            custom_path = input("输入视频路径: ").strip()
            custom_path = Path(custom_path)
            if custom_path.exists():
                self.current_material = custom_path
                return True
            else:
                print(f"[错误] 文件不存在")
                return False
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(materials):
                    self.current_material = materials[idx]
                    print(f"\n[选择] {self.current_material.name}")
                    return True
            except ValueError:
                pass

            print("[错误] 无效选择")
            return False

    def step_split_video(self) -> bool:
        """步骤2: 分割视频"""
        print("\n【步骤2】视频分割")
        print("-" * 40)
        print(f"素材: {self.current_material.name}")

        # 获取分割时长
        duration_input = input("分割时长 (秒, 默认4): ").strip()
        duration = int(duration_input) if duration_input.isdigit() else 4

        print(f"\n正在分割 (每段{duration}秒)...")

        segment_results = self.splitter.split_by_duration(
            self.current_material,
            duration
        )

        if not segment_results:
            print("[错误] 分割失败")
            return False

        # 提取路径
        self.segments = [seg.path for seg in segment_results]

        print(f"\n[完成] 生成 {len(self.segments)} 个片段:")
        for i, seg in enumerate(self.segments, 1):
            print(f"  {i}. {seg.name}")

        return True

    def step_separate_vocals(self) -> bool:
        """步骤3: 人声分离"""
        print("\n【步骤3】人声分离")
        print("-" * 40)
        print("这将去除原视频的BGM，保留人声")

        choice = input("是否进行人声分离? (y/n, 默认y): ").strip().lower()

        if choice == 'n':
            print("[跳过] 不进行人声分离")
            return True

        print("\n正在分离人声...")

        output_dir = OUTPUT_DIR / "vocals"
        output_dir.mkdir(parents=True, exist_ok=True)

        for i, seg in enumerate(self.segments, 1):
            print(f"\n  [{i}/{len(self.segments)}] 处理: {seg.name}")

            result = self.separator.separate(seg, output_dir)

            if result:
                self.vocal_files[str(seg)] = {
                    'vocals': result.vocals,
                    'instrumental': result.instrumental
                }
                print(f"    [完成] 人声: {result.vocals.name}")
            else:
                print(f"    [警告] 分离失败，将使用原音频")

        print(f"\n[完成] 人声分离完成")
        return True

    def step_select_bgm(self) -> bool:
        """步骤4: 选择BGM"""
        print("\n【步骤4】选择BGM")
        print("-" * 40)

        # 扫描BGM目录
        bgms = self._scan_bgms()

        if not bgms:
            print("\n[提示] BGM目录为空，请手动输入路径")
            print(f"BGM目录: {BGM_DIR}")

            custom_path = input("\n输入BGM路径 (或回车退出): ").strip()
            if not custom_path:
                return False

            custom_path = Path(custom_path)
            if custom_path.exists() and custom_path.suffix in ['.mp3', '.wav', '.m4a', '.flac']:
                self.selected_bgm = custom_path
                return True
            else:
                print("[错误] 文件不存在或格式不支持")
                return False

        # 显示可用BGM
        print("\n可用BGM:")
        for i, bgm in enumerate(bgms, 1):
            print(f"  {i}. {bgm.name}")

        print(f"  0. 手动输入路径")
        print(f"  q. 退出")

        choice = input("\n选择BGM (输入编号): ").strip().lower()

        if choice == 'q':
            return False
        elif choice == '0':
            custom_path = input("输入BGM路径: ").strip()
            custom_path = Path(custom_path)
            if custom_path.exists():
                self.selected_bgm = custom_path
                print(f"\n[选择] {self.selected_bgm.name}")
                return True
            else:
                print("[错误] 文件不存在")
                return False
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(bgms):
                    self.selected_bgm = bgms[idx]
                    print(f"\n[选择] {self.selected_bgm.name}")
                    return True
            except ValueError:
                pass

            print("[错误] 无效选择")
            return False

    def step_select_segments(self) -> bool:
        """步骤5: 选择片段"""
        print("\n【步骤5】选择片段")
        print("-" * 40)
        print("可用片段:")

        for i, seg in enumerate(self.segments, 1):
            print(f"  {i}. {seg.name}")

        print("\n选择方式:")
        print("  a. 全部使用")
        print("  1,3,5. 使用指定片段 (逗号分隔)")
        print("  1-5. 使用范围片段")
        print("  q. 退出")

        choice = input("\n选择片段: ").strip().lower()

        if choice == 'q':
            return False
        elif choice == 'a':
            self.selected_segments = self.segments
        elif '-' in choice:
            # 范围选择
            try:
                start, end = map(int, choice.split('-'))
                self.selected_segments = self.segments[start-1:end]
            except:
                print("[错误] 无效范围")
                return False
        else:
            # 指定选择
            try:
                indices = [int(x.strip()) for x in choice.split(',')]
                self.selected_segments = [self.segments[i-1] for i in indices if 0 < i <= len(self.segments)]
            except:
                print("[错误] 无效选择")
                return False

        if not self.selected_segments:
            print("[错误] 没有选择片段")
            return False

        print(f"\n[选择] {len(self.selected_segments)} 个片段:")
        for seg in self.selected_segments:
            print(f"  - {seg.name}")

        return True

    def step_edit_video(self):
        """步骤6: 视频合成"""
        print("\n【步骤6】视频合成")
        print("-" * 40)

        # 获取输出名称
        output_name = input("输出文件名 (默认: 输出): ").strip() or "输出"

        # 是否保留人声
        use_vocals = len(self.vocal_files) > 0
        if use_vocals:
            choice = input("是否保留人声? (y/n, 默认y): ").strip().lower()
            use_vocals = choice != 'n'

        # 是否转为竖屏
        vertical = input("转为竖屏? (y/n, 默认n): ").strip().lower() == 'y'

        # 输出路径
        output_path = OUTPUT_DIR / f"{output_name}.mp4"
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        print(f"\n正在合成...")
        print(f"  片段: {len(self.selected_segments)} 个")
        print(f"  BGM: {self.selected_bgm.name}")
        print(f"  人声: {'保留' if use_vocals else '不保留'}")

        # 合成视频
        result = self.editor.concat_segments(
            segments=self.selected_segments,
            bgm_path=self.selected_bgm,
            output_path=output_path,
            use_vocals=use_vocals,
            vocal_files=self.vocal_files if use_vocals else None
        )

        if result:
            # 转竖屏
            if vertical:
                vertical_path = OUTPUT_DIR / f"{output_name}_竖屏.mp4"
                result = self.editor.to_vertical(result, vertical_path)

            if result:
                size = result.stat().st_size / (1024 * 1024)
                print(f"\n[完成] 输出文件: {result}")
                print(f"        文件大小: {size:.1f} MB")

                # 打开输出目录
                open_dir = input("\n打开输出目录? (y/n): ").strip().lower()
                if open_dir == 'y':
                    os.startfile(OUTPUT_DIR)
        else:
            print("[错误] 合成失败")

    def _scan_materials(self) -> List[Path]:
        """扫描素材目录"""
        materials = []

        if MATERIAL_DIR.exists():
            for ext in ['.mp4', '.mkv', '.avi', '.mov', '.flv']:
                materials.extend(MATERIAL_DIR.glob(f"*{ext}"))

        return sorted(materials, key=lambda x: x.stat().st_mtime, reverse=True)

    def _scan_bgms(self) -> List[Path]:
        """扫描BGM目录"""
        bgms = []

        if BGM_DIR.exists():
            for ext in ['.mp3', '.wav', '.m4a', '.flac', '.ogg']:
                bgms.extend(BGM_DIR.glob(f"*{ext}"))

        return sorted(bgms, key=lambda x: x.stat().st_mtime, reverse=True)


def main():
    editor = AutoEditor()
    editor.run()


if __name__ == "__main__":
    main()
