# -*- coding: utf-8 -*-
# Логотип v2: заголовок из splash + овальное растворение краёв (фон дыма
# сливается с тёмной шапкой лобби) + неоновое свечение
from PIL import Image, ImageDraw, ImageFilter

SRC = r"I:\Kimi project\Drop Zone\icons\splash_screen.png"
OUT = r"I:\Kimi project\Drop Zone\icons\logo_v2.png"

im = Image.open(SRC).convert("RGB")
crop = im.crop((300, 335, 1645, 590))   # заголовок целиком
cw, ch = crop.size

# овальная маска с мягкими краями
mask = Image.new("L", (cw, ch), 0)
d = ImageDraw.Draw(mask)
d.ellipse([-cw * 0.12, -ch * 0.55, cw * 1.12, ch * 1.55], fill=255)
mask = mask.filter(ImageFilter.GaussianBlur(38))
logo = crop.convert("RGBA")
logo.putalpha(mask)

# свечение (по ярким пикселям, чтобы не светить всем овалом)
bright = logo.copy()
bright.putalpha(logo.getchannel("A"))
glow = bright.filter(ImageFilter.GaussianBlur(8))
t1 = Image.new("RGBA", glow.size, (40, 216, 255, 0))
t1.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.5)))
glow2 = bright.filter(ImageFilter.GaussianBlur(3))
t2 = Image.new("RGBA", glow2.size, (255, 60, 110, 0))
t2.putalpha(glow2.getchannel("A").point(lambda v: int(v * 0.25)))

pad = 50
canvas = Image.new("RGBA", (cw + pad * 2, ch + pad * 2), (0, 0, 0, 0))
canvas.paste(t1, (pad, pad), t1)
canvas.paste(t2, (pad, pad), t2)
canvas.paste(logo, (pad, pad), logo)
canvas.save(OUT)

bg = Image.new("RGB", canvas.size, (10, 13, 24))
bg.paste(canvas, (0, 0), canvas)
bg.save(r"I:\Kimi project\Drop Zone\icons\_preview_logo.jpg", quality=92)
print("saved", OUT, canvas.size)
