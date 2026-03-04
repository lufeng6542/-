# -*- coding: utf-8 -*-
"""
迁移脚本
将旧脚本迁移到新模块结构
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
OLD_SCRIPTS = PROJECT_ROOT / "scripts"
NEW_CORE = PROJECT_ROOT / "core"
NEW_UTILS = PROJECT_ROOT / "utils"

SCRIPTS_TO_MIGRATE = {
    "split_video.py": "video_splitter",
    "vocal_separator.py": "vocal_separator",
    "explosion_analyzer.py": "explosion_analyzer",
    "ai_editor.py": "video_editor",
    "simple_vocal_extract.py": "simple_vocal_extract"
}

def create_compat_import(old_name, new_module):
    """创建兼容导入文件"""
    try:
        old_script = OLD_SCRIPTS / old_name
        new_module_path = NEW_CORE / f"{new_module}.py"

        if not new_module_path.exists():
            print(f"  [跳过] {old_name} (新模块不存在)")
            return False

        compat_content = f'''# -*- coding: utf-8 -*-
"""
兼容导入 - 自动生成
此文件允许旧代码继续使用旧导入路径
"""
from core.{new_module} import *
'''

        with open(old_script, 'w', encoding='utf-8') as f:
            f.write(compat_content)

        print(f"  [完成] {old_name} -> core.{new_module}")
        return True
    except Exception as e:
        print(f"  [错误] {old_name}: {e}")
        return False


def main():
    print("=" * 60)
    print("脚本迁移工具")
    print("=" * 60)
    print("\n正在迁移旧脚本...")
    print(f"旧脚本目录: {OLD_SCRIPTS}")
    print(f"新模块目录: {NEW_CORE}")
    print()

    success_count = 0
    for old_name in SCRIPTS_TO_MIGRATE:
        if create_compat_import(old_name, SCRIPTS_TO_MIGRATE[old_name]):
            success_count += 1

    print("\n" + "=" * 60)
    print(f"迁移完成! 成功: {success_count}/{len(SCRIPTS_TO_MIGRATE)}")
    print("=" * 60)
    print("\n现在可以使用:")
    print("  from core import VideoSplitter, VocalSeparator, ExplosionAnalyzer, VideoEditor")


    print("\n运行: python cli.py")


if __name__ == "__main__":
    main()
