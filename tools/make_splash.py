# Сборка заставки: концепт-арт + название DROP ZONE ROYAL BATTLE (текст влезает гарантированно)
from PIL import Image, ImageDraw, ImageFont
import os

SRC = r"G:\Kimi project\Drop Zone\docs\splash_art_raw.png"
OUT = r"G:\Kimi project\Drop Zone\game\assets\ui\splash.png"
FB = "C:/Windows/Fonts/arialbd.ttf"
FR = "C:/Windows/Fonts/arial.ttf"

img = Image.open(SRC).convert("RGB")          # 2048x2048
W, H = img.size
d = ImageDraw.Draw(img, "RGBA")

# 1) закрасить водяной знак «AI生成» в левом нижнем углу
d.rectangle([0, H - 90, 340, H], fill=(8, 10, 16, 255))

# 2) затемнение сверху под текст (градиент)
for y in range(0, 560):
    a = int(200 * (1 - y / 560.0))
    d.line([(0, y), (W, y)], fill=(4, 6, 12, a))

def fit_font(text, path, max_w, start):
    size = start
    while size > 20:
        f = ImageFont.truetype(path, size)
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= max_w:
            return f
        size -= 4
    return f

def center_text(y, text, font, fill, shadow=None, soff=6):
    bb = d.textbbox((0, 0), text, font=font)
    x = (W - (bb[2] - bb[0])) // 2 - bb[0]
    if shadow:
        d.text((x + soff, y + soff), text, font=font, fill=shadow)
    d.text((x, y), text, font=font, fill=fill)

# 3) надписи (максимум 88% ширины — влезает точно)
f_big = fit_font("DROP ZONE", FB, int(W * 0.88), 230)
center_text(90, "DROP ZONE", f_big, (240, 244, 252), shadow=(255, 60, 110, 200))
f_mid = fit_font("ROYAL BATTLE", FB, int(W * 0.70), 110)
center_text(360, "ROYAL BATTLE", f_mid, (255, 70, 120), shadow=(40, 216, 255, 190), soff=5)
f_sub = fit_font("КОРОЛЕВСКАЯ БИТВА", FR, int(W * 0.60), 60)
center_text(480, "КОРОЛЕВСКАЯ БИТВА", f_sub, (150, 200, 220), shadow=(0, 0, 0, 200), soff=3)

img = img.resize((1024, 1024), Image.LANCZOS)
img.save(OUT)
print("SPLASH_SAVED", OUT, os.path.getsize(OUT), "bytes")
# превью для проверки
img.save(r"G:\Kimi project\Drop Zone\docs\splash_preview.png")
