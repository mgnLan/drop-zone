extends Node3D
## Точка Сброса: Королевская битва (ex Drop Zone) — 3D срез v6.2: ИГРАБЕЛЬНЫЙ прототип (4v4 против ботов).
## Управление: ЛКМ — выбрать бойца / ход / открыть ящик / стрелять,
## ПКМ-зажать и тянуть — вращение камеры, колесо — зум, Esc — отмена выбора,
## Space — конец хода, R — перезарядка, F — нож/ствол, I — рюкзак.
## Лутбоксы: содержимое скрыто до вскрытия (2 AP), в каждом 2–4 предмета.
## Запуск: -- --shot [--seed 123] [--closeup] | -- --testplay (проверка UI)
## Модели Quaternius (CC0): Toon Shooter, Cyberpunk Kit, Ultimate Textured Buildings.

const M := "res://assets/models/"
const C := "res://assets/models/cyberpunk/"
const H := "res://assets/models/humans/"
const B := "res://assets/models/buildings/"
const GUNS := "res://assets/models/guns/"

const GRID := 40            # максимальный размер (режим 4×4)
const CELL := 1.2
# фактический размер карты зависит от режима (1×1, 2×2, 4×4)
var _mode := 4
var _grid_n := 40
var _half_n := 19.5
var _size_n := 48.0

const HUMAN_SCALE := 0.85   # уменьшенные персонажи (правка Антона 2026-08-26)

const WEAPON_NODES := ["AK", "GrenadeLauncher", "Knife_1", "Knife_2", "Pistol",
	"Revolver", "Revolver_Small", "RocketLauncher", "SMG", "ShortCannon",
	"Shotgun", "Sniper", "Sniper_2", "Shovel", "Grenade", "FireGrenade"]

const HOUSE_MODELS := ["House_1Story.fbx", "House_1Story_Gable.fbx",
	"House_2Story.fbx", "House_2Story_Gable.fbx", "House_2Story_Wide.fbx"]
const HOUSE_PALETTES := ["Texture_Grey", "Texture_DarkBlue", "Texture_Red", "Texture_Dark"]
const COVER_MODELS := ["AC_Stacked.gltf", "Computer_Large.gltf", "Pipe_1.gltf", "Platform_2x2.gltf"]

var _rng := RandomNumberGenerator.new()
var _items := {}
var _occupied := {}          # "x,z" -> true (статика: дома, укрытия, ящики)
var _chests := {}            # "x,z" -> Array предметов (содержимое скрыто до вскрытия)
var _chest_pads := {}        # "x,z" -> MeshInstance3D подсветки ящика
var _palettes := {}

# ---- ИГРОВОЕ СОСТОЯНИЕ ----
const BASE_CARRY := 12.0     # базовый носимый вес
const OPEN_CHEST_AP := 2
const RELOAD_AP := 2
const HIT_CHANCE := 0.8
const VISION := 10           # радиус обзора бойца (туман войны)

var _fighters := []          # см. _spawn_human
var _unit_at := {}           # "x,z" -> индекс в _fighters
var _selected := -1
var _reach := {}             # Vector2i -> стоимость хода для выбранного
var _hl := []                # ноды подсветки клеток
var _sel_ring: MeshInstance3D = null
var _sel_name: Label3D = null         # имя активного бойца над головой
var _edge_arrows := {}                # idx -> {tri, dl}: стрелки на врагов за экраном
var _arrow_layer: Control = null
var _zone_lbl: Label3D = null
const TEAM_COLORS := [Color("#ff4757"), Color("#3498ff")]
var _busy := false           # идёт анимация/ход ботов — ввод заблокирован
var _turn := 1
var _game_over := false
var _ui := {}

# ---- камера/графика/меню/туман войны ----
var _cam: Camera3D = null
var _cam_dist := 64.0        # текущий зум (дистанция до центра)
var _cam_yaw := 45.0         # азимут камеры (градусы)
var _cam_pitch := 45.0       # угол наклона камеры (градусы)
var _rmb_drag := false       # ПКМ зажата — вращение камеры
var _rmb_moved := false      # было ли движение при зажатой ПКМ
const CAM_MIN := 18.0
const CAM_MAX := 90.0
const CAM_PITCH_MIN := 25.0
const CAM_PITCH_MAX := 70.0
var _gfx := {}               # ссылки на источники света и окружение
var _settings := {"graphics": 2, "sound": true}   # графика: 0/1/2
var _menu_open := false
var _blocks_sight := {}      # "x,z" -> true (дома и тяжёлые укрытия)
var _soft_cover := {}        # "x,z" -> true (лёгкие укрытия: -15% к шансу попадания)
var _sfx := {}
var _profile := {}           # личный профиль: ники, город, аватар, статы бойцов
var _battle_log := []        # последние строки боевого лога
var _shake := 0.0            # тряска камеры при взрывах
var _aim_beam: MeshInstance3D = null   # луч прицеливания
var _aim_lbl: Label3D = null           # подпись шанса попадания
var _aim_target := -1
var _aim_col := Color(-1.0, -1.0, -1.0)
var _houses: Array = []            # {cells, door, node, faded}
var _house_at := {}                # ключ клетки -> id дома
var _covers := {}                  # центр -> {hp, cells, node, heavy}
var _cover_at := {}                # ключ клетки -> центр укрытия
var _fire := {}                    # Vector2i -> осталось раундов
var _graffiti := {}                # ключ клетки -> true (метка оставлена)
var _fire_nodes := {}              # Vector2i -> Node3D
var _zone_min := Vector2i(0, 0)
var _zone_max := Vector2i(0, 0)
var _zone_phase := 0
var _zone_walls := []
var _cam_target := Vector3(0, 0.5, 0)   # точка, за которой следит камера
var _lmb_down := false
var _lmb_moved := false
var _lmb_pos := Vector2.ZERO
var _touch_pts := {}
var _pinch := 0.0
var _override_mouse := Vector2(-1, -1)  # для тач-кликов

func _load_mode() -> void:
	# режим матча: 1 = 1×1, 2 = 2×2, 4 = 4×4 (карта соразмерно меньше)
	var cfg := ConfigFile.new()
	if cfg.load("user://mode.cfg") == OK:
		_mode = int(cfg.get_value("game", "mode", 4))
	if _mode not in [1, 2, 4]:
		_mode = 4
	_grid_n = {1: 22, 2: 28, 4: 40}[_mode]
	_half_n = (_grid_n - 1) / 2.0
	_size_n = _grid_n * CELL

func _save_mode(m: int) -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("game", "mode", m)
	cfg.save("user://mode.cfg")

func gw(gx: float, gz: float, y := 0.0) -> Vector3:
	return Vector3((gx - _half_n) * CELL, y, (gz - _half_n) * CELL)

# ---------- онбординг первого боя ----------
var _onboard_step := -1          # -1 = обучение не идёт
var _onboard_bar: PanelContainer = null
var _onboard_lbl: Label = null
var _onboard_pulse: Control = null
var _pulse_t := 0.0
const ONBOARD_TXT := [
	"Обучение 1/4: выбери бойца — кликни по нему на поле или по карточке слева",
	"Обучение 2/4: кликни подсвеченную клетку — боец переместится",
	"Обучение 3/4: кликни по врагу, чтобы открыть огонь. Открой ящик — там снаряжение",
	"Обучение 4/4: нажми «Конец хода» — ход перейдёт противнику",
]

func _onboard_start() -> void:
	if _menu_open or int(_profile.get("onboarded", 0)) == 1:
		return
	_onboard_step = 0
	var hb := PanelContainer.new()
	hb.anchor_left = 0.5
	hb.anchor_right = 0.5
	var ow: float = min(280.0, _vw() * 0.47)
	hb.offset_left = -ow
	hb.offset_right = ow
	hb.offset_top = 66.0 if _mob() else 10.0
	hb.offset_bottom = 118.0 if _mob() else 62.0
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.10, 0.08, 0.02, 0.88)
	sb.border_color = Color(1.0, 0.85, 0.3, 0.95)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(8)
	sb.set_content_margin_all(8)
	hb.add_theme_stylebox_override("panel", sb)
	var l := Label.new()
	l.add_theme_font_size_override("font_size", 15)
	l.add_theme_color_override("font_color", Color(1.0, 0.92, 0.55))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	hb.add_child(l)
	_ui.layer.add_child(hb)
	_onboard_bar = hb
	_onboard_lbl = l
	_onboard_update()

func _onboard_update() -> void:
	if _onboard_step < 0 or _onboard_lbl == null:
		return
	_onboard_lbl.text = ONBOARD_TXT[_onboard_step]
	# сброс прошлой подсветки
	if _onboard_pulse != null and is_instance_valid(_onboard_pulse):
		_onboard_pulse.modulate = Color(1, 1, 1)
	_onboard_pulse = null
	# цель подсветки по шагу
	if _onboard_step == 0 and _ui.has("squad_rows") and _ui.squad_rows.size() > 0:
		_onboard_pulse = _ui.squad_rows[0].row
	elif _onboard_step == 3 and _ui.has("end_btn"):
		_onboard_pulse = _ui.end_btn

func _onboard_next() -> void:
	if _onboard_step < 0:
		return
	_onboard_step += 1
	if _onboard_step >= ONBOARD_TXT.size():
		_onboard_finish()
	else:
		_onboard_update()

func _onboard_finish() -> void:
	_onboard_step = -1
	if _onboard_pulse != null and is_instance_valid(_onboard_pulse):
		_onboard_pulse.modulate = Color(1, 1, 1)
	_onboard_pulse = null
	if _onboard_bar != null and is_instance_valid(_onboard_bar):
		_onboard_bar.queue_free()
	_onboard_bar = null
	_onboard_lbl = null
	_profile.onboarded = 1
	_save_profile()
	_log("Обучение завершено — в бой!")

# ---------- мобильный UI: масштаб через stretch keep_height (project.godot) ----------
func _apply_display_scale() -> void:
	# масштабом управляет движок (stretch: canvas_items, keep_height) — функция-заглушка
	pass

func _dpr() -> float:
	# в браузере viewport считается в device-пикселях — переводим в CSS-пиксели
	if OS.has_feature("web"):
		var d = JavaScriptBridge.eval("window.devicePixelRatio || 1")
		if d != null and float(d) > 0.01:
			return float(d)
	return 1.0

func _vw() -> float:
	# логическая ширина экрана в CSS-пикселях
	return get_viewport().get_visible_rect().size.x / _dpr()

func _vh() -> float:
	return get_viewport().get_visible_rect().size.y / _dpr()

func _mob() -> bool:
	# узкий экран — компактные раскладки
	return _vw() < 520.0

func _ready() -> void:
	_apply_display_scale()
	get_viewport().size_changed.connect(func(): _apply_display_scale.call_deferred())
	var args := OS.get_cmdline_user_args()
	if args.has("--win324"):
		DisplayServer.window_set_size(Vector2i(648, 1440))  # эмуляция портрета телефона
	var seed_idx := args.find("--seed")
	if seed_idx >= 0 and seed_idx + 1 < args.size():
		_rng.seed = int(args[seed_idx + 1])
	else:
		_rng.randomize()
	_biome = _rng.randi() % 2
	_load_mode()
	_load_items()
	_load_profile()
	_build_ground()
	_build_neon_ring()
	_generate_houses()
	_generate_covers()
	_generate_loot()
	_scatter_decor()
	_build_perimeter()
	_spawn_teams()
	_zone_min = Vector2i(0, 0)
	_zone_max = Vector2i(_grid_n - 1, _grid_n - 1)
	_update_zone_walls()
	_setup_lighting()
	_setup_camera()
	if args.has("--shot"):
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		var name := "slice_3d_v5_closeup" if args.has("--closeup") else "slice_3d_v5"
		get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/%s.png" % name)
		print("SHOT_SAVED seed=", _rng.seed)
		get_tree().quit()
	elif args.has("--testplay"):
		_build_ui()
		_run_testplay()
	elif args.has("--testbots"):
		_build_ui()
		_run_testbots()
	elif args.has("--testmenu"):
		_load_sfx()
		_build_ui()
		_build_menu()
		_run_testmenu()
	elif args.has("--testmenumobile"):
		_load_sfx()
		_build_ui()
		get_window().size = Vector2i(360, 800)
		await get_tree().process_frame
		await get_tree().process_frame
		_build_menu()
		_run_testmenu(true)
	elif args.has("--testauth"):
		_run_testauth("test_auth.png")
	elif args.has("--testauthwide"):
		_dbg_vp = Vector2i(1280, 800)
		_run_testauth("test_auth_wide.png")
	elif args.has("--testauthmobile"):
		_dbg_vp = Vector2i(360, 800)
		_run_testauth("test_auth_mobile.png")
	elif args.has("--rendericons"):
		_run_rendericons()
	else:
		_load_sfx()
		_ambient_start()
		_build_ui()
		# автостарт после выбора режима в меню (сцена перезагружена)
		var as_cfg := ConfigFile.new()
		if as_cfg.load("user://autostart.cfg") == OK and as_cfg.get_value("game", "autostart", 0) == 1:
			as_cfg.set_value("game", "autostart", 0)
			as_cfg.save("user://autostart.cfg")
			_menu_open = false
			_busy = false
			if int(_profile.get("onboarded", 0)) == 1:
				_stamina_update()
				_profile.stamina = maxf(0.0, float(_profile.stamina) - STAMINA_COST)
				_save_profile()
			_apply_graphics(_settings.graphics)
			_update_fog()
			_log("Тренировка %d×%d — ваш ход! ЛКМ — бойцы, ПКМ-тянуть — обзор." % [_mode, _mode])
			_log("Биом: %s" % ("🏭 Индустриальная зона" if _biome == 1 else "🏙 Бетонная арена"))
			_onboard_start()
		else:
			_auth_cfg_load()
			if _auth_token != "":
				_build_auth(true)
				_api_call("load", {"token": _auth_token})
			else:
				_build_auth(false)

func _load_items() -> void:
	var f := FileAccess.open("res://data/items.json", FileAccess.READ)
	var json := JSON.new()
	json.parse(f.get_as_text())
	_items = json.data

# ---------------- АККАУНТ: почта сейчас, ВК/MAX позже ----------------
const API_URL := "https://podvezu.online/dropzone/api/index.php"
var _auth_token := ""
var _auth_email := ""
var _auth_pending := ""        # какой запрос сейчас в полёте
var _http: HTTPRequest = null
var _auth_layer: CanvasLayer = null
var _auth_status: Label = null
var _auth_hint: Label = null      # подсказка про гостевой режим при сетевой ошибке
var _auth_guest: Button = null    # кнопка гостя (пульс при сетевой ошибке)
var _dbg_vp := Vector2i.ZERO      # переопределение вьюпорта для тест-скринов
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

func _on_api_done(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
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

func _auth_fail(msg: String, act: String, net := false) -> void:
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
	# единая вертикальная ось: лого по центру НАД формой, без ручных смещений
	var center := CenterContainer.new()
	center.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(center)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 16)
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_child(col)
	var vw2: float = float(_dbg_vp.x) if _dbg_vp.x > 0 else _vw()
	var vh2: float = float(_dbg_vp.y) if _dbg_vp.y > 0 else _vh()
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
	_logo_pulse(logo)
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
	lis.set_corner_radius_all(12)
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
	# прозрачная кнопка с белой обводкой
	var rgs := StyleBoxFlat.new()
	rgs.bg_color = Color(0, 0, 0, 0)
	rgs.border_color = Color(1, 1, 1, 0.8)
	rgs.set_border_width_all(1)
	rgs.set_corner_radius_all(12)
	rg.add_theme_stylebox_override("normal", rgs)
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
	var gs := _menu_button("Играть как гость")
	gs.custom_minimum_size = Vector2(0, 40)
	# мелкая серая текст-ссылка, не кнопка
	gs.flat = true
	gs.add_theme_font_size_override("font_size", 13)
	gs.add_theme_color_override("font_color", Color(0.72, 0.76, 0.82))
	gs.add_theme_color_override("font_hover_color", Color(1, 1, 1))
	gs.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	gs.pressed.connect(func():
		_auth_close()
		_build_menu()
	)
	vb.add_child(gs)
	_auth_guest = gs
	var note := Label.new()
	note.text = "Аккаунт синхронизирует прогресс между браузером, ВК и MAX.
Вход через ВК и MAX — скоро."
	note.add_theme_font_size_override("font_size", 12)
	note.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(note)

# ---------------- ПРОФИЛЬ ИГРОКА (user://profile.cfg) ----------------
const STAT_KEYS := ["str", "agi", "end", "per", "int", "lck"]
const STAT_NAMES := {"str": "Сила", "agi": "Ловкость", "end": "Выносливость",
	"per": "Восприятие", "int": "Интеллект", "lck": "Удача"}
const STAT_HINTS := {"str": "+2 кг веса/очко; СИЛ 4+ для тяжёлого оружия",
	"agi": "+1 ОД за 3 очка (макс +3); +0.5% уклонения/очко",
	"end": "+15 HP за очко", "per": "+1 обзор за 2 очка",
	"int": "+2% точности (макс 20%) и +10% опыта/очко", "lck": "+0.1% к криту (база 5%, x1.5)/очко"}
const STAT_POINTS := 5        # очков на распределение каждому бойцу
const SLOT_WINS := {2: 3, 3: 10, 4: 25}   # слот -> сколько побед нужно
# таланты: ранг N стоит N очков (1/2/3); очко талантов — каждые 3 уровня бойца
const TALENTS := [
	{"id": "reload1", "icon": "⚡", "name": "Быстрая перезарядка", "max": 1, "desc": "Перезарядка стоит 1 ОД"},
	{"id": "sapper", "icon": "💣", "name": "Сапёр", "max": 1, "desc": "Бочки взводятся с 1 попадания, взрыв +25%"},
	{"id": "steady", "icon": "🛡", "name": "Устойчивость", "max": 1, "desc": "Тяжёлое оружие (6+ ОД / str_req) — на 1 ОД дешевле"},
	{"id": "marathon", "icon": "🏃", "name": "Марафон", "max": 1, "desc": "+1 ОД максимум"},
	{"id": "medic", "icon": "💊", "name": "Полевой врач", "max": 3, "desc": "+25% к лечению аптечкой за ранг"},
	{"id": "scout", "icon": "👁", "name": "Разведчик", "max": 3, "desc": "+1 обзор за ранг"},
	{"id": "mule", "icon": "🎒", "name": "Тягловый", "max": 3, "desc": "+2 кг носимого веса за ранг"},
	{"id": "lucky", "icon": "🍀", "name": "Фартовый", "max": 3, "desc": "+2% к шансу крита за ранг"},
]
const TALENT_RESET_COST := 600  # монет за сброс талантов (слив экономики)
# владение оружием: опыт класса = нанесённый урон; пороги уровней 100/250/500
const WEAPON_CLASS := {"Pistol": "pistols", "Revolver_Small": "pistols", "Revolver": "pistols",
	"SMG": "smg", "AK": "rifles", "Shotgun": "shotguns", "Sniper": "sniper", "Sniper_2": "sniper",
	"GrenadeLauncher": "heavy", "ShortCannon": "heavy", "RocketLauncher": "heavy",
	"knife_1": "melee", "Shovel": "melee", "Knife_2": "melee"}
const PROF_XP := [100, 250, 500]
const CLASS_NAMES := {"pistols": "Пистолеты", "smg": "ПП", "rifles": "Винтовки",
	"shotguns": "Дробовики", "sniper": "Снайперское", "heavy": "Тяжёлое", "melee": "Ближний бой"}
const DAILY_QUESTS := [
	{"name": "Убей 5 противников", "need": 5, "reward": 6},
	{"name": "Открой 3 ящика", "need": 3, "reward": 5},
	{"name": "Выиграй бой", "need": 1, "reward": 10},
]
var _chests_opened := 0       # ящиков открыто игроком за текущий бой
const SHOP_ITEMS := [
	{"kind": "frame", "idx": 1, "name": "Рамка «Неон»", "price": 200},
	{"kind": "frame", "idx": 2, "name": "Рамка «Золото»", "price": 500},
	{"kind": "nick_color", "idx": 1, "name": "Цвет ника «Красный»", "price": 150},
	{"kind": "nick_color", "idx": 2, "name": "Цвет ника «Золотой»", "price": 400},
]

func _shop_owned(kind: String, idx: int) -> bool:
	var arr: Array = _profile.get("owned_frames" if kind == "frame" else "owned_colors", [1, 0, 0])
	return idx < arr.size() and int(arr[idx]) == 1

func _shop_equipped(kind: String, idx: int) -> bool:
	return int(_profile.get(kind, 0)) == idx

func _shop_equip(kind: String, idx: int) -> void:
	if kind == "frame":
		_profile.frame = idx
	else:
		_profile.nick_color = idx
	_save_profile()

func _shop_buy(si: int) -> void:
	var it: Dictionary = SHOP_ITEMS[si]
	var kind := str(it["kind"])
	var idx := int(it["idx"])
	var price := int(it["price"])
	if int(_profile.get("coins", 0)) < price:
		return
	_profile.coins = int(_profile.get("coins", 0)) - price
	var key := "owned_frames" if kind == "frame" else "owned_colors"
	var arr: Array = _profile.get(key, [1, 0, 0]).duplicate()
	while arr.size() <= idx:
		arr.append(0)
	arr[idx] = 1
	_profile[key] = arr
	_shop_equip(kind, idx)
	_save_profile()

func _daily_check() -> void:
	var today := Time.get_date_string_from_system()
	if str(_profile.get("daily_date", "")) != today:
		_profile.daily_date = today
		_profile.daily_prog = [0, 0, 0]
		_profile.daily_claimed = [0, 0, 0]

const STAMINA_MAX := 100.0
const STAMINA_COST := 15.0
const STAMINA_PER_SEC := 100.0 / 86400.0  # 100 за сутки, равномерно

func _stamina_update() -> void:
	# реген по реальному времени (timestamp); локально, позже — на сервер
	var now := float(Time.get_unix_time_from_system())
	var last := float(_profile.get("stamina_ts", 0.0))
	if last <= 0.0:
		_profile.stamina = STAMINA_MAX
	else:
		_profile.stamina = minf(STAMINA_MAX, float(_profile.get("stamina", STAMINA_MAX)) + (now - last) * STAMINA_PER_SEC)
	_profile.stamina_ts = now

func _stamina_can_fight() -> bool:
	_stamina_update()
	# обучение (первый бой) — бесплатно
	return int(_profile.get("onboarded", 0)) == 0 or float(_profile.get("stamina", STAMINA_MAX)) >= STAMINA_COST

func _daily_add(qi: int, n: int) -> Array:
	var msgs := []
	if n <= 0:
		return msgs
	_daily_check()
	if int(_profile.daily_claimed[qi]) == 1:
		return msgs
	var need: int = int(DAILY_QUESTS[qi]["need"])
	_profile.daily_prog[qi] = mini(int(_profile.daily_prog[qi]) + n, need)
	if int(_profile.daily_prog[qi]) >= need:
		_profile.daily_claimed[qi] = 1
		_profile.coins = int(_profile.get("coins", 0)) + int(DAILY_QUESTS[qi]["reward"])
		msgs.append("📅 Задание дня «%s» — +%d 💰" % [str(DAILY_QUESTS[qi]["name"]), int(DAILY_QUESTS[qi]["reward"])])
	return msgs
var _battle_reward := {}      # итоги последнего боя для экрана победы

func _default_fighter_stats() -> Dictionary:
	return {"str": 0, "agi": 0, "end": 0, "per": 0, "int": 0, "lck": 0}

func _load_profile() -> void:
	_profile = {
		"names": ["Волк", "Сокол", "Тень", "Барс"],
		"city": "",
		"avatar": "",
		"avatar_preset": 1,
		"gender": "m",            # m/f — мужчина/женщина
		"skin": 0,                # 0..3 — оттенок кожи
		"frame": 0,               # рамка аватара: 0 стандарт, 1 неон, 2 золото (монетизация)
		"nick_color": 0,          # цвет ника: 0 белый, 1 красный, 2 золото (монетизация)
		"unlocked_slots": 1,      # стартовый игрок: 1 слот; остальные — заслуги/подписка
		"onboarded": 0,           # 1 = обучение первого боя пройдено
		"coins": 0,               # копилка монет (монетизация)
		"stamina": 100.0,         # выносливость шоу (бой −15)
		"stamina_ts": 0.0,        # unixtime последнего пересчёта
		"wins": 0,                # побед всего
		"total_kills": 0,         # убийств всего
		"daily_date": "",           # дата текущих ежедневных заданий
		"daily_prog": [0, 0, 0],    # прогресс по 3 заданиям
		"daily_claimed": [0, 0, 0], # награды получены
		"owned_frames": [1, 0, 0],    # купленные рамки (0 стандарт — всегда есть)
		"owned_colors": [1, 0, 0],    # купленные цвета ника
		"owned_taunts": [1, 0, 0],    # паки насмешек (0 стандартный)
		"shards": 0,                  # осколки (валюта обмена за дубликаты)
		"pity": [0, 0, 0],            # открытий без эпика/легенды/мифика
		"chests_total": 0,            # сундуков открыто всего
		"owned_teleports": [1, 1, 0], # телепорты: луч, дыра, шторм (BP)
		"bp_xp": 0,                   # сезонный опыт Battle Pass
		"bp_owned": 0,                # 1 = пропуск куплен
		"bp_claimed_free": [],        # забранные награды free-ленты
		"bp_claimed_prem": [],        # забранные награды premium-ленты
		"stats": [_default_fighter_stats(), _default_fighter_stats(),
			_default_fighter_stats(), _default_fighter_stats()],
		"lvl": [1, 1, 1, 1],
		"xp": [0, 0, 0, 0],
		"talents": [{}, {}, {}, {}],  # таланты бойцов (id -> ранг)
		"tpts": [0, 0, 0, 0],         # очки талантов
		"prof": [{}, {}, {}, {}],     # владение оружием (класс -> урон)
	}
	var cfg := ConfigFile.new()
	if cfg.load("user://profile.cfg") != OK:
		return
	for i in 4:
		_profile.names[i] = cfg.get_value("fighter%d" % i, "name", _profile.names[i])
		var st := _default_fighter_stats()
		for k in STAT_KEYS:
			st[k] = int(cfg.get_value("fighter%d" % i, k, 0))
		_profile.stats[i] = st
		_profile.lvl[i] = int(cfg.get_value("fighter%d" % i, "lvl", 1))
		_profile.xp[i] = int(cfg.get_value("fighter%d" % i, "xp", 0))
		_profile.talents[i] = cfg.get_value("fighter%d" % i, "talents", {})
		_profile.tpts[i] = int(cfg.get_value("fighter%d" % i, "tpts", 0))
		_profile.prof[i] = cfg.get_value("fighter%d" % i, "prof", {})
	_profile.city = cfg.get_value("player", "city", "")
	_profile.avatar = cfg.get_value("player", "avatar", "")
	_profile.avatar_preset = int(cfg.get_value("player", "avatar_preset", 1))
	_profile.gender = cfg.get_value("player", "gender", "m")
	_profile.skin = int(cfg.get_value("player", "skin", 0))
	_profile.frame = int(cfg.get_value("player", "frame", 0))
	_profile.nick_color = int(cfg.get_value("player", "nick_color", 0))
	_profile.unlocked_slots = int(cfg.get_value("player", "unlocked_slots", 1))
	_profile.onboarded = int(cfg.get_value("player", "onboarded", 0))
	_profile.coins = int(cfg.get_value("player", "coins", 0))
	_profile.stamina = float(cfg.get_value("player", "stamina", 100.0))
	_profile.stamina_ts = float(cfg.get_value("player", "stamina_ts", 0.0))
	_profile.wins = int(cfg.get_value("player", "wins", 0))
	_profile.total_kills = int(cfg.get_value("player", "total_kills", 0))
	_profile.daily_date = str(cfg.get_value("player", "daily_date", ""))
	_profile.daily_prog = cfg.get_value("player", "daily_prog", [0, 0, 0])
	_profile.daily_claimed = cfg.get_value("player", "daily_claimed", [0, 0, 0])
	_profile.teleport = str(cfg.get_value("player", "teleport", "beam"))
	_profile.owned_frames = cfg.get_value("player", "owned_frames", [1, 0, 0])
	_profile.owned_colors = cfg.get_value("player", "owned_colors", [1, 0, 0])
	_profile.owned_taunts = cfg.get_value("player", "owned_taunts", [1, 0, 0])
	_profile.shards = int(cfg.get_value("player", "shards", 0))
	_profile.pity = cfg.get_value("player", "pity", [0, 0, 0])
	_profile.chests_total = int(cfg.get_value("player", "chests_total", 0))
	_profile.owned_teleports = cfg.get_value("player", "owned_teleports", [1, 1, 0])
	_profile.bp_xp = int(cfg.get_value("player", "bp_xp", 0))
	_profile.bp_owned = int(cfg.get_value("player", "bp_owned", 0))
	_profile.bp_claimed_free = cfg.get_value("player", "bp_claimed_free", [])
	_profile.bp_claimed_prem = cfg.get_value("player", "bp_claimed_prem", [])
	_daily_check()

func _save_profile() -> void:
	var cfg := ConfigFile.new()
	for i in 4:
		cfg.set_value("fighter%d" % i, "name", _profile.names[i])
		for k in STAT_KEYS:
			cfg.set_value("fighter%d" % i, k, _profile.stats[i][k])
		cfg.set_value("fighter%d" % i, "lvl", _profile.lvl[i])
		cfg.set_value("fighter%d" % i, "xp", _profile.xp[i])
		cfg.set_value("fighter%d" % i, "talents", _profile.talents[i])
		cfg.set_value("fighter%d" % i, "tpts", _profile.tpts[i])
		cfg.set_value("fighter%d" % i, "prof", _profile.prof[i])
	cfg.set_value("player", "city", _profile.city)
	cfg.set_value("player", "avatar", _profile.avatar)
	cfg.set_value("player", "avatar_preset", _profile.avatar_preset)
	cfg.set_value("player", "gender", _profile.gender)
	cfg.set_value("player", "skin", _profile.skin)
	cfg.set_value("player", "frame", _profile.frame)
	cfg.set_value("player", "nick_color", _profile.nick_color)
	cfg.set_value("player", "unlocked_slots", _profile.unlocked_slots)
	cfg.set_value("player", "onboarded", int(_profile.get("onboarded", 0)))
	cfg.set_value("player", "coins", int(_profile.get("coins", 0)))
	cfg.set_value("player", "stamina", float(_profile.get("stamina", 100.0)))
	cfg.set_value("player", "stamina_ts", float(_profile.get("stamina_ts", 0.0)))
	cfg.set_value("player", "wins", int(_profile.get("wins", 0)))
	cfg.set_value("player", "total_kills", int(_profile.get("total_kills", 0)))
	cfg.set_value("player", "daily_date", str(_profile.get("daily_date", "")))
	cfg.set_value("player", "daily_prog", _profile.get("daily_prog", [0, 0, 0]))
	cfg.set_value("player", "daily_claimed", _profile.get("daily_claimed", [0, 0, 0]))
	cfg.set_value("player", "teleport", str(_profile.get("teleport", "beam")))
	cfg.set_value("player", "owned_frames", _profile.get("owned_frames", [1, 0, 0]))
	cfg.set_value("player", "owned_colors", _profile.get("owned_colors", [1, 0, 0]))
	cfg.set_value("player", "owned_taunts", _profile.get("owned_taunts", [1, 0, 0]))
	cfg.set_value("player", "shards", int(_profile.get("shards", 0)))
	cfg.set_value("player", "pity", _profile.get("pity", [0, 0, 0]))
	cfg.set_value("player", "chests_total", int(_profile.get("chests_total", 0)))
	cfg.set_value("player", "owned_teleports", _profile.get("owned_teleports", [1, 1, 0]))
	cfg.set_value("player", "bp_xp", int(_profile.get("bp_xp", 0)))
	cfg.set_value("player", "bp_owned", int(_profile.get("bp_owned", 0)))
	cfg.set_value("player", "bp_claimed_free", _profile.get("bp_claimed_free", []))
	cfg.set_value("player", "bp_claimed_prem", _profile.get("bp_claimed_prem", []))
	cfg.save("user://profile.cfg")
	if _sync_push and _auth_token != "" and _http != null:
		_api_call("save", {"token": _auth_token, "profile": _profile})

# ---- таланты и владение оружием ----
func _tal(f: Dictionary, tid: String) -> int:
	# ранг таланта бойца (0 — нет)
	return int(f.get("talents", {}).get(tid, 0))

func _weapon_class(w: Dictionary) -> String:
	return WEAPON_CLASS.get(str(w.get("id", "")), "")

func _prof_lvl(f: Dictionary, cls: String) -> int:
	# уровень владения 0..3: опыт класса = нанесённый урон, пороги 100/250/500
	if cls == "":
		return 0
	var px := int(f.get("prof", {}).get(cls, 0))
	var lv := 0
	for th in PROF_XP:
		if px >= th:
			lv += 1
	return lv

func _shot_cost(f: Dictionary, w: Dictionary) -> int:
	# стоимость выстрела: талант «Устойчивость» (−1 ОД тяжёлому) + владение ур.3 (−1 ОД)
	var c: int = w.get("ap_cost", 3)
	if _tal(f, "steady") > 0 and (int(w.get("str_req", 0)) > 0 or c >= 6):
		c -= 1
	if _prof_lvl(f, _weapon_class(w)) >= 3:
		c -= 1
	return maxi(1, c)

func _tal_buy(f: Dictionary, tid: String) -> bool:
	# покупка ранга: ранг N стоит N очков талантов
	var cur := _tal(f, tid)
	var t: Dictionary = TALENTS[0]
	for t2 in TALENTS:
		if t2["id"] == tid:
			t = t2
	if cur >= int(t["max"]):
		return false
	var cost := cur + 1
	if int(f.get("tpts", 0)) < cost:
		return false
	f.tpts = int(f.tpts) - cost
	if not f.has("talents"):
		f.talents = {}
	f.talents[tid] = cur + 1
	_recalc_derived(f)
	_sfx_play("click")
	_log("%s: талант «%s» — ранг %d" % [f.name, t["name"], cur + 1])
	return true

# производные характеристики бойца из распределённых очков
func _stat_hp(st: Dictionary) -> int:
	return 100 + 15 * int(st.get("end", 0))

func _stat_ap(st: Dictionary) -> int:
	# +1 ОД за 3 очка ловкости, максимум +3
	return 10 + mini(3, int(st.get("agi", 0)) / 3)

func _stat_carry(st: Dictionary) -> float:
	return BASE_CARRY + 2.0 * int(st.get("str", 0))

func _stat_vision(st: Dictionary) -> int:
	return VISION + int(st.get("per", 0)) / 2

func _stat_dodge(st: Dictionary) -> float:
	# уклонение от ловкости: +0.5%/очко, макс 15%
	return minf(0.15, 0.005 * int(st.get("agi", 0)))

func _stat_acc(st: Dictionary) -> float:
	# точность от интеллекта: +2%/очко, макс +20%
	return minf(0.20, 0.02 * int(st.get("int", 0)))

func _stat_crit(st: Dictionary) -> float:
	# крит: база 5% + 0.1% за очко удачи
	return 0.05 + 0.001 * int(st.get("lck", 0))

func _armor_ap_penalty(f: Dictionary) -> int:
	var p := 0
	for slot in ["helmets", "body", "pants"]:
		if f.armor[slot]:
			p += int(f.armor[slot].get("ap_penalty", 0))
	return p


# ---------------- МАТЕРИАЛЫ/ЗЕМЛЯ ----------------
func _mat(albedo: Color, metallic := 0.0, rough := 0.8, emission := Color.BLACK, e_energy := 0.0) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = albedo
	m.metallic = metallic
	m.roughness = rough
	if e_energy > 0.0:
		m.emission_enabled = true
		m.emission = emission
		m.emission_energy_multiplier = e_energy
	return m

var _biome := 0                # 0 = бетонная арена, 1 = индустриальная зона

func _build_ground() -> void:
	var ground := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(_size_n * 2.3, _size_n * 2.3)
	ground.mesh = pm
	ground.material_override = _mat(Color(0.07, 0.075, 0.09), 0.4, 0.6)
	add_child(ground)
	# бетонное поле арены — светлый тёплый серый, хорошо читается
	var inner := MeshInstance3D.new()
	var pm2 := PlaneMesh.new()
	pm2.size = Vector2(_size_n + 0.6, _size_n + 0.6)
	inner.mesh = pm2
	inner.position.y = 0.02
	inner.material_override = _mat(Color(0.26, 0.235, 0.20) if _biome == 1 else Color(0.30, 0.295, 0.28), 0.0, 0.97)  # бетон / ржавая индустриалка
	add_child(inner)
	# пятна/потёки на бетоне — крупные полупрозрачные полосы
	var stain_mat := StandardMaterial3D.new()
	stain_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	stain_mat.albedo_color = Color(0.36, 0.21, 0.13, 0.5) if _biome == 1 else Color(0.28, 0.27, 0.25, 0.55)
	stain_mat.roughness = 1.0
	for i in 12:
		var stain := MeshInstance3D.new()
		var sp := PlaneMesh.new()
		sp.size = Vector2(_rng.randf_range(2.0, 6.0), _rng.randf_range(1.2, 3.4))
		stain.mesh = sp
		stain.material_override = stain_mat
		stain.position = Vector3(_rng.randf_range(-20, 20), 0.024, _rng.randf_range(-20, 20))
		stain.rotation_degrees.y = _rng.randf() * 360.0
		add_child(stain)
	# тактическая сетка по клеткам — чуть темнее бетона, контрастная
	var grid_mat := _mat(Color(0.15, 0.15, 0.16), 0.0, 0.97)
	for i in _grid_n + 1:
		var off := (i - _grid_n / 2.0) * CELL - CELL * 0.5
		var lh := MeshInstance3D.new()
		var bh := BoxMesh.new()
		bh.size = Vector3(_size_n, 0.012, 0.035)
		lh.mesh = bh
		lh.material_override = grid_mat
		lh.position = Vector3(0, 0.028, off)
		add_child(lh)
		var lv := MeshInstance3D.new()
		var bv := BoxMesh.new()
		bv.size = Vector3(0.035, 0.012, _size_n)
		lv.mesh = bv
		lv.material_override = grid_mat
		lv.position = Vector3(off, 0.028, 0)
		add_child(lv)
	var podium := MeshInstance3D.new()
	var pm3 := PlaneMesh.new()
	pm3.size = Vector2(12, 12)
	podium.mesh = pm3
	podium.position.y = 0.04
	podium.material_override = _mat(Color(0.23, 0.24, 0.29), 0.6, 0.4)
	add_child(podium)

# ---------------- МЕЛКИЙ ДЕКОР ПОЛА (камни, трещины, трава, баки, фонари) ----------------
func _scatter_decor() -> void:
	var dk: float = _grid_n / 40.0   # масштаб декора под размер карты
	var far := int(_half_n) - 1
	var n_crack := int(_rng.randi_range(14, 20) * dk)
	var n_rock := int(_rng.randi_range(10, 14) * dk)
	var n_grass := int(_rng.randi_range(16, 24) * dk) if _biome == 0 else int(_rng.randi_range(4, 8) * dk)
	var n_bin := int(_rng.randi_range(4, 6) * dk)
	for i in n_crack:  # трещины — тёмные полосы по бетону
		var cell := _free_cell(3, far, 0)
		if cell.x < 0:
			continue
		var crack := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(_rng.randf_range(0.5, 1.6), 0.01, _rng.randf_range(0.06, 0.12))
		crack.mesh = bm
		crack.material_override = _mat(Color(0.10, 0.10, 0.11), 0.0, 1.0)
		crack.position = gw(cell.x, cell.y, 0.032)
		crack.rotation_degrees.y = _rng.randf() * 360.0
		add_child(crack)
	for i in n_rock:  # камни — сплюснутые многогранники
		var cell := _free_cell(3, far, 0)
		if cell.x < 0:
			continue
		var rock := MeshInstance3D.new()
		var sm := SphereMesh.new()
		sm.radial_segments = 6
		sm.rings = 3
		var r := _rng.randf_range(0.08, 0.22)
		sm.radius = r
		sm.height = r * _rng.randf_range(0.7, 1.1)
		rock.mesh = sm
		rock.material_override = _mat(Color(0.32, 0.31, 0.28), 0.0, 0.95)
		rock.position = gw(cell.x + _rng.randf_range(-0.3, 0.3), cell.y + _rng.randf_range(-0.3, 0.3), r * 0.4)
		rock.rotation_degrees.y = _rng.randf() * 360.0
		add_child(rock)
	var grass_mat := _mat(Color(0.25, 0.38, 0.16), 0.0, 0.9)
	for i in n_grass:  # трава из трещин — перекрещенные плоскости
		var cell := _free_cell(3, far, 0)
		if cell.x < 0:
			continue
		var tuft := Node3D.new()
		for k in 2:
			var blade := MeshInstance3D.new()
			var pl := PlaneMesh.new()
			pl.size = Vector2(0.28, 0.22)
			blade.mesh = pl
			blade.material_override = grass_mat
			blade.rotation_degrees = Vector3(-70, k * 90.0 + _rng.randf_range(-20, 20), 0)
			blade.position.y = 0.09
			tuft.add_child(blade)
		tuft.position = gw(cell.x + _rng.randf_range(-0.3, 0.3), cell.y + _rng.randf_range(-0.3, 0.3), 0.02)
		tuft.rotation_degrees.y = _rng.randf() * 360.0
		add_child(tuft)
	for i in n_bin:  # мусорные баки из примитивов
		var cell := _free_cell(4, far - 1, 0)
		if cell.x < 0:
			continue
		var bin := Node3D.new()
		var body := MeshInstance3D.new()
		var cm := CylinderMesh.new()
		cm.top_radius = 0.22
		cm.bottom_radius = 0.19
		cm.height = 0.55
		body.mesh = cm
		body.material_override = _mat(Color(0.20, 0.30, 0.22), 0.3, 0.6)
		body.position.y = 0.28
		bin.add_child(body)
		var lid := MeshInstance3D.new()
		var lm := CylinderMesh.new()
		lm.top_radius = 0.24
		lm.bottom_radius = 0.24
		lm.height = 0.06
		lid.mesh = lm
		lid.material_override = _mat(Color(0.15, 0.16, 0.18), 0.5, 0.45)
		lid.position.y = 0.58
		bin.add_child(lid)
		bin.position = gw(cell.x, cell.y, 0.02)
		bin.rotation_degrees.y = _rng.randf() * 360.0
		add_child(bin)
	# фонари внутри арены (свет не включаем — дёсадко дорого, просто пропсы)
	for i in maxi(2, int(4 * dk)):
		var cell := _free_cell(8, far - 1, 0)
		if cell.x < 0:
			continue
		_place(C + "Light_Street_2.gltf", gw(cell.x, cell.y), _rng.randf() * 360.0, 0.9)

func _build_neon_ring() -> void:
	var mat := _mat(Color.BLACK, 0.0, 1.0, Color(0.1, 0.9, 1.0), 6.0)
	var half_size := _size_n / 2.0 + 0.45
	for i in 4:
		var bar := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(_size_n + 0.9, 0.12, 0.22)
		bar.mesh = bm
		bar.material_override = mat
		bar.position.y = 0.06
		if i == 0: bar.position.z = -half_size
		elif i == 1: bar.position.z = half_size
		elif i == 2:
			bar.position.x = -half_size
			bar.rotation_degrees.y = 90
		else:
			bar.position.x = half_size
			bar.rotation_degrees.y = 90
		add_child(bar)
	var mat2 := _mat(Color.BLACK, 0.0, 1.0, Color(1.0, 0.35, 0.6), 5.0)
	for i in 4:
		var bar := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(12.2, 0.1, 0.16)
		bar.mesh = bm
		bar.material_override = mat2
		bar.position.y = 0.07
		if i == 0: bar.position.z = -6.1
		elif i == 1: bar.position.z = 6.1
		elif i == 2:
			bar.position.x = -6.1
			bar.rotation_degrees.y = 90
		else:
			bar.position.x = 6.1
			bar.rotation_degrees.y = 90
		add_child(bar)

# ---------------- МОДЕЛИ ----------------
func _palette(name: String) -> Texture2D:
	if not _palettes.has(name):
		_palettes[name] = load(B + name + ".png")
	return _palettes[name]

func _place(path: String, pos: Vector3, rot_y := 0.0, scl := 1.0, palette := "") -> Node3D:
	var inst: Node3D = load(path).instantiate()
	inst.position = pos
	inst.rotation_degrees.y = rot_y
	inst.scale = Vector3.ONE * scl
	add_child(inst)
	_make_lit(inst, palette)
	return inst

func _make_lit(node: Node, palette := "") -> void:
	if node is MeshInstance3D and node.mesh:
		for i in node.mesh.get_surface_count():
			var mat: Material = node.get_active_material(i)
			var needs_tex := palette != "" and (mat == null or not (mat is StandardMaterial3D) or (mat as StandardMaterial3D).albedo_texture == null)
			if needs_tex:
				var pm := StandardMaterial3D.new()
				pm.albedo_texture = _palette(palette)
				pm.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
				pm.roughness = 0.7
				pm.metallic = 0.1
				node.set_surface_override_material(i, pm)
			elif mat is StandardMaterial3D and mat.shading_mode == BaseMaterial3D.SHADING_MODE_UNSHADED:
				var lit: StandardMaterial3D = mat.duplicate()
				lit.shading_mode = BaseMaterial3D.SHADING_MODE_PER_PIXEL
				lit.roughness = 0.6
				lit.metallic = 0.15
				node.set_surface_override_material(i, lit)
	for c in node.get_children():
		_make_lit(c, palette)

# ---------------- РАНДОМНАЯ ГЕНЕРАЦИЯ ----------------
func _free_cell(min_d := 2, max_d := 18, footprint := 2) -> Vector2i:
	# случайная свободная клетка на дистанции min_d..max_d от центра
	# footprint 1 = одна клетка; вокруг объекта требуется зазор в 1 клетку,
	# чтобы объекты не слипались в непроходимые стены
	var r: int = footprint / 2
	for attempt in 60:
		var gx := _rng.randi_range(2, _grid_n - 3)
		var gz := _rng.randi_range(2, _grid_n - 3)
		var d: float = Vector2(gx - _half_n, gz - _half_n).length()
		if d < min_d or d > max_d:
			continue
		var ok := true
		for ox in range(-r - 1, r + 2):
			for oz in range(-r - 1, r + 2):
				if _occupied.has("%d,%d" % [gx + ox, gz + oz]):
					ok = false
		if ok:
			return Vector2i(gx, gz)
	return Vector2i(-1, -1)

func _claim(cell: Vector2i, footprint := 2) -> void:
	if footprint <= 1:
		_occupied[_key(cell)] = true
		return
	for ox in range(-footprint / 2, footprint / 2 + 1):
		for oz in range(-footprint / 2, footprint / 2 + 1):
			_occupied["%d,%d" % [cell.x + ox, cell.y + oz]] = true

func _generate_houses() -> void:
	# дома ×3 от исходника; на маленьких картах — соразмерно меньше; ВХОДИМЫЕ
	var k: float = _grid_n / 40.0
	var fp := maxi(3, int(8 * k))
	var n := maxi(1, int(_rng.randi_range(3, 4) * k))
	for i in n:
		var cell := _free_cell(6, _half_n - 2, fp)
		if cell.x < 0:
			continue
		_claim(cell, fp)
		var hcells: Array = []
		for ox in range(-fp / 2, fp / 2 + 1):  # дома блокируют обзор (туман войны)
			for oz in range(-fp / 2, fp / 2 + 1):
				var hc := Vector2i(cell.x + ox, cell.y + oz)
				_blocks_sight[_key(hc)] = true
				hcells.append(hc)
		var model: String = HOUSE_MODELS[_rng.randi() % HOUSE_MODELS.size()]
		var pal: String = HOUSE_PALETTES[_rng.randi() % HOUSE_PALETTES.size()]
		var hnode := _place(B + model, gw(cell.x, cell.y), _rng.randf() * 360.0, 2.9 * k + 0.7, pal)
		# подгонка: модель не должна визуально вылезать за занятые клетки (иначе «сквозь стены»)
		var hb := AABB()
		var hfirst := true
		for mi in hnode.find_children("*", "MeshInstance3D", true, false):
			var mt: Transform3D = hnode.global_transform.affine_inverse() * mi.global_transform
			var mb: AABB = mt * mi.get_aabb()
			hb = mb if hfirst else hb.merge(mb)
			hfirst = false
		if not hfirst:
			var hw: float = maxf(hb.size.x, hb.size.z)
			var target := (fp + 1) * CELL * 0.92
			if hw > target:
				hnode.scale *= target / hw
		var tints := [Color(0.55, 0.33, 0.24), Color(0.42, 0.46, 0.54), Color(0.60, 0.52, 0.38), Color(0.36, 0.44, 0.32)]
		_paint_house(hnode, tints[_rng.randi() % tints.size()])
		_add_house_windows(hnode)
		# дверь — «от границы»: сторона с наибольшим запасом свободного места до края карты
		var door := Vector2i(-1, -1)
		var half := fp / 2 + 1
		var cands := [Vector2i(cell.x, cell.y + half), Vector2i(cell.x, cell.y - half),
			Vector2i(cell.x + half, cell.y), Vector2i(cell.x - half, cell.y)]
		cands.sort_custom(func(p7, q7):
			var dp := mini(mini(p7.x, p7.y), mini(_grid_n - 1 - p7.x, _grid_n - 1 - p7.y))
			var dq := mini(mini(q7.x, q7.y), mini(_grid_n - 1 - q7.x, _grid_n - 1 - q7.y))
			return dp > dq)
		for cand in cands:
			if cand.x < 0 or cand.y < 0 or cand.x >= _grid_n or cand.y >= _grid_n:
				continue
			if _occupied.has(_key(cand)):
				continue
			door = cand
			break
		var hid := _houses.size()
		for hc2 in hcells:
			_house_at[_key(hc2)] = hid
		_houses.append({"cells": hcells, "door": door, "node": hnode, "faded": false})
		if door.x >= 0:
			var dpad := MeshInstance3D.new()
			var dcyl := CylinderMesh.new()
			dcyl.top_radius = 0.4
			dcyl.bottom_radius = 0.4
			dcyl.height = 0.04
			dpad.mesh = dcyl
			dpad.material_override = _mat(Color.BLACK, 0.0, 1.0, Color(1.0, 0.6, 0.15), 3.0)
			dpad.position = gw(door.x, door.y, 0.03)
			add_child(dpad)

func _house_of(c: Vector2i) -> int:
	# id дома, которому принадлежит клетка; дверь считается частью дома
	var k := _key(c)
	if _house_at.has(k):
		return int(_house_at[k])
	for hi in _houses.size():
		if _houses[hi].door == c:
			return hi
	return -1

func _can_enter(from: Vector2i, to: Vector2i) -> bool:
	# внутрь дома — только через дверь или из другой клетки того же дома
	var hk := _key(to)
	if not _house_at.has(hk):
		return true
	var h: int = _house_at[hk]
	if _house_at.get(_key(from), -1) == h:
		return true
	return from == _houses[h].door

func _update_house_fade() -> void:
	# дом с бойцом внутри становится полупрозрачным
	for hi in _houses.size():
		var h = _houses[hi]
		var inside := false
		for f in _fighters:
			if f.alive and _house_at.get(_key(f.cell), -1) == hi:
				inside = true
				break
		if inside != h.faded:
			h.faded = inside
			var tr: float = 0.7 if inside else 0.0
			for mi in h.node.find_children("*", "MeshInstance3D", true, false):
				mi.transparency = tr

func _generate_covers() -> void:
	var k: float = _grid_n / 40.0
	var n := maxi(3, int((_rng.randi_range(10, 13) if _biome == 0 else _rng.randi_range(12, 15)) * k))
	var pool: Array = COVER_MODELS if _biome == 0 else COVER_MODELS + ["Platform_2x2.gltf", "Platform_2x2.gltf", "AC_Stacked.gltf"]
	for i in n:
		var cell := _free_cell(4, _half_n - 1, 2)
		if cell.x < 0:
			continue
		_claim(cell, 2)
		var model: String = pool[_rng.randi() % pool.size()]
		var scl := 1.3 if model == "Platform_2x2.gltf" else 1.2
		var heavy: bool = model == "AC_Stacked.gltf" or model == "Platform_2x2.gltf"
		# тяжёлые укрытия блокируют обзор и огонь, лёгкие — только снижают шанс
		var ccells: Array = []
		for ox in range(-1, 2):
			for oz in range(-1, 2):
				var cc3 := Vector2i(cell.x + ox, cell.y + oz)
				ccells.append(cc3)
				if heavy:
					_blocks_sight[_key(cc3)] = true
		if not heavy:
			_soft_cover[_key(cell)] = true
		var cnode := _place(C + model, gw(cell.x, cell.y), _rng.randf() * 360.0, scl)
		# разрушаемость: тяжёлые держат 3 взрыва, лёгкие — 2
		var ck := _key(cell)
		_covers[ck] = {"hp": 90 if heavy else 40, "cells": ccells, "node": cnode, "heavy": heavy}
		for cc4 in ccells:
			_cover_at[_key(cc4)] = ck
	# деревья — лёгкое укрытие (hp 2); в индустриалке почти нет
	for i in maxi(1 if _biome == 1 else 2, int((_rng.randi_range(1, 2) if _biome == 1 else _rng.randi_range(6, 9)) * k)):
		var tc := _free_cell(3, _half_n, 1)
		if tc.x < 0:
			continue
		_claim(tc, 1)
		_soft_cover[_key(tc)] = true
		var tnode := _make_tree(gw(tc.x, tc.y))
		_covers[_key(tc)] = {"hp": 30, "cells": [tc], "node": tnode, "heavy": false}
		_cover_at[_key(tc)] = _key(tc)
	# валуны — тяжёлое укрытие (hp 4), блокируют обзор
	for i in maxi(2, int(_rng.randi_range(3, 5) * k)):
		var rc := _free_cell(3, _half_n, 1)
		if rc.x < 0:
			continue
		_claim(rc, 1)
		_blocks_sight[_key(rc)] = true
		var rnode := _make_rock(gw(rc.x, rc.y))
		_covers[_key(rc)] = {"hp": 80, "cells": [rc], "node": rnode, "heavy": true}
		_cover_at[_key(rc)] = _key(rc)
	# бочки с топливом — взрываются (hp 1), урон 20 вокруг; в индустриалке вдвое больше
	for i in maxi(2, int((_rng.randi_range(6, 9) if _biome == 1 else _rng.randi_range(3, 5)) * k)):
		var bc := _free_cell(3, _half_n, 1)
		if bc.x < 0:
			continue
		_claim(bc, 1)
		var bnode := _make_barrel(gw(bc.x, bc.y))
		_covers[_key(bc)] = {"hp": 27, "cells": [bc], "node": bnode, "heavy": false, "barrel": true}
		_cover_at[_key(bc)] = _key(bc)
	# трубы — индустриальный биом: лёгкое укрытие (прочность 50)
	if _biome == 1:
		for i in maxi(2, int(_rng.randi_range(4, 6) * k)):
			var pc2 := _free_cell(3, _half_n, 1)
			if pc2.x < 0:
				continue
			_claim(pc2, 1)
			_soft_cover[_key(pc2)] = true
			var pnode := _make_pipe(gw(pc2.x, pc2.y))
			_covers[_key(pc2)] = {"hp": 50, "cells": [pc2], "node": pnode, "heavy": false, "kind": "pipe"}
			_cover_at[_key(pc2)] = _key(pc2)

func _cover_name(rec) -> String:
	if rec.get("barrel", false):
		return "Бочка"
	if bool(rec.get("heavy", false)):
		return "Валун" if rec["cells"].size() == 1 else "Тяжёлое укрытие"
	if str(rec.get("kind", "")) == "pipe":
		return "Труба"
	return "Дерево" if rec["cells"].size() == 1 else "Укрытие"

func _damage_cover_hit(ck: String, dmg: int, src: String, att_idx := -1) -> void:
	# урон по объекту; бочке нужно ДВА попадания (талант «Сапёр» — одно, взрыв +25%)
	var rec = _covers.get(ck)
	if rec == null:
		return
	var sapper := att_idx >= 0 and att_idx < _fighters.size() and _tal(_fighters[att_idx], "sapper") > 0
	rec["hits"] = int(rec.get("hits", 0)) + 1
	rec.hp = int(rec.hp) - dmg
	var cname := _cover_name(rec)
	if int(rec.hp) <= 0:
		if rec.get("barrel", false) and int(rec["hits"]) < 2 and not sapper:
			rec.hp = 1
			_log("%s -> %s: пробита (%d урона), но не взорвалась — нужно ещё попадание!" % [src, cname, dmg])
			return
		_destroy_cover(ck, 1.25 if sapper else 1.0)
	else:
		_log("%s -> %s: %d урона (прочность %d)" % [src, cname, dmg, int(rec.hp)])

func _shoot_cover(att: int, cell: Vector2i) -> void:
	# клик по объекту (бочка/дерево/валун/укрытие) — стреляем по нему
	var a = _fighters[att]
	var w: Dictionary = a.weapon
	var cost := _shot_cost(a, w)
	var k := _key(cell)
	if not _cover_at.has(k):
		return
	var ck: String = _cover_at[k]
	var rec = _covers.get(ck)
	if rec == null:
		return
	var cname := _cover_name(rec)
	var dist := Vector2(a.cell.x - cell.x, a.cell.y - cell.y).length()
	if dist > w.get("range", 1):
		_log("%s вне дальности (%d > %d)" % [cname, int(dist), w.get("range", 1)])
		return
	if a.ap < cost:
		_log("Не хватает AP (%d < %d)" % [a.ap, cost])
		return
	var burst: int = w.get("burst", 1)
	if w.has("ammo") and a.ammo < burst:
		_log("Нет патронов — перезарядка [R]")
		return
	var aoe2: int = w.get("aoe", 0)
	if aoe2 == 0 and not _los(a.cell, cell):
		_log("Нет линии огня — объект за препятствием")
		return
	a.ap -= cost
	if w.has("ammo"):
		a.ammo -= burst
	_face_cell(a, cell)
	_sfx_play("shot")
	if aoe2 > 0:
		_explode_at(cell, aoe2)
		if w.get("burn", false):
			_ignite(cell, aoe2)
		if w.get("consumable", false):
			_spend_consumable(att)
		return
	# объект не уворачивается: урон = урон ствола × очередь
	var dmg: int = w.get("damage", 10) * burst
	_damage_cover_hit(ck, dmg, a.name, att)

func _destroy_cover(ck: String, mul := 1.0) -> void:
	var rec = _covers.get(ck)
	if rec == null:
		return
	for cc5 in rec.cells:
		var kk5 := _key(cc5)
		_occupied.erase(kk5)
		_blocks_sight.erase(kk5)
		_soft_cover.erase(kk5)
		_cover_at.erase(kk5)
	_spawn_burst(rec.node.position + Vector3(0, 0.5, 0), Color(0.6, 0.55, 0.5))
	rec.node.queue_free()
	_covers.erase(ck)
	if rec.get("barrel", false):
		_log("Бочка взорвалась!")
		_explode_barrel(rec.cells[0], mul)
	else:
		_log("%s разрушено!" % _cover_name(rec))

# ---------- огонь (Молотов / зажигательная граната) ----------
func _make_flame(c: Vector2i) -> Node3D:
	var root := Node3D.new()
	root.position = gw(c.x, c.y)
	var fl := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.22
	sm.height = 0.5
	fl.mesh = sm
	fl.material_override = _mat(Color(1.0, 0.45, 0.05), 0.0, 1.0, Color(1.0, 0.5, 0.05), 4.0)
	fl.position = Vector3(0, 0.25, 0)
	root.add_child(fl)
	var l := OmniLight3D.new()
	l.light_color = Color(1.0, 0.55, 0.15)
	l.light_energy = 2.5
	l.omni_range = 4.0
	l.position = Vector3(0, 0.8, 0)
	root.add_child(l)
	add_child(root)
	return root

func _ignite(cell: Vector2i, radius: int) -> void:
	for dx in range(-radius, radius + 1):
		for dz in range(-radius, radius + 1):
			var cf := Vector2i(cell.x + dx, cell.y + dz)
			if cf.x < 0 or cf.y < 0 or cf.x >= _grid_n or cf.y >= _grid_n:
				continue
			if _house_at.has(_key(cf)):
				continue
			_fire[cf] = 3
			if not _fire_nodes.has(cf):
				_fire_nodes[cf] = _make_flame(cf)
	_log("Поджог! Огонь горит 3 раунда и жжёт стоящих (-8 HP)")

func _tick_fire() -> void:
	if _fire.is_empty():
		return
	var expired: Array = []
	for c in _fire.keys():
		var sk := _key(c)
		if _unit_at.has(sk):
			var vi: int = _unit_at[sk]
			_apply_damage(vi, 8, "Огонь", -1)
			if _game_over:
				return
		_fire[c] = int(_fire[c]) - 1
		if int(_fire[c]) <= 0:
			expired.append(c)
	for c2 in expired:
		_fire.erase(c2)
		if _fire_nodes.has(c2):
			_fire_nodes[c2].queue_free()
			_fire_nodes.erase(c2)
func _damage_covers(cell: Vector2i, radius: int) -> void:
	# взрыв бьёт по укрытиям в радиусе; у каждого укрытия есть прочность
	var done := {}
	for dx in range(-radius, radius + 1):
		for dz in range(-radius, radius + 1):
			var c2 := Vector2i(cell.x + dx, cell.y + dz)
			var kk6 := _key(c2)
			if _cover_at.has(kk6) and not done.has(_cover_at[kk6]):
				var ck2: String = _cover_at[kk6]
				done[ck2] = true
				_damage_cover_hit(ck2, 25, "Взрыв")

var _plaster_tex: Texture2D = null
func _paint_house(node: Node3D, col: Color) -> void:
	# штукатурка: тинт + бесшовная текстура в трипланарной проекции (без полос атласа)
	if _plaster_tex == null and ResourceLoader.exists("res://assets/tiles/plaster.png"):
		_plaster_tex = load("res://assets/tiles/plaster.png")
	var m := _mat(col, 0.0, 0.92)
	if _plaster_tex != null:
		m.albedo_texture = _plaster_tex
		m.uv1_triplanar = true
		m.uv1_scale = Vector3(0.22, 0.22, 0.22)
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = null
		for si in mi.mesh.get_surface_count():
			mi.set_surface_override_material(si, m)

func _make_tree(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	root.position = pos
	var trunk := MeshInstance3D.new()
	var tcyl := CylinderMesh.new()
	tcyl.top_radius = 0.07
	tcyl.bottom_radius = 0.11
	tcyl.height = 0.7
	trunk.mesh = tcyl
	trunk.material_override = _mat(Color(0.30, 0.22, 0.14), 0.0, 0.95)
	trunk.position.y = 0.35
	root.add_child(trunk)
	var leaf_mat := _mat(Color(0.16, 0.30, 0.14), 0.0, 0.9)
	var s1 := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.42
	sph.height = 0.84
	s1.mesh = sph
	s1.material_override = leaf_mat
	s1.position.y = 0.95
	root.add_child(s1)
	var s2 := MeshInstance3D.new()
	var sph2 := SphereMesh.new()
	sph2.radius = 0.28
	sph2.height = 0.56
	s2.mesh = sph2
	s2.material_override = leaf_mat
	s2.position = Vector3(0.12, 1.3, -0.08)
	root.add_child(s2)
	add_child(root)
	return root

func _make_rock(pos: Vector3) -> Node3D:
	var rock := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.55
	sph.height = 1.1
	rock.mesh = sph
	rock.material_override = _mat(Color(0.42, 0.42, 0.44), 0.0, 1.0)
	rock.scale = Vector3(1.0, 0.85, 0.85)
	rock.rotation_degrees.y = _rng.randf() * 360.0
	rock.position = pos + Vector3(0, 0.25, 0)
	add_child(rock)
	return rock

func _make_barrel(pos: Vector3) -> Node3D:
	var b := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.26
	cyl.bottom_radius = 0.26
	cyl.height = 0.72
	b.mesh = cyl
	b.material_override = _mat(Color(0.55, 0.12, 0.08), 0.35, 0.5)
	b.position = pos + Vector3(0, 0.36, 0)
	add_child(b)
	return b

func _make_pipe(pos: Vector3) -> Node3D:
	# горизонтальная труба на опорах — индустриальный декор-укрытие
	var g := Node3D.new()
	var body := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.28
	cyl.bottom_radius = 0.28
	cyl.height = 1.7
	body.mesh = cyl
	body.material_override = _mat(Color(0.42, 0.30, 0.18), 0.7, 0.45)  # ржавый металл
	body.rotation_degrees.z = 90.0
	body.position.y = 0.32
	g.add_child(body)
	var flange := MeshInstance3D.new()
	var fm := CylinderMesh.new()
	fm.top_radius = 0.34
	fm.bottom_radius = 0.34
	fm.height = 0.12
	flange.mesh = fm
	flange.material_override = _mat(Color(0.30, 0.22, 0.14), 0.7, 0.5)
	flange.rotation_degrees.z = 90.0
	flange.position = Vector3(0.6, 0.32, 0)
	g.add_child(flange)
	for sx in [-0.5, 0.5]:
		var leg := MeshInstance3D.new()
		var lm := BoxMesh.new()
		lm.size = Vector3(0.12, 0.2, 0.12)
		leg.mesh = lm
		leg.material_override = _mat(Color(0.16, 0.15, 0.14), 0.4, 0.7)
		leg.position = Vector3(sx, 0.1, 0)
		g.add_child(leg)
	g.position = pos
	g.rotation_degrees.y = _rng.randf() * 360.0
	add_child(g)
	return g

func _explode_barrel(c: Vector2i, mul := 1.0) -> void:
	# бочка взрывается: урон 20 (x mul у сапёра) по своей и соседним клеткам, цепная реакция
	_explode_at(c, 1)
	for vi in _fighters.size():
		var v = _fighters[vi]
		if not v.alive:
			continue
		if maxi(absi(v.cell.x - c.x), absi(v.cell.y - c.y)) <= 1:
			_apply_damage(vi, int(20 * mul), "Бочка", -1)
			if _game_over:
				return

# ---------------- ЛУТ (items.json) ----------------
func _roll_chest_contents() -> Array:
	# В ящике НЕСКОЛЬКО предметов, содержимое скрыто до вскрытия:
	# оружие — всегда; броня — 60%; расходник — всегда, второй — 30%
	var contents := []
	var w: Array = _items["weapons"]
	contents.append({"kind": "weapon", "item": w[_rng.randi() % w.size()]})
	if _rng.randf() < 0.60:
		var cat: String = ["helmets", "body", "pants"][_rng.randi() % 3]
		var a: Array = _items["armor"][cat]
		contents.append({"kind": "armor", "cat": cat, "item": a[_rng.randi() % a.size()]})
	var c: Array = _items["consumables"]
	contents.append({"kind": "consumable", "item": c[_rng.randi() % c.size()]})
	if _rng.randf() < 0.30:
		contents.append({"kind": "consumable", "item": c[_rng.randi() % c.size()]})
	return contents

func _generate_loot() -> void:
	var pad_mat := _mat(Color.BLACK, 0.0, 1.0, Color(1.0, 0.8, 0.2), 3.0)
	var report := []
	# 2 ящика гарантированно на подиуме, остальные — рандомно
	var cc := _grid_n / 2
	var cells: Array[Vector2i] = [Vector2i(cc, cc - 2), Vector2i(cc, cc + 2)]
	for i in maxi(3, int(_rng.randi_range(7, 9) * (_grid_n / 40.0))):
		var cell := _free_cell(5, _half_n - 1, 1)
		if cell.x >= 0:
			_claim(cell, 1)
			cells.append(cell)
	for cell in cells:
		_claim(cell, 1)
		_place(C + "Lootbox.gltf", gw(cell.x, cell.y), _rng.randf() * 360.0, 1.0)
		var pad := MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.55
		cyl.bottom_radius = 0.55
		cyl.height = 0.04
		pad.mesh = cyl
		pad.material_override = pad_mat
		pad.position = gw(cell.x, cell.y, 0.03)
		add_child(pad)
		# содержимое ящика — скрыто: визуально все ящики одинаковые
		var key := "%d,%d" % [cell.x, cell.y]
		_chest_pads[key] = pad
		var contents := _roll_chest_contents()
		_chests[key] = contents
		var names := []
		for it in contents:
			names.append(it["item"].get("name", "?"))
		report.append("%s -> %d предм.: %s" % [cell, contents.size(), ", ".join(names)])
	# аптечки на подиуме
	_place(C + "Pickup_Health.gltf", gw(cc - 2, cc, 0.4), 0, 1.0)
	_place(C + "Pickup_Health.gltf", gw(cc + 2, cc, 0.4), 0, 1.0)
	print("LOOT_REPORT seed=", _rng.seed)
	for r in report:
		print("  ", r)

# ---------------- ПЕРИМЕТР ----------------
func _build_perimeter() -> void:
	var o := _size_n / 2.0 + 1.6
	_place(C + "Sign_1.gltf", Vector3(-o, 0, -8), 90)
	_place(C + "Sign_2.gltf", Vector3(o, 0, 8), -90)
	_place(C + "Sign_Hazard.gltf", Vector3(-6, 0, -o), 0)
	_place(C + "Sign_Hazard.gltf", Vector3(8, 0, o), 180)
	_place(C + "TV_2.gltf", Vector3(o, 0, -12), -110)
	_place(C + "TV_1.gltf", Vector3(-o, 0, 12), 70)
	_place(C + "TV_3.gltf", Vector3(14, 0, -o), 20)
	_place(C + "Antenna_1.gltf", Vector3(-o, 0, -o))
	_place(C + "Antenna_1.gltf", Vector3(o, 0, o), 180)
	_place(C + "Light_Street_1.gltf", Vector3(-o, 0, 0), 90, 1.3)
	_place(C + "Light_Street_1.gltf", Vector3(o, 0, 0), -90, 1.3)

var _bar_texture: Texture2D = null
func _bar_tex() -> Texture2D:
	if _bar_texture == null:
		var img := Image.create(8, 8, false, Image.FORMAT_RGBA8)
		img.fill(Color.WHITE)
		_bar_texture = ImageTexture.create_from_image(img)
	return _bar_texture

# ---------------- БОЙЦЫ 4v4 ----------------
func _spawn_teams() -> void:
	# RED (0) — отряд игрока (ники и статы из профиля), BLUE (1) — боты
	var red_models := [["Character_Soldier", "AK"], ["Character_Soldier", "Shotgun"],
		["Character_Hazmat", "SMG"], ["Character_Enemy", "Sniper"]]
	var blue_models := [["Character_Soldier", "AK", "Ворон"], ["Character_Hazmat", "SMG", "Клык"],
		["Character_Soldier", "Shotgun", "Гром"], ["Character_Enemy", "Sniper", "Лёд"]]
	# RED — юго-западный сектор, BLUE — северо-восточный; число бойцов = режим
	var lo := 2
	var hi := _grid_n - 3
	var mid := _grid_n / 2
	for i in _mode:
		var cell := _free_cell_sector(lo, mid - 4, mid + 4, hi)
		_spawn_human(red_models[i][0], cell.x, cell.y, _rng.randf_range(-30, 90),
			red_models[i][1], Color("#ff4757"), 0, _profile.names[i], _profile.stats[i], _profile.lvl[i], _profile.xp[i],
			_profile.talents[i], int(_profile.tpts[i]), _profile.prof[i])
	for i in _mode:
		var m = blue_models[i]
		var cell := _free_cell_sector(mid + 4, hi, lo, mid - 4)
		_spawn_human(m[0], cell.x, cell.y, _rng.randf_range(90, 210), m[1], Color("#3498ff"), 1, m[2])

func _free_cell_sector(x0: int, x1: int, z0: int, z1: int) -> Vector2i:
	for attempt in 40:
		var gx := _rng.randi_range(x0, x1)
		var gz := _rng.randi_range(z0, z1)
		var key := "%d,%d" % [gx, gz]
		if not _occupied.has(key) and not _unit_at.has(key):
			return Vector2i(gx, gz)
	return Vector2i(x0, z0)

func _weapon_by_id(wid: String) -> Dictionary:
	for w in _items["weapons"]:
		if w["id"] == wid:
			return w
	return {}

func _spawn_human(model: String, gx: int, gz: int, rot_y: float, weapon: String, team: Color, team_idx: int, fname: String, st: Dictionary = {}, lvl := 1, xp := 0, talents: Dictionary = {}, tpts := 0, prof: Dictionary = {}) -> void:
	if st.is_empty():
		st = _default_fighter_stats()
	var p: Node3D = _place(H + model + ".gltf", gw(gx, gz), rot_y, HUMAN_SCALE)
	for wn in WEAPON_NODES:
		var w := p.find_child(wn, true, false)
		if w and w is Node3D:
			w.visible = (wn == weapon)
	_teleport_in(p, Vector2i(gx, gz))
	var pad := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.45
	cyl.bottom_radius = 0.45
	cyl.height = 0.03
	pad.mesh = cyl
	pad.material_override = _mat(Color.BLACK, 0.0, 1.0, team, 2.5)
	pad.position = gw(gx, gz, 0.02)
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
	p.add_child(hp_fg)
	var ap := p.find_child("AnimationPlayer", true, false)
	if ap and ap.has_animation("Idle_Shoot"):
		ap.play("Idle_Shoot")
	elif ap and ap.has_animation("Idle"):
		ap.play("Idle")
	# регистрация бойца в игровом состоянии (характеристики — из очков навыков профиля)
	var gun := _weapon_by_id(weapon)
	var hp_max := _stat_hp(st) + 3 * (lvl - 1)
	var ap_max := _stat_ap(st) + mini(3, lvl / 3)
	var pts0 := _stat_points_left(st, lvl)
	_fighters.append({
		"node": p, "pad": pad, "cell": Vector2i(gx, gz), "team": team_idx, "name": fname,
		"model": model, "stats": st,
		"hp": hp_max, "max_hp": hp_max, "ap": ap_max, "max_ap": ap_max,
		"carry_base": _stat_carry(st) + 0.5 * (lvl - 1), "vision": _stat_vision(st),
		"gun": gun, "weapon": gun, "ammo": gun.get("ammo", 0), "spare": gun.get("spare", -1),
		"melee": _items["melee_fixed"],
		"armor": {"helmets": null, "body": null, "pants": null},
		"backpack": [], "alive": true,
		"lvl": lvl, "xp": xp, "kills": 0, "pts": pts0, "dmg": 0,
		"talents": talents.duplicate(), "tpts": tpts, "prof": prof.duplicate(),
		"aggro_to": -1, "aggro_ttl": 0,
		"hp_fg": hp_fg, "hp_bg": hp_bg
	})
	_unit_at["%d,%d" % [gx, gz]] = _fighters.size() - 1

# ---------------- ШОУ: могилы, насмешки, граффити, телепорты ----------------
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
	var pool := _taunt_lines()
	var line: String = pool[_rng.randi() % pool.size()]
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
	var moon := DirectionalLight3D.new()
	moon.light_color = Color(0.55, 0.65, 0.9)
	moon.light_energy = 0.9
	moon.shadow_enabled = true
	moon.directional_shadow_max_distance = 120.0
	moon.rotation_degrees = Vector3(-60, 30, 0)
	add_child(moon)
	var half := _size_n / 2.0 - 2.0
	var corners := [Vector3(-half, 9, -half), Vector3(half, 9, -half), Vector3(-half, 9, half), Vector3(half, 9, half)]
	var hues := [Color(1.0, 0.75, 0.45), Color(0.45, 0.8, 1.0), Color(0.45, 0.8, 1.0), Color(1.0, 0.75, 0.45)]
	for i in corners.size():
		var sp := SpotLight3D.new()
		sp.position = corners[i]
		sp.light_color = hues[i]
		sp.light_energy = 8.0
		sp.spot_range = 70.0
		sp.spot_angle = 55.0
		sp.spot_attenuation = 0.8
		sp.shadow_enabled = true
		add_child(sp)
		sp.look_at(Vector3.ZERO, Vector3.UP)
	var center_spot := SpotLight3D.new()
	center_spot.position = Vector3(0, 14, 0)
	center_spot.light_color = Color(1.0, 0.9, 0.75)
	center_spot.light_energy = 10.0
	center_spot.spot_range = 30.0
	center_spot.spot_angle = 32.0
	center_spot.shadow_enabled = true
	add_child(center_spot)
	center_spot.look_at(Vector3.ZERO, Vector3(0, 0, -1))
	var omni := OmniLight3D.new()
	omni.position = Vector3(0, 5, 0)
	omni.light_color = Color(0.2, 0.7, 0.9)
	omni.light_energy = 1.0
	omni.omni_range = 35.0
	add_child(omni)
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.008, 0.01, 0.02)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.13, 0.13, 0.16)
	env.ambient_light_energy = 0.75
	env.tonemap_mode = Environment.TONE_MAPPER_ACES
	env.glow_enabled = true
	env.glow_intensity = 0.45
	env.glow_bloom = 0.1
	env.fog_enabled = true
	env.fog_light_color = Color(0.02, 0.03, 0.06)
	env.fog_density = 0.005
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	_gfx = {"moon": moon, "env": env, "spots": []}
	for c in get_children():
		if c is SpotLight3D:
			_gfx.spots.append(c)

func _apply_graphics(level: int) -> void:
	# 0 — низкая, 1 — средняя, 2 — высокая
	_settings.graphics = level
	var moon: DirectionalLight3D = _gfx.get("moon")
	var env: Environment = _gfx.get("env")
	if moon == null or env == null:
		return
	moon.shadow_enabled = level >= 1
	for sp in _gfx.spots:
		sp.shadow_enabled = level >= 2
	env.glow_enabled = level >= 1
	env.fog_enabled = level >= 2

func _setup_camera() -> void:
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_PERSPECTIVE
	cam.fov = 34.0
	cam.position = Vector3(36, 38, 36)
	add_child(cam)
	_cam = cam
	_cam_dist = _size_n * 1.35
	if OS.get_cmdline_user_args().has("--closeup"):
		cam.position = gw(20, 26, 3.0) + Vector3(3.2, 1.5, 3.2)
		cam.fov = 40.0
		cam.look_at(gw(20, 20, 1.0), Vector3.UP)
		cam.make_current()
		return
	# начальные углы из стартовой позиции (36, 38, 36)
	_cam_yaw = rad_to_deg(atan2(36.0, 36.0))
	var hd: float = Vector2(36, 36).length()
	_cam_pitch = rad_to_deg(atan2(38.0, hd))
	_update_camera()

func _update_camera() -> void:
	if _cam == null:
		return
	var yr := deg_to_rad(_cam_yaw)
	var pr := deg_to_rad(_cam_pitch)
	var center := _cam_target
	var off := Vector3(sin(yr) * cos(pr), sin(pr), cos(yr) * cos(pr)) * _cam_dist
	_cam.position = center + off
	_cam.look_at(center, Vector3.UP)
	_cam.make_current()

func _orbit(dyaw: float, dpitch: float) -> void:
	_cam_yaw = fmod(_cam_yaw + dyaw + 360.0, 360.0)
	_cam_pitch = clampf(_cam_pitch + dpitch, CAM_PITCH_MIN, CAM_PITCH_MAX)
	_update_camera()

func _pan_camera(rel: Vector2) -> void:
	if _cam == null:
		return
	var yr := deg_to_rad(_cam_yaw)
	var right := Vector3(cos(yr), 0, -sin(yr))
	var fwd := Vector3(-sin(yr), 0, -cos(yr))
	var k := _cam_dist * 0.0016
	_cam_target += (-right * rel.x + fwd * rel.y) * k
	var lim := _size_n * 0.45
	_cam_target.x = clampf(_cam_target.x, -lim, lim)
	_cam_target.z = clampf(_cam_target.z, -lim, lim)
	_update_camera()

func _mouse_pos() -> Vector2:
	if _override_mouse.x >= 0.0:
		return _override_mouse
	return get_viewport().get_mouse_position()

func _click_left_at(pos: Vector2) -> void:
	_override_mouse = pos
	_click_left()
	_override_mouse = Vector2(-1, -1)
func _zoom(delta: float) -> void:
	if _cam == null:
		return
	_cam_dist = clampf(_cam_dist + delta, CAM_MIN, CAM_MAX)
	_update_camera()

func _process(delta: float) -> void:
	if _onboard_pulse != null and is_instance_valid(_onboard_pulse):
		_pulse_t += delta
		var s := 0.75 + 0.25 * sin(_pulse_t * 6.0)
		_onboard_pulse.modulate = Color(s, s, 0.6 * s)
	# тряска камеры при взрывах (через смещения, не трогая орбиту)
	if _cam == null:
		return
	if _shake > 0.0:
		_shake = maxf(0.0, _shake - delta * 2.2)
		_cam.h_offset = _rng.randf_range(-_shake, _shake)
		_cam.v_offset = _rng.randf_range(-_shake, _shake)
	elif _cam.h_offset != 0.0 or _cam.v_offset != 0.0:
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
	_update_aim()
	_update_sel_marker()
	_update_edge_arrows()
	_pulse_end_btn()

# ---------- эффекты: взрыв и гибель ----------
func _spawn_burst(pos: Vector3, color: Color) -> void:
	var parts := GPUParticles3D.new()
	parts.amount = 28
	parts.lifetime = 0.7
	parts.one_shot = true
	parts.explosiveness = 1.0
	var pm := ParticleProcessMaterial.new()
	pm.direction = Vector3(0, 1, 0)
	pm.spread = 65.0
	pm.initial_velocity_min = 3.0
	pm.initial_velocity_max = 7.5
	pm.gravity = Vector3(0, -9.5, 0)
	pm.scale_min = 0.5
	pm.scale_max = 1.4
	parts.process_material = pm
	var bm := SphereMesh.new()
	bm.radius = 0.05
	bm.height = 0.1
	bm.material = _mat(Color.BLACK, 0.0, 1.0, color, 5.0)
	parts.draw_pass_1 = bm
	parts.position = pos
	add_child(parts)
	parts.emitting = true
	get_tree().create_timer(1.3).timeout.connect(parts.queue_free)

func _explode_at(cell: Vector2i, radius := 1) -> void:
	_damage_covers(cell, radius)
	var pos := gw(cell.x, cell.y, 0.7)
	_sfx_play("explosion")
	_shake = 0.55
	# вспышка света
	var flash := OmniLight3D.new()
	flash.position = pos + Vector3(0, 1.6, 0)
	flash.light_color = Color(1.0, 0.6, 0.2)
	flash.light_energy = 14.0
	flash.omni_range = 15.0
	add_child(flash)
	var tw := create_tween()
	tw.tween_property(flash, "light_energy", 0.0, 0.5)
	tw.finished.connect(flash.queue_free)
	# огненный шар: расширяется и гаснет
	var ball := MeshInstance3D.new()
	var sm := SphereMesh.new()
	sm.radius = 0.45
	sm.height = 0.9
	ball.mesh = sm
	ball.material_override = _mat(Color(0.2, 0.05, 0.0), 0.0, 1.0, Color(1.0, 0.45, 0.1), 9.0)
	ball.position = pos
	add_child(ball)
	var tw2 := create_tween()
	tw2.set_parallel(true)
	tw2.tween_property(ball, "scale", Vector3.ONE * 4.2, 0.32).set_trans(Tween.TRANS_CUBIC)
	tw2.tween_method(func(v: float):
		(ball.material_override as StandardMaterial3D).emission_energy_multiplier = v,
		9.0, 0.1, 0.55)
	tw2.finished.connect(ball.queue_free)
	_spawn_burst(pos, Color(1.0, 0.5, 0.15))

# ============================================================
# ---------------- ГЕЙМПЛЕЙ (v6) ----------------
# ============================================================

func _log(msg: String) -> void:
	_battle_log.append(msg)
	if _battle_log.size() > 60:
		_battle_log.pop_front()
	if _ui.has("chat_lines") and _chat_tab == 0:
		_render_chat()
	print("[GAME] ", msg)

# ---------- портреты бойцов (пресеты + свой аватар) ----------
func _preset_avatar(idx: int) -> Texture2D:
	# 6 пресетов: game/assets/ui/avatars/av1..av6.png
	var n := (idx % 6) + 1
	var path := "res://assets/ui/avatars/av%d.png" % n
	if ResourceLoader.exists(path):
		return load(path)
	return null

func _fighter_portrait_tex(i: int) -> Texture2D:
	# слот 0 — аватар игрока (свой или выбранный пресет); остальным — пресеты
	if i == 0:
		var own: Texture2D = _avatar_texture()
		if own != null:
			return own
		return _preset_avatar(int(_profile.get("avatar_preset", 1)) - 1)
	return _preset_avatar(i)

# ---------- панель отряда ----------
func _select_from_squad(i: int) -> void:
	if _busy or _game_over or _menu_open:
		return
	if i < 0 or i >= _fighters.size():
		return
	var f = _fighters[i]
	if f.team != 0 or not f.alive:
		return
	_select(i)

func _refresh_squad() -> void:
	if not _ui.has("squad_rows"):
		return
	for i in mini(4, _ui.squad_rows.size()):
		var r: Dictionary = _ui.squad_rows[i]
		if i >= _fighters.size():
			r.row.visible = false
			continue
		r.row.visible = true
		var f = _fighters[i]
		var tex := _fighter_portrait_tex(i)
		if tex != null:
			r.portrait.texture = tex
		if not f.alive:
			r.name.text = "%s †" % f.name
			r.stats.text = "выбыл из шоу"
			r.row.modulate = Color(0.45, 0.45, 0.5)
		else:
			var mark := "► " if i == _selected else ""
			r.name.text = mark + f.name
			r.stats.text = "HP %d/%d · ОД %d/%d" % [f.hp, f.max_hp, f.ap, f.max_ap]
			r.row.modulate = Color(1, 1, 1)

func _key(c: Vector2i) -> String:
	return "%d,%d" % [c.x, c.y]

func _alive_count(team: int) -> int:
	var n := 0
	for f in _fighters:
		if f.alive and f.team == team:
			n += 1
	return n

func _defense(f: Dictionary) -> int:
	var d := 0
	for slot in ["helmets", "body", "pants"]:
		if f.armor[slot]:
			d += f.armor[slot].get("defense", 0)
	return d

func _carry_limit(f: Dictionary) -> float:
	var lim: float = f.get("carry_base", BASE_CARRY)
	for slot in ["helmets", "body", "pants"]:
		if f.armor[slot]:
			lim += f.armor[slot].get("carry_bonus", 0)
	return lim

func _item_weight(entry: Dictionary) -> float:
	match entry["kind"]:
		"weapon":
			return 3.0 if entry["item"].get("tier", 1) == 1 else 5.0
		"armor":
			return entry["item"].get("weight", 1.0)
		_:
			return 1.0

func _load_weight(f: Dictionary) -> float:
	# вес рюкзака: надетая на бойца экипировка веса НЕ занимает
	var w := 0.0
	for it in f.backpack:
		w += _item_weight(it)
	return w

# ---------- наведение мыши ----------
func _cell_under_mouse() -> Vector2i:
	var cam := get_viewport().get_camera_3d()
	var mp := _mouse_pos()
	var from := cam.project_ray_origin(mp)
	var dir := cam.project_ray_normal(mp)
	if absf(dir.y) < 0.001:
		return Vector2i(-1, -1)
	var t := -from.y / dir.y
	if t < 0:
		return Vector2i(-1, -1)
	var p := from + dir * t
	var c := Vector2i(roundi(p.x / CELL + _half_n), roundi(p.z / CELL + _half_n))
	if c.x < 0 or c.y < 0 or c.x >= _grid_n or c.y >= _grid_n:
		return Vector2i(-1, -1)
	return c

func _fighter_near_mouse() -> int:
	var cam := get_viewport().get_camera_3d()
	var mp := _mouse_pos()
	var from := cam.project_ray_origin(mp)
	var dir := cam.project_ray_normal(mp)
	var best := -1
	var best_d := 0.9
	for i in _fighters.size():
		var f = _fighters[i]
		if not f.alive:
			continue
		var c: Vector3 = f.node.position + Vector3(0, 0.9, 0)
		var t := (c - from).dot(dir)
		if t < 0:
			continue
		var d := (from + dir * t - c).length()
		if d < best_d:
			best_d = d
			best = i
	return best

# ---------- выбор бойца и подсветка ----------
func _select(i: int) -> void:
	if _onboard_step == 0 and _fighters[i].team == 0:
		_onboard_next()
	_selected = i
	_reach = _reachable(_fighters[i].cell, _fighters[i].ap)
	_show_reach()
	if _sel_ring == null:
		_sel_ring = MeshInstance3D.new()
		var cyl := CylinderMesh.new()
		cyl.top_radius = 0.62
		cyl.bottom_radius = 0.62
		cyl.height = 0.05
		_sel_ring.mesh = cyl
		_sel_ring.material_override = _mat(Color.BLACK, 0.0, 1.0, Color(0.5, 1.0, 0.6), 3.5)
		add_child(_sel_ring)
	_sel_ring.visible = true
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
	if _ui.has("chest_panel"):
		_ui.chest_panel.visible = false

func _deselect() -> void:
	_selected = -1
	_reach = {}
	_clear_hl()
	if _sel_ring:
		_sel_ring.visible = false
	if _sel_name:
		_sel_name.visible = false
	if _ui.has("fighter_panel"):
		_ui.fighter_panel.visible = false
		_ui.chest_panel.visible = false
		_ui.card.visible = false
		_ui.inv_panel.visible = false

func _reachable(from: Vector2i, ap: int) -> Dictionary:
	var res := {}
	var queue := [from]
	res[from] = 0
	while not queue.is_empty():
		var cur: Vector2i = queue.pop_front()
		var cost: int = res[cur]
		if cost >= ap:
			continue
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = cur + d
			if n.x < 0 or n.y < 0 or n.x >= _grid_n or n.y >= _grid_n:
				continue
			var k := _key(n)
			if _unit_at.has(k):
				continue
			if _occupied.has(k):
				if not _house_at.has(k) or not _can_enter(cur, n):
					continue
			if not res.has(n):
				res[n] = cost + 1
				queue.append(n)
	res.erase(from)
	return res

func _clear_hl() -> void:
	for h in _hl:
		h.queue_free()
	_hl.clear()

func _show_reach() -> void:
	_clear_hl()
	var mat := StandardMaterial3D.new()
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	mat.albedo_color = Color(0.2, 0.9, 1.0, 0.28)
	mat.emission_enabled = true
	mat.emission = Color(0.2, 0.9, 1.0)
	mat.emission_energy_multiplier = 0.6
	for cell in _reach:
		var q := MeshInstance3D.new()
		var bm := BoxMesh.new()
		bm.size = Vector3(CELL * 0.9, 0.03, CELL * 0.9)
		q.mesh = bm
		q.material_override = mat
		q.position = gw(cell.x, cell.y, 0.05)
		add_child(q)
		_hl.append(q)
		var cost_lbl := Label3D.new()
		cost_lbl.text = str(int(_reach[cell]))
		cost_lbl.font_size = 64
		cost_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		cost_lbl.no_depth_test = true
		cost_lbl.modulate = Color(1.0, 1.0, 1.0, 0.95)
		cost_lbl.outline_size = 12
		cost_lbl.outline_modulate = Color(0, 0, 0, 0.85)
		cost_lbl.position = gw(cell.x, cell.y, 0.4)
		add_child(cost_lbl)
		_hl.append(cost_lbl)

# ---------- перемещение ----------
func _face_cell(f: Dictionary, target: Vector2i) -> void:
	var to := gw(target.x, target.y, f.node.position.y)
	if f.node.position.distance_to(to) < 0.01:
		return
	f.node.look_at(to, Vector3.UP)
	f.node.rotate_y(PI)  # модели Quaternius смотрят в +Z

func _play_anim(f: Dictionary, anim: String) -> void:
	var ap = f.node.find_child("AnimationPlayer", true, false)
	if ap and ap.has_animation(anim):
		ap.play(anim)

func _path_to(from: Vector2i, to: Vector2i) -> Array:
	# восстановление пути по BFS-стоимостям _reach (от цели назад к старту)
	var path: Array = []
	var cur: Vector2i = to
	var guard := 0
	while cur != from and guard < 200:
		guard += 1
		var c: int = _reach.get(cur, -1)
		if c < 0:
			return [to]
		path.push_front(cur)
		if c == 1:
			return path
		var nxt := Vector2i(-1, -1)
		for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
			var n: Vector2i = cur + d
			if _reach.get(n, -1) == c - 1:
				nxt = n
				break
		if nxt.x < 0:
			return path
		cur = nxt
	return path

func _step_face(f: Dictionary, s: Vector2i) -> void:
	_face_cell(f, s)
	_sfx_play("step")

func _move_fighter(i: int, cell: Vector2i, path: Array = []) -> void:
	var f = _fighters[i]
	_unit_at.erase(_key(f.cell))
	f.cell = cell
	_unit_at[_key(cell)] = i
	_play_anim(f, "Run_Gun")
	if path.is_empty():
		path = [cell]
	var tw := create_tween()
	for step in path:
		var st: Vector2i = step
		tw.tween_callback(_step_face.bind(f, st))
		tw.tween_property(f.node, "position", gw(st.x, st.y), 0.22)
	var twp := create_tween()
	twp.tween_property(f.pad, "position", gw(cell.x, cell.y, 0.02), 0.22 * path.size())
	tw.finished.connect(func():
		if f.alive:
			_play_anim(f, "Idle_Shoot")
	)

# ---------- прицеливание: луч и шанс попадания при наведении ----------
func _hide_aim() -> void:
	if _aim_beam:
		_aim_beam.visible = false
	if _aim_lbl:
		_aim_lbl.visible = false
	_aim_target = -1

func _update_aim() -> void:
	var tgt := -1
	if _selected >= 0 and _selected < _fighters.size() and not _busy and not _game_over and not _menu_open and not _lvl_open:
		var a = _fighters[_selected]
		if a.alive:
			var h := _fighter_near_mouse()
			if h >= 0 and h != _selected and _fighters[h].alive and _fighters[h].team != a.team:
				tgt = h
	if tgt < 0:
		if _aim_target >= 0:
			_hide_aim()
		return
	_aim_target = tgt
	var a2 = _fighters[_selected]
	var d = _fighters[tgt]
	var w: Dictionary = a2.weapon
	var dist := Vector2(a2.cell.x - d.cell.x, a2.cell.y - d.cell.y).length()
	var rng_w: int = w.get("range", 1)
	var in_range: bool = dist <= rng_w
	var los_ok: bool = w.has("aoe") or _los(a2.cell, d.cell)
	var chance := clampf(_hit_chance(a2.cell, d.cell) + _stat_acc(a2.stats) - _stat_dodge(d.stats), 0.1, 0.95)
	var col := Color(0.35, 1.0, 0.45)
	var txt := "%d%%" % int(chance * 100)
	if not in_range:
		col = Color(1.0, 0.25, 0.25)
		txt = "ДАЛЕКО (%d > %d)" % [int(round(dist)), rng_w]
	elif not los_ok:
		col = Color(1.0, 0.25, 0.25)
		txt = "НЕТ ЛИНИИ ОГНЯ"
	elif chance < HIT_CHANCE + _stat_acc(a2.stats) - 0.001:
		col = Color(1.0, 0.85, 0.2)
		txt = "%d%% (укрытия)" % int(chance * 100)
	var p0: Vector3 = a2.node.position + Vector3(0, 1.15, 0)
	var p1: Vector3 = d.node.position + Vector3(0, 0.95, 0)
	if _aim_beam == null:
		_aim_beam = MeshInstance3D.new()
		_aim_beam.mesh = BoxMesh.new()
		_aim_beam.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(_aim_beam)
		_aim_lbl = Label3D.new()
		_aim_lbl.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_aim_lbl.font_size = 64
		_aim_lbl.outline_size = 14
		_aim_lbl.outline_modulate = Color(0, 0, 0, 0.9)
		_aim_lbl.no_depth_test = true
		add_child(_aim_lbl)
	var bm: BoxMesh = _aim_beam.mesh
	bm.size = Vector3(0.05, 0.05, maxf(0.1, p0.distance_to(p1)))
	if col != _aim_col:
		_aim_col = col
		_aim_beam.material_override = _mat(Color(col.r, col.g, col.b, 0.75), 0.0, 1.0, col, 2.5)
		_aim_lbl.modulate = col
	if _aim_lbl.text != txt:
		_aim_lbl.text = txt
	_aim_beam.visible = true
	_aim_beam.look_at_from_position((p0 + p1) * 0.5, p1, Vector3.UP)
	_aim_lbl.position = (p0 + p1) * 0.5 + Vector3(0, 0.55, 0)
	_aim_lbl.visible = true

# ---------- бой ----------
func _cover_on_line(a: Vector2i, b: Vector2i) -> int:
	# сколько лёгких укрытий на линии огня (каждое -15% к шансу попадания)
	var x0: int = a.x
	var y0: int = a.y
	var x1: int = b.x
	var y1: int = b.y
	var dx: int = absi(x1 - x0)
	var dy: int = -absi(y1 - y0)
	var sx: int = 1 if x0 < x1 else -1
	var sy: int = 1 if y0 < y1 else -1
	var err: int = dx + dy
	var x := x0
	var y := y0
	var n := 0
	while true:
		if x == x1 and y == y1:
			return n
		if not (x == x0 and y == y0) and _soft_cover.has("%d,%d" % [x, y]):
			n += 1
		var e2 := 2 * err
		if e2 >= dy:
			err += dy
			x += sx
		if e2 <= dx:
			err += dx
			y += sy
	return n

func _hit_chance(a: Vector2i, b: Vector2i) -> float:
	return clampf(HIT_CHANCE - 0.15 * _cover_on_line(a, b), 0.25, 0.95)

func _apply_damage(victim: int, dmg: int, src_name: String, src_idx := -1) -> int:
	var d = _fighters[victim]
	# броня срезает не больше 70% урона
	var real := maxi(maxi(1, dmg - _defense(d)), int(ceil(dmg * 0.3)))
	d.hp = maxi(0, d.hp - real)
	if src_idx >= 0 and src_idx < _fighters.size():
		_fighters[src_idx].dmg = int(_fighters[src_idx].get("dmg", 0)) + real
	_sfx_play("hit")
	var arm_txt := ""
	if dmg > real:
		arm_txt = " (броня -%d)" % (dmg - real)
	_log("%s -> %s: %d урона%s (HP %d)" % [src_name, d.name, real, arm_txt, d.hp])
	if d.hp <= 0:
		_kill(victim)
		if src_idx >= 0 and src_idx < _fighters.size():
			_fighters[src_idx].kills = int(_fighters[src_idx].kills) + 1
			_gain_xp(src_idx, 50)
	else:
		_spawn_burst(d.node.position + Vector3(0, 1.0, 0), Color(0.55, 0.05, 0.08))
	return real

func _shoot(att: int, def: int) -> void:
	var a = _fighters[att]
	var d = _fighters[def]
	var w: Dictionary = a.weapon
	var cost := _shot_cost(a, w)
	var dist := Vector2(a.cell.x - d.cell.x, a.cell.y - d.cell.y).length()
	if dist > w.get("range", 1):
		if a.team == 0:
			_log("Цель вне дальности (%d > %d)" % [int(dist), w.get("range", 1)])
		return
	if a.ap < cost:
		if a.team == 0:
			_log("Не хватает AP (%d < %d)" % [a.ap, cost])
		return
	var burst: int = w.get("burst", 1)
	if w.has("ammo") and a.ammo < burst:
		if a.team == 0:
			_log("Нет патронов — перезарядка [R]")
		return
	# линия огня: дома и тяжёлые укрытия блокируют выстрел (кроме AoE)
	if not w.has("aoe") and not _los(a.cell, d.cell):
		if a.team == 0:
			_log("Нет линии огня — цель за укрытием")
		return
	a.ap -= cost
	if w.has("ammo"):
		a.ammo -= burst
	_face_cell(a, d.cell)
	_sfx_play("shot")
	var aoe: int = w.get("aoe", 0)
	if aoe > 0:
		# площадной урон: все бойцы в радиусе aoe от клетки цели (дружественный огонь!)
		_explode_at(d.cell, aoe)
		_log("%s: %s — взрыв на площади!" % [a.name, w.get("name", "?")])
		var did := false
		var real_sum := 0
		for vi in _fighters.size():
			var v = _fighters[vi]
			if not v.alive or vi == att:
				continue
			var vd := Vector2(v.cell.x - d.cell.x, v.cell.y - d.cell.y).length()
			if vd <= aoe:
				# взрыв не мажет: полный урон в центре, 60% по краю радиуса
				var tot: int = w.get("damage", 10) * burst
				if vd > 0.5:
					tot = int(tot * 0.6)
				if tot > 0:
					did = true
					real_sum += _apply_damage(vi, tot, a.name, att)
		if did:
			_gain_xp(att, 25 + real_sum)
			var cls2 := _weapon_class(w)
			if cls2 != "":
				a.prof[cls2] = int(a.prof.get(cls2, 0)) + real_sum
		if w.get("burn", false):
			_ignite(d.cell, aoe)
		if w.get("consumable", false):
			_spend_consumable(att)
		return
	var cls := _weapon_class(w)
	var pl := _prof_lvl(a, cls)
	var chance := clampf(_hit_chance(a.cell, d.cell) + _stat_acc(a.stats) + 0.03 * pl - _stat_dodge(d.stats), 0.1, 0.95)
	var total := 0
	var crit := false
	for i in burst:
		if _rng.randf() < chance:
			var dm: int = int(w.get("damage", 10) * (1.0 + 0.03 * pl))
			if _rng.randf() < _stat_crit(a.stats) + 0.02 * _tal(a, "lucky"):
				dm = int(dm * 1.5)
				crit = true
			total += dm
	if total > 0:
		var real: int = _apply_damage(def, total, a.name, att)
		_gain_xp(att, 25 + real)
		if cls != "":
			a.prof[cls] = int(a.prof.get(cls, 0)) + real
		if crit:
			_log("КРИТ! x1.5 урона")
	else:
		var base: float = HIT_CHANCE + _stat_acc(a.stats)
		var cover_txt := " (шанс был %d%% — укрытия/уклонение)" % int(chance * 100) if chance < base - 0.001 else ""
		_log("%s -> %s: промах%s" % [a.name, d.name, cover_txt])

func _kill(i: int) -> void:
	var f = _fighters[i]
	f.alive = false
	_unit_at.erase(_key(f.cell))
	f.pad.material_override = _mat(Color(0.2, 0.2, 0.2), 0.0, 0.9)
	_play_anim(f, "Death")
	_sfx_play("death")
	_spawn_burst(f.node.position + Vector3(0, 0.8, 0), Color(0.75, 0.08, 0.12))
	# падение корпуса (поверх анимации Death — на корневой ноде)
	var tw := create_tween()
	tw.tween_property(f.node, "rotation_degrees:x", -72.0, 0.45).set_delay(0.15).set_trans(Tween.TRANS_BACK)
	tw.tween_property(f.node, "position:y", f.node.position.y - 0.15, 0.3)
	_log("%s выбыл из шоу!" % f.name)
	_spawn_grave(f)
	# трупный лут: рюкзак, броня и ствол погибшего остаются в ящике на клетке
	var drop: Array = []
	for it2 in f.backpack:
		drop.append(it2)
	for slot in ["helmets", "body", "pants"]:
		if f.armor[slot]:
			drop.append({"kind": "armor", "cat": slot, "item": f.armor[slot]})
	if not f.gun.is_empty():
		drop.append({"kind": "weapon", "item": f.gun})
	if not drop.is_empty():
		var ck3 := _key(f.cell)
		var contents: Array = _chests.get(ck3, [])
		for d2 in drop:
			contents.append(d2)
		_chests[ck3] = contents
		if not _chest_pads.has(ck3):
			_place(C + "Lootbox.gltf", gw(f.cell.x, f.cell.y), _rng.randf() * 360.0, 1.0)
			var pad2 := MeshInstance3D.new()
			var cyl2 := CylinderMesh.new()
			cyl2.top_radius = 0.55
			cyl2.bottom_radius = 0.55
			cyl2.height = 0.04
			pad2.mesh = cyl2
			pad2.material_override = _mat(Color.BLACK, 0.0, 1.0, Color(1.0, 0.8, 0.2), 3.0)
			pad2.position = gw(f.cell.x, f.cell.y, 0.03)
			add_child(pad2)
			_chest_pads[ck3] = pad2
		_log("Снаряжение %s осталось на земле" % f.name)
	if _selected == i:
		_deselect()
	_check_end()

# ---------- опыт и уровни ----------
var _lvl_open := false
var _lvl_wrap: CenterContainer = null

func _xp_need(lvl: int) -> int:
	return int(floor(100.0 * pow(1.35, lvl - 1)))

func _recalc_derived(f: Dictionary, heal := false) -> void:
	f.max_hp = _stat_hp(f.stats) + 3 * (int(f.lvl) - 1)
	f.max_ap = _stat_ap(f.stats) + mini(3, int(f.lvl) / 3) - _armor_ap_penalty(f) + _tal(f, "marathon")
	f.carry_base = _stat_carry(f.stats) + 0.5 * (int(f.lvl) - 1) + 2.0 * _tal(f, "mule")
	f.vision = _stat_vision(f.stats) + _tal(f, "scout")
	if heal:
		f.hp = f.max_hp
		f.ap = f.max_ap
	f.hp = mini(int(f.hp), int(f.max_hp))
	f.ap = mini(int(f.ap), int(f.max_ap))

func _gain_xp(i: int, amount: int) -> void:
	var f = _fighters[i]
	if not f.alive:
		return
	var bonus := 1.0 + 0.1 * int(f.stats.get("int", 0))
	f.xp = int(f.xp) + int(round(amount * bonus))
	var leveled := false
	while int(f.xp) >= _xp_need(int(f.lvl)):
		f.xp = int(f.xp) - _xp_need(int(f.lvl))
		f.lvl = int(f.lvl) + 1
		f.pts = int(f.pts) + (5 if int(f.lvl) <= 5 else 3)
		if int(f.lvl) % 3 == 0:
			f.tpts = int(f.get("tpts", 0)) + 1
		leveled = true
	if not leveled:
		return
	_recalc_derived(f, true)
	_sfx_play("levelup")
	_log("%s — УРОВЕНЬ %d! (+%d очков навыков)" % [f.name, int(f.lvl), 5 if int(f.lvl) <= 5 else 3])
	if f.team == 1:
		# боты распределяют очки автоматически
		var keys := ["str", "agi", "end", "per"]
		for j in 5:
			var kk2: String = keys[_rng.randi() % keys.size()]
			f.stats[kk2] = int(f.stats.get(kk2, 0)) + 1
		f.pts = 0
		_recalc_derived(f, true)
	elif not _lvl_open:
		_show_levelup(i)

func _lvl_add(f: Dictionary, k: String, d: int, val: Label, pts: Label) -> void:
	if d > 0 and int(f.pts) <= 0:
		return
	if d < 0 and int(f.stats.get(k, 0)) <= 0:
		return
	f.stats[k] = int(f.stats.get(k, 0)) + d
	f.pts = int(f.pts) - d
	val.text = str(int(f.stats[k]))
	pts.text = "Свободно очков: %d" % int(f.pts)

func _lvl_confirm(f: Dictionary) -> void:
	_recalc_derived(f, false)
	_lvl_open = false
	if _lvl_wrap:
		_lvl_wrap.queue_free()
		_lvl_wrap = null
	_refresh_fighter_panel()
	_refresh_squad()
	_log("%s: навыки обновлены — HP %d, ОД %d, обзор %d" % [f.name, int(f.max_hp), int(f.max_ap), int(f.vision)])

func _show_levelup(i: int) -> void:
	if _lvl_open or i < 0:
		return
	var f = _fighters[i]
	_lvl_open = true
	var wrap := CenterContainer.new()
	wrap.set_anchors_preset(Control.PRESET_FULL_RECT)
	_ui.layer.add_child(wrap)
	_lvl_wrap = wrap
	var panel := PanelContainer.new()
	panel.custom_minimum_size = Vector2(min(560.0, _vw() * 0.94), 0)
	panel.add_theme_stylebox_override("panel", _frame_box())
	wrap.add_child(panel)
	var vb := VBoxContainer.new()
	panel.add_child(vb)
	var t := Label.new()
	t.text = "УРОВЕНЬ %d — %s" % [int(f.lvl), f.name]
	t.add_theme_font_size_override("font_size", 24)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(t)
	var sub := Label.new()
	sub.text = "Распредели очки навыков — действуют сразу, нераспределённые сохранятся"
	sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	sub.add_theme_font_size_override("font_size", 13)
	vb.add_child(sub)
	var pts := Label.new()
	pts.text = "Свободно очков: %d" % int(f.pts)
	pts.add_theme_font_size_override("font_size", 17)
	vb.add_child(pts)
	for k in STAT_KEYS:
		var row := HBoxContainer.new()
		vb.add_child(row)
		var lb := Label.new()
		lb.text = STAT_NAMES[k]
		lb.custom_minimum_size = Vector2(100, 0) if _mob() else Vector2(150, 0)
		row.add_child(lb)
		var val := Label.new()
		val.text = str(int(f.stats.get(k, 0)))
		val.custom_minimum_size = Vector2(36, 0)
		val.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		row.add_child(val)
		var minus := Button.new()
		minus.text = "-"
		minus.pressed.connect(_lvl_add.bind(f, k, -1, val, pts))
		row.add_child(minus)
		var plus := Button.new()
		plus.text = "+"
		plus.pressed.connect(_lvl_add.bind(f, k, 1, val, pts))
		row.add_child(plus)
		var hint := Label.new()
		hint.text = "  " + STAT_HINTS[k]
		hint.add_theme_font_size_override("font_size", 10 if _mob() else 12)
		row.add_child(hint)
	var tl := Label.new()
	tl.text = "— Таланты (очков: %d; +1 каждые 3 уровня) —" % int(f.get("tpts", 0))
	tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tl.add_theme_font_size_override("font_size", 14)
	tl.add_theme_color_override("font_color", Color(1.0, 0.9, 0.45))
	vb.add_child(tl)
	for tal in TALENTS:
		var cur := _tal(f, tal["id"])
		var trow := HBoxContainer.new()
		vb.add_child(trow)
		var tnl := Label.new()
		tnl.text = "%s %s — %d/%d" % [tal["icon"], tal["name"], cur, int(tal["max"])]
		tnl.custom_minimum_size = Vector2(180 if _mob() else 240, 0)
		tnl.add_theme_font_size_override("font_size", 13)
		tnl.mouse_filter = Control.MOUSE_FILTER_STOP
		tnl.tooltip_text = str(tal["desc"])
		trow.add_child(tnl)
		var tb := Button.new()
		var cost := cur + 1
		if cur >= int(tal["max"]):
			tb.text = "МАКС"
			tb.disabled = true
		else:
			tb.text = "+%d 🎯" % cost
			tb.disabled = int(f.get("tpts", 0)) < cost
			tb.tooltip_text = "%s\nЦена ранга: %d очк." % [str(tal["desc"]), cost]
			var tid: String = tal["id"]
			var fi3: int = i
			tb.pressed.connect(func():
				if _tal_buy(_fighters[fi3], tid):
					_lvl_wrap.queue_free()
					_lvl_open = false
					_show_levelup(fi3)
			)
		trow.add_child(tb)
		var tdesc := Label.new()
		tdesc.text = "  " + str(tal["desc"])
		tdesc.add_theme_font_size_override("font_size", 10 if _mob() else 11)
		tdesc.add_theme_color_override("font_color", Color(0.65, 0.7, 0.75))
		tdesc.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		tdesc.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		trow.add_child(tdesc)
	var ok := Button.new()
	ok.text = "ПОДТВЕРДИТЬ"
	_style_menu_button(ok)
	ok.pressed.connect(_lvl_confirm.bind(f))
	vb.add_child(ok)
func _spend_consumable(att: int) -> void:
	var a = _fighters[att]
	_log("%s: %s потрачено" % [a.name, a.weapon.get("name", "?")])
	a.gun = {}
	a.weapon = a.melee

func _reload_selected() -> void:
	if _selected < 0:
		return
	var f = _fighters[_selected]
	if not f.weapon.has("ammo"):
		_log("Нож не требует перезарядки")
		return
	var mag: int = f.weapon.get("ammo", 0)
	var need: int = mag - int(f.ammo)
	if need <= 0:
		_log("Магазин полон")
		return
	if int(f.get("spare", -1)) == 0:
		_log("Нет запасных патронов!")
		return
	var rc: int = f.weapon.get("reload_ap", RELOAD_AP)
	if _tal(f, "reload1") > 0:
		rc = 1
	if f.ap < rc:
		_log("Нужно %d AP на перезарядку" % rc)
		return
	f.ap -= rc
	var take: int = need if int(f.get("spare", -1)) < 0 else mini(need, int(f.spare))
	f.ammo = int(f.ammo) + take
	if int(f.get("spare", -1)) > 0:
		f.spare = int(f.spare) - take
	_sfx_play("reload")
	var spare_txt := "∞" if int(f.get("spare", -1)) < 0 else str(int(f.spare))
	_log("%s перезарядился (магазин %d, запас %s)" % [f.name, int(f.ammo), spare_txt])
	_after_action()

func _swap_weapon() -> void:
	if _selected < 0:
		return
	var f = _fighters[_selected]
	if f.weapon == f.melee:
		f.weapon = f.gun if not f.gun.is_empty() else f.melee
	else:
		f.weapon = f.melee
	_sfx_play("swap")
	_log("%s: в руках — %s" % [f.name, f.weapon.get("name", "?")])
	_refresh_fighter_panel()

# ---------- ящики и инвентарь ----------
func _open_chest(fi: int, cell: Vector2i) -> void:
	var f = _fighters[fi]
	var k := _key(cell)
	if not _chests.has(k):
		return
	if maxi(absi(f.cell.x - cell.x), absi(f.cell.y - cell.y)) != 1:
		_log("Подойдите вплотную к ящику")
		return
	if f.ap < OPEN_CHEST_AP:
		_log("Нужно %d AP чтобы открыть ящик" % OPEN_CHEST_AP)
		return
	f.ap -= OPEN_CHEST_AP
	if f.team == 0:
		_chests_opened += 1
	_face_cell(f, cell)
	_sfx_play("open")
	_show_chest_panel(k)

func _entry_name(entry: Dictionary) -> String:
	var s: String = entry["item"].get("name", "?")
	match entry["kind"]:
		"weapon":
			s += " (урон %d)" % entry["item"].get("damage", 0)
		"armor":
			s += " (защита %d)" % entry["item"].get("defense", 0)
		"consumable":
			if entry["item"].has("heal"):
				s += " (+%d HP)" % entry["item"]["heal"]
			else:
				s += " (+%d AP)" % entry["item"].get("ap_restore", 0)
	return s

func _show_chest_panel(k: String) -> void:
	var box: VBoxContainer = _ui.chest_box
	for ch in box.get_children():
		ch.queue_free()
	var title := Label.new()
	title.text = "Содержимое ящика"
	title.add_theme_font_size_override("font_size", 18)
	box.add_child(title)
	for entry in _chests[k]:
		var rowh := HBoxContainer.new()
		rowh.add_theme_constant_override("separation", 8)
		var cic := _item_icon(entry)
		if cic != null:
			rowh.add_child(_icon_rect(cic))
		var l := Label.new()
		l.text = _entry_name(entry)
		l.tooltip_text = _item_tooltip(entry)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rowh.add_child(l)
		box.add_child(rowh)
	var take := Button.new()
	take.custom_minimum_size = Vector2(0, 40)
	take.text = "Взять всё"
	take.pressed.connect(func(): _take_all(k))
	box.add_child(take)
	var close := Button.new()
	close.custom_minimum_size = Vector2(0, 40)
	close.text = "Закрыть"
	close.pressed.connect(func(): _ui.chest_panel.visible = false)
	box.add_child(close)
	_ui.chest_panel.visible = true

func _take_all(k: String) -> void:
	if _selected < 0 or not _chests.has(k):
		return
	var f = _fighters[_selected]
	var taken := 0
	var left := []
	for entry in _chests[k]:
		if _load_weight(f) + _item_weight(entry) <= _carry_limit(f):
			f.backpack.append(entry)
			taken += 1
		else:
			left.append(entry)
	if left.is_empty():
		_chests.erase(k)
		if _chest_pads.has(k):
			_chest_pads[k].material_override = _mat(Color.BLACK, 0.0, 1.0, Color(0.3, 0.3, 0.3), 0.8)
		_ui.chest_panel.visible = false
		_log("%s забрал всё из ящика (+%d предм.)" % [f.name, taken])
	else:
		_chests[k] = left
		_log("%s взял %d предм., %d не влезло (вес)" % [f.name, taken, left.size()])
		_show_chest_panel(k)
	_refresh_fighter_panel()

func _use_backpack(idx: int) -> void:
	if _selected < 0:
		return
	var f = _fighters[_selected]
	if idx < 0 or idx >= f.backpack.size():
		return
	var entry = f.backpack[idx]
	match entry["kind"]:
		"weapon":
			var sreq: int = int(entry["item"].get("str_req", 0))
			if sreq > int(f.stats.get("str", 0)):
				_log("Нужна Сила %d для «%s»" % [sreq, entry["item"].get("name", "?")])
				return
			f.backpack.remove_at(idx)
			if not f.gun.is_empty():
				f.backpack.append({"kind": "weapon", "item": f.gun})
			f.gun = entry["item"]
			f.weapon = entry["item"]
			f.ammo = entry["item"].get("ammo", 0)
			f.spare = entry["item"].get("spare", -1)
			_log("%s взял в руки: %s" % [f.name, entry["item"]["name"]])
		"armor":
			var cat: String = entry["cat"]
			f.backpack.remove_at(idx)
			if f.armor[cat]:
				f.backpack.append({"kind": "armor", "cat": cat, "item": f.armor[cat]})
			f.armor[cat] = entry["item"]
			_recalc_derived(f)  # тяжёлая броня может снижать ОД
			_log("%s надел: %s (защита %d)" % [f.name, entry["item"]["name"], _defense(f)])
		"consumable":
			var it: Dictionary = entry["item"]
			if it.has("heal"):
				if f.ap < it.get("ap_cost", 2):
					_log("Не хватает AP на аптечку")
					return
				f.ap -= it.get("ap_cost", 2)
				var heal_am: int = int(it["heal"] * (1.0 + 0.25 * _tal(f, "medic")))
				f.hp = mini(int(f.max_hp), int(f.hp) + heal_am)
				f.backpack.remove_at(idx)
				_log("%s: +%d HP (итого %d)" % [f.name, heal_am, f.hp])
			else:
				f.ap += it.get("ap_restore", 0)
				f.backpack.remove_at(idx)
				_log("%s: +%d AP (спонсор шоу!)" % [f.name, it.get("ap_restore", 0)])
	_after_action()

# ---------- ввод ----------
func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.pressed:
			if event.button_index == MOUSE_BUTTON_WHEEL_UP:
				_zoom(-4.0)
				return
			elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
				_zoom(4.0)
				return
			elif event.button_index == MOUSE_BUTTON_RIGHT:
				_rmb_drag = true
				_rmb_moved = false
				return
		elif event.button_index == MOUSE_BUTTON_RIGHT and _rmb_drag:
			_rmb_drag = false
			# короткий клик ПКМ без движения — отмена выбора
			if not _rmb_moved and not _busy and not _game_over and not _menu_open and not _lvl_open:
				_deselect()
			return
	if event is InputEventMouseMotion and _rmb_drag:
		_orbit(-event.relative.x * 0.3, event.relative.y * 0.25)
		if event.relative.length() > 2.0:
			_rmb_moved = true
		return
	if _menu_open or _lvl_open:
		return
	# ЛКМ: короткий клик — действие; удержание и тяга — обзор карты
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_lmb_down = true
			_lmb_moved = false
			_lmb_pos = event.position
		elif _lmb_down:
			_lmb_down = false
			if not _lmb_moved and not _busy and not _game_over:
				_click_left()
		return
	if event is InputEventMouseMotion and _lmb_down:
		if (event.position - _lmb_pos).length() > 8.0:
			_lmb_moved = true
		if _lmb_moved:
			_pan_camera(event.relative)
		return
	# тач: 1 палец — тап/тяга; 2 пальца — щипок (зум)
	if event is InputEventScreenTouch:
		if event.pressed:
			_touch_pts[event.index] = event.position
			if _touch_pts.size() == 1:
				_lmb_down = true
				_lmb_moved = false
				_lmb_pos = event.position
		else:
			var was_two := _touch_pts.size() >= 2
			_touch_pts.erase(event.index)
			if not was_two and _lmb_down and not _lmb_moved and not _busy and not _game_over:
				_click_left_at(event.position)
			if _touch_pts.is_empty():
				_lmb_down = false
				_pinch = 0.0
		return
	if event is InputEventScreenDrag:
		_touch_pts[event.index] = event.position
		if _touch_pts.size() >= 2:
			var ks: Array = _touch_pts.keys()
			var pa: Vector2 = _touch_pts[ks[0]]
			var pb: Vector2 = _touch_pts[ks[1]]
			var pinch := (pa - pb).length()
			if _pinch > 0.0:
				_zoom((_pinch - pinch) * 0.25)
			_pinch = pinch
			_lmb_moved = true
		elif _lmb_down:
			if (event.position - _lmb_pos).length() > 10.0:
				_lmb_moved = true
			if _lmb_moved:
				_pan_camera(event.relative)
		return
	if _busy or _game_over:
		return
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_SPACE:
				_end_turn()
			KEY_ESCAPE:
				_deselect()
			KEY_R:
				_reload_selected()
			KEY_F:
				_swap_weapon()
			KEY_I:
				_toggle_inventory()
			KEY_T:
				_taunt_selected()
			KEY_G:
				_graffiti_selected()

func _click_left() -> void:
	var fi := _fighter_near_mouse()
	if fi >= 0:
		if _fighters[fi].team == 0:
			_select(fi)
		elif _selected >= 0:
			_shoot(_selected, fi)
			if _onboard_step == 2:
				_onboard_next()
			_after_action()
		return
	var cell := _cell_under_mouse()
	if cell.x < 0 or _selected < 0:
		return
	var k := _key(cell)
	if _chests.has(k):
		_open_chest(_selected, cell)
		_after_action()
	elif _cover_at.has(k):
		_shoot_cover(_selected, cell)
		_after_action()
	elif _reach.has(cell):
		var f = _fighters[_selected]
		var path := _path_to(f.cell, cell)
		f.ap -= _reach[cell]
		_move_fighter(_selected, cell, path)
		if _onboard_step == 1:
			_onboard_next()
		_after_action()

func _after_action() -> void:
	if _selected >= 0:
		var f = _fighters[_selected]
		_reach = _reachable(f.cell, f.ap)
		_show_reach()
		_sel_ring.position = gw(f.cell.x, f.cell.y, 0.05)
	_update_fog()
	_refresh_fighter_panel()
	_refresh_turn_lbl()

# ---------- ходы и боты ----------
func _end_turn() -> void:
	if _busy or _game_over or _lvl_open:
		return
	if _onboard_step == 3:
		_onboard_finish()
	_busy = true
	_deselect()
	_log("Ход противника...")
	await get_tree().create_timer(0.4).timeout
	for i in _fighters.size():
		if _game_over:
			break
		var f = _fighters[i]
		if f.team == 1 and f.alive:
			await _bot_act(i)
	if not _game_over:
		_tick_fire()
	if not _game_over:
		_turn += 1
		for f in _fighters:
			if f.alive:
				f.ap = f.max_ap
		_log("Ход %d — ваши бойцы готовы" % _turn)
	if not _game_over:
		_tick_zone()
	_update_fog()
	_refresh_turn_lbl()
	_busy = false

func _nearest_enemy(from: Vector2i, enemy_team: int) -> int:
	var best := -1
	var best_d := 999.0
	for i in _fighters.size():
		var f = _fighters[i]
		if not f.alive or f.team != enemy_team:
			continue
		var d := Vector2(from.x - f.cell.x, from.y - f.cell.y).length()
		if d < best_d:
			best_d = d
			best = i
	return best

func _nearest_visible_enemy(from_cell: Vector2i, vision: int, enemy_team: int) -> int:
	# честный туман войны для ботов: цель должна быть в радиусе обзора и в прямой видимости
	var best := -1
	var best_d := 999.0
	for i in _fighters.size():
		var f = _fighters[i]
		if not f.alive or f.team != enemy_team:
			continue
		var d := Vector2(from_cell.x - f.cell.x, from_cell.y - f.cell.y).length()
		if d <= vision and d < best_d and _los(from_cell, f.cell):
			best_d = d
			best = i
	return best

func _bot_act(i: int) -> void:
	var f = _fighters[i]
	if int(f.get("aggro_ttl", 0)) > 0:
		f.aggro_ttl = int(f.get("aggro_ttl", 0)) - 1
	var guard := 0
	while f.alive and f.ap > 0 and guard < 24 and not _game_over:
		guard += 1
		var vis: int = f.get("vision", VISION)
		var t := _bot_pick_target(f, vis)
		if t < 0:
			# никого не видно — идём к центру арены (подиум)
			if not _bot_step(i, Vector2i(_grid_n / 2, _grid_n / 2)):
				return
			await get_tree().create_timer(0.25).timeout
			continue
		var w: Dictionary = f.weapon
		var burst: int = w.get("burst", 1)
		var dist := Vector2(f.cell.x - _fighters[t].cell.x, f.cell.y - _fighters[t].cell.y).length()
		if w.has("ammo") and f.ammo < burst:
			var rc2: int = w.get("reload_ap", RELOAD_AP)
			if _tal(f, "reload1") > 0:
				rc2 = 1
			if int(f.get("spare", -1)) == 0:
				# запас пуст — переходим на нож
				f.weapon = f.melee
				continue
			if f.ap >= rc2:
				f.ap -= rc2
				var need2: int = w.get("ammo", 0) - int(f.ammo)
				var take2: int = need2 if int(f.get("spare", -1)) < 0 else mini(need2, int(f.spare))
				f.ammo = int(f.ammo) + take2
				if int(f.get("spare", -1)) > 0:
					f.spare = int(f.spare) - take2
				_sfx_play("reload")
				_log("%s перезаряжается" % f.name)
				await get_tree().create_timer(0.3).timeout
				continue
		if dist <= w.get("range", 1) and f.ap >= w.get("ap_cost", 3):
			_shoot(i, t)
			await get_tree().create_timer(0.5).timeout
		elif f.ap >= 1:
			if not _bot_step(i, _fighters[t].cell):
				return
			await get_tree().create_timer(0.25).timeout
		else:
			return

func _bot_step(i: int, target: Vector2i) -> bool:
	var f = _fighters[i]
	var best: Vector2i = f.cell
	var best_d := Vector2(f.cell.x - target.x, f.cell.y - target.y).length()
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		var n: Vector2i = f.cell + d
		if n.x < 0 or n.y < 0 or n.x >= _grid_n or n.y >= _grid_n:
			continue
		var k := _key(n)
		if _unit_at.has(k) or _fire.has(n):
			continue
		if not _in_zone(n) and _in_zone(f.cell):
			continue
		if _occupied.has(k):
			if not _house_at.has(k) or not _can_enter(f.cell, n):
				continue
		var nd := Vector2(n.x - target.x, n.y - target.y).length()
		if nd < best_d:
			best_d = nd
			best = n
	if best == f.cell:
		return false
	f.ap -= 1
	_move_fighter(i, best)
	return true

func _check_end() -> void:
	if _game_over:
		return
	var red := _alive_count(0)
	var blue := _alive_count(1)
	if blue == 0 or red == 0:
		_game_over = true
		_deselect()
		# прогресс бойцов игрока сохраняется в профиль
		for pi in _mode:
			var pf = _fighters[pi]
			_profile.stats[pi] = pf.stats
			_profile.lvl[pi] = int(pf.lvl)
			_profile.xp[pi] = int(pf.xp)
			_profile.talents[pi] = pf.get("talents", {})
			_profile.tpts[pi] = int(pf.get("tpts", 0))
			_profile.prof[pi] = pf.get("prof", {})
		# --- награды за бой: монеты, победы, открытие слотов ---
		var win := blue == 0
		var p_kills := 0
		for fk in _fighters:
			if fk.team == 0:
				p_kills += int(fk.kills)
		var bp_gain := 5 + 5 * p_kills + (20 if win else 0)
		_profile.bp_xp = int(_profile.get("bp_xp", 0)) + bp_gain
		var reward := 2 + 1 * p_kills  # +2 за бой, +1 за убийство
		_profile.coins = int(_profile.get("coins", 0)) + reward
		_profile.total_kills = int(_profile.get("total_kills", 0)) + p_kills
		if win:
			_profile.wins = int(_profile.get("wins", 0)) + 1
		var unlock_msg := ""
		var wn := int(_profile.get("wins", 0))
		for si in range(2, 5):
			if _profile.unlocked_slots < si and wn >= int(SLOT_WINS[si]):
				_profile.unlocked_slots = si
				unlock_msg = "🔓 Открыт слот бойца №%d!" % si
		var daily_msgs: Array = _daily_add(0, p_kills)
		daily_msgs.append_array(_daily_add(1, _chests_opened))
		if win:
			daily_msgs.append_array(_daily_add(2, 1))
		_battle_reward = {"coins": reward, "kills": p_kills, "win": win, "unlock": unlock_msg, "daily": daily_msgs}
		_save_profile()
		var msg := "ПОБЕДА! Арена ваша!" if blue == 0 else "Поражение. Шоу окончено."
		_log(msg)
		if _ui.has("layer"):
			var wrap := CenterContainer.new()
			wrap.set_anchors_preset(Control.PRESET_FULL_RECT)
			_ui.layer.add_child(wrap)
			var panel := PanelContainer.new()
			panel.custom_minimum_size = Vector2(min(540.0, _vw() * 0.94), 0)
			panel.add_theme_stylebox_override("panel", _frame_box())
			wrap.add_child(panel)
			var vb := VBoxContainer.new()
			panel.add_child(vb)
			var l := Label.new()
			l.text = msg
			l.add_theme_font_size_override("font_size", 24 if _mob() else 32)
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			vb.add_child(l)
			var sub := Label.new()
			sub.text = "Раундов: %d · Зона: фаза %d" % [_turn, _zone_phase]
			sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			sub.add_theme_font_size_override("font_size", 14)
			vb.add_child(sub)
			if not _battle_reward.is_empty():
				var rw := Label.new()
				rw.text = "Награда: +%d монет (бой 2 + убийства %d×1) · Всего: %d 💰" % [
					int(_battle_reward.coins),
					int(_battle_reward.kills),
					int(_profile.get("coins", 0))]
				rw.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
				rw.add_theme_font_size_override("font_size", 15)
				rw.add_theme_color_override("font_color", Color(1.0, 0.9, 0.45))
				rw.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
				rw.custom_minimum_size = Vector2(min(500.0, _vw() * 0.9), 0)
				vb.add_child(rw)
				if str(_battle_reward.get("unlock", "")) != "":
					var ul := Label.new()
					ul.text = str(_battle_reward.unlock)
					ul.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
					ul.add_theme_font_size_override("font_size", 16)
					ul.add_theme_color_override("font_color", Color(0.5, 1.0, 0.6))
					vb.add_child(ul)
				for dm in _battle_reward.get("daily", []):
					var dl := Label.new()
					dl.text = str(dm)
					dl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
					dl.add_theme_font_size_override("font_size", 14)
					dl.add_theme_color_override("font_color", Color(0.65, 0.9, 1.0))
					vb.add_child(dl)
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
			btns.add_child(rv)

# ---------- интерфейс ----------
func _build_ui() -> void:
	# кириллический шрифт Manrope + монохромные эмодзи Noto Emoji как fallback
	if ResourceLoader.exists("res://assets/fonts/Manrope.ttf"):
		var fv := FontVariation.new()
		fv.base_font = load("res://assets/fonts/Manrope.ttf")
		if ResourceLoader.exists("res://assets/fonts/NotoEmojiStatic.ttf"):
			fv.fallbacks = [load("res://assets/fonts/NotoEmojiStatic.ttf")]
		ThemeDB.fallback_font = fv
		ThemeDB.fallback_font_size = 16
	var layer := CanvasLayer.new()
	layer.name = "UI"
	add_child(layer)
	_ui.layer = layer
	_http = HTTPRequest.new()
	_http.request_completed.connect(_on_api_done)
	layer.add_child(_http)
	var turn := Label.new()
	turn.position = Vector2(16, 10)
	turn.add_theme_font_size_override("font_size", 14 if _mob() else 20)
	layer.add_child(turn)
	_ui.turn = turn
	var btn := Button.new()
	btn.text = "Конец хода" if _mob() else "Конец хода [Space]"
	btn.anchor_left = 1.0
	btn.anchor_right = 1.0
	btn.offset_left = -150.0 if _mob() else -212.0
	btn.offset_right = -8.0 if _mob() else -16.0
	btn.offset_top = 10.0
	btn.offset_bottom = 56.0
	btn.pressed.connect(_end_turn)
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
	btn.add_theme_font_size_override("font_size", 14 if _mob() else 17)
	layer.add_child(btn)
	_ui.end_btn = btn
	var lobby := Button.new()
	lobby.text = "Лобби"
	lobby.anchor_left = 1.0
	lobby.anchor_right = 1.0
	lobby.offset_left = -150.0 if _mob() else -212.0
	lobby.offset_right = -8.0 if _mob() else -16.0
	lobby.offset_top = 62.0
	lobby.offset_bottom = 108.0
	lobby.tooltip_text = "Выйти в главное меню (бой будет потерян)"
	lobby.pressed.connect(_go_lobby)
	layer.add_child(lobby)
	# --- карточка бойца слева сверху: портрет + HP/AP + рюкзак под анимацией ---
	var card := PanelContainer.new()
	card.position = Vector2(12, 48)
	card.custom_minimum_size = Vector2(180, 158) if _mob() else Vector2(204, 168)
	var card_sb := _frame_box()
	card_sb.border_color = Color(1.0, 0.28, 0.34, 0.8)
	card_sb.shadow_color = Color(1.0, 0.2, 0.35, 0.25)
	card.add_theme_stylebox_override("panel", card_sb)
	layer.add_child(card)
	var card_v := VBoxContainer.new()
	card.add_child(card_v)
	var ch := HBoxContainer.new()
	card_v.add_child(ch)
	var pvc := SubViewportContainer.new()
	pvc.custom_minimum_size = Vector2(72, 104)
	pvc.stretch = true
	var pv := SubViewport.new()
	pv.size = Vector2i(172, 248)
	pv.own_world_3d = true
	pv.transparent_bg = true
	pvc.add_child(pv)
	ch.add_child(pvc)
	_ui.card_pvc = pvc
	# аватар игрока из профиля (заменяет 3D-портрет, если загружен)
	var ava := TextureRect.new()
	ava.custom_minimum_size = Vector2(72, 104)
	ava.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	ava.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	ava.visible = false
	ch.add_child(ava)
	_ui.card_avatar = ava
	var cvb2 := VBoxContainer.new()
	ch.add_child(cvb2)
	var name_l := Label.new()
	name_l.add_theme_font_size_override("font_size", 16)
	cvb2.add_child(name_l)
	var hp_l := Label.new()
	cvb2.add_child(hp_l)
	var hp_bar := ProgressBar.new()
	hp_bar.max_value = 100
	hp_bar.custom_minimum_size = Vector2(88, 12) if _mob() else Vector2(104, 12)
	hp_bar.show_percentage = false
	cvb2.add_child(hp_bar)
	var ap_l := Label.new()
	cvb2.add_child(ap_l)
	var ap_bar := ProgressBar.new()
	ap_bar.max_value = 10
	ap_bar.custom_minimum_size = Vector2(88, 12) if _mob() else Vector2(104, 12)
	ap_bar.show_percentage = false
	cvb2.add_child(ap_bar)
	# иконка рюкзака прямо под портретом/анимацией бойца
	var bag := Button.new()
	bag.text = "🎒 Рюкзак [I]"
	bag.custom_minimum_size = Vector2(0, 40)
	bag.pressed.connect(_toggle_inventory)
	card_v.add_child(bag)
	card.visible = false
	_ui.card = card
	_ui.card_view = pv
	_ui.card_name = name_l
	_ui.card_hp_l = hp_l
	_ui.card_hp = hp_bar
	_ui.card_ap_l = ap_l
	_ui.card_ap = ap_bar
	_style_bar(hp_bar, Color(0.25, 0.9, 0.3))
	_style_bar(ap_bar, Color(0.2, 0.8, 1.0))
	# --- ростер отряда: вертикальный список слева, компактный, с портретами ---
	var roster := VBoxContainer.new()
	roster.position = Vector2(12, 226)
	roster.add_theme_constant_override("separation", 4)
	layer.add_child(roster)
	_ui.squad_rows = []
	for i in 4:
		var row := PanelContainer.new()
		row.custom_minimum_size = Vector2(160, 42) if _mob() else Vector2(190, 42)
		var rh := HBoxContainer.new()
		rh.add_theme_constant_override("separation", 6)
		row.add_child(rh)
		var rp := TextureRect.new()
		rp.custom_minimum_size = Vector2(30, 30)
		rp.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		rp.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
		rh.add_child(rp)
		var rv := VBoxContainer.new()
		rv.add_theme_constant_override("separation", 0)
		rh.add_child(rv)
		var rn := Label.new()
		rn.add_theme_font_size_override("font_size", 12)
		rv.add_child(rn)
		var rs := Label.new()
		rs.add_theme_font_size_override("font_size", 10)
		rv.add_child(rs)
		var fi: int = i
		row.gui_input.connect(func(ev: InputEvent):
			if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
				_select_from_squad(fi)
		)
		roster.add_child(row)
		_ui.squad_rows.append({"row": row, "portrait": rp, "name": rn, "stats": rs})
	# --- диалоговое окно снизу слева: вкладки Логи битвы / Чат Арены / Чат комнаты ---
	var chat := PanelContainer.new()
	chat.anchor_top = 1.0
	chat.anchor_bottom = 1.0
	chat.offset_left = 12.0
	chat.offset_right = 392.0
	chat.offset_top = -234.0
	chat.offset_bottom = -12.0
	var chat_sb := StyleBoxFlat.new()
	chat_sb.bg_color = Color(0.14, 0.20, 0.15, 0.78)
	chat_sb.border_color = Color(0.38, 0.55, 0.40, 0.85)
	chat_sb.set_border_width_all(1)
	chat_sb.set_corner_radius_all(10)
	chat_sb.set_content_margin_all(8)
	chat.add_theme_stylebox_override("panel", chat_sb)
	layer.add_child(chat)
	var cvb := VBoxContainer.new()
	chat.add_child(cvb)
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 4)
	cvb.add_child(tabs)
	_ui.chat_tab_btns = []
	var tab_names := ["Логи битвы", "Чат Арены", "Чат комнаты"]
	for ti in 3:
		var tb := Button.new()
		tb.text = tab_names[ti]
		tb.custom_minimum_size = Vector2(0, 34)
		tb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var tn: int = ti
		tb.pressed.connect(func():
			_chat_tab = tn
			_render_chat()
		)
		tabs.add_child(tb)
		_ui.chat_tab_btns.append(tb)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 132)
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	cvb.add_child(scroll)
	var lines := VBoxContainer.new()
	lines.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(lines)
	_ui.chat_lines = lines
	_ui.chat_scroll = scroll
	var inrow_b := HBoxContainer.new()
	inrow_b.add_theme_constant_override("separation", 4)
	cvb.add_child(inrow_b)
	var inp := LineEdit.new()
	inp.placeholder_text = "Сообщение… (вкладки чатов, пока локально)"
	inp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inp.text_submitted.connect(func(_t): _battle_chat_send(inp))
	inrow_b.add_child(inp)
	_ui.chat_input = inp
	var emb2 := Button.new()
	emb2.custom_minimum_size = Vector2(34, 30)
	emb2.tooltip_text = "Эмодзи"
	var emtr2 := TextureRect.new()
	emtr2.texture = _icon_tex("smile")
	emtr2.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	emtr2.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	emtr2.custom_minimum_size = Vector2(18, 18)
	emtr2.set_anchors_preset(Control.PRESET_CENTER)
	emtr2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	emb2.add_child(emtr2)
	emb2.pressed.connect(func(): _toggle_emoji_panel(inp, chat))
	inrow_b.add_child(emb2)
	var sendb2 := Button.new()
	sendb2.text = "»"
	sendb2.custom_minimum_size = Vector2(34, 30)
	sendb2.tooltip_text = "Отправить"
	sendb2.pressed.connect(func(): _battle_chat_send(inp))
	inrow_b.add_child(sendb2)
	_render_chat()
	# мобильный режим: лог свёрнут, разворачивается кнопкой
	if minf(_vw(), _vh()) < 700.0:
		chat.visible = false
		var ct := Button.new()
		ct.text = "📜 Лог"
		ct.anchor_top = 1.0
		ct.anchor_bottom = 1.0
		ct.offset_left = 12.0
		ct.offset_right = 100.0
		ct.offset_top = -56.0
		ct.offset_bottom = -12.0
		ct.pressed.connect(func(): chat.visible = not chat.visible)
		ct.pressed.connect(_sfx_play.bind("click"))
		layer.add_child(ct)
	# --- панель выбранного бойца: справа ---
	var fp := PanelContainer.new()
	fp.anchor_left = 1.0
	fp.anchor_right = 1.0
	fp.offset_left = -min(296.0, _vw() * 0.68)
	fp.offset_right = -8.0
	fp.offset_top = 96.0
	fp.offset_bottom = 328.0
	fp.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(fp)
	var vb := VBoxContainer.new()
	fp.add_child(vb)
	_ui.fighter_panel = fp
	_ui.fighter_box = vb
	fp.visible = false
	var cp := PanelContainer.new()
	cp.set_anchors_preset(Control.PRESET_CENTER)
	var cw: float = min(240.0, _vw() * 0.46)
	cp.offset_left = -cw
	cp.offset_right = cw
	cp.offset_top = -170.0
	cp.offset_bottom = 170.0
	cp.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(cp)
	var cvb3 := VBoxContainer.new()
	cp.add_child(cvb3)
	_ui.chest_panel = cp
	_ui.chest_box = cvb3
	cp.visible = false
	# --- окно инвентаря (скрыто) ---
	var iw := PanelContainer.new()
	iw.set_anchors_preset(Control.PRESET_CENTER)
	var iw2: float = min(320.0, _vw() * 0.47)
	iw.offset_left = -iw2
	iw.offset_right = iw2
	iw.offset_top = -250.0
	iw.offset_bottom = 250.0
	iw.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(iw)
	var ivb := VBoxContainer.new()
	iw.add_child(ivb)
	iw.visible = false
	_ui.inv_panel = iw
	_ui.inv_box = ivb
	var al := Control.new()
	al.set_anchors_preset(Control.PRESET_FULL_RECT)
	al.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(al)
	_arrow_layer = al
	_refresh_turn_lbl()

func _layout_menu() -> void:
	# логотип центрируется над фактической шириной колонки кнопок
	if not _ui.has("menu_box"):
		return
	var vb2: VBoxContainer = _ui.menu_box
	var vw3: float = _vw()
	var bw: float = maxf(vb2.size.x, 400.0)
	var mx: float = maxf(600.0, (vw3 - bw) / 2.0)
	vb2.position.x = mx
	if _ui.has("menu_logo"):
		var lg: TextureRect = _ui.menu_logo
		lg.position.x = mx + bw / 2.0 - lg.size.x / 2.0

# ---------- диалоговое окно: вкладки чатов/логов ----------
var _chat_tab := 0
var _battle_chat_local := [[], []]  # локальное эхо: [0]=Арена, [1]=Комната
const CHAT_STUB_ARENA := ["Система: Чат Арены — общение участников текущего боя.", "Система: появится в онлайн-режиме."]
const CHAT_STUB_ROOM := ["Система: Чат комнаты — ваше лобби перед боем.", "Система: появится в онлайн-режиме."]

func _battle_chat_send(inp: LineEdit) -> void:
	if _chat_tab == 0:
		return  # во вкладке логов отправка недоступна
	var t := inp.text.strip_edges()
	if t == "":
		return
	inp.clear()
	_battle_chat_local[_chat_tab - 1].append("Вы: " + t)
	if _battle_chat_local[_chat_tab - 1].size() > 30:
		_battle_chat_local[_chat_tab - 1].pop_front()
	_render_chat()

func _render_chat() -> void:
	if not _ui.has("chat_lines"):
		return
	for c in _ui.chat_lines.get_children():
		c.queue_free()
	var data: Array = _battle_log
	var col := Color(0.85, 0.9, 0.95)
	if _chat_tab == 1:
		data = CHAT_STUB_ARENA.duplicate()
		col = Color(0.7, 0.85, 0.7)
	elif _chat_tab == 2:
		data = CHAT_STUB_ROOM.duplicate()
		col = Color(0.7, 0.85, 0.7)
	if _chat_tab > 0:
		for my_line in _battle_chat_local[_chat_tab - 1]:
			data.append(my_line)
	for line in data:
		var l := Label.new()
		l.text = line
		l.add_theme_font_size_override("font_size", 11)
		l.add_theme_color_override("font_color", col)
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		_ui.chat_lines.add_child(l)
	for tb_i in _ui.chat_tab_btns.size():
		_ui.chat_tab_btns[tb_i].modulate = Color(1, 1, 1) if tb_i == _chat_tab else Color(0.6, 0.6, 0.65)
	await get_tree().process_frame
	_ui.chat_scroll.scroll_vertical = 100000

func _rematch() -> void:
	# реванш: тот же режим, автостарт
	var cfg := ConfigFile.new()
	cfg.set_value("game", "autostart", 1)
	cfg.save("user://autostart.cfg")
	get_tree().reload_current_scene()

func _go_lobby() -> void:
	# выход в главное меню: перезагрузка сцены (автостарт выключен — откроется меню)
	var cfg := ConfigFile.new()
	cfg.set_value("game", "autostart", 0)
	cfg.save("user://autostart.cfg")
	get_tree().reload_current_scene()

func _refresh_turn_lbl() -> void:
	if _ui.has("turn"):
		if _mob():
			_ui.turn.text = "Ход %d · %d:%d" % [_turn, _alive_count(0), _alive_count(1)]
		else:
			_ui.turn.text = "Ход %d   |   Красные: %d   Синие: %d" % [_turn, _alive_count(0), _alive_count(1)]
	_refresh_squad()

func _refresh_fighter_panel() -> void:
	if _selected < 0 or not _ui.has("fighter_panel"):
		return
	var f = _fighters[_selected]
	_ui.fighter_panel.visible = true
	var box: VBoxContainer = _ui.fighter_box
	for ch in box.get_children():
		ch.queue_free()
	var w := Label.new()
	var ammo_txt := ""
	if f.weapon.has("ammo"):
		var sp_txt := "∞" if int(f.get("spare", -1)) < 0 else str(int(f.spare))
		ammo_txt = " [патр. %d/%s]" % [int(f.ammo), sp_txt]
	w.text = "В руках: %s%s" % [f.weapon.get("name", "?"), ammo_txt]
	box.add_child(w)
	var lv := Label.new()
	lv.text = "Ур. %d · Опыт %d/%d · Убийств: %d" % [int(f.lvl), int(f.xp), _xp_need(int(f.lvl)), int(f.kills)]
	box.add_child(lv)
	var cls3 := _weapon_class(f.weapon)
	if cls3 != "":
		var plv := _prof_lvl(f, cls3)
		var px := int(f.get("prof", {}).get(cls3, 0))
		var next_txt := "МАКС" if plv >= 3 else "%d/%d" % [px, PROF_XP[plv]]
		var pl2 := Label.new()
		pl2.text = "Владение «%s»: ур. %d (%s)" % [CLASS_NAMES[cls3], plv, next_txt]
		pl2.add_theme_font_size_override("font_size", 12)
		pl2.add_theme_color_override("font_color", Color(0.6, 0.9, 1.0))
		box.add_child(pl2)
	var d := Label.new()
	d.text = "Защита: %d   Вес: %.1f/%.1f кг" % [_defense(f), _load_weight(f), _carry_limit(f)]
	box.add_child(d)
	var row := GridContainer.new()
	row.columns = 2
	box.add_child(row)
	var inv := Button.new()
	inv.text = "Рюкзак [I]"
	if ResourceLoader.exists("res://assets/ui/icons/backpack.png"):
		inv.icon = load("res://assets/ui/icons/backpack.png")
		inv.add_theme_constant_override("icon_max_width", 22)
	inv.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inv.add_theme_font_size_override("font_size", 12)
	inv.pressed.connect(_toggle_inventory)
	inv.pressed.connect(_sfx_play.bind("click"))
	row.add_child(inv)
	var sw := Button.new()
	sw.text = "Нож/ствол [F]"
	if ResourceLoader.exists("res://assets/ui/icons/Knife_1.png"):
		sw.icon = load("res://assets/ui/icons/Knife_1.png")
		sw.add_theme_constant_override("icon_max_width", 22)
	sw.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sw.add_theme_font_size_override("font_size", 12)
	sw.pressed.connect(_swap_weapon)
	sw.pressed.connect(_sfx_play.bind("click"))
	row.add_child(sw)
	var rl := Button.new()
	rl.text = "Перезарядка [R]"
	if ResourceLoader.exists("res://assets/ui/icons/reload.png"):
		rl.icon = load("res://assets/ui/icons/reload.png")
		rl.add_theme_constant_override("icon_max_width", 22)
	rl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rl.add_theme_font_size_override("font_size", 12)
	rl.pressed.connect(_reload_selected)
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
	if (int(f.get("pts", 0)) > 0 or int(f.get("tpts", 0)) > 0) and f.team == 0:
		var pb := Button.new()
		pb.text = "Навыки +%d" % int(f.pts)
		pb.add_theme_color_override("font_color", Color(1.0, 0.92, 0.4))
		var pbs := StyleBoxFlat.new()
		pbs.bg_color = Color(0.45, 0.33, 0.08, 0.95)
		pbs.border_color = Color(1.0, 0.85, 0.3, 0.95)
		pbs.set_border_width_all(2)
		pbs.set_corner_radius_all(6)
		pb.add_theme_stylebox_override("normal", pbs)
		pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		pb.pressed.connect(_show_levelup.bind(_selected))
		row.add_child(pb)
	_refresh_card()

# ---------- тестовый прогон для скриншота ----------
func _run_testplay() -> void:
	await get_tree().process_frame
	_profile.onboarded = 0
	_onboard_start()
	var f = _fighters[0]
	f.ap = 40
	_unit_at.erase(_key(f.cell))
	f.cell = Vector2i(20, 17)
	_unit_at["20,17"] = 0
	f.node.position = gw(20, 17)
	f.pad.position = gw(20, 17, 0.02)
	_select(0)
	_open_chest(0, Vector2i(20, 18))
	_take_all("20,18")
	_show_inventory()
	_log("TESTPLAY: ящик вскрыт, лут в рюкзаке")
	# проверка брони: жилет защита 8, удар 50 -> 42
	var f0 = _fighters[0]
	f0.backpack.append({"kind": "armor", "cat": "body", "item": _items["armor"]["body"][1]})
	_use_backpack(f0.backpack.size() - 1)
	var hp0: int = f0.hp
	_apply_damage(0, 50, "TEST")
	print("ARMOR_TEST защита=", _defense(f0), " урон50->", hp0 - f0.hp, " (ожидается 42)")
	f0.hp = hp0
	f0.armor["body"] = null
	# проверка бочки: 27 HP + 2 обязательных попадания (43 урона за раз мало)
	var bk := ""
	for ck9 in _covers.keys():
		if _covers[ck9].get("barrel", false):
			bk = ck9
			break
	if bk != "":
		_damage_cover_hit(bk, 43, "TEST")
		print("BARREL_TEST 1-е попадание 43: жива=", _covers.has(bk), " (ожидается true)")
		_damage_cover_hit(bk, 43, "TEST")
		print("BARREL_TEST 2-е попадание: жива=", _covers.has(bk), " (ожидается false)")
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_play.png")
	print("TESTPLAY_SAVED")
	get_tree().quit()

# ---------- тест ботов: синие ходят и стреляют ----------
func _run_testbots() -> void:
	await get_tree().process_frame
	# телепорт: игрок 0 и все боты — в центр, ближний бой
	var spots := [Vector2i(18, 20), Vector2i(22, 20), Vector2i(20, 18), Vector2i(20, 22)]
	var p0 = _fighters[0]
	_unit_at.erase(_key(p0.cell))
	p0.cell = Vector2i(20, 20)
	_unit_at[_key(p0.cell)] = 0
	p0.node.position = gw(20, 20)
	p0.pad.position = gw(20, 20, 0.02)
	for bi in range(4, 8):
		var b = _fighters[bi]
		_unit_at.erase(_key(b.cell))
		b.cell = spots[bi - 4]
		_unit_at[_key(b.cell)] = bi
		b.node.position = gw(b.cell.x, b.cell.y)
		b.pad.position = gw(b.cell.x, b.cell.y, 0.02)
		b.ap = 8
	print("TESTBOTS: старт, HP игрока0 = ", p0.hp)
	_end_turn()
	while _busy:
		await get_tree().process_frame
	print("TESTBOTS: конец, HP игрока0 = ", p0.hp, " живых красных = ", _alive_count(0))
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_bots.png")
	print("TESTBOTS_SAVED")
	get_tree().quit()

func _run_testmenu(mobile := false) -> void:
	var sfx := "_mob" if mobile else ""
	await get_tree().process_frame
	# дым-тест чата: локальное эхо с эмодзи + открытая панель эмодзи
	_menu_chat_local[0].append("Вы: проверка эмодзи 😀🔥👍")
	_render_menu_chat()
	if _ui.has("menu_chat_input"):
		_toggle_emoji_panel(_ui.menu_chat_input, _ui.menu_chat_panel)
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_menu%s.png" % sfx)
	_show_menu_squad()
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_squad%s.png" % sfx)
	_show_menu_shop()
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_shop%s.png" % sfx)
	_show_menu_chests()
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_chests%s.png" % sfx)
	_show_menu_profile()
	await RenderingServer.frame_post_draw
	await RenderingServer.frame_post_draw
	get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_profile%s.png" % sfx)
	print("TESTMENU_SAVED")
	get_tree().quit()

func _run_testauth(fname: String) -> void:
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
func _load_sfx() -> void:
	for n in ["shot", "hit", "open", "step", "explosion", "death", "reload", "swap", "levelup", "click", "zone"]:
		var p := "res://assets/sfx/%s.wav" % n
		if ResourceLoader.exists(p):
			_sfx[n] = load(p)

func _ambient_start() -> void:
	# зацикленный ветер пустоши, тихо на фоне
	if not _settings.get("sound", true):
		return
	if not ResourceLoader.exists("res://assets/sfx/wind.wav"):
		return
	var ws: AudioStreamWAV = load("res://assets/sfx/wind.wav")
	ws.loop_mode = AudioStreamWAV.LOOP_FORWARD
	ws.loop_begin = 0
	ws.loop_end = int(ws.get_length() * ws.mix_rate)
	var amb := AudioStreamPlayer.new()
	amb.stream = ws
	amb.volume_db = -18.0
	add_child(amb)
	amb.play()

func _sfx_play(n: String) -> void:
	if not _settings.get("sound", true) or not _sfx.has(n):
		return
	var a := AudioStreamPlayer.new()
	a.stream = _sfx[n]
	a.volume_db = 4.0
	add_child(a)
	a.play()
	a.finished.connect(a.queue_free)

# ============================================================
# ---------------- ГЛАВНОЕ МЕНЮ ----------------
# ============================================================
# ---------- стиль меню: рамки, неон, hover-прожатие ----------
func _style_menu_button(b: Button) -> void:
	b.pressed.connect(_sfx_play.bind("click"))
	var normal := StyleBoxFlat.new()
	normal.bg_color = Color(0.05, 0.08, 0.14, 0.85)
	normal.border_color = Color(0.16, 0.85, 1.0, 0.75)
	normal.set_border_width_all(1)
	normal.set_corner_radius_all(8)
	normal.content_margin_top = 8.0
	# при наводке кнопка «прожимается»: текст смещается вниз, рамка розовеет
	var hover: StyleBoxFlat = normal.duplicate()
	hover.bg_color = Color(0.03, 0.05, 0.10, 0.92)
	hover.border_color = Color(1.0, 0.24, 0.43, 0.95)
	hover.content_margin_top = 11.0
	var pressed: StyleBoxFlat = hover.duplicate()
	pressed.bg_color = Color(0.02, 0.03, 0.07, 0.96)
	pressed.content_margin_top = 13.0
	b.add_theme_stylebox_override("normal", normal)
	b.add_theme_stylebox_override("hover", hover)
	b.add_theme_stylebox_override("pressed", pressed)
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	b.add_theme_color_override("font_color", Color(0.88, 0.94, 1.0))
	b.add_theme_color_override("font_hover_color", Color(1.0, 1.0, 1.0))
	b.add_theme_font_size_override("font_size", 16)

# ---------- иконки предметов: офлайн-рендер из 3D-моделей ----------
const ICON_ALIAS := {"Molotov": "Grenade", "FireGrenade": "Grenade", "knife_1": "Knife_1"}

func _node_aabb(n: Node) -> AABB:
	var out := AABB()
	var first := true
	var meshes: Array = []
	if n is MeshInstance3D:
		meshes.append(n)
	for mi2 in n.find_children("*", "MeshInstance3D", true, false):
		meshes.append(mi2)
	for mi in meshes:
		var a: AABB = (mi as MeshInstance3D).get_global_transform() * (mi as MeshInstance3D).get_aabb()
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
	for wid in ids:
		var node: Node3D = null
		if wid == "medkit":
			node = load(C + "Pickup_Health.gltf").instantiate()
		else:
			var node_name: String = ICON_ALIAS.get(wid, wid)
			if ResourceLoader.exists(GUNS + node_name + ".gltf"):
				node = load(GUNS + node_name + ".gltf").instantiate()
			elif ResourceLoader.exists(GUNS + wid + ".gltf"):
				node = load(GUNS + wid + ".gltf").instantiate()
			else:
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
		var kk: float = 1.15 / mm
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

func _item_tooltip(entry: Dictionary) -> String:
	var it: Dictionary = entry["item"]
	match entry["kind"]:
		"weapon":
			var st := "%s\nУрон: %d" % [it.get("name", "?"), it.get("damage", 0)]
			if int(it.get("burst", 1)) > 1:
				st += " ×%d пули" % int(it["burst"])
			st += "\nОД: %d · Дальность: %d" % [it.get("ap_cost", 0), it.get("range", 0)]
			if it.has("ammo"):
				st += "\nПатроны: %d" % int(it["ammo"])
			if int(it.get("aoe", 0)) > 0:
				st += "\nВзрыв: радиус %d (край 60%%)" % int(it["aoe"])
			if it.get("burn", false):
				st += "\nПоджигает клетки (3 раунда)"
			st += "\nВес: %.1f кг" % _item_weight(entry)
			return st
		"armor":
			var st2 := "%s\nЗащита: %d" % [it.get("name", "?"), it.get("defense", 0)]
			if int(it.get("carry_bonus", 0)) > 0:
				st2 += "\nНосимый вес: +%d кг" % int(it["carry_bonus"])
			st2 += "\nВес: %.1f кг" % _item_weight(entry)
			return st2
		_:
			var st3 := "%s" % it.get("name", "?")
			if it.has("heal"):
				st3 += "\nЛечит: +%d HP" % int(it["heal"])
			if it.has("ap_restore"):
				st3 += "\nВосстанавливает: +%d ОД" % int(it["ap_restore"])
			st3 += "\nОД на использование: %d" % int(it.get("ap_cost", 0))
			st3 += "\nВес: %.1f кг" % _item_weight(entry)
			return st3
	return ""

func _style_bar(bar: ProgressBar, fill_col: Color) -> void:
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
			var dl := Label.new()
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
	var wm := _mat(Color(0.02, 0.02, 0.03), 0.0, 1.0, wcol, 1.7)
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
		q.scale = Vector3.ONE / hnode.scale  # компенсация масштаба дома

func _frame_box() -> StyleBoxFlat:
	# рамочка для текстов лобби
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.03, 0.05, 0.09, 0.92)
	sb.border_color = Color(0.16, 0.85, 1.0, 0.85)
	sb.set_border_width_all(2)
	sb.shadow_color = Color(0.16, 0.85, 1.0, 0.22)
	sb.shadow_size = 6
	sb.set_corner_radius_all(6)
	sb.content_margin_left = 10.0
	sb.content_margin_right = 10.0
	sb.content_margin_top = 5.0
	sb.content_margin_bottom = 5.0
	return sb

func _framed_label(txt: String, fsize := 14) -> PanelContainer:
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", _frame_box())
	var l := Label.new()
	l.text = txt
	l.add_theme_font_size_override("font_size", fsize)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	pc.add_child(l)
	return pc

func _menu_button(txt: String) -> Button:
	var b := Button.new()
	b.text = txt
	b.custom_minimum_size = Vector2(0, 46)
	_style_menu_button(b)
	return b

# ---------- иконки-пиктограммы лобби (SVG, белые силуэты) ----------
func _icon_tex(n: String) -> Texture2D:
	var p := "res://assets/icons/%s.svg" % n
	if ResourceLoader.exists(p):
		return load(p)
	return null

func _icon_chip(n: String, size := 40) -> PanelContainer:
	# тёмная скруглённая подложка с белой пиктограммой
	var pc := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(1, 1, 1, 0.07)
	sb.border_color = Color(1, 1, 1, 0.10)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(10)
	pc.add_theme_stylebox_override("panel", sb)
	pc.custom_minimum_size = Vector2(size + 16, size + 16)
	pc.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var tr := TextureRect.new()
	tr.texture = _icon_tex(n)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.custom_minimum_size = Vector2(size, size)
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if n != "chest":
		tr.modulate = Color(0.88, 0.90, 0.93)
	pc.add_child(tr)
	return pc

func _card_style(hover := false, glow := false) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.08, 0.13, 0.80)
	sb.border_color = Color(1, 1, 1, 0.16)
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(12)
	sb.content_margin_left = 14.0
	sb.content_margin_right = 14.0
	sb.content_margin_top = 12.0
	sb.content_margin_bottom = 12.0
	if hover:
		sb.border_color = Color(0.6, 0.85, 1.0, 0.7)
	if glow:
		sb.border_color = Color(0.45, 0.8, 1.0, 0.85)
		sb.set_border_width_all(2)
		sb.shadow_color = Color(0.35, 0.75, 1.0, 0.35)
		sb.shadow_size = 12
	return sb

func _section_title(t: String) -> HBoxContainer:
	# заголовок секции: белый текст + тонкая линия вправо
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 12)
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", 14)
	l.add_theme_color_override("font_color", Color(1, 1, 1, 0.9))
	hb.add_child(l)
	var line := ColorRect.new()
	line.color = Color(1, 1, 1, 0.18)
	line.custom_minimum_size = Vector2(0, 1)
	line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	line.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hb.add_child(line)
	return hb

func _logo_pulse(logo: CanvasItem) -> void:
	# мигающая ярко-голубая подсветка логотипа
	var tw := logo.create_tween().set_loops()
	tw.tween_property(logo, "modulate", Color(0.55, 1.35, 1.6), 0.7).set_trans(Tween.TRANS_SINE)
	tw.tween_property(logo, "modulate", Color(1, 1, 1), 0.7).set_trans(Tween.TRANS_SINE)

func _chip(icon: String, text: String, tip := "") -> PanelContainer:
	# чип показателя: SVG-иконка + текст (без эмодзи — надёжно в web)
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", _frame_box())
	pc.mouse_filter = Control.MOUSE_FILTER_PASS  # PASS — работает подсказка при наведении
	if tip != "":
		pc.tooltip_text = tip
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 6)
	hb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pc.add_child(hb)
	var tr := TextureRect.new()
	tr.texture = _icon_tex(icon)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	tr.custom_minimum_size = Vector2(16, 16)
	tr.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hb.add_child(tr)
	var l := Label.new()
	l.text = text
	l.add_theme_font_size_override("font_size", 13)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hb.add_child(l)
	return pc

func _mk_label(t: String, fsize := 14) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", fsize)
	return l

func _card_label(t: String, fsize: int, col: Color, bold := false) -> Label:
	var l := Label.new()
	l.text = t
	l.add_theme_font_size_override("font_size", fsize)
	l.add_theme_color_override("font_color", col)
	if bold:
		var fb: FontVariation = _ui.get("font_bold_var")
		if fb == null and ThemeDB.fallback_font != null:
			fb = FontVariation.new()
			fb.base_font = ThemeDB.fallback_font
			fb.variation_embolden = 0.7
			_ui.font_bold_var = fb
		if fb != null:
			l.add_theme_font_override("font", fb)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l

func _fight_card(icon: String, title: String, sub: String, sub_col: Color, locked := false, glow := false) -> Button:
	# крупная карточка режима боя: иконка на подложке + название + подпись
	var b := Button.new()
	b.custom_minimum_size = Vector2(0, 132 if glow else 118)
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.add_theme_stylebox_override("normal", _card_style(false, glow))
	b.add_theme_stylebox_override("hover", _card_style(true, glow))
	b.add_theme_stylebox_override("pressed", _card_style(false, glow))
	b.add_theme_stylebox_override("focus", _card_style(true, glow))
	if locked:
		var ds := _card_style()
		ds.bg_color = Color(0.04, 0.05, 0.08, 0.85)
		ds.border_color = Color(0.5, 0.55, 0.65, 0.5)
		b.add_theme_stylebox_override("disabled", ds)
		b.disabled = true
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 14)
	hb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(hb)
	var chip := _icon_chip("lock" if locked else icon, 52)
	chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hb.add_child(chip)
	var vb2 := VBoxContainer.new()
	vb2.add_theme_constant_override("separation", 4)
	vb2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	vb2.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	hb.add_child(vb2)
	vb2.add_child(_card_label(title, 18, Color(0.55, 0.6, 0.68) if locked else Color.WHITE, true))
	if sub != "":
		vb2.add_child(_card_label(sub, 13, sub_col))
	return b

func _ctrl_button(icon: String, caption: String) -> Button:
	# кнопка раздела: иконка на подложке + подпись снизу
	var b := Button.new()
	b.custom_minimum_size = Vector2(104, 100)
	var n := StyleBoxFlat.new()
	n.bg_color = Color(0, 0, 0, 0)
	n.set_corner_radius_all(10)
	var h := StyleBoxFlat.new()
	h.bg_color = Color(1, 1, 1, 0.08)
	h.set_corner_radius_all(10)
	b.add_theme_stylebox_override("normal", n)
	b.add_theme_stylebox_override("pressed", n)
	b.add_theme_stylebox_override("focus", h)
	b.add_theme_stylebox_override("hover", h)
	var vb2 := VBoxContainer.new()
	vb2.alignment = BoxContainer.ALIGNMENT_CENTER
	vb2.add_theme_constant_override("separation", 6)
	vb2.custom_minimum_size = Vector2(100, 0)
	vb2.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(vb2)
	var chip := _icon_chip(icon, 38)
	chip.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	vb2.add_child(chip)
	var l := _card_label(caption, 11, Color(0.82, 0.85, 0.9))
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb2.add_child(l)
	return b


var _menu_chat_tab := 0
var _menu_chat_collapsed := false
const MENU_CHAT_STUBS := [
	["Система: добро пожаловать в ТОЧКУ СБРОСА: Королевская битва!",
	 "Система: общий чат всех игроков появится в онлайн-режиме.",
	 "Система: пока доступны тренировки 1×1, 2×2 и 4×4 против ботов."],
	["Система: чат комнаты — для общения перед боем с командой.",
	 "Система: появится в онлайн-режиме (комнаты/лобби матчей)."],
	["Система: клановый чат. Создай клан или вступи в существующий —",
	 "Система: кланы появятся в онлайн-режиме вместе с подпиской."],
]

var _menu_chat_local := [[], [], []]  # локальные сообщения игрока (эхо до онлайна)
const MENU_EMOJIS := ["😀", "😂", "😎", "😢", "😡", "🤝", "👍", "👎", "🔥", "💀", "⚡", "🏆", "❤️", "👋", "🎉", "💪"]

func _render_menu_chat() -> void:
	if not _ui.has("menu_chat_lines"):
		return
	for c in _ui.menu_chat_lines.get_children():
		c.queue_free()
	for line in MENU_CHAT_STUBS[_menu_chat_tab]:
		var l := Label.new()
		l.text = line
		l.add_theme_font_size_override("font_size", 12)
		l.modulate = Color(0.7, 0.85, 0.7)
		_ui.menu_chat_lines.add_child(l)
	for line2 in _menu_chat_local[_menu_chat_tab]:
		var l2 := Label.new()
		l2.text = line2
		l2.add_theme_font_size_override("font_size", 12)
		l2.modulate = Color(0.85, 0.95, 1.0)
		_ui.menu_chat_lines.add_child(l2)
	for ti in _ui.menu_chat_btns.size():
		_ui.menu_chat_btns[ti].modulate = Color(1, 1, 1) if ti == _menu_chat_tab else Color(0.55, 0.55, 0.6)

func _menu_chat_send(inp: LineEdit) -> void:
	# локальное эхо: сообщение видно только игроку до появления онлайн-чата
	var t := inp.text.strip_edges()
	if t == "":
		return
	inp.clear()
	_menu_chat_local[_menu_chat_tab].append("Вы: " + t)
	if _menu_chat_local[_menu_chat_tab].size() > 30:
		_menu_chat_local[_menu_chat_tab].pop_front()
	_render_menu_chat()

func _toggle_emoji_panel(inp: LineEdit, host: Control) -> void:
	# панель эмодзи над панелью чата (host); одна на каждый чат
	var key := "emoji_panel_%d" % host.get_instance_id()
	if _ui.has(key):
		_ui[key].visible = not _ui[key].visible
		return
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(288, 0)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.08, 0.13, 0.95)
	sb.set_corner_radius_all(8)
	sb.set_border_width_all(1)
	sb.border_color = Color(0.3, 0.5, 0.6, 0.8)
	p.add_theme_stylebox_override("panel", sb)
	var grid := GridContainer.new()
	grid.columns = 8
	grid.add_theme_constant_override("h_separation", 2)
	grid.add_theme_constant_override("v_separation", 2)
	p.add_child(grid)
	for em in MENU_EMOJIS:
		var eb := Button.new()
		eb.text = em
		eb.custom_minimum_size = Vector2(34, 34)
		eb.add_theme_font_size_override("font_size", 18)
		var e: String = em
		eb.pressed.connect(func():
			inp.insert_text_at_caret(e)
			inp.grab_focus()
		)
		grid.add_child(eb)
	# над чатом: родитель — слой UI (нельзя в PanelContainer — он перезапишет геометрию)
	var par := host.get_parent()
	par.add_child(p)
	p.set_anchors_preset(Control.PRESET_TOP_LEFT)
	var hr := host.get_rect()
	p.position = Vector2(hr.position.x, hr.position.y - 108.0)
	p.size = Vector2(300, 100)
	_ui[key] = p

func _start_mode(m: int) -> void:
	if not _stamina_can_fight():
		var d := AcceptDialog.new()
		d.title = "Выносливость"
		d.dialog_text = "Недостаточно выносливости (бой стоит 15).
Восстанавливается равномерно: 100 за сутки.
Сейчас: %d/100 ⚡" % int(float(_profile.get("stamina", 0.0)))
		_ui.menu_layer.add_child(d)
		d.popup_centered()
		return
	_save_mode(m)
	var cfg := ConfigFile.new()
	cfg.set_value("game", "autostart", 1)
	cfg.save("user://autostart.cfg")
	get_tree().reload_current_scene()

func _build_menu() -> void:
	_menu_open = true
	_busy = true
	var layer := CanvasLayer.new()
	layer.layer = 10
	add_child(layer)
	_ui.menu_layer = layer
	# фон лобби — концепт-арт арены (шоу на выживание)
	var bg := TextureRect.new()
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	if ResourceLoader.exists("res://assets/ui/menu_bg.jpg"):
		bg.texture = load("res://assets/ui/menu_bg.jpg")
	layer.add_child(bg)
	# тёмный градиент поверх арта: тёмно-синий сверху → почти чёрный снизу (стиль PUBG Mobile)
	var grad := Gradient.new()
	grad.set_color(0, Color(0.04, 0.07, 0.14, 0.90))
	grad.set_color(1, Color(0.005, 0.008, 0.02, 0.97))
	var gtex := GradientTexture2D.new()
	gtex.gradient = grad
	gtex.fill_from = Vector2(0.5, 0.0)
	gtex.fill_to = Vector2(0.5, 1.0)
	var dim := TextureRect.new()
	dim.texture = gtex
	dim.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.add_child(dim)
	# --- верхняя панель: лого слева, чипы игрока справа ---
	var mob_w: bool = _vw() < 520.0
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
	logo.custom_minimum_size = Vector2(150, 44) if mob_w else Vector2(280, 72)
	if ResourceLoader.exists("res://assets/ui/logo.png"):
		logo.texture = load("res://assets/ui/logo.png")
	top.add_child(logo)
	_logo_pulse(logo)
	_ui.menu_logo = logo
	var sp := Control.new()
	sp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(sp)
	# чипы: на узком экране переносятся в 2 ряда (FlowContainer)
	var chips := FlowContainer.new()
	chips.add_theme_constant_override("h_separation", 4)
	chips.add_theme_constant_override("v_separation", 4)
	chips.alignment = FlowContainer.ALIGNMENT_END
	chips.custom_minimum_size = Vector2(190, 0) if mob_w else Vector2(0, 0)
	top.add_child(chips)
	_ui.menu_chips = chips
	# --- центральная зона: скролл, чтобы меню влезало на любых экранах ---
	var scroll := ScrollContainer.new()
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.offset_left = 12.0 if mob_w else 24.0
	scroll.offset_right = -12.0 if mob_w else -24.0
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
	if mob_w:
		# на телефоне чат — на всю ширину снизу
		chat.anchor_right = 1.0
		chat.offset_right = -16.0
	else:
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
	var inrow := HBoxContainer.new()
	inrow.add_theme_constant_override("separation", 4)
	content.add_child(inrow)
	var inp := LineEdit.new()
	inp.placeholder_text = "Сообщение… (пока локально)"
	inp.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inp.text_submitted.connect(func(_t): _menu_chat_send(inp))
	inrow.add_child(inp)
	_ui.menu_chat_input = inp
	var emb := Button.new()
	emb.custom_minimum_size = Vector2(36, 30)
	emb.tooltip_text = "Эмодзи"
	var emtr := TextureRect.new()
	emtr.texture = _icon_tex("smile")
	emtr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	emtr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	emtr.custom_minimum_size = Vector2(20, 20)
	emtr.set_anchors_preset(Control.PRESET_CENTER)
	emtr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	emb.add_child(emtr)
	emb.pressed.connect(func(): _toggle_emoji_panel(inp, _ui.menu_chat_panel))
	inrow.add_child(emb)
	var sendb := Button.new()
	sendb.text = "»"
	sendb.custom_minimum_size = Vector2(36, 30)
	sendb.tooltip_text = "Отправить"
	sendb.pressed.connect(func(): _menu_chat_send(inp))
	inrow.add_child(sendb)
	var env := HBoxContainer.new()
	env.add_theme_constant_override("separation", 8)
	env.visible = false
	chat_v.add_child(env)
	_ui.menu_chat_env = env
	var env_icons := ["globe", "swords", "shield"]
	var env_tips := ["Общий чат", "Чат комнаты", "Чат с кланом"]
	for ei in 3:
		var eb := Button.new()
		eb.custom_minimum_size = Vector2(64, 44)
		var etr := TextureRect.new()
		etr.texture = _icon_tex(env_icons[ei])
		etr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		etr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		etr.custom_minimum_size = Vector2(24, 24)
		etr.set_anchors_preset(Control.PRESET_CENTER)
		etr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		eb.add_child(etr)
		eb.tooltip_text = env_tips[ei]
		var en: int = ei
		eb.pressed.connect(func():
			_menu_chat_tab = en
			_toggle_menu_chat()
		)
		env.add_child(eb)
	_render_menu_chat()
	if mob_w:
		# на телефоне чат стартует свёрнутым — не перекрывает меню
		_toggle_menu_chat()
	_show_menu_main()

func _toggle_menu_chat() -> void:
	# свернуть/развернуть чат лобби; в свёрнутом виде — конверты вкладок
	if not _ui.has("menu_chat_panel"):
		return
	_menu_chat_collapsed = not _menu_chat_collapsed
	var p: PanelContainer = _ui.menu_chat_panel
	_ui.menu_chat_content.visible = not _menu_chat_collapsed
	_ui.menu_chat_env.visible = _menu_chat_collapsed
	if _menu_chat_collapsed:
		for ek in _ui.keys():
			if str(ek).begins_with("emoji_panel_"):
				_ui[ek].visible = false
	p.offset_top = -72.0 if _menu_chat_collapsed else -180.0
	_ui.menu_chat_collapse.text = "+" if _menu_chat_collapsed else "—"
	_render_menu_chat()

func _daily_box() -> PanelContainer:
	_daily_check()
	var pc := PanelContainer.new()
	var sb := _card_style()
	sb.bg_color = Color(0.05, 0.08, 0.13, 0.60)
	pc.add_theme_stylebox_override("panel", sb)
	var dvb := VBoxContainer.new()
	dvb.add_theme_constant_override("separation", 8)
	pc.add_child(dvb)
	var q_icons := ["skull", "crate", "trophy"]
	for qi in DAILY_QUESTS.size():
		var q: Dictionary = DAILY_QUESTS[qi]
		var done := int(_profile.daily_claimed[qi]) == 1
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 12)
		dvb.add_child(row)
		var chip := _icon_chip(q_icons[qi] if qi < q_icons.size() else "trophy", 26)
		chip.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(chip)
		var l := Label.new()
		l.text = "%s — %d/%d" % [str(q["name"]), int(_profile.daily_prog[qi]), int(q["need"])]
		l.add_theme_font_size_override("font_size", 13)
		l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		if done:
			l.modulate = Color(0.6, 1.0, 0.6)
		row.add_child(l)
		var rw := Label.new()
		rw.text = "✅" if done else "+%d 💰" % int(q["reward"])
		rw.add_theme_font_size_override("font_size", 13)
		rw.add_theme_color_override("font_color", Color(0.35, 0.95, 0.45))
		rw.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(rw)
	return pc

func _style_locked_button(b: Button) -> void:
	# заблокированный режим — тусклая неон-рамка + серый текст (в стиле лобби)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.07, 0.10, 0.85)
	sb.border_color = Color(0.45, 0.5, 0.6, 0.7)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(8)
	b.add_theme_stylebox_override("disabled", sb)
	b.add_theme_color_override("font_disabled_color", Color(0.65, 0.7, 0.8))

func _show_menu_main() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	# чипы игрока в верхней панели
	if _ui.has("menu_chips"):
		var ch: Control = _ui.menu_chips
		for cc in ch.get_children():
			cc.queue_free()
		ch.add_child(_chip("person", _auth_email if _auth_email != "" else "Гость", "Твой аккаунт. Гость — прогресс только на этом устройстве"))
		_stamina_update()
		ch.add_child(_chip("shop", "%d" % int(_profile.get("coins", 0)), "Монеты — валюта магазина: скины, рамки, цвета ника. Зарабатываются за бои и задания"))
		ch.add_child(_chip("shard", "%d" % int(_profile.get("shards", 0)), "Осколки — редкая валюта из сундуков, для особых наград"))
		ch.add_child(_chip("bolt", "%d/100" % int(float(_profile.get("stamina", 100.0))), "Энергия — тратится на бой, восстанавливается со временем"))
		ch.add_child(_chip("trophy", "%d" % int(_profile.get("wins", 0)), "Победы — открывают слоты бойцов: 2-й на 3 победах, далее 10 и 25"))
		ch.add_child(_chip("skull", "%d" % int(_profile.get("total_kills", 0)), "Всего противников уничтожено"))
	# --- секция БОЙ: три карточки режимов (иконки-пиктограммы) ---
	var wins: int = int(_profile.get("wins", 0))
	var m1 := _fight_card("fighter1", "1×1 · Дуэль", "Соло-тренировка против бота", Color(0.72, 0.78, 0.86), false, true)
	m1.pressed.connect(func(): _start_mode(1))
	var lock2: bool = _profile.unlocked_slots < 2
	var m2 := _fight_card("fighter2", "2×2 · Пара", "Побед %d/%d до слота №2" % [wins, int(SLOT_WINS[2])], Color(1.0, 0.78, 0.28), lock2)
	if not lock2:
		m2.pressed.connect(func(): _start_mode(2))
	var lock4: bool = _profile.unlocked_slots < 4
	var m4 := _fight_card("fighter4", "4×4 · Отряд", "Побед %d/%d до слота №4" % [wins, int(SLOT_WINS[4])], Color(1.0, 0.78, 0.28), lock4)
	if not lock4:
		m4.pressed.connect(func(): _start_mode(4))
	# --- секция УПРАВЛЕНИЕ: горизонтальный ряд иконок ---
	var squad := _ctrl_button("squad", "Отряд")
	squad.pressed.connect(_show_menu_squad)
	var shop := _ctrl_button("shop", "Магазин")
	shop.pressed.connect(_show_menu_shop)
	var chests := _ctrl_button("chest", "Сундуки")
	chests.pressed.connect(_show_menu_chests)
	var bp := _ctrl_button("ticket", "Battle Pass")
	bp.pressed.connect(_show_menu_bp)
	var prof := _ctrl_button("profile", "Личные")
	prof.pressed.connect(_show_menu_profile)
	var sett := _ctrl_button("gear", "Настройки")
	sett.pressed.connect(_show_menu_settings)
	var ctrls: Array = [squad, shop, chests, bp, prof, sett]
	var vw4: float = _vw()
	vb.custom_minimum_size = Vector2(minf(1100.0, vw4 * 0.92) if vw4 >= 980.0 else minf(560.0, vw4 * 0.92), 0)
	vb.add_child(_section_title("БОЙ"))
	if vw4 >= 980.0:
		var brow := HBoxContainer.new()
		brow.add_theme_constant_override("separation", 14)
		vb.add_child(brow)
		brow.add_child(m1)
		brow.add_child(m2)
		brow.add_child(m4)
	else:
		vb.add_child(m1)
		vb.add_child(m2)
		vb.add_child(m4)
	vb.add_child(_section_title("УПРАВЛЕНИЕ"))
	if vw4 >= 980.0:
		var crow := HBoxContainer.new()
		crow.add_theme_constant_override("separation", 10)
		crow.alignment = BoxContainer.ALIGNMENT_CENTER
		vb.add_child(crow)
		for cb in ctrls:
			crow.add_child(cb)
	else:
		var grid := GridContainer.new()
		grid.columns = 3
		grid.add_theme_constant_override("h_separation", 6)
		grid.add_theme_constant_override("v_separation", 6)
		vb.add_child(grid)
		for cb in ctrls:
			grid.add_child(cb)
	vb.add_child(_section_title("ЗАДАНИЯ ДНЯ"))
	vb.add_child(_daily_box())
	# нижние текстовые ссылки — без иконок, белый текст на тёмном фоне
	var links := FlowContainer.new()
	links.alignment = FlowContainer.ALIGNMENT_CENTER
	links.add_theme_constant_override("h_separation", 28)
	links.add_theme_constant_override("v_separation", 4)
	vb.add_child(links)
	for lt in ["Служба поддержки", "Служба помощи", "Помощь новым игрокам"]:
		var lb := Label.new()
		lb.text = lt
		lb.add_theme_font_size_override("font_size", 11)
		lb.add_theme_color_override("font_color", Color(1, 1, 1, 0.5))
		links.add_child(lb)

func _show_menu_settings() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	vb.custom_minimum_size = Vector2(minf(460.0, _vw() * 0.92), 0)
	var t := Label.new()
	t.text = "Настройки"
	t.add_theme_font_size_override("font_size", 30)
	vb.add_child(t)
	var gl := Label.new()
	gl.text = "Графика:"
	vb.add_child(gl)
	var grow := HBoxContainer.new()
	vb.add_child(grow)
	var names := ["Низкая", "Средняя", "Высокая"]
	for i in 3:
		var b := Button.new()
		b.text = names[i] + (" ✓" if _settings.graphics == i else "")
		var lv: int = i
		b.pressed.connect(func():
			_apply_graphics(lv)
			_show_menu_settings()
		)
		grow.add_child(b)
	var srow := HBoxContainer.new()
	vb.add_child(srow)
	var sl := Label.new()
	sl.text = "Звук:"
	srow.add_child(sl)
	var st := Button.new()
	st.text = "Вкл" if _settings.sound else "Выкл"
	st.pressed.connect(func():
		_settings.sound = not _settings.sound
		_show_menu_settings()
	)
	srow.add_child(st)
	var tprow := HBoxContainer.new()
	vb.add_child(tprow)
	var tpl := Label.new()
	tpl.text = "Телепорт: "
	tprow.add_child(tpl)
	for tp in [["beam", "☄ Луч"], ["hole", "🕳 Дыра"], ["storm", "⚡ Шторм"]]:
		var tb2 := Button.new()
		var tid: String = tp[0]
		var ots: Array = _profile.get("owned_teleports", [1, 1, 0])
		var locked := tid == "storm" and (ots.size() < 3 or int(ots[2]) == 0)
		tb2.text = str(tp[1]) + (" ✓" if str(_profile.get("teleport", "beam")) == tid else "")
		tb2.disabled = locked
		if locked:
			tb2.tooltip_text = "Эксклюзив Battle Pass — 30 уровень 1 сезона"
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
	var back := Button.new()
	back.text = "← Назад"
	back.pressed.connect(_show_menu_main)
	vb.add_child(back)

# ---------- экран отряда: создание персонажа + слоты ----------
var _squad_edit := 0            # какого бойца редактируем

func _stat_points_left(st: Dictionary, lvl := 1) -> int:
	var spent := 0
	for k in STAT_KEYS:
		spent += int(st.get(k, 0))
	return STAT_POINTS + 5 * mini(lvl - 1, 4) + 3 * maxi(0, lvl - 5) - spent

const SKIN_NAMES := ["Светлый", "Смуглый", "Тёмный", "Фарфоровый"]
const FRAME_NAMES := ["Стандарт", "Неоновая", "Золотая", "Камуфляж", "Пустыня", "Крипто", "Пламя", "Призрак", "Сиреневая"]
const NICK_COLORS := [Color(1, 1, 1), Color(1, 0.35, 0.45), Color(1, 0.85, 0.3), Color(0.2, 0.9, 0.45), Color(0.5, 0.8, 1.0), Color(0.7, 0.4, 1.0), Color(1.0, 0.55, 0.2), Color(0.85, 0.12, 0.18), Color(1.0, 0.5, 1.0)]
const NICK_COLOR_NAMES := ["Белый", "Красный", "Золотой", "Изумруд", "Ледяной", "Фиолет", "Закат", "Кровавый", "Сиреневый"]

# ---- сундуки шоу: редкости, гаранты (pity), осколки ----
const CHEST_PRICE := 150
const RARITY_NAMES := ["Обычный", "Редкий", "Эпический", "Легендарный", "Мифический", "СИРЕНЕВЫЙ"]
const RARITY_COLORS := [Color(0.72, 0.72, 0.78), Color(0.3, 0.55, 1.0), Color(0.72, 0.35, 1.0), Color(1.0, 0.8, 0.25), Color(1.0, 0.25, 0.3), Color(1.0, 0.5, 1.0)]
const RARITY_SHARD_DUP := [5, 15, 40, 100, 300, 1000]     # осколки за дубликат
const RARITY_EXCHANGE := [80, 200, 500, 1200, 3000, 0]     # цена обмена осколков (сиреневый — только удача)
# шансы: сиреневый 0.1% / мифик 1.9% / лега 5% / эпик 13% / редкий 25% / остальное обычный
const CHEST_POOL := {
	0: [{"kind": "shards", "n": 8, "name": "Осколки ×8"}, {"kind": "coins", "n": 60, "name": "60 💰"},
		{"kind": "frame", "idx": 3, "name": "Рамка «Камуфляж»"}, {"kind": "nick", "idx": 3, "name": "Ник «Изумруд»"}],
	1: [{"kind": "shards", "n": 20, "name": "Осколки ×20"}, {"kind": "coins", "n": 120, "name": "120 💰"},
		{"kind": "frame", "idx": 4, "name": "Рамка «Пустыня»"}, {"kind": "nick", "idx": 4, "name": "Ник «Ледяной»"},
		{"kind": "taunt", "idx": 1, "name": "Пак насмешек «Дерзкие»"}],
	2: [{"kind": "shards", "n": 50, "name": "Осколки ×50"}, {"kind": "frame", "idx": 5, "name": "Рамка «Крипто»"},
		{"kind": "nick", "idx": 5, "name": "Ник «Фиолет»"}, {"kind": "taunt", "idx": 2, "name": "Пак «Философы пустоши»"}],
	3: [{"kind": "shards", "n": 150, "name": "Осколки ×150"}, {"kind": "frame", "idx": 6, "name": "Рамка «Пламя»"},
		{"kind": "nick", "idx": 6, "name": "Ник «Закат»"}],
	4: [{"kind": "shards", "n": 400, "name": "Осколки ×400"}, {"kind": "frame", "idx": 7, "name": "Рамка «Призрак»"},
		{"kind": "nick", "idx": 7, "name": "Ник «Кровавый»"}],
	5: [{"kind": "siren", "idx": 8, "name": "СИРЕНЕВЫЙ НАБОР: рамка + ник"}],
}
const TAUNT_PACK_LINES := {
	1: ["Ты стреляешь как тостер!", "Мой бот стреляет точнее тебя!", "Беги, пока я добрый!", "Это был твой лучший выстрел? Ха!"],
	2: ["Пустошь всё равно заберёт тебя.", "Мы все — лишь шум в эфире.", "Пули — это почтальоны судьбы.", "Твой страх я слышу отсюда."],
}

func _show_menu_squad() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	vb.custom_minimum_size = Vector2(minf(460.0, _vw() * 0.92), 0)
	var t := Label.new()
	t.text = "Отряд — создание бойцов"
	t.add_theme_font_size_override("font_size", 20 if _mob() else 26)
	t.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	vb.add_child(t)
	# вкладки 4 слотов: открыт только первый, остальные — заслуги/подписка
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 4)
	vb.add_child(tabs)
	var slot_w := floorf((_vw() * 0.92 - 30.0) / 4.0) if _mob() else 96.0
	for i in 4:
		var b := Button.new()
		if i < _profile.unlocked_slots:
			b.text = _profile.names[i] + (" ✓" if i == _squad_edit else "")
		else:
			b.text = "🔒 %d" % (i + 1) if _mob() else "🔒 Слот %d" % (i + 1)
		b.custom_minimum_size = Vector2(slot_w, 34)
		b.add_theme_font_size_override("font_size", 12 if _mob() else 14)
		var fi: int = i
		b.pressed.connect(func():
			_squad_edit = fi
			_show_menu_squad()
		)
		tabs.add_child(b)
	if _squad_edit >= _profile.unlocked_slots:
		# закрытый слот — монетизация/прогресс
		var lock := Label.new()
		var need_w: int = int(SLOT_WINS.get(_squad_edit + 1, 25))
		lock.text = "Слот закрыт. Нужно побед: %d (у вас %d)
или месячная подписка (с призами) — скоро." % [need_w, int(_profile.get("wins", 0))]
		lock.add_theme_font_size_override("font_size", 15)
		vb.add_child(lock)
		var back := Button.new()
		back.text = "← Назад"
		back.pressed.connect(_show_menu_main)
		vb.add_child(back)
		return
	# --- никнейм ---
	var nrow := HBoxContainer.new()
	vb.add_child(nrow)
	var nl := Label.new()
	nl.text = "Ник:"
	nrow.add_child(nl)
	var ne := LineEdit.new()
	ne.text = _profile.names[_squad_edit]
	ne.custom_minimum_size = Vector2(200, 0)
	ne.max_length = 16
	ne.text_changed.connect(func(txt: String):
		var clean := txt.strip_edges()
		if clean != "":
			_profile.names[_squad_edit] = clean
			_save_profile()
	)
	nrow.add_child(ne)
	# --- пол и внешность (только для основного бойца, слот 0) ---
	if _squad_edit == 0:
		var grow2 := HBoxContainer.new()
		vb.add_child(grow2)
		var gl := Label.new()
		gl.text = "Пол:"
		grow2.add_child(gl)
		for g in [["m", "Мужчина"], ["f", "Женщина"]]:
			var gb := Button.new()
			gb.text = g[1] + (" ✓" if _profile.gender == g[0] else "")
			var gv: String = g[0]
			gb.pressed.connect(func():
				_profile.gender = gv
				_save_profile()
				_show_menu_squad()
			)
			grow2.add_child(gb)
		var srow := HBoxContainer.new()
		vb.add_child(srow)
		var sl := Label.new()
		sl.text = "Кожа:"
		srow.add_child(sl)
		var SKIN_COLS := [Color(0.96, 0.80, 0.66), Color(0.78, 0.56, 0.38), Color(0.42, 0.28, 0.18), Color(0.98, 0.93, 0.88)]
		for si in SKIN_NAMES.size():
			var sb := Button.new()
			sb.custom_minimum_size = Vector2(30, 30)
			sb.tooltip_text = SKIN_NAMES[si]
			var ss := StyleBoxFlat.new()
			ss.bg_color = SKIN_COLS[si]
			ss.set_corner_radius_all(15)
			if _profile.skin == si:
				ss.border_color = Color(1, 1, 1)
				ss.set_border_width_all(2)
			sb.add_theme_stylebox_override("normal", ss)
			sb.add_theme_stylebox_override("hover", ss)
			sb.add_theme_stylebox_override("pressed", ss)
			sb.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
			var sv: int = si
			sb.pressed.connect(func():
				_profile.skin = sv
				_save_profile()
				_show_menu_squad()
			)
			srow.add_child(sb)
		# цвет ника (монетизация) — 9 цветных квадратов (переносятся на узких экранах)
		var crow := FlowContainer.new()
		crow.add_theme_constant_override("h_separation", 4)
		crow.add_theme_constant_override("v_separation", 4)
		vb.add_child(crow)
		var cl := Label.new()
		cl.text = "Цвет ника:"
		crow.add_child(cl)
		for ci in NICK_COLOR_NAMES.size():
			var cb := Button.new()
			cb.custom_minimum_size = Vector2(26, 26)
			cb.tooltip_text = NICK_COLOR_NAMES[ci]
			var cs := StyleBoxFlat.new()
			cs.bg_color = NICK_COLORS[ci]
			cs.set_corner_radius_all(6)
			if _profile.nick_color == ci:
				cs.border_color = Color(1, 1, 1)
				cs.set_border_width_all(2)
			cb.add_theme_stylebox_override("normal", cs)
			cb.add_theme_stylebox_override("hover", cs)
			cb.add_theme_stylebox_override("pressed", cs)
			cb.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
			if ci > 0 and not _shop_owned("nick_color", ci):
				cb.tooltip_text = NICK_COLOR_NAMES[ci] + " — открывается в магазине или из сундуков"
			var cv: int = ci
			cb.pressed.connect(func():
				if cv == 0 or _shop_owned("nick_color", cv):
					_profile.nick_color = cv
					_save_profile()
					_show_menu_squad()
			)
			crow.add_child(cb)
		# рамка аватара (монетизация) — 9 пресетов сеткой
		vb.add_child(_mk_label("Рамка:", 14))
		var fgrid := GridContainer.new()
		fgrid.columns = 5
		fgrid.add_theme_constant_override("h_separation", 4)
		fgrid.add_theme_constant_override("v_separation", 4)
		vb.add_child(fgrid)
		for fi2 in FRAME_NAMES.size():
			var fb := Button.new()
			fb.text = FRAME_NAMES[fi2] + (" ✓" if _profile.frame == fi2 else "")
			fb.add_theme_font_size_override("font_size", 11)
			fb.custom_minimum_size = Vector2(84, 30)
			if fi2 > 0 and not _shop_owned("frame", fi2):
				fb.tooltip_text = "Открывается в магазине или из сундуков"
			var fv: int = fi2
			fb.pressed.connect(func():
				if fv == 0 or _shop_owned("frame", fv):
					_profile.frame = fv
					_save_profile()
					_show_menu_squad()
			)
			fgrid.add_child(fb)
		var avn := Label.new()
		avn.text = "Аватар: на экране «Личные настройки» (своё фото или 1 из 6 пресетов)"
		avn.add_theme_font_size_override("font_size", 12)
		vb.add_child(avn)
	# --- очки навыков ---
	var st: Dictionary = _profile.stats[_squad_edit]
	var left := _stat_points_left(st, _profile.lvl[_squad_edit])
	var pl := Label.new()
	pl.text = "Уровень %d (опыт %d/%d) · Свободно очков: %d" % [_profile.lvl[_squad_edit], _profile.xp[_squad_edit], _xp_need(_profile.lvl[_squad_edit]), left]
	pl.add_theme_font_size_override("font_size", 17)
	vb.add_child(pl)
	for k in STAT_KEYS:
		var row := HBoxContainer.new()
		vb.add_child(row)
		var lb := Label.new()
		lb.text = "%s: %d" % [STAT_NAMES[k], st[k]]
		lb.custom_minimum_size = Vector2(100, 0) if _mob() else Vector2(160, 0)
		row.add_child(lb)
		var minus := Button.new()
		minus.text = "−"
		minus.disabled = st[k] <= 0
		var kk: String = k
		minus.pressed.connect(func():
			_profile.stats[_squad_edit][kk] -= 1
			_save_profile()
			_show_menu_squad()
		)
		row.add_child(minus)
		var plus := Button.new()
		plus.text = "+"
		plus.disabled = left <= 0
		plus.pressed.connect(func():
			_profile.stats[_squad_edit][kk] += 1
			_save_profile()
			_show_menu_squad()
		)
		row.add_child(plus)
		var hint := Label.new()
		hint.text = "  " + STAT_HINTS[k]
		hint.add_theme_font_size_override("font_size", 10 if _mob() else 12)
		row.add_child(hint)
	var tl2 := Label.new()
	tl2.text = "Таланты — очков: %d (+1 каждые 3 уровня)" % int(_profile.tpts[_squad_edit])
	tl2.add_theme_font_size_override("font_size", 15)
	tl2.add_theme_color_override("font_color", Color(1.0, 0.9, 0.45))
	vb.add_child(tl2)
	var tprof: Dictionary = _profile.talents[_squad_edit]
	for tal in TALENTS:
		var cur := int(tprof.get(tal["id"], 0))
		var trow := HBoxContainer.new()
		vb.add_child(trow)
		var tnl := Label.new()
		tnl.text = "%s %s — %d/%d" % [tal["icon"], tal["name"], cur, int(tal["max"])]
		tnl.custom_minimum_size = Vector2(180 if _mob() else 240, 0)
		tnl.add_theme_font_size_override("font_size", 13)
		tnl.mouse_filter = Control.MOUSE_FILTER_STOP
		tnl.tooltip_text = str(tal["desc"])
		trow.add_child(tnl)
		var tb := Button.new()
		var cost := cur + 1
		if cur >= int(tal["max"]):
			tb.text = "МАКС"
			tb.disabled = true
		else:
			tb.text = "+%d 🎯" % cost
			tb.disabled = int(_profile.tpts[_squad_edit]) < cost
			tb.tooltip_text = "%s\nЦена ранга: %d очк." % [str(tal["desc"]), cost]
			var tid2: String = tal["id"]
			tb.pressed.connect(func():
				var c2 := int(_profile.talents[_squad_edit].get(tid2, 0))
				var price := c2 + 1
				if int(_profile.tpts[_squad_edit]) >= price:
					_profile.tpts[_squad_edit] = int(_profile.tpts[_squad_edit]) - price
					_profile.talents[_squad_edit][tid2] = c2 + 1
					_save_profile()
					_show_menu_squad()
			)
		trow.add_child(tb)
		var tdesc2 := Label.new()
		tdesc2.text = "  " + str(tal["desc"])
		tdesc2.add_theme_font_size_override("font_size", 10 if _mob() else 11)
		tdesc2.add_theme_color_override("font_color", Color(0.65, 0.7, 0.75))
		tdesc2.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		tdesc2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		trow.add_child(tdesc2)
	var spent := 0
	for k3 in tprof.keys():
		var r3 := int(tprof[k3])
		spent += r3 * (r3 + 1) / 2
	if spent > 0:
		var rst := Button.new()
		rst.text = "♻ Сброс талантов — %d 💰 (вернёт %d очк.)" % [TALENT_RESET_COST, spent]
		rst.custom_minimum_size = Vector2(0, 40)
		rst.disabled = int(_profile.get("coins", 0)) < TALENT_RESET_COST
		rst.pressed.connect(func():
			if int(_profile.get("coins", 0)) >= TALENT_RESET_COST:
				_profile.coins = int(_profile.coins) - TALENT_RESET_COST
				_profile.tpts[_squad_edit] = int(_profile.tpts[_squad_edit]) + spent
				_profile.talents[_squad_edit] = {}
				_save_profile()
				_show_menu_squad()
		)
		vb.add_child(rst)
	var sum := Label.new()
	sum.text = "Итог: HP %d · ОД %d · вес %.0f кг · обзор %d" % [
		_stat_hp(st), _stat_ap(st), _stat_carry(st), _stat_vision(st)]
	sum.add_theme_font_size_override("font_size", 15)
	vb.add_child(sum)
	var back := Button.new()
	back.text = "← Назад"
	back.pressed.connect(_show_menu_main)
	vb.add_child(back)

# ---------- личные настройки: аватар, город ----------
# ---------- Battle Pass: сезон 1 ----------
const BP_LEVELS := 30
const BP_XP_PER := 120          # сезонного опыта на уровень

func _bp_level() -> int:
	return mini(BP_LEVELS, int(_profile.get("bp_xp", 0)) / BP_XP_PER)

func _bp_reward_for(lv: int, prem: bool) -> Dictionary:
	# награды каждые 3 уровня; финал 30: free — рамка «Пламя», premium — телепорт «Шторм»
	if lv % 3 != 0:
		return {}
	if prem:
		if lv == BP_LEVELS:
			return {"kind": "teleport", "name": "⚡ Телепорт «Шторм»"}
		return {"kind": "shards", "n": lv * 3, "name": "%d 💠" % (lv * 3)}
	if lv == BP_LEVELS:
		return {"kind": "frame", "idx": 6, "name": "Рамка «Пламя»"}
	if lv % 6 == 0:
		return {"kind": "coins", "n": lv * 2, "name": "%d 💰" % (lv * 2)}
	return {"kind": "shards", "n": lv * 2, "name": "%d 💠" % (lv * 2)}

func _bp_claim(lv: int, prem: bool) -> void:
	if lv > _bp_level():
		return
	if prem and int(_profile.get("bp_owned", 0)) != 1:
		return
	var key := "bp_claimed_prem" if prem else "bp_claimed_free"
	var arr: Array = _profile.get(key, []).duplicate()
	while arr.size() <= BP_LEVELS:
		arr.append(0)
	if int(arr[lv]) == 1:
		return
	var rw := _bp_reward_for(lv, prem)
	match str(rw.get("kind", "")):
		"shards":
			_profile.shards = int(_profile.get("shards", 0)) + int(rw["n"])
		"coins":
			_profile.coins = int(_profile.get("coins", 0)) + int(rw["n"])
		"frame":
			_owned_grant("frame", int(rw["idx"]))
		"teleport":
			var ots: Array = _profile.get("owned_teleports", [1, 1, 0]).duplicate()
			while ots.size() < 3:
				ots.append(0)
			ots[2] = 1
			_profile.owned_teleports = ots
	arr[lv] = 1
	_profile[key] = arr
	_save_profile()

func _show_menu_bp() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	vb.custom_minimum_size = Vector2(minf(620.0, _vw() * 0.95), 0)
	var t := Label.new()
	t.text = "🏅 Battle Pass — сезон 1 «Первый снег»"
	t.add_theme_font_size_override("font_size", 26)
	vb.add_child(t)
	var lvl := _bp_level()
	var cur_xp := int(_profile.get("bp_xp", 0))
	vb.add_child(_framed_label("Уровень %d/%d · сезонный опыт %d (+%d за бой, +5 за убийство, +20 за победу)" % [
		lvl, BP_LEVELS, cur_xp, 5], 13))
	var bar := ProgressBar.new()
	bar.max_value = BP_XP_PER
	bar.value = (0 if lvl >= BP_LEVELS else cur_xp - lvl * BP_XP_PER)
	bar.custom_minimum_size = Vector2(0, 14)
	bar.show_percentage = false
	vb.add_child(bar)
	if int(_profile.get("bp_owned", 0)) != 1:
		var buy := _menu_button("👑 Premium — 399 ₽ (платежи после запуска онлайна)")
		buy.disabled = true
		buy.tooltip_text = "Premium-лента: осколки x1.5 и телепорт «Шторм» на 30 уровне"
		vb.add_child(buy)
	else:
		vb.add_child(_framed_label("👑 Premium активен", 14))
	var grid := GridContainer.new()
	grid.columns = 6
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	vb.add_child(grid)
	var claimed_f: Array = _profile.get("bp_claimed_free", [])
	var claimed_p: Array = _profile.get("bp_claimed_prem", [])
	for lv in range(3, BP_LEVELS + 1, 3):
		var cellp := PanelContainer.new()
		var csb := StyleBoxFlat.new()
		csb.bg_color = Color(0.08, 0.10, 0.14, 0.9)
		csb.border_color = Color(1.0, 0.8, 0.25, 0.9) if lv <= lvl else Color(0.35, 0.38, 0.45, 0.7)
		csb.set_border_width_all(2)
		csb.set_corner_radius_all(6)
		cellp.add_theme_stylebox_override("panel", csb)
		grid.add_child(cellp)
		var cv := VBoxContainer.new()
		cv.add_theme_constant_override("separation", 3)
		cellp.add_child(cv)
		var ll := Label.new()
		ll.text = "Ур. %d" % lv
		ll.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		ll.add_theme_font_size_override("font_size", 12)
		cv.add_child(ll)
		for prem in [false, true]:
			var rw := _bp_reward_for(lv, prem)
			var claimed: Array = claimed_p if prem else claimed_f
			var got := lv < claimed.size() and int(claimed[lv]) == 1
			var rb := Button.new()
			rb.add_theme_font_size_override("font_size", 11)
			rb.custom_minimum_size = Vector2(96, 26)
			rb.text = ("👑 " if prem else "") + str(rw.get("name", ""))
			if got:
				rb.text = "✓"
				rb.disabled = true
			elif lv > lvl or (prem and int(_profile.get("bp_owned", 0)) != 1):
				rb.disabled = true
			else:
				var lv2: int = lv
				var pr2: bool = prem
				rb.pressed.connect(func():
					_bp_claim(lv2, pr2)
					_sfx_play("levelup")
					_show_menu_bp()
				)
			cv.add_child(rb)
	var note := Label.new()
	note.text = "Free-лента бесплатна всем. Premium — косметика и бустеры, без продажи силы."
	note.add_theme_font_size_override("font_size", 12)
	note.add_theme_color_override("font_color", Color(0.6, 0.65, 0.72))
	vb.add_child(note)
	var back := _menu_button("← Назад")
	back.pressed.connect(_show_menu_main)
	vb.add_child(back)

# ---------- сундуки шоу ----------
var _chest_last := ""           # текст последнего дропа
var _chest_last_rarity := -1

func _taunt_lines() -> Array:
	# фразы насмешек: стандарт + открытые паки
	var pool: Array = TAUNT_LINES.duplicate()
	var owned: Array = _profile.get("owned_taunts", [1, 0, 0])
	for pi in TAUNT_PACK_LINES.keys():
		if pi < owned.size() and int(owned[pi]) == 1:
			for ln in TAUNT_PACK_LINES[pi]:
				pool.append(ln)
	return pool

func _owned_grant(kind: String, idx: int) -> bool:
	# выдать косметику; true = уже была (дубликат)
	var key := "owned_frames" if kind == "frame" else ("owned_colors" if kind == "nick" else "owned_taunts")
	var arr: Array = _profile.get(key, [1, 0, 0]).duplicate()
	while arr.size() <= idx:
		arr.append(0)
	if int(arr[idx]) == 1:
		return true
	arr[idx] = 1
	_profile[key] = arr
	return false

func _roll_rarity() -> int:
	# pity: эпик гарантирован на 10-м, легенда на 30-м, мифик на 80-м открытии
	var pity: Array = _profile.get("pity", [0, 0, 0])
	var r := randf() * 100.0
	var res := 0
	if r < 0.1:
		res = 5
	elif r < 2.0:
		res = 4
	elif r < 7.0:
		res = 3
	elif r < 20.0:
		res = 2
	elif r < 45.0:
		res = 1
	if int(pity[2]) >= 79:
		res = maxi(res, 4)
	elif int(pity[1]) >= 29:
		res = maxi(res, 3)
	elif int(pity[0]) >= 9:
		res = maxi(res, 2)
	return res

func _open_show_chest() -> void:
	if int(_profile.get("coins", 0)) < CHEST_PRICE:
		return
	_profile.coins = int(_profile.coins) - CHEST_PRICE
	var rarity := _roll_rarity()
	var pool: Array = CHEST_POOL[rarity]
	var it: Dictionary = pool[randi() % pool.size()]
	var kind := str(it["kind"])
	var dup_shards := 0
	match kind:
		"shards":
			_profile.shards = int(_profile.get("shards", 0)) + int(it["n"])
		"coins":
			_profile.coins = int(_profile.coins) + int(it["n"])
		"siren":
			var d1 := _owned_grant("frame", 8)
			var d2 := _owned_grant("nick", 8)
			if d1 and d2:
				dup_shards = RARITY_SHARD_DUP[5]
		_:
			if _owned_grant(kind, int(it["idx"])):
				dup_shards = RARITY_SHARD_DUP[rarity]
	if dup_shards > 0:
		_profile.shards = int(_profile.get("shards", 0)) + dup_shards
	# pity-счётчики
	var pity: Array = _profile.get("pity", [0, 0, 0]).duplicate()
	for pi in 3:
		pity[pi] = int(pity[pi]) + 1
	if rarity >= 2:
		pity[0] = 0
	if rarity >= 3:
		pity[1] = 0
	if rarity >= 4:
		pity[2] = 0
	_profile.pity = pity
	_profile.chests_total = int(_profile.get("chests_total", 0)) + 1
	_chest_last = str(it["name"]) + ("  (дубликат → +%d 💠)" % dup_shards if dup_shards > 0 else "")
	_chest_last_rarity = rarity
	_save_profile()

func _chest_exchange(kind: String, idx: int, price: int) -> void:
	if int(_profile.get("shards", 0)) < price:
		return
	if not _owned_grant(kind, idx):
		_profile.shards = int(_profile.get("shards", 0)) - price
		_save_profile()

func _show_menu_chests() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	vb.custom_minimum_size = Vector2(minf(520.0, _vw() * 0.94), 0)
	var t := Label.new()
	t.text = "🎁 Сундуки удачи"
	t.add_theme_font_size_override("font_size", 28)
	vb.add_child(t)
	vb.add_child(_framed_label("Баланс: %d 💰  ·  %d 💠 осколков  ·  открыто сундуков: %d" % [
		int(_profile.get("coins", 0)), int(_profile.get("shards", 0)), int(_profile.get("chests_total", 0))], 14))
	var pity: Array = _profile.get("pity", [0, 0, 0])
	# гаранты с тонкими прогресс-барами
	var gbox := VBoxContainer.new()
	gbox.add_theme_constant_override("separation", 4)
	vb.add_child(gbox)
	var gn := ["Эпик", "Легенда", "Мифик"]
	var gn_max := [10, 30, 80]
	for gi in 3:
		var grow3 := HBoxContainer.new()
		grow3.add_theme_constant_override("separation", 8)
		gbox.add_child(grow3)
		var gl2 := _mk_label("%s через %d" % [gn[gi], maxi(1, int(gn_max[gi]) - int(pity[gi]))], 12)
		gl2.custom_minimum_size = Vector2(130, 0)
		gl2.add_theme_color_override("font_color", Color(0.75, 0.8, 0.9))
		grow3.add_child(gl2)
		var pb := ProgressBar.new()
		pb.max_value = gn_max[gi]
		pb.value = clampi(int(pity[gi]), 0, int(gn_max[gi]))
		pb.custom_minimum_size = Vector2(0, 8)
		pb.show_percentage = false
		pb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		pb.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		grow3.add_child(pb)
	if _chest_last != "":
		var rl := Label.new()
		rl.text = "Выпало: " + _chest_last
		rl.add_theme_font_size_override("font_size", 18)
		if _chest_last_rarity >= 0:
			rl.add_theme_color_override("font_color", RARITY_COLORS[_chest_last_rarity])
			var rn := Label.new()
			rn.text = "Редкость: " + RARITY_NAMES[_chest_last_rarity]
			rn.add_theme_font_size_override("font_size", 13)
			rn.add_theme_color_override("font_color", RARITY_COLORS[_chest_last_rarity])
			vb.add_child(rn)
		vb.add_child(rl)
	var ob := _menu_button("📦 Открыть сундук — %d 💰" % CHEST_PRICE)
	ob.custom_minimum_size = Vector2(0, 56)
	# крупная золотая кнопка открытия
	var obs := StyleBoxFlat.new()
	obs.bg_color = Color(0.78, 0.55, 0.10, 0.97)
	obs.border_color = Color(1.0, 0.85, 0.35, 0.95)
	obs.set_border_width_all(2)
	obs.set_corner_radius_all(12)
	ob.add_theme_stylebox_override("normal", obs)
	ob.add_theme_color_override("font_color", Color(0.12, 0.08, 0.02))
	ob.add_theme_font_size_override("font_size", 18)
	ob.disabled = int(_profile.get("coins", 0)) < CHEST_PRICE
	ob.pressed.connect(func():
		_open_show_chest()
		_sfx_play("open")
		_show_menu_chests()
	)
	vb.add_child(ob)
	var leg := Label.new()
	leg.text = "Шансы: обычный 55% · редкий 25% · эпик 13% · лега 5% · мифик 1.9% · СИРЕНЕВЫЙ 0.1%"
	leg.add_theme_font_size_override("font_size", 12)
	leg.add_theme_color_override("font_color", Color(0.6, 0.65, 0.72))
	vb.add_child(leg)
	# обмен осколков: любая косметика из пула (кроме сиреневой)
	vb.add_child(_framed_label("💠 Обмен осколков — точно то, что нужно", 15))
	for r in 5:
		for it in CHEST_POOL[r]:
			var kind := str(it["kind"])
			if kind == "shards" or kind == "coins":
				continue
			var idx := int(it["idx"])
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 8)
			vb.add_child(row)
			var nl := Label.new()
			nl.text = str(it["name"])
			nl.add_theme_font_size_override("font_size", 14)
			nl.add_theme_color_override("font_color", RARITY_COLORS[r])
			nl.custom_minimum_size = Vector2(230, 0)
			row.add_child(nl)
			var eb := Button.new()
			eb.custom_minimum_size = Vector2(140, 34)
			if (kind == "frame" and _shop_owned("frame", idx)) or (kind == "nick" and _shop_owned("nick_color", idx)) or (kind == "taunt" and idx < _profile.get("owned_taunts", []).size() and int(_profile.owned_taunts[idx]) == 1):
				eb.text = "✓ Есть"
				eb.disabled = true
			else:
				eb.text = "%d 💠" % RARITY_EXCHANGE[r]
				eb.disabled = int(_profile.get("shards", 0)) < RARITY_EXCHANGE[r]
				var k2 := kind
				var i2 := idx
				var p2: int = RARITY_EXCHANGE[r]
				eb.pressed.connect(func():
					_chest_exchange(k2, i2, p2)
					_show_menu_chests()
				)
			row.add_child(eb)
	var back := _menu_button("← Назад")
	back.pressed.connect(_show_menu_main)
	vb.add_child(back)

func _show_menu_shop() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	vb.custom_minimum_size = Vector2(minf(460.0, _vw() * 0.92), 0)
	var t := Label.new()
	t.text = "🛒 Магазин"
	t.add_theme_font_size_override("font_size", 28)
	vb.add_child(t)
	vb.add_child(_framed_label("Баланс: %d 💰 — монеты за бои и задания дня" % int(_profile.get("coins", 0)), 15))
	for si in SHOP_ITEMS.size():
		var it: Dictionary = SHOP_ITEMS[si]
		var kind := str(it["kind"])
		var idx := int(it["idx"])
		var price := int(it["price"])
		# карточка товара: превью слева, название, цена и кнопка справа
		var card := PanelContainer.new()
		card.add_theme_stylebox_override("panel", _card_style())
		vb.add_child(card)
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		card.add_child(row)
		# превью: цвет ника — квадрат цвета; рамка — панель с акцентной каймой
		var FRAME_ACCENTS := [Color(0.6, 0.62, 0.66), Color(0.2, 0.9, 1.0), Color(1.0, 0.8, 0.25), Color(0.35, 0.5, 0.25), Color(0.85, 0.7, 0.4), Color(0.2, 1.0, 0.5), Color(1.0, 0.45, 0.1), Color(0.9, 0.9, 0.95), Color(1.0, 0.5, 1.0)]
		var pv := PanelContainer.new()
		pv.custom_minimum_size = Vector2(40, 40)
		var pvs := StyleBoxFlat.new()
		if kind == "nick_color" and idx < NICK_COLORS.size():
			pvs.bg_color = NICK_COLORS[idx]
		else:
			pvs.bg_color = Color(0.1, 0.12, 0.16)
			pvs.border_color = FRAME_ACCENTS[idx] if idx < FRAME_ACCENTS.size() else Color.WHITE
			pvs.set_border_width_all(3)
		pvs.set_corner_radius_all(8)
		pv.add_theme_stylebox_override("panel", pvs)
		pv.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(pv)
		var nl := Label.new()
		nl.text = str(it["name"])
		nl.add_theme_font_size_override("font_size", 15)
		nl.custom_minimum_size = Vector2(0, 0)
		nl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		nl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(nl)
		var b := Button.new()
		b.custom_minimum_size = Vector2(140, 40)
		b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		if _shop_equipped(kind, idx):
			b.text = "✓ Выбрано"
			b.disabled = true
		elif _shop_owned(kind, idx):
			b.text = "Выбрать"
			var k1 := kind
			var i1 := idx
			b.pressed.connect(func():
				_shop_equip(k1, i1)
				_show_menu_shop()
			)
		else:
			b.text = "Купить · %d 💰" % price
			# красная кнопка покупки
			var bs := StyleBoxFlat.new()
			bs.bg_color = Color(0.72, 0.16, 0.20, 0.95)
			bs.border_color = Color(1.0, 0.45, 0.25, 0.9)
			bs.set_border_width_all(1)
			bs.set_corner_radius_all(12)
			b.add_theme_stylebox_override("normal", bs)
			b.add_theme_color_override("font_color", Color.WHITE)
			if int(_profile.get("coins", 0)) < price:
				b.disabled = true
			var s1: int = si
			b.pressed.connect(func():
				_shop_buy(s1)
				_show_menu_shop()
			)
		row.add_child(b)
	var note := Label.new()
	note.text = "Скины бойца и подписка с призами — в онлайн-версии."
	note.add_theme_font_size_override("font_size", 12)
	vb.add_child(note)
	var back := _menu_button("← Назад")
	back.pressed.connect(_show_menu_main)
	vb.add_child(back)

func _show_menu_profile() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	vb.custom_minimum_size = Vector2(minf(460.0, _vw() * 0.92), 0)
	var t := Label.new()
	t.text = "Личные настройки"
	t.add_theme_font_size_override("font_size", 28)
	vb.add_child(t)
	# аватар
	var arow := HBoxContainer.new()
	vb.add_child(arow)
	var av := TextureRect.new()
	av.custom_minimum_size = Vector2(96, 96)
	av.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	av.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	var cur: Texture2D = _avatar_texture()
	if cur:
		av.texture = cur
	arow.add_child(av)
	var ab := Button.new()
	ab.text = "Загрузить фото (аватар)"
	ab.custom_minimum_size = Vector2(230, 44)
	ab.pressed.connect(_pick_avatar)
	arow.add_child(ab)
	# в онлайне аватар подтянется из ЛК ВК / MAX автоматически
	var an := Label.new()
	an.text = "В онлайн-версии фото подтянется из профиля ВК / MAX"
	an.add_theme_font_size_override("font_size", 12)
	vb.add_child(an)
	# 6 пресет-аватаров на выбор
	var pl := Label.new()
	pl.text = "Или выбери пресет:"
	vb.add_child(pl)
	var agrid := HBoxContainer.new()
	agrid.add_theme_constant_override("separation", 6)
	vb.add_child(agrid)
	for pi in 6:
		var pb := Button.new()
		pb.custom_minimum_size = Vector2(58, 58)
		var ptex := _preset_avatar(pi)
		if ptex != null:
			var tr := TextureRect.new()
			tr.texture = ptex
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
			tr.set_anchors_preset(Control.PRESET_FULL_RECT)
			tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
			pb.add_child(tr)
		if _profile.avatar == "" and _profile.avatar_preset == pi + 1:
			pb.text = "✓"
		var pv2: int = pi + 1
		pb.pressed.connect(func():
			_profile.avatar_preset = pv2
			_profile.avatar = ""   # пресет заменяет своё фото
			_save_profile()
			_show_menu_profile()
		)
		agrid.add_child(pb)
	# город
	var crow := HBoxContainer.new()
	vb.add_child(crow)
	var cl := Label.new()
	cl.text = "Город:"
	crow.add_child(cl)
	var ce := LineEdit.new()
	ce.text = _profile.city
	ce.placeholder_text = "Откуда вы, боец?"
	ce.custom_minimum_size = Vector2(240, 0)
	ce.max_length = 32
	ce.text_changed.connect(func(txt: String):
		_profile.city = txt
		_save_profile()
	)
	crow.add_child(ce)
	var note := Label.new()
	note.text = "Ники бойцов меняются на экране «Отряд»"
	note.add_theme_font_size_override("font_size", 12)
	vb.add_child(note)
	var back := Button.new()
	back.text = "← Назад"
	back.pressed.connect(_show_menu_main)
	vb.add_child(back)

func _pick_avatar() -> void:
	# выбор файла через системный диалог (в браузере — загрузка файла)
	DisplayServer.file_dialog_show("Выберите фото", "", "", false,
		DisplayServer.FILE_DIALOG_MODE_OPEN_FILE, ["*.png,*.jpg,*.jpeg ; Изображения"],
		func(ok: bool, paths: PackedStringArray, _filter: int):
			if not ok or paths.is_empty():
				return
			var src := paths[0]
			var img := Image.new()
			if img.load(src) != OK:
				return
			img.resize(mini(img.get_width(), 256), mini(img.get_height(), 256))
			var dst := "user://avatar.png"
			img.save_png(dst)
			_profile.avatar = dst
			_save_profile()
			_show_menu_profile()
	)

func _close_menu() -> void:
	_menu_open = false
	_busy = false
	if _ui.has("menu_layer"):
		_ui.menu_layer.queue_free()
	_apply_graphics(_settings.graphics)
	_update_fog()
	_log("Ваш ход: выберите бойца (ЛКМ или панель сверху). Колесо — зум, ПКМ-тянуть — обзор, I — рюкзак.")

# ============================================================
# ---------------- КАРТОЧКА БОЙЦА (портрет + HP/AP) ----------------
# ============================================================
func _avatar_texture() -> Texture2D:
	# аватар из user://avatar.png/jpg, если игрок загрузил его в личных настройках
	var path: String = _profile.get("avatar", "")
	if path == "" or not FileAccess.file_exists(path):
		return null
	var img := Image.new()
	if img.load(path) != OK:
		return null
	return ImageTexture.create_from_image(img)

func _refresh_card() -> void:
	if _selected < 0 or not _ui.has("card"):
		return
	var f = _fighters[_selected]
	_ui.card.visible = true
	_ui.card_name.text = f.name
	_ui.card_hp.max_value = f.max_hp
	_ui.card_hp.value = f.hp
	var hr: float = float(f.hp) / maxf(1.0, float(f.max_hp))
	var hfill := _ui.card_hp.get_theme_stylebox("fill") as StyleBoxFlat
	if hfill:
		hfill.bg_color = Color(1.0 - hr * 0.8, 0.15 + hr * 0.72, 0.18)
		hfill.shadow_color = Color(1.0 - hr * 0.8, 0.15 + hr * 0.72, 0.18, 0.5)
	_ui.card_hp_l.text = "HP %d/%d" % [f.hp, f.max_hp]
	_ui.card_ap.max_value = f.max_ap
	_ui.card_ap.value = f.ap
	_ui.card_ap_l.text = "ОД %d/%d" % [f.ap, f.max_ap]
	# аватар игрока вместо 3D-портрета (только для своего отряда)
	var ava_tex: Texture2D = _avatar_texture() if f.team == 0 else null
	if ava_tex != null:
		_ui.card_avatar.texture = ava_tex
		_ui.card_avatar.visible = true
		_ui.card_pvc.visible = false
		return
	_ui.card_avatar.visible = false
	_ui.card_pvc.visible = true
	var pv: SubViewport = _ui.card_view
	for c in pv.get_children():
		c.queue_free()
	var model: Node3D = load(H + f.model + ".gltf").instantiate()
	# в портрете оружие не нужно — только голова
	for wname in WEAPON_NODES:
		var wn := model.find_child(wname, true, false)
		if wn and wn is Node3D:
			wn.visible = false
	pv.add_child(model)
	_make_lit(model)
	var ap = model.find_child("AnimationPlayer", true, false)
	if ap and ap.has_animation("Idle_Shoot"):
		ap.play("Idle_Shoot")
	var l := OmniLight3D.new()
	l.position = Vector3(0.6, 2.0, 1.4)
	l.light_energy = 1.6
	pv.add_child(l)
	var bb2 := _node_aabb(model)
	var hh: float = maxf(bb2.size.y, 0.2)
	var head := Vector3(bb2.get_center().x, bb2.end.y - hh * 0.08, bb2.get_center().z)
	var cam := Camera3D.new()
	cam.position = head + Vector3(0.10 * hh, 0.02 * hh, 0.60 * hh)
	cam.fov = 26.0
	pv.add_child(cam)
	cam.look_at(head, Vector3.UP)
	cam.make_current()

# ============================================================
# ---------------- ОКНО ИНВЕНТАРЯ (силуэт + сетка) ----------------
# ============================================================

var _sil_tex: Texture2D = null
func _silhouette_tex() -> Texture2D:
	if _sil_tex:
		return _sil_tex
	var img := Image.create(200, 300, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var c := Color(0.45, 0.6, 0.65, 0.35)
	for y in range(8, 62):  # голова
		for x in range(72, 128):
			if Vector2(x - 100, y - 35).length() < 26:
				img.set_pixel(x, y, c)
	for y in range(66, 168):  # торс-трапеция
		var hw: int = 26 + int((y - 66) * 0.22)
		for x in range(100 - hw, 100 + hw):
			img.set_pixel(x, y, c)
	for y in range(70, 160):  # руки
		for x in range(52, 70):
			img.set_pixel(x, y, c)
		for x in range(130, 148):
			img.set_pixel(x, y, c)
	for y in range(172, 292):  # ноги
		for x in range(74, 96):
			img.set_pixel(x, y, c)
		for x in range(104, 126):
			img.set_pixel(x, y, c)
	_sil_tex = ImageTexture.create_from_image(img)
	return _sil_tex

func _toggle_inventory() -> void:
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
			_ui.fighter_panel.visible = false

func _show_inventory() -> void:
	var f = _fighters[_selected]
	var box: VBoxContainer = _ui.inv_box
	for c in box.get_children():
		c.queue_free()
	var title := Label.new()
	title.text = "Снаряжение: %s" % f.name
	title.add_theme_font_size_override("font_size", 20)
	box.add_child(title)
	if _mob():
		_show_inventory_mobile(f, box)
		_ui.inv_panel.visible = true
		return
	var hb := HBoxContainer.new()
	hb.add_theme_constant_override("separation", 24)
	box.add_child(hb)
	# --- силуэт бойца: слоты экипировки поверх фигуры ---
	var sil := VBoxContainer.new()
	sil.add_theme_constant_override("separation", 6)
	hb.add_child(sil)
	var stats := Label.new()
	stats.text = "HP %d/%d   AP %d/%d\nЗащита: %d\nВес: %.1f/%.1f кг" % [
		f.hp, f.max_hp, f.ap, f.max_ap, _defense(f), _load_weight(f), _carry_limit(f)]
	sil.add_child(stats)
	var fig := Control.new()
	fig.custom_minimum_size = Vector2(240, 330)
	sil.add_child(fig)
	var sil_tex := TextureRect.new()
	sil_tex.texture = _silhouette_tex()
	sil_tex.position = Vector2(20, 0)
	sil_tex.size = Vector2(200, 300)
	fig.add_child(sil_tex)
	# слоты поверх частей тела: шлем — голова, корпус — торс, штаны — ноги
	var slots := [["Шлем", "helmets", Vector2(50, 2)], ["Корпус", "body", Vector2(50, 96)],
		["Штаны", "pants", Vector2(50, 224)]]
	for sd in slots:
		var b := Button.new()
		var it = f.armor[sd[1]]
		b.text = "%s: %s" % [sd[0], it["name"] if it else "—"]
		b.position = sd[2]
		b.custom_minimum_size = Vector2(140, 46)
		var cat: String = sd[1]
		if it:
			var sit := _item_icon({"kind": "armor", "cat": cat, "item": it})
			if sit != null:
				b.icon = sit
				b.add_theme_constant_override("icon_max_width", 30)
			b.tooltip_text = _item_tooltip({"kind": "armor", "cat": cat, "item": it}) + "\n—\nКлик — снять"
		else:
			b.tooltip_text = "Пусто — перетащи броню из рюкзака"
		b.pressed.connect(func(): _unequip(cat))
		# drag&drop: слот принимает только броню своей категории
		b.set_drag_forwarding(Callable(),
			func(_pos: Vector2, data) -> bool:
				return data is Dictionary and data.get("kind") == "armor" and data.get("cat") == cat,
			func(_pos: Vector2, data) -> void:
				_use_backpack(int(data["idx"]))
				if _selected >= 0:
					_show_inventory()
		)
		fig.add_child(b)
	var hands := Button.new()
	hands.text = "Руки: %s" % f.weapon.get("name", "?")
	var hic: Texture2D = _item_icon({"kind": "weapon", "item": f.weapon})
	if hic != null:
		hands.icon = hic
		hands.expand_icon = true
		hands.add_theme_constant_override("icon_max_width", 44)
	hands.position = Vector2(50, 152)
	hands.custom_minimum_size = Vector2(140, 52)
	hands.tooltip_text = _item_tooltip({"kind": "weapon", "item": f.weapon}) + "\n—\nКлик — нож/ствол; перетащить оружие из рюкзака"
	hands.pressed.connect(func():
		_swap_weapon()
		_show_inventory()
	)
	# drag&drop: слот рук принимает оружие
	hands.set_drag_forwarding(Callable(),
		func(_pos: Vector2, data) -> bool:
			return data is Dictionary and data.get("kind") == "weapon",
		func(_pos: Vector2, data) -> void:
			_use_backpack(int(data["idx"]))
			if _selected >= 0:
				_show_inventory()
	)
	fig.add_child(hands)
	var knife := Label.new()
	knife.text = "Нож: всегда при себе"
	sil.add_child(knife)
	# --- сетка рюкзака ---
	var right := VBoxContainer.new()
	hb.add_child(right)
	var bl := Label.new()
	bl.text = "Рюкзак (клик или перетащи на слот):"
	right.add_child(bl)
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	right.add_child(grid)
	for idx in f.backpack.size():
		var b := Button.new()
		b.text = f.backpack[idx]["item"].get("name", "?")
		var bic := _item_icon(f.backpack[idx])
		if bic != null:
			b.icon = bic
			b.expand_icon = true
			b.add_theme_constant_override("icon_max_width", 40)
		b.custom_minimum_size = Vector2(168, 56)
		b.add_theme_font_size_override("font_size", 13)
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.tooltip_text = _item_tooltip(f.backpack[idx]) + "\n—\nКлик — надеть/использовать; перетащить — в слот"
		var i: int = idx
		b.pressed.connect(func():
			_use_backpack(i)
			if _selected >= 0:
				_show_inventory()
		)
		# drag&drop: предмет рюкзака можно тянуть на слоты силуэта
		var kind: String = f.backpack[idx]["kind"]
		var cat2: String = f.backpack[idx].get("cat", "")
		var kb := StyleBoxFlat.new()
		kb.bg_color = Color(0.05, 0.08, 0.12, 0.95)
		kb.set_corner_radius_all(6)
		kb.set_border_width_all(2)
		kb.border_color = {"weapon": Color(1.0, 0.35, 0.35, 0.8), "armor": Color(0.35, 0.7, 1.0, 0.8), "consumable": Color(0.4, 0.95, 0.5, 0.8)}.get(kind, Color(0.6, 0.6, 0.6, 0.8))
		b.add_theme_stylebox_override("normal", kb)
		b.set_drag_forwarding(
			func(_pos: Vector2):
				var prev := Label.new()
				prev.text = b.text
				b.set_drag_preview(prev)
				return {"idx": i, "kind": kind, "cat": cat2},
			Callable(),
			Callable()
		)
		var rowbox := HBoxContainer.new()
		rowbox.add_theme_constant_override("separation", 4)
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rowbox.add_child(b)
		var db := Button.new()
		db.text = "✕"
		db.custom_minimum_size = Vector2(30, 56)
		db.add_theme_color_override("font_color", Color(1.0, 0.45, 0.45))
		db.tooltip_text = "Выбросить на землю"
		var di: int = idx
		db.pressed.connect(func(): _drop_item(di))
		rowbox.add_child(db)
		grid.add_child(rowbox)
	if f.backpack.is_empty():
		var e := Label.new()
		e.text = "(пусто — ищите ящики)"
		grid.add_child(e)
	var close := Button.new()
	close.text = "Закрыть [I]"
	close.pressed.connect(_toggle_inventory)
	box.add_child(close)
	_ui.inv_panel.visible = true

func _show_inventory_mobile(f: Dictionary, box: VBoxContainer) -> void:
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
			b.tooltip_text = _item_tooltip({"kind": "weapon", "item": f.weapon}) + "\n—\nКлик — нож/ствол"
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
				b.tooltip_text = _item_tooltip({"kind": "armor", "cat": cat, "item": it}) + "\n—\nКлик — снять"
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
		var rowbox2 := HBoxContainer.new()
		rowbox2.add_theme_constant_override("separation", 3)
		b2.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		rowbox2.add_child(b2)
		var db2 := Button.new()
		db2.text = "✕"
		db2.custom_minimum_size = Vector2(30, 50)
		db2.add_theme_color_override("font_color", Color(1.0, 0.45, 0.45))
		db2.tooltip_text = "Выбросить на землю"
		var di2: int = idx
		db2.pressed.connect(func(): _drop_item(di2))
		rowbox2.add_child(db2)
		grid.add_child(rowbox2)
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
	if _selected < 0:
		return
	var f = _fighters[_selected]
	var it = f.armor[cat]
	if it == null:
		return
	var entry := {"kind": "armor", "cat": cat, "item": it}
	if _load_weight(f) + _item_weight(entry) > _carry_limit(f):
		_log("Не влезает в рюкзак по весу")
		return
	f.armor[cat] = null
	f.backpack.append(entry)
	_recalc_derived(f)
	_log("%s снял: %s" % [f.name, it["name"]])
	_show_inventory()
	_refresh_fighter_panel()

func _drop_item(idx: int) -> void:
	# выбросить предмет из рюкзака на клетку под бойцом (становится ящиком-лутом)
	if _selected < 0:
		return
	var f = _fighters[_selected]
	if idx < 0 or idx >= f.backpack.size():
		return
	var entry = f.backpack[idx]
	f.backpack.remove_at(idx)
	# кладём на ближайшую свободную соседнюю клетку (на своей — иначе ящик не открыть)
	var target: Vector2i = f.cell
	for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
		var n: Vector2i = f.cell + d
		if n.x < 0 or n.y < 0 or n.x >= _grid_n or n.y >= _grid_n:
			continue
		var nk := _key(n)
		if not _occupied.has(nk) and not _unit_at.has(nk):
			target = n
			break
	var key := _key(target)
	if not _chests.has(key):
		_chests[key] = []
		_place(C + "Lootbox.gltf", gw(target.x, target.y), _rng.randf() * 360.0, 0.7)
	_chests[key].append(entry)
	_log("%s выбросил: %s" % [f.name, entry["item"].get("name", "?")])
	_recalc_derived(f)
	_refresh_fighter_panel()
	_show_inventory()

# ---------- сужающаяся зона (королевская битва) ----------
func _in_zone(c: Vector2i) -> bool:
	return c.x >= _zone_min.x and c.x <= _zone_max.x and c.y >= _zone_min.y and c.y <= _zone_max.y

func _update_zone_walls() -> void:
	if _zone_walls.is_empty():
		for i in 4:
			var w := MeshInstance3D.new()
			w.mesh = BoxMesh.new()
			var m := _mat(Color(1.0, 0.12, 0.22, 0.28), 0.0, 1.0, Color(1.0, 0.12, 0.22), 1.6)
			m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			w.material_override = m
			add_child(w)
			_zone_walls.append(w)
	var p0: Vector3 = gw(_zone_min.x, _zone_min.y) - Vector3(CELL * 0.5, 0, CELL * 0.5)
	var p1: Vector3 = gw(_zone_max.x, _zone_max.y) + Vector3(CELL * 0.5, 0, CELL * 0.5)
	var h := 2.4
	var t := 0.12
	var midx: float = (p0.x + p1.x) * 0.5
	var midz: float = (p0.z + p1.z) * 0.5
	var sizes := [Vector3(p1.x - p0.x, h, t), Vector3(p1.x - p0.x, h, t), Vector3(t, h, p1.z - p0.z), Vector3(t, h, p1.z - p0.z)]
	var poss := [Vector3(midx, h * 0.5, p0.z), Vector3(midx, h * 0.5, p1.z), Vector3(p0.x, h * 0.5, midz), Vector3(p1.x, h * 0.5, midz)]
	for i in 4:
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

func _tick_zone() -> void:
	# сужение каждый 2-й раунд начиная с 3-го; снаружи — нарастающий урон
	if _turn >= 3 and _turn % 2 == 1 and _zone_max.x - _zone_min.x > 6:
		_zone_min += Vector2i(1, 1)
		_zone_max -= Vector2i(1, 1)
		_zone_phase += 1
		_update_zone_walls()
		_sfx_play("zone")
		_log("ЗОНА СУЖАЕТСЯ! Снаружи — урон каждый раунд")
	if _zone_phase == 0:
		return
	var dmg := 4 + 2 * _zone_phase
	for fi in _fighters.size():
		var f = _fighters[fi]
		if f.alive and not _in_zone(f.cell):
			_log("%s вне зоны! -%d HP" % [f.name, dmg])
			_apply_damage(fi, dmg, "Зона", -1)
			if _game_over:
				return

# ============================================================
# ---------------- ТУМАН ВОЙНЫ ----------------
# ============================================================
func _los(a: Vector2i, b: Vector2i) -> bool:
	# линия видимости по клеткам (Брезенхэм); блокируют дома и тяжёлые укрытия
	# дома: снаружи внутрь (и обратно) стрелять нельзя; внутри одного дома — можно
	var ha := _house_of(a)
	var hb := _house_of(b)
	if ha != hb:
		return false
	if ha >= 0:
		return true
	var x0: int = a.x
	var y0: int = a.y
	var x1: int = b.x
	var y1: int = b.y
	var dx: int = absi(x1 - x0)
	var dy: int = -absi(y1 - y0)
	var sx: int = 1 if x0 < x1 else -1
	var sy: int = 1 if y0 < y1 else -1
	var err: int = dx + dy
	var x := x0
	var y := y0
	while true:
		if x == x1 and y == y1:
			return true
		if not (x == x0 and y == y0) and _blocks_sight.has("%d,%d" % [x, y]):
			return false
		var e2 := 2 * err
		if e2 >= dy:
			err += dy
			x += sx
		if e2 <= dx:
			err += dx
			y += sy
	return true

func _update_fog() -> void:
	for ef in _fighters:
		if ef.team != 1:
			continue
		var vis := true
		if ef.alive:
			vis = false
			for pf in _fighters:
				if pf.team != 0 or not pf.alive:
					continue
				var d := Vector2(pf.cell.x - ef.cell.x, pf.cell.y - ef.cell.y).length()
				var vis_r: int = pf.get("vision", VISION)
				if d <= vis_r and _los(pf.cell, ef.cell):
					vis = true
					break
		ef.node.visible = vis
		ef.pad.visible = vis
	_update_house_fade()
