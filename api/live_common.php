<?php
// LIVE PvP 1×1: общая схема, состояние комнаты и рейтинг.
require_once __DIR__ . '/pvp_common.php';

const LIVE_TURN_SECONDS = 40;
const LIVE_QUEUE_STALE = 20;
const LIVE_DISCONNECT_SECONDS = 90;

function live_out(array $data): void {
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

function live_input(): array {
    $in = json_decode(file_get_contents('php://input'), true);
    if (!is_array($in)) live_out(['ok' => false, 'error' => 'bad request']);
    return $in;
}

function live_db(): PDO {
    $db = new PDO('sqlite:' . __DIR__ . '/data.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_live_queue (
        owner INTEGER PRIMARY KEY, name TEXT DEFAULT '', rating INTEGER DEFAULT 1000,
        squad_lvl INTEGER DEFAULT 1, json TEXT DEFAULT '', heartbeat INTEGER DEFAULT 0
    )");
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_live_fights (
        fight_id TEXT PRIMARY KEY, red INTEGER, blue INTEGER,
        red_name TEXT DEFAULT '', blue_name TEXT DEFAULT '',
        red_rating INTEGER DEFAULT 1000, blue_rating INTEGER DEFAULT 1000,
        red_json TEXT DEFAULT '', blue_json TEXT DEFAULT '', seed INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active', turn_side INTEGER DEFAULT 0, turn_no INTEGER DEFAULT 1,
        seq INTEGER DEFAULT 0, deadline INTEGER DEFAULT 0,
        red_seen INTEGER DEFAULT 0, blue_seen INTEGER DEFAULT 0,
        winner INTEGER DEFAULT -1, red_delta INTEGER DEFAULT 0, blue_delta INTEGER DEFAULT 0,
        created_at INTEGER DEFAULT 0, finished_at INTEGER DEFAULT 0
    )");
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_live_actions (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fight_id TEXT, seq INTEGER,
        owner INTEGER DEFAULT 0, kind TEXT DEFAULT '', payload TEXT DEFAULT '',
        action_uid TEXT DEFAULT '', at INTEGER DEFAULT 0,
        UNIQUE(fight_id, seq), UNIQUE(fight_id, owner, action_uid)
    )");
    // На существующем проде pvp_snapshots могла быть создана ранней async-версией
    // без allow_offline. CREATE IF NOT EXISTS такую таблицу не обновляет — мигрируем.
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_snapshots (
        owner INTEGER PRIMARY KEY, name TEXT DEFAULT '', squad_lvl INTEGER DEFAULT 1,
        json TEXT DEFAULT '', rating INTEGER DEFAULT 1000, anomalies INTEGER DEFAULT 0,
        allow_offline INTEGER DEFAULT 0, updated_at TEXT
    )");
    $snapshot_cols = $db->query('PRAGMA table_info(pvp_snapshots)')->fetchAll(PDO::FETCH_ASSOC);
    $snapshot_names = array_map(static fn($c) => $c['name'], $snapshot_cols);
    if (!in_array('allow_offline', $snapshot_names, true)) {
        $db->exec('ALTER TABLE pvp_snapshots ADD COLUMN allow_offline INTEGER DEFAULT 0');
    }
    return $db;
}

function live_auth(PDO $db, string $token): int {
    if ($token === '') return 0;
    $st = $db->prepare('SELECT id FROM users WHERE token = ?');
    $st->execute([$token]);
    return (int)($st->fetchColumn() ?: 0);
}

function live_fight(PDO $db, string $fight_id, int $uid): array {
    $st = $db->prepare('SELECT * FROM pvp_live_fights WHERE fight_id = ?');
    $st->execute([$fight_id]);
    $fight = $st->fetch(PDO::FETCH_ASSOC);
    if (!$fight || ((int)$fight['red'] !== $uid && (int)$fight['blue'] !== $uid)) {
        live_out(['ok' => false, 'error' => 'Бой не найден']);
    }
    return $fight;
}

function live_side(array $fight, int $uid): int {
    return (int)$fight['red'] === $uid ? 0 : 1;
}

function live_public(array $fight, int $uid): array {
    $side = live_side($fight, $uid);
    $me = $side === 0 ? $fight : $fight;
    $opp_name = $side === 0 ? (string)$fight['blue_name'] : (string)$fight['red_name'];
    $opp_rating = $side === 0 ? (int)$fight['blue_rating'] : (int)$fight['red_rating'];
    return [
        'fight_id' => (string)$fight['fight_id'], 'side' => $side,
        'seed' => (int)$fight['seed'], 'status' => (string)$fight['status'],
        'turn_side' => (int)$fight['turn_side'], 'turn_no' => (int)$fight['turn_no'],
        'seq' => (int)$fight['seq'], 'deadline' => (int)$fight['deadline'],
        'server_now' => time(), 'winner' => (int)$fight['winner'],
        'opponent_name' => $opp_name, 'opponent_rating' => $opp_rating,
        'my_rating' => $side === 0 ? (int)$fight['red_rating'] : (int)$fight['blue_rating'],
        'rating_delta' => $side === 0 ? (int)$fight['red_delta'] : (int)$fight['blue_delta'],
        'red_fighters' => json_decode((string)$fight['red_json'], true),
        'blue_fighters' => json_decode((string)$fight['blue_json'], true),
    ];
}

function live_append_action(PDO $db, array &$fight, int $owner, string $kind, array $payload, string $action_uid = ''): int {
    if ($action_uid === '') $action_uid = 'sys_' . bin2hex(random_bytes(8));
    $seq = (int)$fight['seq'] + 1;
    $db->prepare("INSERT INTO pvp_live_actions (fight_id, seq, owner, kind, payload, action_uid, at)
                  VALUES (?, ?, ?, ?, ?, ?, ?)")
       ->execute([$fight['fight_id'], $seq, $owner, $kind,
                  json_encode($payload, JSON_UNESCAPED_UNICODE), $action_uid, time()]);
    $db->prepare('UPDATE pvp_live_fights SET seq = ? WHERE fight_id = ?')->execute([$seq, $fight['fight_id']]);
    $fight['seq'] = $seq;
    return $seq;
}

function live_finish(PDO $db, array &$fight, int $winner_side): void {
    if ($fight['status'] !== 'active') return;
    $winner_side = $winner_side === 1 ? 1 : 0;
    $red = (int)$fight['red'];
    $blue = (int)$fight['blue'];
    $rr = (int)$fight['red_rating'];
    $br = (int)$fight['blue_rating'];
    $red_win = $winner_side === 0;
    $er = 1.0 / (1.0 + pow(10.0, ($br - $rr) / 400.0));
    $eb = 1.0 / (1.0 + pow(10.0, ($rr - $br) / 400.0));
    $rd = (int)round(32.0 * (($red_win ? 1.0 : 0.0) - $er));
    $bd = (int)round(32.0 * (($red_win ? 0.0 : 1.0) - $eb));
    $db->prepare('UPDATE pvp_snapshots SET rating = ? WHERE owner = ?')->execute([$rr + $rd, $red]);
    $db->prepare('UPDATE pvp_snapshots SET rating = ? WHERE owner = ?')->execute([$br + $bd, $blue]);
    $db->prepare("UPDATE pvp_live_fights SET status='done', winner=?, red_delta=?, blue_delta=?, finished_at=? WHERE fight_id=?")
       ->execute([$winner_side, $rd, $bd, time(), $fight['fight_id']]);
    $db->prepare("INSERT INTO pvp_history (owner, opponent, outcome, delta, bot, at) VALUES (?, ?, ?, ?, 0, datetime('now'))")
       ->execute([$red, $fight['blue_name'], $red_win ? 'win' : 'lose', $rd]);
    $db->prepare("INSERT INTO pvp_history (owner, opponent, outcome, delta, bot, at) VALUES (?, ?, ?, ?, 0, datetime('now'))")
       ->execute([$blue, $fight['red_name'], $red_win ? 'lose' : 'win', $bd]);
    $fight['status'] = 'done';
    $fight['winner'] = $winner_side;
    $fight['red_delta'] = $rd;
    $fight['blue_delta'] = $bd;
}

function live_touch_and_tick(PDO $db, array &$fight, int $uid): void {
    $now = time();
    $side = live_side($fight, $uid);
    $seen_col = $side === 0 ? 'red_seen' : 'blue_seen';
    $db->prepare("UPDATE pvp_live_fights SET $seen_col = ? WHERE fight_id = ?")
       ->execute([$now, $fight['fight_id']]);
    $fight[$seen_col] = $now;
    if ($fight['status'] !== 'active') return;

    $other_seen = $side === 0 ? (int)$fight['blue_seen'] : (int)$fight['red_seen'];
    if ($other_seen > 0 && $now - $other_seen > LIVE_DISCONNECT_SECONDS) {
        live_append_action($db, $fight, 0, 'disconnect', ['side' => 1 - $side]);
        live_finish($db, $fight, $side);
        return;
    }
    if ($now > (int)$fight['deadline']) {
        $expired = (int)$fight['turn_side'];
        live_append_action($db, $fight, 0, 'timeout', ['side' => $expired, 'turn_no' => (int)$fight['turn_no']]);
        $next = 1 - $expired;
        $turn_no = (int)$fight['turn_no'] + 1;
        $deadline = $now + LIVE_TURN_SECONDS;
        $db->prepare('UPDATE pvp_live_fights SET turn_side=?, turn_no=?, deadline=? WHERE fight_id=?')
           ->execute([$next, $turn_no, $deadline, $fight['fight_id']]);
        $fight['turn_side'] = $next;
        $fight['turn_no'] = $turn_no;
        $fight['deadline'] = $deadline;
    }
}

function live_actions(PDO $db, string $fight_id, int $since): array {
    $st = $db->prepare('SELECT seq, owner, kind, payload, at FROM pvp_live_actions WHERE fight_id = ? AND seq > ? ORDER BY seq ASC LIMIT 100');
    $st->execute([$fight_id, $since]);
    $out = [];
    foreach ($st->fetchAll(PDO::FETCH_ASSOC) as $row) {
        $out[] = [
            'seq' => (int)$row['seq'], 'owner' => (int)$row['owner'],
            'kind' => (string)$row['kind'], 'payload' => json_decode((string)$row['payload'], true),
            'at' => (int)$row['at'],
        ];
    }
    return $out;
}
