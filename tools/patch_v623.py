# v6.23 — магазин скинов за монеты: рамки аватара, цвета ника
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) товары магазина + функции покупки/выбора (после блока заданий дня)
rep("""var _chests_opened := 0       # ящиков открыто игроком за текущий бой""",
"""var _chests_opened := 0       # ящиков открыто игроком за текущий бой
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
	_save_profile()""")

# 2) дефолты профиля
rep("""		"daily_claimed": [0, 0, 0], # награды получены""",
"""		"daily_claimed": [0, 0, 0], # награды получены
		"owned_frames": [1, 0, 0],    # купленные рамки (0 стандарт — всегда есть)
		"owned_colors": [1, 0, 0],    # купленные цвета ника""")

# 3) загрузка
rep("""	_profile.daily_claimed = cfg.get_value("player", "daily_claimed", [0, 0, 0])
	_daily_check()""",
"""	_profile.daily_claimed = cfg.get_value("player", "daily_claimed", [0, 0, 0])
	_profile.owned_frames = cfg.get_value("player", "owned_frames", [1, 0, 0])
	_profile.owned_colors = cfg.get_value("player", "owned_colors", [1, 0, 0])
	_daily_check()""")

# 4) сохранение
rep("""	cfg.set_value("player", "daily_claimed", _profile.get("daily_claimed", [0, 0, 0]))
	cfg.save("user://profile.cfg")""",
"""	cfg.set_value("player", "daily_claimed", _profile.get("daily_claimed", [0, 0, 0]))
	cfg.set_value("player", "owned_frames", _profile.get("owned_frames", [1, 0, 0]))
	cfg.set_value("player", "owned_colors", _profile.get("owned_colors", [1, 0, 0]))
	cfg.save("user://profile.cfg")""")

# 5) кнопка магазина в главном меню
rep("""	var squad := _menu_button("Отряд: создание бойца, навыки, слоты")
	squad.pressed.connect(_show_menu_squad)
	vb.add_child(squad)""",
"""	var squad := _menu_button("Отряд: создание бойца, навыки, слоты")
	squad.pressed.connect(_show_menu_squad)
	vb.add_child(squad)
	var shop := _menu_button("🛒 Магазин: рамки и цвета ника (за монеты)")
	shop.pressed.connect(_show_menu_shop)
	vb.add_child(shop)""")

# 6) экран магазина (перед экраном профиля)
rep("""func _show_menu_profile() -> void:""",
"""func _show_menu_shop() -> void:
	var vb: VBoxContainer = _ui.menu_box
	for c in vb.get_children():
		c.queue_free()
	var t := Label.new()
	t.text = "🛒 Магазин"
	t.add_theme_font_size_override("font_size", 28)
	vb.add_child(t)
	vb.add_child(_framed_label("Баланс: %d 🪙 — монеты за бои и задания дня" % int(_profile.get("coins", 0)), 15))
	for si in SHOP_ITEMS.size():
		var it: Dictionary = SHOP_ITEMS[si]
		var kind := str(it["kind"])
		var idx := int(it["idx"])
		var price := int(it["price"])
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		vb.add_child(row)
		var nl := Label.new()
		nl.text = str(it["name"])
		nl.add_theme_font_size_override("font_size", 16)
		nl.custom_minimum_size = Vector2(220, 0)
		row.add_child(nl)
		var b := Button.new()
		b.custom_minimum_size = Vector2(150, 40)
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
			b.text = "Купить: %d 🪙" % price
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

func _show_menu_profile() -> void:""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.23")
