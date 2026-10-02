#!/usr/bin/env python3
"""Drop Zone: версионирование web-билда после экспорта Godot.

Проблема: браузеры (и WebView ВК) кэшируют index.pck/index.wasm на сутки —
игроки получают старый код после деплоя. Решение: каждый билд получает
уникальное имя index_t<ts>.pck / .wasm, index.html правится под него.
HTML отдаётся с no-cache (см. deploy_regru/.htaccess), тяжёлые файлы —
с длинным кэшем, т.к. имя меняется при каждой сборке.

Запускать ПОСЛЕ экспорта:  godot --export-release "Web" web_build/index.html
"""
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "web_build")


def main() -> int:
    stamp = str(int(time.time()))
    tag = f"index_t{stamp}"
    html_path = os.path.join(BUILD, "index.html")
    src = open(html_path, encoding="utf-8").read()

    m = re.search(r'"executable"\s*:\s*"([^"]+)"', src)
    if not m:
        print("Не найден executable в index.html — это Godot-экспорт?")
        return 1
    old = m.group(1)
    if old != "index":
        print(f"executable уже версионирован: {old} — сначала чистая пересборка")
        return 1

    sizes = {}
    for ext in ("pck", "wasm"):
        p = os.path.join(BUILD, f"index.{ext}")
        if not os.path.isfile(p):
            print(f"НЕТ ФАЙЛА: {p}")
            return 1
        sizes[ext] = os.path.getsize(p)
        os.replace(p, os.path.join(BUILD, f"{tag}.{ext}"))

    # правим GODOT_CONFIG: executable и ключи fileSizes
    out = src.replace('"executable":"index"', f'"executable":"{tag}"')
    out = out.replace('"index.pck"', f'"{tag}.pck"')
    out = out.replace('"index.wasm"', f'"{tag}.wasm"')
    if tag not in out or f"{tag}.pck" not in out:
        print("Патч index.html не применился — формат GODOT_CONFIG изменился?")
        return 1
    open(html_path, "w", encoding="utf-8").write(out)

    # удаляем локальные версионные файлы прошлых сборок — иначе ftp_upload
    # зальёт их на сервер повторно (мусор + двойной трафик)
    for name in os.listdir(BUILD):
        if re.fullmatch(r"index_t\d+\.(pck|wasm)", name) and not name.startswith(tag):
            os.remove(os.path.join(BUILD, name))

    meta = {"tag": tag, "stamp": stamp, "sizes": sizes}
    json.dump(meta, open(os.path.join(BUILD, "build.json"), "w", encoding="utf-8"))
    print(f"OK: {tag} (pck {sizes['pck']} байт, wasm {sizes['wasm']} байт)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
