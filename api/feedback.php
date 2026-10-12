<?php
// Drop Zone Royal Battle — обратная связь (пак 1.1 «Релиз-кандидат»)
// POST JSON {subject, text, user, token} -> пишет в таблицу feedback (data.sqlite)
// GET ?key=СЕКРЕТ -> последние 100 сообщений (для просмотра владельцем)
// Ключ просмотра: config.php -> ['feedback_key' => '...']; по умолчанию — строка ниже (сменить на проде!)

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, GET, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

function out($d) { echo json_encode($d, JSON_UNESCAPED_UNICODE); exit; }

$DZ_CFG = [];
if (file_exists(__DIR__ . '/config.php')) {
    $tmp = include __DIR__ . '/config.php';
    if (is_array($tmp)) $DZ_CFG = $tmp;
}
$VIEW_KEY = $DZ_CFG['feedback_key'] ?? 'dz_feedback_2026';

try {
    $db = new PDO('sqlite:' . __DIR__ . '/data.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec("CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user TEXT DEFAULT '',
        subject TEXT DEFAULT '',
        text TEXT NOT NULL,
        token TEXT DEFAULT '',
        ip TEXT DEFAULT '',
        created_at TEXT
    )");
} catch (Exception $e) {
    out(['ok' => false, 'error' => 'db error']);
}

// --- rate-limit: не более 10 фидбеков в минуту с одного IP (жалоб меньше, чем запросов) ---
try {
    $db->exec("CREATE TABLE IF NOT EXISTS ratelimit_fb (ip TEXT, ts INTEGER)");
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $now = time();
    $db->prepare("DELETE FROM ratelimit_fb WHERE ts < ?")->execute([$now - 60]);
    $c = $db->prepare("SELECT COUNT(*) FROM ratelimit_fb WHERE ip = ?");
    $c->execute([$ip]);
    if ((int)$c->fetchColumn() >= 10) out(['ok' => false, 'error' => 'Слишком часто — подожди минуту']);
    $db->prepare("INSERT INTO ratelimit_fb (ip, ts) VALUES (?, ?)")->execute([$ip, $now]);
} catch (Exception $e) { /* лимит не критичен */ }

// --- просмотр: GET ?key=СЕКРЕТ (константа для владельца) ---
if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    if (($_GET['key'] ?? '') !== $VIEW_KEY) {
        out(['ok' => false, 'error' => 'key?']);
    }
    $rows = $db->query("SELECT id, user, subject, text, ip, created_at FROM feedback ORDER BY id DESC LIMIT 100")->fetchAll(PDO::FETCH_ASSOC);
    out(['ok' => true, 'items' => $rows]);
}

// --- приём: POST JSON ---
$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) out(['ok' => false, 'error' => 'bad request']);
$text = trim((string)($in['text'] ?? ''));
if ($text === '' || mb_strlen($text) > 4000) out(['ok' => false, 'error' => 'пусто или слишком длинно']);
$subject = mb_substr(trim((string)($in['subject'] ?? '')), 0, 200);
$user = mb_substr(trim((string)($in['user'] ?? '')), 0, 120);
$token = mb_substr((string)($in['token'] ?? ''), 0, 64);

try {
    $db->prepare("INSERT INTO feedback (user, subject, text, token, ip, created_at) VALUES (?, ?, ?, ?, ?, ?)")
       ->execute([$user, $subject, $text, $token, $_SERVER['REMOTE_ADDR'] ?? '', date('Y-m-d H:i:s')]);
    out(['ok' => true]);
} catch (Exception $e) {
    out(['ok' => false, 'error' => 'write error']);
}
