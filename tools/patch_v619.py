# v6.19+v6.20 — монеты за бой, копилка в профиле, слоты бойцов за заслуги
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) пороги открытия слотов + переменная награды за бой
rep("""const STAT_POINTS := 5        # очков на распределение каждому бойцу""",
"""const STAT_POINTS := 5        # очков на распределение каждому бойцу
const SLOT_WINS := {2: 3, 3: 10, 4: 25}   # слот -> сколько побед нужно
var _battle_reward := {}      # итоги последнего боя для экрана победы""")

# 2) поля профиля: дефолт
rep("""		"onboarded": 0,           # 1 = обучение первого боя пройдено""",
"""		"onboarded": 0,           # 1 = обучение первого боя пройдено
		"coins": 0,               # копилка монет (монетизация)
		"wins": 0,                # побед всего
		"total_kills": 0,         # убийств всего""")

# 3) загрузка
rep("""	_profile.onboarded = int(cfg.get_value("player", "onboarded", 0))""",
"""	_profile.onboarded = int(cfg.get_value("player", "onboarded", 0))
	_profile.coins = int(cfg.get_value("player", "coins", 0))
	_profile.wins = int(cfg.get_value("player", "wins", 0))
	_profile.total_kills = int(cfg.get_value("player", "total_kills", 0))""")

# 4) сохранение
rep("""	cfg.set_value("player", "onboarded", int(_profile.get("onboarded", 0)))
	cfg.save("user://profile.cfg")""",
"""	cfg.set_value("player", "onboarded", int(_profile.get("onboarded", 0)))
	cfg.set_value("player", "coins", int(_profile.get("coins", 0)))
	cfg.set_value("player", "wins", int(_profile.get("wins", 0)))
	cfg.set_value("player", "total_kills", int(_profile.get("total_kills", 0)))
	cfg.save("user://profile.cfg")""")

# 5) начисление наград и открытие слотов в конце боя
rep("""		for pi in _mode:
			var pf = _fighters[pi]
			_profile.stats[pi] = pf.stats
			_profile.lvl[pi] = int(pf.lvl)
			_profile.xp[pi] = int(pf.xp)
		_save_profile()""",
"""		for pi in _mode:
			var pf = _fighters[pi]
			_profile.stats[pi] = pf.stats
			_profile.lvl[pi] = int(pf.lvl)
			_profile.xp[pi] = int(pf.xp)
		# --- награды за бой: монеты, победы, открытие слотов ---
		var win := blue == 0
		var p_kills := 0
		for fk in _fighters:
			if fk.team == 0:
				p_kills += int(fk.kills)
		var reward := (100 if win else 25) + 15 * p_kills
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
		_battle_reward = {"coins": reward, "kills": p_kills, "win": win, "unlock": unlock_msg}
		_save_profile()""")

# 6) экран итогов: строка награды
rep("""			sub.text = "Раундов: %d · Зона: фаза %d" % [_turn, _zone_phase]
			sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			sub.add_theme_font_size_override("font_size", 14)
			vb.add_child(sub)""",
"""			sub.text = "Раундов: %d · Зона: фаза %d" % [_turn, _zone_phase]
			sub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			sub.add_theme_font_size_override("font_size", 14)
			vb.add_child(sub)
			if not _battle_reward.is_empty():
				var rw := Label.new()
				rw.text = "Награда: +%d монет (за %s + убийства %d×15) · Всего: %d 🪙" % [
					int(_battle_reward.coins),
					"победу 100" if _battle_reward.win else "участие 25",
					int(_battle_reward.kills),
					int(_profile.get("coins", 0))]
				rw.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
				rw.add_theme_font_size_override("font_size", 15)
				rw.add_theme_color_override("font_color", Color(1.0, 0.9, 0.45))
				vb.add_child(rw)
				if str(_battle_reward.get("unlock", "")) != "":
					var ul := Label.new()
					ul.text = str(_battle_reward.unlock)
					ul.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
					ul.add_theme_font_size_override("font_size", 16)
					ul.add_theme_color_override("font_color", Color(0.5, 1.0, 0.6))
					vb.add_child(ul)""")

# 7) лобби: сводка монет/побед + блокировка режимов по слотам
rep("""	vb.add_child(_framed_label("ROYAL BATTLE — королевская битва на арене телешоу будущего", 15))
	var m1 := _menu_button("Тренировка 1×1 — дуэль (малая арена)")
	m1.pressed.connect(func(): _start_mode(1))
	vb.add_child(m1)
	var m2 := _menu_button("Тренировка 2×2 — пара (средняя арена)")
	m2.pressed.connect(func(): _start_mode(2))
	vb.add_child(m2)
	var m4 := _menu_button("Тренировка 4×4 — отряд (большая арена)")
	m4.pressed.connect(func(): _start_mode(4))
	vb.add_child(m4)""",
"""	vb.add_child(_framed_label("ROYAL BATTLE — королевская битва на арене телешоу будущего", 15))
	vb.add_child(_framed_label("🪙 Монеты: %d · Побед: %d · Убийств: %d" % [
		int(_profile.get("coins", 0)), int(_profile.get("wins", 0)), int(_profile.get("total_kills", 0))], 16))
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
	vb.add_child(m4)""")

# 8) текст закрытого слота в отряде — конкретное условие
rep("""		lock.text = "Слот закрыт. Откроется за заслуги в боях
или по месячной подписке (с призами) — скоро.\"""",
"""		var need_w: int = int(SLOT_WINS.get(_squad_edit + 1, 25))
		lock.text = "Слот закрыт. Нужно побед: %d (у вас %d)
или месячная подписка (с призами) — скоро." % [need_w, int(_profile.get("wins", 0))]""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.19-20")
