<?php
// Drop Zone Royal Battle — ASYNC PvP: приём и валидация снапшота отряда.
// POST JSON {token, snapshot:{name, squad_lvl, fighters:[...]}} -> ok / отказ с причиной.

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
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_snapshots (
        owner INTEGER PRIMARY KEY,
        name TEXT DEFAULT '',
        squad_lvl INTEGER DEFAULT 1,
        json TEXT DEFAULT '',
        rating INTEGER DEFAULT 1000,
        anomalies INTEGER DEFAULT 0,
        updated_at TEXT
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

// --- rate-limit: 30/мин с IP (как основной API) ---
try {
    $db->exec("CREATE TABLE IF NOT EXISTS ratelimit (ip TEXT, ts INTEGER)");
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $now = time();
    $db->prepare("DELETE FROM ratelimit WHERE ts < ?")->execute([$now - 60]);
    $c = $db->prepare("SELECT COUNT(*) FROM ratelimit WHERE ip = ?");
    $c->execute([$ip]);
    if ((int)$c->fetchColumn() >= 30) out(['ok' => false, 'error' => 'Слишком много запросов — подожди минуту']);
    $db->prepare("INSERT INTO ratelimit (ip, ts) VALUES (?, ?)")->execute([$ip, $now]);
} catch (Exception $e) { /* не критично */ }

$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) out(['ok' => false, 'error' => 'bad request']);
$token = (string)($in['token'] ?? '');
$snap = $in['snapshot'] ?? null;
if ($token === '' || !is_array($snap)) out(['ok' => false, 'error' => 'bad request']);

$st = $db->prepare("SELECT id FROM users WHERE token = ?");
$st->execute([$token]);
$uid = (int)($st->fetchColumn() ?: 0);
if ($uid <= 0) out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);

list($ok, $why) = dz_validate_snapshot($snap);
if (!$ok) {
    // невалидный снапшот — отказ + лог в anomalies
    try {
        $db->prepare("INSERT INTO pvp_anomalies (owner, kind, detail, at) VALUES (?, 'push', ?, datetime('now'))")
           ->execute([$uid, mb_substr($why, 0, 120)]);
    } catch (Exception $e) { }
    out(['ok' => false, 'error' => 'Снапшот отклонён: ' . $why]);
}

$name = mb_substr(trim((string)($snap['name'] ?? 'Боец')), 0, 32);
if ($name === '') $name = 'Боец';
$squad_lvl = 1;
foreach (($snap['fighters'] ?? []) as $f) {
    $squad_lvl = max($squad_lvl, (int)($f['lvl'] ?? 1));
}

// upsert: рейтинг уже набранный сохраняем (не сбрасываем правки снапшота)
$old = $db->prepare("SELECT rating FROM pvp_snapshots WHERE owner = ?");
$old->execute([$uid]);
$rating = (int)($old->fetchColumn() ?: 1000);
$db->prepare("INSERT INTO pvp_snapshots (owner, name, squad_lvl, json, rating, updated_at)
              VALUES (?, ?, ?, ?, ?, datetime('now'))
              ON CONFLICT(owner) DO UPDATE SET name=excluded.name, squad_lvl=excluded.squad_lvl,
                  json=excluded.json, updated_at=excluded.updated_at")
   ->execute([$uid, $name, $squad_lvl, json_encode($snap, JSON_UNESCAPED_UNICODE), $rating]);

out(['ok' => true, 'rating' => $rating]);
