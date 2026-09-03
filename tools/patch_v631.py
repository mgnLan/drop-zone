# v6.31 — Очередь 2: таланты (ранги 1/2/3, очко за 3 уровня, ресет 600) + владение оружием
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()
fails = []

def rep(old, new, cnt=1):
    global src
    n = src.count(old)
    if n != cnt:
        fails.append("COUNT %d != %d: %r" % (n, cnt, old[:70]))
        return
    src = src.replace(old, new, cnt)

# ---- 1. Константы талантов и владения ----
rep("""const SLOT_WINS := {2: 3, 3: 10, 4: 25}   # слот -> сколько побед нужно
""", """const SLOT_WINS := {2: 3, 3: 10, 4: 25}   # слот -> сколько побед нужно
# таланты: ранг N стоит N очков (1/2/3); очко талантов — каждые 3 уровня бойца
const TALENTS := [
	{"id": "reload1", "icon": "⚡", "name": "Быстрая перезарядка", "max": 1, "desc": "Перезарядка стоит 1 ОД"},
	{"id": "sapper", "icon": "💣", "name": "Сапёр", "max": 1, "desc": "Бочки взводятся с 1 попадания, взрыв +25%"},
	{"id": "steady", "icon": "🪨", "name": "Устойчивость", "max": 1, "desc": "Тяжёлое оружие (6+ ОД / str_req) — на 1 ОД дешевле"},
	{"id": "marathon", "icon": "🏃", "name": "Марафон", "max": 1, "desc": "+1 ОД максимум"},
	{"id": "medic", "icon": "🩹", "name": "Полевой врач", "max": 3, "desc": "+25% к лечению аптечкой за ранг"},
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
""")

# ---- 2. Профиль: поля ----
rep("""		"lvl": [1, 1, 1, 1],
		"xp": [0, 0, 0, 0],
	}
""", """		"lvl": [1, 1, 1, 1],
		"xp": [0, 0, 0, 0],
		"talents": [{}, {}, {}, {}],  # таланты бойцов (id -> ранг)
		"tpts": [0, 0, 0, 0],         # очки талантов
		"prof": [{}, {}, {}, {}],     # владение оружием (класс -> урон)
	}
""")
rep("""		_profile.lvl[i] = int(cfg.get_value("fighter%d" % i, "lvl", 1))
		_profile.xp[i] = int(cfg.get_value("fighter%d" % i, "xp", 0))
""", """		_profile.lvl[i] = int(cfg.get_value("fighter%d" % i, "lvl", 1))
		_profile.xp[i] = int(cfg.get_value("fighter%d" % i, "xp", 0))
		_profile.talents[i] = cfg.get_value("fighter%d" % i, "talents", {})
		_profile.tpts[i] = int(cfg.get_value("fighter%d" % i, "tpts", 0))
		_profile.prof[i] = cfg.get_value("fighter%d" % i, "prof", {})
""")
rep("""		cfg.set_value("fighter%d" % i, "lvl", _profile.lvl[i])
		cfg.set_value("fighter%d" % i, "xp", _profile.xp[i])
""", """		cfg.set_value("fighter%d" % i, "lvl", _profile.lvl[i])
		cfg.set_value("fighter%d" % i, "xp", _profile.xp[i])
		cfg.set_value("fighter%d" % i, "talents", _profile.talents[i])
		cfg.set_value("fighter%d" % i, "tpts", _profile.tpts[i])
		cfg.set_value("fighter%d" % i, "prof", _profile.prof[i])
""")

# ---- 3. Хелперы талантов/владения перед _stat_hp ----
rep("""# производные характеристики бойца из распределённых очков
func _stat_hp(st: Dictionary) -> int:
""", """# ---- таланты и владение оружием ----
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
""")

# ---- 4. Спавн: таланты/владение в бойца ----
rep("""func _spawn_human(model: String, gx: int, gz: int, rot_y: float, weapon: String, team: Color, team_idx: int, fname: String, st: Dictionary = {}, lvl := 1, xp := 0) -> void:
""", """func _spawn_human(model: String, gx: int, gz: int, rot_y: float, weapon: String, team: Color, team_idx: int, fname: String, st: Dictionary = {}, lvl := 1, xp := 0, talents: Dictionary = {}, tpts := 0, prof: Dictionary = {}) -> void:
""")
rep("""		"lvl": lvl, "xp": xp, "kills": 0, "pts": pts0, "dmg": 0,
""", """		"lvl": lvl, "xp": xp, "kills": 0, "pts": pts0, "dmg": 0,
		"talents": talents.duplicate(), "tpts": tpts, "prof": prof.duplicate(),
""")
rep("""			red_models[i][1], Color("#ff4757"), 0, _profile.names[i], _profile.stats[i], _profile.lvl[i], _profile.xp[i])
""", """			red_models[i][1], Color("#ff4757"), 0, _profile.names[i], _profile.stats[i], _profile.lvl[i], _profile.xp[i],
			_profile.talents[i], int(_profile.tpts[i]), _profile.prof[i])
""")

# ---- 5. После боя — сохранить таланты/владение ----
rep("""			_profile.stats[pi] = pf.stats
			_profile.lvl[pi] = int(pf.lvl)
			_profile.xp[pi] = int(pf.xp)
""", """			_profile.stats[pi] = pf.stats
			_profile.lvl[pi] = int(pf.lvl)
			_profile.xp[pi] = int(pf.xp)
			_profile.talents[pi] = pf.get("talents", {})
			_profile.tpts[pi] = int(pf.get("tpts", 0))
			_profile.prof[pi] = pf.get("prof", {})
""")

# ---- 6. Очко талантов каждые 3 уровня ----
rep("""		f.lvl = int(f.lvl) + 1
		f.pts = int(f.pts) + (5 if int(f.lvl) <= 5 else 3)
""", """		f.lvl = int(f.lvl) + 1
		f.pts = int(f.pts) + (5 if int(f.lvl) <= 5 else 3)
		if int(f.lvl) % 3 == 0:
			f.tpts = int(f.get("tpts", 0)) + 1
""")

# ---- 7. Таланты в производных ----
rep("""	f.max_hp = _stat_hp(f.stats) + 3 * (int(f.lvl) - 1)
	f.max_ap = _stat_ap(f.stats) + mini(3, int(f.lvl) / 3) - _armor_ap_penalty(f)
	f.carry_base = _stat_carry(f.stats) + 0.5 * (int(f.lvl) - 1)
	f.vision = _stat_vision(f.stats)
""", """	f.max_hp = _stat_hp(f.stats) + 3 * (int(f.lvl) - 1)
	f.max_ap = _stat_ap(f.stats) + mini(3, int(f.lvl) / 3) - _armor_ap_penalty(f) + _tal(f, "marathon")
	f.carry_base = _stat_carry(f.stats) + 0.5 * (int(f.lvl) - 1) + 2.0 * _tal(f, "mule")
	f.vision = _stat_vision(f.stats) + _tal(f, "scout")
""")

# ---- 8. Крит + «Фартовый» ----
rep("""			if _rng.randf() < _stat_crit(a.stats):
""", """			if _rng.randf() < _stat_crit(a.stats) + 0.02 * _tal(a, "lucky"):
""")

# ---- 9. Стоимость выстрела через _shot_cost ----
rep("""	var w: Dictionary = a.weapon
	var cost: int = w.get("ap_cost", 3)
	var dist := Vector2(a.cell.x - d.cell.x, a.cell.y - d.cell.y).length()
""", """	var w: Dictionary = a.weapon
	var cost := _shot_cost(a, w)
	var dist := Vector2(a.cell.x - d.cell.x, a.cell.y - d.cell.y).length()
""")
rep("""	var w: Dictionary = a.weapon
	var cost: int = w.get("ap_cost", 3)
	var k := _key(cell)
""", """	var w: Dictionary = a.weapon
	var cost := _shot_cost(a, w)
	var k := _key(cell)
""")

# ---- 10. Владение: точность/урон/опыт класса ----
rep("""	var chance := clampf(_hit_chance(a.cell, d.cell) + _stat_acc(a.stats) - _stat_dodge(d.stats), 0.1, 0.95)
	var total := 0
	var crit := false
""", """	var cls := _weapon_class(w)
	var pl := _prof_lvl(a, cls)
	var chance := clampf(_hit_chance(a.cell, d.cell) + _stat_acc(a.stats) + 0.03 * pl - _stat_dodge(d.stats), 0.1, 0.95)
	var total := 0
	var crit := false
""")
rep("""		if _rng.randf() < chance:
			var dm: int = w.get("damage", 10)
""", """		if _rng.randf() < chance:
			var dm: int = int(w.get("damage", 10) * (1.0 + 0.03 * pl))
""")
rep("""	if total > 0:
		var real: int = _apply_damage(def, total, a.name, att)
		_gain_xp(att, 25 + real)
""", """	if total > 0:
		var real: int = _apply_damage(def, total, a.name, att)
		_gain_xp(att, 25 + real)
		if cls != "":
			a.prof[cls] = int(a.prof.get(cls, 0)) + real
""")
rep("""		if did:
			_gain_xp(att, 25 + real_sum)
""", """		if did:
			_gain_xp(att, 25 + real_sum)
			var cls2 := _weapon_class(w)
			if cls2 != "":
				a.prof[cls2] = int(a.prof.get(cls2, 0)) + real_sum
""")

# ---- 11. «Быстрая перезарядка» ----
rep("""	var rc: int = f.weapon.get("reload_ap", RELOAD_AP)
	if f.ap < rc:
""", """	var rc: int = f.weapon.get("reload_ap", RELOAD_AP)
	if _tal(f, "reload1") > 0:
		rc = 1
	if f.ap < rc:
""")
rep("""			var rc2: int = w.get("reload_ap", RELOAD_AP)
""", """			var rc2: int = w.get("reload_ap", RELOAD_AP)
			if _tal(f, "reload1") > 0:
				rc2 = 1
""")

# ---- 12. «Полевой врач» ----
rep("""				f.ap -= it.get("ap_cost", 2)
				f.hp = mini(f.max_hp, f.hp + it["heal"])
				f.backpack.remove_at(idx)
				_log("%s: +%d HP (итого %d)" % [f.name, it["heal"], f.hp])
""", """				f.ap -= it.get("ap_cost", 2)
				var heal_am: int = int(it["heal"] * (1.0 + 0.25 * _tal(f, "medic")))
				f.hp = mini(int(f.max_hp), int(f.hp) + heal_am)
				f.backpack.remove_at(idx)
				_log("%s: +%d HP (итого %d)" % [f.name, heal_am, f.hp])
""")

# ---- 13. «Сапёр»: бочка с 1 попадания, взрыв +25% ----
rep("""func _damage_cover_hit(ck: String, dmg: int, src: String) -> void:
	# урон по объекту; бочке нужно ДВА попадания даже при большом уроне
	var rec = _covers.get(ck)
	if rec == null:
		return
	rec["hits"] = int(rec.get("hits", 0)) + 1
	rec.hp = int(rec.hp) - dmg
	var cname := _cover_name(rec)
	if int(rec.hp) <= 0:
		if rec.get("barrel", false) and int(rec["hits"]) < 2:
			rec.hp = 1
			_log("%s -> %s: пробита (%d урона), но не взорвалась — нужно ещё попадание!" % [src, cname, dmg])
			return
		_destroy_cover(ck)
""", """func _damage_cover_hit(ck: String, dmg: int, src: String, att_idx := -1) -> void:
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
""")
rep("""func _destroy_cover(ck: String) -> void:
""", """func _destroy_cover(ck: String, mul := 1.0) -> void:
""")
rep("""		_explode_barrel(rec.cells[0])
""", """		_explode_barrel(rec.cells[0], mul)
""")
rep("""func _explode_barrel(c: Vector2i) -> void:
	# бочка взрывается: урон 20 по своей и соседним клеткам, возможна цепная реакция
	_explode_at(c, 1)
	for vi in _fighters.size():
		var v = _fighters[vi]
		if not v.alive:
			continue
		if maxi(absi(v.cell.x - c.x), absi(v.cell.y - c.y)) <= 1:
			_apply_damage(vi, 20, "Бочка", -1)
""", """func _explode_barrel(c: Vector2i, mul := 1.0) -> void:
	# бочка взрывается: урон 20 (x mul у сапёра) по своей и соседним клеткам, цепная реакция
	_explode_at(c, 1)
	for vi in _fighters.size():
		var v = _fighters[vi]
		if not v.alive:
			continue
		if maxi(absi(v.cell.x - c.x), absi(v.cell.y - c.y)) <= 1:
			_apply_damage(vi, int(20 * mul), "Бочка", -1)
""")
rep("""	_damage_cover_hit(ck, dmg, a.name)
""", """	_damage_cover_hit(ck, dmg, a.name, att)
""")

# ---- 14. Окно уровня: секция талантов ----
rep("""	var ok := Button.new()
	ok.text = "ПОДТВЕРДИТЬ"
""", """	var tl := Label.new()
	tl.text = "— Таланты (очков: %d; +1 каждые 3 уровня) —" % int(f.get("tpts", 0))
	tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tl.add_theme_font_size_override("font_size", 14)
	tl.add_theme_color_override("font_color", Color(1.0, 0.9, 0.45))
	vb.add_child(tl)
	for t in TALENTS:
		var cur := _tal(f, t["id"])
		var trow := HBoxContainer.new()
		vb.add_child(trow)
		var tnl := Label.new()
		tnl.text = "%s %s — %d/%d" % [t["icon"], t["name"], cur, int(t["max"])]
		tnl.custom_minimum_size = Vector2(180 if _mob() else 240, 0)
		tnl.add_theme_font_size_override("font_size", 13)
		tnl.tooltip_text = str(t["desc"])
		trow.add_child(tnl)
		var tb := Button.new()
		var cost := cur + 1
		if cur >= int(t["max"]):
			tb.text = "МАКС"
			tb.disabled = true
		else:
			tb.text = "+%d 🎯" % cost
			tb.disabled = int(f.get("tpts", 0)) < cost
			tb.tooltip_text = "%s\nЦена ранга: %d очк." % [str(t["desc"]), cost]
			var tid: String = t["id"]
			var fi3: int = i
			tb.pressed.connect(func():
				if _tal_buy(_fighters[fi3], tid):
					_lvl_wrap.queue_free()
					_lvl_open = false
					_show_levelup(fi3)
			)
		trow.add_child(tb)
	var ok := Button.new()
	ok.text = "ПОДТВЕРДИТЬ"
""")

# ---- 15. Отряд (лобби): таланты + сброс за 600 ----
rep("""	var sum := Label.new()
	sum.text = "Итог: HP %d · ОД %d · вес %.0f кг · обзор %d" % [
		_stat_hp(st), _stat_ap(st), _stat_carry(st), _stat_vision(st)]
""", """	var tl2 := Label.new()
	tl2.text = "Таланты — очков: %d (+1 каждые 3 уровня)" % int(_profile.tpts[_squad_edit])
	tl2.add_theme_font_size_override("font_size", 15)
	tl2.add_theme_color_override("font_color", Color(1.0, 0.9, 0.45))
	vb.add_child(tl2)
	var tprof: Dictionary = _profile.talents[_squad_edit]
	for t in TALENTS:
		var cur := int(tprof.get(t["id"], 0))
		var trow := HBoxContainer.new()
		vb.add_child(trow)
		var tnl := Label.new()
		tnl.text = "%s %s — %d/%d" % [t["icon"], t["name"], cur, int(t["max"])]
		tnl.custom_minimum_size = Vector2(180 if _mob() else 240, 0)
		tnl.add_theme_font_size_override("font_size", 13)
		tnl.tooltip_text = str(t["desc"])
		trow.add_child(tnl)
		var tb := Button.new()
		var cost := cur + 1
		if cur >= int(t["max"]):
			tb.text = "МАКС"
			tb.disabled = true
		else:
			tb.text = "+%d 🎯" % cost
			tb.disabled = int(_profile.tpts[_squad_edit]) < cost
			tb.tooltip_text = "%s\nЦена ранга: %d очк." % [str(t["desc"]), cost]
			var tid2: String = t["id"]
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
	var spent := 0
	for k3 in tprof.keys():
		var r3 := int(tprof[k3])
		spent += r3 * (r3 + 1) / 2
	if spent > 0:
		var rst := Button.new()
		rst.text = "♻ Сброс талантов — %d 🪙 (вернёт %d очк.)" % [TALENT_RESET_COST, spent]
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
""")

# ---- 16. Панель бойца: владение оружием ----
rep("""	lv.text = "Ур. %d · Опыт %d/%d · Убийств: %d" % [int(f.lvl), int(f.xp), _xp_need(int(f.lvl)), int(f.kills)]
	box.add_child(lv)
""", """	lv.text = "Ур. %d · Опыт %d/%d · Убийств: %d" % [int(f.lvl), int(f.xp), _xp_need(int(f.lvl)), int(f.kills)]
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
""")

# ---- 17. Кнопка «Навыки» видна и при очках талантов ----
rep("""	if int(f.get("pts", 0)) > 0 and f.team == 0:
""", """	if (int(f.get("pts", 0)) > 0 or int(f.get("tpts", 0)) > 0) and f.team == 0:
""")

if fails:
    print("\n".join(fails))
    print("FAIL")
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ALL_OK")
