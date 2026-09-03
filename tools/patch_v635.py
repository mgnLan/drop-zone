# -*- coding: utf-8 -*-
# v6.35: экран входа — единая ось лого+форма, ScrollContainer, фикс-статус,
# подсказка про гостя + пульс кнопки при сетевой ошибке, диагностика result/code
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    c = src.count(old)
    if c != 1:
        print("FAIL: маркер найден %d раз (нужно 1):" % c)
        print(old[:140])
        sys.exit(1)
    src = src.replace(old, new)

def rep_range(start_marker, end_marker, new_block):
    # заменяет текст от start_marker до end_marker (end не входит)
    global src
    i = src.find(start_marker)
    j = src.find(end_marker)
    if i < 0 or j < 0 or j <= i:
        print("FAIL: диапазон не найден:", start_marker[:60], "->", end_marker[:60])
        sys.exit(1)
    src = src[:i] + new_block + src[j:]

# ---- 1. Новые переменные ----
rep("""var _auth_status: Label = null
""", """var _auth_status: Label = null
var _auth_hint: Label = null      # подсказка про гостевой режим при сетевой ошибке
var _auth_guest: Button = null    # кнопка гостя (пульс при сетевой ошибке)
var _dbg_vp := Vector2i.ZERO      # переопределение вьюпорта для тест-скринов
""")

# ---- 2. Полная замена _build_auth ----
rep_range("func _build_auth(auto: bool) -> void:",
	"\n# ---------------- ПРОФИЛЬ ИГРОКА (user://profile.cfg) ----------------",
	"""func _build_auth(auto: bool) -> void:
	_menu_open = true
	_busy = true
	var layer := CanvasLayer.new()
	layer.layer = 20
	add_child(layer)
	_auth_layer = layer
	var bg := TextureRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	if ResourceLoader.exists("res://assets/ui/menu_bg.jpg"):
		bg.texture = load("res://assets/ui/menu_bg.jpg")
	layer.add_child(bg)
	var dim := ColorRect.new()
	dim.color = Color(0.02, 0.03, 0.06, 0.72)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(dim)
	# единая вертикальная ось: лого по центру НАД формой, без ручных смещений
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(center)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_child(col)
	var vw2: float = float(_dbg_vp.x) if _dbg_vp.x > 0 else get_viewport().get_visible_rect().size.x
	var vh2: float = float(_dbg_vp.y) if _dbg_vp.y > 0 else get_viewport().get_visible_rect().size.y
	var logo_w := minf(560.0, vw2 * 0.86)
	var logo := TextureRect.new()
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.custom_minimum_size = Vector2(logo_w, 120)
	if ResourceLoader.exists("res://assets/ui/logo.png"):
		var ltex: Texture2D = load("res://assets/ui/logo.png")
		logo.texture = ltex
		var ar := float(ltex.get_height()) / maxf(1.0, float(ltex.get_width()))
		logo.custom_minimum_size = Vector2(logo_w, logo_w * ar)
	col.add_child(logo)
	# скролл на ВСЕХ разрешениях: макс. высота = вьюпорт - лого - отступы
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(minf(460.0, vw2 * 0.92),
		minf(500.0, vh2 - logo.custom_minimum_size.y - 60.0))
	col.add_child(scroll)
	var panel := PanelContainer.new()
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.add_theme_stylebox_override("panel", _frame_box())
	scroll.add_child(panel)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 12)
	panel.add_child(vb)
	var t := Label.new()
	t.text = "Вход в аккаунт"
	t.add_theme_font_size_override("font_size", 22)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(t)
	if auto:
		var w := Label.new()
		w.text = "Проверка аккаунта…"
		w.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vb.add_child(w)
		return
	var em := LineEdit.new()
	em.placeholder_text = "✉ Почта"
	em.text = _auth_email
	em.custom_minimum_size = Vector2(0, 52)
	vb.add_child(em)
	var pw := LineEdit.new()
	pw.placeholder_text = "🔒 Пароль (минимум 6 символов)"
	pw.secret = true
	pw.custom_minimum_size = Vector2(0, 52)
	vb.add_child(pw)
	# статус и подсказка — фиксированная высота, кнопки не прыгают
	var st := Label.new()
	st.text = ""
	st.custom_minimum_size = Vector2(0, 24)
	st.add_theme_color_override("font_color", Color(1.0, 0.45, 0.45))
	st.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	st.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(st)
	_auth_status = st
	var hint := Label.new()
	hint.text = ""
	hint.custom_minimum_size = Vector2(0, 34)
	hint.add_theme_font_size_override("font_size", 12)
	hint.add_theme_color_override("font_color", Color(0.6, 0.9, 1.0))
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(hint)
	_auth_hint = hint
	var li := _menu_button("ВОЙТИ")
	li.custom_minimum_size = Vector2(0, 52)
	var lis := StyleBoxFlat.new()
	lis.bg_color = Color(0.72, 0.16, 0.20, 0.95)
	lis.border_color = Color(1.0, 0.45, 0.25, 0.9)
	lis.set_border_width_all(2)
	lis.set_corner_radius_all(8)
	li.add_theme_stylebox_override("normal", lis)
	li.pressed.connect(func():
		_auth_email = em.text.strip_edges()
		if _auth_email.find("@") < 0 or pw.text == "":
			st.text = "Введи почту и пароль"
			return
		st.text = "Вход…"
		_auth_cfg_save()
		_api_call("login", {"email": _auth_email, "password": pw.text})
	)
	vb.add_child(li)
	var rg := _menu_button("РЕГИСТРАЦИЯ")
	rg.custom_minimum_size = Vector2(0, 52)
	rg.pressed.connect(func():
		_auth_email = em.text.strip_edges()
		if _auth_email.find("@") < 0:
			st.text = "Введи корректную почту"
			return
		if pw.text.length() < 6:
			st.text = "Пароль — минимум 6 символов"
			return
		st.text = "Регистрация…"
		_auth_cfg_save()
		_api_call("register", {"email": _auth_email, "password": pw.text})
	)
	vb.add_child(rg)
	var gs := _menu_button("👤 Играть как гость")
	gs.custom_minimum_size = Vector2(0, 48)
	gs.pressed.connect(func():
		_auth_close()
		_build_menu()
	)
	vb.add_child(gs)
	_auth_guest = gs
	var note := Label.new()
	note.text = "Аккаунт синхронизирует прогресс между браузером, ВК и MAX.\nВход через ВК и MAX — скоро."
	note.add_theme_font_size_override("font_size", 12)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(note)
""")

# ---- 3. Диагностика в _on_api_done: отделяем «нет сети» от кода и битого ответа ----
rep("""func _on_api_done(_result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var act := _auth_pending
	_auth_pending = ""
	if code != 200:
		_auth_fail("Сервер недоступен (код %d)" % code, act)
		return
	var js := JSON.new()
	if js.parse(body.get_string_from_utf8()) != OK or not (js.data is Dictionary):
		_auth_fail("Сервер недоступен", act)
		return
""", """func _on_api_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var act := _auth_pending
	_auth_pending = ""
	if result != HTTPRequest.RESULT_SUCCESS:
		_auth_fail("Нет соединения с сервером — проверь интернет", act, true)
		return
	if code != 200:
		_auth_fail("Сервер недоступен (код %d)" % code, act, true)
		return
	var js := JSON.new()
	if js.parse(body.get_string_from_utf8()) != OK or not (js.data is Dictionary):
		_auth_fail("Сервер ответил что-то непонятное", act, true)
		return
""")

# ---- 4. _auth_fail: подсказка + пульс гостя при сетевой ошибке ----
rep("""func _auth_fail(msg: String, act: String) -> void:
	if act == "load":
		# автологин не удался — офлайн-режим с локальным профилем
		_auth_close()
		_build_menu()
		return
	if _auth_status != null and is_instance_valid(_auth_status):
		_auth_status.text = msg
""", """func _auth_fail(msg: String, act: String, net := false) -> void:
	if act == "load":
		# автологин не удался — офлайн-режим с локальным профилем
		_auth_close()
		_build_menu()
		return
	if _auth_status != null and is_instance_valid(_auth_status):
		_auth_status.text = msg
	if net:
		if _auth_hint != null and is_instance_valid(_auth_hint):
			_auth_hint.text = "Нет соединения? Нажми «Играть как гость» — прогресс сохранится на этом устройстве"
		if _auth_guest != null and is_instance_valid(_auth_guest):
			var twp := _auth_guest.create_tween().set_loops()
			twp.tween_property(_auth_guest, "modulate", Color(1.5, 1.35, 0.5), 0.5)
			twp.tween_property(_auth_guest, "modulate", Color(1, 1, 1), 0.5)
""")

# ---- 5. Тест-скрины входа: wide 1280x800 и mobile 360x800 ----
rep("""	elif args.has("--testauth"):
		_load_sfx()
		_build_ui()
		_build_auth(false)
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_auth.png")
		print("TESTAUTH_SAVED")
		get_tree().quit()
""", """	elif args.has("--testauth"):
		_run_testauth("test_auth.png")
	elif args.has("--testauthwide"):
		_dbg_vp = Vector2i(1280, 800)
		_run_testauth("test_auth_wide.png")
	elif args.has("--testauthmobile"):
		_dbg_vp = Vector2i(360, 800)
		_run_testauth("test_auth_mobile.png")
""")

# ---- 6. Хелпер теста ----
rep("""# ============================================================
# ---------------- ЗВУК ----------------
# ============================================================
""", """func _run_testauth(fname: String) -> void:
	_load_sfx()
	_build_ui()
	_build_auth(false)
	for i in 4:
		await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/" + fname)
	print("TESTAUTH_SAVED " + fname)
	get_tree().quit()

# ============================================================
# ---------------- ЗВУК ----------------
# ============================================================
""")

io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ALL_OK v6.35")
