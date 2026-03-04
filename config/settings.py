# -*- coding: utf-8 -*-
"""
项目配置文件
统一管理所有路径和参数
"""

from pathlib import Path

# ============ 项目路径 ============
PROJECT_DIR = Path("D:/海贼王剪辑项目")
MATERIAL_DIR = PROJECT_DIR / "素材"
SEGMENTS_DIR = PROJECT_DIR / "素材片段"
BGM_DIR = PROJECT_DIR / "BGM"
OUTPUT_DIR = PROJECT_DIR / "输出"
SEPARATED_DIR = PROJECT_DIR / "分离音频"
SCRIPTS_DIR = PROJECT_DIR / "脚本"
MODELS_DIR = PROJECT_DIR / "models"
TEST_DIR = PROJECT_DIR / "测试素材"

# ============ 模型路径 ============
MDX23C_MODEL = MODELS_DIR / "mdx23c" / "MDX23C-8KFFT-InstVoc_HQ.ckpt"

# ============ 视频参数 ============
VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920  # 抖音竖屏
FPS = 30
SEGMENT_DURATION = 4  # 默认片段时长(秒)

# ============ 分析参数 ============
# 爆款分析关键词
HIGH_VALUE_WORDS = ['万', '赚', '月入', '零成本', '免费', '简单', '倍', '收入', '利润', '财富']
EMOTION_WORDS = ['不信', '吹牛', '关键', '最可怕', '别犹豫', '机会', '震惊', '真相', '秘密', '竟然']
ACTION_WORDS = ['扣', '评论', '发你', '教程', '关注', '点赞', '收藏', '转发', '领取', '私信']
REVERSAL_WORDS = ['但', '其实', '实际上', '然而', '却', '没想到', '原来']

# ============ 开头钩子模板 ============
HOOK_TEMPLATES = {
    "数字冲击型": [
        "这个月我又靠这个方法赚了12万",
        "3天涨粉5000",
        "这2个方法让我副业收入翻倍",
        "只用7天，粉丝从0到1万",
    ],
    "行动召唤型": [
        "评论区扣666",
        "点赞收藏不迷路",
        "关注我教你",
        "私信我发你",
        "链接在简介",
        "下期预告",
    ],
    "反转悬念型": [
        "很多人不信，但学员已经做到了",
        "你本来以为...直到",
        "你以为很简单？",
        "说出了很多人的心声",
        "你并不孤单",
    ],
}

# ============ 平台参数 ============
PLATFORM_CONFIG = {
    "douyin": {
        "name": "抖音",
        "max_duration": 60,  # 秒
        "resolution": (1080, 1920),
        "style": "热血燃向",
        "tips": ["高潮战斗片段", "卡点BGM", "快节奏切换"],
    },
    "bilibili": {
        "name": "B站",
        "max_duration": 600,  # 10分钟
        "resolution": (1920, 1080),
        "style": "剧情解说/混剪",
        "tips": ["完整剧情线", "粉丝向内容", "弹幕互动"],
    },
    "xiaohongshu": {
        "name": "小红书",
        "max_duration": 90,  # 秒
        "resolution": (1080, 1440),
        "style": "角色安利/剧情分析",
        "tips": ["情感共鸣", "精美封面", "详细文案"],
    },
}

# ============ 支持的视频格式 ============
VIDEO_EXTENSIONS = ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg']
