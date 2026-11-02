"""Изолированный HTTP-тест общего онлайна: два аккаунта, временная SQLite, без прода."""
from __future__ import annotations
import json, shutil, socket, sqlite3, subprocess, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(r"I:\Kimi project\Drop Zone")
SRC = ROOT / "api"
PHP = ROOT / "tools" / "php_runtime" / "php.exe"
FILES = ("pvp_common.php", "live_common.php", "live_social.php")


def post(base: str, data: dict) -> dict:
    req = urllib.request.Request(f"{base}/live_social.php", data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as response:
        return json.loads(response.read().decode())


def main() -> None:
    assert PHP.exists(), PHP
    with tempfile.TemporaryDirectory(prefix="live_social_test_", dir=Path(__file__).resolve().parent) as tmp:
        work = Path(tmp)
        for filename in FILES:
            src = SRC / filename if (SRC / filename).exists() else Path(__file__).resolve().parent.parent / "pvp_audit" / "api" / filename
            shutil.copy2(src, work / filename)
        db = sqlite3.connect(work / "data.sqlite")
        db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, token TEXT)")
        db.executemany("INSERT INTO users VALUES (?, ?)", [(1, "token-a"), (2, "token-b")])
        db.execute("""CREATE TABLE pvp_snapshots (
            owner INTEGER PRIMARY KEY, name TEXT DEFAULT '', squad_lvl INTEGER DEFAULT 1,
            json TEXT DEFAULT '', rating INTEGER DEFAULT 1000, anomalies INTEGER DEFAULT 0,
            allow_offline INTEGER DEFAULT 0, updated_at TEXT)""")
        db.executemany("INSERT INTO pvp_snapshots (owner, name, rating) VALUES (?, ?, ?)",
            [(1, "Alpha", 1100), (2, "Bravo", 950)])
        db.commit()
        db.close()
        with socket.socket() as sock:
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        log = (work / "server.log").open("w", encoding="utf-8")
        server = subprocess.Popen([str(PHP), "-d", f"extension_dir={PHP.parent / 'ext'}",
            "-d", "extension=pdo_sqlite", "-d", "extension=sqlite3", "-d", "extension=mbstring",
            "-S", f"127.0.0.1:{port}", "-t", str(work)], cwd=work,
            stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.1)
            else:
                raise RuntimeError("PHP did not start")

            a = post(base, {"token": "token-a", "name": "Alpha", "playing": False})
            assert a["ok"] and a["online"] == 1 and a["players"][0]["me"] == 1, a
            b = post(base, {"token": "token-b", "name": "Bravo", "playing": True})
            assert b["ok"] and b["online"] == 2 and len(b["players"]) == 2, b
            assert {p["name"] for p in b["players"]} == {"Alpha", "Bravo"}, b

            sent = post(base, {"token": "token-a", "name": "Alpha", "playing": False, "text": "Привет, общий чат! 🔥"})
            assert sent["ok"] and sent["messages"][-1]["text"] == "Привет, общий чат! 🔥", sent
            assert sent["messages"][-1]["me"] == 1, sent
            seen_b = post(base, {"token": "token-b", "name": "Bravo", "playing": True})
            assert seen_b["messages"][-1]["text"] == "Привет, общий чат! 🔥", seen_b
            assert seen_b["messages"][-1]["me"] == 0, seen_b

            empty = post(base, {"token": "token-a", "text": "   "})
            assert not empty["ok"], empty
            long = post(base, {"token": "token-a", "text": "я" * 301})
            assert not long["ok"], long
            flood = post(base, {"token": "token-a", "text": "Слишком быстро"})
            assert not flood["ok"], flood

            db = sqlite3.connect(work / "data.sqlite")
            db.execute("UPDATE pvp_social_presence SET seen = ? WHERE owner = 1", (int(time.time()) - 30,))
            db.commit()
            db.close()
            after_ttl = post(base, {"token": "token-b", "name": "Bravo", "playing": False})
            assert after_ttl["online"] == 1 and after_ttl["players"][0]["name"] == "Bravo", after_ttl
            assert after_ttl["messages"][-1]["text"] == "Привет, общий чат! 🔥", after_ttl
            print("LIVE_SOCIAL_TEST OK: heartbeat, online list, shared chat, validation, antiflood, TTL")
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
                server.wait(timeout=5)
            log.close()


if __name__ == "__main__":
    main()
