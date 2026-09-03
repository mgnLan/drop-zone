# Обложка ВК: заменить титл NEON GLADIATORS на DROP ZONE ROYAL BATTLE, опустить ниже
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

ROOT = r"G:\Kimi project\Drop Zone"
SRC = os.path.join(ROOT, "docs", "vk_cover.png")
OUT = os.path.join(ROOT, "docs", "vk_cover_new.png")

img = Image.open(SRC).convert("RGB")
W, H = img.size  # 2048x1152

# 1) закрыть старый титл: небо затемняем, размываем, края — плавный градиент
box = (470, 0, 1590, 400)
bw, bh = box[2] - box[0], box[3] - box[1]
sky = img.crop(box).filter(ImageFilter.GaussianBlur(60))
dark = Image.new("RGB", sky.size, (6, 9, 19))
sky = Image.blend(sky, dark, 0.90)
# вертикальный градиент: сверху почти непрозрачный, книзу растворяется
mask = Image.new("L", (bw, bh), 0)
for yy in range(bh):
    a = int(255 * max(0.0, 1.0 - max(0.0, (yy - bh * 0.78) / (bh * 0.22))))
    ImageDraw.Draw(mask).line([(0, yy), (bw, yy)], fill=a)
# боковые края тоже смягчаем
edge = Image.new("L", (bw, bh), 0)
ed = ImageDraw.Draw(edge)
ed.rectangle([35, 0, bw - 35, bh], fill=255)
edge = edge.filter(ImageFilter.GaussianBlur(25))
from PIL import ImageChops
mask = ImageChops.multiply(mask, edge)
img.paste(sky, box, mask)

# 2) водяной знак слева внизу
d0 = ImageDraw.Draw(img)
d0.rectangle([0, H - 90, 220, H], fill=(6, 8, 14))

# 3) новый титл — опущен ниже (центр ~48% высоты), с неоновым свечением
FB = "C:/Windows/Fonts/arialbd.ttf"
def fit(text, start, max_w):
    size = start
    while size > 20:
        f = ImageFont.truetype(FB, size)
        bb = f.getbbox(text)
        if bb[2] - bb[0] <= max_w:
            return f
        size -= 4
    return f

f1 = fit("DROP ZONE", 300, int(W * 0.80))
f2 = fit("ROYAL BATTLE", 110, int(W * 0.50))

def center(text, font, y):
    bb = font.getbbox(text)
    return ((W - (bb[2] - bb[0])) // 2 - bb[0], y)

Y1, Y2 = 370, 660
# слой свечения
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.text(center("DROP ZONE", f1, Y1), "DROP ZONE", font=f1, fill=(40, 216, 255, 255))
gd.text(center("ROYAL BATTLE", f2, Y2), "ROYAL BATTLE", font=f2, fill=(255, 60, 110, 255))
glow = glow.filter(ImageFilter.GaussianBlur(20))
img = img.convert("RGBA")
img = Image.alpha_composite(img, glow)
d = ImageDraw.Draw(img)
d.text(center("DROP ZONE", f1, Y1), "DROP ZONE", font=f1, fill=(245, 248, 255, 255))
d.text(center("ROYAL BATTLE", f2, Y2), "ROYAL BATTLE", font=f2, fill=(255, 95, 140, 255))
# неоновые линии-акценты по бокам подзаголовка
bb2 = f2.getbbox("ROYAL BATTLE")
w2 = bb2[2] - bb2[0]
ly = Y2 + (bb2[3] - bb2[1]) // 2
d.line([(W // 2 - w2 // 2 - 240, ly), (W // 2 - w2 // 2 - 40, ly)], fill=(255, 60, 110, 220), width=6)
d.line([(W // 2 + w2 // 2 + 40, ly), (W // 2 + w2 // 2 + 240, ly)], fill=(255, 60, 110, 220), width=6)

img.convert("RGB").save(OUT)
img.convert("RGB").resize((1024, 576), Image.LANCZOS).save(os.path.join(ROOT, "docs", "vk_cover_new_small.jpg"), quality=88)
print("VK_COVER_OK", OUT, os.path.getsize(OUT))
