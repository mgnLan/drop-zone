# -*- coding: utf-8 -*-
# v6.11: логотип центрируется над РЕАЛЬНОЙ шириной колонки меню (кнопки шире 400px),
#         пересчёт при изменении размера окна и смене экрана меню
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

# запоминаем логотип
rep("""	if ResourceLoader.exists("res://assets/ui/logo.png"):
		logo.texture = load("res://assets/ui/logo.png")
	layer.add_child(logo)""",
"""	if ResourceLoader.exists("res://assets/ui/logo.png"):
		logo.texture = load("res://assets/ui/logo.png")
	layer.add_child(logo)
	_ui.menu_logo = logo""", "logo_ref")

# подписки на пересчёт раскладки
rep("""	layer.add_child(vb)
	_ui.menu_box = vb""",
"""	layer.add_child(vb)
	_ui.menu_box = vb
	vb.resized.connect(_layout_menu)
	get_viewport().size_changed.connect(_layout_menu)
	_layout_menu()""", "layout_hooks")

# функция раскладки: логотип строго над центром колонки, колонка не левее 600 (чат)
rep("""# ---------- диалоговое окно: вкладки чатов/логов ----------
var _chat_tab := 0""",
"""func _layout_menu() -> void:
	# логотип центрируется над фактической шириной колонки кнопок
	if not _ui.has("menu_box"):
		return
	var vb2: VBoxContainer = _ui.menu_box
	var vw3: float = get_viewport().get_visible_rect().size.x
	var bw: float = maxf(vb2.size.x, 400.0)
	var mx: float = maxf(600.0, (vw3 - bw) / 2.0)
	vb2.position.x = mx
	if _ui.has("menu_logo"):
		var lg: TextureRect = _ui.menu_logo
		lg.position.x = mx + bw / 2.0 - lg.size.x / 2.0

# ---------- диалоговое окно: вкладки чатов/логов ----------
var _chat_tab := 0""", "layout_fn")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
