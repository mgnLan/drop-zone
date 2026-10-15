# -*- coding: utf-8 -*-
# Кнопки v3 — статичные, без перелива; приоритетный цвет: глубокий тил,
# красно-розовые оттенки выведены из интерфейса.
from PIL import Image, ImageDraw
import os

OUT = r"I:\Kimi project\Drop Zone\icons\_buttons_v3"
DST = r"I:\Kimi project\Drop Zone\game\assets\ui\buttons"
os.makedirs(OUT, exist_ok=True)
os.makedirs(DST, exist_ok=True)

W, H, R = 512, 128, 20
CYAN = (40, 216, 255)
GOLD = (255, 209, 102)
INK_TOP, INK_BOT = (27, 34, 51), (12, 16, 28)
PRI_TOP, PRI_BOT = (24, 165, 188), (10, 74, 92)   # тил циан → глубокий тил

def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

def vgrad(w, h, c_top, c_bot):
    im = Image.new("RGB", (w, h))
    for y in range(h):
        ImageDraw.Draw(im).line([(0, y), (w, y)], fill=lerp(c_top, c_bot, y / max(1, h - 1)))
    return im

def rounded_mask(w, h, r):
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=r, fill=255)
    return m

def base_button(fill_top, fill_bot, border_rgb, border_a, hl_a=14):
    im = vgrad(W, H, fill_top, fill_bot).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([1, 1, W - 2, H - 2], radius=R - 1,
                        outline=border_rgb + (border_a,), width=2)
    hl = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(hl).rounded_rectangle([3, 3, W - 4, H // 2], radius=R - 3,
                                         fill=(255, 255, 255, hl_a))
    im = Image.alpha_composite(im, hl)
    im.putalpha(rounded_mask(W, H, R))
    return im

# обычное состояние — графитовая чернильная кнопка
base_button(INK_TOP, INK_BOT, (43, 58, 85), 110).save(f"{OUT}/btn_bg_normal.png")
# hover — тот же графит, рамка циан
base_button((35, 44, 66), (16, 22, 39), CYAN, 150).save(f"{OUT}/btn_bg_hover.png")
# приоритет (CTA «В БОЙ», «Купить»): глубокий тил + золотая рамка, верхний блик
pri = base_button(PRI_TOP, PRI_BOT, GOLD, 210, hl_a=30)
pri.save(f"{OUT}/btn_bg_priority.png")

# копируем в игру поверх старых имён (код менять не нужно)
import shutil
for f in ("btn_bg_normal.png", "btn_bg_hover.png", "btn_bg_priority.png"):
    shutil.copy(f"{OUT}/{f}", f"{DST}/{f}")
print("OK ->", DST)
