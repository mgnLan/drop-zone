# v6.21 — компактные панели боя (-30%), сворачиваемый лог на мобильных, прозрачность
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) карточка бойца: 230x186 -> 204x168, портрет 86x124 -> 72x104, бары уже, шрифт имени меньше
rep("""	card.position = Vector2(12, 48)
	card.custom_minimum_size = Vector2(230, 186)""",
"""	card.position = Vector2(12, 48)
	card.custom_minimum_size = Vector2(204, 168)""")
rep("""	pvc.custom_minimum_size = Vector2(86, 124)
	pvc.stretch = true
	var pv := SubViewport.new()
	pv.size = Vector2i(172, 248)""",
"""	pvc.custom_minimum_size = Vector2(72, 104)
	pvc.stretch = true
	var pv := SubViewport.new()
	pv.size = Vector2i(172, 248)""")
rep("""	ava.custom_minimum_size = Vector2(86, 124)""",
"""	ava.custom_minimum_size = Vector2(72, 104)""")
rep("""	name_l.add_theme_font_size_override("font_size", 18)""",
"""	name_l.add_theme_font_size_override("font_size", 16)""")
rep("""	hp_bar.max_value = 100
	hp_bar.custom_minimum_size = Vector2(120, 14)""",
"""	hp_bar.max_value = 100
	hp_bar.custom_minimum_size = Vector2(104, 12)""")
rep("""	ap_bar.max_value = 10
	ap_bar.custom_minimum_size = Vector2(120, 14)""",
"""	ap_bar.max_value = 10
	ap_bar.custom_minimum_size = Vector2(104, 12)""")

# 2) ростер: выше к карточке, строки компактнее
rep("""	roster.position = Vector2(12, 244)""",
"""	roster.position = Vector2(12, 226)""")
rep("""		row.custom_minimum_size = Vector2(212, 46)""",
"""		row.custom_minimum_size = Vector2(190, 42)""")
rep("""		rp.custom_minimum_size = Vector2(34, 34)""",
"""		rp.custom_minimum_size = Vector2(30, 30)""")
rep("""		rn.add_theme_font_size_override("font_size", 13)""",
"""		rn.add_theme_font_size_override("font_size", 12)""")
rep("""		rs.add_theme_font_size_override("font_size", 11)""",
"""		rs.add_theme_font_size_override("font_size", 10)""")

# 3) панель бойца справа: уже (308 -> 252)
rep("""	fp.offset_left = -316.0
	fp.offset_right = -8.0
	fp.offset_top = 96.0
	fp.offset_bottom = 336.0""",
"""	fp.offset_left = -268.0
	fp.offset_right = -8.0
	fp.offset_top = 96.0
	fp.offset_bottom = 328.0""")

# 4) лог/чат: 440x260 -> 380x222, шрифт строк 12 -> 11, прозрачнее
rep("""	chat.offset_left = 12.0
	chat.offset_right = 452.0
	chat.offset_top = -272.0
	chat.offset_bottom = -12.0""",
"""	chat.offset_left = 12.0
	chat.offset_right = 392.0
	chat.offset_top = -234.0
	chat.offset_bottom = -12.0""")
rep("""	chat_sb.bg_color = Color(0.14, 0.20, 0.15, 0.9)""",
"""	chat_sb.bg_color = Color(0.14, 0.20, 0.15, 0.78)""")
rep("""	scroll.custom_minimum_size = Vector2(0, 176)""",
"""	scroll.custom_minimum_size = Vector2(0, 132)""")
rep("""	for line in data:
		var l := Label.new()
		l.text = line
		l.add_theme_font_size_override("font_size", 12)""",
"""	for line in data:
		var l := Label.new()
		l.text = line
		l.add_theme_font_size_override("font_size", 11)""")

# 5) рамки панелей прозрачнее — карта просвечивает
rep("""	sb.bg_color = Color(0.04, 0.06, 0.11, 0.72)""",
"""	sb.bg_color = Color(0.04, 0.06, 0.11, 0.60)""")

# 6) на мобильных лог свёрнут в кнопку-переключатель
rep("""	_ui.chat_input = inp
	_render_chat()""",
"""	_ui.chat_input = inp
	_render_chat()
	# мобильный режим: лог свёрнут, разворачивается кнопкой
	if _ui_scale_factor > 1.0:
		chat.visible = false
		var ct := Button.new()
		ct.text = "📜 Лог"
		ct.anchor_top = 1.0
		ct.anchor_bottom = 1.0
		ct.offset_left = 12.0
		ct.offset_right = 100.0
		ct.offset_top = -56.0
		ct.offset_bottom = -12.0
		ct.pressed.connect(func(): chat.visible = not chat.visible)
		ct.pressed.connect(_sfx_play.bind("click"))
		layer.add_child(ct)""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.21")
