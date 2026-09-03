# v6.26 — редизайн лобби: верхняя панель с чипами, 3 колонки, скролл, сворачиваемый чат с конвертами
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new, count=1):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, count)

# 1) переменная свёрнутого чата
rep("""var _menu_chat_tab := 0""",
"""var _menu_chat_tab := 0
var _menu_chat_collapsed := false""")

# 2) новая раскладка _build_menu: верхняя панель + скролл + сворачиваемый чат
rep("""	# логотип игры
	var vw2: float = get_viewport().get_visible_rect().size.x
	var menu_x: float = maxf(600.0, (vw2 - 400.0) / 2.0)
	var logo := TextureRect.new()
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.position = Vector2(menu_x + 200.0 - 300.0, 26)
	logo.custom_minimum_size = Vector2(600, 150)
	logo.size = Vector2(600, 150)
	if ResourceLoader.exists("res://assets/ui/logo.png"):
		logo.texture = load("res://assets/ui/logo.png")
	layer.add_child(logo)
	_ui.menu_logo = logo
	var vb := VBoxContainer.new()
	vb.position = Vector2(menu_x, 190)
	vb.custom_minimum_size = Vector2(400, 440)
	vb.add_theme_constant_override("separation", 12)
	layer.add_child(vb)
	_ui.menu_box = vb
	vb.resized.connect(_layout_menu)
	get_viewport().size_changed.connect(_layout_menu)
	_layout_menu()
	# --- чаты лобби: вкладки Общий / Комната / Клан (заглушка до онлайна) ---
	var chat := PanelContainer.new()
	chat.add_theme_stylebox_override("panel", _frame_box())
	chat.position = Vector2(16, 556)
	chat.custom_minimum_size = Vector2(560, 152)
	layer.add_child(chat)
	var cvb := VBoxContainer.new()
	chat.add_child(cvb)
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 4)
	cvb.add_child(tabs)
	_ui.menu_chat_btns = []
	var tab_names := ["Общий чат", "Чат комнаты", "Чат с кланом"]
	for ti in 3:
		var tb := Button.new()
		tb.text = tab_names[ti]
		tb.custom_minimum_size = Vector2(0, 24)
		tb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var tn: int = ti
		tb.pressed.connect(func():
			_menu_chat_tab = tn
			_render_menu_chat()
		)
		tabs.add_child(tb)
		_ui.menu_chat_btns.append(tb)
	var lines := VBoxContainer.new()
	cvb.add_child(lines)
	_ui.menu_chat_lines = lines
	var inp := LineEdit.new()
	inp.placeholder_text = "Чат появится в онлайн-режиме…"
	inp.editable = false
	cvb.add_child(inp)
	_render_menu_chat()
	_show_menu_main()""",
"""	# --- верхняя панель: лого слева, чипы игрока справа ---
	var top := HBoxContainer.new()
	top.set_anchors_preset(Control.PRESET_TOP_WIDE)
	top.offset_left = 16.0
	top.offset_right = -16.0
	top.offset_top = 10.0
	top.offset_bottom = 88.0
	layer.add_child(top)
	var logo := TextureRect.new()
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.custom_minimum_size = Vector2(280, 72)
	if ResourceLoader.exists("res://assets/ui/logo.png"):
		logo.texture = load("res://assets/ui/logo.png")
	top.add_child(logo)
	_ui.menu_logo = logo
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(sp)
	var chips := HBoxContainer.new()
	chips.add_theme_constant_override("separation", 8)
	chips.alignment = BoxContainer.ALIGNMENT_END
	top.add_child(chips)
	_ui.menu_chips = chips
	# --- центральная зона: скролл, чтобы меню влезало на любых экранах ---
	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.offset_left = 24.0
	scroll.offset_right = -24.0
	scroll.offset_top = 100.0
	scroll.offset_bottom = -196.0
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	layer.add_child(scroll)
	var cc := CenterContainer.new()
	cc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(cc)
	var vb := VBoxContainer.new()
	vb.custom_minimum_size = Vector2(460, 0)
	vb.add_theme_constant_override("separation", 12)
	cc.add_child(vb)
	_ui.menu_box = vb
	# --- чат лобби: сворачиваемый; в свёрнутом виде — 3 конверта ---
	var chat := PanelContainer.new()
	chat.add_theme_stylebox_override("panel", _frame_box())
	chat.anchor_top = 1.0
	chat.anchor_bottom = 1.0
	chat.offset_left = 16.0
	chat.offset_right = 316.0
	chat.offset_top = -180.0
	chat.offset_bottom = -16.0
	layer.add_child(chat)
	_ui.menu_chat_panel = chat
	var chat_v := VBoxContainer.new()
	chat.add_child(chat_v)
	var head := HBoxContainer.new()
	chat_v.add_child(head)
	var htl := Label.new()
	htl.text = "Чаты"
	htl.add_theme_font_size_override("font_size", 13)
	htl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(htl)
	var collapse := Button.new()
	collapse.text = "—"
	collapse.custom_minimum_size = Vector2(44, 26)
	collapse.tooltip_text = "Свернуть чат"
	collapse.pressed.connect(_toggle_menu_chat)
	head.add_child(collapse)
	_ui.menu_chat_collapse = collapse
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", 4)
	chat_v.add_child(content)
	_ui.menu_chat_content = content
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 4)
	content.add_child(tabs)
	_ui.menu_chat_btns = []
	var tab_names := ["Общий", "Комната", "Клан"]
	for ti in 3:
		var tb := Button.new()
		tb.text = tab_names[ti]
		tb.custom_minimum_size = Vector2(0, 26)
		tb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var tn: int = ti
		tb.pressed.connect(func():
			_menu_chat_tab = tn
			_render_menu_chat()
		)
		tabs.add_child(tb)
		_ui.menu_chat_btns.append(tb)
	var lines := VBoxContainer.new()
	content.add_child(lines)
	_ui.menu_chat_lines = lines
	var inp := LineEdit.new()
	inp.placeholder_text = "Чат появится в онлайн-режиме…"
	inp.editable = false
	content.add_child(inp)
	var env := HBoxContainer.new()
	env.add_theme_constant_override("separation", 8)
	env.visible = false
	chat_v.add_child(env)
	_ui.menu_chat_env = env
	var env_icons := ["🌐", "⚔️", "🛡️"]
	var env_tips := ["Общий чат", "Чат комнаты", "Чат с кланом"]
	for ei in 3:
		var eb := Button.new()
		eb.text = env_icons[ei]
		eb.custom_minimum_size = Vector2(64, 44)
		eb.tooltip_text = env_tips[ei]
		var en: int = ei
		eb.pressed.connect(func():
			_menu_chat_tab = en
			_toggle_menu_chat()
		)
		env.add_child(eb)
	_render_menu_chat()
	_show_menu_main()

func _toggle_menu_chat() -> void:
	# свернуть/развернуть чат лобби; в свёрнутом виде — конверты вкладок
	if not _ui.has("menu_chat_panel"):
		return
	_menu_chat_collapsed = not _menu_chat_collapsed
	var p: PanelContainer = _ui.menu_chat_panel
	_ui.menu_chat_content.visible = not _menu_chat_collapsed
	_ui.menu_chat_env.visible = _menu_chat_collapsed
	p.offset_top = -72.0 if _menu_chat_collapsed else -180.0
	_ui.menu_chat_collapse.text = "+" if _menu_chat_collapsed else "—"
	_render_menu_chat()""")

# 3) новый главный экран: 3 колонки на широких, 1 на узких, чипы сверху
rep("""func _show_menu_main() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	vb.add_child(_framed_label("ROYAL BATTLE — королевская битва на арене телешоу будущего", 15))
	vb.add_child(_framed_label("🪙 Монеты: %d · Побед: %d · Убийств: %d" % [
		int(_profile.get("coins", 0)), int(_profile.get("wins", 0)), int(_profile.get("total_kills", 0))], 16))
	vb.add_child(_daily_box())
	vb.add_child(_framed_label("👤 " + (_auth_email if _auth_email != "" else "Гость — прогресс только на этом устройстве"), 13))
	var m1 := _menu_button("Тренировка 1×1 — дуэль (малая арена)")
	m1.pressed.connect(func(): _start_mode(1))
	vb.add_child(m1)
	var m2 := _menu_button("Тренировка 2×2 — пара (средняя арена)")
	if _profile.unlocked_slots >= 2:
		m2.pressed.connect(func(): _start_mode(2))
	else:
		m2.text = "🔒 2×2 — слот №2 после %d побед" % int(SLOT_WINS[2])
		m2.disabled = true
	vb.add_child(m2)
	var m4 := _menu_button("Тренировка 4×4 — отряд (большая арена)")
	if _profile.unlocked_slots >= 4:
		m4.pressed.connect(func(): _start_mode(4))
	else:
		m4.text = "🔒 4×4 — слот №4 после %d побед" % int(SLOT_WINS[4])
		m4.disabled = true
	vb.add_child(m4)
	var squad := _menu_button("Отряд: создание бойца, навыки, слоты")
	squad.pressed.connect(_show_menu_squad)
	vb.add_child(squad)
	var shop := _menu_button("🛒 Магазин: рамки и цвета ника (за монеты)")
	shop.pressed.connect(_show_menu_shop)
	vb.add_child(shop)
	var prof := _menu_button("Личные настройки: аватар, город")
	prof.pressed.connect(_show_menu_profile)
	vb.add_child(prof)
	var sett := _menu_button("Настройки: звук, графика")
	sett.pressed.connect(_show_menu_settings)
	vb.add_child(sett)""",
"""func _show_menu_main() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	# чипы игрока в верхней панели
	if _ui.has("menu_chips"):
		var ch: HBoxContainer = _ui.menu_chips
		for cc in ch.get_children():
			cc.queue_free()
		ch.add_child(_framed_label("👤 " + (_auth_email if _auth_email != "" else "Гость"), 13))
		ch.add_child(_framed_label("🪙 %d" % int(_profile.get("coins", 0)), 13))
		ch.add_child(_framed_label("🏆 %d" % int(_profile.get("wins", 0)), 13))
		ch.add_child(_framed_label("💀 %d" % int(_profile.get("total_kills", 0)), 13))
	# кнопки режимов и разделов
	var m1 := _menu_button("🎯 Тренировка 1×1 — дуэль")
	m1.pressed.connect(func(): _start_mode(1))
	var m2 := _menu_button("Тренировка 2×2 — пара")
	if _profile.unlocked_slots >= 2:
		m2.pressed.connect(func(): _start_mode(2))
	else:
		m2.text = "🔒 2×2 — слот №2 после %d побед" % int(SLOT_WINS[2])
		m2.disabled = true
	var m4 := _menu_button("Тренировка 4×4 — отряд")
	if _profile.unlocked_slots >= 4:
		m4.pressed.connect(func(): _start_mode(4))
	else:
		m4.text = "🔒 4×4 — слот №4 после %d побед" % int(SLOT_WINS[4])
		m4.disabled = true
	var squad := _menu_button("👥 Отряд: бойцы, навыки, слоты")
	squad.pressed.connect(_show_menu_squad)
	var shop := _menu_button("🛒 Магазин: рамки и цвет ника")
	shop.pressed.connect(_show_menu_shop)
	var prof := _menu_button("🎨 Личные настройки: аватар, город")
	prof.pressed.connect(_show_menu_profile)
	var sett := _menu_button("⚙️ Настройки: звук, графика")
	sett.pressed.connect(_show_menu_settings)
	# раскладка: 3 колонки на широких экранах, 1 колонка на узких
	var vw4: float = get_viewport().get_visible_rect().size.x
	if vw4 >= 980.0:
		vb.custom_minimum_size = Vector2(minf(1100.0, vw4 * 0.92), 0)
		var cols := HBoxContainer.new()
		cols.add_theme_constant_override("separation", 16)
		cols.alignment = BoxContainer.ALIGNMENT_CENTER
		vb.add_child(cols)
		var c1 := VBoxContainer.new()
		c1.custom_minimum_size = Vector2(320, 0)
		c1.add_theme_constant_override("separation", 10)
		cols.add_child(c1)
		c1.add_child(_framed_label("⚔️ БОЙ", 16))
		c1.add_child(m1)
		c1.add_child(m2)
		c1.add_child(m4)
		var c2 := VBoxContainer.new()
		c2.custom_minimum_size = Vector2(320, 0)
		c2.add_theme_constant_override("separation", 10)
		cols.add_child(c2)
		c2.add_child(_framed_label("🗂️ УПРАВЛЕНИЕ", 16))
		c2.add_child(squad)
		c2.add_child(shop)
		c2.add_child(prof)
		c2.add_child(sett)
		var c3 := VBoxContainer.new()
		c3.custom_minimum_size = Vector2(320, 0)
		c3.add_theme_constant_override("separation", 10)
		cols.add_child(c3)
		c3.add_child(_framed_label("📋 ЗАДАНИЯ", 16))
		c3.add_child(_daily_box())
	else:
		vb.custom_minimum_size = Vector2(minf(460.0, vw4 * 0.92), 0)
		vb.add_child(_framed_label("⚔️ БОЙ", 15))
		vb.add_child(m1)
		vb.add_child(m2)
		vb.add_child(m4)
		vb.add_child(_framed_label("🗂️ УПРАВЛЕНИЕ", 15))
		vb.add_child(squad)
		vb.add_child(shop)
		vb.add_child(prof)
		vb.add_child(sett)
		vb.add_child(_daily_box())""")

# 4) подэкраны: сброс ширины колонки (все 4 функции)
rep("""	for c in vb.get_children():
		c.queue_free()
	var t := Label.new()""",
"""	for c in vb.get_children():
		c.queue_free()
	vb.custom_minimum_size = Vector2(minf(460.0, get_viewport().get_visible_rect().size.x * 0.92), 0)
	var t := Label.new()""", 4)

# 5) заставка загрузки на весь экран
EP = r"G:\Kimi project\Drop Zone\game\export_presets.cfg"
ep = io.open(EP, encoding="utf-8").read()
old_css = "#status-splash{filter:drop-shadow(0 0 18px rgba(255,60,110,.45))}"
new_css = "#status-splash{position:fixed;inset:0;width:100vw;height:100vh;max-width:none;max-height:none;object-fit:cover;filter:drop-shadow(0 0 18px rgba(255,60,110,.45))}"
if old_css in ep:
    ep = ep.replace(old_css, new_css, 1)
    io.open(EP, "w", encoding="utf-8", newline="").write(ep)
    print("PRESET_OK заставка на весь экран")
else:
    print("PRESET_FAIL маркер splash не найден")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.26")
