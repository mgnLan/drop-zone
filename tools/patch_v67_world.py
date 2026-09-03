# Патч A: бетон/свет, дома без полос, двери к центру, деревья/камни/бочки, зона
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

# A1) переменные зоны
rep("var _fire_nodes := {}              # Vector2i -> Node3D",
    "var _fire_nodes := {}              # Vector2i -> Node3D\n"
    "var _zone_min := Vector2i(0, 0)\nvar _zone_max := Vector2i(0, 0)\n"
    "var _zone_phase := 0\nvar _zone_walls := []", "zone_vars")

# A2) инициализация зоны в _ready
rep("\t_spawn_teams()\n\t_setup_lighting()",
    "\t_spawn_teams()\n\t_zone_min = Vector2i(0, 0)\n\t_zone_max = Vector2i(_grid_n - 1, _grid_n - 1)\n\t_update_zone_walls()\n\t_setup_lighting()", "zone_init")

# A3) бетон темнее + сетка темнее
rep("inner.material_override = _mat(Color(0.52, 0.50, 0.46), 0.0, 0.95)  # бетон",
    "inner.material_override = _mat(Color(0.30, 0.295, 0.28), 0.0, 0.97)  # бетон — серый, не белый", "concrete")
rep("var grid_mat := _mat(Color(0.20, 0.20, 0.21), 0.0, 0.95)",
    "var grid_mat := _mat(Color(0.15, 0.15, 0.16), 0.0, 0.97)", "grid")

# A4) свет приглушаем (пол пересвечивали споты и glow)
rep("sp.light_energy = 16.0", "sp.light_energy = 8.0", "spots")
rep("center_spot.light_energy = 20.0", "center_spot.light_energy = 10.0", "center_spot")
rep("moon.light_energy = 1.1", "moon.light_energy = 0.9", "moon")
rep("env.ambient_light_energy = 0.9", "env.ambient_light_energy = 0.75", "ambient")
rep("env.glow_intensity = 0.8", "env.glow_intensity = 0.45", "glow")

# A5) дома: дверь к центру + однотонная окраска вместо полосатых текстур
rep("""		# дверь — первая свободная клетка у края дома
		var door := Vector2i(-1, -1)
		var half := fp / 2 + 1
		var cands := [Vector2i(cell.x, cell.y + half), Vector2i(cell.x, cell.y - half),
			Vector2i(cell.x + half, cell.y), Vector2i(cell.x - half, cell.y)]
		for cand in cands:""",
"""		# дверь — смотрит к центру карты, не к краю
		var door := Vector2i(-1, -1)
		var half := fp / 2 + 1
		var cands := [Vector2i(cell.x, cell.y + half), Vector2i(cell.x, cell.y - half),
			Vector2i(cell.x + half, cell.y), Vector2i(cell.x - half, cell.y)]
		cands.sort_custom(func(p7, q7):
			return Vector2(p7.x - _half_n, p7.y - _half_n).length() < Vector2(q7.x - _half_n, q7.y - _half_n).length())
		for cand in cands:""", "door_center")

rep("""		var hnode := _place(B + model, gw(cell.x, cell.y), _rng.randf() * 360.0, 3.0 * k + 0.8, pal)""",
"""		var hnode := _place(B + model, gw(cell.x, cell.y), _rng.randf() * 360.0, 3.0 * k + 0.8, pal)
		var tints := [Color(0.60, 0.55, 0.48), Color(0.48, 0.51, 0.55), Color(0.58, 0.46, 0.38), Color(0.45, 0.49, 0.42)]
		_paint_house(hnode, tints[_rng.randi() % tints.size()])""", "house_paint_call")

paint_fn = """
func _paint_house(node: Node3D, col: Color) -> void:
	# однотонная штукатурка вместо полосатых текстур-атласов
	var m := _mat(col, 0.0, 0.92)
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = m

func _make_tree(pos: Vector3) -> Node3D:
	var root := Node3D.new()
	root.position = pos
	var trunk := MeshInstance3D.new()
	var tcyl := CylinderMesh.new()
	tcyl.top_radius = 0.07
	tcyl.bottom_radius = 0.11
	tcyl.height = 0.7
	trunk.mesh = tcyl
	trunk.material_override = _mat(Color(0.30, 0.22, 0.14), 0.0, 0.95)
	trunk.position.y = 0.35
	root.add_child(trunk)
	var leaf_mat := _mat(Color(0.16, 0.30, 0.14), 0.0, 0.9)
	var s1 := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.42
	sph.height = 0.84
	s1.mesh = sph
	s1.material_override = leaf_mat
	s1.position.y = 0.95
	root.add_child(s1)
	var s2 := MeshInstance3D.new()
	var sph2 := SphereMesh.new()
	sph2.radius = 0.28
	sph2.height = 0.56
	s2.mesh = sph2
	s2.material_override = leaf_mat
	s2.position = Vector3(0.12, 1.3, -0.08)
	root.add_child(s2)
	add_child(root)
	return root

func _make_rock(pos: Vector3) -> Node3D:
	var rock := MeshInstance3D.new()
	var sph := SphereMesh.new()
	sph.radius = 0.55
	sph.height = 1.1
	rock.mesh = sph
	rock.material_override = _mat(Color(0.42, 0.42, 0.44), 0.0, 1.0)
	rock.scale = Vector3(1.0, 0.85, 0.85)
	rock.rotation_degrees.y = _rng.randf() * 360.0
	rock.position = pos + Vector3(0, 0.25, 0)
	add_child(rock)
	return rock

func _make_barrel(pos: Vector3) -> Node3D:
	var b := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.26
	cyl.bottom_radius = 0.26
	cyl.height = 0.72
	b.mesh = cyl
	b.material_override = _mat(Color(0.55, 0.12, 0.08), 0.35, 0.5)
	b.position = pos + Vector3(0, 0.36, 0)
	add_child(b)
	return b

func _explode_barrel(c: Vector2i) -> void:
	# бочка взрывается: урон 20 по своей и соседним клеткам, возможна цепная реакция
	_explode_at(c, 1)
	for vi in _fighters.size():
		var v = _fighters[vi]
		if not v.alive:
			continue
		if maxi(absi(v.cell.x - c.x), absi(v.cell.y - c.y)) <= 1:
			_apply_damage(vi, 20, "Бочка", -1)
			if _game_over:
				return
"""
rep("\n# ---------------- ЛУТ (items.json) ----------------", paint_fn + "\n# ---------------- ЛУТ (items.json) ----------------", "maker_fns")

# A6) новые укрытия в конце _generate_covers
rep("""		var ck := _key(cell)
		_covers[ck] = {"hp": 3 if heavy else 2, "cells": ccells, "node": cnode, "heavy": heavy}
		for cc4 in ccells:
			_cover_at[_key(cc4)] = ck
""",
"""		var ck := _key(cell)
		_covers[ck] = {"hp": 3 if heavy else 2, "cells": ccells, "node": cnode, "heavy": heavy}
		for cc4 in ccells:
			_cover_at[_key(cc4)] = ck
	# деревья — лёгкое укрытие (hp 2)
	for i in maxi(3, int(_rng.randi_range(8, 12) * k)):
		var tc := _free_cell(3, _half_n, 1)
		if tc.x < 0:
			continue
		_claim(tc, 1)
		_soft_cover[_key(tc)] = true
		var tnode := _make_tree(gw(tc.x, tc.y))
		_covers[_key(tc)] = {"hp": 2, "cells": [tc], "node": tnode, "heavy": false}
		_cover_at[_key(tc)] = _key(tc)
	# валуны — тяжёлое укрытие (hp 4), блокируют обзор
	for i in maxi(2, int(_rng.randi_range(4, 6) * k)):
		var rc := _free_cell(3, _half_n, 1)
		if rc.x < 0:
			continue
		_claim(rc, 1)
		_blocks_sight[_key(rc)] = true
		var rnode := _make_rock(gw(rc.x, rc.y))
		_covers[_key(rc)] = {"hp": 4, "cells": [rc], "node": rnode, "heavy": true}
		_cover_at[_key(rc)] = _key(rc)
	# бочки с топливом — взрываются (hp 1), урон 20 вокруг
	for i in maxi(2, int(_rng.randi_range(4, 6) * k)):
		var bc := _free_cell(3, _half_n, 1)
		if bc.x < 0:
			continue
		_claim(bc, 1)
		var bnode := _make_barrel(gw(bc.x, bc.y))
		_covers[_key(bc)] = {"hp": 1, "cells": [bc], "node": bnode, "heavy": false, "barrel": true}
		_cover_at[_key(bc)] = _key(bc)
""", "new_covers")

# A7) бочка взрывается при разрушении
rep("""	_covers.erase(ck)
	_log("Укрытие разрушено взрывом!")""",
"""	_covers.erase(ck)
	_log("Укрытие разрушено взрывом!")
	if rec.get("barrel", false):
		_explode_barrel(rec.cells[0])""", "barrel_hook")

# A8) функции зоны — перед туманом войны
zone_lines = [
"",
"# ---------- сужающаяся зона (королевская битва) ----------",
"func _in_zone(c: Vector2i) -> bool:",
"\treturn c.x >= _zone_min.x and c.x <= _zone_max.x and c.y >= _zone_min.y and c.y <= _zone_max.y",
"",
"func _update_zone_walls() -> void:",
"\tif _zone_walls.is_empty():",
"\t\tfor i in 4:",
"\t\t\tvar w := MeshInstance3D.new()",
"\t\t\tw.mesh = BoxMesh.new()",
"\t\t\tvar m := _mat(Color(1.0, 0.12, 0.22, 0.28), 0.0, 1.0, Color(1.0, 0.12, 0.22), 1.6)",
"\t\t\tm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA",
"\t\t\tw.material_override = m",
"\t\t\tadd_child(w)",
"\t\t\t_zone_walls.append(w)",
"\tvar p0: Vector3 = gw(_zone_min.x, _zone_min.y) - Vector3(CELL * 0.5, 0, CELL * 0.5)",
"\tvar p1: Vector3 = gw(_zone_max.x, _zone_max.y) + Vector3(CELL * 0.5, 0, CELL * 0.5)",
"\tvar h := 2.4",
"\tvar t := 0.12",
"\tvar midx: float = (p0.x + p1.x) * 0.5",
"\tvar midz: float = (p0.z + p1.z) * 0.5",
"\tvar sizes := [Vector3(p1.x - p0.x, h, t), Vector3(p1.x - p0.x, h, t), Vector3(t, h, p1.z - p0.z), Vector3(t, h, p1.z - p0.z)]",
"\tvar poss := [Vector3(midx, h * 0.5, p0.z), Vector3(midx, h * 0.5, p1.z), Vector3(p0.x, h * 0.5, midz), Vector3(p1.x, h * 0.5, midz)]",
"\tfor i in 4:",
"\t\t(_zone_walls[i].mesh as BoxMesh).size = sizes[i]",
"\t\t_zone_walls[i].position = poss[i]",
"",
"func _tick_zone() -> void:",
"\t# сужение каждый 2-й раунд начиная с 3-го; снаружи — нарастающий урон",
"\tif _turn >= 3 and _turn % 2 == 1 and _zone_max.x - _zone_min.x > 6:",
"\t\t_zone_min += Vector2i(1, 1)",
"\t\t_zone_max -= Vector2i(1, 1)",
"\t\t_zone_phase += 1",
"\t\t_update_zone_walls()",
"\t\t_sfx_play(\"zone\")",
"\t\t_log(\"ЗОНА СУЖАЕТСЯ! Снаружи — урон каждый раунд\")",
"\tif _zone_phase == 0:",
"\t\treturn",
"\tvar dmg := 4 + 2 * _zone_phase",
"\tfor fi in _fighters.size():",
"\t\tvar f = _fighters[fi]",
"\t\tif f.alive and not _in_zone(f.cell):",
"\t\t\t_log(\"%s вне зоны! -%d HP\" % [f.name, dmg])",
"\t\t\t_apply_damage(fi, dmg, \"Зона\", -1)",
"\t\t\tif _game_over:",
"\t\t\t\treturn",
"",
]
zone_block = "\n".join(zone_lines)
rep("\n# ============================================================\n# ---------------- ТУМАН ВОЙНЫ ----------------",
    zone_block + "\n# ============================================================\n# ---------------- ТУМАН ВОЙНЫ ----------------", "zone_fns")

# A9) тик зоны в конце раунда
rep("\t_update_fog()\n\t_refresh_turn_lbl()\n\t_busy = false",
    "\tif not _game_over:\n\t\t_tick_zone()\n\t_update_fog()\n\t_refresh_turn_lbl()\n\t_busy = false", "zone_tick")

# A10) боты не выходят из зоны добровольно
rep("""		if _unit_at.has(k) or _fire.has(n):
			continue
		if _occupied.has(k):""",
"""		if _unit_at.has(k) or _fire.has(n):
			continue
		if not _in_zone(n) and _in_zone(f.cell):
			continue
		if _occupied.has(k):""", "bot_zone")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
