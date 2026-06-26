"""
fast_viz_v2.py - Pillow逐帧渲染框架
数据可视化动画的唯一允许实现方式。
"""

from PIL import Image, ImageDraw, ImageFont
import subprocess
import os

WIDTH = 1080
CONTENT_H = 768
FPS = 30

def make_bg(w, h):
    """统一背景：暗色渐变 + 斜线纹理"""
    img = Image.new('RGB', (w, h), (10, 10, 10))
    draw = ImageDraw.Draw(img)
    line_color = (60, 3, 10)
    spacing = 30
    for x in range(-h, w + h, spacing):
        draw.line([(x, 0), (x + h + 20, h)], fill=line_color, width=2)
    return img

def render_anim(anim_func, duration, outvid):
    """逐帧渲染 → FFmpeg合成，自动验证时长"""
    total = int(duration * FPS)
    frame_dir = "/tmp/frames"
    os.makedirs(frame_dir, exist_ok=True)
    
    for i in range(total):
        t = i / total
        img = anim_func(t, i, total)
        img.save(f"{frame_dir}/frame_{i:04d}.png", quality=88)
    
    subprocess.run([
        'ffmpeg', '-y', '-framerate', str(FPS),
        '-i', f'{frame_dir}/frame_%04d.png',
        '-c:v', 'libx264', '-pix_fmt', 'yuv420p',
        outvid
    ], capture_output=True)
    
    # 验证时长
    r = subprocess.run([
        'ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=duration', '-of', 'json', outvid
    ], capture_output=True, text=True)
    import json
    info = json.loads(r.stdout)
    actual_dur = float(info['streams'][0]['duration'])
    print(f"渲染完成: {outvid} 时长={actual_dur:.1f}s (目标={duration}s)")
    return actual_dur

# === 已验证的动画函数 ===

def anim_circle_shrink(t, i, total):
    """缩圈 - 同心圆收缩+箭头向内"""
    img = make_bg(WIDTH, CONTENT_H)
    draw = ImageDraw.Draw(img)
    cx, cy = WIDTH // 2, CONTENT_H // 2
    max_r = 300
    r = max_r * (1 - t * 0.7)
    draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(232, 200, 96), width=4)
    # 内圆
    r2 = r * 0.6
    draw.ellipse([cx-r2, cy-r2, cx+r2, cy+r2], outline=(100, 150, 255), width=2)
    return img

def anim_split_compare(t, i, total):
    """左右对比 - 双柱状图增长"""
    img = make_bg(WIDTH, CONTENT_H)
    draw = ImageDraw.Draw(img)
    progress = min(t / 0.7, 1.0)
    bar_w = 200
    max_h = 400
    # 左柱
    h1 = int(max_h * progress * 0.8)
    draw.rectangle([200, CONTENT_H//2 + 100 - h1, 200+bar_w, CONTENT_H//2 + 100],
                   fill=(50, 100, 220))
    # 右柱
    h2 = int(max_h * progress)
    draw.rectangle([600, CONTENT_H//2 + 100 - h2, 600+bar_w, CONTENT_H//2 + 100],
                   fill=(232, 200, 96))
    return img

def anim_bamboo_grow(t, i, total):
    """竹竿效应 - 竹节逐段生长"""
    img = make_bg(WIDTH, CONTENT_H)
    draw = ImageDraw.Draw(img)
    progress = min(t / 0.7, 1.0)
    base_y = CONTENT_H - 100
    segments = 6
    seg_h = 60
    for s in range(segments):
        if s / segments <= progress:
            y0 = base_y - (s+1) * seg_h
            y1 = base_y - s * seg_h
            draw.rectangle([WIDTH//2 - 30, y0, WIDTH//2 + 30, y1],
                          fill=(232, 200, 96) if s % 2 == 0 else (50, 100, 220))
    return img

def anim_barrel_short(t, i, total):
    """木桶效应 - 木桶+水位上升"""
    img = make_bg(WIDTH, CONTENT_H)
    draw = ImageDraw.Draw(img)
    progress = min(t / 0.7, 1.0)
    cx, cy = WIDTH//2, CONTENT_H//2
    # 桶壁
    draw.rectangle([cx-150, cy-200, cx-130, cy+100], fill=(139, 90, 43))
    draw.rectangle([cx+130, cy-200, cx+150, cy+100], fill=(139, 90, 43))
    # 桶底
    draw.rectangle([cx-150, cy+100, cx+150, cy+120], fill=(139, 90, 43))
    # 水位（最短板限制）
    short_h = 200 * (1 - progress * 0.6)
    water_y = cy + 100 - int(short_h)
    draw.rectangle([cx-128, water_y, cx+128, cy+100], fill=(50, 100, 220))
    return img

def anim_counter(t, i, total, target_val=100, label=""):
    """数字递增+进度条"""
    img = make_bg(WIDTH, CONTENT_H)
    draw = ImageDraw.Draw(img)
    progress = min(t / 0.7, 1.0)
    cur_val = int(target_val * progress)
    # 进度条
    bar_w = 600
    bar_h = 40
    bx, by = (WIDTH - bar_w)//2, CONTENT_H//2
    draw.rectangle([bx, by, bx+bar_w, by+bar_h], outline=(100, 100, 100), width=2)
    fill_w = int(bar_w * progress)
    draw.rectangle([bx, by, bx+fill_w, by+bar_h], fill=(232, 200, 96))
    return img
