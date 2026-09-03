# -*- coding: utf-8 -*-
# Иконки брони (12), рюкзака и перезарядки — плоский 2D стиль, как medkit/ap_battery.
import os
from PIL import Image, ImageDraw

D = r"G:\Kimi project\Drop Zone\game\assets\ui\icons"
TIER = {1: (154, 160, 168, 255), 2: (76, 175, 80, 255), 3: (61, 123, 214, 255), 4: (224, 138, 46, 255)}
BASE = (52, 58, 68, 255)
DARK = (30, 34, 40, 255)

def new_icon():
    return Image.new("RGBA", (256, 256), (0, 0, 0, 0))

def save(im, name):
    im.save(os.path.join(D, name))
    print("ok", name)

# ---------- ШЛЕМА ----------
def helmet(tier, kind):
    im = new_icon(); dr = ImageDraw.Draw(im)
    tc = TIER[tier]
    if kind == 1:  # кепка
        dr.pieslice([56, 80, 200, 220], 180, 360, fill=BASE, outline=tc, width=6)
        dr.rounded_rectangle([44, 148, 212, 176], 12, fill=DARK, outline=tc, width=5)
    else:
        dr.pieslice([52, 56, 204, 216], 180, 360, fill=BASE, outline=tc, width=7)
        dr.rectangle([52, 136, 204, 176], fill=BASE)
        dr.line([52, 176, 204, 176], fill=tc, width=7)
        if kind >= 3:  # тактический: очки
            dr.rounded_rectangle([78, 110, 178, 142], 10, fill=DARK, outline=tc, width=4)
            dr.line([128, 110, 128, 142], fill=tc, width=4)
        if kind == 4:  # бастион: полная маска
            dr.rounded_rectangle([64, 150, 192, 214], 14, fill=BASE, outline=tc, width=7)
            dr.rounded_rectangle([88, 168, 168, 190], 6, fill=DARK)
    return im

# ---------- НАГРУДНИКИ ----------
def body(tier, kind):
    im = new_icon(); dr = ImageDraw.Draw(im)
    tc = TIER[tier]
    if kind == 1:  # куртка
        dr.polygon([(84, 58), (172, 58), (192, 210), (64, 210)], fill=BASE, outline=tc)
        dr.line([128, 62, 128, 208], fill=tc, width=5)
        dr.line([84, 58, 66, 96], fill=tc, width=6)
        dr.line([172, 58, 190, 96], fill=tc, width=6)
    else:
        # жилет: торс без рукавов
        dr.polygon([(88, 62), (168, 62), (184, 206), (72, 206)], fill=BASE, outline=tc)
        dr.line([98, 100, 158, 100], fill=DARK, width=8)
        dr.line([96, 132, 160, 132], fill=DARK, width=8)
        dr.line([94, 164, 162, 164], fill=DARK, width=8)
        if kind >= 3:  # наплечники + пояс
            dr.ellipse([56, 48, 104, 92], fill=BASE, outline=tc, width=6)
            dr.ellipse([152, 48, 200, 92], fill=BASE, outline=tc, width=6)
            dr.line([78, 196, 178, 196], fill=tc, width=10)
        if kind == 4:  # джаггер: тяжёлая плита
            dr.polygon([(80, 70), (176, 70), (192, 212), (64, 212)], outline=tc)
            dr.line([88, 118, 168, 118], fill=tc, width=5)
            dr.line([86, 150, 170, 150], fill=tc, width=5)
    # контур жилета всегда тир-цветом потолще
    if kind > 1:
        dr.line([(88, 62), (72, 206)], fill=tc, width=6)
        dr.line([(168, 62), (184, 206)], fill=tc, width=6)
    return im

# ---------- ШТАНЫ ----------
def pants(tier, kind):
    im = new_icon(); dr = ImageDraw.Draw(im)
    tc = TIER[tier]
    # две штанины
    dr.polygon([(78, 56), (124, 56), (118, 214), (72, 214)], fill=BASE, outline=tc)
    dr.polygon([(132, 56), (178, 56), (184, 214), (138, 214)], fill=BASE, outline=tc)
    dr.line([78, 56, 178, 56], fill=tc, width=8)  # пояс
    if kind >= 2:  # карго-карманы
        dr.rectangle([64, 118, 88, 152], fill=DARK, outline=tc, width=4)
        dr.rectangle([168, 118, 192, 152], fill=DARK, outline=tc, width=4)
    if kind >= 3:  # наколенники
        dr.ellipse([80, 150, 112, 182], fill=DARK, outline=tc, width=4)
        dr.ellipse([144, 150, 176, 182], fill=DARK, outline=tc, width=4)
    if kind == 4:  # экзо-каркас
        dr.line([60, 70, 56, 208], fill=tc, width=5)
        dr.line([196, 70, 200, 208], fill=tc, width=5)
        dr.line([56, 140, 76, 140], fill=tc, width=5)
        dr.line([180, 140, 200, 140], fill=tc, width=5)
    return im

def backpack():
    im = new_icon(); dr = ImageDraw.Draw(im)
    tc = (210, 180, 90, 255)
    dr.rounded_rectangle([66, 70, 190, 216], 22, fill=BASE, outline=tc, width=7)
    dr.rounded_rectangle([86, 44, 170, 88], 14, fill=DARK, outline=tc, width=5)   # клапан
    dr.rounded_rectangle([92, 140, 164, 200], 12, fill=DARK, outline=tc, width=5)  # карман
    dr.line([66, 100, 40, 150], fill=tc, width=8)   # лямки
    dr.line([190, 100, 216, 150], fill=tc, width=8)
    return im

def reload():
    im = new_icon(); dr = ImageDraw.Draw(im)
    tc = (120, 200, 230, 255)
    dr.rounded_rectangle([104, 60, 152, 190], 8, fill=BASE, outline=tc, width=6)  # магазин
    dr.line([104, 96, 152, 96], fill=DARK, width=6)
    dr.line([104, 130, 152, 130], fill=DARK, width=6)
    dr.arc([52, 52, 204, 204], 300, 200, fill=tc, width=12)                       # круговая стрелка
    dr.polygon([(196, 150), (218, 186), (178, 184)], fill=tc)
    return im

for i in range(1, 5):
    save(helmet(i, i), "helm_%d.png" % i)
    save(body(i, i), "body_%d.png" % i)
    save(pants(i, i), "pants_%d.png" % i)
save(backpack(), "backpack.png")
save(reload(), "reload.png")
print("ICONS_DONE")
