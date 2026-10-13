<?php
// Drop Zone Royal Battle — ASYNC PvP: рейтинговая таблица и история боёв.
// POST JSON {token} -> {rating, top:[{name,rating,wins}], history:[{opponent,outcome,delta,bot,at}]}

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

function out($d) { echo json_encode($d, JSON_UNESCAPED_UNICODE); exit; }

try {
    $db = new PDO('sqlite:' . __DIR__ . '/data.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
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
if ($token === '') out(['ok' => false, 'error' => 'bad request']);

$st = $db->prepare("SELECT id FROM users WHERE token = ?");
$st->execute([$token]);
$uid = (int)($st->fetchColumn() ?: 0);
if ($uid <= 0) out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);

$rating = 1000;
$ms = $db->prepare("SELECT rating FROM pvp_snapshots WHERE owner = ?");
$ms->execute([$uid]);
$r = $ms->fetchColumn();
if ($r !== false) $rating = (int)$r;

$top = [];
$ts = $db->query("SELECT owner, name, rating FROM pvp_snapshots ORDER BY rating DESC, owner ASC LIMIT 100");
foreach ($ts->fetchAll(PDO::FETCH_ASSOC) as $row) {
    $wc = $db->prepare("SELECT COUNT(*) FROM pvp_history WHERE owner = ? AND outcome = 'win'");
    $wc->execute([(int)$row['owner']]);
    $top[] = [
        'name' => (string)$row['name'],
        'rating' => (int)$row['rating'],
        'wins' => (int)$wc->fetchColumn(),
        'me' => (int)$row['owner'] === $uid,
    ];
}

$history = [];
$hs = $db->prepare("SELECT opponent, outcome, delta, bot, at FROM pvp_history WHERE owner = ? ORDER BY id DESC LIMIT 10");
$hs->execute([$uid]);
foreach ($hs->fetchAll(PDO::FETCH_ASSOC) as $row) {
    $history[] = [
        'opponent' => (string)$row['opponent'],
        'outcome' => (string)$row['outcome'],
        'delta' => (int)$row['delta'],
        'bot' => (int)$row['bot'],
        'at' => (string)$row['at'],
    ];
}

out(['ok' => true, 'rating' => $rating, 'top' => $top, 'history' => $history]);
