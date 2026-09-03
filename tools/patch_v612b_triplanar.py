# -*- coding: utf-8 -*-
# v6.12b: правильное свойство трипланара — uv1_triplanar
import io, sys

p = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
s = io.open(p, encoding="utf-8").read()
orig = s

old = """		m.set_flag(BaseMaterial3D.FLAG_USE_TEXTURE_TRIPLANAR, true)"""
new = """		m.uv1_triplanar = true"""
c = s.count(old)
if c != 1:
    print("FAIL triplanar count=", c)
    sys.exit(1)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
