# v6.27 — редизайн экрана входа: логотип вынесен из формы, поля/кнопки 52px
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    if old not in src:
        print("FAIL: маркер не найден:", old[:70].replace("\n", "\\n"))
        sys.exit(1)
    src = src.replace(old, new, 1)

# 1) логотип над формой (отдельный блок), форма шире
rep("""	layer.add_child(dim)
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.custom_minimum_size = Vector2(430, 0)
	panel.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(panel)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 10)
	panel.add_child(vb)
	var t := Label.new()
	t.text = "DROP ZONE — вход в аккаунт"
	t.add_theme_font_size_override("font_size", 24)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(t)""",
"""	layer.add_child(dim)
	# логотип игры — отдельным блоком НАД формой
	var logo := TextureRect.new()
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.anchor_left = 0.5
	logo.anchor_right = 0.5
	logo.offset_left = -300.0
	logo.offset_right = 300.0
	logo.offset_top = 36.0
	logo.offset_bottom = 176.0
	if ResourceLoader.exists("res://assets/ui/logo.png"):
		logo.texture = load("res://assets/ui/logo.png")
	layer.add_child(logo)
	var panel := PanelContainer.new()
	panel.set_anchors_preset(Control.PRESET_CENTER)
	panel.offset_top = 70.0
	panel.custom_minimum_size = Vector2(440, 0)
	panel.add_theme_stylebox_override("panel", _frame_box())
	layer.add_child(panel)
	var vb := VBoxContainer.new()
	vb.add_theme_constant_override("separation", 12)
	panel.add_child(vb)
	var t := Label.new()
	t.text = "Вход в аккаунт"
	t.add_theme_font_size_override("font_size", 22)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vb.add_child(t)""")

# 2) поля 52px
rep("""	em.placeholder_text = "Почта"
	em.text = _auth_email
	em.custom_minimum_size = Vector2(0, 44)""",
"""	em.placeholder_text = "✉ Почта"
	em.text = _auth_email
	em.custom_minimum_size = Vector2(0, 52)""")
rep("""	pw.placeholder_text = "Пароль (минимум 6 символов)"
	pw.secret = true
	pw.custom_minimum_size = Vector2(0, 44)""",
"""	pw.placeholder_text = "🔒 Пароль (минимум 6 символов)"
	pw.secret = true
	pw.custom_minimum_size = Vector2(0, 52)""")

# 3) «Войти» — главная красно-оранжевая кнопка 52px
rep("""	var li := _menu_button("Войти")
	li.pressed.connect(func():""",
"""	var li := _menu_button("ВОЙТИ")
	li.custom_minimum_size = Vector2(0, 52)
	var lis := StyleBoxFlat.new()
	lis.bg_color = Color(0.72, 0.16, 0.20, 0.95)
	lis.border_color = Color(1.0, 0.45, 0.25, 0.9)
	lis.set_border_width_all(2)
	lis.set_corner_radius_all(8)
	li.add_theme_stylebox_override("normal", lis)
	li.pressed.connect(func():""")

# 4) регистрация и гость — 52px
rep("""	var rg := _menu_button("Регистрация")
	rg.pressed.connect(func():""",
"""	var rg := _menu_button("РЕГИСТРАЦИЯ")
	rg.custom_minimum_size = Vector2(0, 52)
	rg.pressed.connect(func():""")
rep("""	var gs := _menu_button("Играть как гость (прогресс только на этом устройстве)")
	gs.pressed.connect(func():""",
"""	var gs := _menu_button("👤 Играть как гость")
	gs.custom_minimum_size = Vector2(0, 48)
	gs.pressed.connect(func():""")

io.open(P, "w", encoding="utf-8", newline="").write(src)
print("ALL_OK v6.27")
