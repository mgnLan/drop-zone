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

    # СТРАЖ МОСТА ВК: наш инжект из head_include живёт в ОДНУ строку.
    # Любой // внутри dz-скрипта съест весь остаток строки -> SyntaxError,
    # вход молча умирает (проверено на проде, v6.71). Комментарии только /* */.
    a = src.find("<script>(function(){ window.dzVKError")
    b = src.find("</script>", a) if a >= 0 else -1
    if a < 0 or b < 0:
        print("НЕ НАЙДЕН dz-мост ВК в index.html — экспорт без head_include?")
        return 1
    dz = src[a:b]
    if "//" in dz:
        print("ОТКАЗ: '//' внутри dz-моста ВК — замени на /* */ (одна строка!)")
        return 1
    for marker in ("dzFired", "2500"):
        if marker not in dz:
            print(f"ОТКАЗ: маркер {marker} не найден в мосте — вход сломан")
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

    # Сплэш загрузки: index.png (~3 МБ) Apache не жмёт (image/png не в mod_deflate) —
    # конвертируем в JPEG q90 (~0.3 МБ), src в <img id="status-splash"> патчим.
    png_path = os.path.join(BUILD, "index.png")
    if os.path.isfile(png_path):
        from PIL import Image
        sizes["splash_png"] = os.path.getsize(png_path)
        im = Image.open(png_path).convert("RGB")
        jpg_path = os.path.join(BUILD, "index.jpg")
        im.save(jpg_path, "JPEG", quality=90, optimize=True)
        os.remove(png_path)
        out = out.replace('src="index.png"', 'src="index.jpg"')
        if 'src="index.jpg"' not in out:
            print("Патч сплэша не применился — src=\"index.png\" не найден в html")
            return 1
        sizes["splash_jpg"] = os.path.getsize(jpg_path)
        print(f"splash: index.png {sizes.get('splash_png', 0)} -> index.jpg {sizes['splash_jpg']} байт")

    open(html_path, "w", encoding="utf-8").write(out)

    # удаляем локальные версионные файлы прошлых сборок — иначе ftp_upload
    # зальёт их на сервер повторно (мусор + двойной трафик)
    for name in os.listdir(BUILD):
        if re.fullmatch(r"index_t\d+\.(pck|wasm)", name) and not name.startswith(tag):
            os.remove(os.path.join(BUILD, name))

    meta = {"tag": tag, "stamp": stamp, "sizes": sizes}

    # wav-звуки для JS-моста (dzPlay) — копируем в web_build/sfx,
    # движок их не пакует в pck, мост тянет по HTTP
    sfx_src = os.path.join(ROOT, "game", "assets", "sfx")
    sfx_dst = os.path.join(BUILD, "sfx")
    os.makedirs(sfx_dst, exist_ok=True)
    n_sfx = 0
    for name in os.listdir(sfx_src):
        if name.endswith(".wav"):
            with open(os.path.join(sfx_src, name), "rb") as fh_in, \
                 open(os.path.join(sfx_dst, name), "wb") as fh_out:
                fh_out.write(fh_in.read())
            n_sfx += 1
    meta["sfx"] = n_sfx
    print(f"sfx: {n_sfx} wav -> web_build/sfx")

    # docs: шаблоны privacy/offer — отдаются статикой рядом с игрой
    docs_src = os.path.join(ROOT, "docs")
    docs_dst = os.path.join(BUILD, "docs")
    if os.path.isdir(docs_src):
        os.makedirs(docs_dst, exist_ok=True)
        for name in os.listdir(docs_src):
            if name.endswith(".html"):
                with open(os.path.join(docs_src, name), "rb") as fh_in,                      open(os.path.join(docs_dst, name), "wb") as fh_out:
                    fh_out.write(fh_in.read())
        print("docs: privacy/offer -> web_build/docs")

    json.dump(meta, open(os.path.join(BUILD, "build.json"), "w", encoding="utf-8"))
    print(f"OK: {tag} (pck {sizes['pck']} байт, wasm {sizes['wasm']} байт)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
