# -*- coding: utf-8 -*-
# v6.15: тултипы характеристик, иконки брони/кнопок, подсветка «Навыки»,
#         низ панели бойца короче, автопроверка защиты брони в --testplay
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

TT_SEP = "\\n—\\n"   # в файл уйдёт литеральная последовательность \n—\n

# --- 1) хелпер тултипа предмета (перед _frame_box) ---
rep("""func _frame_box() -> StyleBoxFlat:""",
"""func _item_tooltip(entry: Dictionary) -> String:
	var it: Dictionary = entry["item"]
	match entry["kind"]:
		"weapon":
			var st := "%s\\nУрон: %d" % [it.get("name", "?"), it.get("damage", 0)]
			if int(it.get("burst", 1)) > 1:
				st += " ×%d пули" % int(it["burst"])
			st += "\\nОД: %d · Дальность: %d" % [it.get("ap_cost", 0), it.get("range", 0)]
			if it.has("ammo"):
				st += "\\nПатроны: %d" % int(it["ammo"])
			if int(it.get("aoe", 0)) > 0:
				st += "\\nВзрыв: радиус %d (край 60%%)" % int(it["aoe"])
			if it.get("burn", false):
				st += "\\nПоджигает клетки (3 раунда)"
			st += "\\nВес: %.1f кг" % _item_weight(entry)
			return st
		"armor":
			var st2 := "%s\\nЗащита: %d" % [it.get("name", "?"), it.get("defense", 0)]
			if int(it.get("carry_bonus", 0)) > 0:
				st2 += "\\nНосимый вес: +%d кг" % int(it["carry_bonus"])
			st2 += "\\nВес: %.1f кг" % _item_weight(entry)
			return st2
		_:
			var st3 := "%s" % it.get("name", "?")
			if it.has("heal"):
				st3 += "\\nЛечит: +%d HP" % int(it["heal"])
			if it.has("ap_restore"):
				st3 += "\\nВосстанавливает: +%d ОД" % int(it["ap_restore"])
			st3 += "\\nОД на использование: %d" % int(it.get("ap_cost", 0))
			st3 += "\\nВес: %.1f кг" % _item_weight(entry)
			return st3
	return ""

func _frame_box() -> StyleBoxFlat:""", "tooltip_fn")

# --- 2) тултип на кнопках рюкзака ---
old = '\t\tb.tooltip_text = "Клик — надеть/использовать; перетащить — в слот"'
new = '\t\tb.tooltip_text = _item_tooltip(f.backpack[idx]) + "' + TT_SEP + 'Клик — надеть/использовать; перетащить — в слот"'
rep(old, new, "bp_tooltip")

# --- 3) тултип в строках ящика ---
rep("""		var l := Label.new()
		l.text = _entry_name(entry)
		rowh.add_child(l)""",
"""		var l := Label.new()
		l.text = _entry_name(entry)
		l.tooltip_text = _item_tooltip(entry)
		rowh.add_child(l)""", "chest_tooltip")

# --- 4) слоты силуэта: иконка брони + тултип ---
old = '\t\tb.tooltip_text = "Клик — снять; сюда можно перетащить броню из рюкзака"'
new = ('\t\tif it:\n'
       '\t\t\tvar sit := _item_icon({"kind": "armor", "cat": cat, "item": it})\n'
       '\t\t\tif sit != null:\n'
       '\t\t\t\tb.icon = sit\n'
       '\t\t\t\tb.add_theme_constant_override("icon_max_width", 30)\n'
       '\t\t\tb.tooltip_text = _item_tooltip({"kind": "armor", "cat": cat, "item": it}) + "' + TT_SEP + 'Клик — снять"\n'
       '\t\telse:\n'
       '\t\t\tb.tooltip_text = "Пусто — перетащи броню из рюкзака"')
rep(old, new, "slot_tooltip")

# --- 5) тултип слота рук ---
old = '\thands.tooltip_text = "Клик — нож/ствол; сюда можно перетащить оружие из рюкзака"'
new = '\thands.tooltip_text = _item_tooltip({"kind": "weapon", "item": f.weapon}) + "' + TT_SEP + 'Клик — нож/ствол; перетащить оружие из рюкзака"'
rep(old, new, "hands_tooltip")

# --- 6) панель бойца: низ короче (96..336 вместо 96..400) ---
rep("""	fp.offset_top = 96.0
	fp.offset_bottom = 400.0""",
"""	fp.offset_top = 96.0
	fp.offset_bottom = 336.0""", "fp_height")

# --- 7) иконки на кнопках панели + золотая подсветка «Навыки» ---
rep("""	var inv := Button.new()
	inv.text = "Рюкзак [I]"
	inv.size_flags_horizontal = Control.SIZE_EXPAND_FILL""",
"""	var inv := Button.new()
	inv.text = "Рюкзак [I]"
	if ResourceLoader.exists("res://assets/ui/icons/backpack.png"):
		inv.icon = load("res://assets/ui/icons/backpack.png")
		inv.add_theme_constant_override("icon_max_width", 26)
	inv.size_flags_horizontal = Control.SIZE_EXPAND_FILL""", "inv_icon")

rep("""	var sw := Button.new()
	sw.text = "Нож/ствол [F]"
	sw.size_flags_horizontal = Control.SIZE_EXPAND_FILL""",
"""	var sw := Button.new()
	sw.text = "Нож/ствол [F]"
	if ResourceLoader.exists("res://assets/ui/icons/Knife_1.png"):
		sw.icon = load("res://assets/ui/icons/Knife_1.png")
		sw.add_theme_constant_override("icon_max_width", 26)
	sw.size_flags_horizontal = Control.SIZE_EXPAND_FILL""", "sw_icon")

rep("""	var rl := Button.new()
	rl.text = "Перезарядка [R]"
	rl.size_flags_horizontal = Control.SIZE_EXPAND_FILL""",
"""	var rl := Button.new()
	rl.text = "Перезарядка [R]"
	if ResourceLoader.exists("res://assets/ui/icons/reload.png"):
		rl.icon = load("res://assets/ui/icons/reload.png")
		rl.add_theme_constant_override("icon_max_width", 26)
	rl.size_flags_horizontal = Control.SIZE_EXPAND_FILL""", "rl_icon")

rep("""		var pb := Button.new()
		pb.text = "Навыки +%d" % int(f.pts)
		pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL""",
"""		var pb := Button.new()
		pb.text = "Навыки +%d" % int(f.pts)
		pb.add_theme_color_override("font_color", Color(1.0, 0.92, 0.4))
		var pbs := StyleBoxFlat.new()
		pbs.bg_color = Color(0.45, 0.33, 0.08, 0.95)
		pbs.border_color = Color(1.0, 0.85, 0.3, 0.95)
		pbs.set_border_width_all(2)
		pbs.set_corner_radius_all(6)
		pb.add_theme_stylebox_override("normal", pbs)
		pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL""", "pb_gold")

# --- 8) автопроверка брони в --testplay ---
rep("""	_log("TESTPLAY: ящик вскрыт, лут в рюкзаке")""",
"""	_log("TESTPLAY: ящик вскрыт, лут в рюкзаке")
	# проверка брони: жилет защита 8, удар 50 -> 42
	var f0 = _fighters[0]
	f0.backpack.append({"kind": "armor", "cat": "body", "item": _items["armor"]["body"][1]})
	_use_backpack(f0.backpack.size() - 1)
	var hp0: int = f0.hp
	_apply_damage(0, 50, "TEST")
	print("ARMOR_TEST защита=", _defense(f0), " урон50->", hp0 - f0.hp, " (ожидается 42)")
	f0.hp = hp0
	f0.armor["body"] = null""", "armor_test")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
