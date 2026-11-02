<?php
// LIVE PvP 1×1: упорядоченные действия, конец хода, сдача и результат.
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
$kind = (string)($in['kind'] ?? '');
$payload = $in['payload'] ?? [];
$action_uid = mb_substr((string)($in['action_uid'] ?? ''), 0, 48);
$allowed = ['move', 'shoot', 'reload', 'end_turn', 'chest', 'cover', 'use', 'swap', 'card', 'taunt', 'graffiti', 'finish', 'forfeit'];
if (!in_array($kind, $allowed, true) || !is_array($payload)) live_out(['ok' => false, 'error' => 'bad action']);
if (strlen(json_encode($payload)) > 8000) live_out(['ok' => false, 'error' => 'action too large']);
if ($action_uid === '') live_out(['ok' => false, 'error' => 'action_uid required']);

$dup = $db->prepare('SELECT seq FROM pvp_live_actions WHERE fight_id = ? AND owner = ? AND action_uid = ?');
$dup->execute([$fight_id, $uid, $action_uid]);
$dup_seq = (int)($dup->fetchColumn() ?: 0);
if ($dup_seq > 0) {
    $fight = live_fight($db, $fight_id, $uid);
    live_out(['ok' => true, 'duplicate' => true, 'seq' => $dup_seq, 'fight' => live_public($fight, $uid)]);
}

$db->exec('BEGIN IMMEDIATE');
try {
    $fight = live_fight($db, $fight_id, $uid);
    live_touch_and_tick($db, $fight, $uid);
    if ($fight['status'] !== 'active') {
        $db->exec('COMMIT');
        live_out(['ok' => false, 'error' => 'Бой уже завершён', 'fight' => live_public($fight, $uid)]);
    }
    $side = live_side($fight, $uid);

    if ($kind === 'forfeit') {
        $seq = live_append_action($db, $fight, $uid, $kind, $payload, $action_uid);
        live_finish($db, $fight, 1 - $side);
        $db->exec('COMMIT');
        live_out(['ok' => true, 'seq' => $seq, 'fight' => live_public($fight, $uid)]);
    }
    if ($kind === 'finish') {
        $winner = (int)($payload['winner_side'] ?? -1);
        if ($winner < 0 || $winner > 1) {
            $db->exec('ROLLBACK');
            live_out(['ok' => false, 'error' => 'bad winner']);
        }
        $seq = live_append_action($db, $fight, $uid, $kind, ['winner_side' => $winner], $action_uid);
        live_finish($db, $fight, $winner);
        $db->exec('COMMIT');
        live_out(['ok' => true, 'seq' => $seq, 'fight' => live_public($fight, $uid)]);
    }

    if ((int)$fight['turn_side'] !== $side) {
        $db->exec('ROLLBACK');
        live_out(['ok' => false, 'error' => 'Сейчас ход соперника', 'fight' => live_public($fight, $uid)]);
    }
    $seq = live_append_action($db, $fight, $uid, $kind, $payload, $action_uid);
    if ($kind === 'end_turn') {
        $next = 1 - $side;
        $turn_no = (int)$fight['turn_no'] + 1;
        $deadline = time() + LIVE_TURN_SECONDS;
        $db->prepare('UPDATE pvp_live_fights SET turn_side=?, turn_no=?, deadline=? WHERE fight_id=?')
           ->execute([$next, $turn_no, $deadline, $fight_id]);
        $fight['turn_side'] = $next;
        $fight['turn_no'] = $turn_no;
        $fight['deadline'] = $deadline;
    }
    $db->exec('COMMIT');
} catch (Throwable $e) {
    if ($db->inTransaction()) $db->exec('ROLLBACK');
    live_out(['ok' => false, 'error' => 'Действие не принято']);
}

live_out(['ok' => true, 'seq' => $seq, 'fight' => live_public($fight, $uid)]);
