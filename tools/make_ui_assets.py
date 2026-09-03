# Нарезка 6 аватаров из сетки 3x2 + логотип + фон меню
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

ROOT = r"G:\Kimi project\Drop Zone"

# --- 1) аватары av1..av6.png (512x512) ---
grid = Image.open(os.path.join(ROOT, "docs", "avatars_grid.png")).convert("RGB")
W, H = grid.size  # 1536x1024
cw, ch = W // 3, H // 2
outdir = os.path.join(ROOT, "game", "assets", "ui", "avatars")
os.makedirs(outdir, exist_ok=True)
n = 1
for r in range(2):
    for c in range(3):
        cell = grid.crop((c * cw + 10, r * ch + 10, (c + 1) * cw - 10, (r + 1) * ch - 10))
        if n == 4:  # водяной знак в левом нижнем углу ячейки 4
            d = ImageDraw.Draw(cell)
            d.rectangle([0, cell.size[1] - 80, 130, cell.size[1]], fill=(8, 10, 16))
        cell = cell.resize((512, 512), Image.LANCZOS)
        cell.save(os.path.join(outdir, "av%d.png" % n))
        n += 1
print("AVATARS_OK", outdir)

# --- 2) фон меню из концепт-арта (без текста) ---
art = Image.open(os.path.join(ROOT, "docs", "splash_art_raw.png")).convert("RGB")
art = art.resize((1600, 1600), Image.LANCZOS)
art.save(os.path.join(ROOT, "game", "assets", "ui", "menu_bg.jpg"), quality=82)
print("MENU_BG_OK")

# --- 3) логотип logo.png (прозрачный, неоновое свечение) ---
LW, LH = 1200, 300
logo = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
d = ImageDraw.Draw(logo)
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

f1 = fit("DROP ZONE", 190, int(LW * 0.92))
f2 = fit("ROYAL BATTLE", 76, int(LW * 0.60))

def ctext(y, text, font):
    bb = d.textbbox((0, 0), text, font=font)
    return ((LW - (bb[2] - bb[0])) // 2 - bb[0], y)

# свечение: рисуем текст в отдельный слой, размываем, кладём под основной
glow = Image.new("RGBA", (LW, LH), (0, 0, 0, 0))
gd = ImageDraw.Draw(glow)
gd.text(ctext(20, "DROP ZONE", f1), "DROP ZONE", font=f1, fill=(40, 216, 255, 255))
gd.text(ctext(220, "ROYAL BATTLE", f2), "ROYAL BATTLE", font=f2, fill=(255, 60, 110, 255))
glow = glow.filter(ImageFilter.GaussianBlur(14))
logo = Image.alpha_composite(logo, glow)
d = ImageDraw.Draw(logo)
# неоновые линии над и под
d.line([(60, 8), (LW - 60, 8)], fill=(40, 216, 255, 200), width=3)
d.line([(160, 292), (LW - 160, 292)], fill=(255, 60, 110, 200), width=3)
d.text(ctext(20, "DROP ZONE", f1), "DROP ZONE", font=f1, fill=(245, 248, 255, 255))
d.text(ctext(220, "ROYAL BATTLE", f2), "ROYAL BATTLE", font=f2, fill=(255, 90, 135, 255))
logo.save(os.path.join(ROOT, "game", "assets", "ui", "logo.png"))
# превью на тёмном для проверки
prev = Image.new("RGB", (LW, LH), (6, 8, 14))
prev.paste(logo, (0, 0), logo)
prev.save(os.path.join(ROOT, "docs", "logo_preview.png"))
print("LOGO_OK")
