extends SceneTree

func _init() -> void:
	for f in ["House_2Story.fbx", "House_2Story_Gable.fbx", "House_1Story.fbx"]:
		print("==== ", f)
		var inst = load("res://assets/models/buildings/" + f).instantiate()
		_dump(inst, 0)
	quit()

func _dump(n: Node, d: int) -> void:
	var pad := ""
	for i in d:
		pad += "  "
	var extra := ""
	if n is MeshInstance3D and (n as MeshInstance3D).mesh:
		var m := (n as MeshInstance3D).mesh
		extra = " surfaces=%d" % m.get_surface_count()
		for i in m.get_surface_count():
			var mat := m.surface_get_material(i)
			extra += " [m%d=%s]" % [i, mat.resource_name if mat else "null"]
	print(pad, n.name, " <", n.get_class(), ">", extra)
	for c in n.get_children():
		_dump(c, d + 1)
