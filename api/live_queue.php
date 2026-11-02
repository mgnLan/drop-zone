<?php
// LIVE PvP 1×1: heartbeat очереди и создание комнаты двух онлайн-игроков.
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
require __DIR__ . '/live_common.php';

$db = live_db();
$in = live_input();
$uid = live_auth($db, (string)($in['token'] ?? ''));
if ($uid <= 0) live_out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);
$now = time();

// Повторный вход/перезагрузка: существующий активный бой важнее новой очереди.
$st = $db->prepare("SELECT * FROM pvp_live_fights WHERE status='active' AND (red=? OR blue=?) ORDER BY created_at DESC LIMIT 1");
$st->execute([$uid, $uid]);
$existing = $st->fetch(PDO::FETCH_ASSOC);
if ($existing) live_out(['ok' => true, 'matched' => true, 'fight' => live_public($existing, $uid)]);

if (!empty($in['cancel'])) {
    $db->prepare('DELETE FROM pvp_live_queue WHERE owner = ?')->execute([$uid]);
    live_out(['ok' => true, 'cancelled' => true]);
}

$snap = $in['snapshot'] ?? null;
list($valid, $why) = dz_validate_snapshot($snap);
if (!$valid) live_out(['ok' => false, 'error' => 'Снапшот отклонён: ' . $why]);
if (count($snap['fighters']) !== 1) live_out(['ok' => false, 'error' => 'Для живой дуэли выбери ровно одного бойца']);

$name = mb_substr(trim((string)($snap['name'] ?? 'Боец')), 0, 32);
if ($name === '') $name = 'Боец';
$lvl = max(1, (int)($snap['fighters'][0]['lvl'] ?? 1));
$json = json_encode($snap, JSON_UNESCAPED_UNICODE);

// Рейтинг общий с асинхронными дуэлями; согласие на офлайн-бой здесь не требуется.
$old = $db->prepare('SELECT rating FROM pvp_snapshots WHERE owner = ?');
$old->execute([$uid]);
$rating = (int)($old->fetchColumn() ?: 1000);
$db->prepare("INSERT INTO pvp_snapshots (owner, name, squad_lvl, json, rating, allow_offline, updated_at)
              VALUES (?, ?, ?, ?, ?, 0, datetime('now'))
              ON CONFLICT(owner) DO UPDATE SET name=excluded.name, squad_lvl=excluded.squad_lvl,
                  json=excluded.json, updated_at=excluded.updated_at")
   ->execute([$uid, $name, $lvl, $json, $rating]);

$db->exec('BEGIN IMMEDIATE');
try {
    $db->prepare('DELETE FROM pvp_live_queue WHERE heartbeat < ?')->execute([$now - LIVE_QUEUE_STALE]);
    $db->prepare("INSERT INTO pvp_live_queue (owner, name, rating, squad_lvl, json, heartbeat)
                  VALUES (?, ?, ?, ?, ?, ?)
                  ON CONFLICT(owner) DO UPDATE SET name=excluded.name, rating=excluded.rating,
                      squad_lvl=excluded.squad_lvl, json=excluded.json, heartbeat=excluded.heartbeat")
       ->execute([$uid, $name, $rating, $lvl, $json, $now]);

    $cand = $db->prepare("SELECT * FROM pvp_live_queue
        WHERE owner != ? AND ABS(rating - ?) <= 300 AND ABS(squad_lvl - ?) <= 2
        ORDER BY ABS(rating - ?) ASC, heartbeat ASC LIMIT 1");
    $cand->execute([$uid, $rating, $lvl, $rating]);
    $opp = $cand->fetch(PDO::FETCH_ASSOC);
    if (!$opp) {
        $db->exec('COMMIT');
        live_out(['ok' => true, 'matched' => false, 'waiting' => true, 'rating' => $rating]);
    }

    $fight_id = bin2hex(random_bytes(8));
    $seed = random_int(1, 2147483646);
    $deadline = $now + LIVE_TURN_SECONDS;
    $db->prepare("INSERT INTO pvp_live_fights (
            fight_id, red, blue, red_name, blue_name, red_rating, blue_rating,
            red_json, blue_json, seed, status, turn_side, turn_no, seq, deadline,
            red_seen, blue_seen, winner, created_at, finished_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', 0, 1, 0, ?, ?, ?, -1, ?, 0)")
       ->execute([$fight_id, (int)$opp['owner'], $uid, (string)$opp['name'], $name,
                  (int)$opp['rating'], $rating, (string)$opp['json'], $json,
                  $seed, $deadline, $now, $now, $now]);
    $db->prepare('DELETE FROM pvp_live_queue WHERE owner IN (?, ?)')->execute([(int)$opp['owner'], $uid]);
    $db->exec('COMMIT');
} catch (Throwable $e) {
    if ($db->inTransaction()) $db->exec('ROLLBACK');
    live_out(['ok' => false, 'error' => 'Не удалось создать бой']);
}

$st = $db->prepare('SELECT * FROM pvp_live_fights WHERE fight_id = ?');
$st->execute([$fight_id]);
$fight = $st->fetch(PDO::FETCH_ASSOC);
live_out(['ok' => true, 'matched' => true, 'fight' => live_public($fight, $uid)]);
