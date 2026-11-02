"""Изолированный HTTP-тест LIVE PvP: временная SQLite, два аккаунта, без прода."""
from __future__ import annotations
import json, shutil, socket, sqlite3, subprocess, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(r"I:\Kimi project\Drop Zone")
SRC = ROOT / "api"
PHP = ROOT / "tools" / "php_runtime" / "php.exe"
FILES = ("pvp_common.php", "live_common.php", "live_queue.php", "live_state.php", "live_action.php")

def snap(name: str) -> dict:
    return {"name": name, "squad_lvl": 1, "fighters": [{
        "name": name, "cls": 0, "lvl": 1,
        "stats": {"str": 1, "agi": 1, "end": 1, "per": 1, "int": 1, "lck": 1},
        "talents": {}, "weapon": "Pistol", "armor_grade": 0,
    }]}

def post(base: str, ep: str, data: dict) -> dict:
    req = urllib.request.Request(f"{base}/{ep}", data=json.dumps(data).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read().decode())

def main() -> None:
    assert PHP.exists(), PHP
    with tempfile.TemporaryDirectory(prefix="live_pvp_test_", dir=Path(__file__).resolve().parent) as tmp:
        work = Path(tmp)
        for fn in FILES:
            src = SRC / fn if (SRC / fn).exists() else Path(__file__).resolve().parent.parent / "pvp_audit" / "api" / fn
            shutil.copy2(src, work / fn)
        db = sqlite3.connect(work / "data.sqlite")
        db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, token TEXT)")
        db.executemany("INSERT INTO users VALUES (?, ?)", [(1, "token-a"), (2, "token-b")])
        # Намеренно старая схема без allow_offline: live_db обязан её мигрировать.
        db.execute("""CREATE TABLE pvp_snapshots (
            owner INTEGER PRIMARY KEY, name TEXT DEFAULT '', squad_lvl INTEGER DEFAULT 1,
            json TEXT DEFAULT '', rating INTEGER DEFAULT 1000, anomalies INTEGER DEFAULT 0,
            updated_at TEXT)""")
        db.execute("""CREATE TABLE pvp_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT, owner INTEGER, opponent TEXT DEFAULT '',
            outcome TEXT DEFAULT '', delta INTEGER DEFAULT 0, bot INTEGER DEFAULT 0, at TEXT)""")
        db.commit(); db.close()
        with socket.socket() as s:
            s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        log = (work / "server.log").open("w", encoding="utf-8")
        server = subprocess.Popen([str(PHP), "-d", f"extension_dir={PHP.parent / 'ext'}",
            "-d", "extension=pdo_sqlite", "-d", "extension=sqlite3", "-d", "extension=mbstring",
            "-S", f"127.0.0.1:{port}", "-t", str(work)], cwd=work,
            stdout=log, stderr=subprocess.STDOUT)
        try:
            for _ in range(50):
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.2): break
                except OSError: time.sleep(0.1)
            else: raise RuntimeError("PHP did not start")

            qa = post(base, "live_queue.php", {"token": "token-a", "snapshot": snap("A")})
            assert qa["waiting"] and not qa["matched"], qa
            qb = post(base, "live_queue.php", {"token": "token-b", "snapshot": snap("B")})
            assert qb["matched"] and qb["fight"]["side"] == 1, qb
            fid = qb["fight"]["fight_id"]
            qa2 = post(base, "live_queue.php", {"token": "token-a", "snapshot": snap("A")})
            assert qa2["matched"] and qa2["fight"]["side"] == 0, qa2

            wrong = post(base, "live_action.php", {"token": "token-b", "fight_id": fid,
                "kind": "move", "payload": {"fighter": 1, "cell": [3, 3]}, "action_uid": "b-wrong"})
            assert not wrong["ok"], wrong
            a1 = post(base, "live_action.php", {"token": "token-a", "fight_id": fid,
                "kind": "move", "payload": {"fighter": 0, "cell": [3, 3]}, "action_uid": "a-1"})
            assert a1["ok"] and a1["seq"] == 1, a1
            dup = post(base, "live_action.php", {"token": "token-a", "fight_id": fid,
                "kind": "move", "payload": {"fighter": 0, "cell": [3, 3]}, "action_uid": "a-1"})
            assert dup["duplicate"] and dup["seq"] == 1, dup
            sb = post(base, "live_state.php", {"token": "token-b", "fight_id": fid, "since": 0})
            assert len(sb["actions"]) == 1 and sb["actions"][0]["kind"] == "move", sb

            end = post(base, "live_action.php", {"token": "token-a", "fight_id": fid,
                "kind": "end_turn", "payload": {}, "action_uid": "a-2"})
            assert end["fight"]["turn_side"] == 1, end
            b1 = post(base, "live_action.php", {"token": "token-b", "fight_id": fid,
                "kind": "shoot", "payload": {"attacker": 1, "target": 0}, "action_uid": "b-1"})
            assert b1["ok"] and b1["seq"] == 3, b1
            sa = post(base, "live_state.php", {"token": "token-a", "fight_id": fid, "since": 1})
            assert [a["kind"] for a in sa["actions"]] == ["end_turn", "shoot"], sa

            db = sqlite3.connect(work / "data.sqlite")
            db.execute("UPDATE pvp_live_fights SET deadline = ? WHERE fight_id = ?", (int(time.time()) - 2, fid))
            db.commit(); db.close()
            timeout = post(base, "live_state.php", {"token": "token-b", "fight_id": fid, "since": 3})
            assert timeout["fight"]["turn_side"] == 0, timeout
            assert timeout["actions"][-1]["kind"] == "timeout", timeout

            fin = post(base, "live_action.php", {"token": "token-a", "fight_id": fid,
                "kind": "finish", "payload": {"winner_side": 0}, "action_uid": "a-finish"})
            assert fin["fight"]["status"] == "done" and fin["fight"]["winner"] == 0, fin
            done_b = post(base, "live_state.php", {"token": "token-b", "fight_id": fid, "since": 99})
            assert done_b["fight"]["rating_delta"] == -16, done_b
            db = sqlite3.connect(work / "data.sqlite")
            ratings = dict(db.execute("SELECT owner, rating FROM pvp_snapshots").fetchall())
            history = db.execute("SELECT COUNT(*) FROM pvp_history").fetchone()[0]
            db.close()
            assert ratings == {1: 1016, 2: 984}, ratings
            assert history == 2, history

            # Новая комната и сдача: победа достаётся второму игроку.
            post(base, "live_queue.php", {"token": "token-a", "snapshot": snap("A")})
            q2 = post(base, "live_queue.php", {"token": "token-b", "snapshot": snap("B")})
            fid2 = q2["fight"]["fight_id"]
            surrender = post(base, "live_action.php", {"token": "token-a", "fight_id": fid2,
                "kind": "forfeit", "payload": {}, "action_uid": "a-surrender"})
            assert surrender["fight"]["status"] == "done" and surrender["fight"]["winner"] == 1, surrender
            print("LIVE_PVP_SERVER_TEST OK: queue, turns, ordered actions, dedup, timeout, ELO, forfeit")
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=5)
            log.close()

if __name__ == "__main__": main()
