# Логотип «ТОЧКА СБРОСА — Королевская битва» в стиле старого (белое + бирюзовое свечение + розовый подзаголовок)
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 1200, 300
FONT = r"G:\Kimi project\Drop Zone\game\assets\fonts\Manrope.ttf"
OUT = r"G:\Kimi project\Drop Zone\game\assets\ui\logo.png"

img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

def draw_tracked(draw, pos, text, font, fill, tracking=0, anchor_center_x=None, stroke_width=0, stroke_fill=None):
    widths = [draw.textlength(ch, font=font) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = pos[0] if anchor_center_x is None else anchor_center_x - total / 2
    y = pos[1]
    for ch, w in zip(text, widths):
        draw.text((x, y), ch, font=font, fill=fill, stroke_width=stroke_width, stroke_fill=stroke_fill)
        x += w + tracking
    return total

# линии сверху/снизу
d.rectangle([0, 4, W, 7], fill=(40, 216, 255, 200))
d.rectangle([160, H - 8, W - 160, H - 5], fill=(255, 60, 110, 200))

f_main = ImageFont.truetype(FONT, 130)
f_sub = ImageFont.truetype(FONT, 44)

# свечение под основным текстом
glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
dg = ImageDraw.Draw(glow)
draw_tracked(dg, (0, 30), "ТОЧКА СБРОСА", f_main, (40, 216, 255, 255), tracking=10, anchor_center_x=W / 2, stroke_width=4, stroke_fill=(40, 216, 255, 255))
glow = glow.filter(ImageFilter.GaussianBlur(9))
img.alpha_composite(glow)

# основной текст — белый, утолщённый белой обводкой
d = ImageDraw.Draw(img)
draw_tracked(d, (0, 28), "ТОЧКА СБРОСА", f_main, (245, 250, 255, 255), tracking=10, anchor_center_x=W / 2, stroke_width=5, stroke_fill=(245, 250, 255, 255))

# подзаголовок — розовый, разрядка
draw_tracked(d, (0, 208), "КОРОЛЕВСКАЯ БИТВА", f_sub, (255, 60, 110, 255), tracking=16, anchor_center_x=W / 2, stroke_width=2, stroke_fill=(255, 60, 110, 255))

img.save(OUT)
print("saved", OUT)
