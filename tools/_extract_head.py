# -*- coding: utf-8 -*-
src = open("game/export_presets.cfg", encoding="utf-8").read()
i = src.index('html/head_include="') + len('html/head_include="')
j = i
while True:
    k = src.index('"', j)
    if src[k - 1] != chr(92):  # неэкранированная кавычка
        break
    j = k + 1
val = src[i:k].replace(chr(92) + '"', '"').replace(chr(92) + "n", "\n")
open("head_include_extracted.html", "w", encoding="utf-8").write(val)
print(len(val))
