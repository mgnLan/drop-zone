# Патч B: камера (пан по ЛКМ) + тач-управление
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

# B1) переменные камеры/тача
rep("var _zone_walls := []",
    "var _zone_walls := []\n"
    "var _cam_target := Vector3(0, 0.5, 0)   # точка, за которой следит камера\n"
    "var _lmb_down := false\nvar _lmb_moved := false\nvar _lmb_pos := Vector2.ZERO\n"
    "var _touch_pts := {}\nvar _pinch := 0.0\n"
    "var _override_mouse := Vector2(-1, -1)  # для тач-кликов", "cam_vars")

# B2) камера следит за _cam_target
rep("	var center := Vector3(0, 0.5, 0)",
    "	var center := _cam_target", "cam_center")

# B3) функции панорамирования и клика по координатам
pan_lines = [
"",
"func _pan_camera(rel: Vector2) -> void:",
"\tif _cam == null:",
"\t\treturn",
"\tvar yr := deg_to_rad(_cam_yaw)",
"\tvar right := Vector3(cos(yr), 0, -sin(yr))",
"\tvar fwd := Vector3(-sin(yr), 0, -cos(yr))",
"\tvar k := _cam_dist * 0.0016",
"\t_cam_target += (-right * rel.x + fwd * rel.y) * k",
"\tvar lim := _size_n * 0.45",
"\t_cam_target.x = clampf(_cam_target.x, -lim, lim)",
"\t_cam_target.z = clampf(_cam_target.z, -lim, lim)",
"\t_update_camera()",
"",
"func _mouse_pos() -> Vector2:",
"\tif _override_mouse.x >= 0.0:",
"\t\treturn _override_mouse",
"\treturn get_viewport().get_mouse_position()",
"",
"func _click_left_at(pos: Vector2) -> void:",
"\t_override_mouse = pos",
"\t_click_left()",
"\t_override_mouse = Vector2(-1, -1)",
"",
]
pan_block = "\n".join(pan_lines)
rep("\nfunc _zoom(delta: float) -> void:", pan_block + "func _zoom(delta: float) -> void:", "pan_fns")

# B4) хелперы наведения используют _mouse_pos
assert s.count("var mp := get_viewport().get_mouse_position()") == 2
s = s.replace("var mp := get_viewport().get_mouse_position()", "var mp := _mouse_pos()")
print("ok mouse_pos x2")

# B5) новый ввод: ЛКМ-тага, тач
old_tail = """	if _busy or _game_over or _menu_open or _lvl_open:
		return
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_SPACE:
				_end_turn()
			KEY_ESCAPE:
				_deselect()
			KEY_R:
				_reload_selected()
			KEY_F:
				_swap_weapon()
			KEY_I:
				_toggle_inventory()
	elif event is InputEventMouseButton and event.pressed:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_click_left()"""
new_tail = """	if _menu_open or _lvl_open:
		return
	# ЛКМ: короткий клик — действие; удержание и тяга — обзор карты
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_lmb_down = true
			_lmb_moved = false
			_lmb_pos = event.position
		elif _lmb_down:
			_lmb_down = false
			if not _lmb_moved and not _busy and not _game_over:
				_click_left()
		return
	if event is InputEventMouseMotion and _lmb_down:
		if (event.position - _lmb_pos).length() > 8.0:
			_lmb_moved = true
		if _lmb_moved:
			_pan_camera(event.relative)
		return
	# тач: 1 палец — тап/тяга; 2 пальца — щипок (зум)
	if event is InputEventScreenTouch:
		if event.pressed:
			_touch_pts[event.index] = event.position
			if _touch_pts.size() == 1:
				_lmb_down = true
				_lmb_moved = false
				_lmb_pos = event.position
		else:
			var was_two := _touch_pts.size() >= 2
			_touch_pts.erase(event.index)
			if not was_two and _lmb_down and not _lmb_moved and not _busy and not _game_over:
				_click_left_at(event.position)
			if _touch_pts.is_empty():
				_lmb_down = false
				_pinch = 0.0
		return
	if event is InputEventScreenDrag:
		_touch_pts[event.index] = event.position
		if _touch_pts.size() >= 2:
			var ks: Array = _touch_pts.keys()
			var pa: Vector2 = _touch_pts[ks[0]]
			var pb: Vector2 = _touch_pts[ks[1]]
			var pinch := (pa - pb).length()
			if _pinch > 0.0:
				_zoom((_pinch - pinch) * 0.25)
			_pinch = pinch
			_lmb_moved = true
		elif _lmb_down:
			if (event.position - _lmb_pos).length() > 10.0:
				_lmb_moved = true
			if _lmb_moved:
				_pan_camera(event.relative)
		return
	if _busy or _game_over:
		return
	if event is InputEventKey and event.pressed:
		match event.keycode:
			KEY_SPACE:
				_end_turn()
			KEY_ESCAPE:
				_deselect()
			KEY_R:
				_reload_selected()
			KEY_F:
				_swap_weapon()
			KEY_I:
				_toggle_inventory()"""
rep(old_tail, new_tail, "input_tail")

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
