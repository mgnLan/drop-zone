# -*- coding: utf-8 -*-
# v6.12: 1) дома — штукатурная текстура (трипланар) поверх тинта, не «голый пластик»
#        2) ящик открывается с 8 соседних клеток (по диагонали тоже)
import io, sys

p = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
s = io.open(p, encoding="utf-8").read()
orig = s
fails = []

def rep(old, new, tag, cnt=1):
    global s
    c = s.count(old)
    if c != cnt:
        fails.append((tag, c))
        print("FAIL", tag, "count=", c)
        return
    s = s.replace(old, new)
    print("ok", tag)

# --- 1) штукатурка на домах ---
rep("""func _paint_house(node: Node3D, col: Color) -> void:
	# однотонная штукатурка вместо полосатых текстур-атласов:
	# surface override СИЛЬНЕЕ material_override, поэтому перебиваем каждую поверхность
	var m := _mat(col, 0.0, 0.92)
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = null
		for si in mi.mesh.get_surface_count():
			mi.set_surface_override_material(si, m)""",
"""var _plaster_tex: Texture2D = null
func _paint_house(node: Node3D, col: Color) -> void:
	# штукатурка: тинт + бесшовная текстура в трипланарной проекции (без полос атласа)
	if _plaster_tex == null and ResourceLoader.exists("res://assets/tiles/plaster.png"):
		_plaster_tex = load("res://assets/tiles/plaster.png")
	var m := _mat(col, 0.0, 0.92)
	if _plaster_tex != null:
		m.albedo_texture = _plaster_tex
		m.set_flag(BaseMaterial3D.FLAG_USE_TEXTURE_TRIPLANAR, true)
		m.uv1_scale = Vector3(0.22, 0.22, 0.22)
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = null
		for si in mi.mesh.get_surface_count():
			mi.set_surface_override_material(si, m)""", "plaster")

# --- 2) ящик: открытие с любой из 8 соседних клеток ---
rep("""	if absi(f.cell.x - cell.x) + absi(f.cell.y - cell.y) != 1:
		_log("Подойдите вплотную к ящику")
		return""",
"""	if maxi(absi(f.cell.x - cell.x), absi(f.cell.y - cell.y)) != 1:
		_log("Подойдите вплотную к ящику")
		return""", "chest_diag")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
