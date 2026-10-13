<?php
// Drop Zone Royal Battle — ASYNC PvP: матчмейкинг.
// POST JSON {token, size} -> {fight_id, seed, bot, opponent_name, opponent_rating, fighters}

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
        owner INTEGER PRIMARY KEY, name TEXT DEFAULT '', squad_lvl INTEGER DEFAULT 1,
        json TEXT DEFAULT '', rating INTEGER DEFAULT 1000, anomalies INTEGER DEFAULT 0, updated_at TEXT
    )");
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
    $db->exec("CREATE TABLE IF NOT EXISTS pvp_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        owner INTEGER,
        opponent TEXT DEFAULT '',
        outcome TEXT DEFAULT '',
        delta INTEGER DEFAULT 0,
        bot INTEGER DEFAULT 0,
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
$size = (int)($in['size'] ?? 0);
if ($token === '' || $size < 1 || $size > 4) out(['ok' => false, 'error' => 'bad request']);

$st = $db->prepare("SELECT id FROM users WHERE token = ?");
$st->execute([$token]);
$uid = (int)($st->fetchColumn() ?: 0);
if ($uid <= 0) out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);

$ms = $db->prepare("SELECT json, rating, squad_lvl FROM pvp_snapshots WHERE owner = ?");
$ms->execute([$uid]);
$mine = $ms->fetch(PDO::FETCH_ASSOC);
if (!$mine) out(['ok' => false, 'error' => 'Сначала сохрани отряд (pvp_push)']);
$my_rating = (int)$mine['rating'];
$my_lvl = (int)$mine['squad_lvl'];
$my_snap = json_decode($mine['json'], true);

// --- пул: |рейтинг| ≤ 200 И |уровень| ≤ 1, не сам, не из последних 3 боёв ---
$recent = [];
try {
    $rh = $db->prepare("SELECT opponent FROM pvp_history WHERE owner = ? ORDER BY id DESC LIMIT 3");
    $rh->execute([$uid]);
    foreach ($rh->fetchAll(PDO::FETCH_COLUMN) as $rn) $recent[] = (string)$rn;
} catch (Exception $e) { }

$cand = $db->prepare("SELECT owner, name, rating, squad_lvl, json FROM pvp_snapshots
    WHERE owner != ? AND ABS(rating - ?) <= 200 AND ABS(squad_lvl - ?) <= 1
    ORDER BY ABS(rating - ?) ASC, RANDOM() LIMIT 8");
$cand->execute([$uid, $my_rating, $my_lvl, $my_rating]);

$pick = null;
foreach ($cand->fetchAll(PDO::FETCH_ASSOC) as $row) {
    if (in_array('u' . $row['owner'], $recent, true)) continue;
    $pick = $row;
    break;
}

$fight_id = bin2hex(random_bytes(8));
$seed = random_int(1, 2147483646);

if ($pick) {
    $opp_snap = json_decode($pick['json'], true);
    $opp_name = (string)$pick['name'];
    $opp_rating = (int)$pick['rating'];
    $defender = (int)$pick['owner'];
    $bot = 0;
    $opp_fighters = $opp_snap['fighters'] ?? [];
    // под размер отряда атакующего: добираем/обрезаем честно (те же бойцы по кругу нельзя — только обрезка)
    $opp_fighters = array_slice($opp_fighters, 0, $size);
    if (count($opp_fighters) < $size) {
        // отряд меньше — добиваем претендентами под уровень оппонента
        $opp_fighters = array_merge($opp_fighters, dz_make_pretender($size - count($opp_fighters), (int)$pick['squad_lvl']));
    }
} else {
    // пустой пул — серверный претендент
    $bot = 1;
    $defender = 0;
    $opp_rating = 1000;
    $opp_name = 'Претендент №' . rand(100, 999);
    $opp_fighters = dz_make_pretender($size, $my_lvl);
}

$db->prepare("INSERT INTO pvp_fights (fight_id, attacker, defender, bot, opp_name, opp_rating, seed, status, created_at)
              VALUES (?, ?, ?, ?, ?, ?, ?, 'open', datetime('now'))")
   ->execute([$fight_id, $uid, $defender, $bot, $opp_name, $opp_rating, $seed]);

out([
    'ok' => true,
    'fight_id' => $fight_id,
    'seed' => $seed,
    'bot' => $bot,
    'opponent_name' => $opp_name,
    'opponent_rating' => $opp_rating,
    'my_rating' => $my_rating,
    'fighters' => $opp_fighters,
]);
