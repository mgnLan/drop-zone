# -*- coding: utf-8 -*-
"""Скачать боевой api/index.php и data.sqlite (бэкап) с прода по FTP."""
import json
import os
import sys
from ftplib import FTP

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = json.load(open(os.path.join(ROOT, "deploy_regru", "ftp_config.json"), encoding="utf-8"))
out_dir = os.path.join(ROOT, "deploy_regru", "prod_snapshot")
os.makedirs(out_dir, exist_ok=True)

ftp = FTP()
ftp.connect(cfg["host"], cfg.get("port", 21), timeout=30)
ftp.login(cfg["user"], cfg["password"])
ftp.set_pasv(True)
for part in [p for p in (cfg["remote_dir"] + "/api").split("/") if p]:
    ftp.cwd(part)
print("Папка:", ftp.pwd())
for name in ("index.php", "data.sqlite"):
    local = os.path.join(out_dir, name)
    with open(local, "wb") as fh:
        ftp.retrbinary("RETR " + name, fh.write)
    print("OK", name, os.path.getsize(local), "байт")
ftp.quit()
