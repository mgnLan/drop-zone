# v6.29 — мобильная адаптация боевого экрана (портрет телефона, ~324 лог. px)
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

# ---- хелперы _vw/_mob ----
rep("""func _apply_display_scale() -> void:
	# масштабом управляет движок (stretch: canvas_items, keep_height) — функция-заглушка
	pass
""", """func _apply_display_scale() -> void:
	# масштабом управляет движок (stretch: canvas_items, keep_height) — функция-заглушка
	pass

func _vw() -> float:
	# логическая ширина экрана (при keep_height телефон-портрет ~324)
	return get_viewport().get_visible_rect().size.x

func _mob() -> bool:
	# узкий экран — компактные раскладки
	return _vw() < 520.0
""")

# ---- флаг эмуляции портрета телефона для тестов ----
rep("""	var args := OS.get_cmdline_user_args()
	var seed_idx := args.find("--seed")
""", """	var args := OS.get_cmdline_user_args()
	if args.has("--win324"):
		DisplayServer.window_set_size(Vector2i(648, 1440))  # эмуляция портрета телефона
	var seed_idx := args.find("--seed")
""")

# ---- строка хода ----
rep("""	turn.add_theme_font_size_override("font_size", 20)
""", """	turn.add_theme_font_size_override("font_size", 14 if _mob() else 20)
""")
rep("""		_ui.turn.text = "Ход %d   |   Красные: %d   Синие: %d" % [_turn, _alive_count(0), _alive_count(1)]
""", """		if _mob():
			_ui.turn.text = "Ход %d · %d:%d" % [_turn, _alive_count(0), _alive_count(1)]
		else:
			_ui.turn.text = "Ход %d   |   Красные: %d   Синие: %d" % [_turn, _alive_count(0), _alive_count(1)]
""")

# ---- кнопки «Конец хода»/«Лобби» уже на узком экране ----
rep("""	btn.offset_left = -212.0
	btn.offset_right = -16.0
	btn.offset_top = 10.0
""", """	btn.offset_left = -150.0 if _mob() else -212.0
	btn.offset_right = -8.0 if _mob() else -16.0
	btn.offset_top = 10.0
""")
rep("""	btn.add_theme_font_size_override("font_size", 17)
""", """	btn.add_theme_font_size_override("font_size", 14 if _mob() else 17)
""")
rep("""	lobby.offset_left = -212.0
	lobby.offset_right = -16.0
""", """	lobby.offset_left = -150.0 if _mob() else -212.0
	lobby.offset_right = -8.0 if _mob() else -16.0
""")

# ---- карточка бойца и бары компактнее ----
rep("""	card.custom_minimum_size = Vector2(204, 168)
""", """	card.custom_minimum_size = Vector2(180, 158) if _mob() else Vector2(204, 168)
""")
rep("""	hp_bar.custom_minimum_size = Vector2(104, 12)
""", """	hp_bar.custom_minimum_size = Vector2(88, 12) if _mob() else Vector2(104, 12)
""")
rep("""	ap_bar.custom_minimum_size = Vector2(104, 12)
""", """	ap_bar.custom_minimum_size = Vector2(88, 12) if _mob() else Vector2(104, 12)
""")

# ---- ростер отряда ----
rep("""		row.custom_minimum_size = Vector2(190, 42)
""", """		row.custom_minimum_size = Vector2(160, 42) if _mob() else Vector2(190, 42)
""")

# ---- панель бойца справа ----
rep("""	fp.offset_left = -296.0
""", """	fp.offset_left = -min(296.0, _vw() * 0.68)
""")

# ---- панель ящика ----
rep("""	cp.offset_left = -240.0
	cp.offset_right = 240.0
""", """	var cw: float = min(240.0, _vw() * 0.46)
	cp.offset_left = -cw
	cp.offset_right = cw
""")

# ---- окно инвентаря ----
rep("""	iw.offset_left = -320.0
	iw.offset_right = 320.0
""", """	var iw2: float = min(320.0, _vw() * 0.47)
	iw.offset_left = -iw2
	iw.offset_right = iw2
""")

# ---- мобильная ветка инвентаря ----
rep("""	title.add_theme_font_size_override("font_size", 20)
	box.add_child(title)
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 24)
""", """	title.add_theme_font_size_override("font_size", 20)
	box.add_child(title)
	if _mob():
		_show_inventory_mobile(f, box)
		_ui.inv_panel.visible = true
		return
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 24)
""")

# ---- новая функция: компактный мобильный инвентарь ----
rep("""func _unequip(cat: String) -> void:
""", """func _show_inventory_mobile(f: Dictionary, box: VBoxContainer) -> void:
	# компактный инвентарь для узкого экрана: статы, слоты в ряд, сетка 2 колонки
	var stats := Label.new()
	stats.text = "HP %d/%d · ОД %d/%d · Защита %d · Вес %.1f/%.1f" % [
		f.hp, f.max_hp, f.ap, f.max_ap, _defense(f), _load_weight(f), _carry_limit(f)]
	stats.add_theme_font_size_override("font_size", 12)
	box.add_child(stats)
	var srow := HBoxContainer.new()
	srow.add_theme_constant_override("separation", 4)
	box.add_child(srow)
	var slots := [["Шлем", "helmets"], ["Корпус", "body"], ["Руки", "hands"], ["Штаны", "pants"]]
	for sd in slots:
		var b := Button.new()
		b.custom_minimum_size = Vector2(62, 60)
		b.add_theme_font_size_override("font_size", 10)
		b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		b.expand_icon = true
		b.add_theme_constant_override("icon_max_width", 24)
		var cat: String = sd[1]
		if cat == "hands":
			b.text = "Руки"
			var hic: Texture2D = _item_icon({"kind": "weapon", "item": f.weapon})
			if hic != null:
				b.icon = hic
			b.tooltip_text = _item_tooltip({"kind": "weapon", "item": f.weapon}) + "\\n—\\nКлик — нож/ствол"
			b.pressed.connect(func():
				_swap_weapon()
				if _selected >= 0:
					_show_inventory()
			)
		else:
			var it = f.armor[cat]
			b.text = sd[0]
			if it:
				var sit := _item_icon({"kind": "armor", "cat": cat, "item": it})
				if sit != null:
					b.icon = sit
				b.tooltip_text = _item_tooltip({"kind": "armor", "cat": cat, "item": it}) + "\\n—\\nКлик — снять"
			else:
				b.tooltip_text = "Пусто"
			b.pressed.connect(func():
				_unequip(cat)
			)
		srow.add_child(b)
	var bl := Label.new()
	bl.text = "Рюкзак (клик — надеть/использовать):"
	bl.add_theme_font_size_override("font_size", 12)
	box.add_child(bl)
	var sc := ScrollContainer.new()
	sc.custom_minimum_size = Vector2(0, 170)
	sc.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(sc)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 4)
	grid.add_theme_constant_override("v_separation", 4)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sc.add_child(grid)
	for idx in f.backpack.size():
		var b2 := Button.new()
		b2.text = f.backpack[idx]["item"].get("name", "?")
		var bic := _item_icon(f.backpack[idx])
		if bic != null:
			b2.icon = bic
			b2.expand_icon = true
			b2.add_theme_constant_override("icon_max_width", 26)
		b2.custom_minimum_size = Vector2(126, 50)
		b2.add_theme_font_size_override("font_size", 11)
		b2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b2.tooltip_text = _item_tooltip(f.backpack[idx])
		var kind: String = f.backpack[idx]["kind"]
		var kb := StyleBoxFlat.new()
		kb.bg_color = Color(0.05, 0.08, 0.12, 0.95)
		kb.set_corner_radius_all(6)
		kb.set_border_width_all(2)
		kb.border_color = {"weapon": Color(1.0, 0.35, 0.35, 0.8), "armor": Color(0.35, 0.7, 1.0, 0.8), "consumable": Color(0.4, 0.95, 0.5, 0.8)}.get(kind, Color(0.6, 0.6, 0.6, 0.8))
		b2.add_theme_stylebox_override("normal", kb)
		var i: int = idx
		b2.pressed.connect(func():
			_use_backpack(i)
			if _selected >= 0:
				_show_inventory()
		)
		grid.add_child(b2)
	if f.backpack.is_empty():
		var e := Label.new()
		e.text = "(пусто — ищите ящики)"
		grid.add_child(e)
	var close := Button.new()
	close.text = "Закрыть [I]"
	close.custom_minimum_size = Vector2(0, 44)
	close.pressed.connect(_toggle_inventory)
	box.add_child(close)

func _unequip(cat: String) -> void:
""")

# ---- окно уровня ----
rep("""	panel.custom_minimum_size = Vector2(560, 0)
""", """	panel.custom_minimum_size = Vector2(min(560.0, _vw() * 0.94), 0)
""")
rep("""		lb.custom_minimum_size = Vector2(150, 0)
""", """		lb.custom_minimum_size = Vector2(100, 0) if _mob() else Vector2(150, 0)
""")
rep("""		var hint := Label.new()
		hint.text = "  " + STAT_HINTS[k]
		hint.add_theme_font_size_override("font_size", 12)
""", """		var hint := Label.new()
		hint.text = "  " + STAT_HINTS[k]
		hint.add_theme_font_size_override("font_size", 10 if _mob() else 12)
""", 2)
rep("""		lb.custom_minimum_size = Vector2(160, 0)
""", """		lb.custom_minimum_size = Vector2(100, 0) if _mob() else Vector2(160, 0)
""")

# ---- экран конца боя ----
rep("""			panel.custom_minimum_size = Vector2(540, 0)
""", """			panel.custom_minimum_size = Vector2(min(540.0, _vw() * 0.94), 0)
""")
rep("""			l.add_theme_font_size_override("font_size", 32)
""", """			l.add_theme_font_size_override("font_size", 24 if _mob() else 32)
""")
rep("""				rw.add_theme_color_override("font_color", Color(1.0, 0.9, 0.45))
""", """				rw.add_theme_color_override("font_color", Color(1.0, 0.9, 0.45))
				rw.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				rw.custom_minimum_size = Vector2(min(500.0, _vw() * 0.9), 0)
""")

# ---- бар обучения ----
rep("""	hb.offset_left = -280.0
	hb.offset_right = 280.0
	hb.offset_top = 10.0
	hb.offset_bottom = 62.0
""", """	var ow: float = min(280.0, _vw() * 0.47)
	hb.offset_left = -ow
	hb.offset_right = ow
	hb.offset_top = 66.0 if _mob() else 10.0
	hb.offset_bottom = 118.0 if _mob() else 62.0
""")

if fails:
    print("\n".join(fails))
    print("FAIL")
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ALL_OK")
