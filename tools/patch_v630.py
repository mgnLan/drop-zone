# v6.30 — Очередь 1: статы/уровни v2, магазин+запас, кап брони, экономика, выносливость
import io, json, sys

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

# ---- 1. Подсказки и дейлики ----
rep("""const STAT_HINTS := {"str": "+2 кг носимого веса за очко", "agi": "+1 ОД за очко",
	"end": "+15 HP за очко", "per": "+1 клетка обзора за очко",
	"int": "+10% к опыту за очко", "lck": "+3% к шансу крита (x1.5) за очко"}
""", """const STAT_HINTS := {"str": "+2 кг веса/очко; СИЛ 4+ для тяжёлого оружия",
	"agi": "+1 ОД за 3 очка (макс +3); +0.5% уклонения/очко",
	"end": "+15 HP за очко", "per": "+1 обзор за 2 очка",
	"int": "+2% точности (макс 20%) и +10% опыта/очко", "lck": "+0.1% к криту (база 5%, x1.5)/очко"}
""")
rep("""	{"name": "Убей 5 противников", "need": 5, "reward": 50},
	{"name": "Открой 3 ящика", "need": 3, "reward": 40},
	{"name": "Выиграй бой", "need": 1, "reward": 75},
""", """	{"name": "Убей 5 противников", "need": 5, "reward": 6},
	{"name": "Открой 3 ящика", "need": 3, "reward": 5},
	{"name": "Выиграй бой", "need": 1, "reward": 10},
""")

# ---- 2. Выносливость: константы и хелперы перед _daily_add ----
rep("""func _daily_add(qi: int, n: int) -> Array:
""", """const STAMINA_MAX := 100.0
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
""")

# ---- 3. Профиль: выносливость в дефолт/загрузку/сохранение ----
rep("""		"coins": 0,               # копилка монет (монетизация)
""", """		"coins": 0,               # копилка монет (монетизация)
		"stamina": 100.0,         # выносливость шоу (бой −15)
		"stamina_ts": 0.0,        # unixtime последнего пересчёта
""")
rep("""	_profile.coins = int(cfg.get_value("player", "coins", 0))
""", """	_profile.coins = int(cfg.get_value("player", "coins", 0))
	_profile.stamina = float(cfg.get_value("player", "stamina", 100.0))
	_profile.stamina_ts = float(cfg.get_value("player", "stamina_ts", 0.0))
""")
rep("""	cfg.set_value("player", "coins", int(_profile.get("coins", 0)))
""", """	cfg.set_value("player", "coins", int(_profile.get("coins", 0)))
	cfg.set_value("player", "stamina", float(_profile.get("stamina", 100.0)))
	cfg.set_value("player", "stamina_ts", float(_profile.get("stamina_ts", 0.0)))
""")

# ---- 4. Статы v2 ----
rep("""func _stat_ap(st: Dictionary) -> int:
	return 10 + int(st.get("agi", 0))
""", """func _stat_ap(st: Dictionary) -> int:
	# +1 ОД за 3 очка ловкости, максимум +3
	return 10 + mini(3, int(st.get("agi", 0)) / 3)
""")
rep("""func _stat_vision(st: Dictionary) -> int:
	return VISION + int(st.get("per", 0))
""", """func _stat_vision(st: Dictionary) -> int:
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
""")

# ---- 5. Производные уровня ----
rep("""	var hp_max := _stat_hp(st) + 5 * (lvl - 1)
	var ap_max := _stat_ap(st) + lvl / 3
""", """	var hp_max := _stat_hp(st) + 3 * (lvl - 1)
	var ap_max := _stat_ap(st) + mini(3, lvl / 3)
""")
rep("""		"carry_base": _stat_carry(st), "vision": _stat_vision(st),
""", """		"carry_base": _stat_carry(st) + 0.5 * (lvl - 1), "vision": _stat_vision(st),
""")
rep("""	f.max_hp = _stat_hp(f.stats) + 5 * (int(f.lvl) - 1)
	f.max_ap = _stat_ap(f.stats) + int(f.lvl) / 3
	f.carry_base = _stat_carry(f.stats)
""", """	f.max_hp = _stat_hp(f.stats) + 3 * (int(f.lvl) - 1)
	f.max_ap = _stat_ap(f.stats) + mini(3, int(f.lvl) / 3) - _armor_ap_penalty(f)
	f.carry_base = _stat_carry(f.stats) + 0.5 * (int(f.lvl) - 1)
""")
rep("""	return STAT_POINTS + 5 * (lvl - 1) - spent
""", """	return STAT_POINTS + 5 * mini(lvl - 1, 4) + 3 * maxi(0, lvl - 5) - spent
""")

# ---- 6. Кривая опыта и очки за уровень ----
rep("""	return int(floor(100.0 * pow(1.2, lvl - 1)))
""", """	return int(floor(100.0 * pow(1.35, lvl - 1)))
""")
rep("""		f.pts = int(f.pts) + 5
""", """		f.pts = int(f.pts) + (5 if int(f.lvl) <= 5 else 3)
""")
rep("""	_log("%s — УРОВЕНЬ %d! (+5 очков навыков)" % [f.name, int(f.lvl)])
""", """	_log("%s — УРОВЕНЬ %d! (+%d очков навыков)" % [f.name, int(f.lvl), 5 if int(f.lvl) <= 5 else 3])
""")

# ---- 7. Урон: кап брони 70%, XP за килл, возврат реального урона ----
rep("""func _apply_damage(victim: int, dmg: int, src_name: String, src_idx := -1) -> void:
	var d = _fighters[victim]
	var real := maxi(1, dmg - _defense(d))
""", """func _apply_damage(victim: int, dmg: int, src_name: String, src_idx := -1) -> int:
	var d = _fighters[victim]
	# броня срезает не больше 70% урона
	var real := maxi(maxi(1, dmg - _defense(d)), int(ceil(dmg * 0.3)))
""")
rep("""		if src_idx >= 0 and src_idx < _fighters.size():
			_fighters[src_idx].kills = int(_fighters[src_idx].kills) + 1
	else:
		_spawn_burst(d.node.position + Vector3(0, 1.0, 0), Color(0.55, 0.05, 0.08))
""", """		if src_idx >= 0 and src_idx < _fighters.size():
			_fighters[src_idx].kills = int(_fighters[src_idx].kills) + 1
			_gain_xp(src_idx, 50)
	else:
		_spawn_burst(d.node.position + Vector3(0, 1.0, 0), Color(0.55, 0.05, 0.08))
	return real
""")

# ---- 8. Выстрел: точность/уклонение/крит v2, XP = 25+урон ----
rep("""	var chance := _hit_chance(a.cell, d.cell)
	var total := 0
	var crit := false
	var lck: int = int(a.stats.get("lck", 0))
	for i in burst:
		if _rng.randf() < chance:
			var dm: int = w.get("damage", 10)
			if lck > 0 and _rng.randf() < 0.03 * lck:
				dm = int(dm * 1.5)
				crit = true
			total += dm
	if total > 0:
		_apply_damage(def, total, a.name, att)
		_gain_xp(att, 50)
		if crit:
			_log("КРИТ! x1.5 урона")
	else:
		var cover_txt := " (шанс был %d%% — укрытия)" % int(chance * 100) if chance < HIT_CHANCE else ""
		_log("%s -> %s: промах%s" % [a.name, d.name, cover_txt])
""", """	var chance := clampf(_hit_chance(a.cell, d.cell) + _stat_acc(a.stats) - _stat_dodge(d.stats), 0.1, 0.95)
	var total := 0
	var crit := false
	for i in burst:
		if _rng.randf() < chance:
			var dm: int = w.get("damage", 10)
			if _rng.randf() < _stat_crit(a.stats):
				dm = int(dm * 1.5)
				crit = true
			total += dm
	if total > 0:
		var real: int = _apply_damage(def, total, a.name, att)
		_gain_xp(att, 25 + real)
		if crit:
			_log("КРИТ! x1.5 урона")
	else:
		var base: float = HIT_CHANCE + _stat_acc(a.stats)
		var cover_txt := " (шанс был %d%% — укрытия/уклонение)" % int(chance * 100) if chance < base - 0.001 else ""
		_log("%s -> %s: промах%s" % [a.name, d.name, cover_txt])
""")
rep("""		var did := false
		for vi in _fighters.size():
""", """		var did := false
		var real_sum := 0
		for vi in _fighters.size():
""")
rep("""				if tot > 0:
					did = true
					_apply_damage(vi, tot, a.name, att)
		if did:
			_gain_xp(att, 50)
""", """				if tot > 0:
					did = true
					real_sum += _apply_damage(vi, tot, a.name, att)
		if did:
			_gain_xp(att, 25 + real_sum)
""")

# ---- 9. Прицел: показываем точность с учётом ИНТ/уклонения ----
rep("""	var chance := _hit_chance(a2.cell, d.cell)
""", """	var chance := clampf(_hit_chance(a2.cell, d.cell) + _stat_acc(a2.stats) - _stat_dodge(d.stats), 0.1, 0.95)
""")
rep("""	elif chance < HIT_CHANCE - 0.001:
""", """	elif chance < HIT_CHANCE + _stat_acc(a2.stats) - 0.001:
""")

# ---- 10. Перезарядка: магазин + запас ----
rep("""	if f.ap < RELOAD_AP:
		_log("Нужно %d AP на перезарядку" % RELOAD_AP)
		return
	f.ap -= RELOAD_AP
	f.ammo = f.weapon.get("ammo", 0)
	_sfx_play("reload")
	_log("%s перезарядился (%d патронов)" % [f.name, f.ammo])
	_after_action()
""", """	var mag: int = f.weapon.get("ammo", 0)
	var need: int = mag - int(f.ammo)
	if need <= 0:
		_log("Магазин полон")
		return
	if int(f.get("spare", -1)) == 0:
		_log("Нет запасных патронов!")
		return
	var rc: int = f.weapon.get("reload_ap", RELOAD_AP)
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
""")

# ---- 11. Перезарядка ботов ----
rep("""		if w.has("ammo") and f.ammo < burst:
			if f.ap >= RELOAD_AP:
				f.ap -= RELOAD_AP
				f.ammo = w.get("ammo", 0)
				_sfx_play("reload")
				_log("%s перезаряжается" % f.name)
				await get_tree().create_timer(0.3).timeout
				continue
""", """		if w.has("ammo") and f.ammo < burst:
			var rc2: int = w.get("reload_ap", RELOAD_AP)
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
""")

# ---- 12. Рюкзак: str_req для тяжёлого, запас патронов, пересчёт ОД от брони ----
rep("""		"weapon":
			f.backpack.remove_at(idx)
			if not f.gun.is_empty():
				f.backpack.append({"kind": "weapon", "item": f.gun})
			f.gun = entry["item"]
			f.weapon = entry["item"]
			f.ammo = entry["item"].get("ammo", 0)
			_log("%s взял в руки: %s" % [f.name, entry["item"]["name"]])
""", """		"weapon":
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
""")
rep("""			f.armor[cat] = entry["item"]
			_log("%s надел: %s (защита %d)" % [f.name, entry["item"]["name"], _defense(f)])
""", """			f.armor[cat] = entry["item"]
			_recalc_derived(f)  # тяжёлая броня может снижать ОД
			_log("%s надел: %s (защита %d)" % [f.name, entry["item"]["name"], _defense(f)])
""")
rep("""	f.armor[cat] = null
	f.backpack.append(entry)
""", """	f.armor[cat] = null
	f.backpack.append(entry)
	_recalc_derived(f)
""")

# ---- 13. Спавн бойца: запас патронов ----
rep("""		"gun": gun, "weapon": gun, "ammo": gun.get("ammo", 0),
""", """		"gun": gun, "weapon": gun, "ammo": gun.get("ammo", 0), "spare": gun.get("spare", -1),
""")

# ---- 14. Панель: магазин/запас ----
rep("""	var ammo_txt := " [патр. %d]" % f.ammo if f.weapon.has("ammo") else ""
""", """	var ammo_txt := ""
	if f.weapon.has("ammo"):
		var sp_txt := "∞" if int(f.get("spare", -1)) < 0 else str(int(f.spare))
		ammo_txt = " [патр. %d/%s]" % [int(f.ammo), sp_txt]
""")

# ---- 15. Экономика: +2 бой, +1 убийство ----
rep("""		var reward := (100 if win else 25) + 15 * p_kills
""", """		var reward := 2 + 1 * p_kills  # +2 за бой, +1 за убийство
""")
rep("""Награда: +%d монет (за %s + убийства %d×15) · Всего: %d 🪙""", """Награда: +%d монет (бой 2 + убийства %d×1) · Всего: %d 🪙""")
rep("""					"победу 100" if _battle_reward.win else "участие 25",
""", """""")

# ---- 16. Выносливость: гейт старта боя ----
rep("""func _start_mode(m: int) -> void:
	_save_mode(m)
""", """func _start_mode(m: int) -> void:
	if not _stamina_can_fight():
		var d := AcceptDialog.new()
		d.title = "Выносливость"
		d.dialog_text = "Недостаточно выносливости (бой стоит 15).\nВосстанавливается равномерно: 100 за сутки.\nСейчас: %d/100 ⚡" % int(float(_profile.get("stamina", 0.0)))
		_ui.menu_layer.add_child(d)
		d.popup_centered()
		return
	_save_mode(m)
""")

# ---- 17. Списание выносливости при старте боя ----
rep("""			_menu_open = false
			_busy = false
			_apply_graphics(_settings.graphics)
""", """			_menu_open = false
			_busy = false
			if int(_profile.get("onboarded", 0)) == 1:
				_stamina_update()
				_profile.stamina = maxf(0.0, float(_profile.stamina) - STAMINA_COST)
				_save_profile()
			_apply_graphics(_settings.graphics)
""")

# ---- 18. Чип выносливости в меню ----
rep("""		ch.add_child(_framed_label("🪙 %d" % int(_profile.get("coins", 0)), 13))
""", """		_stamina_update()
		ch.add_child(_framed_label("🪙 %d" % int(_profile.get("coins", 0)), 13))
		ch.add_child(_framed_label("⚡ %d/100" % int(float(_profile.get("stamina", 100.0))), 13))
""")

if fails:
    print("\n".join(fails))
    print("FAIL")
    sys.exit(1)
io.open(P, "w", encoding="utf-8", newline="\n").write(src)

# ---- items.json: магазины/запасы, РПГ 1+1, str_req, тяжёлая броня −1 ОД ----
J = r"G:\Kimi project\Drop Zone\game\data\items.json"
data = json.load(io.open(J, encoding="utf-8"))
weap = {w["id"]: w for w in data["weapons"]}
def setw(wid, **kw):
    weap[wid].update(kw)
setw("Pistol", spare=12)
setw("Revolver_Small", spare=6)
setw("Revolver", spare=6)
setw("SMG", burst=2, spare=30)
setw("Shotgun", spare=6)
setw("AK", ammo=10, spare=20)
setw("Sniper", spare=5)
setw("Sniper_2", spare=3)
setw("GrenadeLauncher", ammo=3, spare=2)
setw("ShortCannon", spare=2)
setw("RocketLauncher", ammo=1, spare=1, reload_ap=3, str_req=4)
data["armor"]["body"][3]["ap_penalty"] = 1  # Тяжёлая броня «Джаггер»
io.open(J, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False, indent=2))
print("ALL_OK")
