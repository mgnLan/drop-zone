<?php
// Drop Zone Royal Battle — API аккаунтов
// Регистрация/вход по почте + хранение профиля (JSON). SQLite, без внешних зависимостей.
// Позже сюда добавятся vk_id / max_id — тот же аккаунт, другой способ входа.

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: POST, OPTIONS');
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') { http_response_code(204); exit; }

function out($d) { echo json_encode($d, JSON_UNESCAPED_UNICODE); exit; }

try {
    $db = new PDO('sqlite:' . __DIR__ . '/data.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec("CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        pass_hash TEXT NOT NULL,
        token TEXT,
        profile TEXT DEFAULT '',
        vk_id TEXT DEFAULT NULL,
        max_id TEXT DEFAULT NULL,
        created_at TEXT,
        updated_at TEXT
    )");
} catch (Exception $e) {
    out(['ok' => false, 'error' => 'db error']);
}

$in = json_decode(file_get_contents('php://input'), true);
if (!is_array($in)) out(['ok' => false, 'error' => 'bad request']);
$action = $in['action'] ?? '';

if ($action === 'register') {
    $email = strtolower(trim($in['email'] ?? ''));
    $pass  = (string)($in['password'] ?? '');
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) out(['ok' => false, 'error' => 'Некорректная почта']);
    if (strlen($pass) < 6) out(['ok' => false, 'error' => 'Пароль — минимум 6 символов']);
    $st = $db->prepare("SELECT id FROM users WHERE email = ?");
    $st->execute([$email]);
    if ($st->fetch()) out(['ok' => false, 'error' => 'Такая почта уже зарегистрирована']);
    $token = bin2hex(random_bytes(24));
    $db->prepare("INSERT INTO users (email, pass_hash, token, created_at, updated_at) VALUES (?, ?, ?, datetime('now'), datetime('now'))")
       ->execute([$email, password_hash($pass, PASSWORD_DEFAULT), $token]);
    out(['ok' => true, 'token' => $token, 'profile' => new stdClass()]);
}

if ($action === 'login') {
    $email = strtolower(trim($in['email'] ?? ''));
    $pass  = (string)($in['password'] ?? '');
    $st = $db->prepare("SELECT * FROM users WHERE email = ?");
    $st->execute([$email]);
    $u = $st->fetch(PDO::FETCH_ASSOC);
    if (!$u || !password_verify($pass, $u['pass_hash'])) out(['ok' => false, 'error' => 'Неверная почта или пароль']);
    $token = bin2hex(random_bytes(24));
    $db->prepare("UPDATE users SET token = ?, updated_at = datetime('now') WHERE id = ?")->execute([$token, $u['id']]);
    $profile = $u['profile'] !== '' ? json_decode($u['profile'], true) : new stdClass();
    if ($profile === null) $profile = new stdClass();
    out(['ok' => true, 'token' => $token, 'profile' => $profile]);
}

if ($action === 'save') {
    $token = (string)($in['token'] ?? '');
    $profile = $in['profile'] ?? null;
    if ($token === '' || !is_array($profile)) out(['ok' => false, 'error' => 'bad token or profile']);
    $st = $db->prepare("UPDATE users SET profile = ?, updated_at = datetime('now') WHERE token = ?");
    $st->execute([json_encode($profile, JSON_UNESCAPED_UNICODE), $token]);
    if ($st->rowCount() === 0) out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);
    out(['ok' => true]);
}

if ($action === 'load') {
    $token = (string)($in['token'] ?? '');
    $st = $db->prepare("SELECT profile FROM users WHERE token = ?");
    $st->execute([$token]);
    $u = $st->fetch(PDO::FETCH_ASSOC);
    if (!$u) out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);
    $profile = $u['profile'] !== '' ? json_decode($u['profile'], true) : new stdClass();
    if ($profile === null) $profile = new stdClass();
    out(['ok' => true, 'profile' => $profile]);
}

out(['ok' => false, 'error' => 'unknown action']);
