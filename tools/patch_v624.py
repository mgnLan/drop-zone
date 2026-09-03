# v6.24 — второй биом «Индустриальная зона»: ржавый бетон, трубы, больше бочек и платформ
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) переменная биома + выбор при старте
rep("""func _build_ground() -> void:""",
"""var _biome := 0                # 0 = бетонная арена, 1 = индустриальная зона

func _build_ground() -> void:""")
rep("""	_rng.randomize()
	_load_mode()""",
"""	_rng.randomize()
	_biome = _rng.randi() % 2
	_load_mode()""")

# 2) цвет бетона и пятен по биому
rep("""	inner.material_override = _mat(Color(0.30, 0.295, 0.28), 0.0, 0.97)  # бетон — серый, не белый""",
"""	inner.material_override = _mat(Color(0.26, 0.235, 0.20) if _biome == 1 else Color(0.30, 0.295, 0.28), 0.0, 0.97)  # бетон / ржавая индустриалка""")
rep("""	stain_mat.albedo_color = Color(0.28, 0.27, 0.25, 0.55)""",
"""	stain_mat.albedo_color = Color(0.36, 0.21, 0.13, 0.5) if _biome == 1 else Color(0.28, 0.27, 0.25, 0.55)""")

# 3) декор: в индустриалке почти нет травы
rep("""	var n_grass := int(_rng.randi_range(16, 24) * dk)""",
"""	var n_grass := int(_rng.randi_range(16, 24) * dk) if _biome == 0 else int(_rng.randi_range(4, 8) * dk)""")

# 4) укрытия: пул моделей и счётчики по биому
rep("""	var n := maxi(4, int(_rng.randi_range(12, 16) * k))
	for i in n:
		var cell := _free_cell(4, _half_n - 1, 2)
		if cell.x < 0:
			continue
		_claim(cell, 2)
		var model: String = COVER_MODELS[_rng.randi() % COVER_MODELS.size()]""",
"""	var n := maxi(4, int((_rng.randi_range(12, 16) if _biome == 0 else _rng.randi_range(14, 18)) * k))
	var pool: Array = COVER_MODELS if _biome == 0 else COVER_MODELS + ["Platform_2x2.gltf", "Platform_2x2.gltf", "AC_Stacked.gltf"]
	for i in n:
		var cell := _free_cell(4, _half_n - 1, 2)
		if cell.x < 0:
			continue
		_claim(cell, 2)
		var model: String = pool[_rng.randi() % pool.size()]""")
rep("""	# деревья — лёгкое укрытие (hp 2)
	for i in maxi(3, int(_rng.randi_range(8, 12) * k)):""",
"""	# деревья — лёгкое укрытие (hp 2); в индустриалке почти нет
	for i in maxi(1 if _biome == 1 else 3, int((_rng.randi_range(1, 3) if _biome == 1 else _rng.randi_range(8, 12)) * k)):""")
rep("""	# бочки с топливом — взрываются (hp 1), урон 20 вокруг
	for i in maxi(2, int(_rng.randi_range(4, 6) * k)):""",
"""	# бочки с топливом — взрываются (hp 1), урон 20 вокруг; в индустриалке вдвое больше
	for i in maxi(2, int((_rng.randi_range(8, 12) if _biome == 1 else _rng.randi_range(4, 6)) * k)):""")

# 5) трубы — только индустриальный биом
rep("""		_covers[_key(bc)] = {"hp": 27, "cells": [bc], "node": bnode, "heavy": false, "barrel": true}
		_cover_at[_key(bc)] = _key(bc)
""",
"""		_covers[_key(bc)] = {"hp": 27, "cells": [bc], "node": bnode, "heavy": false, "barrel": true}
		_cover_at[_key(bc)] = _key(bc)
	# трубы — индустриальный биом: лёгкое укрытие (прочность 50)
	if _biome == 1:
		for i in maxi(2, int(_rng.randi_range(4, 6) * k)):
			var pc2 := _free_cell(3, _half_n, 1)
			if pc2.x < 0:
				continue
			_claim(pc2, 1)
			_soft_cover[_key(pc2)] = true
			var pnode := _make_pipe(gw(pc2.x, pc2.y))
			_covers[_key(pc2)] = {"hp": 50, "cells": [pc2], "node": pnode, "heavy": false, "kind": "pipe"}
			_cover_at[_key(pc2)] = _key(pc2)
""")

# 6) название трубы в логах
rep("""	if bool(rec.get("heavy", false)):
		return "Валун" if rec["cells"].size() == 1 else "Тяжёлое укрытие"
	return "Дерево" if rec["cells"].size() == 1 else "Укрытие\"""",
"""	if bool(rec.get("heavy", false)):
		return "Валун" if rec["cells"].size() == 1 else "Тяжёлое укрытие"
	if str(rec.get("kind", "")) == "pipe":
		return "Труба"
	return "Дерево" if rec["cells"].size() == 1 else "Укрытие\"""")

# 7) модель трубы (после _make_barrel)
rep("""func _explode_barrel(c: Vector2i) -> void:""",
"""func _make_pipe(pos: Vector3) -> Node3D:
	# горизонтальная труба на опорах — индустриальный декор-укрытие
	var g := Node3D.new()
	var body := MeshInstance3D.new()
	var cyl := CylinderMesh.new()
	cyl.top_radius = 0.28
	cyl.bottom_radius = 0.28
	cyl.height = 1.7
	body.mesh = cyl
	body.material_override = _mat(Color(0.42, 0.30, 0.18), 0.7, 0.45)  # ржавый металл
	body.rotation_degrees.z = 90.0
	body.position.y = 0.32
	g.add_child(body)
	var flange := MeshInstance3D.new()
	var fm := CylinderMesh.new()
	fm.top_radius = 0.34
	fm.bottom_radius = 0.34
	fm.height = 0.12
	flange.mesh = fm
	flange.material_override = _mat(Color(0.30, 0.22, 0.14), 0.7, 0.5)
	flange.rotation_degrees.z = 90.0
	flange.position = Vector3(0.6, 0.32, 0)
	g.add_child(flange)
	for sx in [-0.5, 0.5]:
		var leg := MeshInstance3D.new()
		var lm := BoxMesh.new()
		lm.size = Vector3(0.12, 0.2, 0.12)
		leg.mesh = lm
		leg.material_override = _mat(Color(0.16, 0.15, 0.14), 0.4, 0.7)
		leg.position = Vector3(sx, 0.1, 0)
		g.add_child(leg)
	g.position = pos
	g.rotation_degrees.y = _rng.randf() * 360.0
	add_child(g)
	return g

func _explode_barrel(c: Vector2i) -> void:""")

# 8) лог биома при старте боя
rep("""		_log("Тренировка %d×%d — ваш ход! ЛКМ — бойцы, ПКМ-тянуть — обзор." % [_mode, _mode])""",
"""		_log("Тренировка %d×%d — ваш ход! ЛКМ — бойцы, ПКМ-тянуть — обзор." % [_mode, _mode])
		_log("Биом: %s" % ("🏭 Индустриальная зона" if _biome == 1 else "🏙 Бетонная арена"))""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.24")
