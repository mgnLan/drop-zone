# -*- coding: utf-8 -*-
# v6.10b: фикс рендера иконок — AABB через global_transform * get_aabb(),
#         фолбэк на standalone-модели из guns/ (гранаты и пр.)
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

rep("""	for mi in meshes:
		var a: AABB = (mi as MeshInstance3D).get_transformed_aabb()""",
"""	for mi in meshes:
		var a: AABB = (mi as MeshInstance3D).get_global_transform() * (mi as MeshInstance3D).get_aabb()""", "aabb_fix")

rep("""		else:
			var node_name: String = ICON_ALIAS.get(wid, wid)
			var found := soldier.find_child(node_name, true, false)
			if found and found is Node3D:
				node = found.duplicate()""",
"""		else:
			var node_name: String = ICON_ALIAS.get(wid, wid)
			if ResourceLoader.exists(GUNS + node_name + ".gltf"):
				node = load(GUNS + node_name + ".gltf").instantiate()
			elif ResourceLoader.exists(GUNS + wid + ".gltf"):
				node = load(GUNS + wid + ".gltf").instantiate()
			else:
				var found := soldier.find_child(node_name, true, false)
				if found and found is Node3D:
					node = found.duplicate()""", "src_fallback")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
