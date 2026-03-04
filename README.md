# 海贼王剪辑项目

> 基于 Whisper 的智能视频剪辑工具
> 使用 MDX23C 模型进行高质量人声分离

## 项目结构

```
D:/海贼王剪辑项目/
├── config/                  # 配置文件
│   └── settings.py
├── core/                   # 核心功能模块
│   ├── __init__.py
│   ├── video_splitter.py     # 视频分割
│   ├── vocal_separator.py    # 人声分离
│   ├── explosion_analyzer.py  # 爆款分析
│   └── video_editor.py        # 视频编辑
├── utils/                   # 工具模块
│   ├── __init__.py
│   └── ffmpeg_utils.py
├── scripts/               # 独立脚本 (兼容旧版)
│   ├── auto_editor.py
│   ├── explosion_analyzer.py
│   ├── quick_menu.py
│   └── ...
├── cli.py                  # 统一命令行入口
├── requirements.txt
└── README.md
```

---

## 快速开始

```bash
# 方式1: 使用快速菜单
python D:/海贼王剪辑项目/cli.py

# 方式2: 使用命令行
python D:/海贼王剪辑项目/cli.py split --input 视频.mp4 --duration 4
python D:/海贼王剪辑项目/cli.py edit --input 片段目录 --bgm BGM.mp3

python D:/海贼王剪辑项目/cli.py analyze --input 视频.mp4

# 方式3: 从Python直接调用
from core import VideoSplitter, VocalSeparator, ExplosionAnalyzer, VideoEditor

```

---

## 核心模块说明

### VideoSplitter - 视频分割
```python
splitter = VideoSplitter()
segments = splitter.split_by_duration("视频.mp4", 4)  # 4秒一段
```

### VocalSeparator - 人声分离
```python
separator = VocalSeparator()
result = separator.separate("视频.mp4", "输出目录")
# result.vocals    # 人声
# result.instrumental  # 伴奏
```

### ExplosionAnalyzer - 爆款分析
```python
analyzer = ExplosionAnalyzer()
points = analyzer.analyze_video("视频.mp4")
# 按评分排序的爆点列表
```

### VideoEditor - 视频编辑
```python
editor = VideoEditor()
output = editor.concat_segments(
    segments=["片段1.mp4", "片段2.mp4"],
    bgm_path="BGM.mp3",
    output_path="输出.mp4"
)
```

---

## 配置说明

编辑 `config/settings.py` 修改:
- 项目路径
- 视频参数
- 平台配置
- 分析关键词

---

## 剪辑大师 - 高燃卡点工作流

### 快速启动
```bash
python scripts/clip_master.py
```

### 功能特性
- 自动素材分析
- 智能剪辑方案生成
- 节奏配乐匹配
- 抖音算法优化

### 剪辑标准
- 开场3秒强钩子
- 每3秒一个视觉爆点
- 高潮连续上升
- 大招收尾

### 输出格式
- 分辨率: 1080×1920 (竖屏)
- 时长: 15-30秒
- 编码: H.264 / AAC

---

## 项目技能

输入 **"剪辑大师"** 自动激活高燃剪辑工作流

技能文件: `.claude/skills/剪辑大师/skill.md`
