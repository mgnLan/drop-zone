# -*- coding: utf-8 -*-
"""Перенос рабочего JS-моста из живого prod index.html в export_presets.cfg (head_include).

Гарантирует посимвольное совпадение с продом: берём блок от <script src="vk-bridge.min.js"
до закрывающего </script> из скачанного index.html и подставляем в .cfg с экранированием.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
prod = open(os.path.join(ROOT, "deploy_regru", "prod_snapshot", "index.html"), encoding="utf-8").read()
start = prod.index('<script src="vk-bridge.min.js"')
end = prod.index("})();</script>", start) + len("})();</script>")
block = prod[start:end]
# одна строка без переносов (в .cfg значение — однострочное)
block = " ".join(line.strip() for line in block.splitlines() if line.strip())
open(os.path.join(ROOT, "tools", "_head_scripts_new.html"), "w", encoding="utf-8").write(block)

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
pos = val.index('<script src="vk-bridge.min.js"')
new_val = val[:pos] + block
escaped = new_val.replace('"', chr(92) + '"')
src = src[:i] + escaped + src[k:]
open(cfg_path, "w", encoding="utf-8", newline="\n").write(src)
print("мост перенесён,", len(block), "символов")
