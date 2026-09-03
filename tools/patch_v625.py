# v6.25 — аккаунты: регистрация/вход по почте, синхронизация профиля с сервером
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) блок аккаунта: константы, переменные, функции API и экран входа
rep("""# ---------------- ПРОФИЛЬ ИГРОКА (user://profile.cfg) ----------------""",
"""# ---------------- АККАУНТ: почта сейчас, ВК/MAX позже ----------------
const API_URL := "https://podvezu.online/dropzone/api/index.php"
var _auth_token := ""
var _auth_email := ""
var _auth_pending := ""        # какой запрос сейчас в полёте
var _http: HTTPRequest = null
var _auth_layer: CanvasLayer = null
var _auth_status: Label = null
var _sync_push := true         # false — когда применяем профиль с сервера (без ответной отправки)

func _auth_cfg_load() -> void:
	var cfg := ConfigFile.new()
	if cfg.load("user://auth.cfg") == OK:
		_auth_token = str(cfg.get_value("auth", "token", ""))
		_auth_email = str(cfg.get_value("auth", "email", ""))

func _auth_cfg_save() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("auth", "token", _auth_token)
	cfg.set_value("auth", "email", _auth_email)
	cfg.save("user://auth.cfg")

func _api_call(action: String, data: Dictionary) -> void:
	if _http == null:
		return
	_auth_pending = action
	var body := data.duplicate()
	body["action"] = action
	_http.request(API_URL, ["Content-Type: application/json"], HTTPClient.METHOD_POST, JSON.stringify(body))

func _on_api_done(_result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	var act := _auth_pending
	_auth_pending = ""
	if code != 200:
		_auth_fail("Сервер недоступен (код %d)" % code, act)
		return
	var js := JSON.new()
	if js.parse(body.get_string_from_utf8()) != OK or not (js.data is Dictionary):
		_auth_fail("Сервер недоступен", act)
		return
	var d: Dictionary = js.data
	if not bool(d.get("ok", false)):
		_auth_fail(str(d.get("error", "Ошибка")), act)
		return
	match act:
		"register", "login":
			_auth_token = str(d.get("token", ""))
			_auth_cfg_save()
			_profile_from_server(d.get("profile", {}))
			_auth_close()
			_build_menu()
		"load":
			_profile_from_server(d.get("profile", {}))
			_auth_close()
			_build_menu()
		_:
			pass

func _profile_from_server(sp) -> void:
	# сервер — источник правды: применяем его профиль поверх локального
	if not (sp is Dictionary) or (sp as Dictionary).is_empty():
		return
	for k in (sp as Dictionary).keys():
		_profile[k] = sp[k]
	_sync_push = false
	_save_profile()
	_sync_push = true

func _auth_fail(msg: String, act: String) -> void:
	if act == "load":
		# автологин не удался — офлайн-режим с локальным профилем
		_auth_close()
		_build_menu()
		return
	if _auth_status != null and is_instance_valid(_auth_status):
		_auth_status.text = msg

func _auth_close() -> void:
	if _auth_layer != null and is_instance_valid(_auth_layer):
		_auth_layer.queue_free()
	_auth_layer = null
	_auth_status = null

func _build_auth(auto: bool) -> void:
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
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.custom_minimum_size = Vector2(430, 0)
	panel.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(panel)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 10)
	panel.add_child(vb)
	var t := Label.new()
	t.text = "DROP ZONE — вход в аккаунт"
	t.add_theme_font_size_override("font_size", 24)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(t)
	if auto:
		var w := Label.new()
		w.text = "Проверка аккаунта…"
		w.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		vb.add_child(w)
		return
	var em := LineEdit.new()
	em.placeholder_text = "Почта"
	em.text = _auth_email
	em.custom_minimum_size = Vector2(0, 44)
	vb.add_child(em)
	var pw := LineEdit.new()
	pw.placeholder_text = "Пароль (минимум 6 символов)"
	pw.secret = true
	pw.custom_minimum_size = Vector2(0, 44)
	vb.add_child(pw)
	var st := Label.new()
	st.text = ""
	st.add_theme_color_override("font_color", Color(1.0, 0.45, 0.45))
	st.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(st)
	_auth_status = st
	var li := _menu_button("Войти")
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
	var rg := _menu_button("Регистрация")
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
	var gs := _menu_button("Играть как гость (прогресс только на этом устройстве)")
	gs.pressed.connect(func():
		_auth_close()
		_build_menu()
	)
	vb.add_child(gs)
	var note := Label.new()
	note.text = "Аккаунт синхронизирует прогресс между браузером, ВК и MAX.\\nВход через ВК и MAX — скоро."
	note.add_theme_font_size_override("font_size", 12)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(note)

# ---------------- ПРОФИЛЬ ИГРОКА (user://profile.cfg) ----------------""")

# 2) HTTPRequest в _build_ui
rep("""	add_child(layer)
	_ui.layer = layer
	var turn := Label.new()""",
"""	add_child(layer)
	_ui.layer = layer
	_http = HTTPRequest.new()
	_http.request_completed.connect(_on_api_done)
	layer.add_child(_http)
	var turn := Label.new()""")

# 3) пуш профиля на сервер при каждом сохранении
rep("""	cfg.set_value("player", "owned_colors", _profile.get("owned_colors", [1, 0, 0]))
	cfg.save("user://profile.cfg")""",
"""	cfg.set_value("player", "owned_colors", _profile.get("owned_colors", [1, 0, 0]))
	cfg.save("user://profile.cfg")
	if _sync_push and _auth_token != "" and _http != null:
		_api_call("save", {"token": _auth_token, "profile": _profile})""")

# 4) точка входа: автологин или экран входа вместо сразу меню
rep("""		else:
			_build_menu()""",
"""		else:
			_auth_cfg_load()
			if _auth_token != "":
				_build_auth(true)
				_api_call("load", {"token": _auth_token})
			else:
				_build_auth(false)""")

# 5) метка аккаунта в главном меню
rep("""	vb.add_child(_daily_box())""",
"""	vb.add_child(_daily_box())
	vb.add_child(_framed_label("👤 " + (_auth_email if _auth_email != "" else "Гость — прогресс только на этом устройстве"), 13))""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.25")
