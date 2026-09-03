# -*- coding: utf-8 -*-
# v6.10e: портрет — прячем оружие у модели перед кадрированием головы;
#         инвентарь открывается ВМЕСТО панели бойца (нет наложения)
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

rep("""	var model: Node3D = load(H + f.model + ".gltf").instantiate()
	pv.add_child(model)
	_make_lit(model)""",
"""	var model: Node3D = load(H + f.model + ".gltf").instantiate()
	# в портрете оружие не нужно — только голова
	for wname in WEAPON_NODES:
		var wn := model.find_child(wname, true, false)
		if wn and wn is Node3D:
			wn.visible = false
	pv.add_child(model)
	_make_lit(model)""", "card_hide_guns")

rep("""func _toggle_inventory() -> void:
	if _selected < 0 or not _ui.has("inv_panel"):
		return
	if _ui.inv_panel.visible:
		_ui.inv_panel.visible = false
	else:
		_show_inventory()""",
"""func _toggle_inventory() -> void:
	if _selected < 0 or not _ui.has("inv_panel"):
		return
	if _ui.inv_panel.visible:
		_ui.inv_panel.visible = false
		if _ui.has("fighter_panel"):
			_ui.fighter_panel.visible = true
	else:
		_show_inventory()
		# инвентарь шире панели бойца — прячем её, чтобы не было наложения
		if _ui.has("fighter_panel"):
			_ui.fighter_panel.visible = false""", "inv_no_overlap")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
