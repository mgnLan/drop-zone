# -*- coding: utf-8 -*-
# Рендер кнопок «Перелив v2» — пиксель-точные ассеты по палитре игры
from PIL import Image, ImageDraw, ImageFilter
import math, os

OUT = r"I:\Kimi project\Drop Zone\icons\_buttons"
os.makedirs(OUT, exist_ok=True)

W, H, R = 512, 128, 20          # базовый размер кнопки, радиус скругления
MARG = 24                        # 9-slice отступы (>= R+4)
PINK, CYAN, GOLD = (255, 60, 110), (40, 216, 255), (255, 209, 102)
INK_TOP, INK_BOT = (27, 34, 51), (12, 16, 28)

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def grad_color(t):
    """роза → циан → золото по t 0..1"""
    if t < 0.5:
        return lerp(PINK, CYAN, t * 2)
    return lerp(CYAN, GOLD, (t - 0.5) * 2)

def vgrad(w, h, c_top, c_bot):
    im = Image.new("RGB", (w, h))
    for y in range(h):
        ImageDraw.Draw(im).line([(0, y), (w, y)], fill=lerp(c_top, c_bot, y / max(1, h - 1)))
    return im

def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    return m

def base_button(fill_top, fill_bot, border_rgb, border_a=90):
    """фон кнопки с заливкой и спокойной рамкой"""
    im = vgrad(W, H, fill_top, fill_bot).convert("RGBA")
    d = ImageDraw.Draw(im)
    # рамка
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=R - 1,
                        outline=border_rgb + (border_a,), width=2)
    # верхний внутренний блик
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle([3, 3, W - 4, H // 2], radius=R - 3,
                                         fill=(255, 255, 255, 14))
    im = Image.alpha_composite(im, hl)
    im.putalpha(rounded_mask(W, H, R))
    return im

# ---------- периметр скруглённого прямоугольника ----------
def perimeter_pts(w, h, r, step=2.0):
    pts = []
    # top edge (слева направо), правый верхний угол, правый край вниз,
    # нижний правый угол, низ справа налево, левый нижний угол, левый край вверх, левый верхний угол
    cx, cy = w - r - 1, r
    for x in range(r, w - r):
        pts.append((x, 1.0))
    for a in range(-90, 1):
        pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    for y in range(r, h - r):
        pts.append((w - 1.0, y))
    cx, cy = w - r - 1, h - r - 1
    for a in range(0, 91):
        pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    for x in range(w - r - 1, r - 1, -1):
        pts.append((x, h - 1.0))
    cx, cy = r, h - r - 1
    for a in range(90, 181):
        pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    for y in range(h - r - 1, r - 1, -1):
        pts.append((0.0, y))
    cx, cy = r, r
    for a in range(180, 271):
        pts.append((cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a))))
    return pts

PTS = perimeter_pts(W, H, R)
L = len(PTS)

def draw_comet(frame_i, n_frames, tail_frac=0.35, head_t=1.0):
    """один кадр: по рамке бежит мягкий градиент + яркая комета со свечением"""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    head = int((frame_i / n_frames) * L)
    tail = int(L * tail_frac)
    # ободок: весь периметр тонирован бегущим градиентом (роза→циан→золото)
    for idx in range(0, L, 2):
        rel = ((idx - head) % L) / L          # 0 у головы → 1 позади
        col = grad_color(1.0 - rel)
        d.line([PTS[idx], PTS[(idx + 2) % L]], fill=col + (30 + int(26 * (1 - rel)),), width=2)
    # комета: точки позади головы (движение = рост индекса)
    for k in range(tail):
        idx = (head - k) % L
        t = 1.0 - k / tail                    # 1 у головы → 0 в хвосте
        col = grad_color(min(1.0, t * 1.15))
        alpha = int(255 * (t ** 1.25))
        x, y = PTS[idx]
        r2 = 3.0 if k < 8 else 2.1
        d.ellipse([x - r2, y - r2, x + r2, y + r2], fill=col + (alpha,))
    # головка — белое свечение
    hx, hy = PTS[head % L]
    for rr, aa in ((10, 90), (7, 140), (4, 210), (2, 255)):
        d.ellipse([hx - rr, hy - rr, hx + rr, hy + rr], fill=(255, 255, 255, aa))
    im = im.filter(ImageFilter.GaussianBlur(0.6))
    # звёздочка: два всплеска после прохождения верхнего правого угла
    corner_idx = int(0.125 * L)               # ~правый верх
    passed = (head - corner_idx) % L
    spark_frame = passed / L * n_frames       # кадров с момента прохождения
    if 0.2 < spark_frame < 4.2:
        ph = (spark_frame - 0.2) / 4.0        # 0..1
        alpha = int(255 * max(0.0, math.sin(ph * math.pi * 2)) ** 2)
        if alpha > 8:
            sx, sy = W - 26.0, 16.0
            s = 10 + 3 * math.sin(ph * math.pi * 2)
            sp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            sd = ImageDraw.Draw(sp)
            sd.polygon([(sx, sy - s), (sx + s * 0.28, sy - s * 0.28),
                        (sx + s, sy), (sx + s * 0.28, sy + s * 0.28),
                        (sx, sy + s), (sx - s * 0.28, sy + s * 0.28),
                        (sx - s, sy), (sx - s * 0.28, sy - s * 0.28)],
                       fill=(255, 255, 255, alpha))
            sp = sp.filter(ImageFilter.GaussianBlur(0.4))
            im = Image.alpha_composite(im, sp)
    return im

# ---------- фоны ----------
base_button(INK_TOP, INK_BOT, (43, 58, 85), 110).save(f"{OUT}/btn_bg_normal.png")
base_button((35, 44, 66), (16, 22, 39), CYAN, 150).save(f"{OUT}/btn_bg_hover.png")
# приоритетная: диагональный градиент роза → оранж
pri = Image.new("RGBA", (W, H), (0, 0, 0, 0))
pd = ImageDraw.Draw(pri)
for x in range(W):
    for y in range(0, H, 2):
        t = (x / W * 0.65 + y / H * 0.35)
        pd.line([(x, y), (x, y + 1)], fill=lerp(PINK, (255, 122, 69), t) + (255,))
pri.putalpha(rounded_mask(W, H, R))
pd = ImageDraw.Draw(pri)
pd.rounded_rectangle([1, 1, W - 2, H - 2], radius=R - 1, outline=GOLD + (200,), width=2)
hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
ImageDraw.Draw(hl).rounded_rectangle([3, 3, W - 4, H // 2], radius=R - 3, fill=(255, 255, 255, 26))
pri = Image.alpha_composite(pri, hl)
pri.putalpha(rounded_mask(W, H, R))
pri.save(f"{OUT}/btn_bg_priority.png")

# ---------- кадры перелива (12 шт, цикл 2.4 c при 5 fps) ----------
N = 12
for i in range(N):
    draw_comet(i, N).save(f"{OUT}/btn_shine_{i:02d}.png")
    print("frame", i)
print("OK", OUT)
