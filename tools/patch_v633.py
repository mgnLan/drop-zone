# -*- coding: utf-8 -*-
# v6.33: сундуки шоу — 6 редкостей, pity 10/30/80, осколки, обмен, паки насмешек
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

# ---- 1. Расширение каталогов косметики + данные сундуков ----
rep("""const FRAME_NAMES := ["Стандарт", "Неоновая 🔒", "Золотая 🔒"]
const NICK_COLORS := [Color(1, 1, 1), Color(1, 0.35, 0.45), Color(1, 0.85, 0.3)]
const NICK_COLOR_NAMES := ["Белый", "Красный 🔒", "Золотой 🔒"]
""", """const FRAME_NAMES := ["Стандарт", "Неоновая", "Золотая", "Камуфляж", "Пустыня", "Крипто", "Пламя", "Призрак", "Сиреневая"]
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
	0: [{"kind": "shards", "n": 8, "name": "Осколки ×8"}, {"kind": "coins", "n": 60, "name": "60 🪙"},
		{"kind": "frame", "idx": 3, "name": "Рамка «Камуфляж»"}, {"kind": "nick", "idx": 3, "name": "Ник «Изумруд»"}],
	1: [{"kind": "shards", "n": 20, "name": "Осколки ×20"}, {"kind": "coins", "n": 120, "name": "120 🪙"},
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
""")

# ---- 2. Поля профиля ----
rep("""		"owned_colors": [1, 0, 0],    # купленные цвета ника
""", """		"owned_colors": [1, 0, 0],    # купленные цвета ника
		"owned_taunts": [1, 0, 0],    # паки насмешек (0 стандартный)
		"shards": 0,                  # осколки (валюта обмена за дубликаты)
		"pity": [0, 0, 0],            # открытий без эпика/легенды/мифика
		"chests_total": 0,            # сундуков открыто всего
""")
rep("""	_profile.owned_colors = cfg.get_value("player", "owned_colors", [1, 0, 0])
""", """	_profile.owned_colors = cfg.get_value("player", "owned_colors", [1, 0, 0])
	_profile.owned_taunts = cfg.get_value("player", "owned_taunts", [1, 0, 0])
	_profile.shards = int(cfg.get_value("player", "shards", 0))
	_profile.pity = cfg.get_value("player", "pity", [0, 0, 0])
	_profile.chests_total = int(cfg.get_value("player", "chests_total", 0))
""")
rep("""	cfg.set_value("player", "owned_colors", _profile.get("owned_colors", [1, 0, 0]))
""", """	cfg.set_value("player", "owned_colors", _profile.get("owned_colors", [1, 0, 0]))
	cfg.set_value("player", "owned_taunts", _profile.get("owned_taunts", [1, 0, 0]))
	cfg.set_value("player", "shards", int(_profile.get("shards", 0)))
	cfg.set_value("player", "pity", _profile.get("pity", [0, 0, 0]))
	cfg.set_value("player", "chests_total", int(_profile.get("chests_total", 0)))
""")

# ---- 3. Выбор косметики в отряде: разрешить выбранное из сундуков ----
rep("""			if ci > 0:
				cb.tooltip_text = "Откроется за донат/подписку"
			var cv: int = ci
			cb.pressed.connect(func():
				if cv == 0:
					_profile.nick_color = cv
					_save_profile()
					_show_menu_squad()
			)
""", """			if ci > 0 and not _shop_owned("nick_color", ci):
				cb.tooltip_text = "Открывается в магазине или из сундуков"
			var cv: int = ci
			cb.pressed.connect(func():
				if cv == 0 or _shop_owned("nick_color", cv):
					_profile.nick_color = cv
					_save_profile()
					_show_menu_squad()
			)
""")
rep("""			if fi2 > 0:
				fb.tooltip_text = "Откроется за донат/подписку"
			var fv: int = fi2
			fb.pressed.connect(func():
				if fv == 0:
					_profile.frame = fv
					_save_profile()
					_show_menu_squad()
			)
""", """			if fi2 > 0 and not _shop_owned("frame", fi2):
				fb.tooltip_text = "Открывается в магазине или из сундуков"
			var fv: int = fi2
			fb.pressed.connect(func():
				if fv == 0 or _shop_owned("frame", fv):
					_profile.frame = fv
					_save_profile()
					_show_menu_squad()
			)
""")

# ---- 4. Кнопка сундуков в главном меню + чип осколков ----
rep("""		ch.add_child(_framed_label("🪙 %d" % int(_profile.get("coins", 0)), 13))
""", """		ch.add_child(_framed_label("🪙 %d" % int(_profile.get("coins", 0)), 13))
		ch.add_child(_framed_label("💠 %d" % int(_profile.get("shards", 0)), 13))
""")
rep("""	var shop := _menu_button("🛒 Магазин: рамки и цвет ника")
	shop.pressed.connect(_show_menu_shop)
""", """	var shop := _menu_button("🛒 Магазин: рамки и цвет ника")
	shop.pressed.connect(_show_menu_shop)
	var chests := _menu_button("🎁 Сундуки: удача, редкости, осколки")
	chests.pressed.connect(_show_menu_chests)
""")
rep("""		c2.add_child(shop)
""", """		c2.add_child(shop)
		c2.add_child(chests)
""")
rep("""		vb.add_child(shop)
""", """		vb.add_child(shop)
		vb.add_child(chests)
""")

# ---- 5. Насмешки из открытых паков ----
rep("""	var line: String = TAUNT_LINES[_rng.randi() % TAUNT_LINES.size()]
""", """	var pool := _taunt_lines()
	var line: String = pool[_rng.randi() % pool.size()]
""")

# ---- 6. Логика сундуков + экран (перед магазином) ----
rep("""func _show_menu_shop() -> void:
""", """# ---------- сундуки шоу ----------
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

func _open_chest() -> void:
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
	vb.custom_minimum_size = Vector2(minf(520.0, get_viewport().get_visible_rect().size.x * 0.94), 0)
	var t := Label.new()
	t.text = "🎁 Сундуки удачи"
	t.add_theme_font_size_override("font_size", 28)
	vb.add_child(t)
	vb.add_child(_framed_label("Баланс: %d 🪙  ·  %d 💠 осколков  ·  открыто сундуков: %d" % [
		int(_profile.get("coins", 0)), int(_profile.get("shards", 0)), int(_profile.get("chests_total", 0))], 14))
	var pity: Array = _profile.get("pity", [0, 0, 0])
	var pl := Label.new()
	pl.text = "Гаранты: эпик через %d · легенда через %d · мифик через %d" % [
		maxi(1, 10 - int(pity[0])), maxi(1, 30 - int(pity[1])), maxi(1, 80 - int(pity[2]))]
	pl.add_theme_font_size_override("font_size", 13)
	pl.add_theme_color_override("font_color", Color(0.75, 0.8, 0.9))
	vb.add_child(pl)
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
	var ob := _menu_button("📦 Открыть сундук — %d 🪙" % CHEST_PRICE)
	ob.disabled = int(_profile.get("coins", 0)) < CHEST_PRICE
	ob.pressed.connect(func():
		_open_chest()
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
""")

io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ALL_OK v6.33")
