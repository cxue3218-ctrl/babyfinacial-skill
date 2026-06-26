"""
engine.py - 宝哥视频渲染引擎
核心渲染函数，从企微文档中的实战代码提取并适配。
"""

import re
from PIL import Image, ImageDraw, ImageFont
import subprocess
import json
import os

# ============================================================
# 贴片纹理生成
# ============================================================

def make_banner(width, height, base_color=(90, 5, 16), line_color=(60, 3, 10), spacing=30):
    """
    生成暗红底板 + 45度斜线纹理。
    
    Args:
        width: 画布宽度
        height: 画布高度
        base_color: 底色 RGB，默认暗红 #5a0510
        line_color: 斜线颜色 RGB，默认更暗红 #3c030a
        spacing: 斜线间距，默认30px
    
    Returns:
        PIL.Image: 带斜线纹理的贴片
    """
    img = Image.new('RGB', (width, height), base_color)
    draw = ImageDraw.Draw(img)
    for x in range(-height, width + height, spacing):
        draw.line([(x, 0), (x + height + 20, height)], fill=line_color, width=2)
    return img


# ============================================================
# 长句子幕轮播时间分配
# ============================================================

def split_subtitle_times(text, duration):
    """
    将长句按标点切分为子句，按字数比例分配显示时间。
    
    Args:
        text: 完整文案句
        duration: TTS 总时长（秒）
    
    Returns:
        list[tuple]: [(子句, 开始时间, 结束时间), ...]
    """
    parts = re.split(r'([，。,.?？!！;；])', text)
    subs = []
    current = ""
    for p in parts:
        if not p:
            continue
        if p in "，。,.?？!！;；":
            current += p
            subs.append(current)
            current = ""
        else:
            current = p
    if current:
        subs.append(current)

    total_chars = sum(len(s) for s in subs)
    if total_chars == 0:
        return [(text, 0, duration)]

    timed_subs = []
    current_time = 0.0
    for s in subs:
        ratio = len(s) / total_chars
        part_dur = duration * ratio
        timed_subs.append((s, current_time, current_time + part_dur))
        current_time += part_dur

    return timed_subs


# ============================================================
# 字体回退
# ============================================================

def get_fallback_font(size):
    """获取可用中文字体，按优先级回退。"""
    fonts = [
        '/usr/share/fonts/msyhbd.ttc',   # Microsoft YaHei Bold
        '/usr/share/fonts/msyh.ttc',     # Microsoft YaHei
        '/usr/share/fonts/PingFang.ttc', # PingFang
        '/usr/share/fonts/NotoSansCJK-Bold.ttc',
        '/usr/share/fonts/NotoSansCJK-Regular.ttc',
    ]
    for fp in fonts:
        if os.path.exists(fp):
            return ImageFont.truetype(fp, size)
    return ImageFont.load_default()


# ============================================================
# 单帧渲染（四层结构）
# ============================================================

def generate_segment_frame(title, subtitle_text, material_img, output_path):
    """
    渲染单帧：上贴片(384) + 素材(768) + 文案条(384) + 下贴片(384) = 1920
    
    Args:
        title: 标题文字（金色，不斜体）
        subtitle_text: 当前子句文案（白色）
        material_img: 素材画面 PIL.Image
        output_path: 输出 PNG 路径
    """
    CANVAS_W = 1080
    CANVAS_H = 1920
    SEGMENT_H = 384
    MATERIAL_H = 768

    final_canvas = Image.new('RGB', (CANVAS_W, CANVAS_H), (0, 0, 0))

    # 三块贴片（上/文案条/下）
    top_banner = make_banner(CANVAS_W, SEGMENT_H)
    middle_banner = make_banner(CANVAS_W, SEGMENT_H)
    bottom_banner = make_banner(CANVAS_W, SEGMENT_H)

    # ---- 上贴片：金色标题（不斜体） ----
    lines = [title] if len(title) <= 12 else [title[:12], title[12:]]
    font_size = 81
    draw_top = ImageDraw.Draw(top_banner)
    while font_size > 40:
        font_title = get_fallback_font(font_size)
        max_w = max(
            draw_top.textbbox((0, 0), ln, font=font_title, stroke_width=3)[2]
            for ln in lines
        )
        if max_w <= 1000:
            break
        font_size -= 4

    current_y = (SEGMENT_H - (len(lines) * (font_size + 15))) // 2
    for line in lines:
        font_title = get_fallback_font(font_size)
        draw_top.text(
            ((CANVAS_W - draw_top.textbbox((0, 0), line, font=font_title, stroke_width=3)[2]) // 2, current_y),
            line,
            font=font_title,
            fill=(232, 200, 96),  # 金色 #e8c860
            stroke_fill=(42, 3, 8),
            stroke_width=3,
        )
        current_y += font_size + 15

    # ---- 文案条：白色字幕 ----
    draw_mid = ImageDraw.Draw(middle_banner)
    font_sub = get_fallback_font(54)
    sub_bbox = draw_mid.textbbox((0, 0), subtitle_text, font=font_sub)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_h = sub_bbox[3] - sub_bbox[1]
    if sub_w > 1000:
        font_sub = get_fallback_font(42)
        sub_bbox = draw_mid.textbbox((0, 0), subtitle_text, font=font_sub)
        sub_w = sub_bbox[2] - sub_bbox[0]
        sub_h = sub_bbox[3] - sub_bbox[1]
    draw_mid.text(
        ((CANVAS_W - sub_w) // 2, (SEGMENT_H - sub_h) // 2),
        subtitle_text,
        font=font_sub,
        fill=(255, 255, 255),
    )

    # ---- 四层垂直拼接 ----
    material_img_resized = material_img.resize((CANVAS_W, MATERIAL_H), Image.Resampling.LANCZOS)
    final_canvas.paste(top_banner, (0, 0))
    final_canvas.paste(material_img_resized, (0, SEGMENT_H))
    final_canvas.paste(middle_banner, (0, SEGMENT_H + MATERIAL_H))
    final_canvas.paste(bottom_banner, (0, SEGMENT_H + MATERIAL_H + SEGMENT_H))
    final_canvas.save(output_path, "PNG")


# ============================================================
# TTS 时长估算
# ============================================================

def estimate_tts_duration(text):
    """
    估算 TTS 朗读时长（秒）。
    
    中文字 4.5字/秒，数字按位数，英文缩写 0.8s/组，标点 0.15s/个，+1s 缓冲。
    
    Returns:
        float: 估算时长（秒），调用方自行 ceil
    """
    duration = 0.0
    i = 0
    while i < len(text):
        ch = text[i]
        if '\u4e00' <= ch <= '\u9fff':
            duration += 1 / 4.5
        elif ch.isdigit():
            num_str = ""
            while i < len(text) and text[i].isdigit():
                num_str += text[i]
                i += 1
            n = len(num_str)
            if n == 1:
                duration += 0.5
            elif n == 2:
                duration += 0.8
            elif n == 3:
                duration += 1.2
            else:
                duration += 1.5
            continue
        elif ch.isascii() and ch.isalpha():
            abbr = ""
            while i < len(text) and text[i].isascii() and text[i].isalpha():
                abbr += text[i]
                i += 1
            duration += 0.8
            continue
        elif ch in "，。,.?？!！;；、":
            duration += 0.15
        i += 1

    duration += 1.0  # 缓冲
    return duration


# ============================================================
# 数据可视化自检
# ============================================================

def check_data_viz(video_path, expected_dur, expected_w=1080, expected_h=768):
    """
    检查数据可视化动画是否合格。
    
    Returns:
        list[str]: 问题列表，空列表表示全部通过
    """
    import json as _json
    issues = []

    # 1. 分辨率检查
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,duration", "-of", "json", video_path],
        capture_output=True, text=True,
    )
    info = _json.loads(r.stdout)["streams"][0]
    w, h = int(info["width"]), int(info["height"])
    if w != expected_w or h != expected_h:
        issues.append(f"D7: 分辨率 {w}x{h} != {expected_w}x{expected_h}")

    # 2. 时长检查
    dur = float(info["duration"])
    if abs(dur - expected_dur) > 0.5:
        issues.append(f"D8: 时长 {dur:.1f}s != {expected_dur}s")

    # 3. 截帧检查是否有运动（对比第1帧和中间帧的文件大小差异）
    subprocess.run(
        ["ffmpeg", "-y", "-ss", "0.5", "-i", video_path, "-frames:v", "1", "/tmp/check_f1.jpg"],
        capture_output=True,
    )
    subprocess.run(
        ["ffmpeg", "-y", "-ss", str(dur / 2), "-i", video_path, "-frames:v", "1", "/tmp/check_f2.jpg"],
        capture_output=True,
    )
    s1 = os.path.getsize("/tmp/check_f1.jpg")
    s2 = os.path.getsize("/tmp/check_f2.jpg")
    if max(s1, s2) > 0 and abs(s1 - s2) / max(s1, s2) < 0.05:
        issues.append("D4: 第1帧和中间帧几乎相同，可能没有运动")

    return issues
