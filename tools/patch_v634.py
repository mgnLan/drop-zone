# -*- coding: utf-8 -*-
# v6.34: Battle Pass каркас — сезон 1, 30 уровней, free/prem ленты, телепорт «Шторм»
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

# ---- 1. Поля профиля ----
rep("""		"chests_total": 0,            # сундуков открыто всего
""", """		"chests_total": 0,            # сундуков открыто всего
		"owned_teleports": [1, 1, 0], # телепорты: луч, дыра, шторм (BP)
		"bp_xp": 0,                   # сезонный опыт Battle Pass
		"bp_owned": 0,                # 1 = пропуск куплен
		"bp_claimed_free": [],        # забранные награды free-ленты
		"bp_claimed_prem": [],        # забранные награды premium-ленты
""")
rep("""	_profile.chests_total = int(cfg.get_value("player", "chests_total", 0))
""", """	_profile.chests_total = int(cfg.get_value("player", "chests_total", 0))
	_profile.owned_teleports = cfg.get_value("player", "owned_teleports", [1, 1, 0])
	_profile.bp_xp = int(cfg.get_value("player", "bp_xp", 0))
	_profile.bp_owned = int(cfg.get_value("player", "bp_owned", 0))
	_profile.bp_claimed_free = cfg.get_value("player", "bp_claimed_free", [])
	_profile.bp_claimed_prem = cfg.get_value("player", "bp_claimed_prem", [])
""")
rep("""	cfg.set_value("player", "chests_total", int(_profile.get("chests_total", 0)))
""", """	cfg.set_value("player", "chests_total", int(_profile.get("chests_total", 0)))
	cfg.set_value("player", "owned_teleports", _profile.get("owned_teleports", [1, 1, 0]))
	cfg.set_value("player", "bp_xp", int(_profile.get("bp_xp", 0)))
	cfg.set_value("player", "bp_owned", int(_profile.get("bp_owned", 0)))
	cfg.set_value("player", "bp_claimed_free", _profile.get("bp_claimed_free", []))
	cfg.set_value("player", "bp_claimed_prem", _profile.get("bp_claimed_prem", []))
""")

# ---- 2. Сезонный опыт после боя ----
rep("""		var reward := 2 + 1 * p_kills  # +2 за бой, +1 за убийство
""", """		var bp_gain := 5 + 5 * p_kills + (20 if win else 0)
		_profile.bp_xp = int(_profile.get("bp_xp", 0)) + bp_gain
		var reward := 2 + 1 * p_kills  # +2 за бой, +1 за убийство
""")

# ---- 3. Телепорт «Шторм» открывается через BP ----
rep("""		var locked := tid == "storm"
""", """		var ots: Array = _profile.get("owned_teleports", [1, 1, 0])
		var locked := tid == "storm" and (ots.size() < 3 or int(ots[2]) == 0)
""")
rep("""			tb2.tooltip_text = "Эксклюзив Battle Pass — появится в 1 сезоне"
""", """			tb2.tooltip_text = "Эксклюзив Battle Pass — 30 уровень 1 сезона"
""")

# ---- 4. Кнопка BP в главном меню ----
rep("""	var chests := _menu_button("🎁 Сундуки: удача, редкости, осколки")
	chests.pressed.connect(_show_menu_chests)
""", """	var chests := _menu_button("🎁 Сундуки: удача, редкости, осколки")
	chests.pressed.connect(_show_menu_chests)
	var bp := _menu_button("🏅 Battle Pass — сезон 1")
	bp.pressed.connect(_show_menu_bp)
""")
rep("""		c2.add_child(chests)
""", """		c2.add_child(chests)
		c2.add_child(bp)
""")
rep("""		vb.add_child(chests)
""", """		vb.add_child(chests)
		vb.add_child(bp)
""")

# ---- 5. Логика и экран Battle Pass (перед сундуками) ----
rep("""# ---------- сундуки шоу ----------
""", """# ---------- Battle Pass: сезон 1 ----------
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
		return {"kind": "coins", "n": lv * 2, "name": "%d 🪙" % (lv * 2)}
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
	vb.custom_minimum_size = Vector2(minf(620.0, get_viewport().get_visible_rect().size.x * 0.95), 0)
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
""")

io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ALL_OK v6.34")
