# -*- coding: utf-8 -*-
# v6.10: 1) панель бойца справа — фон, не уходит за край, кнопки сеткой 2 колонки
#        2) портрет в карточке — только голова (камера ближе и выше)
#        3) иконки оружия из 3D-моделей (--rendericons) в инвентаре, ящике и слоте рук
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

# --- 1) панель бойца: фон + шире, не за экран ---
rep("""	var fp := PanelContainer.new()
	fp.anchor_left = 1.0
	fp.anchor_right = 1.0
	fp.offset_left = -272.0
	fp.offset_right = -12.0
	fp.offset_top = 96.0
	fp.offset_bottom = 356.0
	layer.add_child(fp)""",
"""	var fp := PanelContainer.new()
	fp.anchor_left = 1.0
	fp.anchor_right = 1.0
	fp.offset_left = -316.0
	fp.offset_right = -8.0
	fp.offset_top = 96.0
	fp.offset_bottom = 400.0
	fp.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(fp)""", "fp_frame")

# --- 1б) кнопки панели сеткой 2 колонки (не вылезают за ширину) ---
rep("""	var row := HBoxContainer.new()
	box.add_child(row)
	var inv := Button.new()
	inv.text = "Рюкзак [I]"
	inv.pressed.connect(_toggle_inventory)
	row.add_child(inv)
	var sw := Button.new()
	sw.text = "Нож/ствол [F]"
	sw.pressed.connect(_swap_weapon)
	row.add_child(sw)
	var rl := Button.new()
	rl.text = "Перезарядка [R]"
	rl.pressed.connect(_reload_selected)
	row.add_child(rl)
	if int(f.get("pts", 0)) > 0 and f.team == 0:
		var pb := Button.new()
		pb.text = "Навыки +%d" % int(f.pts)
		pb.pressed.connect(_show_levelup.bind(_selected))
		row.add_child(pb)
	_refresh_card()""",
"""	var row := GridContainer.new()
	row.columns = 2
	box.add_child(row)
	var inv := Button.new()
	inv.text = "Рюкзак [I]"
	inv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inv.pressed.connect(_toggle_inventory)
	inv.pressed.connect(_sfx_play.bind("click"))
	row.add_child(inv)
	var sw := Button.new()
	sw.text = "Нож/ствол [F]"
	sw.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sw.pressed.connect(_swap_weapon)
	sw.pressed.connect(_sfx_play.bind("click"))
	row.add_child(sw)
	var rl := Button.new()
	rl.text = "Перезарядка [R]"
	rl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rl.pressed.connect(_reload_selected)
	rl.pressed.connect(_sfx_play.bind("click"))
	row.add_child(rl)
	if int(f.get("pts", 0)) > 0 and f.team == 0:
		var pb := Button.new()
		pb.text = "Навыки +%d" % int(f.pts)
		pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		pb.pressed.connect(_show_levelup.bind(_selected))
		row.add_child(pb)
	_refresh_card()""", "fp_grid")

# --- 2) портрет: только голова ---
rep("""	var cam := Camera3D.new()
	cam.position = Vector3(0.4, 1.45, 2.6)
	cam.fov = 26.0
	pv.add_child(cam)
	cam.look_at(Vector3(0, 0.95, 0), Vector3.UP)""",
"""	var cam := Camera3D.new()
	cam.position = Vector3(0.18, 1.66, 1.1)
	cam.fov = 24.0
	pv.add_child(cam)
	cam.look_at(Vector3(0, 1.52, 0), Vector3.UP)""", "card_head")

# --- 3) режим офлайн-рендера иконок ---
rep("""	elif args.has("--testmenu"):
		_load_sfx()
		_build_ui()
		_build_menu()
		_run_testmenu()
	else:""",
"""	elif args.has("--testmenu"):
		_load_sfx()
		_build_ui()
		_build_menu()
		_run_testmenu()
	elif args.has("--rendericons"):
		_run_rendericons()
	else:""", "args_icons")

# --- 3б) функции рендера иконок + хелпер иконки предмета (перед _frame_box) ---
rep("""func _frame_box() -> StyleBoxFlat:""",
"""# ---------- иконки предметов: офлайн-рендер из 3D-моделей ----------
const ICON_ALIAS := {"Molotov": "FireGrenade", "knife_1": "Knife_1"}

func _node_aabb(n: Node) -> AABB:
	var out := AABB()
	var first := true
	var meshes: Array = []
	if n is MeshInstance3D:
		meshes.append(n)
	for mi2 in n.find_children("*", "MeshInstance3D", true, false):
		meshes.append(mi2)
	for mi in meshes:
		var a: AABB = (mi as MeshInstance3D).get_transformed_aabb()
		if first:
			out = a
			first = false
		else:
			out = out.merge(a)
	return out

func _run_rendericons() -> void:
	DirAccess.make_dir_recursive_absolute("G:/Kimi project/Drop Zone/game/assets/ui/icons")
	await get_tree().process_frame
	var vp := SubViewport.new()
	vp.size = Vector2i(256, 256)
	vp.transparent_bg = true
	vp.own_world_3d = true
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-50, -30, 0)
	sun.light_energy = 1.5
	vp.add_child(sun)
	var fill := OmniLight3D.new()
	fill.position = Vector3(-1.5, 1.0, 1.5)
	fill.light_energy = 0.9
	vp.add_child(fill)
	var cam := Camera3D.new()
	cam.position = Vector3(1.35, 0.95, 1.35)
	cam.fov = 30.0
	vp.add_child(cam)
	cam.look_at(Vector3.ZERO, Vector3.UP)
	cam.make_current()
	var soldier: Node3D = load(H + "Character_Soldier.gltf").instantiate()
	var ids: Array = WEAPON_NODES.duplicate()
	ids.append("Molotov")
	ids.append("medkit")
	for wid in ids:
		var node: Node3D = null
		if wid == "medkit":
			node = load(C + "Pickup_Health.gltf").instantiate()
		else:
			var node_name: String = ICON_ALIAS.get(wid, wid)
			var found := soldier.find_child(node_name, true, false)
			if found and found is Node3D:
				node = found.duplicate()
		if node == null:
			print("ICON_SKIP ", wid)
			continue
		vp.add_child(node)
		node.transform = Transform3D.IDENTITY
		var bb := _node_aabb(node)
		var sz: Vector3 = bb.size
		var mm: float = maxf(sz.x, maxf(sz.y, sz.z))
		if mm <= 0.0001:
			mm = 1.0
		var kk: float = 1.45 / mm
		node.scale = Vector3.ONE * kk
		node.position = -bb.get_center() * kk
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		vp.get_texture().get_image().save_png("G:/Kimi project/Drop Zone/game/assets/ui/icons/%s.png" % wid)
		print("ICON_OK ", wid)
		vp.remove_child(node)
		node.queue_free()
	print("ICONS_SAVED")
	get_tree().quit()

func _item_icon(entry: Dictionary) -> Texture2D:
	var iid: String = entry["item"].get("id", "")
	if iid == "":
		return null
	var ipath := "res://assets/ui/icons/%s.png" % iid
	if ResourceLoader.exists(ipath):
		return load(ipath)
	return null

func _icon_rect(tex: Texture2D, px := 36) -> TextureRect:
	var tr := TextureRect.new()
	tr.texture = tex
	tr.custom_minimum_size = Vector2(px, px)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	return tr

func _frame_box() -> StyleBoxFlat:""", "icon_fns")

# --- 3в) иконки в ящике ---
rep("""	for entry in _chests[k]:
		var l := Label.new()
		l.text = "• " + _entry_name(entry)
		box.add_child(l)""",
"""	for entry in _chests[k]:
		var rowh := HBoxContainer.new()
		rowh.add_theme_constant_override("separation", 8)
		var cic := _item_icon(entry)
		if cic != null:
			rowh.add_child(_icon_rect(cic))
		var l := Label.new()
		l.text = _entry_name(entry)
		rowh.add_child(l)
		box.add_child(rowh)""", "chest_icons")

# --- 3г) иконки в рюкзаке ---
rep("""		var b := Button.new()
		b.text = f.backpack[idx]["item"].get("name", "?")
		b.custom_minimum_size = Vector2(150, 52)""",
"""		var b := Button.new()
		b.text = f.backpack[idx]["item"].get("name", "?")
		var bic := _item_icon(f.backpack[idx])
		if bic != null:
			b.icon = bic
			b.expand_icon = true
			b.add_theme_constant_override("icon_max_width", 40)
		b.custom_minimum_size = Vector2(150, 52)""", "backpack_icons")

# --- 3д) иконка в слоте рук на силуэте ---
rep("""	var hands := Button.new()
	hands.text = "Руки: %s" % f.weapon.get("name", "?")""",
"""	var hands := Button.new()
	hands.text = "Руки: %s" % f.weapon.get("name", "?")
	var hic: Texture2D = _item_icon({"kind": "weapon", "item": f.weapon})
	if hic != null:
		hands.icon = hic
		hands.expand_icon = true
		hands.add_theme_constant_override("icon_max_width", 44)""", "hands_icon")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
