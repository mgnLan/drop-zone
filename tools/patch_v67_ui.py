# Патч C: UI — анкеры, шрифт, чат, HP-бары, цена ОД, экран итогов
import io
p = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
s = io.open(p, encoding="utf-8").read()
orig = s

def rep(old, new, tag):
    global s
    n = s.count(old)
    if n != 1:
        print("FAIL", tag, "count=", n)
        raise SystemExit(1)
    s = s.replace(old, new)
    print("ok", tag)

# C1) шрифт Manrope как fallback всей темы + старт _build_ui
rep("""# ---------- интерфейс ----------
func _build_ui() -> void:
	var layer := CanvasLayer.new()""",
"""# ---------- интерфейс ----------
func _build_ui() -> void:
	# кириллический шрифт Manrope вместо системного
	if ResourceLoader.exists("res://assets/fonts/Manrope.ttf"):
		ThemeDB.fallback_font = load("res://assets/fonts/Manrope.ttf")
		ThemeDB.fallback_font_size = 16
	var layer := CanvasLayer.new()""", "font")

# C2) кнопки «Конец хода» и «Лобби» — якорь вправо вверху (не середина при широком окне)
rep("""	var btn := Button.new()
	btn.text = "Конец хода [Space]"
	btn.position = Vector2(1080, 10)
	btn.custom_minimum_size = Vector2(180, 40)
	btn.pressed.connect(_end_turn)
	layer.add_child(btn)
	var lobby := Button.new()
	lobby.text = "Лобби"
	lobby.position = Vector2(1080, 58)
	lobby.custom_minimum_size = Vector2(180, 32)""",
"""	var btn := Button.new()
	btn.text = "Конец хода [Space]"
	btn.anchor_left = 1.0
	btn.anchor_right = 1.0
	btn.offset_left = -196.0
	btn.offset_right = -16.0
	btn.offset_top = 10.0
	btn.offset_bottom = 50.0
	btn.pressed.connect(_end_turn)
	layer.add_child(btn)
	var lobby := Button.new()
	lobby.text = "Лобби"
	lobby.anchor_left = 1.0
	lobby.anchor_right = 1.0
	lobby.offset_left = -196.0
	lobby.offset_right = -16.0
	lobby.offset_top = 56.0
	lobby.offset_bottom = 88.0""", "anchors_tr")

# C3) лог — снизу справа, чтобы не пересекаться с чатом
rep("""	var log := Label.new()
	log.position = Vector2(470, 680)
	log.size = Vector2(560, 32)
	log.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER""",
"""	var log := Label.new()
	log.anchor_left = 1.0
	log.anchor_right = 1.0
	log.anchor_top = 1.0
	log.anchor_bottom = 1.0
	log.offset_left = -576.0
	log.offset_right = -16.0
	log.offset_top = -36.0
	log.offset_bottom = -8.0
	log.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT""", "log_anchor")

# C4) чат — якорь снизу слева + серо-зелёный фон
rep("""	var chat := PanelContainer.new()
	chat.position = Vector2(12, 452)
	chat.custom_minimum_size = Vector2(440, 258)
	layer.add_child(chat)""",
"""	var chat := PanelContainer.new()
	chat.anchor_top = 1.0
	chat.anchor_bottom = 1.0
	chat.offset_left = 12.0
	chat.offset_right = 452.0
	chat.offset_top = -272.0
	chat.offset_bottom = -12.0
	var chat_sb := StyleBoxFlat.new()
	chat_sb.bg_color = Color(0.14, 0.20, 0.15, 0.9)
	chat_sb.border_color = Color(0.38, 0.55, 0.40, 0.85)
	chat_sb.set_border_width_all(1)
	chat_sb.set_corner_radius_all(10)
	chat_sb.set_content_margin_all(8)
	chat.add_theme_stylebox_override("panel", chat_sb)
	layer.add_child(chat)""", "chat_style")

# C5) панель бойца — якорь вправо
rep("""	var fp := PanelContainer.new()
	fp.position = Vector2(1010, 56)
	fp.custom_minimum_size = Vector2(258, 250)""",
"""	var fp := PanelContainer.new()
	fp.anchor_left = 1.0
	fp.anchor_right = 1.0
	fp.offset_left = -272.0
	fp.offset_right = -12.0
	fp.offset_top = 96.0
	fp.offset_bottom = 356.0""", "fp_anchor")

# C6) панель ящика и инвентарь — по центру окна
rep("""	var cp := PanelContainer.new()
	cp.position = Vector2(460, 180)
	cp.custom_minimum_size = Vector2(380, 320)""",
"""	var cp := PanelContainer.new()
	cp.set_anchors_preset(Control.PRESET_CENTER)
	cp.offset_left = -200.0
	cp.offset_right = 200.0
	cp.offset_top = -170.0
	cp.offset_bottom = 170.0""", "chest_anchor")
rep("""	var iw := PanelContainer.new()
	iw.position = Vector2(340, 130)
	iw.custom_minimum_size = Vector2(600, 460)""",
"""	var iw := PanelContainer.new()
	iw.set_anchors_preset(Control.PRESET_CENTER)
	iw.offset_left = -320.0
	iw.offset_right = 320.0
	iw.offset_top = -250.0
	iw.offset_bottom = 250.0""", "inv_anchor")

# C7) HP-бары над бойцами: текстура и спрайты
rep("""# ---------------- БОЙЦЫ 4v4 ----------------""",
"""var _bar_texture: Texture2D = null
func _bar_tex() -> Texture2D:
	if _bar_texture == null:
		var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
		img.fill(Color.WHITE)
		_bar_texture = ImageTexture.create_from_image(img)
	return _bar_texture

# ---------------- БОЙЦЫ 4v4 ----------------""", "bar_tex")

rep("""	pad.position = gw(gx, gz, 0.02)
	add_child(pad)""",
"""	pad.position = gw(gx, gz, 0.02)
	add_child(pad)
	# HP-бар над головой (billboard-спрайты)
	var hp_bg := Sprite3D.new()
	hp_bg.texture = _bar_tex()
	hp_bg.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	hp_bg.centered = false
	hp_bg.modulate = Color(0.04, 0.05, 0.06, 0.85)
	hp_bg.scale = Vector3(1.2, 0.15, 1)
	hp_bg.position = Vector3(-0.6, 2.5, 0)
	p.add_child(hp_bg)
	var hp_fg := Sprite3D.new()
	hp_fg.texture = _bar_tex()
	hp_fg.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	hp_fg.centered = false
	hp_fg.modulate = Color(0.2, 0.95, 0.3)
	hp_fg.scale = Vector3(1.2, 0.15, 1)
	hp_fg.position = Vector3(-0.6, 2.5, 0.02)
	hp_fg.no_depth_test = true
	hp_bg.no_depth_test = true
	p.add_child(hp_fg)""", "hp_sprites")

rep("""		"backpack": [], "alive": true,
		"lvl": lvl, "xp": xp, "kills": 0, "pts": pts0
	})""",
"""		"backpack": [], "alive": true,
		"lvl": lvl, "xp": xp, "kills": 0, "pts": pts0, "dmg": 0,
		"hp_fg": hp_fg, "hp_bg": hp_bg
	})""", "fighter_dict")

# обновление HP-баров каждый кадр
rep("""	elif _cam.h_offset != 0.0 or _cam.v_offset != 0.0:
		_cam.h_offset = 0.0
		_cam.v_offset = 0.0
	_update_aim()""",
"""	elif _cam.h_offset != 0.0 or _cam.v_offset != 0.0:
		_cam.h_offset = 0.0
		_cam.v_offset = 0.0
	# HP-бары над бойцами
	for f9 in _fighters:
		var fg9 = f9.get("hp_fg")
		if fg9:
			var r9: float = float(f9.hp) / maxf(1.0, float(f9.max_hp))
			fg9.scale.x = 1.2 * r9
			fg9.modulate = Color(1.0 - r9 * 0.85, 0.12 + r9 * 0.83, 0.18)
			fg9.visible = f9.alive and f9.node.visible
			f9.hp_bg.visible = f9.alive and f9.node.visible
	_update_aim()""", "hp_update")

# C8) цена хода (ОД) на подсвеченных клетках
rep("""		q.material_override = mat
		q.position = gw(cell.x, cell.y, 0.05)
		add_child(q)
		_hl.append(q)""",
"""		q.material_override = mat
		q.position = gw(cell.x, cell.y, 0.05)
		add_child(q)
		_hl.append(q)
		var cost_lbl := Label3D.new()
		cost_lbl.text = str(int(_reach[cell]))
		cost_lbl.font_size = 44
		cost_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		cost_lbl.no_depth_test = true
		cost_lbl.modulate = Color(0.75, 0.95, 1.0, 0.8)
		cost_lbl.outline_size = 10
		cost_lbl.outline_modulate = Color(0, 0, 0, 0.85)
		cost_lbl.position = gw(cell.x, cell.y, 0.4)
		add_child(cost_lbl)
		_hl.append(cost_lbl)""", "ap_cost")

# C9) учёт нанесённого урона
rep("""	d.hp = maxi(0, d.hp - real)
	_sfx_play("hit")""",
"""	d.hp = maxi(0, d.hp - real)
	if src_idx >= 0 and src_idx < _fighters.size():
		_fighters[src_idx].dmg = int(_fighters[src_idx].get("dmg", 0)) + real
	_sfx_play("hit")""", "dmg_track")

# C10) экран итогов со статистикой и кнопкой «Реванш»
old_end = """		if _ui.has("layer"):
			var l := Label.new()
			l.text = msg
			l.add_theme_font_size_override("font_size", 42)
			l.position = Vector2(340, 280)
			l.size = Vector2(600, 80)
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			_ui.layer.add_child(l)
			var lb := Button.new()
			lb.text = "В лобби"
			lb.position = Vector2(540, 380)
			lb.custom_minimum_size = Vector2(200, 52)
			_style_menu_button(lb)
			lb.pressed.connect(_go_lobby)
			_ui.layer.add_child(lb)"""
new_end = """		if _ui.has("layer"):
			var wrap := CenterContainer.new()
			wrap.set_anchors_preset(Control.PRESET_FULL_RECT)
			_ui.layer.add_child(wrap)
			var panel := PanelContainer.new()
			panel.custom_minimum_size = Vector2(540, 0)
			panel.add_theme_stylebox_override("panel", _frame_box())
			wrap.add_child(panel)
			var vb := VBoxContainer.new()
			panel.add_child(vb)
			var l := Label.new()
			l.text = msg
			l.add_theme_font_size_override("font_size", 32)
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			vb.add_child(l)
			var sub := Label.new()
			sub.text = "Раундов: %d · Зона: фаза %d" % [_turn, _zone_phase]
			sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			sub.add_theme_font_size_override("font_size", 14)
			vb.add_child(sub)
			var sep := HSeparator.new()
			vb.add_child(sep)
			for f2 in _fighters:
				var row2 := HBoxContainer.new()
				vb.add_child(row2)
				var chip := ColorRect.new()
				chip.custom_minimum_size = Vector2(14, 14)
				chip.color = Color("#ff4757") if f2.team == 0 else Color("#3498ff")
				row2.add_child(chip)
				var nl2 := Label.new()
				nl2.text = " " + f2.name
				nl2.custom_minimum_size = Vector2(140, 0)
				row2.add_child(nl2)
				var st2 := Label.new()
				st2.text = "Ур.%d · Убийств %d · Урон %d" % [int(f2.lvl), int(f2.kills), int(f2.get("dmg", 0))]
				st2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
				row2.add_child(st2)
				var al := Label.new()
				al.text = "Жив" if f2.alive else "Выбыл"
				al.modulate = Color(0.5, 1.0, 0.5) if f2.alive else Color(1.0, 0.5, 0.5)
				row2.add_child(al)
			var btns := HBoxContainer.new()
			btns.alignment = BoxContainer.ALIGNMENT_CENTER
			btns.add_theme_constant_override("separation", 16)
			vb.add_child(btns)
			var lb := Button.new()
			lb.text = "В лобби"
			lb.custom_minimum_size = Vector2(180, 48)
			_style_menu_button(lb)
			lb.pressed.connect(_go_lobby)
			btns.add_child(lb)
			var rv := Button.new()
			rv.text = "Реванш"
			rv.custom_minimum_size = Vector2(180, 48)
			_style_menu_button(rv)
			rv.pressed.connect(_rematch)
			btns.add_child(rv)"""
rep(old_end, new_end, "end_screen")

rep("""func _go_lobby() -> void:""",
"""func _rematch() -> void:
	# реванш: тот же режим, автостарт
	var cfg := ConfigFile.new()
	cfg.set_value("game", "autostart", 1)
	cfg.save("user://autostart.cfg")
	get_tree().reload_current_scene()

func _go_lobby() -> void:""", "rematch_fn")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
