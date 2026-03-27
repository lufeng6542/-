# 视频创作工具

AI视频生成 + AI图片生成 + 视频剪辑一站式工具

## 快速开始

```bash
# 查看所有命令
python cli.py

# 剪辑
python cli.py split -i 视频.mp4 -d 4
python cli.py edit -i 片段目录 -b BGM.mp3

# AI生成
python cli.py gen image "一只猫" --ar 16:9
python cli.py gen video "海浪拍打沙滩" --auto-verify
python cli.py gen img2video 首帧.png "猫咪奔跑" --ar 9:16
```

## 命令一览

| 命令 | 说明 |
|------|------|
| `split` | 分割视频素材 |
| `separate` | 人声分离 |
| `edit` | 视频编辑合成 |
| `analyze` | 爆点分析 |
| `auto` | 自动剪辑流程 |
| `gen image` | AI生成图片（CogView-4） |
| `gen video` | AI生成视频（CogVideoX-3） |
| `gen img2video` | 图片转视频 |
| `verify` | 视频质量验证 |
| `task-status` | 查询AI生成任务状态 |

## API Key 配置

编辑 `~/.baoyu-skills/.env`：
```
ZHIPU_API_KEY=你的密钥
```
