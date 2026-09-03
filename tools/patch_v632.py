# -*- coding: utf-8 -*-
# v6.32: «шоу» — могилы со скинами, насмешки (аггро ботов), граффити, телепорты
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    c = src.count(old)
    if c != 1:
        print("FAIL: маркер найден %d раз (нужно 1):" % c)
        print(old[:120])
        sys.exit(1)
    src = src.replace(old, new)

# ---- 1. Поля аггро в бойце ----
rep("""		"talents": talents.duplicate(), "tpts": tpts, "prof": prof.duplicate(),
""", """		"talents": talents.duplicate(), "tpts": tpts, "prof": prof.duplicate(),
		"aggro_to": -1, "aggro_ttl": 0,
""")

# ---- 2. Могила при гибели ----
rep("""	_log("%s выбыл из шоу!" % f.name)
""", """	_log("%s выбыл из шоу!" % f.name)
	_spawn_grave(f)
""")

# ---- 3. Телепорт при спавне ----
rep("""	for wn in WEAPON_NODES:
		var w := p.find_child(wn, true, false)
		if w and w is Node3D:
			w.visible = (wn == weapon)
""", """	for wn in WEAPON_NODES:
		var w := p.find_child(wn, true, false)
		if w and w is Node3D:
			w.visible = (wn == weapon)
	_teleport_in(p, Vector2i(gx, gz))
""")

# ---- 4. Аггро в ходе бота ----
rep("""func _bot_act(i: int) -> void:
	var f = _fighters[i]
	var guard := 0
""", """func _bot_act(i: int) -> void:
	var f = _fighters[i]
	if int(f.get("aggro_ttl", 0)) > 0:
		f.aggro_ttl = int(f.get("aggro_ttl", 0)) - 1
	var guard := 0
""")
rep("""		var vis: int = f.get("vision", VISION)
		var t := _nearest_visible_enemy(f.cell, vis, 0)
""", """		var vis: int = f.get("vision", VISION)
		var t := _bot_pick_target(f, vis)
""")

# ---- 5. Кнопки насмешки и граффити в панели действий ----
rep("""	rl.pressed.connect(_reload_selected)
	rl.pressed.connect(_sfx_play.bind("click"))
	row.add_child(rl)
""", """	rl.pressed.connect(_reload_selected)
	rl.pressed.connect(_sfx_play.bind("click"))
	row.add_child(rl)
	var tt := Button.new()
	tt.text = "😈 Насмешка [T]"
	tt.tooltip_text = "Насмешка (1 ОД): боты в радиусе 8 клеток 2 хода атакуют этого бойца"
	tt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tt.add_theme_font_size_override("font_size", 12)
	tt.pressed.connect(_taunt_selected)
	tt.pressed.connect(_sfx_play.bind("click"))
	row.add_child(tt)
	var gf := Button.new()
	gf.text = "🎨 Граффити [G]"
	gf.tooltip_text = "Граффити (1 ОД): оставить яркую метку на клетке"
	gf.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	gf.add_theme_font_size_override("font_size", 12)
	gf.pressed.connect(_graffiti_selected)
	gf.pressed.connect(_sfx_play.bind("click"))
	row.add_child(gf)
""")

# ---- 6. Горячие клавиши T / G ----
rep("""			KEY_I:
				_toggle_inventory()
""", """			KEY_I:
				_toggle_inventory()
			KEY_T:
				_taunt_selected()
			KEY_G:
				_graffiti_selected()
""")

# ---- 7. Реестр граффити ----
rep("""var _fire := {}                    # Vector2i -> осталось раундов
""", """var _fire := {}                    # Vector2i -> осталось раундов
var _graffiti := {}                # ключ клетки -> true (метка оставлена)
""")

# ---- 8. Выбор телепорта в настройках ----
rep("""	var note := Label.new()
	note.text = "(звуки: выстрел, попадание, шаги, вскрытие ящика)"
	vb.add_child(note)
""", """	var tprow := HBoxContainer.new()
	vb.add_child(tprow)
	var tpl := Label.new()
	tpl.text = "Телепорт: "
	tprow.add_child(tpl)
	for tp in [["beam", "☄ Луч"], ["hole", "🕳 Дыра"], ["storm", "⚡ Шторм"]]:
		var tb2 := Button.new()
		var tid: String = tp[0]
		var locked := tid == "storm"
		tb2.text = str(tp[1]) + (" ✓" if str(_profile.get("teleport", "beam")) == tid else "")
		tb2.disabled = locked
		if locked:
			tb2.tooltip_text = "Эксклюзив Battle Pass — появится в 1 сезоне"
		else:
			tb2.pressed.connect(func():
				_profile.teleport = tid
				_save_profile()
				_show_menu_settings()
			)
		tprow.add_child(tb2)
	var note := Label.new()
	note.text = "(звуки: выстрел, попадание, шаги, вскрытие ящика)"
	vb.add_child(note)
""")

# ---- 9. Сейв/лоад выбора телепорта ----
rep("""	_profile.daily_claimed = cfg.get_value("player", "daily_claimed", [0, 0, 0])
""", """	_profile.daily_claimed = cfg.get_value("player", "daily_claimed", [0, 0, 0])
	_profile.teleport = str(cfg.get_value("player", "teleport", "beam"))
""")
rep("""	cfg.set_value("player", "daily_claimed", _profile.get("daily_claimed", [0, 0, 0]))
""", """	cfg.set_value("player", "daily_claimed", _profile.get("daily_claimed", [0, 0, 0]))
	cfg.set_value("player", "teleport", str(_profile.get("teleport", "beam")))
""")

# ---- 10. Новые функции (перед _setup_lighting) ----
rep("""# ---------------- СВЕТ ----------------
func _setup_lighting() -> void:
""", """# ---------------- ШОУ: могилы, насмешки, граффити, телепорты ----------------
const TAUNT_LINES := [
	"Эй, мешки с мясом! Я здесь!",
	"Стреляй в меня, если сможешь!",
	"Твоя мама была тостером!",
	"Идите сюда, по одному!",
	"Это всё, на что вы способны?!",
]
const GRAFFITI_COLORS := [Color(0.2, 0.9, 1.0), Color(1.0, 0.25, 0.8), Color(0.5, 1.0, 0.25), Color(1.0, 0.65, 0.15), Color(0.8, 0.4, 1.0)]

func _spawn_grave(f: Dictionary) -> void:
	# надгробие на клетке гибели; стиль по уровню бойца: крест (1-2) / плита (3-4) / обелиск (5+)
	var lv := int(f.get("lvl", 1))
	var g := Node3D.new()
	g.position = gw(f.cell.x, f.cell.y) + Vector3(0.42, 0, 0.42)
	g.rotation_degrees.y = _rng.randf_range(-12.0, 12.0)
	add_child(g)
	var stone := _mat(Color(0.34, 0.35, 0.38), 0.0, 0.9)
	var base := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.62, 0.09, 0.44)
	base.mesh = bm
	base.material_override = stone
	base.position.y = 0.045
	g.add_child(base)
	if lv >= 5:
		var ob := MeshInstance3D.new()
		var om := BoxMesh.new()
		om.size = Vector3(0.26, 0.95, 0.26)
		ob.mesh = om
		ob.material_override = stone
		ob.position.y = 0.55
		g.add_child(ob)
		var tip := MeshInstance3D.new()
		var tm := PrismMesh.new()
		tm.size = Vector3(0.3, 0.22, 0.3)
		tip.mesh = tm
		tip.material_override = _mat(Color(0.55, 0.55, 0.62), 0.4, 0.5)
		tip.position.y = 1.13
		g.add_child(tip)
	elif lv >= 3:
		var slab := MeshInstance3D.new()
		var sm := BoxMesh.new()
		sm.size = Vector3(0.5, 0.7, 0.1)
		slab.mesh = sm
		slab.material_override = stone
		slab.position.y = 0.44
		g.add_child(slab)
	else:
		var v := MeshInstance3D.new()
		var vm := BoxMesh.new()
		vm.size = Vector3(0.12, 0.8, 0.08)
		v.mesh = vm
		v.material_override = stone
		v.position.y = 0.49
		g.add_child(v)
		var hbar := MeshInstance3D.new()
		var hm := BoxMesh.new()
		hm.size = Vector3(0.42, 0.11, 0.08)
		hbar.mesh = hm
		hbar.material_override = stone
		hbar.position.y = 0.66
		g.add_child(hbar)
	var tag := Label3D.new()
	tag.text = "%s ☠" % f.name
	tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	tag.font_size = 42
	tag.modulate = Color(0.85, 0.87, 0.9)
	tag.outline_modulate = Color(0, 0, 0, 0.8)
	tag.outline_size = 8
	tag.position = Vector3(0, 1.35, 0)
	g.add_child(tag)

func _taunt_selected() -> void:
	if _selected < 0 or _busy or _game_over:
		return
	var f = _fighters[_selected]
	if not f.alive or f.team != 0:
		return
	if f.ap < 1:
		_log("Насмешка: нужен 1 ОД")
		return
	f.ap -= 1
	var line: String = TAUNT_LINES[_rng.randi() % TAUNT_LINES.size()]
	_sfx_play("swap")
	_log("%s кричит: «%s»" % [f.name, line])
	var lbl := Label3D.new()
	lbl.text = "💬 " + line
	lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	lbl.font_size = 34
	lbl.modulate = Color(1.0, 0.9, 0.4)
	lbl.outline_size = 10
	lbl.outline_modulate = Color(0, 0, 0, 0.85)
	lbl.position = f.node.position + Vector3(0, 2.7, 0)
	add_child(lbl)
	var tw := create_tween()
	tw.tween_property(lbl, "position:y", lbl.position.y + 0.9, 1.1)
	tw.parallel().tween_property(lbl, "modulate:a", 0.0, 0.5).set_delay(0.7)
	tw.tween_callback(lbl.queue_free)
	# аггро: боты в радиусе 8 клеток 2 своих хода целятся в крикуна
	var n := 0
	for bf in _fighters:
		if bf.team != 1 or not bf.alive:
			continue
		var d := Vector2(bf.cell.x - f.cell.x, bf.cell.y - f.cell.y).length()
		if d <= 8.0:
			bf.aggro_to = _selected
			bf.aggro_ttl = 2
			n += 1
	if n > 0:
		_log("Насмешка разозлила ботов: %d целятся в %s (2 хода)" % [n, f.name])
	_refresh_card()

func _bot_pick_target(f: Dictionary, vis: int) -> int:
	# цель бота: разъярённый насмешкой бьёт крикуна, иначе — ближайшего видимого
	var ag := int(f.get("aggro_to", -1))
	if ag >= 0 and int(f.get("aggro_ttl", 0)) > 0 and ag < _fighters.size():
		var af = _fighters[ag]
		if af.alive:
			var d := Vector2(f.cell.x - af.cell.x, f.cell.y - af.cell.y).length()
			if d <= vis + 2 and _los(f.cell, af.cell):
				return ag
	return _nearest_visible_enemy(f.cell, vis, 0)

func _graffiti_selected() -> void:
	if _selected < 0 or _busy or _game_over:
		return
	var f = _fighters[_selected]
	if not f.alive or f.team != 0:
		return
	if f.ap < 1:
		_log("Граффити: нужен 1 ОД")
		return
	var ck := _key(f.cell)
	if _graffiti.has(ck):
		_log("Здесь уже есть граффити")
		return
	f.ap -= 1
	_graffiti[ck] = true
	_sfx_play("open")
	var col: Color = GRAFFITI_COLORS[_rng.randi() % GRAFFITI_COLORS.size()]
	var g := Node3D.new()
	g.position = gw(f.cell.x, f.cell.y, 0.032)
	add_child(g)
	for s in [[0.0, 0.0, 0.34], [0.22, 0.14, 0.13], [-0.2, 0.16, 0.11], [0.05, -0.22, 0.15], [-0.14, -0.12, 0.09]]:
		var sp := MeshInstance3D.new()
		var cy := CylinderMesh.new()
		cy.top_radius = s[2]
		cy.bottom_radius = s[2]
		cy.height = 0.012
		sp.mesh = cy
		sp.material_override = _mat(col, 0.0, 1.0, col, 1.2)
		sp.position = Vector3(s[0], 0, s[1])
		g.add_child(sp)
	_log("%s оставляет граффити 🎨" % f.name)
	_refresh_card()

func _teleport_in(node: Node3D, cell: Vector2i) -> void:
	# эффект появления бойца (~2 сек): «луч» с неба или «чёрная дыра»; стиль из настроек
	if not OS.get_cmdline_user_args().is_empty():
		return   # в тестовых прогонах эффекты не нужны (скриншоты)
	var style: String = str(_profile.get("teleport", "beam"))
	var wp := gw(cell.x, cell.y)
	node.scale = Vector3.ONE * 0.01
	if style == "hole":
		var disc := MeshInstance3D.new()
		var dm := CylinderMesh.new()
		dm.top_radius = 0.7
		dm.bottom_radius = 0.7
		dm.height = 0.05
		disc.mesh = dm
		disc.material_override = _mat(Color(0.02, 0.0, 0.05), 0.0, 1.0, Color(0.45, 0.1, 0.9), 2.5)
		disc.position = wp + Vector3(0, 0.05, 0)
		add_child(disc)
		var ring := MeshInstance3D.new()
		var rm := TorusMesh.new()
		rm.inner_radius = 0.55
		rm.outer_radius = 0.75
		ring.mesh = rm
		ring.material_override = _mat(Color(0.6, 0.2, 1.0), 0.0, 0.6, Color(0.7, 0.3, 1.0), 3.0)
		ring.position = wp + Vector3(0, 0.12, 0)
		add_child(ring)
		node.position = wp + Vector3(0, -1.0, 0)
		var tw := create_tween()
		tw.tween_property(ring, "rotation_degrees:y", 540.0, 1.6)
		tw.parallel().tween_property(node, "position:y", wp.y, 0.9).set_delay(0.4).set_trans(Tween.TRANS_BACK)
		tw.parallel().tween_property(node, "scale", Vector3.ONE * HUMAN_SCALE, 0.7).set_delay(0.45).set_trans(Tween.TRANS_BACK)
		tw.parallel().tween_property(disc, "scale", Vector3(0.05, 1.0, 0.05), 0.6).set_delay(1.4)
		tw.parallel().tween_property(ring, "scale", Vector3.ONE * 0.05, 0.6).set_delay(1.4)
		tw.tween_callback(disc.queue_free)
		tw.tween_callback(ring.queue_free)
		_sfx_play("zone")
	else:
		var beam := MeshInstance3D.new()
		var bmm := CylinderMesh.new()
		bmm.top_radius = 0.32
		bmm.bottom_radius = 0.55
		bmm.height = 9.0
		beam.mesh = bmm
		var bma := StandardMaterial3D.new()
		bma.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		bma.albedo_color = Color(0.45, 0.8, 1.0, 0.28)
		bma.emission_enabled = true
		bma.emission = Color(0.5, 0.85, 1.0)
		bma.emission_energy_multiplier = 1.6
		beam.material_override = bma
		beam.position = wp + Vector3(0, 4.5, 0)
		add_child(beam)
		var tw2 := create_tween()
		tw2.tween_property(node, "scale", Vector3.ONE * HUMAN_SCALE, 0.65).set_delay(0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw2.parallel().tween_property(bma, "albedo_color:a", 0.0, 0.7).set_delay(1.2)
		tw2.tween_callback(beam.queue_free)
		_spawn_burst(wp + Vector3(0, 0.4, 0), Color(0.5, 0.85, 1.0))
		_sfx_play("zone")

# ---------------- СВЕТ ----------------
func _setup_lighting() -> void:
""")

io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ALL_OK v6.32")
