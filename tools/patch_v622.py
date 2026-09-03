# v6.22 — ежедневные задания: 3 шт/день, награда монетами, блок в лобби
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) константы заданий + счётчик ящиков за бой
rep("""const SLOT_WINS := {2: 3, 3: 10, 4: 25}   # слот -> сколько побед нужно""",
"""const SLOT_WINS := {2: 3, 3: 10, 4: 25}   # слот -> сколько побед нужно
const DAILY_QUESTS := [
	{"name": "Убей 5 противников", "need": 5, "reward": 50},
	{"name": "Открой 3 ящика", "need": 3, "reward": 40},
	{"name": "Выиграй бой", "need": 1, "reward": 75},
]
var _chests_opened := 0       # ящиков открыто игроком за текущий бой

func _daily_check() -> void:
	var today := Time.get_date_string_from_system()
	if str(_profile.get("daily_date", "")) != today:
		_profile.daily_date = today
		_profile.daily_prog = [0, 0, 0]
		_profile.daily_claimed = [0, 0, 0]

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
		msgs.append("📅 Задание дня «%s» — +%d 🪙" % [str(DAILY_QUESTS[qi]["name"]), int(DAILY_QUESTS[qi]["reward"])])
	return msgs""")

# 2) дефолты профиля
rep("""		"total_kills": 0,         # убийств всего""",
"""		"total_kills": 0,         # убийств всего
		"daily_date": "",           # дата текущих ежедневных заданий
		"daily_prog": [0, 0, 0],    # прогресс по 3 заданиям
		"daily_claimed": [0, 0, 0], # награды получены""")

# 3) загрузка
rep("""	_profile.total_kills = int(cfg.get_value("player", "total_kills", 0))""",
"""	_profile.total_kills = int(cfg.get_value("player", "total_kills", 0))
	_profile.daily_date = str(cfg.get_value("player", "daily_date", ""))
	_profile.daily_prog = cfg.get_value("player", "daily_prog", [0, 0, 0])
	_profile.daily_claimed = cfg.get_value("player", "daily_claimed", [0, 0, 0])
	_daily_check()""")

# 4) сохранение
rep("""	cfg.set_value("player", "total_kills", int(_profile.get("total_kills", 0)))
	cfg.save("user://profile.cfg")""",
"""	cfg.set_value("player", "total_kills", int(_profile.get("total_kills", 0)))
	cfg.set_value("player", "daily_date", str(_profile.get("daily_date", "")))
	cfg.set_value("player", "daily_prog", _profile.get("daily_prog", [0, 0, 0]))
	cfg.set_value("player", "daily_claimed", _profile.get("daily_claimed", [0, 0, 0]))
	cfg.save("user://profile.cfg")""")

# 5) счётчик открытых ящиков (только команда игрока)
rep("""	f.ap -= OPEN_CHEST_AP
	_face_cell(f, cell)""",
"""	f.ap -= OPEN_CHEST_AP
	if f.team == 0:
		_chests_opened += 1
	_face_cell(f, cell)""")

# 6) прогресс заданий в конце боя
rep("""		_battle_reward = {"coins": reward, "kills": p_kills, "win": win, "unlock": unlock_msg}
		_save_profile()""",
"""		var daily_msgs: Array = _daily_add(0, p_kills)
		daily_msgs.append_array(_daily_add(1, _chests_opened))
		if win:
			daily_msgs.append_array(_daily_add(2, 1))
		_battle_reward = {"coins": reward, "kills": p_kills, "win": win, "unlock": unlock_msg, "daily": daily_msgs}
		_save_profile()""")

# 7) строки заданий на экране итогов
rep("""				if str(_battle_reward.get("unlock", "")) != "":
					var ul := Label.new()
					ul.text = str(_battle_reward.unlock)
					ul.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
					ul.add_theme_font_size_override("font_size", 16)
					ul.add_theme_color_override("font_color", Color(0.5, 1.0, 0.6))
					vb.add_child(ul)""",
"""				if str(_battle_reward.get("unlock", "")) != "":
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
					vb.add_child(dl)""")

# 8) блок заданий дня в лобби
rep("""	vb.add_child(_framed_label("🪙 Монеты: %d · Побед: %d · Убийств: %d" % [
		int(_profile.get("coins", 0)), int(_profile.get("wins", 0)), int(_profile.get("total_kills", 0))], 16))""",
"""	vb.add_child(_framed_label("🪙 Монеты: %d · Побед: %d · Убийств: %d" % [
		int(_profile.get("coins", 0)), int(_profile.get("wins", 0)), int(_profile.get("total_kills", 0))], 16))
	vb.add_child(_daily_box())""")

# 9) функция блока заданий (перед _show_menu_main)
rep("""func _show_menu_main() -> void:""",
"""func _daily_box() -> PanelContainer:
	_daily_check()
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", _frame_box())
	var dvb := VBoxContainer.new()
	pc.add_child(dvb)
	var t := Label.new()
	t.text = "📅 Задания дня:"
	t.add_theme_font_size_override("font_size", 14)
	dvb.add_child(t)
	for qi in DAILY_QUESTS.size():
		var q: Dictionary = DAILY_QUESTS[qi]
		var done := int(_profile.daily_claimed[qi]) == 1
		var l := Label.new()
		l.text = "%s %s — %d/%d (+%d 🪙)" % [
			"✅" if done else "▫", str(q["name"]),
			int(_profile.daily_prog[qi]), int(q["need"]), int(q["reward"])]
		l.add_theme_font_size_override("font_size", 12)
		if done:
			l.modulate = Color(0.6, 1.0, 0.6)
		dvb.add_child(l)
	return pc

func _show_menu_main() -> void:""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.22")
