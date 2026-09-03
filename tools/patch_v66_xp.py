# Патч 1: XP/уровни/крит/расходники для arena3d.gd
import io
p = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
s = io.open(p, encoding="utf-8").read()
orig = s

def rep(old, new, tag):
    global s
    n = s.count(old)
    if n != 1:
        print("FAIL", tag, "count=", n)
        raise SystemExit(1)
    s = s.replace(old, new)
    print("ok", tag)

# 1) подсказки статов
rep('"int": "бонус опыта (скоро)", "lck": "шанс крита (скоро)"}',
    '"int": "+10% к опыту за очко", "lck": "+3% к шансу крита (x1.5) за очко"}', "hints")

# 2) профиль: lvl/xp по умолчанию
rep('\t\t"stats": [_default_fighter_stats(), _default_fighter_stats(),\n\t\t\t_default_fighter_stats(), _default_fighter_stats()],\n\t}',
    '\t\t"stats": [_default_fighter_stats(), _default_fighter_stats(),\n\t\t\t_default_fighter_stats(), _default_fighter_stats()],\n\t\t"lvl": [1, 1, 1, 1],\n\t\t"xp": [0, 0, 0, 0],\n\t}', "prof_defaults")

# 3) загрузка lvl/xp
rep('\t\t_profile.stats[i] = st\n\t_profile.city = cfg.get_value("player", "city", "")',
    '\t\t_profile.stats[i] = st\n\t\t_profile.lvl[i] = int(cfg.get_value("fighter%d" % i, "lvl", 1))\n\t\t_profile.xp[i] = int(cfg.get_value("fighter%d" % i, "xp", 0))\n\t_profile.city = cfg.get_value("player", "city", "")', "prof_load")

# 4) сохранение lvl/xp
rep('\t\tfor k in STAT_KEYS:\n\t\t\tcfg.set_value("fighter%d" % i, k, _profile.stats[i][k])\n\tcfg.set_value("player", "city", _profile.city)',
    '\t\tfor k in STAT_KEYS:\n\t\t\tcfg.set_value("fighter%d" % i, k, _profile.stats[i][k])\n\t\tcfg.set_value("fighter%d" % i, "lvl", _profile.lvl[i])\n\t\tcfg.set_value("fighter%d" % i, "xp", _profile.xp[i])\n\tcfg.set_value("player", "city", _profile.city)', "prof_save")

# 5) очки с учётом уровня
rep('func _stat_points_left(st: Dictionary) -> int:\n\tvar spent := 0\n\tfor k in STAT_KEYS:\n\t\tspent += int(st.get(k, 0))\n\treturn STAT_POINTS - spent',
    'func _stat_points_left(st: Dictionary, lvl := 1) -> int:\n\tvar spent := 0\n\tfor k in STAT_KEYS:\n\t\tspent += int(st.get(k, 0))\n\treturn STAT_POINTS + 5 * (lvl - 1) - spent',
    "pts_left")

# 6) меню отряда: строка уровня
rep('\tvar st: Dictionary = _profile.stats[_squad_edit]\n\tvar left := _stat_points_left(st)\n\tvar pl := Label.new()\n\tpl.text = "Свободно очков: %d / %d" % [left, STAT_POINTS]',
    '\tvar st: Dictionary = _profile.stats[_squad_edit]\n\tvar left := _stat_points_left(st, _profile.lvl[_squad_edit])\n\tvar pl := Label.new()\n\tpl.text = "Уровень %d (опыт %d/%d) · Свободно очков: %d" % [_profile.lvl[_squad_edit], _profile.xp[_squad_edit], _xp_need(_profile.lvl[_squad_edit]), left]',
    "menu_pts")

# 7) спавн бойца: уровень/опыт/очки
rep('func _spawn_human(model: String, gx: int, gz: int, rot_y: float, weapon: String, team: Color, team_idx: int, fname: String, st: Dictionary = {}) -> void:',
    'func _spawn_human(model: String, gx: int, gz: int, rot_y: float, weapon: String, team: Color, team_idx: int, fname: String, st: Dictionary = {}, lvl := 1, xp := 0) -> void:\n\tif st.is_empty():\n\t\tst = _default_fighter_stats()', "spawn_sig")

rep('\tvar hp_max := _stat_hp(st)\n\tvar ap_max := _stat_ap(st)',
    '\tvar hp_max := _stat_hp(st) + 5 * (lvl - 1)\n\tvar ap_max := _stat_ap(st) + lvl / 3\n\tvar pts0 := _stat_points_left(st, lvl)', "spawn_derived")

rep('\t\t"backpack": [], "alive": true\n\t})',
    '\t\t"backpack": [], "alive": true,\n\t\t"lvl": lvl, "xp": xp, "kills": 0, "pts": pts0\n\t})', "spawn_dict")

rep('\t\t_spawn_human(red_models[i][0], cell.x, cell.y, _rng.randf_range(-30, 90),\n\t\t\tred_models[i][1], Color("#ff4757"), 0, _profile.names[i], _profile.stats[i])',
    '\t\t_spawn_human(red_models[i][0], cell.x, cell.y, _rng.randf_range(-30, 90),\n\t\t\tred_models[i][1], Color("#ff4757"), 0, _profile.names[i], _profile.stats[i], _profile.lvl[i], _profile.xp[i])', "spawn_teams")

# 8) блок XP/уровней + модальное окно прокачки
xp_lines = [
"",
"# ---------- опыт и уровни ----------",
"var _lvl_open := false",
"var _lvl_wrap: CenterContainer = null",
"",
"func _xp_need(lvl: int) -> int:",
"\treturn int(floor(100.0 * pow(1.2, lvl - 1)))",
"",
"func _recalc_derived(f: Dictionary, heal := false) -> void:",
"\tf.max_hp = _stat_hp(f.stats) + 5 * (int(f.lvl) - 1)",
"\tf.max_ap = _stat_ap(f.stats) + int(f.lvl) / 3",
"\tf.carry_base = _stat_carry(f.stats)",
"\tf.vision = _stat_vision(f.stats)",
"\tif heal:",
"\t\tf.hp = f.max_hp",
"\t\tf.ap = f.max_ap",
"\tf.hp = mini(int(f.hp), int(f.max_hp))",
"\tf.ap = mini(int(f.ap), int(f.max_ap))",
"",
"func _gain_xp(i: int, amount: int) -> void:",
"\tvar f = _fighters[i]",
"\tif not f.alive:",
"\t\treturn",
"\tvar bonus := 1.0 + 0.1 * int(f.stats.get(\"int\", 0))",
"\tf.xp = int(f.xp) + int(round(amount * bonus))",
"\tvar leveled := false",
"\twhile int(f.xp) >= _xp_need(int(f.lvl)):",
"\t\tf.xp = int(f.xp) - _xp_need(int(f.lvl))",
"\t\tf.lvl = int(f.lvl) + 1",
"\t\tf.pts = int(f.pts) + 5",
"\t\tleveled = true",
"\tif not leveled:",
"\t\treturn",
"\t_recalc_derived(f, true)",
"\t_sfx_play(\"levelup\")",
"\t_log(\"%s — УРОВЕНЬ %d! (+5 очков навыков)\" % [f.name, int(f.lvl)])",
"\tif f.team == 1:",
"\t\t# боты распределяют очки автоматически",
"\t\tvar keys := [\"str\", \"agi\", \"end\", \"per\"]",
"\t\tfor j in 5:",
"\t\t\tvar kk2: String = keys[_rng.randi() % keys.size()]",
"\t\t\tf.stats[kk2] = int(f.stats.get(kk2, 0)) + 1",
"\t\tf.pts = 0",
"\t\t_recalc_derived(f, true)",
"\telif not _lvl_open:",
"\t\t_show_levelup(i)",
"",
"func _lvl_add(f: Dictionary, k: String, d: int, val: Label, pts: Label) -> void:",
"\tif d > 0 and int(f.pts) <= 0:",
"\t\treturn",
"\tif d < 0 and int(f.stats.get(k, 0)) <= 0:",
"\t\treturn",
"\tf.stats[k] = int(f.stats.get(k, 0)) + d",
"\tf.pts = int(f.pts) - d",
"\tval.text = str(int(f.stats[k]))",
"\tpts.text = \"Свободно очков: %d\" % int(f.pts)",
"",
"func _lvl_confirm(f: Dictionary) -> void:",
"\t_recalc_derived(f, false)",
"\t_lvl_open = false",
"\tif _lvl_wrap:",
"\t\t_lvl_wrap.queue_free()",
"\t\t_lvl_wrap = null",
"\t_refresh_fighter_panel()",
"\t_refresh_squad()",
"\t_log(\"%s: навыки обновлены — HP %d, ОД %d, обзор %d\" % [f.name, int(f.max_hp), int(f.max_ap), int(f.vision)])",
"",
"func _show_levelup(i: int) -> void:",
"\tif _lvl_open or i < 0:",
"\t\treturn",
"\tvar f = _fighters[i]",
"\t_lvl_open = true",
"\tvar wrap := CenterContainer.new()",
"\twrap.set_anchors_preset(Control.PRESET_FULL_RECT)",
"\t_ui.layer.add_child(wrap)",
"\t_lvl_wrap = wrap",
"\tvar panel := PanelContainer.new()",
"\tpanel.custom_minimum_size = Vector2(560, 0)",
"\tpanel.add_theme_stylebox_override(\"panel\", _frame_box())",
"\twrap.add_child(panel)",
"\tvar vb := VBoxContainer.new()",
"\tpanel.add_child(vb)",
"\tvar t := Label.new()",
"\tt.text = \"УРОВЕНЬ %d — %s\" % [int(f.lvl), f.name]",
"\tt.add_theme_font_size_override(\"font_size\", 24)",
"\tt.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER",
"\tvb.add_child(t)",
"\tvar sub := Label.new()",
"\tsub.text = \"Распредели очки навыков — действуют сразу, нераспределённые сохранятся\"",
"\tsub.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER",
"\tsub.add_theme_font_size_override(\"font_size\", 13)",
"\tvb.add_child(sub)",
"\tvar pts := Label.new()",
"\tpts.text = \"Свободно очков: %d\" % int(f.pts)",
"\tpts.add_theme_font_size_override(\"font_size\", 17)",
"\tvb.add_child(pts)",
"\tfor k in STAT_KEYS:",
"\t\tvar row := HBoxContainer.new()",
"\t\tvb.add_child(row)",
"\t\tvar lb := Label.new()",
"\t\tlb.text = STAT_NAMES[k]",
"\t\tlb.custom_minimum_size = Vector2(150, 0)",
"\t\trow.add_child(lb)",
"\t\tvar val := Label.new()",
"\t\tval.text = str(int(f.stats.get(k, 0)))",
"\t\tval.custom_minimum_size = Vector2(36, 0)",
"\t\tval.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER",
"\t\trow.add_child(val)",
"\t\tvar minus := Button.new()",
"\t\tminus.text = \"-\"",
"\t\tminus.pressed.connect(_lvl_add.bind(f, k, -1, val, pts))",
"\t\trow.add_child(minus)",
"\t\tvar plus := Button.new()",
"\t\tplus.text = \"+\"",
"\t\tplus.pressed.connect(_lvl_add.bind(f, k, 1, val, pts))",
"\t\trow.add_child(plus)",
"\t\tvar hint := Label.new()",
"\t\thint.text = \"  \" + STAT_HINTS[k]",
"\t\thint.add_theme_font_size_override(\"font_size\", 12)",
"\t\trow.add_child(hint)",
"\tvar ok := Button.new()",
"\tok.text = \"ПОДТВЕРДИТЬ\"",
"\t_style_menu_button(ok)",
"\tok.pressed.connect(_lvl_confirm.bind(f))",
"\tvb.add_child(ok)",
"",
]
xp_block = "\n".join(xp_lines)
rep("\nfunc _reload_selected() -> void:", xp_block + "func _reload_selected() -> void:", "xp_block")

# 9) входные блокировки при открытом окне прокачки
rep("if not _rmb_moved and not _busy and not _game_over and not _menu_open:",
    "if not _rmb_moved and not _busy and not _game_over and not _menu_open and not _lvl_open:", "guard_rmb")
rep("\tif _busy or _game_over or _menu_open:\n\t\treturn\n\tif event is InputEventKey and event.pressed:",
    "\tif _busy or _game_over or _menu_open or _lvl_open:\n\t\treturn\n\tif event is InputEventKey and event.pressed:", "guard_input")
rep("func _end_turn() -> void:\n\tif _busy or _game_over:\n\t\treturn",
    "func _end_turn() -> void:\n\tif _busy or _game_over or _lvl_open:\n\t\treturn", "guard_endturn")
rep("if _selected >= 0 and _selected < _fighters.size() and not _busy and not _game_over and not _menu_open:",
    "if _selected >= 0 and _selected < _fighters.size() and not _busy and not _game_over and not _menu_open and not _lvl_open:", "guard_aim")

# 10) урон: индекс атакующего для счёта убийств
rep("func _apply_damage(victim: int, dmg: int, src_name: String) -> void:",
    "func _apply_damage(victim: int, dmg: int, src_name: String, src_idx := -1) -> void:", "dmg_sig")
rep("\tif d.hp <= 0:\n\t\t_kill(victim)\n",
    "\tif d.hp <= 0:\n\t\t_kill(victim)\n\t\tif src_idx >= 0 and src_idx < _fighters.size():\n\t\t\t_fighters[src_idx].kills = int(_fighters[src_idx].kills) + 1\n", "dmg_kill")

# 11) выстрел AoE: флаг попадания + XP + трата расходника
rep("\t\tfor vi in _fighters.size():\n\t\t\tvar v = _fighters[vi]\n\t\t\tif not v.alive or vi == att:\n\t\t\t\tcontinue",
    "\t\tvar did := false\n\t\tfor vi in _fighters.size():\n\t\t\tvar v = _fighters[vi]\n\t\t\tif not v.alive or vi == att:\n\t\t\t\tcontinue", "aoe_did")
rep("\t\t\t\tif tot > 0:\n\t\t\t\t\t_apply_damage(vi, tot, a.name)\n\t\treturn",
    "\t\t\t\tif tot > 0:\n\t\t\t\t\tdid = true\n\t\t\t\t\t_apply_damage(vi, tot, a.name, att)\n\t\tif did:\n\t\t\t_gain_xp(att, 50)\n\t\tif w.get(\"consumable\", false):\n\t\t\t_spend_consumable(att)\n\t\treturn", "aoe_xp")

# 12) обычный выстрел: крит от Удачи + XP
rep("\tvar chance := _hit_chance(a.cell, d.cell)\n\tvar total := 0\n\tfor i in burst:\n\t\tif _rng.randf() < chance:\n\t\t\ttotal += w.get(\"damage\", 10)\n\tif total > 0:\n\t\t_apply_damage(def, total, a.name)\n\telse:",
    "\tvar chance := _hit_chance(a.cell, d.cell)\n\tvar total := 0\n\tvar crit := false\n\tvar lck: int = int(a.stats.get(\"lck\", 0))\n\tfor i in burst:\n\t\tif _rng.randf() < chance:\n\t\t\tvar dm: int = w.get(\"damage\", 10)\n\t\t\tif lck > 0 and _rng.randf() < 0.03 * lck:\n\t\t\t\tdm = int(dm * 1.5)\n\t\t\t\tcrit = true\n\t\t\ttotal += dm\n\tif total > 0:\n\t\t_apply_damage(def, total, a.name, att)\n\t\t_gain_xp(att, 50)\n\t\tif crit:\n\t\t\t_log(\"КРИТ! x1.5 урона\")\n\telse:", "shoot_hit")

# 13) сохранение прогресса при конце боя
rep("\t\t_game_over = true\n\t\t_deselect()\n",
    "\t\t_game_over = true\n\t\t_deselect()\n\t\t# прогресс бойцов игрока сохраняется в профиль\n\t\tfor pi in _mode:\n\t\t\tvar pf = _fighters[pi]\n\t\t\t_profile.stats[pi] = pf.stats\n\t\t\t_profile.lvl[pi] = int(pf.lvl)\n\t\t\t_profile.xp[pi] = int(pf.xp)\n\t\t_save_profile()\n", "persist")

# 14) панель бойца: уровень + кнопка навыков
rep("\tw.text = \"В руках: %s%s\" % [f.weapon.get(\"name\", \"?\"), ammo_txt]\n\tbox.add_child(w)",
    "\tw.text = \"В руках: %s%s\" % [f.weapon.get(\"name\", \"?\"), ammo_txt]\n\tbox.add_child(w)\n\tvar lv := Label.new()\n\tlv.text = \"Ур. %d · Опыт %d/%d · Убийств: %d\" % [int(f.lvl), int(f.xp), _xp_need(int(f.lvl)), int(f.kills)]\n\tbox.add_child(lv)", "panel_lv")

rep("\trl.pressed.connect(_reload_selected)\n\trow.add_child(rl)\n\t_refresh_card()",
    "\trl.pressed.connect(_reload_selected)\n\trow.add_child(rl)\n\tif int(f.get(\"pts\", 0)) > 0 and f.team == 0:\n\t\tvar pb := Button.new()\n\t\tpb.text = \"Навыки +%d\" % int(f.pts)\n\t\tpb.pressed.connect(_show_levelup.bind(_selected))\n\t\trow.add_child(pb)\n\t_refresh_card()", "panel_btn")

# 15) звук levelup в загрузку
rep('for n in ["shot", "hit", "open", "step", "explosion", "death", "reload", "swap"]:',
    'for n in ["shot", "hit", "open", "step", "explosion", "death", "reload", "swap", "levelup"]:', "sfxlist")

# 16) трата расходников (граната/молотов — одноразовые)
rep("func _reload_selected() -> void:",
    "func _spend_consumable(att: int) -> void:\n\tvar a = _fighters[att]\n\t_log(\"%s: %s потрачено\" % [a.name, a.weapon.get(\"name\", \"?\")])\n\ta.gun = {}\n\ta.weapon = a.melee\n\nfunc _reload_selected() -> void:", "spend_fn")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
