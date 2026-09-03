# -*- coding: utf-8 -*-
# v6.9: 1) дома — убираем полосатую текстуру по-настоящему (surface override сильнее material_override)
#       2) меню лобби сдвинуто правее, чтобы не пересекаться с чатом
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

# --- 1) дома: surface override на каждую поверхность (material_override проигрывал палитре) ---
rep("""func _paint_house(node: Node3D, col: Color) -> void:
	# однотонная штукатурка вместо полосатых текстур-атласов
	var m := _mat(col, 0.0, 0.92)
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = m""",
"""func _paint_house(node: Node3D, col: Color) -> void:
	# однотонная штукатурка вместо полосатых текстур-атласов:
	# surface override СИЛЬНЕЕ material_override, поэтому перебиваем каждую поверхность
	var m := _mat(col, 0.0, 0.92)
	for mi in node.find_children("*", "MeshInstance3D", true, false):
		mi.material_override = null
		for si in mi.mesh.get_surface_count():
			mi.set_surface_override_material(si, m)""", "paint_house")

# --- 1б) более сочные цвета домов (кирпич, сланец, песчаник, олива) ---
rep("""		var tints := [Color(0.60, 0.55, 0.48), Color(0.48, 0.51, 0.55), Color(0.58, 0.46, 0.38), Color(0.45, 0.49, 0.42)]""",
"""		var tints := [Color(0.55, 0.33, 0.24), Color(0.42, 0.46, 0.54), Color(0.60, 0.52, 0.38), Color(0.36, 0.44, 0.32)]""", "tints")

# --- 2) меню правее: колонка не левее 600px (чат занимает левые 576px), лого над колонкой ---
rep("""	var logo := TextureRect.new()
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.position = Vector2(340, 26)""",
"""	var vw2: float = get_viewport().get_visible_rect().size.x
	var menu_x: float = maxf(600.0, (vw2 - 400.0) / 2.0)
	var logo := TextureRect.new()
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.position = Vector2(menu_x + 200.0 - 300.0, 26)""", "menu_logo")

rep("""	var vb := VBoxContainer.new()
	vb.position = Vector2(440, 190)
	vb.custom_minimum_size = Vector2(400, 440)""",
"""	var vb := VBoxContainer.new()
	vb.position = Vector2(menu_x, 190)
	vb.custom_minimum_size = Vector2(400, 440)""", "menu_box")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
