# -*- coding: utf-8 -*-
# v6.10d: портрет — кадрирование головы по реальному AABB модели;
#         окна инвентаря и ящика получают непрозрачный фон (_frame_box)
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

# --- портрет: голова по AABB модели (любой рост) ---
rep("""	var cam := Camera3D.new()
	cam.position = Vector3(0.18, 1.66, 1.1)
	cam.fov = 24.0
	pv.add_child(cam)
	cam.look_at(Vector3(0, 1.52, 0), Vector3.UP)""",
"""	var bb2 := _node_aabb(model)
	var hh: float = maxf(bb2.size.y, 0.2)
	var head := Vector3(bb2.get_center().x, bb2.end.y - hh * 0.08, bb2.get_center().z)
	var cam := Camera3D.new()
	cam.position = head + Vector3(0.10 * hh, 0.02 * hh, 0.60 * hh)
	cam.fov = 26.0
	pv.add_child(cam)
	cam.look_at(head, Vector3.UP)""", "card_aabb")

# --- фон окну ящика ---
rep("""	var cp := PanelContainer.new()
	cp.set_anchors_preset(Control.PRESET_CENTER)
	cp.offset_left = -200.0
	cp.offset_right = 200.0
	cp.offset_top = -170.0
	cp.offset_bottom = 170.0
	layer.add_child(cp)""",
"""	var cp := PanelContainer.new()
	cp.set_anchors_preset(Control.PRESET_CENTER)
	cp.offset_left = -200.0
	cp.offset_right = 200.0
	cp.offset_top = -170.0
	cp.offset_bottom = 170.0
	cp.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(cp)""", "chest_bg")

# --- фон окну инвентаря ---
rep("""	var iw := PanelContainer.new()
	iw.set_anchors_preset(Control.PRESET_CENTER)
	iw.offset_left = -320.0
	iw.offset_right = 320.0
	iw.offset_top = -250.0
	iw.offset_bottom = 250.0
	layer.add_child(iw)""",
"""	var iw := PanelContainer.new()
	iw.set_anchors_preset(Control.PRESET_CENTER)
	iw.offset_left = -320.0
	iw.offset_right = 320.0
	iw.offset_top = -250.0
	iw.offset_bottom = 250.0
	iw.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(iw)""", "inv_bg")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
