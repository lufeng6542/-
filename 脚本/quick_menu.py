# -*- coding: utf-8 -*-
"""
海贼王剪辑项目 - 快速菜单
快速访问常用功能
"""

import os
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = Path("D:/海贼王剪辑项目")
OUTPUT_DIR = PROJECT_DIR / "输出"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    print("=" * 50)
    print("     海贼王剪辑项目 - 快速菜单")
    print("=" * 50)
    print()
def print_menu():
    print("【智能剪辑】")
    print("  1. 自动剪辑流程 (分割→人声分离→选择BGM→合成)")
    print("  2. 爆款片段分析 (转写→爆点识别→剪辑建议)")
    print()
    print("【常用功能】")
    print("  3. 分割视频素材")
    print("  4. 合成选中片段")
    print("  5. 替换BGM")
    print("  6. 转为抖音竖屏")
    print("  7. 人声分离+BGM替换")
    print()
    print("【查看结果】")
    print("  8. 查看输出文件")
    print("  9. 打开输出文件夹")
    print()
    print("  0. 退出")
    print()
def run_script(script_name, args=[]):
    script_path = PROJECT_DIR / "脚本" / script_name
    cmd = [sys.executable, str(script_path)] + args
    subprocess.run(cmd)
def list_output_files():
    print("\n【输出文件列表】")
    print("-" * 50)
    if OUTPUT_DIR.exists():
        for f in sorted(OUTPUT_DIR.glob("*.mp4")):
            size = f.stat().st_size / (1024 * 1024)
            print(f"  {f.name} ({size:.1f} MB)")
    else:
        print("  输出目录不存在")
    print("-" * 50)
def open_output_folder():
    output_path = str(OUTPUT_DIR)
    if os.name == 'nt':
        os.system(f'explorer "{output_path}"')
    elif os.name == 'darwin':
        os.system(f'open "{output_path}"')
    else:
        os.system(f'xdg-open "{output_path}"')
    print(f"\n已打开: {output_path}")
def main():
    while True:
        clear_screen()
        print_header()
        print_menu()
        choice = input("请选择功能 [0-9]: ").strip()
        if choice == '0':
            print("\n再见!")
            break
        elif choice == '1':
            print("\n启动自动剪辑流程...")
            run_script("auto_editor.py")
        elif choice == '2':
            print("\n爆款片段分析...")
            video = input("输入视频路径: ").strip()
            if video:
                run_script("explosion_analyzer.py", [video])
        elif choice == '3':
            duration = input("输入片段时长(秒, 默认4): ").strip() or "4"
            print("\n正在分割视频...")
            run_script("split_video.py", [duration])
        elif choice == '4':
            print("\n正在合成视频...")
            run_script("ai_editor.py")
        elif choice == '5':
            print("\n替换BGM功能...")
            video = input("输入视频路径: ").strip()
            bgm = input("输入BGM路径: ").strip()
            if video and bgm:
                run_script("ai_editor.py", ["replace_bgm", video, bgm])
        elif choice == '6':
            print("\n转为抖音竖屏...")
            video = input("输入视频路径: ").strip()
            if video:
                run_script("ai_editor.py", ["vertical", video])
        elif choice == '7':
            print("\n人声分离+BGM替换...")
            run_script("simple_vocal_extract.py")
        elif choice == '8':
            list_output_files()
        elif choice == '9':
            open_output_folder()
        else:
            print("\n无效选择，请重试")
        if choice != '0':
            input("\n按回车键继续...")
if __name__ == "__main__":
    main()
