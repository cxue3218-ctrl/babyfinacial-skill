---
name: baoge-video
description: >-
  生成"宝哥"风格科普长视频。当用户说"给我一个宝哥"、"来一个宝哥"、"宝哥视频"时触发。
  用户提供约800字脚本文案，技能负责从分镜方案到最终视频的全流程：拆句分镜、TTS语音合成、
  素材采集清洗、数据可视化动画、贴片文案条设计、AI图片运镜、分镜合成、全帧验证、最终合成、复盘报告。
  不覆盖选题策划和脚本撰写。输出1080×1920竖版MP4，时长约2分钟。
cn_name: 宝哥科普长视频制作器
cn_description: 从800字脚本生成"宝哥"风格竖版科普长视频，含分镜方案、语音合成、素材采集清洗、数据可视化、贴片设计、AI运镜、合成验证、复盘报告全流程。
compatibility: ffmpeg, yt-dlp, Pillow, matplotlib, Playwright, Windows SAPI TTS, image_generate(MCP)
---

# 宝哥科普长视频制作器

## 这是什么

用户说 **"给我一个宝哥"** / **"来一个宝哥"** / **"宝哥视频"** 时触发。

用户提供一段 **约800字的科普脚本文案**（纯文字），技能负责将其变成一条可发布的竖版长视频。

- **输出**：1080×1920 竖版 MP4，约2分钟
- **输入**：约800字纯文字脚本
- **不覆盖**：选题策划、脚本撰写 — 用户直接给成品脚本，技能只负责把脚本变成视频

**完整制作链路：**
```
800字脚本 → 拆句分镜 → TTS语音 → 素材采集/生成 → 贴片文案条制作 → 分镜合成 → 全帧验证 → 最终合成 → 复盘报告
```

---

## 引用文件索引

| 文件 | 内容 |
|------|------|
| `README.md` | 项目说明（工作流程、画面结构、技术栈、快速开始） |
| `references/production-rules.md` | 导演人设、画面结构、标题样式、素材红线规则 |
| `references/storyboard-rules.md` | Phase 0：分镜方案（拆句、素材方案、标题、分镜表） |
| `references/tts-rules.md` | TTS时长估算公式、长句分幕规则 |
| `references/keyword-rules.md` | 搜索关键词规则（所有平台） |
| `references/keyword-strategy-diagram.md` | 关键词编辑策略逻辑架构图（Mermaid） |
| `references/material-collection.md` | 素材类型优先级、占比方案、平台采集流程（简版） |
| `references/platform-collection-v2.md` | 平台采集详细方案v2（抖音JS API法、B站格式ID+drawbox去水印、YouTube搜索提取、抽帧筛选） |
| `references/ai-generation.md` | AI生成素材、FFmpeg运镜 |
| `references/data-viz.md` | 数据可视化动画规则 |
| `references/post-production.md` | Phase 1-7 制作流程（TTS、贴片、合成、验证、复盘） |
| `references/verification.md` | 素材验收12项检查、审查机制、素材备注清单 |

---

## Phase 0：分镜方案（第一步，必须先做）

详见 `references/storyboard-rules.md`。

拿到800字脚本后，**先制定分镜方案再开始任何制作**。

### 0a. 拆句分镜
每句 = 一个分镜，用TTS时长公式估算时长，超15s必须拆分。

### 0b. 逐镜确定素材方案
确定每镜的素材类型、搜索关键词、备选方案、技术/插件、转场运镜。

### 0b-extra. 搜索关键词规则
详见 `references/keyword-rules.md`。

### 0c. 确定标题
用户提供标题，显示在上贴片。

### 0d. 输出分镜方案表
表格格式见 `references/storyboard-rules.md`。

**分镜方案完成后，直接进入制作，不等用户确认。**

---

## 画面结构（固定，不可变）

详见 `references/production-rules.md`。

```
┌─────────────────────────┐
│   上贴片 384px           │ ← 暗红#5a0510 + 斜线纹理 + 金色粗体标题
├─────────────────────────┤
│   素材画面 768px（净）    │ ← 纯净素材，零文字/水印/人脸
├─────────────────────────┤
│   文案条 384px           │ ← 暗红#5a0510 + 斜线纹理 + 白字#fff 54px
├─────────────────────────┤
│   下贴片 384px           │ ← 暗红#5a0510 + 斜线纹理（不放标题）
└─────────────────────────┘
      1080 × 1920px
```

---

## 素材红线规则（零容忍）

详见 `references/production-rules.md`。

**绝对禁止**：K线截图、PPT截图/录屏、水印、人脸、字幕/文字、无关画面。

---

## 素材类型优先级

详见 `references/material-collection.md`。

1. **平台实拍素材**（抖音→B站→YouTube）
2. **素材网站**（Pexels / Pixabay / Mixkit）
3. **AI生成视频** / AI图片+运镜
4. **数据可视化动画**

---

## 制作流程（Phase 1-7）

详见 `references/post-production.md`。

### Phase 1：TTS语音合成
Windows SAPI逐完整句合成，ffprobe实测时长验证。

### Phase 2：素材采集与生成
按分镜方案逐镜采集，详见 `references/material-collection.md`、`references/ai-generation.md`、`references/data-viz.md`。

### Phase 3：贴片与文案条制作
暗红底+斜线纹理+金色标题+白字文案。

### Phase 4：分镜合成
四层垂直拼接（上贴片+素材+文案条+下贴片），1080×1920。

### Phase 5：全帧验证
每2秒截帧，逐项检查。

### Phase 6：最终合成
视频拼接 → 音频合并 → 音视频合成。

### Phase 7：复盘报告
每次生成必须输出复盘报告。

---

## 分步审查机制

详见 `references/verification.md`。

每个Phase完成后，**必须截屏展示给用户检查**，用户确认通过后才进入下一个Phase。

---

## 素材验收12项检查

详见 `references/verification.md`。

每段素材下载/生成后全帧验证，任何一项不合格 → 整段丢弃。

---

## 技术限制说明

| 限制 | 说明 |
|------|------|
| AI生视频 | 优先尝试AI生成视频；若不可用，备选image_generate图片+FFmpeg运镜 |
| WorkRally AI生视频 | 需API Key，若已配置则优先用于AI生成视频 |
| TTS | Windows SAPI，中文仅Huihui声音，语速可调，无法换声音 |
| 性能 | FFmpeg编码是主要耗时环节 |

---

## v5违规问题清单（制作时必须逐项避免）

| 序号 | v5违规项 | 正确做法 |
|------|----------|----------|
| 1 | city_night素材含"SHANGHAI $600 BILLION"水印 | 素材采集后必须逐帧检查水印 |
| 2 | 上下贴片用纯黑底#08080c，无斜线纹理 | 贴片必须用暗红#5a0510+斜线纹理 |
| 3 | 标题字体缺块 | 不使用斜体transform，标题改为纯bold |
| 4 | ai_pole柱状图配"竹竿效应"——通用图与比喻语义不符 | 概念比喻必须用匹配的可视化 |
| 5 | fiber.png金属拉丝图配"光纤光棒"——语义错误 | 素材必须与文案直接语义匹配 |
| 6 | 长句拆成63个独立TTS，语音断续 | 长句必须整句TTS+字幕轮播 |
| 7 | 数据镜全部用静态AI图，无数据可视化动画 | 数据/概念镜必须用Pillow/matplotlib动画 |
| 8 | 没有输出复盘报告 | 每次生成必须输出复盘报告.md |
| 9 | 分镜时长用"3字/秒"粗估，大量段落TTS超时导致音画不同步 | 必须用TTS时长公式估算，超15s必拆分，TTS生成后ffprobe实测验证 |

---

## 目录结构

```
output/
├── final.mp4                    # 最终视频
├── 复盘报告.md                   # 复盘报告（必须输出）
├── segments/
│   ├── seg_00/
│   │   ├── content.mp4          # 素材画面
│   │   ├── tts.mp3              # 整句TTS音频
│   │   ├── overlay.png          # 贴片+文案条叠加
│   │   └── final.mp4            # 合成后的单镜
│   ├── seg_01/
│   └── ...
├── tts/
│   ├── chunk_000.mp3            # 每镜一段完整句TTS
│   └── ...
├── animations/                  # 数据可视化动画
│   └── ...
└── raw_materials/               # 原始素材
    ├── pexels/
    ├── youtube/
    ├── ai_generated/
    └── animations/
```
