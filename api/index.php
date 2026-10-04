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

// --- rate-limit: не более 30 запросов в минуту с одного IP ---
try {
    $db->exec("CREATE TABLE IF NOT EXISTS ratelimit (ip TEXT, ts INTEGER)");
    $ip = $_SERVER['REMOTE_ADDR'] ?? 'unknown';
    $now = time();
    $db->prepare("DELETE FROM ratelimit WHERE ts < ?")->execute([$now - 60]);
    $c = $db->prepare("SELECT COUNT(*) FROM ratelimit WHERE ip = ?");
    $c->execute([$ip]);
    if ((int)$c->fetchColumn() >= 30) out(['ok' => false, 'error' => 'Слишком много запросов — подожди минуту']);
    $db->prepare("INSERT INTO ratelimit (ip, ts) VALUES (?, ?)")->execute([$ip, $now]);
} catch (Exception $e) { /* лимит не критичен — не ломаем запрос */ }

// --- секреты приложения (config.php не в репо) ---
$DZ_CFG = [];
if (file_exists(__DIR__ . '/config.php')) {
    $tmp = include __DIR__ . '/config.php';
    if (is_array($tmp)) $DZ_CFG = $tmp;
}

// проверка подписи launch-параметров VK Mini Apps:
// sign = base64url(sha256(параметры ksort key=value через '&' + защищённый ключ))
function vk_launch_valid($launch, $secret) {
    if (!is_array($launch) || $secret === '' || !isset($launch['sign'], $launch['vk_user_id'])) return false;
    $sign = (string)$launch['sign'];
    if ($sign === '') return false;
    // в подпись входят ТОЛЬКО параметры с префиксом vk_ — остальные ВК добавляет
    // к запуску произвольно (access_token_settings, odr_enabled, api_url и прочие)
    $params = [];
    foreach ($launch as $k => $v) {
        if (strncmp((string)$k, 'vk_', 3) === 0) $params[(string)$k] = (string)$v;
    }
    if (!$params) return false;
    ksort($params);
    // срок жизни ссылки проверяем, только если ВК передал vk_ts
    if (isset($params['vk_ts']) && abs(time() - (int)$params['vk_ts']) > 172800) return false;
    $hash = hash_hmac('sha256', http_build_query($params), $secret, true);
    // обе стороны приводим к base64url без набивки
    $norm = function ($s) { return rtrim(strtr($s, '+/', '-_'), '='); };
    return hash_equals($norm(base64_encode($hash)), $norm($sign));
}

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
    sleep(1); // анти-bruteforce: подбор пароля не быстрее 1 попытки в секунду
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

if ($action === 'vklogin') {
    // бесшовный вход из мини-приложения ВК. Личность подтверждает ТОЛЬКО подпись
    // launch-параметров (sign + защищённый ключ). Вход по голому vk_id удалён:
    // vk_id публичен, любой мог бы зайти в чужой аккаунт. Нет sign — вход по почте.
    $launch = $in['launch'] ?? null;
    $secret = (string)($DZ_CFG['vk_secure_key'] ?? '');
    if ($secret === '') out(['ok' => false, 'error' => 'secure key not configured']);
    $name = trim(mb_substr((string)($in['name'] ?? ''), 0, 32));
    if (!is_array($launch) || !vk_launch_valid($launch, $secret)) {
        out(['ok' => false, 'error' => 'bad sign']);
    }
    $vkId = trim((string)$launch['vk_user_id']);
    if ($vkId === '' || !ctype_digit($vkId)) out(['ok' => false, 'error' => 'bad request']);
    // имя: если клиент прислал пустое (VKWebAppGetUserInfo в вебвью ВК может молчать
    // вообще) — дозапрашиваем серверно сервисным ключом, клиент от имени не зависит
    if ($name === '') {
        $app_token = (string)($DZ_CFG['vk_app_token'] ?? '');
        if ($app_token !== '') {
            $q = http_build_query(['user_ids' => $vkId, 'v' => '5.131', 'access_token' => $app_token]);
            $resp = @file_get_contents('https://api.vk.com/method/users.get?' . $q);
            if ($resp !== false) {
                $jd = json_decode($resp, true);
                if (is_array($jd) && isset($jd['response'][0]) && is_array($jd['response'][0])) {
                    $u0 = $jd['response'][0];
                    $name = trim(((string)($u0['first_name'] ?? '')) . ' ' . ((string)($u0['last_name'] ?? '')));
                    $name = trim(mb_substr($name, 0, 32));
                }
            }
        }
    }
    $st = $db->prepare("SELECT * FROM users WHERE vk_id = ?");
    $st->execute([$vkId]);
    $u = $st->fetch(PDO::FETCH_ASSOC);
    if (!$u) {
        $email = 'vk' . $vkId . '@dropzone.local';
        $token = bin2hex(random_bytes(24));
        $db->prepare("INSERT INTO users (email, pass_hash, token, vk_id, created_at, updated_at) VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))")
           ->execute([$email, password_hash($token, PASSWORD_DEFAULT), $token, $vkId]);
        out(['ok' => true, 'token' => $token, 'profile' => new stdClass(), 'new' => 1, 'name' => $name]);
    }
    $token = bin2hex(random_bytes(24));
    $db->prepare("UPDATE users SET token = ?, updated_at = datetime('now') WHERE id = ?")->execute([$token, $u['id']]);
    $profile = $u['profile'] !== '' ? json_decode($u['profile'], true) : new stdClass();
    if ($profile === null) $profile = new stdClass();
    out(['ok' => true, 'token' => $token, 'profile' => $profile, 'name' => $name]);
}

if ($action === 'save') {
    $token = (string)($in['token'] ?? '');
    $profile = $in['profile'] ?? null;
    if ($token === '' || !is_array($profile)) out(['ok' => false, 'error' => 'bad token or profile']);
    // лимит: 256 КБ на профиль — больше не нужно и безопаснее
    if (strlen(json_encode($profile)) > 262144) out(['ok' => false, 'error' => 'profile too large']);
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
    // верификация заказа у ВК. Токен приложения — в config.php (не в репо)
    $VK_APP_TOKEN = (string)($DZ_CFG['vk_app_token'] ?? '');
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

if ($action === 'buybp') {
    // покупка Premium-пропуска Battle Pass: верификация order_id у ВК, bp_owned ставит сервер
    $token   = (string)($in['token'] ?? '');
    $orderId = trim((string)($in['order_id'] ?? ''));
    if ($token === '' || $orderId === '') out(['ok' => false, 'error' => 'bad request']);
    $st = $db->prepare("SELECT id, profile FROM users WHERE token = ?");
    $st->execute([$token]);
    $u = $st->fetch(PDO::FETCH_ASSOC);
    if (!$u) out(['ok' => false, 'error' => 'Сессия устарела — войди снова']);
    // idempotency: один order_id — одна активация (pack=-1 — маркер пропуска)
    $db->exec("CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_id INTEGER,
        pack INTEGER,
        coins INTEGER,
        created_at TEXT
    )");
    $st = $db->prepare("SELECT order_id FROM orders WHERE order_id = ?");
    $st->execute([$orderId]);
    if ($st->fetch()) out(['ok' => true, 'duplicate' => true]);
    $VK_APP_TOKEN = (string)($DZ_CFG['vk_app_token'] ?? '');
    if ($VK_APP_TOKEN !== '') {
        $vk = @file_get_contents('https://api.vk.com/method/orders.getById?'
            . http_build_query(['order_id' => $orderId, 'access_token' => $VK_APP_TOKEN, 'v' => '5.199']));
        $vkr = $vk ? json_decode($vk, true) : null;
        $status = $vkr['response']['status'] ?? null;
        if ($status === null || (int)$status !== 1) { // 1 = оплачен
            out(['ok' => false, 'error' => 'Заказ не подтверждён ВК']);
        }
    } else {
        out(['ok' => false, 'error' => 'payments disabled']);
    }
    $profile = $u['profile'] !== '' ? json_decode($u['profile'], true) : [];
    if (!is_array($profile)) $profile = [];
    $profile['bp_owned'] = 1;
    $db->prepare("UPDATE users SET profile = ?, updated_at = datetime('now') WHERE id = ?")
       ->execute([json_encode($profile, JSON_UNESCAPED_UNICODE), $u['id']]);
    $db->prepare("INSERT INTO orders (order_id, user_id, pack, coins, created_at) VALUES (?, ?, ?, ?, datetime('now'))")
       ->execute([$orderId, $u['id'], -1, 0]);
    out(['ok' => true]);
}

out(['ok' => false, 'error' => 'unknown action']);
