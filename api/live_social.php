<?php
// Общий онлайн: heartbeat, один общий чат и список активных игроков без комнат.
header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }
require __DIR__ . '/live_common.php';

const SOCIAL_ONLINE_SECONDS = 25;
const SOCIAL_MESSAGE_LIMIT = 300;

$db = live_db();
$db->exec("CREATE TABLE IF NOT EXISTS pvp_social_presence (
    owner INTEGER PRIMARY KEY, name TEXT DEFAULT '', rating INTEGER DEFAULT 1000,
    playing INTEGER DEFAULT 0, seen INTEGER DEFAULT 0
)");
$db->exec("CREATE TABLE IF NOT EXISTS pvp_social_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT, owner INTEGER, name TEXT DEFAULT '',
    text TEXT DEFAULT '', at INTEGER DEFAULT 0
)");
$db->exec('CREATE INDEX IF NOT EXISTS idx_social_messages_at ON pvp_social_messages(at)');
$db->exec('CREATE INDEX IF NOT EXISTS idx_social_presence_seen ON pvp_social_presence(seen)');

$in = live_input();
$uid = live_auth($db, (string)($in['token'] ?? ''));
if ($uid <= 0) live_out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);
$now = time();

$name = mb_substr(trim((string)($in['name'] ?? '')), 0, 32);
if ($name === '') {
    $st = $db->prepare('SELECT name FROM pvp_snapshots WHERE owner = ?');
    $st->execute([$uid]);
    $name = (string)($st->fetchColumn() ?: 'Боец');
}
$rating_st = $db->prepare('SELECT rating FROM pvp_snapshots WHERE owner = ?');
$rating_st->execute([$uid]);
$rating = (int)($rating_st->fetchColumn() ?: 1000);
$playing = !empty($in['playing']) ? 1 : 0;

$db->prepare("INSERT INTO pvp_social_presence (owner, name, rating, playing, seen)
              VALUES (?, ?, ?, ?, ?)
              ON CONFLICT(owner) DO UPDATE SET name=excluded.name, rating=excluded.rating,
                  playing=excluded.playing, seen=excluded.seen")
   ->execute([$uid, $name, $rating, $playing, $now]);

if (isset($in['text'])) {
    $text = trim((string)$in['text']);
    if ($text === '') live_out(['ok' => false, 'error' => 'Пустое сообщение']);
    if (mb_strlen($text) > SOCIAL_MESSAGE_LIMIT) {
        live_out(['ok' => false, 'error' => 'Сообщение слишком длинное (максимум 300 символов)']);
    }
    $last = $db->prepare('SELECT at FROM pvp_social_messages WHERE owner = ? ORDER BY id DESC LIMIT 1');
    $last->execute([$uid]);
    $last_at = (int)($last->fetchColumn() ?: 0);
    if ($now - $last_at < 1) live_out(['ok' => false, 'error' => 'Слишком быстро — отправь через секунду']);
    $db->prepare('INSERT INTO pvp_social_messages (owner, name, text, at) VALUES (?, ?, ?, ?)')
       ->execute([$uid, $name, $text, $now]);
    // Достаточно компактной истории; старые записи не раздувают SQLite бесконечно.
    $db->exec("DELETE FROM pvp_social_messages WHERE id NOT IN (SELECT id FROM pvp_social_messages ORDER BY id DESC LIMIT 500)");
}

$db->prepare('DELETE FROM pvp_social_presence WHERE seen < ?')->execute([$now - SOCIAL_ONLINE_SECONDS]);
$players_st = $db->prepare('SELECT owner, name, rating, playing FROM pvp_social_presence ORDER BY seen DESC, name LIMIT 50');
$players_st->execute();
$players = [];
foreach ($players_st->fetchAll(PDO::FETCH_ASSOC) as $row) {
    $players[] = [
        'name' => (string)$row['name'], 'rating' => (int)$row['rating'],
        'playing' => (int)$row['playing'], 'me' => (int)$row['owner'] === $uid ? 1 : 0,
    ];
}
$messages_st = $db->query('SELECT id, owner, name, text, at FROM pvp_social_messages ORDER BY id DESC LIMIT 50');
$messages = [];
foreach (array_reverse($messages_st->fetchAll(PDO::FETCH_ASSOC)) as $row) {
    $messages[] = [
        'id' => (int)$row['id'], 'name' => (string)$row['name'],
        'text' => (string)$row['text'], 'at' => (int)$row['at'],
        'me' => (int)$row['owner'] === $uid ? 1 : 0,
    ];
}
live_out(['ok' => true, 'online' => count($players), 'players' => $players, 'messages' => $messages, 'server_now' => $now]);
