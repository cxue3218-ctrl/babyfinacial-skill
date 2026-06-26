# 宝哥科普长视频制作器

从800字脚本生成"宝哥"风格竖版科普长视频，含分镜方案、语音合成、素材采集清洗、数据可视化、贴片设计、AI运镜、合成验证、复盘报告全流程。

## 功能

- 拆句分镜 → TTS语音合成 → 素材采集（抖音/B站/YouTube/Pexels）
- AI生成视频/图片+运镜
- 数据可视化动画（Pillow逐帧渲染）
- 贴片文案条制作（暗红底+斜线纹理+金色标题）
- 分镜合成 → 全帧验证 → 最终合成
- 复盘报告输出

## 输出规格

- 1080×1920 竖版 MP4
- 时长约2分钟
- 四层结构：上贴片(384px) + 素材(768px) + 文案条(384px) + 下贴片(384px)

## 目录结构

```
baoge-video/
├── SKILL.md              # 主技能文档（完整制作流程）
├── README.md             # 本文件
├── references/           # 参考文件
│   ├── data_viz_spec.md  # 数据可视化排版规范
│   └── fast_viz_v2.py    # Pillow逐帧渲染框架代码
└── scripts/              # 辅助脚本
```

## 依赖

- ffmpeg
- yt-dlp
- Pillow
- matplotlib
- Playwright
- Windows SAPI TTS
- image_generate (MCP)

## 使用方式

1. 用户提供约800字科普脚本文案
2. 技能自动执行完整制作链路
3. 输出可发布的竖版视频
