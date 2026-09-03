# -*- coding: utf-8 -*-
# v6.16: 1) дома чуть меньше (модель не вылезает на соседние клетки)
#        2) объекты атакуются кликом: бочка 27 HP + 2 обяз. попадания, дерево 30, валун 80,
#           лёгкие укрытия 40, тяжёлые 90; взрыв бьёт по объектам на 25
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

# --- 1) масштаб дома чуть меньше ---
rep("""		var hnode := _place(B + model, gw(cell.x, cell.y), _rng.randf() * 360.0, 3.0 * k + 0.8, pal)""",
"""		var hnode := _place(B + model, gw(cell.x, cell.y), _rng.randf() * 360.0, 2.9 * k + 0.7, pal)""", "house_scale")

# --- 2) прочность объектов ---
rep("""		_covers[ck] = {"hp": 3 if heavy else 2, "cells": ccells, "node": cnode, "heavy": heavy}""",
"""		_covers[ck] = {"hp": 90 if heavy else 40, "cells": ccells, "node": cnode, "heavy": heavy}""", "hp_cover")
rep("""		_covers[_key(tc)] = {"hp": 2, "cells": [tc], "node": tnode, "heavy": false}""",
"""		_covers[_key(tc)] = {"hp": 30, "cells": [tc], "node": tnode, "heavy": false}""", "hp_tree")
rep("""		_covers[_key(rc)] = {"hp": 4, "cells": [rc], "node": rnode, "heavy": true}""",
"""		_covers[_key(rc)] = {"hp": 80, "cells": [rc], "node": rnode, "heavy": true}""", "hp_rock")
rep("""		_covers[_key(bc)] = {"hp": 1, "cells": [bc], "node": bnode, "heavy": false, "barrel": true}""",
"""		_covers[_key(bc)] = {"hp": 27, "cells": [bc], "node": bnode, "heavy": false, "barrel": true}""", "hp_barrel")

# --- 3) взрыв по объектам: 25 урона через общий обработчик ---
rep("""				var rec2 = _covers.get(ck2)
				if rec2 != null:
					rec2.hp = int(rec2.hp) - 1
					if int(rec2.hp) <= 0:
						_destroy_cover(ck2)""",
"""				_damage_cover_hit(ck2, 25, "Взрыв")""", "expl_hits")

# --- 4) сообщения о разрушении ---
rep("""	_log("Укрытие разрушено взрывом!")
	if rec.get("barrel", false):
		_explode_barrel(rec.cells[0])""",
"""	if rec.get("barrel", false):
		_log("Бочка взорвалась!")
		_explode_barrel(rec.cells[0])
	else:
		_log("%s разрушено!" % _cover_name(rec))""", "destroy_msg")

# --- 5) новые функции: имя объекта, урон по объекту, выстрел по объекту ---
rep("""func _destroy_cover(ck: String) -> void:""",
"""func _cover_name(rec) -> String:
	if rec.get("barrel", false):
		return "Бочка"
	if bool(rec.get("heavy", false)):
		return "Валун" if rec["cells"].size() == 1 else "Тяжёлое укрытие"
	return "Дерево" if rec["cells"].size() == 1 else "Укрытие"

func _damage_cover_hit(ck: String, dmg: int, src: String) -> void:
	# урон по объекту; бочке нужно ДВА попадания даже при большом уроне
	var rec = _covers.get(ck)
	if rec == null:
		return
	rec["hits"] = int(rec.get("hits", 0)) + 1
	rec.hp = int(rec.hp) - dmg
	var cname := _cover_name(rec)
	if int(rec.hp) <= 0:
		if rec.get("barrel", false) and int(rec["hits"]) < 2:
			rec.hp = 1
			_log("%s -> %s: пробита (%d урона), но не взорвалась — нужно ещё попадание!" % [src, cname, dmg])
			return
		_destroy_cover(ck)
	else:
		_log("%s -> %s: %d урона (прочность %d)" % [src, cname, dmg, int(rec.hp)])

func _shoot_cover(att: int, cell: Vector2i) -> void:
	# клик по объекту (бочка/дерево/валун/укрытие) — стреляем по нему
	var a = _fighters[att]
	var w: Dictionary = a.weapon
	var cost: int = w.get("ap_cost", 3)
	var k := _key(cell)
	if not _cover_at.has(k):
		return
	var ck: String = _cover_at[k]
	var rec = _covers.get(ck)
	if rec == null:
		return
	var cname := _cover_name(rec)
	var dist := Vector2(a.cell.x - cell.x, a.cell.y - cell.y).length()
	if dist > w.get("range", 1):
		_log("%s вне дальности (%d > %d)" % [cname, int(dist), w.get("range", 1)])
		return
	if a.ap < cost:
		_log("Не хватает AP (%d < %d)" % [a.ap, cost])
		return
	var burst: int = w.get("burst", 1)
	if w.has("ammo") and a.ammo < burst:
		_log("Нет патронов — перезарядка [R]")
		return
	var aoe2: int = w.get("aoe", 0)
	if aoe2 == 0 and not _los(a.cell, cell):
		_log("Нет линии огня — объект за препятствием")
		return
	a.ap -= cost
	if w.has("ammo"):
		a.ammo -= burst
	_face_cell(a, cell)
	_sfx_play("shot")
	if aoe2 > 0:
		_explode_at(cell, aoe2)
		if w.get("burn", false):
			_ignite(cell, aoe2)
		if w.get("consumable", false):
			_spend_consumable(att)
		return
	# объект не уворачивается: урон = урон ствола × очередь
	var dmg: int = w.get("damage", 10) * burst
	_damage_cover_hit(ck, dmg, a.name)

func _destroy_cover(ck: String) -> void:""", "shoot_cover_fn")

# --- 6) клик по объекту ---
rep("""	elif _reach.has(cell):
		var f = _fighters[_selected]
		var path := _path_to(f.cell, cell)""",
"""	elif _cover_at.has(k):
		_shoot_cover(_selected, cell)
		_after_action()
	elif _reach.has(cell):
		var f = _fighters[_selected]
		var path := _path_to(f.cell, cell)""", "click_cover")

if fails:
    print("FAILED:", fails)
    sys.exit(1)

io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("ALL_OK", len(orig), "->", len(s))
