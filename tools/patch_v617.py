# v6.17 — мобильный UI: автомасштаб интерфейса + крупные сенсорные кнопки
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) функция автомасштаба + вызов в _ready
rep("""func _ready() -> void:
	var args := OS.get_cmdline_user_args()""",
"""# ---------- мобильный UI: автомасштаб интерфейса ----------
var _ui_scale_factor := 1.0

func _apply_display_scale() -> void:
	var win := get_tree().root
	win.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	# физический размер окна (без влияния текущего масштаба — нет петли обратной связи)
	var sz: Vector2i = DisplayServer.window_get_size()
	var mind: float = float(mini(sz.x, sz.y))
	var factor := 1.0
	if mind < 520.0:
		factor = 1.6
	elif mind < 760.0:
		factor = 1.35
	elif mind < 950.0:
		factor = 1.15
	if absf(factor - _ui_scale_factor) > 0.01:
		_ui_scale_factor = factor
		win.content_scale_factor = factor

func _ready() -> void:
	_apply_display_scale()
	get_viewport().size_changed.connect(_apply_display_scale)
	var args := OS.get_cmdline_user_args()""")

# 2) сенсорные цели 44px+: Конец хода и Лобби (справа сверху)
rep("""	btn.offset_left = -196.0
	btn.offset_right = -16.0
	btn.offset_top = 10.0
	btn.offset_bottom = 50.0
	btn.pressed.connect(_end_turn)""",
"""	btn.offset_left = -212.0
	btn.offset_right = -16.0
	btn.offset_top = 10.0
	btn.offset_bottom = 56.0
	btn.pressed.connect(_end_turn)""")
rep("""	lobby.offset_left = -196.0
	lobby.offset_right = -16.0
	lobby.offset_top = 56.0
	lobby.offset_bottom = 88.0""",
"""	lobby.offset_left = -212.0
	lobby.offset_right = -16.0
	lobby.offset_top = 62.0
	lobby.offset_bottom = 108.0""")

# 3) кнопка рюкзака под портретом — выше
rep("""	bag.text = "🎒 Рюкзак [I]"
	bag.custom_minimum_size = Vector2(0, 30)""",
"""	bag.text = "🎒 Рюкзак [I]"
	bag.custom_minimum_size = Vector2(0, 40)""")

# 4) вкладки чата — выше для пальца
rep("""		tb.text = tab_names[ti]
		tb.custom_minimum_size = Vector2(0, 26)""",
"""		tb.text = tab_names[ti]
		tb.custom_minimum_size = Vector2(0, 34)""")

# 5) кнопки сундука «Взять всё/Закрыть» — 40px
rep("""	var take := Button.new()
	take.text = "Взять всё\"""",
"""	var take := Button.new()
	take.custom_minimum_size = Vector2(0, 40)
	take.text = "Взять всё\"""")
rep("""	var close := Button.new()
	close.text = "Закрыть\"""",
"""	var close := Button.new()
	close.custom_minimum_size = Vector2(0, 40)
	close.text = "Закрыть\"""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.17")

# 6) viewport meta для мобильных браузеров
EP = r"G:\Kimi project\Drop Zone\game\export_presets.cfg"
ep = io.open(EP, encoding="utf-8").read()
marker = 'html/head_include="<style>'
if marker in ep and "viewport" not in ep:
    ep = ep.replace(marker, 'html/head_include="<meta name=\\"viewport\\" content=\\"width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no\\"><style>', 1)
    io.open(EP, "w", encoding="utf-8", newline="").write(ep)
    print("PRESET_OK viewport meta добавлен")
elif "viewport" in ep:
    print("PRESET_SKIP viewport уже есть")
else:
    print("PRESET_FAIL маркер head_include не найден")
