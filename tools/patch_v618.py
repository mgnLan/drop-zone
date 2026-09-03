# v6.18 — онбординг первого боя: 4 подсказки с пульсирующей подсветкой
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) переменные и тексты обучения (перед _ready)
rep("""# ---------- мобильный UI: автомасштаб интерфейса ----------""",
"""# ---------- онбординг первого боя ----------
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
	hb.offset_left = -280.0
	hb.offset_right = 280.0
	hb.offset_top = 10.0
	hb.offset_bottom = 62.0
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

# ---------- мобильный UI: автомасштаб интерфейса ----------""")

# 2) поле onboarded в профиле: дефолт, загрузка, сохранение
rep("""		"unlocked_slots": 1,      # стартовый игрок: 1 слот; остальные — заслуги/подписка""",
"""		"unlocked_slots": 1,      # стартовый игрок: 1 слот; остальные — заслуги/подписка
		"onboarded": 0,           # 1 = обучение первого боя пройдено""")
rep("""	_profile.unlocked_slots = int(cfg.get_value("player", "unlocked_slots", 1))
""",
"""	_profile.unlocked_slots = int(cfg.get_value("player", "unlocked_slots", 1))
	_profile.onboarded = int(cfg.get_value("player", "onboarded", 0))
""")
rep("""	cfg.set_value("player", "unlocked_slots", _profile.unlocked_slots)
	cfg.save("user://profile.cfg")""",
"""	cfg.set_value("player", "unlocked_slots", _profile.unlocked_slots)
	cfg.set_value("player", "onboarded", int(_profile.get("onboarded", 0)))
	cfg.save("user://profile.cfg")""")

# 3) запуск обучения при старте боя (автостарт из меню)
rep("""		_log("Тренировка %d×%d — ваш ход! ЛКМ — бойцы, ПКМ-тянуть — обзор." % [_mode, _mode])""",
"""		_log("Тренировка %d×%d — ваш ход! ЛКМ — бойцы, ПКМ-тянуть — обзор." % [_mode, _mode])
		_onboard_start()""")

# 4) ссылка на кнопку «Конец хода» для подсветки
rep("""	btn.pressed.connect(_end_turn)
	btn.pressed.connect(_sfx_play.bind("click"))
	layer.add_child(btn)""",
"""	btn.pressed.connect(_end_turn)
	btn.pressed.connect(_sfx_play.bind("click"))
	layer.add_child(btn)
	_ui.end_btn = btn""")

# 5) пульсация подсветки в _process
rep("""func _process(delta: float) -> void:""",
"""func _process(delta: float) -> void:
	if _onboard_pulse != null and is_instance_valid(_onboard_pulse):
		_pulse_t += delta
		var s := 0.75 + 0.25 * sin(_pulse_t * 6.0)
		_onboard_pulse.modulate = Color(s, s, 0.6 * s)""")

# 6) шаг 1 пройден — выбор своего бойца
rep("""func _select(i: int) -> void:
	_selected = i""",
"""func _select(i: int) -> void:
	if _onboard_step == 0 and _fighters[i].team == 0:
		_onboard_next()
	_selected = i""")

# 7) шаг 2 — перемещение; шаг 3 — выстрел (в _click_left)
rep("""	elif _reach.has(cell):
		var f = _fighters[_selected]
		var path := _path_to(f.cell, cell)
		f.ap -= _reach[cell]
		_move_fighter(_selected, cell, path)
		_after_action()""",
"""	elif _reach.has(cell):
		var f = _fighters[_selected]
		var path := _path_to(f.cell, cell)
		f.ap -= _reach[cell]
		_move_fighter(_selected, cell, path)
		if _onboard_step == 1:
			_onboard_next()
		_after_action()""")
rep("""		elif _selected >= 0:
			_shoot(_selected, fi)
			_after_action()""",
"""		elif _selected >= 0:
			_shoot(_selected, fi)
			if _onboard_step == 2:
				_onboard_next()
			_after_action()""")

# 8) шаг 4 — конец хода завершает обучение
rep("""func _end_turn() -> void:
	if _busy or _game_over or _lvl_open:
		return""",
"""func _end_turn() -> void:
	if _busy or _game_over or _lvl_open:
		return
	if _onboard_step == 3:
		_onboard_finish()""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.18")
