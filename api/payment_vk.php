<?php
// Drop Zone Royal Battle — приём платёжных уведомлений VK.
// URL настроен в консоли VK: Платежи → Подключение → URL для платёжных уведомлений.
// ВК шлёт GET/POST с параметрами notification_type, order_id, status, item, price, sig.
// Здесь: проверка sig, лог, подтверждение/отмена заказа.
// Начисление монет игроку НЕ здесь — оно в index.php (action=buy/buybp) через
// верификацию orders.getById: одно место начисления, idempotency по order_id.

header('Content-Type: application/json; charset=utf-8');

$APP_ID = 54822735;

function pay_out($d) { echo json_encode($d, JSON_UNESCAPED_UNICODE); exit; }

// --- параметры: ВК шлёт их в query string (GET), принимаем и POST ---
$params = $_GET;
if (!$params && $_SERVER['REQUEST_METHOD'] === 'POST') {
    $ct = $_SERVER['CONTENT_TYPE'] ?? '';
    if (stripos($ct, 'application/json') !== false) {
        $params = json_decode(file_get_contents('php://input'), true) ?: [];
    } else {
        $params = $_POST;
    }
}
if (!is_array($params)) $params = [];

$cfg = [];
if (file_exists(__DIR__ . '/config.php')) {
    $tmp = include __DIR__ . '/config.php';
    if (is_array($tmp)) $cfg = $tmp;
}
$SECURE = (string)($cfg['vk_secure_key'] ?? '');

// --- лог всех уведомлений (в т.ч. с невалидной подписью — для отладки) ---
try {
    $db = new PDO('sqlite:' . __DIR__ . '/data.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $db->exec("CREATE TABLE IF NOT EXISTS vk_pay_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        at TEXT,
        ip TEXT,
        notification_type TEXT,
        order_id TEXT,
        status TEXT,
        item TEXT,
        price INTEGER,
        user_id INTEGER,
        app_id INTEGER,
        sig_ok INTEGER,
        raw TEXT
    )");
    $db->prepare("INSERT INTO vk_pay_log (at, ip, notification_type, order_id, status, item, price, user_id, app_id, sig_ok, raw)
        VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
       ->execute([
            $_SERVER['REMOTE_ADDR'] ?? '',
            (string)($params['notification_type'] ?? ''),
            (string)($params['order_id'] ?? ''),
            (string)($params['status'] ?? ''),
            (string)($params['item'] ?? ''),
            (int)($params['price'] ?? 0),
            (int)($params['user_id'] ?? 0),
            (int)($params['app_id'] ?? 0),
            0,
            substr(json_encode($params, JSON_UNESCAPED_UNICODE), 0, 4000),
        ]);
} catch (Exception $e) { /* лог не критичен */ }

// --- проверка подписи: md5(конкатенация key=value по алфавиту ключей + защищённый ключ) ---
function vk_pay_sig_ok($params, $secret) {
    if ($secret === '' || !isset($params['sig'])) return false;
    $sig = (string)$params['sig'];
    $pairs = [];
    foreach ($params as $k => $v) {
        if ((string)$k === 'sig') continue;
        if (is_array($v)) return false;
        $pairs[(string)$k] = (string)$k . '=' . (string)$v;
    }
    ksort($pairs);
    $expect = md5(implode('', $pairs) . $secret);
    return hash_equals($expect, $sig);
}

if (!vk_pay_sig_ok($params, $SECURE)) {
    pay_out(['error' => ['error_code' => 10, 'error_msg' => 'bad sig', 'critical' => true]]);
}

if ((int)($params['app_id'] ?? 0) !== $APP_ID) {
    pay_out(['error' => ['error_code' => 11, 'error_msg' => 'bad app', 'critical' => true]]);
}

$type = (string)($params['notification_type'] ?? '');
$orderId = (int)($params['order_id'] ?? 0);

if ($orderId <= 0) {
    pay_out(['error' => ['error_code' => 12, 'error_msg' => 'no order', 'critical' => true]]);
}

if ($type === 'order_state_change') {
    $status = (string)($params['status'] ?? '');
    if ($status === 'chargeable') {
        // заказ оплачен — подтверждаем. app_order_id = наш id заказа (здесь = order_id ВК)
        pay_out(['response' => ['order_id' => $orderId, 'app_order_id' => $orderId]]);
    }
    // отмена/возврат — подтверждаем отмену
    pay_out(['cancel_order' => 1]);
}

if ($type === 'order_cancel') {
    // тестовый возврат из консоли VK — подтверждаем отмену заказа
    pay_out(['cancel_order' => 1]);
}

// неизвестный тип — не критично, просто подтверждаем получение
pay_out(['response' => ['order_id' => $orderId, 'app_order_id' => $orderId]]);
