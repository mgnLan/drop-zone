extends SceneTree
func _init() -> void:
	var m := StandardMaterial3D.new()
	for pr in m.get_property_list():
		var n: String = pr.name
		if "triplanar" in n or "uv1" in n or "texture_repeat" in n:
			print("PROP ", n, " type=", pr.type)
	quit()
