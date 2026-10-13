<?php
// Drop Zone Royal Battle — ASYNC PvP: приём результата боя, ELO, аномалии.
// POST JSON {token, fight_id, outcome(win/lose), turns, dmg_dealt, dmg_taken}
// Проверки: fight существует, результат ещё не принят, turns разумны,
// dmg_dealt ≤ теоретический максимум (обоймы×урон×turns ×1.6). Нарушение -> anomaly, рейтинг не начисляется.

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

require __DIR__ . '/pvp_common.php';

function out($d) { echo json_encode($d, JSON_UNESCAPED_UNICODE); exit; }

try {
    $db = new PDO('sqlite:' . __DIR__ . '/data.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_fights (
        fight_id TEXT PRIMARY KEY,
        attacker INTEGER,
        defender INTEGER DEFAULT 0,
        bot INTEGER DEFAULT 0,
        opp_name TEXT DEFAULT '',
        opp_rating INTEGER DEFAULT 1000,
        seed INTEGER DEFAULT 0,
        status TEXT DEFAULT 'open',
        created_at TEXT
    )");
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_snapshots (
        owner INTEGER PRIMARY KEY, name TEXT DEFAULT '', squad_lvl INTEGER DEFAULT 1,
        json TEXT DEFAULT '', rating INTEGER DEFAULT 1000, anomalies INTEGER DEFAULT 0, updated_at TEXT
    )");
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner INTEGER,
        opponent TEXT DEFAULT '',
        outcome TEXT DEFAULT '',
        delta INTEGER DEFAULT 0,
        bot INTEGER DEFAULT 0,
        at TEXT
    )");
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_anomalies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner INTEGER,
        kind TEXT DEFAULT '',
        detail TEXT DEFAULT '',
        at TEXT
    )");
} catch (Exception $e) {
    out(['ok' => false, 'error' => 'db error']);
}

try {
    $db->exec("CREATE TABLE IF NOT EXISTS ratelimit (ip TEXT, ts INTEGER)");
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $now = time();
    $db->prepare("DELETE FROM ratelimit WHERE ts < ?")->execute([$now - 60]);
    $c = $db->prepare("SELECT COUNT(*) FROM ratelimit WHERE ip = ?");
    $c->execute([$ip]);
    if ((int)$c->fetchColumn() >= 30) out(['ok' => false, 'error' => 'Слишком много запросов — подожди минуту']);
    $db->prepare("INSERT INTO ratelimit (ip, ts) VALUES (?, ?)")->execute([$ip, $now]);
} catch (Exception $e) { }

$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) out(['ok' => false, 'error' => 'bad request']);
$token = (string)($in['token'] ?? '');
$fight_id = (string)($in['fight_id'] ?? '');
$outcome = (string)($in['outcome'] ?? '');
$turns = (int)($in['turns'] ?? 0);
$dmg_dealt = (int)($in['dmg_dealt'] ?? -1);
$dmg_taken = (int)($in['dmg_taken'] ?? 0);
if ($token === '' || $fight_id === '' || !in_array($outcome, ['win', 'lose'], true)) {
    out(['ok' => false, 'error' => 'bad request']);
}

$st = $db->prepare("SELECT id FROM users WHERE token = ?");
$st->execute([$token]);
$uid = (int)($st->fetchColumn() ?: 0);
if ($uid <= 0) out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);

$fs = $db->prepare("SELECT * FROM pvp_fights WHERE fight_id = ?");
$fs->execute([$fight_id]);
$fight = $fs->fetch(PDO::FETCH_ASSOC);
if (!$fight || (int)$fight['attacker'] !== $uid) out(['ok' => false, 'error' => 'Бой не найден']);
if ($fight['status'] !== 'open') out(['ok' => false, 'error' => 'Результат по этому бою уже принят']);

// --- санити-чеки: нарушение -> anomaly, рейтинг НЕ начислять ---
$anomaly = '';
if ($turns < 1 || $turns > 300) {
    $anomaly = "turns=$turns";
} elseif ($dmg_dealt < 0 || $dmg_taken < 0) {
    $anomaly = "negative dmg";
} else {
    $ms = $db->prepare("SELECT json FROM pvp_snapshots WHERE owner = ?");
    $ms->execute([$uid]);
    $mj = (string)($ms->fetchColumn() ?: '');
    $snap = $mj !== '' ? json_decode($mj, true) : [];
    $cap = dz_dmg_cap(is_array($snap) ? $snap : [], $turns);
    if ($dmg_dealt > $cap) {
        $anomaly = "dmg $dmg_dealt > cap $cap";
    }
}

if ($anomaly !== '') {
    $db->prepare("INSERT INTO pvp_anomalies (owner, kind, detail, at) VALUES (?, 'result', ?, datetime('now'))")
       ->execute([$uid, mb_substr($anomaly, 0, 160)]);
    $db->prepare("UPDATE pvp_fights SET status = 'anomaly' WHERE fight_id = ?")->execute([$fight_id]);
    $db->prepare("UPDATE pvp_snapshots SET anomalies = anomalies + 1 WHERE owner = ?")->execute([$uid]);
    out(['ok' => true, 'anomaly' => true, 'detail' => $anomaly, 'delta' => 0]);
}

// --- ELO: старт 1000, K=32 ---
$rs = $db->prepare("SELECT rating FROM pvp_snapshots WHERE owner = ?");
$rs->execute([$uid]);
$ra = (int)($rs->fetchColumn() ?: 1000);
$rb = (int)$fight['opp_rating'];
$ea = 1.0 / (1.0 + pow(10.0, ($rb - $ra) / 400.0));
$score = $outcome === 'win' ? 1.0 : 0.0;
$delta = (int)round(32.0 * ($score - $ea));
$new_rating = $ra + $delta;

$db->prepare("UPDATE pvp_snapshots SET rating = ? WHERE owner = ?")->execute([$new_rating, $uid]);
$db->prepare("UPDATE pvp_fights SET status = 'done' WHERE fight_id = ?")->execute([$fight_id]);
$db->prepare("INSERT INTO pvp_history (owner, opponent, outcome, delta, bot, at) VALUES (?, ?, ?, ?, ?, datetime('now'))")
   ->execute([$uid, (string)$fight['opp_name'], $outcome, $delta, (int)$fight['bot']]);

out(['ok' => true, 'anomaly' => false, 'delta' => $delta, 'rating' => $new_rating]);
