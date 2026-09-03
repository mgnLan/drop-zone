extends Node2D
## Drop Zone — вертикальный срез: ночная арена телешоу будущего.
## Карта собирается кодом из спрайтов Kenney (CC0). Y-sort даёт глубину.

const G := 14                  # размер сетки (GxG)
const STEP_X := 66             # половина ширины ромба
const STEP_Y := 33             # половина высоты ромба

const T := {
	"concrete": "res://assets/tiles/floor_concrete.png",
	"concrete2": "res://assets/tiles/floor_concrete2.png",
	"asphalt":  "res://assets/tiles/floor_asphalt.png",
	"grass":    "res://assets/tiles/floor_grass.png",
	"sand":     "res://assets/tiles/floor_sand.png",
	"block":    "res://assets/tiles/block_low.png",
	"block2":   "res://assets/tiles/block_low2.png",
	"bldg_grey": "res://assets/tiles/bldg_grey.png",
	"bldg_red":  "res://assets/tiles/bldg_red.png",
	"bldg_big":  "res://assets/tiles/bldg_big.png",
	"bldg_tower": "res://assets/tiles/bldg_tower.png",
	"tree":     "res://assets/tiles/deco_tree.png",
}

# Объекты на карте: "x,y" -> ключ текстуры (укрытия/здания/декор)
const OBJECTS := {
	"3,3": "block", "3,4": "block2",
	"10,3": "block", "10,4": "block",
	"3,10": "block2", "4,10": "block",
	"9,9": "block", "10,10": "block2",
	"6,6": "bldg_grey", "7,6": "bldg_red",
	"6,7": "bldg_big",
	"2,7": "bldg_tower", "11,7": "bldg_tower",
	"5,2": "tree", "8,11": "tree",
	"7,2": "block", "2,10": "tree", "11,11": "block2",
}

var _tex := {}
var _ground: Node2D   # пол (y-sort внутри, всегда под объектами)
var _stage: Node2D    # объекты и бойцы (y-sort)

func grid_to_world(gx: int, gy: int) -> Vector2:
	return Vector2((gx - gy) * STEP_X, (gx + gy) * STEP_Y)

func _ready() -> void:
	if OS.get_cmdline_user_args().has("--test"):
		_test_poly()
		return
	if OS.get_cmdline_user_args().has("--test2"):
		_test_pawn()
		return
	for k in T:
		_tex[k] = load(T[k])
	_ground = Node2D.new()
	_ground.y_sort_enabled = true
	add_child(_ground)
	_stage = Node2D.new()
	_stage.y_sort_enabled = true
	add_child(_stage)
	_build_ground()
	_build_objects()
	_build_neon_ring()
	_spawn_pawn(5, 8, Color("#ff4757"), "RED-1")
	_spawn_pawn(8, 5, Color("#3498ff"), "BLU-1")
	_setup_lighting()
	_setup_camera()
	if OS.get_cmdline_user_args().has("--shot"):
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		img.save_png("G:/Kimi project/Drop Zone/docs/slice_v1.png")
		print("SHOT_SAVED")
		get_tree().quit()

func _build_ground() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 42
	for gx in G:
		for gy in G:
			var d: int = mini(mini(gx, gy), mini(G - 1 - gx, G - 1 - gy))
			var key := "concrete" if rng.randf() < 0.7 else "concrete2"
			if d == 0:
				key = "grass"
			elif d == 1:
				key = "asphalt"
			elif rng.randf() < 0.08:
				key = "sand"
			_add_tile(key, gx, gy, _ground)

func _build_objects() -> void:
	for cell in OBJECTS:
		var p: PackedStringArray = cell.split(",")
		_add_tile(OBJECTS[cell], int(p[0]), int(p[1]), _stage)

func _add_tile(key: String, gx: int, gy: int, layer: Node2D) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = _tex[key]
	s.position = grid_to_world(gx, gy)
	layer.add_child(s)
	return s

func _build_neon_ring() -> void:
	# Неоновый контур арены (граница между бетоном и асфальтом)
	var pts := PackedVector2Array([
		grid_to_world(2, 2) + Vector2(0, -STEP_Y),
		grid_to_world(G - 3, 2) + Vector2(STEP_X, 0),
		grid_to_world(G - 3, G - 3) + Vector2(0, STEP_Y),
		grid_to_world(2, G - 3) + Vector2(-STEP_X, 0),
		grid_to_world(2, 2) + Vector2(0, -STEP_Y),
	])
	var glow_line := Line2D.new()
	glow_line.points = pts
	glow_line.width = 12.0
	glow_line.default_color = Color(0.0, 0.9, 1.0, 0.45)
	glow_line.z_index = 5
	add_child(glow_line)
	var line := Line2D.new()
	line.points = pts
	line.width = 4.0
	line.default_color = Color(0.3, 1.0, 1.0, 1.0)
	line.z_index = 6
	add_child(line)

func _spawn_pawn(gx: int, gy: int, color: Color, tag: String) -> void:
	var pawn := Node2D.new()
	pawn.position = grid_to_world(gx, gy) + Vector2(0, -6)
	pawn.scale = Vector2(1.35, 1.35)
	# светящаяся стартовая площадка
	var pad := Polygon2D.new()
	pad.polygon = PackedVector2Array([Vector2(-30, 8), Vector2(0, 23), Vector2(30, 8), Vector2(0, -7)])
	pad.color = Color(color.r, color.g, color.b, 0.35)
	pawn.add_child(pad)
	# тень
	var sh := Polygon2D.new()
	sh.polygon = PackedVector2Array([Vector2(-16, 4), Vector2(0, 12), Vector2(16, 4), Vector2(0, -4)])
	sh.color = Color(0, 0, 0, 0.4)
	pawn.add_child(sh)
	# тело (капсула-голограмма бойца)
	var body := Polygon2D.new()
	body.polygon = PackedVector2Array([
		Vector2(-9, 2), Vector2(-9, -22), Vector2(-5, -30), Vector2(5, -30),
		Vector2(9, -22), Vector2(9, 2), Vector2(0, 8)])
	body.color = color
	pawn.add_child(body)
	var visor := Polygon2D.new()
	visor.polygon = PackedVector2Array([Vector2(-5, -24), Vector2(5, -24), Vector2(5, -19), Vector2(-5, -19)])
	visor.color = Color(0.8, 1.0, 1.0, 0.95)
	pawn.add_child(visor)
	# подсветка бойца
	var pl := PointLight2D.new()
	pl.texture = _make_radial_tex()
	pl.texture_scale = 1.6
	pl.energy = 0.35
	pl.color = color.lightened(0.4)
	pl.position = Vector2(0, -14)
	pawn.add_child(pl)
	# тег
	var lb := Label.new()
	lb.text = tag
	lb.add_theme_font_size_override("font_size", 13)
	lb.add_theme_color_override("font_color", Color(1, 1, 1, 0.95))
	lb.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	lb.add_theme_constant_override("outline_size", 4)
	lb.position = Vector2(-20, -56)
	pawn.add_child(lb)
	_stage.add_child(pawn)

func _setup_lighting() -> void:
	# ночь
	var cm := CanvasModulate.new()
	cm.color = Color(0.30, 0.32, 0.50)
	add_child(cm)
	# 4 прожектора по углам арены
	var corners := [Vector2i(2, 2), Vector2i(G - 3, 2), Vector2i(2, G - 3), Vector2i(G - 3, G - 3)]
	var hues := [Color(1.0, 0.85, 0.6), Color(0.6, 0.9, 1.0), Color(0.6, 0.9, 1.0), Color(1.0, 0.85, 0.6)]
	for i in corners.size():
		var c: Vector2i = corners[i]
		var spot := PointLight2D.new()
		spot.texture = _make_radial_tex()
		spot.texture_scale = 3.4
		spot.energy = 0.30
		spot.color = hues[i]
		spot.position = grid_to_world(c.x, c.y)
		add_child(spot)
		# мачта прожектора
		var mast := Polygon2D.new()
		mast.polygon = PackedVector2Array([Vector2(-2, 0), Vector2(2, 0), Vector2(2, -70), Vector2(-2, -70)])
		mast.color = Color(0.15, 0.15, 0.2)
		mast.position = spot.position
		_stage.add_child(mast)
		var head := Polygon2D.new()
		head.polygon = PackedVector2Array([Vector2(-6, -74), Vector2(6, -74), Vector2(6, -66), Vector2(-6, -66)])
		head.color = hues[i].lightened(0.5)
		head.position = spot.position
		_stage.add_child(head)

func _make_radial_tex() -> Texture2D:
	var g := Gradient.new()
	g.set_color(0, Color(1, 1, 1, 1))
	g.set_color(1, Color(1, 1, 1, 0))
	var gt := GradientTexture2D.new()
	gt.gradient = g
	gt.fill = GradientTexture2D.FILL_RADIAL
	gt.fill_from = Vector2(0.5, 0.5)
	gt.fill_to = Vector2(1.0, 0.5)
	gt.width = 256
	gt.height = 256
	return gt

func _setup_camera() -> void:
	var cam := Camera2D.new()
	cam.position = Vector2(0, (G - 1) * STEP_Y * 0.5)
	cam.zoom = Vector2(0.62, 0.62)
	if OS.get_cmdline_user_args().has("--debugpawn"):
		cam.position = grid_to_world(5, 8)
		cam.zoom = Vector2(2.2, 2.2)
	add_child(cam)
	cam.make_current()
	# фон + bloom
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.015, 0.015, 0.04)
	env.glow_enabled = true
	env.glow_intensity = 0.5
	env.glow_bloom = 0.15
	env.glow_blend_mode = Environment.GLOW_BLEND_MODE_ADDITIVE
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)


func _test_poly() -> void:
	var body := Polygon2D.new()
	body.polygon = PackedVector2Array([
		Vector2(-30, 8), Vector2(-30, -80), Vector2(-16, -100), Vector2(16, -100),
		Vector2(30, -80), Vector2(30, 8), Vector2(0, 28)])
	body.color = Color(1, 0.2, 0.3)
	add_child(body)
	var cam := Camera2D.new()
	cam.zoom = Vector2(3, 3)
	add_child(cam)
	cam.make_current()
	if OS.get_cmdline_user_args().has("--shot"):
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_poly.png")
		print("SHOT_SAVED")
		get_tree().quit()


func _test_pawn() -> void:
	_ground = Node2D.new()
	add_child(_ground)
	_stage = Node2D.new()
	_stage.y_sort_enabled = true
	add_child(_stage)
	var cm := CanvasModulate.new()
	cm.color = Color(0.30, 0.32, 0.50)
	add_child(cm)
	_spawn_pawn(0, 0, Color("#ff4757"), "RED-1")
	var cam := Camera2D.new()
	cam.zoom = Vector2(3, 3)
	add_child(cam)
	cam.make_current()
	if OS.get_cmdline_user_args().has("--shot"):
		await RenderingServer.frame_post_draw
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().save_png("G:/Kimi project/Drop Zone/docs/test_pawn.png")
		print("SHOT_SAVED")
		get_tree().quit()
