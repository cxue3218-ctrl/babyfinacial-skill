# 视频素材采集方案文档 v2

## 一、总览

本文档覆盖三个平台的视频素材采集全流程：**抖音**（中文实拍素材）、**YouTube**（英文/无版权素材）和 **B站**（中文演讲/科技素材）。所有采集的素材统一输出 **16:9 横版原版**，不裁剪为竖版。

### 素材验收标准（6项）

| 序号 | 标准 | 判定 |
|------|------|------|
| 1 | 无人脸 | 有→淘汰 |
| 2 | 无水印 | 有→淘汰 |
| 3 | 字体文字 | 几乎没有→合格（角落logo/零散数字可crop截掉或马赛克）；大量字体→淘汰 |
| 4 | 画面与文案语义匹配 | 不匹配→淘汰 |
| 5 | 画面动感（稍微动一下也行） | 纯静态图片→淘汰 |
| 6 | 分辨率 720p+ | 不达标→淘汰 |

### 通用规范

- **每次只下载 3 个视频**（不贪多），看完抽帧结果再决定要不要补
- **统一 16:9 横版**，保持原比例不裁剪
- **拼接策略**：2个不同来源视频各截几秒，秒数按分镜镜头所需而定
- **统一 1080p / 30fps** 输出

---

## 二、抖音采集方案

### 2.1 方案演进

| 版本 | 方案 | 状态 | 原因 |
|------|------|------|------|
| v1 | Playwright网络请求拦截 | ❌ 弃用 | 游标/签名失效，反复拿到旧视频 |
| v2 | yt-dlp抖音extractor | ❌ 弃用 | cookie报错，抖音extractor有bug |
| v3 | **Playwright内JS调抖音API拿真实URL + FFmpeg下载** | ✅ 最终方案 | 绕过签名问题，稳定可用 |

### 2.2 最终方案流程（JS API法）

```
步骤1: Playwright打开抖音搜索页（需已登录）
步骤2: browser_evaluate 执行JS → 调抖音搜索API，获取视频列表（aweme_id + 标题 + 作者）
步骤3: 对每个视频，browser_evaluate 执行JS → 调视频详情API，拿到真实下载URL（douyinvod.com域名）
步骤4: 保存视频列表为 video_urls.json
步骤5: Python + FFmpeg 下载视频（带Referer头）
步骤6: Python 抽帧筛选
步骤7: 选定最佳素材后，FFmpeg 切割所需段落
```

### 2.3 关键技术点

1. **JS大整数精度丢失**：抖音视频ID（aweme_id）是大整数，在JS中会精度丢失。必须用字符串方式处理，不能直接做数值运算
2. **下载URL时效性**：douyinvod.com 的URL有时效（约几小时），获取后需尽快下载
3. **Referer头必须**：FFmpeg下载时必须带 `Referer: https://www.douyin.com/`，否则403
4. **弹窗模式URL不变**：抖音PC网页版搜索页点击视频是弹窗播放，地址栏URL始终是搜索页URL
5. **编码回退**：`-c copy` 失败时回退到 `-c:v libx264 -c:a aac` 重新编码

### 2.4 抖音JS API代码

在 Playwright 的 `browser_evaluate` 中执行以下JS：

**搜索API调用（获取视频列表）：**

```javascript
() => {
  // 抖音搜索API：在已登录的抖音页面上下文中调用
  // 注意：aweme_id 必须用字符串处理，避免大整数精度丢失
  const results = [];
  // 通过页面已有的 fetch/XHR 拦截或直接调用搜索接口
  // 搜索结果包含：aweme_id, desc(标题), author.nickname, duration
  // 实际执行时由 Playwright 在抖音页面上下文中运行
  return JSON.stringify(results);
}
```

> 实际执行时，JS代码在已登录的抖音页面上下文中运行，利用页面已有的cookie和签名机制调用API。搜索结果保存为 `video_urls.json`，包含字段：`id`（aweme_id）, `author`, `desc`, `dur`, `url`（真实下载URL）。

**video_urls.json 数据结构示例：**

```json
[
  {
    "id": "7580567492326690098",
    "author": "landspace",
    "desc": "朱雀三号首飞",
    "dur": 210,
    "url": "https://v11-weba.douyinvod.com/.../?a=6383&ch=26&..."
  }
]
```

### 2.5 抖音下载脚本（Python + FFmpeg）

```python
# -*- coding: utf-8 -*-
"""抖音视频批量下载脚本"""
import subprocess, os, json

with open("video_urls.json", "r", encoding="utf-8") as f:
    videos = json.load(f)

os.makedirs("raw", exist_ok=True)

for i, v in enumerate(videos):
    outpath = "raw/v{:02d}_{}.mp4".format(i, v["author"])
    if os.path.exists(outpath) and os.path.getsize(outpath) > 100000:
        print("[{}] {} already exists".format(i, v["author"]))
        continue
    print("[{}] Downloading {} ({}s)...".format(i, v["author"], v["dur"]))
    # 第一优先：直接copy（快）
    cmd = ["ffmpeg", "-y",
           "-headers", "Referer: https://www.douyin.com/\r\nUser-Agent: Mozilla/5.0\r\n",
           "-i", v["url"],
           "-c", "copy", outpath]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        # 回退：重新编码
        cmd2 = ["ffmpeg", "-y", "-headers", "Referer: https://www.douyin.com/\r\n",
                "-i", v["url"], "-c:v", "libx264", "-c:a", "aac", outpath]
        r2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=180)
        if r2.returncode != 0:
            print("  FAILED: " + r2.stderr[-200:])
        else:
            print("  OK (re-enc): {}KB".format(os.path.getsize(outpath)//1024))
    else:
        print("  OK: {}KB".format(os.path.getsize(outpath)//1024))

print("All done!")
```

---

## 三、YouTube采集方案

### 3.1 方案流程

```
步骤1: Playwright打开YouTube搜索页
步骤2: browser_evaluate 提取搜索结果（视频ID + 标题 + 时长）
步骤3: browser_cookies 获取YouTube cookies（Netscape格式）
步骤4: yt-dlp 用cookies下载视频（YouTube上yt-dlp无bug）
步骤5: Python 抽帧筛选
步骤6: FFmpeg 切割所需段落
```

### 3.2 关键技术点

1. **yt-dlp在YouTube上正常工作**：与抖音不同，yt-dlp的YouTube extractor没有cookie bug，直接用cookies下载即可
2. **Cookies需要刷新**：每次下载前用 `browser_cookies` 获取最新cookies，旧cookies可能过期
3. **格式选择**：`-f "best[ext=mp4][height<=1080]"` 确保拿到1080p MP4
4. **无版权搜索词**：搜索时加 `no copyright` / `royalty free` / `free` 关键词，更容易找到无字体素材

### 3.3 Cookies转换脚本

Playwright的 `browser_cookies` 返回JSON格式，yt-dlp需要Netscape格式。转换脚本：

```python
# -*- coding: utf-8 -*-
"""YouTube JSON cookies → Netscape cookies 转换"""
import json, os, glob

# 自动找最新的cookies JSON文件
files = glob.glob("cookies_.youtube.com_*.json")
latest = max(files, key=os.path.getmtime)

with open(latest, "r", encoding="utf-8") as f:
    cookies = json.load(f)

with open("youtube_cookies.txt", "w", encoding="utf-8") as f:
    f.write("# Netscape HTTP Cookie File\n")
    for c in cookies:
        domain = c.get("domain", "")
        flag = "TRUE" if domain.startswith(".") else "FALSE"
        path = c.get("path", "/")
        secure = "TRUE" if c.get("secure", False) else "FALSE"
        expires_str = c.get("expires", "")
        if expires_str:
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
                expires = int(dt.timestamp())
            except:
                expires = 0
        else:
            expires = 0
        name = c.get("name", "")
        value = c.get("value", "")
        f.write(f"{domain}\t{flag}\t{path}\t{secure}\t{expires}\t{name}\t{value}\n")

print(f"Converted {len(cookies)} cookies")
```

### 3.4 YouTube下载命令

```powershell
# 刷新cookies
# Playwright MCP: browser_cookies → domain=".youtube.com"

# 转换cookies格式
& python convert_cookies.py

# 下载视频（每次最多3个）
& yt-dlp --cookies youtube_cookies.txt `
    -f "best[ext=mp4][height<=1080]" `
    -o "finance_01.mp4" `
    "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 3.5 YouTube搜索结果提取JS

在 Playwright 的 `browser_evaluate` 中执行：

```javascript
() => {
  const results = [];
  const seen = new Set();
  const items = document.querySelectorAll('ytd-video-renderer');
  for (const item of items) {
    const link = item.querySelector('a#video-title');
    if (!link) continue;
    const href = link.getAttribute('href') || '';
    const m = href.match(/watch\?v=([\w-]+)/);
    if (!m) continue;
    const vid = m[1];
    if (seen.has(vid)) continue;
    seen.add(vid);
    const title = link.textContent.trim();
    const durEl = item.querySelector('#text');
    const dur = durEl ? durEl.textContent.trim() : '';
    results.push({vid, title, dur});
    if (results.length >= 8) break;
  }
  return JSON.stringify(results);
}
```

---

## 四、B站采集方案

### 4.1 方案流程

```
步骤1: Playwright打开B站搜索页（需已登录）
步骤2: browser_snapshot 获取搜索结果（BV号 + 标题 + UP主 + 时长 + 播放量）
步骤3: 选定3个候选视频，进入视频页
步骤4: browser_cookies 获取B站cookies（.bilibili.com域名）
步骤5: Python转换cookies为Netscape格式（注意BOM编码问题）
步骤6: yt-dlp用cookies下载（视频音频分离，需指定格式ID合并）
步骤7: Python抽帧筛选
步骤8: FFmpeg切割 + drawbox去水印/字幕
步骤9: 抽帧验证处理效果，确保无文字
```

### 4.2 关键技术点

1. **yt-dlp在B站正常工作**：与抖音不同，yt-dlp的B站extractor没有cookie bug，用cookies下载即可
2. **视频音频分离**：B站1080p视频流和音频流是分开的（DASH格式），必须用 `-f "30080+30280"` 指定视频流+音频流，再用 `--merge-output-format mp4` 合并。不能用通用的 `best[ext=mp4]`，否则只有视频没有声音
3. **Cookies需要刷新**：每次下载前用 `browser_cookies` 获取最新cookies，旧cookies会返回412 Precondition Failed
4. **Cookie文件BOM问题**：PowerShell默认用UTF-8 with BOM写文件，yt-dlp不认BOM头。必须用 `[System.IO.File]::WriteAllLines()` + ASCII编码写入，否则报 `does not look like a Netscape format cookies file`
5. **User-Agent必须**：下载时需带与浏览器一致的User-Agent，否则可能被拦截
6. **优先选官方账号**：NVIDIA英伟达官方账号(space.bilibili.com/1320140761)的视频只有右上角"英伟达GeForce bilibili"水印+底部字幕，无中部@水印。第三方UP主视频常有中部@账号水印，位置居中无法drawbox去除

### 4.3 B站搜索结果提取

在Playwright中导航到B站搜索页后，用 `browser_snapshot` 获取页面快照，从快照中提取视频信息：

```
搜索URL格式：
https://search.bilibili.com/all?keyword=关键词&order=click&duration=4

参数说明：
- keyword: 搜索关键词（URL编码）
- order=click: 按播放量排序
- duration=4: 10分钟以上（筛选长视频，演讲/发布会类）

快照中提取字段：
- BV号: href中的 /video/BVxxxxxx/
- 标题: heading或img alt
- UP主: span文本
- 播放量: span文本（如"158.3万"）
- 时长: span文本（如"02:18:56"）
```

### 4.4 B站Cookies转换脚本

```python
# -*- coding: utf-8 -*-
"""B站 JSON cookies → Netscape cookies 转换"""
import json, os, glob

# 自动找最新的cookies JSON文件
files = glob.glob("cookies_.bilibili.com_*.json")
if not files:
    print("ERROR: No cookie file found")
    exit(1)
latest = max(files, key=os.path.getmtime)

with open(latest, "r", encoding="utf-8") as f:
    cookies = json.load(f)

lines = ["# Netscape HTTP Cookie File", "# This is a generated file! Do not edit.", ""]

for c in cookies:
    domain = c.get("domain", "")
    flag = "TRUE" if domain.startswith(".") else "FALSE"
    path = c.get("path", "/")
    secure = "TRUE" if c.get("secure", False) else "FALSE"
    expiry = c.get("expiry", 0)
    if expiry:
        expiry = int(float(expiry))
    else:
        expiry = 0
    name = c.get("name", "")
    value = c.get("value", "")
    lines.append(f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}")

# 用ASCII编码写入，避免BOM问题
with open("bilibili_cookies.txt", "w", encoding="ascii") as f:
    f.write("\n".join(lines) + "\n")

print(f"Converted {len(cookies)} cookies → bilibili_cookies.txt")
```

### 4.5 B站下载命令

```powershell
# 刷新cookies
# Playwright MCP: browser_cookies → domain=".bilibili.com"

# 转换cookies格式（注意：必须用ASCII编码，不能有BOM）
& python convert_bilibili_cookies.py

# 下载视频（每次最多3个）
# 关键：B站视频音频分离，必须指定格式ID合并
& yt-dlp --cookies bilibili_cookies.txt `
    --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36" `
    -f "30080+30280" `
    --merge-output-format mp4 `
    -o "nv_01.mp4" `
    "https://www.bilibili.com/video/BV1AbwSzeEKD/"
```

> **格式ID说明**：
> - `30080` = 1080P 高清视频流（仅视频）
> - `30280` = 高品质音频流（仅音频）
> - 用 `+` 连接表示合并，`--merge-output-format mp4` 确保输出为MP4容器
> - 如果不确定可用格式，先用 `yt-dlp -F URL --cookies bilibili_cookies.txt` 查看所有格式

### 4.6 B站去水印/字幕处理

B站视频常见的文字干扰及处理方式：

| 文字类型 | 位置 | 处理方式 | drawbox参数（1920x1080） |
|---------|------|---------|------------------------|
| UP主水印 | 右上角 | drawbox黑块覆盖 | `drawbox=x=1200:y=0:w=720:h=130:color=black:t=fill` |
| 中文字幕 | 底部 | drawbox黑块覆盖 | `drawbox=x=0:y=880:w=1920:h=200:color=black:t=fill` |
| @账号水印 | 画面中部 | **无法处理→淘汰** | 位置居中，drawbox会覆盖人脸 |
| 双语字幕 | 底部（偏高） | drawbox黑块覆盖（需加高） | `drawbox=x=0:y=880:w=1920:h=200:color=black:t=fill` |

**完整去水印命令示例：**

```powershell
# 右上角水印 + 底部字幕（官方账号常见组合）
$vf = "drawbox=x=1200:y=0:w=720:h=130:color=black:t=fill,drawbox=x=0:y=880:w=1920:h=200:color=black:t=fill"

& ffmpeg -y -ss 1590 -i nv_01.mp4 -t 20 -vf $vf -c:v libx264 -c:a aac -r 30 nv_01_clean.mp4
```

**注意事项：**
- drawbox的x/y/w/h需要根据实际水印位置调整，**抽帧后用image工具确认精确位置**
- 水印位置可能比预想的更靠中间/更低，需要逐步加大drawbox范围直到完全覆盖
- 处理后**必须再次抽帧验证**，确保所有帧都无文字
- 如果水印在画面中部（如`@账号`），drawbox会覆盖画面内容，此时应直接淘汰该视频换一个

---

## 五、抽帧筛选流程

### 5.1 抽帧规则

**开头前8秒每2秒抽帧**（0/2/4/6/8s 共5帧）+ **后面均匀抽5帧**，共10帧。

这样设计的原因：视频开头往往是片头/logo/字幕最密集的部分，需要密集检查；后面均匀抽样看整体内容。

### 5.2 抽帧脚本

```python
# -*- coding: utf-8 -*-
"""通用抽帧脚本 - 适用于抖音和YouTube下载的视频"""
import subprocess, os

vpath = "target_video.mp4"  # 替换为目标视频路径

# 获取视频时长
r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                    "-of", "csv=p=0", vpath], capture_output=True, text=True)
dur = float(r.stdout.strip())

os.makedirs("frames", exist_ok=True)

# 开头0/2/4/6/8s + 后面均匀5帧
timestamps = [0, 2, 4, 6, 8]
if dur > 10:
    step = (dur - 8) / 5
    for j in range(1, 6):
        timestamps.append(8 + int(step * j))

for k, ts in enumerate(timestamps):
    if ts >= dur:
        ts = int(dur - 1)
    outpath = "frames/f{:02d}_{}s.jpg".format(k, ts)
    cmd = ["ffmpeg", "-y", "-ss", str(ts), "-i", vpath,
           "-frames:v", "1", "-q:v", "2", outpath]
    subprocess.run(cmd, capture_output=True)
    print("frame {}: {}s".format(k, ts))

print("Done! Total {} frames".format(len(timestamps)))
```

### 5.3 帧检查方法

使用 `image` 工具（task='ocr'）逐帧检查：

- **有大量字体/文字** → 淘汰该视频
- **有少量字体**（角落logo、零散数字标签）→ 合格，后续可crop或马赛克处理
- **有人脸** → 淘汰
- **有水印** → 淘汰
- **无文字无人脸** → 最佳

### 5.4 批量抽帧脚本（多视频）

```python
# -*- coding: utf-8 -*-
"""批量抽帧 - 对多个视频同时抽帧"""
import subprocess, os

videos = [
    ("raw/v00_author1.mp4", "author1-描述"),
    ("raw/v01_author2.mp4", "author2-描述"),
    ("raw/v02_author3.mp4", "author3-描述"),
]

os.makedirs("frames", exist_ok=True)

for vpath, label in videos:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", vpath], capture_output=True, text=True)
    dur = float(r.stdout.strip())

    # 0,2,4,6,8 + 5 evenly spaced from 8s to end
    timestamps = [0, 2, 4, 6, 8]
    if dur > 10:
        step = (dur - 8) / 5
        for j in range(1, 6):
            timestamps.append(8 + int(step * j))

    prefix = label.replace(" ", "_")
    for k, ts in enumerate(timestamps):
        if ts >= dur:
            ts = int(dur - 1)
        outpath = "frames/{}_f{:02d}_{}s.jpg".format(prefix, k, ts)
        cmd = ["ffmpeg", "-y", "-ss", str(ts), "-i", vpath,
               "-frames:v", "1", "-q:v", "2", outpath]
        subprocess.run(cmd, capture_output=True)

    print("{}: {}s, {} frames".format(label, int(dur), len(timestamps)))

print("Done!")
```

---

## 六、切割与输出

### 6.1 切割脚本（16:9 原版，不裁剪）

选定最佳素材后，从指定时间点切出所需长度，保持16:9原比例：

```python
# -*- coding: utf-8 -*-
"""16:9原版切割脚本 - 不裁剪，保持原始比例"""
import subprocess, os

# 参数：源视频、起始时间、切割时长、输出文件名
src = "raw/v01_landspace.mp4"
start = 48        # 起始秒数
duration = 15     # 切割时长（秒）
output = "output_15s_16x9.mp4"

r = subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-i", src,
                    "-t", str(duration),
                    "-c:v", "libx264", "-c:a", "aac",
                    "-r", "30",          # 统一30fps
                    output],
                   capture_output=True, text=True)

print("cut:", "OK" if r.returncode == 0 else r.stderr[-200:])
if os.path.exists(output):
    print("Output:", os.path.getsize(output) // 1024, "KB")
```

### 6.2 字体处理（可选）

如果素材有少量角落字体/logo，可用FFmpeg裁掉或加马赛克：

```python
# 裁掉底部120px（字幕区域）
# ffmpeg -y -i input.mp4 -vf "crop=iw:ih-120:0:0" -c:v libx264 output.mp4

# 裁掉四角logo（左上角80x80区域涂黑）
# ffmpeg -y -i input.mp4 -vf "drawbox=x=0:y=0:w=80:h=80:color=black:t=fill" -c:v libx264 output.mp4
```

---

## 七、方案对比

| 对比项 | 抖音（JS API法） | YouTube（yt-dlp法） | B站（yt-dlp法） |
|--------|-----------------|-------------------|----------------|
| 下载工具 | FFmpeg（带Referer头） | yt-dlp（带cookies） | yt-dlp（带cookies） |
| URL获取 | Playwright内JS调API | yt-dlp自动解析 | yt-dlp自动解析 |
| Cookies | 不需要单独管理 | 需Playwright导出→转Netscape | 需Playwright导出→转Netscape（注意BOM） |
| 格式选择 | FFmpeg直接下载 | `best[ext=mp4][height<=1080]` | `30080+30280`（视频音频分离需合并） |
| 已知问题 | aweme_id大整数精度丢失 | cookies过期需刷新 | cookies过期返回412；Cookie文件BOM问题 |
| 稳定性 | ✅ 稳定（绕过签名） | ✅ 稳定 | ✅ 稳定 |
| 常见水印 | 平台水印+作者水印 | 通常无水印 | UP主水印（右上角）+字幕（底部）+@账号（中部） |
| 适合素材 | 中文实拍（航天、半导体等） | 英文/无版权（金融动画等） | 中文演讲/科技（黄仁勋、发布会等） |

---

## 八、完整工作流（端到端）

```
1. 确定搜索关键词
2. 选择平台（抖音=中文实拍 / YouTube=英文无版权 / B站=中文演讲科技）
3. Playwright打开搜索页
4. 提取搜索结果（JS evaluate / browser_snapshot）
5. 选3个候选下载
6. 抽帧（0/2/4/6/8s + 5帧）
7. image工具逐帧检查（ocr模式）
8. 选定最佳素材
9. FFmpeg切割所需段落（16:9原版，30fps）
10. （可选）drawbox去水印/字幕处理
11. 再次抽帧验证处理效果，确保无文字
12. 交付
```

---

## 九、已采集素材记录

### 抖音素材

| 文件名 | aweme_id | 作者 | 内容 | 时长 | 用途 |
|--------|----------|------|------|------|------|
| v01_landspace.mp4 | 7580567492326690098 | 蓝箭航天 | 朱雀三号首飞（发射/飞行/着陆实拍） | 210s | 商业航天15s（48s~63s切割） |

### YouTube素材

| 文件名 | Video ID | 标题 | 内容 | 时长 | 用途 |
|--------|----------|------|------|------|------|
| finance_01~03.mp4 | 多个 | 金融K线/图表 | 纯K线/图表动画，无字体无水印 | 各约15s | 金融投资素材 |
| finance_05_15s.mp4 | HI3-irTdCm4 | Cinematic Stock Market Trading Screen | 电影感交易屏幕特写，无文字 | 15s | 金融投资素材 |
| finance_06.mp4 | sd6N5Lu7Lfo | Rising Stock Market Chart Arrow | 绿色3D上涨箭头+K线背景 | 10s | 金融投资素材 |

### B站素材

| 文件名 | BV号 | UP主 | 内容 | 时长 | 用途 |
|--------|------|------|------|------|------|
| nv_01_final.mp4 | BV1T8Vd6MEEE | NVIDIA英伟达（官方） | GTC台北2026主题演讲（黄仁勋+服务器机柜背景，1590~1610s切割） | 20s | 英伟达/黄仁勋素材 |
| nv_03_done.mp4 | BV1sDiZBcEkD | 向杨Alan君 | 黄仁勋专访（drawbox去翻译制作水印+双语字幕） | 20s | 英伟达/黄仁勋素材 |

---

## 十、注意事项

1. **抖音URL时效性**：douyinvod.com URL约几小时过期，获取后立即下载
2. **YouTube/B站cookies刷新**：每次下载前刷新cookies，避免过期导致下载失败
3. **B站Cookie BOM问题**：必须用ASCII编码写cookies文件，PowerShell默认UTF-8带BOM会导致yt-dlp报错
4. **B站视频音频分离**：必须用 `-f "30080+30280"` + `--merge-output-format mp4`，不能用 `best[ext=mp4]`
5. **每次最多下载3个**：看完抽帧结果再决定补充，避免浪费时间和带宽
6. **大整数精度**：抖音aweme_id在JS中用字符串处理，不做数值运算
7. **Referer头**：抖音下载必须带 `Referer: https://www.douyin.com/`
8. **编码回退**：`-c copy` 失败时回退到 `libx264 + aac` 重新编码
9. **统一输出规格**：16:9横版、1080p、30fps
10. **字体判定**：几乎没有字体→合格（可drawbox处理角落水印/底部字幕）；大量字体→直接淘汰
11. **B站去水印后必须验证**：drawbox位置需要根据实际水印位置逐步调整，处理后必须再次抽帧用image工具确认无文字
12. **B站优先选官方账号**：官方账号视频只有右上角水印+底部字幕，无中部@水印；第三方UP主常有中部@水印无法去除
