<?php
// LIVE PvP 1×1: heartbeat, таймеры и пакет действий после указанного seq.
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
$fight_id = (string)($in['fight_id'] ?? '');
$since = max(0, (int)($in['since'] ?? 0));
$fight = live_fight($db, $fight_id, $uid);

$db->exec('BEGIN IMMEDIATE');
try {
    // Перечитываем под блокировкой, чтобы таймер не сработал дважды на двух клиентах.
    $fight = live_fight($db, $fight_id, $uid);
    live_touch_and_tick($db, $fight, $uid);
    $db->exec('COMMIT');
} catch (Throwable $e) {
    if ($db->inTransaction()) $db->exec('ROLLBACK');
    live_out(['ok' => false, 'error' => 'Ошибка состояния боя']);
}

live_out([
    'ok' => true,
    'fight' => live_public($fight, $uid),
    'actions' => live_actions($db, $fight_id, $since),
]);
