# Патч D+E+F: силуэт инвентаря, звук, кровь, трупный лут, AoE-баланс
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

# --- D1) генератор силуэта бойца ---
sil_fn = """
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

func _toggle_inventory() -> void:"""
rep("func _toggle_inventory() -> void:", sil_fn, "sil_fn")

# --- D2) инвентарь: слоты поверх силуэта ---
old_sil = """	# --- силуэт бойца: слоты экипировки ---
	var sil := VBoxContainer.new()
	sil.add_theme_constant_override("separation", 6)
	hb.add_child(sil)
	var stats := Label.new()
	stats.text = "HP %d/%d   AP %d/%d\\nЗащита: %d\\nВес: %.1f/%.1f кг" % [
		f.hp, f.max_hp, f.ap, f.max_ap, _defense(f), _load_weight(f), _carry_limit(f)]
	sil.add_child(stats)
	var slots := [["Шлем", "helmets"], ["Корпус", "body"], ["Штаны", "pants"]]
	for s in slots:
		var b := Button.new()
		var it = f.armor[s[1]]
		b.text = "%s: %s" % [s[0], it["name"] if it else "—"]
		b.custom_minimum_size = Vector2(250, 42)
		var cat: String = s[1]
		b.tooltip_text = "Клик — снять; сюда можно перетащить броню из рюкзака"
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
		sil.add_child(b)
	var hands := Button.new()
	hands.text = "В руках: %s" % f.weapon.get("name", "?")
	hands.custom_minimum_size = Vector2(250, 42)"""
new_sil = """	# --- силуэт бойца: слоты экипировки поверх фигуры ---
	var sil := VBoxContainer.new()
	sil.add_theme_constant_override("separation", 6)
	hb.add_child(sil)
	var stats := Label.new()
	stats.text = "HP %d/%d   AP %d/%d\\nЗащита: %d\\nВес: %.1f/%.1f кг" % [
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
		b.tooltip_text = "Клик — снять; сюда можно перетащить броню из рюкзака"
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
	hands.position = Vector2(50, 152)
	hands.custom_minimum_size = Vector2(140, 52)"""
rep(old_sil, new_sil, "sil_layout")

rep("""	sil.add_child(hands)
	var knife := Label.new()""",
"""	fig.add_child(hands)
	var knife := Label.new()""", "sil_hands")

# --- E1) громкость звуков ---
rep("""	var a := AudioStreamPlayer.new()
	a.stream = _sfx[n]
	add_child(a)
	a.play()""",
"""	var a := AudioStreamPlayer.new()
	a.stream = _sfx[n]
	a.volume_db = 4.0
	add_child(a)
	a.play()""", "sfx_vol")

# --- E2) загрузка click/zone + эмбиент ветра ---
rep("""	for n in ["shot", "hit", "open", "step", "explosion", "death", "reload", "swap", "levelup"]:""",
"""	for n in ["shot", "hit", "open", "step", "explosion", "death", "reload", "swap", "levelup", "click", "zone"]:""", "sfx_list")

rep("""func _sfx_play(n: String) -> void:""",
"""func _ambient_start() -> void:
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

func _sfx_play(n: String) -> void:""", "ambient_fn")

rep("""	else:
		_load_sfx()
		_build_ui()""",
"""	else:
		_load_sfx()
		_ambient_start()
		_build_ui()""", "ambient_start")

# --- E3) клик на меню-кнопках и боевых кнопках ---
rep("""func _style_menu_button(b: Button) -> void:""",
"""func _style_menu_button(b: Button) -> void:
	b.pressed.connect(_sfx_play.bind("click"))""", "click_menu")

rep("""	btn.pressed.connect(_end_turn)
	layer.add_child(btn)""",
"""	btn.pressed.connect(_end_turn)
	btn.pressed.connect(_sfx_play.bind("click"))
	layer.add_child(btn)""", "click_endturn")

# --- F1) кровь при несмертельном попадании ---
rep("""	if d.hp <= 0:
		_kill(victim)
		if src_idx >= 0 and src_idx < _fighters.size():
			_fighters[src_idx].kills = int(_fighters[src_idx].kills) + 1
""",
"""	if d.hp <= 0:
		_kill(victim)
		if src_idx >= 0 and src_idx < _fighters.size():
			_fighters[src_idx].kills = int(_fighters[src_idx].kills) + 1
	else:
		_spawn_burst(d.node.position + Vector3(0, 1.0, 0), Color(0.55, 0.05, 0.08))
""", "blood")

# --- F2) трупный лут ---
rep("""	_log("%s выбыл из шоу!" % f.name)
	if _selected == i:""",
"""	_log("%s выбыл из шоу!" % f.name)
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
	if _selected == i:""", "corpse_loot")

# --- F3) взрыв не мажет: полный урон в центре, 60% по краю ---
rep("""			if vd <= aoe:
				var tot := 0
				for i in burst:
					if _rng.randf() < HIT_CHANCE:
						tot += w.get("damage", 10)
				if tot > 0:
					did = true
					_apply_damage(vi, tot, a.name, att)""",
"""			if vd <= aoe:
				# взрыв не мажет: полный урон в центре, 60% по краю радиуса
				var tot: int = w.get("damage", 10) * burst
				if vd > 0.5:
					tot = int(tot * 0.6)
				if tot > 0:
					did = true
					_apply_damage(vi, tot, a.name, att)""", "aoe_falloff")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
