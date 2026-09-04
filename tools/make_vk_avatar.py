# Аватарка группы ВК 512x512: «ТОЧКА СБРОСА» в две строки + подзаголовок
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

ROOT = r"G:\Kimi project\Drop Zone"
FB = "C:/Windows/Fonts/arialbd.ttf"
AV = 512

av = Image.new("RGB", (AV, AV), (6, 9, 19))
for yy in range(AV):
    t = yy / AV
    ImageDraw.Draw(av).line([(0, yy), (AV, yy)], fill=(int(10 + 16 * (1 - t)), int(16 + 26 * (1 - t)), int(32 + 48 * (1 - t))))

f1 = ImageFont.truetype(FB, 118)
f2 = ImageFont.truetype(FB, 34)

def cx(text, font, y):
    bb = font.getbbox(text)
    return ((AV - (bb[2] - bb[0])) // 2 - bb[0], y)

glow = Image.new("RGBA", (AV, AV), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.text(cx("ТОЧКА", f1, 108), "ТОЧКА", font=f1, fill=(40, 216, 255, 255))
gd.text(cx("СБРОСА", f1, 226), "СБРОСА", font=f1, fill=(40, 216, 255, 255))
gd.text(cx("КОРОЛЕВСКАЯ БИТВА", f2, 376), "КОРОЛЕВСКАЯ БИТВА", font=f2, fill=(255, 60, 110, 255))
glow = glow.filter(ImageFilter.GaussianBlur(14))
av = Image.alpha_composite(av.convert("RGBA"), glow)
d = ImageDraw.Draw(av)
d.text(cx("ТОЧКА", f1, 108), "ТОЧКА", font=f1, fill=(245, 248, 255, 255))
d.text(cx("СБРОСА", f1, 226), "СБРОСА", font=f1, fill=(245, 248, 255, 255))
d.text(cx("КОРОЛЕВСКАЯ БИТВА", f2, 376), "КОРОЛЕВСКАЯ БИТВА", font=f2, fill=(255, 95, 140, 255))
d.rectangle([120, 60, AV - 120, 66], fill=(40, 216, 255, 220))
d.rectangle([120, AV - 66, AV - 120, AV - 60], fill=(255, 60, 110, 220))
av.convert("RGB").save(os.path.join(ROOT, "docs", "vk_avatar.png"))
print("AVATAR_OK")
