# -*- coding: utf-8 -*-
# v6.36: эмодзи-шрифт (Noto Emoji fallback), карточки заблокированных режимов,
# промо-зона Battle Pass + сундуки в пустом центре лобби
import io, sys

P = r"G:\Kimi project\Drop Zone\game\scripts\arena3d.gd"
src = io.open(P, encoding="utf-8").read()

def rep(old, new):
    global src
    c = src.count(old)
    if c != 1:
        print("FAIL: маркер найден %d раз (нужно 1):" % c)
        print(old[:140])
        sys.exit(1)
    src = src.replace(old, new)

# ---- 1. Эмодзи-fallback: FontVariation = Manrope + NotoEmoji ----
rep("""	# кириллический шрифт Manrope вместо системного
	if ResourceLoader.exists("res://assets/fonts/Manrope.ttf"):
		ThemeDB.fallback_font = load("res://assets/fonts/Manrope.ttf")
		ThemeDB.fallback_font_size = 16
""", """	# кириллический шрифт Manrope + монохромные эмодзи Noto Emoji как fallback
	if ResourceLoader.exists("res://assets/fonts/Manrope.ttf"):
		var fv := FontVariation.new()
		fv.base_font = load("res://assets/fonts/Manrope.ttf")
		if ResourceLoader.exists("res://assets/fonts/NotoEmoji.ttf"):
			fv.fallbacks = [load("res://assets/fonts/NotoEmoji.ttf")]
		ThemeDB.fallback_font = fv
		ThemeDB.fallback_font_size = 16
""")

# ---- 2. Хелпер стиля заблокированных кнопок ----
rep("""func _show_menu_main() -> void:
""", """func _style_locked_button(b: Button) -> void:
	# заблокированный режим — тусклая неон-рамка + серый текст (в стиле лобби)
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.05, 0.07, 0.10, 0.85)
	sb.border_color = Color(0.45, 0.5, 0.6, 0.7)
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(8)
	b.add_theme_stylebox_override("disabled", sb)
	b.add_theme_color_override("font_disabled_color", Color(0.65, 0.7, 0.8))

func _show_menu_main() -> void:
""")

# ---- 3. Карточки заблокированных режимов с прогрессом ----
rep("""	else:
		m2.text = "🔒 2×2 — слот №2 после %d побед" % int(SLOT_WINS[2])
		m2.disabled = true
""", """	else:
		m2.text = "🔒 2×2 — побед %d/%d до слота №2" % [int(_profile.get("wins", 0)), int(SLOT_WINS[2])]
		m2.disabled = true
		_style_locked_button(m2)
""")
rep("""	else:
		m4.text = "🔒 4×4 — слот №4 после %d побед" % int(SLOT_WINS[4])
		m4.disabled = true
""", """	else:
		m4.text = "🔒 4×4 — побед %d/%d до слота №4" % [int(_profile.get("wins", 0)), int(SLOT_WINS[4])]
		m4.disabled = true
		_style_locked_button(m4)
""")

# ---- 4. Промо-зона внизу лобби: BP + сундуки ----
rep("""		vb.add_child(_daily_box())

func _show_menu_settings() -> void:
""", """		vb.add_child(_daily_box())
	# промо-зона: сезонный пропуск и сундуки (заполняет пустой центр лобби)
	var promo := HBoxContainer.new()
	promo.add_theme_constant_override("separation", 16)
	promo.alignment = BoxContainer.ALIGNMENT_CENTER
	vb.add_child(promo)
	var pc_w := minf(430.0, vw4 * 0.44)
	var bpc := PanelContainer.new()
	bpc.add_theme_stylebox_override("panel", _frame_box())
	bpc.custom_minimum_size = Vector2(pc_w, 118)
	promo.add_child(bpc)
	var bpv := VBoxContainer.new()
	bpv.add_theme_constant_override("separation", 6)
	bpc.add_child(bpv)
	var bpt := Label.new()
	bpt.text = "🏅 Battle Pass — сезон 1 «Первый снег»"
	bpt.add_theme_font_size_override("font_size", 15)
	bpt.add_theme_color_override("font_color", Color(1.0, 0.85, 0.3))
	bpv.add_child(bpt)
	var bpl := Label.new()
	bpl.text = "Уровень %d/%d · опыт %d" % [_bp_level(), BP_LEVELS, int(_profile.get("bp_xp", 0))]
	bpl.add_theme_font_size_override("font_size", 12)
	bpv.add_child(bpl)
	var bpb := ProgressBar.new()
	bpb.max_value = BP_XP_PER
	bpb.value = (0 if _bp_level() >= BP_LEVELS else int(_profile.get("bp_xp", 0)) - _bp_level() * BP_XP_PER)
	bpb.custom_minimum_size = Vector2(0, 10)
	bpb.show_percentage = false
	bpv.add_child(bpb)
	var bpbtn := _menu_button("Открыть пропуск")
	bpbtn.custom_minimum_size = Vector2(0, 36)
	bpbtn.pressed.connect(_show_menu_bp)
	bpv.add_child(bpbtn)
	var chc := PanelContainer.new()
	chc.add_theme_stylebox_override("panel", _frame_box())
	chc.custom_minimum_size = Vector2(pc_w, 118)
	promo.add_child(chc)
	var chv := VBoxContainer.new()
	chv.add_theme_constant_override("separation", 6)
	chc.add_child(chv)
	var cht := Label.new()
	cht.text = "🎁 Сундук удачи — %d 🪙" % CHEST_PRICE
	cht.add_theme_font_size_override("font_size", 15)
	cht.add_theme_color_override("font_color", Color(0.72, 0.5, 1.0))
	chv.add_child(cht)
	var pity2: Array = _profile.get("pity", [0, 0, 0])
	var chl := Label.new()
	chl.text = "Эпик гарантирован через %d откр. · легенда через %d" % [maxi(1, 10 - int(pity2[0])), maxi(1, 30 - int(pity2[1]))]
	chl.add_theme_font_size_override("font_size", 12)
	chl.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	chv.add_child(chl)
	var chb := _menu_button("Испытать удачу")
	chb.custom_minimum_size = Vector2(0, 36)
	chb.pressed.connect(_show_menu_chests)
	chv.add_child(chb)

func _show_menu_settings() -> void:
""")

io.open(P, "w", encoding="utf-8", newline="\n").write(src)
print("ALL_OK v6.36")
