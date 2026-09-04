# Ребрендинг артов ВК: «ТОЧКА СБРОСА / КОРОЛЕВСКАЯ БИТВА» — обложка + аватарка группы
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
import os

ROOT = r"G:\Kimi project\Drop Zone"
FB = "C:/Windows/Fonts/arialbd.ttf"  # жирный, кириллица
T1, T2 = "ТОЧКА СБРОСА", "КОРОЛЕВСКАЯ БИТВА"

def fit(text, start, max_w):
    size = start
    f = ImageFont.truetype(FB, size)
    while size > 20:
        f = ImageFont.truetype(FB, size)
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= max_w:
            return f
        size -= 4
    return f

def cx(text, font, W, y):
    bb = font.getbbox(text)
    return ((W - (bb[2] - bb[0])) // 2 - bb[0], y)

# ---------- 1) обложка 2048x1152 ----------
SRC = os.path.join(ROOT, "docs", "vk_cover.png")
# бэкап старой версии один раз
if not os.path.exists(os.path.join(ROOT, "docs", "vk_cover_dropzone.png")):
    Image.open(SRC).save(os.path.join(ROOT, "docs", "vk_cover_dropzone.png"))

img = Image.open(SRC).convert("RGB")
W, H = img.size

# закрываем старый титл (зона y 300..840, почти вся ширина)
box = (60, 300, W - 60, 840)
bw, bh = box[2] - box[0], box[3] - box[1]
sky = img.crop(box).filter(ImageFilter.GaussianBlur(70))
dark = Image.new("RGB", sky.size, (6, 9, 19))
sky = Image.blend(sky, dark, 0.92)
mask = Image.new("L", (bw, bh), 0)
md = ImageDraw.Draw(mask)
for yy in range(bh):
    a = 255 if bh * 0.08 < yy < bh * 0.86 else 0
    md.line([(0, yy), (bw, yy)], fill=a)
mask = mask.filter(ImageFilter.GaussianBlur(18))
edge = Image.new("L", (bw, bh), 0)
ed = ImageDraw.Draw(edge)
ed.rectangle([40, 0, bw - 40, bh], fill=255)
edge = edge.filter(ImageFilter.GaussianBlur(30))
mask = ImageChops.multiply(mask, edge)
img.paste(sky, box, mask)

f1 = fit(T1, 260, int(W * 0.80))
f2 = fit(T2, 100, int(W * 0.55))
Y1, Y2 = 380, 650

glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.text(cx(T1, f1, W, Y1), T1, font=f1, fill=(40, 216, 255, 255))
gd.text(cx(T2, f2, W, Y2), T2, font=f2, fill=(255, 60, 110, 255))
glow = glow.filter(ImageFilter.GaussianBlur(20))
img = Image.alpha_composite(img.convert("RGBA"), glow)
d = ImageDraw.Draw(img)
d.text(cx(T1, f1, W, Y1), T1, font=f1, fill=(245, 248, 255, 255))
d.text(cx(T2, f2, W, Y2), T2, font=f2, fill=(255, 95, 140, 255))
bb2 = f2.getbbox(T2)
w2 = bb2[2] - bb2[0]
ly = Y2 + (bb2[3] - bb2[1]) // 2
d.line([(W // 2 - w2 // 2 - 240, ly), (W // 2 - w2 // 2 - 40, ly)], fill=(255, 60, 110, 220), width=6)
d.line([(W // 2 + w2 // 2 + 40, ly), (W // 2 + w2 // 2 + 240, ly)], fill=(255, 60, 110, 220), width=6)

img.convert("RGB").save(os.path.join(ROOT, "docs", "vk_cover.png"))
img.convert("RGB").resize((1024, 576), Image.LANCZOS).save(os.path.join(ROOT, "docs", "vk_cover_small.jpg"), quality=88)
print("COVER_OK")

# ---------- 2) аватарка 512x512 ----------
AV = 512
av = Image.new("RGB", (AV, AV), (6, 9, 19))
# вертикальный градиент тёмно-синий -> чёрный
for yy in range(AV):
    t = yy / AV
    r = int(10 + 14 * (1 - t)); g = int(14 + 22 * (1 - t)); b = int(28 + 40 * (1 - t))
    ImageDraw.Draw(av).line([(0, yy), (AV, yy)], fill=(r, g, b))
logo = Image.open(os.path.join(ROOT, "game", "assets", "ui", "logo.png")).convert("RGBA")
lw = int(AV * 0.92)
lh = int(logo.height * lw / logo.width)
logo = logo.resize((lw, lh), Image.LANCZOS)
av = av.convert("RGBA")
av.alpha_composite(logo, ((AV - lw) // 2, (AV - lh) // 2))
d = ImageDraw.Draw(av)
d.rectangle([60, AV - 74, AV - 60, AV - 66], fill=(255, 60, 110, 220))
d.rectangle([60, 66, AV - 60, 74], fill=(40, 216, 255, 220))
av.convert("RGB").save(os.path.join(ROOT, "docs", "vk_avatar.png"))
print("AVATAR_OK")
