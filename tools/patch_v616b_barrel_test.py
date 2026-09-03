# -*- coding: utf-8 -*-
# v6.16b: автопроверка правила бочки в --testplay
import io, sys

p = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
s = io.open(p, encoding="utf-8").read()
orig = s

old = """	print("ARMOR_TEST защита=", _defense(f0), " урон50->", hp0 - f0.hp, " (ожидается 42)")
	f0.hp = hp0
	f0.armor["body"] = null"""
new = """	print("ARMOR_TEST защита=", _defense(f0), " урон50->", hp0 - f0.hp, " (ожидается 42)")
	f0.hp = hp0
	f0.armor["body"] = null
	# проверка бочки: 27 HP + 2 обязательных попадания (43 урона за раз мало)
	var bk := ""
	for ck9 in _covers.keys():
		if _covers[ck9].get("barrel", false):
			bk = ck9
			break
	if bk != "":
		_damage_cover_hit(bk, 43, "TEST")
		print("BARREL_TEST 1-е попадание 43: жива=", _covers.has(bk), " (ожидается true)")
		_damage_cover_hit(bk, 43, "TEST")
		print("BARREL_TEST 2-е попадание: жива=", _covers.has(bk), " (ожидается false)")"""
c = s.count(old)
if c != 1:
    print("FAIL barrel_test count=", c)
    sys.exit(1)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
