# v6.28 — боевой экран: критические фиксы + читаемость + неон-стиль
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()
fails = []

def rep(old, new, cnt=1):
    global src
    n = src.count(old)
    if n != cnt:
        fails.append("COUNT %d != %d: %r" % (n, cnt, old[:70]))
        return
    src = src.replace(old, new, cnt)

# ---- R1: новые переменные ----
rep("""var _sel_ring: MeshInstance3D = null
""", """var _sel_ring: MeshInstance3D = null
var _sel_name: Label3D = null         # имя активного бойца над головой
var _edge_arrows := {}                # idx -> {tri, dl}: стрелки на врагов за экраном
var _arrow_layer: Control = null
var _zone_lbl: Label3D = null
const TEAM_COLORS := [Color("#ff4757"), Color("#3498ff")]
""")

# ---- R2: кнопка «Конец хода» — красный неон ----
rep("""	btn.pressed.connect(_end_turn)
	btn.pressed.connect(_sfx_play.bind("click"))
	layer.add_child(btn)
	_ui.end_btn = btn
""", """	btn.pressed.connect(_end_turn)
	btn.pressed.connect(_sfx_play.bind("click"))
	var eb_n := StyleBoxFlat.new()
	eb_n.bg_color = Color(0.50, 0.10, 0.14, 0.95)
	eb_n.border_color = Color(1.0, 0.28, 0.40, 0.95)
	eb_n.set_border_width_all(2)
	eb_n.set_corner_radius_all(8)
	eb_n.shadow_color = Color(1.0, 0.2, 0.35, 0.35)
	eb_n.shadow_size = 8
	var eb_h: StyleBoxFlat = eb_n.duplicate()
	eb_h.bg_color = Color(0.72, 0.16, 0.20, 1.0)
	var eb_p: StyleBoxFlat = eb_n.duplicate()
	eb_p.bg_color = Color(0.34, 0.06, 0.09, 1.0)
	btn.add_theme_stylebox_override("normal", eb_n)
	btn.add_theme_stylebox_override("hover", eb_h)
	btn.add_theme_stylebox_override("pressed", eb_p)
	btn.add_theme_color_override("font_color", Color(1, 1, 1))
	btn.add_theme_color_override("font_hover_color", Color(1, 1, 1))
	btn.add_theme_font_size_override("font_size", 17)
	layer.add_child(btn)
	_ui.end_btn = btn
""")

# ---- R3: карточка бойца — рамка в цвет команды ----
rep("""	var card := PanelContainer.new()
	card.position = Vector2(12, 48)
	card.custom_minimum_size = Vector2(204, 168)
	layer.add_child(card)
""", """	var card := PanelContainer.new()
	card.position = Vector2(12, 48)
	card.custom_minimum_size = Vector2(204, 168)
	var card_sb := _frame_box()
	card_sb.border_color = Color(1.0, 0.28, 0.34, 0.8)
	card_sb.shadow_color = Color(1.0, 0.2, 0.35, 0.25)
	card.add_theme_stylebox_override("panel", card_sb)
	layer.add_child(card)
""")

# ---- R4: цветные бары HP/ОД ----
rep("""	_ui.card_ap_l = ap_l
	_ui.card_ap = ap_bar
""", """	_ui.card_ap_l = ap_l
	_ui.card_ap = ap_bar
	_style_bar(hp_bar, Color(0.25, 0.9, 0.3))
	_style_bar(ap_bar, Color(0.2, 0.8, 1.0))
""")

# ---- R5: слой стрелок на врагов ----
rep("""	_ui.inv_panel = iw
	_ui.inv_box = ivb
	_refresh_turn_lbl()
""", """	_ui.inv_panel = iw
	_ui.inv_box = ivb
	var al := Control.new()
	al.set_anchors_preset(Control.PRESET_FULL_RECT)
	al.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(al)
	_arrow_layer = al
	_refresh_turn_lbl()
""")

# ---- R6: правая панель шире (кнопки не обрезаются) ----
rep("""	fp.offset_left = -268.0
	fp.offset_right = -8.0
""", """	fp.offset_left = -296.0
	fp.offset_right = -8.0
""")

# ---- R7: панель ящика шире ----
rep("""	cp.offset_left = -200.0
	cp.offset_right = 200.0
""", """	cp.offset_left = -240.0
	cp.offset_right = 240.0
""")

# ---- R8: кнопки панели бойца — мельче шрифт и иконки ----
rep("""	inv.add_theme_constant_override("icon_max_width", 26)
""", """	inv.add_theme_constant_override("icon_max_width", 22)
""")
rep("""	inv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inv.pressed.connect(_toggle_inventory)
""", """	inv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inv.add_theme_font_size_override("font_size", 12)
	inv.pressed.connect(_toggle_inventory)
""")
rep("""	sw.add_theme_constant_override("icon_max_width", 26)
""", """	sw.add_theme_constant_override("icon_max_width", 22)
""")
rep("""	sw.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sw.pressed.connect(_swap_weapon)
""", """	sw.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sw.add_theme_font_size_override("font_size", 12)
	sw.pressed.connect(_swap_weapon)
""")
rep("""	rl.add_theme_constant_override("icon_max_width", 26)
""", """	rl.add_theme_constant_override("icon_max_width", 22)
""")
rep("""	rl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rl.pressed.connect(_reload_selected)
""", """	rl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rl.add_theme_font_size_override("font_size", 12)
	rl.pressed.connect(_reload_selected)
""")

# ---- R9: цифры стоимости хода крупнее ----
rep("""		cost_lbl.font_size = 44
""", """		cost_lbl.font_size = 64
""")
rep("""		cost_lbl.modulate = Color(0.75, 0.95, 1.0, 0.8)
		cost_lbl.outline_size = 10
""", """		cost_lbl.modulate = Color(1.0, 1.0, 1.0, 0.95)
		cost_lbl.outline_size = 12
""")

# ---- R10: имя над активным бойцом ----
rep("""	_sel_ring.visible = true
	_sel_ring.position = gw(_fighters[i].cell.x, _fighters[i].cell.y, 0.05)
	_refresh_fighter_panel()
""", """	_sel_ring.visible = true
	_sel_ring.position = gw(_fighters[i].cell.x, _fighters[i].cell.y, 0.05)
	if _sel_name == null:
		_sel_name = Label3D.new()
		_sel_name.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_sel_name.no_depth_test = true
		_sel_name.font_size = 60
		_sel_name.outline_size = 12
		_sel_name.outline_modulate = Color(0, 0, 0, 0.9)
		add_child(_sel_name)
	_sel_name.text = _fighters[i].name
	_sel_name.modulate = TEAM_COLORS[_fighters[i].team]
	_sel_name.visible = true
	_sel_name.position = gw(_fighters[i].cell.x, _fighters[i].cell.y, 2.95)
	_refresh_fighter_panel()
""")

# ---- R11: прятать имя при снятии выбора ----
rep("""	if _sel_ring:
		_sel_ring.visible = false
""", """	if _sel_ring:
		_sel_ring.visible = false
	if _sel_name:
		_sel_name.visible = false
""")

# ---- R12: хуки в _process ----
rep("""	_update_aim()

# ---------- эффекты: взрыв и гибель ----------
""", """	_update_aim()
	_update_sel_marker()
	_update_edge_arrows()
	_pulse_end_btn()

# ---------- эффекты: взрыв и гибель ----------
""")

# ---- R14: _frame_box — непрозрачный неон ----
rep("""	sb.bg_color = Color(0.04, 0.06, 0.11, 0.60)
	sb.border_color = Color(0.16, 0.85, 1.0, 0.55)
	sb.set_border_width_all(1)
""", """	sb.bg_color = Color(0.03, 0.05, 0.09, 0.92)
	sb.border_color = Color(0.16, 0.85, 1.0, 0.85)
	sb.set_border_width_all(2)
	sb.shadow_color = Color(0.16, 0.85, 1.0, 0.22)
	sb.shadow_size = 6
""")

# ---- R15: HP-бар по проценту (зелёный->жёлтый->красный) ----
rep("""	_ui.card_hp.max_value = f.max_hp
	_ui.card_hp.value = f.hp
""", """	_ui.card_hp.max_value = f.max_hp
	_ui.card_hp.value = f.hp
	var hr: float = float(f.hp) / maxf(1.0, float(f.max_hp))
	var hfill := _ui.card_hp.get_theme_stylebox("fill") as StyleBoxFlat
	if hfill:
		hfill.bg_color = Color(1.0 - hr * 0.8, 0.15 + hr * 0.72, 0.18)
		hfill.shadow_color = Color(1.0 - hr * 0.8, 0.15 + hr * 0.72, 0.18, 0.5)
""")

# ---- R16: рюкзак — 2 колонки (влезает в панель) ----
rep("""	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 6)
""", """	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 6)
""")

# ---- R17: кнопки рюкзака шире, шрифт мельче, рамка по типу ----
rep("""		b.custom_minimum_size = Vector2(150, 52)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
""", """		b.custom_minimum_size = Vector2(168, 56)
		b.add_theme_font_size_override("font_size", 13)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
""")
rep("""		var kind: String = f.backpack[idx]["kind"]
		var cat2: String = f.backpack[idx].get("cat", "")
""", """		var kind: String = f.backpack[idx]["kind"]
		var cat2: String = f.backpack[idx].get("cat", "")
		var kb := StyleBoxFlat.new()
		kb.bg_color = Color(0.05, 0.08, 0.12, 0.95)
		kb.set_corner_radius_all(6)
		kb.set_border_width_all(2)
		kb.border_color = {"weapon": Color(1.0, 0.35, 0.35, 0.8), "armor": Color(0.35, 0.7, 1.0, 0.8), "consumable": Color(0.4, 0.95, 0.5, 0.8)}.get(kind, Color(0.6, 0.6, 0.6, 0.8))
		b.add_theme_stylebox_override("normal", kb)
""")

# ---- R18: перенос строк в панели ящика ----
rep("""		var l := Label.new()
		l.text = _entry_name(entry)
		l.tooltip_text = _item_tooltip(entry)
""", """		var l := Label.new()
		l.text = _entry_name(entry)
		l.tooltip_text = _item_tooltip(entry)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
""")

# ---- R19: светящиеся окна домов ----
rep("""		_paint_house(hnode, tints[_rng.randi() % tints.size()])
""", """		_paint_house(hnode, tints[_rng.randi() % tints.size()])
		_add_house_windows(hnode)
""")

# ---- R20: подпись зоны ----
rep("""	for i in 4:
		(_zone_walls[i].mesh as BoxMesh).size = sizes[i]
		_zone_walls[i].position = poss[i]
""", """	for i in 4:
		(_zone_walls[i].mesh as BoxMesh).size = sizes[i]
		_zone_walls[i].position = poss[i]
	if _zone_lbl == null:
		_zone_lbl = Label3D.new()
		_zone_lbl.text = "ЗОНА РИСКА"
		_zone_lbl.font_size = 56
		_zone_lbl.modulate = Color(1.0, 0.25, 0.3)
		_zone_lbl.outline_size = 12
		_zone_lbl.outline_modulate = Color(0, 0, 0, 0.85)
		_zone_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_zone_lbl.no_depth_test = true
		add_child(_zone_lbl)
	_zone_lbl.position = Vector3(midx, 3.1, p0.z)
""")

# ---- R13: новые функции перед _frame_box ----
rep("""func _frame_box() -> StyleBoxFlat:
""", """func _style_bar(bar: ProgressBar, fill_col: Color) -> void:
	# цветной бар с подсветкой вместо серого системного
	var bg := StyleBoxFlat.new()
	bg.bg_color = Color(0.03, 0.05, 0.07, 0.90)
	bg.set_corner_radius_all(4)
	bg.set_border_width_all(1)
	bg.border_color = Color(0.5, 0.6, 0.65, 0.4)
	var fg := StyleBoxFlat.new()
	fg.bg_color = fill_col
	fg.set_corner_radius_all(4)
	fg.shadow_color = Color(fill_col.r, fill_col.g, fill_col.b, 0.5)
	fg.shadow_size = 4
	bar.add_theme_stylebox_override("background", bg)
	bar.add_theme_stylebox_override("fill", fg)

func _update_sel_marker() -> void:
	# пульсирующее кольцо и имя над активным бойцом (цвет команды)
	if _selected < 0 or _selected >= _fighters.size() or _sel_ring == null or not _sel_ring.visible:
		return
	var f = _fighters[_selected]
	var s := 1.0 + 0.10 * sin(Time.get_ticks_msec() * 0.005)
	_sel_ring.scale = Vector3(s, 1.0, s)
	_sel_ring.position = f.node.position + Vector3(0, 0.05, 0)
	if _sel_name:
		_sel_name.position = f.node.position + Vector3(0, 2.95, 0)

func _pulse_end_btn() -> void:
	# «Конец хода» пульсирует, когда у бойца не осталось ОД
	if not _ui.has("end_btn"):
		return
	var b: Button = _ui.end_btn
	var hot := false
	if _selected >= 0 and _selected < _fighters.size() and not _menu_open and not _game_over:
		var f = _fighters[_selected]
		hot = f.alive and f.team == 0 and int(f.ap) <= 0
	if hot:
		var g := 1.0 + 0.35 * sin(Time.get_ticks_msec() * 0.006)
		b.modulate = Color(g, g, g)
	elif b.modulate != Color(1, 1, 1):
		b.modulate = Color(1, 1, 1)

func _update_edge_arrows() -> void:
	# красные стрелки у края экрана на видимых врагов вне кадра + дистанция
	if _arrow_layer == null or _cam == null:
		return
	var vr: Vector2 = _arrow_layer.size
	if vr.x < 10.0:
		return
	var center: Vector2 = vr * 0.5
	var margin := 48.0
	var shown := {}
	for fi in _fighters.size():
		var f = _fighters[fi]
		if f.team != 1 or not f.alive or not f.node.visible or _menu_open or _game_over:
			continue
		var wp: Vector3 = f.node.position + Vector3(0, 1.2, 0)
		var sp: Vector2 = _cam.unproject_position(wp)
		if _cam.is_position_behind(wp):
			sp = center - (sp - center)
		if sp.x > margin and sp.y > margin and sp.x < vr.x - margin and sp.y < vr.y - margin:
			continue
		var pos: Vector2 = sp
		pos.x = clampf(pos.x, margin, vr.x - margin)
		pos.y = clampf(pos.y, margin, vr.y - margin)
		var ang: float = (pos - center).angle()
		var dist := 0
		if _selected >= 0 and _selected < _fighters.size():
			dist = int(round(Vector2(f.cell.x - _fighters[_selected].cell.x, f.cell.y - _fighters[_selected].cell.y).length()))
		var e: Dictionary
		if _edge_arrows.has(fi):
			e = _edge_arrows[fi]
		else:
			var tri := Polygon2D.new()
			tri.polygon = PackedVector2Array([Vector2(17, 0), Vector2(-9, -10), Vector2(-5, 0), Vector2(-9, 10)])
			tri.color = Color(1.0, 0.25, 0.3, 0.92)
			_arrow_layer.add_child(tri)
			var dl := Label2D.new()
			dl.add_theme_font_size_override("font_size", 15)
			dl.add_theme_color_override("font_color", Color(1.0, 0.5, 0.55))
			dl.add_theme_color_override("font_outline_color", Color(0, 0, 0))
			dl.add_theme_constant_override("outline_size", 6)
			dl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			_arrow_layer.add_child(dl)
			e = {"tri": tri, "dl": dl}
			_edge_arrows[fi] = e
		e.tri.position = pos
		e.tri.rotation = ang
		e.tri.visible = true
		if dist > 0:
			e.dl.text = "%d м" % dist
		else:
			e.dl.text = ""
		e.dl.position = pos + Vector2(-20, 14)
		e.dl.visible = true
		shown[fi] = true
	for fi2 in _edge_arrows.keys():
		if not shown.has(fi2):
			_edge_arrows[fi2].tri.visible = false
			_edge_arrows[fi2].dl.visible = false

func _add_house_windows(hnode: Node3D) -> void:
	# светящиеся окна — «телешоу будущего»: тёплые/неоновые вставки на стенах
	var bb := _node_aabb(hnode)
	if bb.size.x < 1.0 or bb.size.y < 1.5:
		return
	var cols := [Color(1.0, 0.72, 0.28), Color(0.35, 0.9, 1.0), Color(1.0, 0.45, 0.6)]
	var wcol: Color = cols[_rng.randi() % cols.size()]
	var wm := _mat(Color(0.02, 0.02, 0.03), 0.0, 1.0, wcol, 2.6)
	var n_win := _rng.randi_range(4, 7)
	for i in n_win:
		var q := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(_rng.randf_range(0.5, 0.9), _rng.randf_range(0.6, 1.1), 0.06)
		q.mesh = bm
		q.material_override = wm
		var side := _rng.randi() % 4
		var y := _rng.randf_range(bb.position.y + bb.size.y * 0.30, bb.position.y + bb.size.y * 0.82)
		var px := _rng.randf_range(bb.position.x + bb.size.x * 0.2, bb.end.x - bb.size.x * 0.2)
		var pz := _rng.randf_range(bb.position.z + bb.size.z * 0.2, bb.end.z - bb.size.z * 0.2)
		var p := Vector3.ZERO
		var ry := 0.0
		match side:
			0:
				p = Vector3(px, y, bb.end.z + 0.03)
			1:
				p = Vector3(px, y, bb.position.z - 0.03)
				ry = PI
			2:
				p = Vector3(bb.end.x + 0.03, y, pz)
				ry = PI * 0.5
			3:
				p = Vector3(bb.position.x - 0.03, y, pz)
				ry = -PI * 0.5
		hnode.add_child(q)
		q.global_position = p
		q.global_rotation = Vector3(0, ry, 0)

func _frame_box() -> StyleBoxFlat:
""")

# ---- R21: убрать отладочную строку из _run_testmenu ----
import re
src2, n_dbg = re.subn(r'\tprint\("DBG window=.*\)\n', "", src)
if n_dbg == 1:
    src = src2
elif n_dbg > 1:
    fails.append("DBG lines: %d" % n_dbg)

if fails:
    print("\n".join(fails))
    print("FAIL")
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ALL_OK")
