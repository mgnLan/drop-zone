# Патч 2: разрушаемые укрытия, входимые дома, огонь Молотова
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

# 0) новые словари состояния
rep("var _aim_col := Color(-1.0, -1.0, -1.0)",
    "var _aim_col := Color(-1.0, -1.0, -1.0)\n"
    "var _houses: Array = []            # {cells, door, node, faded}\n"
    "var _house_at := {}                # ключ клетки -> id дома\n"
    "var _covers := {}                  # центр -> {hp, cells, node, heavy}\n"
    "var _cover_at := {}                # ключ клетки -> центр укрытия\n"
    "var _fire := {}                    # Vector2i -> осталось раундов\n"
    "var _fire_nodes := {}              # Vector2i -> Node3D", "state_vars")

# 1) дома: входимые, с дверью и мерцающей подсветкой двери
old_houses = """func _generate_houses() -> void:
	# дома ×3 от исходника; на маленьких картах — соразмерно меньше
	var k: float = _grid_n / 40.0
	var fp := maxi(3, int(8 * k))
	var n := maxi(1, int(_rng.randi_range(3, 4) * k))
	for i in n:
		var cell := _free_cell(6, _half_n - 2, fp)
		if cell.x < 0:
			continue
		_claim(cell, fp)
		for ox in range(-fp / 2, fp / 2 + 1):  # дома блокируют обзор (туман войны)
			for oz in range(-fp / 2, fp / 2 + 1):
				_blocks_sight["%d,%d" % [cell.x + ox, cell.y + oz]] = true
		var model: String = HOUSE_MODELS[_rng.randi() % HOUSE_MODELS.size()]
		var pal: String = HOUSE_PALETTES[_rng.randi() % HOUSE_PALETTES.size()]
		_place(B + model, gw(cell.x, cell.y), _rng.randf() * 360.0, 3.0 * k + 0.8, pal)
"""
new_houses = """func _generate_houses() -> void:
	# дома ×3 от исходника; на маленьких картах — соразмерно меньше; ВХОДИМЫЕ
	var k: float = _grid_n / 40.0
	var fp := maxi(3, int(8 * k))
	var n := maxi(1, int(_rng.randi_range(3, 4) * k))
	for i in n:
		var cell := _free_cell(6, _half_n - 2, fp)
		if cell.x < 0:
			continue
		_claim(cell, fp)
		var hcells: Array = []
		for ox in range(-fp / 2, fp / 2 + 1):  # дома блокируют обзор (туман войны)
			for oz in range(-fp / 2, fp / 2 + 1):
				var hc := Vector2i(cell.x + ox, cell.y + oz)
				_blocks_sight[_key(hc)] = true
				hcells.append(hc)
		var model: String = HOUSE_MODELS[_rng.randi() % HOUSE_MODELS.size()]
		var pal: String = HOUSE_PALETTES[_rng.randi() % HOUSE_PALETTES.size()]
		var hnode := _place(B + model, gw(cell.x, cell.y), _rng.randf() * 360.0, 3.0 * k + 0.8, pal)
		# дверь — первая свободная клетка у края дома
		var door := Vector2i(-1, -1)
		var half := fp / 2 + 1
		var cands := [Vector2i(cell.x, cell.y + half), Vector2i(cell.x, cell.y - half),
			Vector2i(cell.x + half, cell.y), Vector2i(cell.x - half, cell.y)]
		for cand in cands:
			if cand.x < 0 or cand.y < 0 or cand.x >= _grid_n or cand.y >= _grid_n:
				continue
			if _occupied.has(_key(cand)):
				continue
			door = cand
			break
		var hid := _houses.size()
		for hc2 in hcells:
			_house_at[_key(hc2)] = hid
		_houses.append({"cells": hcells, "door": door, "node": hnode, "faded": false})
		if door.x >= 0:
			var dpad := MeshInstance3D.new()
			var dcyl := CylinderMesh.new()
			dcyl.top_radius = 0.4
			dcyl.bottom_radius = 0.4
			dcyl.height = 0.04
			dpad.mesh = dcyl
			dpad.material_override = _mat(Color.BLACK, 0.0, 1.0, Color(1.0, 0.6, 0.15), 3.0)
			dpad.position = gw(door.x, door.y, 0.03)
			add_child(dpad)

func _house_of(c: Vector2i) -> int:
	# id дома, которому принадлежит клетка; дверь считается частью дома
	var k := _key(c)
	if _house_at.has(k):
		return int(_house_at[k])
	for hi in _houses.size():
		if _houses[hi].door == c:
			return hi
	return -1

func _can_enter(from: Vector2i, to: Vector2i) -> bool:
	# внутрь дома — только через дверь или из другой клетки того же дома
	var hk := _key(to)
	if not _house_at.has(hk):
		return true
	var h: int = _house_at[hk]
	if _house_at.get(_key(from), -1) == h:
		return true
	return from == _houses[h].door

func _update_house_fade() -> void:
	# дом с бойцом внутри становится полупрозрачным
	for hi in _houses.size():
		var h = _houses[hi]
		var inside := false
		for f in _fighters:
			if f.alive and _house_at.get(_key(f.cell), -1) == hi:
				inside = true
				break
		if inside != h.faded:
			h.faded = inside
			var tr: float = 0.7 if inside else 0.0
			for mi in h.node.find_children("*", "MeshInstance3D", true, false):
				mi.transparency = tr
"""
rep(old_houses, new_houses, "houses")

# 2) укрытия: hp и разрушаемость
old_covers = """		_claim(cell, 2)
		var model: String = COVER_MODELS[_rng.randi() % COVER_MODELS.size()]
		var scl := 1.3 if model == "Platform_2x2.gltf" else 1.2
		# тяжёлые укрытия блокируют обзор и огонь, лёгкие — только снижают шанс
		if model == "AC_Stacked.gltf" or model == "Platform_2x2.gltf":
			for ox in range(-1, 2):
				for oz in range(-1, 2):
					_blocks_sight["%d,%d" % [cell.x + ox, cell.y + oz]] = true
		else:
			_soft_cover[_key(cell)] = true
		_place(C + model, gw(cell.x, cell.y), _rng.randf() * 360.0, scl)
"""
new_covers = """		_claim(cell, 2)
		var model: String = COVER_MODELS[_rng.randi() % COVER_MODELS.size()]
		var scl := 1.3 if model == "Platform_2x2.gltf" else 1.2
		var heavy: bool = model == "AC_Stacked.gltf" or model == "Platform_2x2.gltf"
		# тяжёлые укрытия блокируют обзор и огонь, лёгкие — только снижают шанс
		var ccells: Array = []
		for ox in range(-1, 2):
			for oz in range(-1, 2):
				var cc3 := Vector2i(cell.x + ox, cell.y + oz)
				ccells.append(cc3)
				if heavy:
					_blocks_sight[_key(cc3)] = true
		if not heavy:
			_soft_cover[_key(cell)] = true
		var cnode := _place(C + model, gw(cell.x, cell.y), _rng.randf() * 360.0, scl)
		# разрушаемость: тяжёлые держат 3 взрыва, лёгкие — 2
		var ck := _key(cell)
		_covers[ck] = {"hp": 3 if heavy else 2, "cells": ccells, "node": cnode, "heavy": heavy}
		for cc4 in ccells:
			_cover_at[_key(cc4)] = ck

func _destroy_cover(ck: String) -> void:
	var rec = _covers.get(ck)
	if rec == null:
		return
	for cc5 in rec.cells:
		var kk5 := _key(cc5)
		_occupied.erase(kk5)
		_blocks_sight.erase(kk5)
		_soft_cover.erase(kk5)
		_cover_at.erase(kk5)
	_spawn_burst(rec.node.position + Vector3(0, 0.5, 0), Color(0.6, 0.55, 0.5))
	rec.node.queue_free()
	_covers.erase(ck)
	_log("Укрытие разрушено взрывом!")

func _damage_covers(cell: Vector2i, radius: int) -> void:
	# взрыв бьёт по укрытиям в радиусе; у каждого укрытия есть прочность
	var done := {}
	for dx in range(-radius, radius + 1):
		for dz in range(-radius, radius + 1):
			var c2 := Vector2i(cell.x + dx, cell.y + dz)
			var kk6 := _key(c2)
			if _cover_at.has(kk6) and not done.has(_cover_at[kk6]):
				var ck2: String = _cover_at[kk6]
				done[ck2] = true
				var rec2 = _covers.get(ck2)
				if rec2 != null:
					rec2.hp = int(rec2.hp) - 1
					if int(rec2.hp) <= 0:
						_destroy_cover(ck2)
"""
rep(old_covers, new_covers, "covers")

# 3) взрыв принимает радиус и бьёт по укрытиям
rep("func _explode_at(cell: Vector2i) -> void:\n\tvar pos := gw(cell.x, cell.y, 0.7)",
    "func _explode_at(cell: Vector2i, radius := 1) -> void:\n\t_damage_covers(cell, radius)\n\tvar pos := gw(cell.x, cell.y, 0.7)", "explode_sig")
rep("\t\t_explode_at(d.cell)\n\t\t_log(\"%s: %s — взрыв на площади!\" % [a.name, w.get(\"name\", \"?\")])",
    "\t\t_explode_at(d.cell, aoe)\n\t\t_log(\"%s: %s — взрыв на площади!\" % [a.name, w.get(\"name\", \"?\")])", "explode_call")

# 4) огонь: функции
fire_lines = [
"",
"# ---------- огонь (Молотов / зажигательная граната) ----------",
"func _make_flame(c: Vector2i) -> Node3D:",
"\tvar root := Node3D.new()",
"\troot.position = gw(c.x, c.y)",
"\tvar fl := MeshInstance3D.new()",
"\tvar sm := SphereMesh.new()",
"\tsm.radius = 0.22",
"\tsm.height = 0.5",
"\tfl.mesh = sm",
"\tfl.material_override = _mat(Color(1.0, 0.45, 0.05), 0.0, 1.0, Color(1.0, 0.5, 0.05), 4.0)",
"\tfl.position = Vector3(0, 0.25, 0)",
"\troot.add_child(fl)",
"\tvar l := OmniLight3D.new()",
"\tl.light_color = Color(1.0, 0.55, 0.15)",
"\tl.light_energy = 2.5",
"\tl.omni_range = 4.0",
"\tl.position = Vector3(0, 0.8, 0)",
"\troot.add_child(l)",
"\tadd_child(root)",
"\treturn root",
"",
"func _ignite(cell: Vector2i, radius: int) -> void:",
"\tfor dx in range(-radius, radius + 1):",
"\t\tfor dz in range(-radius, radius + 1):",
"\t\t\tvar cf := Vector2i(cell.x + dx, cell.y + dz)",
"\t\t\tif cf.x < 0 or cf.y < 0 or cf.x >= _grid_n or cf.y >= _grid_n:",
"\t\t\t\tcontinue",
"\t\t\tif _house_at.has(_key(cf)):",
"\t\t\t\tcontinue",
"\t\t\t_fire[cf] = 3",
"\t\t\tif not _fire_nodes.has(cf):",
"\t\t\t\t_fire_nodes[cf] = _make_flame(cf)",
"\t_log(\"Поджог! Огонь горит 3 раунда и жжёт стоящих (-8 HP)\")",
"",
"func _tick_fire() -> void:",
"\tif _fire.is_empty():",
"\t\treturn",
"\tvar expired: Array = []",
"\tfor c in _fire.keys():",
"\t\tvar sk := _key(c)",
"\t\tif _unit_at.has(sk):",
"\t\t\tvar vi: int = _unit_at[sk]",
"\t\t\t_apply_damage(vi, 8, \"Огонь\", -1)",
"\t\t\tif _game_over:",
"\t\t\t\treturn",
"\t\t_fire[c] = int(_fire[c]) - 1",
"\t\tif int(_fire[c]) <= 0:",
"\t\t\texpired.append(c)",
"\tfor c2 in expired:",
"\t\t_fire.erase(c2)",
"\t\tif _fire_nodes.has(c2):",
"\t\t\t_fire_nodes[c2].queue_free()",
"\t\t\t_fire_nodes.erase(c2)",
"",
]
fire_block = "\n".join(fire_lines)
rep("\nfunc _damage_covers(", fire_block + "func _damage_covers(", "fire_fns")

# 5) поджог в AoE-ветке выстрела (burn)
rep("\t\tif did:\n\t\t\t_gain_xp(att, 50)\n\t\tif w.get(\"consumable\", false):",
    "\t\tif did:\n\t\t\t_gain_xp(att, 50)\n\t\tif w.get(\"burn\", false):\n\t\t\t_ignite(d.cell, aoe)\n\t\tif w.get(\"consumable\", false):", "burn_hook")

# 6) тик огня в конце раунда
rep("\tif not _game_over:\n\t\t_turn += 1",
    "\tif not _game_over:\n\t\t_tick_fire()\n\tif not _game_over:\n\t\t_turn += 1", "fire_tick")

# 7) LOS с учётом домов
rep("""func _los(a: Vector2i, b: Vector2i) -> bool:
	# линия видимости по клеткам (Брезенхэм); блокируют дома и тяжёлые укрытия
	var x0: int = a.x""",
"""func _los(a: Vector2i, b: Vector2i) -> bool:
	# линия видимости по клеткам (Брезенхэм); блокируют дома и тяжёлые укрытия
	# дома: снаружи внутрь (и обратно) стрелять нельзя; внутри одного дома — можно
	var ha := _house_of(a)
	var hb := _house_of(b)
	if ha != hb:
		return false
	if ha >= 0:
		return true
	var x0: int = a.x""", "los_houses")

# 8) BFS достижимости: вход в дом через дверь
rep("""			var k := _key(n)
			if _occupied.has(k) or _unit_at.has(k):
				continue
			if not res.has(n):""",
"""			var k := _key(n)
			if _unit_at.has(k):
				continue
			if _occupied.has(k):
				if not _house_at.has(k) or not _can_enter(cur, n):
					continue
			if not res.has(n):""", "bfs_houses")

# 9) шаг бота: дома через дверь + обход огня
rep("""		var k := _key(n)
		if _occupied.has(k) or _unit_at.has(k):
			continue
		var nd := Vector2(n.x - target.x, n.y - target.y).length()""",
"""		var k := _key(n)
		if _unit_at.has(k) or _fire.has(n):
			continue
		if _occupied.has(k):
			if not _house_at.has(k) or not _can_enter(f.cell, n):
				continue
		var nd := Vector2(n.x - target.x, n.y - target.y).length()""", "bot_step")

# 10) мерцание домов после каждого действия (вызывается из _update_fog)
rep("""		ef.node.visible = vis
""",
"""		ef.node.visible = vis
	_update_house_fade()
""", "fade_hook")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
