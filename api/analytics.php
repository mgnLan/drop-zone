<?php
// Drop Zone Royal Battle — АНАЛИТИКА: приём пакетов событий.
// POST JSON {token?, events:[{e, ts, d}]} -> ok / n (записанных).
// Основной путь веба — sendBeacon (Content-Type text/plain у beacon: читаем raw body и парсим).

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

function out($d) { echo json_encode($d, JSON_UNESCAPED_UNICODE); exit; }

try {
    $db = new PDO('sqlite:' . __DIR__ . '/data.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec("CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 0,
        event TEXT NOT NULL,
        json TEXT DEFAULT '',
        at TEXT
    )");
} catch (Exception $e) {
    out(['ok' => false, 'error' => 'db error']);
}

// --- rate-limit: 60 пакетов в минуту с IP ---
try {
    $db->exec("CREATE TABLE IF NOT EXISTS ratelimit_an (ip TEXT, ts INTEGER)");
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $now = time();
    $db->prepare("DELETE FROM ratelimit_an WHERE ts < ?")->execute([$now - 60]);
    $c = $db->prepare("SELECT COUNT(*) FROM ratelimit_an WHERE ip = ?");
    $c->execute([$ip]);
    if ((int)$c->fetchColumn() >= 60) out(['ok' => false, 'error' => 'rate limit']);
    $db->prepare("INSERT INTO ratelimit_an (ip, ts) VALUES (?, ?)")->execute([$ip, $now]);
} catch (Exception $e) { }

// sendBeacon шлёт Blob с type application/json, но у некоторых вебвью — text/plain: читаем raw
$raw = file_get_contents('php://input');
$in = json_decode($raw, true);
if (!is_array($in) || !isset($in['events']) || !is_array($in['events'])) {
    out(['ok' => false, 'error' => 'bad request']);
}

$user_id = 0;
$token = (string)($in['token'] ?? '');
if ($token !== '') {
    try {
        $st = $db->prepare("SELECT id FROM users WHERE token = ?");
        $st->execute([$token]);
        $user_id = (int)($st->fetchColumn() ?: 0);
    } catch (Exception $e) { }
}

// пакет ограничим разумным потолком — злоупотребления не пропускаем
$events = array_slice($in['events'], 0, 250);
$allowed = ['session_start', 'session_end', 'tutorial_step', 'battle_start', 'battle_end',
    'level_up', 'chest_open', 'card_play', 'pvp_fight', 'daily_claim', 'shop_view'];
$n = 0;
try {
    $db->beginTransaction();
    $ins = $db->prepare("INSERT INTO events (user_id, event, json, at) VALUES (?, ?, ?, datetime('now'))");
    foreach ($events as $ev) {
        if (!is_array($ev)) continue;
        $e = (string)($ev['e'] ?? '');
        if (!in_array($e, $allowed, true)) continue;   # мусор и подделки — мимо
        $ts = (int)($ev['ts'] ?? time());
        $d = json_encode($ev['d'] ?? [], JSON_UNESCAPED_UNICODE);
        if (strlen($d) > 2048) $d = '"oversize"';
        $ins->execute([$user_id, $e . '@' . $ts, $d]);
        $n++;
    }
    $db->commit();
} catch (Exception $e) {
    if ($db->inTransaction()) $db->rollBack();
    out(['ok' => false, 'error' => 'write error']);
}
out(['ok' => true, 'n' => $n]);
