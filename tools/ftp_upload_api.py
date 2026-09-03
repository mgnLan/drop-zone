#!/usr/bin/env python3
"""Drop Zone: заливка PHP API (api/) на reg.ru по FTP в remote_dir/api/."""
import json
import os
import sys
from ftplib import FTP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "api")
CONFIG = os.path.join(ROOT, "deploy_regru", "ftp_config.json")


def main() -> int:
    cfg = json.load(open(CONFIG, encoding="utf-8"))
    ftp = FTP()
    ftp.connect(cfg["host"], cfg.get("port", 21), timeout=30)
    ftp.login(cfg["user"], cfg["password"])
    if cfg.get("passive", True):
        ftp.set_pasv(True)
    print("Подключено:", ftp.getwelcome())
    for part in [p for p in (cfg["remote_dir"] + "/api").split("/") if p]:
        try:
            ftp.mkd(part)
        except Exception:
            pass
        ftp.cwd(part)
    print("Папка:", ftp.pwd())
    ok, fail = 0, 0
    for name in sorted(os.listdir(API)):
        src = os.path.join(API, name)
        if not os.path.isfile(src) or name == "data.sqlite":
            continue
        try:
            with open(src, "rb") as fh:
                ftp.storbinary("STOR " + name, fh)
            print(f"  OK  {name}")
            ok += 1
        except Exception as e:
            print(f"  FAIL {name}: {e}")
            fail += 1
    ftp.quit()
    print(f"Готово: {ok} файлов, ошибок: {fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
