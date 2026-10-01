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

if ($action === 'buy') {
    // покупка пака монет: сервер верифицирует order_id у ВК и начисляет монеты сам.
    // Клиент НИКОГДА не начисляет покупки — только сервер (экономика не на клиенте).
    $token   = (string)($in['token'] ?? '');
    $pack_id = (int)($in['pack'] ?? -1);
    $orderId = trim((string)($in['order_id'] ?? ''));
    if ($token === '' || $orderId === '') out(['ok' => false, 'error' => 'bad request']);
    // серверная таблица цен — клиентскую не доверяем
    $PACKS = [0 => 210, 1 => 825, 2 => 1950, 3 => 4800]; // coins+bonus по индексу пака
    if (!isset($PACKS[$pack_id])) out(['ok' => false, 'error' => 'unknown pack']);
    $st = $db->prepare("SELECT id, profile FROM users WHERE token = ?");
    $st->execute([$token]);
    $u = $st->fetch(PDO::FETCH_ASSOC);
    if (!$u) out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);
    // idempotency: один order_id — одно начисление
    $db->exec("CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_id INTEGER,
        pack INTEGER,
        coins INTEGER,
        created_at TEXT
    )");
    $st = $db->prepare("SELECT order_id FROM orders WHERE order_id = ?");
    $st->execute([$orderId]);
    if ($st->fetch()) out(['ok' => true, 'duplicate' => true]); // уже начислено
    // верификация заказа у ВК. Токен приложения — в config.php (не в репо):
    //   <?php return ['vk_app_token' => '...'];
    $VK_APP_TOKEN = '';
    if (file_exists(__DIR__ . '/config.php')) {
        $cfg = include __DIR__ . '/config.php';
        if (is_array($cfg) && isset($cfg['vk_app_token'])) $VK_APP_TOKEN = $cfg['vk_app_token'];
    }
    if ($VK_APP_TOKEN !== '') {
        $vk = @file_get_contents('https://api.vk.com/method/orders.getById?'
            . http_build_query(['order_id' => $orderId, 'access_token' => $VK_APP_TOKEN, 'v' => '5.199']));
        $vkr = $vk ? json_decode($vk, true) : null;
        $status = $vkr['response']['status'] ?? null;
        if ($status === null || (int)$status !== 1) { // 1 = оплачен
            out(['ok' => false, 'error' => 'Заказ не подтверждён ВК']);
        }
    } else {
        // токен не настроен — платежи выключены: не начисляем
        out(['ok' => false, 'error' => 'payments disabled']);
    }
    // начисление: профиль хранится целиком — поправим coins на сервере
    $profile = $u['profile'] !== '' ? json_decode($u['profile'], true) : [];
    if (!is_array($profile)) $profile = [];
    $profile['coins'] = (int)($profile['coins'] ?? 0) + $PACKS[$pack_id];
    $db->prepare("UPDATE users SET profile = ?, updated_at = datetime('now') WHERE id = ?")
       ->execute([json_encode($profile, JSON_UNESCAPED_UNICODE), $u['id']]);
    $db->prepare("INSERT INTO orders (order_id, user_id, pack, coins, created_at) VALUES (?, ?, ?, ?, datetime('now'))")
       ->execute([$orderId, $u['id'], $pack_id, $PACKS[$pack_id]]);
    out(['ok' => true, 'coins' => $profile['coins'], 'credited' => $PACKS[$pack_id]]);
}

out(['ok' => false, 'error' => 'unknown action']);
