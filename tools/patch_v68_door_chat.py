# -*- coding: utf-8 -*-
# v6.8: 1) дверь дома — «от границы» (сторона с максимумом свободного места до края)
#       2) лог и чат в ОДНОМ окне с вкладками: убираем отдельную строку лога справа внизу
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

# --- 1) дверь «от границы» ---
rep("""		# дверь — смотрит к центру карты, не к краю""",
"""		# дверь — «от границы»: сторона с наибольшим запасом свободного места до края карты""", "door_comment")

rep("""		cands.sort_custom(func(p7, q7):
			return Vector2(p7.x - _half_n, p7.y - _half_n).length() < Vector2(q7.x - _half_n, q7.y - _half_n).length())""",
"""		cands.sort_custom(func(p7, q7):
			var dp := mini(mini(p7.x, p7.y), mini(_grid_n - 1 - p7.x, _grid_n - 1 - p7.y))
			var dq := mini(mini(q7.x, q7.y), mini(_grid_n - 1 - q7.x, _grid_n - 1 - q7.y))
			return dp > dq)""", "door_sort")

# --- 2) убираем отдельную строку лога справа внизу (остаётся окно с вкладками Логи/Чаты) ---
rep("""	var log := Label.new()
	log.anchor_left = 1.0
	log.anchor_right = 1.0
	log.anchor_top = 1.0
	log.anchor_bottom = 1.0
	log.offset_left = -576.0
	log.offset_right = -16.0
	log.offset_top = -36.0
	log.offset_bottom = -8.0
	log.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	log.add_theme_font_size_override("font_size", 15)
	layer.add_child(log)
	_ui.log = log
""", "", "log_label")

rep("""func _log(msg: String) -> void:
	if _ui.has("log"):
		_ui.log.text = msg
	_battle_log.append(msg)""",
"""func _log(msg: String) -> void:
	_battle_log.append(msg)""", "log_fn")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
