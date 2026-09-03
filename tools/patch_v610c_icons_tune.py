# -*- coding: utf-8 -*-
# v6.10c: иконки — FireGrenade/Molotov -> модель Grenade; больше отступ (kk 1.15);
#         medkit убран из 3D-рендера (сделаем 2D через PIL)
import io, sys

p = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
s = io.open(p, encoding="utf-8").read()
orig = s
fails = []

def rep(old, new, tag, cnt=1):
    global s
    c = s.count(old)
    if c != cnt:
        fails.append((tag, c))
        print("FAIL", tag, "count=", c)
        return
    s = s.replace(old, new)
    print("ok", tag)

rep('''const ICON_ALIAS := {"Molotov": "FireGrenade", "knife_1": "Knife_1"}''',
'''const ICON_ALIAS := {"Molotov": "Grenade", "FireGrenade": "Grenade", "knife_1": "Knife_1"}''', "alias")

rep("""		var kk: float = 1.45 / mm""",
"""		var kk: float = 1.15 / mm""", "margin")

rep("""	ids.append("Molotov")
	ids.append("medkit")""",
"""	ids.append("Molotov")""", "no_medkit")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
