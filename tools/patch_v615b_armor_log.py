# -*- coding: utf-8 -*-
# v6.15b: в логе видно, сколько урона съела броня
import io, sys

p = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
s = io.open(p, encoding="utf-8").read()
orig = s

old = """	_sfx_play("hit")
	_log("%s -> %s: %d урона (HP %d)" % [src_name, d.name, real, d.hp])"""
new = """	_sfx_play("hit")
	var arm_txt := ""
	if dmg > real:
		arm_txt = " (броня -%d)" % (dmg - real)
	_log("%s -> %s: %d урона%s (HP %d)" % [src_name, d.name, real, arm_txt, d.hp])"""
c = s.count(old)
if c != 1:
    print("FAIL armor_log count=", c)
    sys.exit(1)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
