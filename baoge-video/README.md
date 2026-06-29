# 宝哥科普长视频制作器 🎬

> 从800字脚本 → 一条可发布的竖版科普长视频

## 这是什么

**宝哥科普长视频制作器** 是一个 AI 驱动的视频制作工具。你只需要提供一段 **约800字的科普脚本文案**，它就能自动完成从分镜方案到最终视频的全流程：

```
800字脚本 → 拆句分镜 → TTS语音合成 → 素材采集/生成 → 贴片文案条制作 → 分镜合成 → 全帧验证 → 最终合成 → 复盘报告
```

- **输出**：1080×1920 竖版 MP4，约2分钟
- **输入**：约800字纯文字脚本
- **不覆盖**：选题策划、脚本撰写（用户直接给成品脚本）

## 工作流程

```mermaid
graph LR
    A[用户提供脚本] --> B[Phase 0: 分镜方案]
    B --> C[Phase 1: TTS语音]
    C --> D[Phase 2: 素材采集/生成]
    D --> E[Phase 3: 贴片与文案条]
    E --> F[Phase 4: 分镜合成]
    F --> G[Phase 5: 全帧验证]
    G --> H[Phase 6: 最终合成]
    H --> I[Phase 7: 复盘报告]
    I --> J[输出MP4]
```

## 素材来源

| 类型 | 说明 | 占比 |
|------|------|------|
| 🎥 平台实拍 | 抖音/B站/YouTube 搜索下载 | ~30% |
| 🌐 素材网站 | Pexels / Pixabay / Mixkit 免费素材 | ~30% |
| 🤖 AI生成 | AI视频 / AI图片+运镜 | ~35% |
| 📊 数据可视化 | Pillow逐帧动画 | 含在AI生成中 |

## 画面结构

```
┌─────────────────────────┐
│   上贴片 384px           │ 暗红底+斜线纹理+金色标题
├─────────────────────────┤
│   素材画面 768px（净）    │ 纯净素材，零文字/水印/人脸
├─────────────────────────┤
│   文案条 384px           │ 暗红底+斜线纹理+白字
├─────────────────────────┤
│   下贴片 384px           │ 暗红底+斜线纹理
└─────────────────────────┘
      1080 × 1920px
```

## 仓库结构

```
baoge-video/
├── SKILL.md                    # 主入口：流程骨架 + 引用索引
├── README.md                   # 本文件：项目说明
├── references/                 # 详细规则文档（按主题拆分）
│   ├── production-rules.md     # 导演人设、画面结构、标题样式、素材红线
│   ├── storyboard-rules.md     # 分镜方案规则
│   ├── tts-rules.md            # TTS时长估算、长句分幕
│   ├── keyword-rules.md        # 搜索关键词规则
│   ├── material-collection.md  # 素材类型优先级、平台采集流程
│   ├── ai-generation.md        # AI生成素材、FFmpeg运镜
│   ├── data-viz.md             # 数据可视化动画
│   ├── post-production.md      # 制作流程（Phase 1-7）
│   └── verification.md         # 素材验收、审查机制
├── scripts/                    # 代码脚本
│   ├── stock_downloader_v3.py  # 素材采集工具
│   ├── fast_viz_v2.py          # 数据可视化框架
│   └── tts_script.py           # TTS语音合成
└── engine.py                   # 渲染引擎
```

## 技术栈

| 技术 | 用途 |
|------|------|
| FFmpeg | 视频裁剪、合成、编码 |
| yt-dlp | 平台视频下载 |
| Playwright | 浏览器自动化（搜索、提取URL） |
| Pillow | 数据可视化逐帧渲染 |
| Windows SAPI | TTS语音合成 |
| curl_cffi | 素材网站反爬绕过 |
| image_generate (MCP) | AI图片生成 |

## 兼容性

- **操作系统**：Windows（TTS依赖SAPI）
- **依赖**：ffmpeg, yt-dlp, Pillow, matplotlib, Playwright, curl_cffi
- **AI工具**：image_generate (MCP 工具)

## 快速开始

1. 准备约800字科普脚本文案
2. 触发技能：说"给我一个宝哥"或"来一个宝哥"
3. 技能自动完成分镜方案 → TTS → 素材采集 → 合成 → 验证 → 输出

---

> 由 [宝哥仓库](https://github.com/cxue3218-ctrl/babyfinacial-skill) 提供
