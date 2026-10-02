# -*- coding: utf-8 -*-
"""Заменить JS-часть head_include в export_presets.cfg на содержимое tools/_head_scripts_new.html."""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg_path = os.path.join(ROOT, "game", "export_presets.cfg")
src = open(cfg_path, encoding="utf-8").read()

i = src.index('html/head_include="') + len('html/head_include="')
j = i
while True:
    k = src.index('"', j)
    if src[k - 1] != chr(92):
        break
    j = k + 1
val = src[i:k].replace(chr(92) + '"', '"')

new_scripts = open(os.path.join(ROOT, "tools", "_head_scripts_new.html"), encoding="utf-8").read().strip()
pos = val.index('<script src="vk-bridge.min.js"')
new_val = val[:pos] + new_scripts
escaped = new_val.replace('"', chr(92) + '"')
src = src[:i] + escaped + src[k:]
open(cfg_path, "w", encoding="utf-8", newline="\n").write(src)
print("head_include обновлён,", len(new_val), "символов")
