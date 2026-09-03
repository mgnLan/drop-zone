#!/usr/bin/env python3
"""Drop Zone: заливка web-билда на reg.ru по FTP.

Использование:
    python tools/ftp_upload.py

Настройки — deploy_regru/ftp_config.json (скопировать из ftp_config.example.json).
Заливает содержимое web_build/ + deploy_regru/.htaccess в remote_dir.
"""
import json
import os
import sys
from ftplib import FTP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, "web_build")
CONFIG = os.path.join(ROOT, "deploy_regru", "ftp_config.json")
HTACCESS = os.path.join(ROOT, "deploy_regru", ".htaccess")


def main() -> int:
    if not os.path.isfile(CONFIG):
        print("НЕТ КОНФИГА: скопируй deploy_regru/ftp_config.example.json "
              "-> ftp_config.json и впиши доступы")
        return 1
    cfg = json.load(open(CONFIG, encoding="utf-8"))

    ftp = FTP()
    ftp.connect(cfg["host"], cfg.get("port", 21), timeout=30)
    ftp.login(cfg["user"], cfg["password"])
    if cfg.get("passive", True):
        ftp.set_pasv(True)
    print("Подключено:", ftp.getwelcome())

    # создать целевую папку (и родителей) если нет
    for part in [p for p in cfg["remote_dir"].split("/") if p]:
        try:
            ftp.mkd(part)
        except Exception:
            pass  # уже существует
        ftp.cwd(part)
    print("Папка:", ftp.pwd())

    files = [f for f in os.listdir(BUILD) if os.path.isfile(os.path.join(BUILD, f))]
    ok, fail = 0, 0
    for name in sorted(files):
        src = os.path.join(BUILD, name)
        try:
            with open(src, "rb") as fh:
                ftp.storbinary("STOR " + name, fh)
            print(f"  OK  {name} ({os.path.getsize(src)} байт)")
            ok += 1
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            fail += 1

    if os.path.isfile(HTACCESS):
        with open(HTACCESS, "rb") as fh:
            ftp.storbinary("STOR .htaccess", fh)
        print("  OK  .htaccess")

    ftp.quit()
    print(f"Готово: {ok} файлов, ошибок: {fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
