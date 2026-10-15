<?php
// Drop Zone Royal Battle — приём платёжных уведомлений VK.
// URL настроен в консоли VK: Платежи → Подключение → URL для платёжных уведомлений.
//
// Протокол (VK Payments API):
//  get_item            — диалог покупки спрашивает каталог; отвечаем title+price товара
//                        (ошибка 20 «товара нет» = диалог закроется с ошибкой)
//  order_state_change  — статус заказа; chargeable → подтверждаем, остальное → отмена
//  order_cancel        — возврат (в т.ч. тестовый из консоли) → подтверждаем отмену
// Тестовые уведомления (пока приложение непроверенное) приходят с суффиксом _test.
//
// Начисление игроку НЕ здесь — в index.php (action=buy/buybp) через верификацию
// orders.getById: одно место начисления, idempotency по order_id.

header('Content-Type: application/json; charset=utf-8');

$APP_ID = 54822735;

// --- каталог товаров: ключ = item (имя, которое шлёт клиент в ShowOrderBox) ---
// Цены в рублях (новая платёжная схема VK). Имена — в точности как в DZ_PACKS (export_presets.cfg).
// Два набора имён: «Пак N монет» (тест/новый клиент) и старые имена прод-клиента t1792087862.
$ITEMS = [
    'Пак 150 монет' => ['title' => 'Пак 150 монет · Точка Сброса', 'price' => 29],
    'Пак 750 монет' => ['title' => 'Пак 750 монет · Точка Сброса', 'price' => 99],
    'Пак 1800 монет' => ['title' => 'Пак 1800 монет · Точка Сброса', 'price' => 199],
    'Пак 3750 монет' => ['title' => 'Пак 3750 монет · Точка Сброса', 'price' => 399],
    'Пак 600 монет' => ['title' => 'Пак 600 монет · Точка Сброса', 'price' => 29],
    'Пак 2250 монет' => ['title' => 'Пак 2250 монет · Точка Сброса', 'price' => 99],
    'Пак 5100 монет' => ['title' => 'Пак 5100 монет · Точка Сброса', 'price' => 199],
    'Пак 12000 монет' => ['title' => 'Пак 12000 монет · Точка Сброса', 'price' => 399],
    'Premium Battle Pass · сезон 1' => ['title' => 'Premium Battle Pass · сезон 1', 'price' => 399],
];

function pay_out($d) { echo json_encode($d, JSON_UNESCAPED_UNICODE); exit; }
function pay_err($code, $msg, $critical) {
    pay_out(['error' => ['error_code' => $code, 'error_msg' => $msg, 'critical' => $critical]]);
}

// --- параметры: ВК шлёт GET (query string); принимаем и POST ---
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

// --- подпись: md5(конкатенация key=value по алфавиту ключей + защищённый ключ) ---
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
    return hash_equals(md5(implode('', $pairs) . $secret), $sig);
}

$sig_ok = vk_pay_sig_ok($params, $SECURE) ? 1 : 0;

// --- лог всех уведомлений (и с невалидной подписью — для отладки) ---
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
            $sig_ok,
            substr(json_encode($params, JSON_UNESCAPED_UNICODE), 0, 4000),
        ]);
} catch (Exception $e) { /* лог не критичен */ }

if (!$sig_ok) pay_err(10, 'bad sig', true);
if ((int)($params['app_id'] ?? 0) !== $APP_ID) pay_err(11, 'bad app', true);

$type = (string)($params['notification_type'] ?? '');
$base = preg_replace('/_test$/', '', $type);   // тестовый режим — та же логика
$orderId = (int)($params['order_id'] ?? 0);
$item = (string)($params['item'] ?? '');

if ($base === 'get_item') {
    // диалог покупки ждёт данные товара; без них — «Ваш запрос не был обработан»
    if ($orderId <= 0) pay_err(11, 'no order', true);
    if (!isset($ITEMS[$item])) pay_err(20, 'Product does not exist', true);
    pay_out([
        'title' => $ITEMS[$item]['title'],
        'price' => $ITEMS[$item]['price'],
        'expiration' => 300,   // кэш каталога 5 мин — удобно править цены на тесте
    ]);
}

if ($base === 'order_state_change') {
    if ($orderId <= 0) pay_err(11, 'no order', true);
    $status = (string)($params['status'] ?? '');
    if ($status === 'chargeable') {
        // подтверждаем заказ; app_order_id = наш id (здесь = order_id ВК)
        pay_out(['response' => ['order_id' => $orderId, 'app_order_id' => $orderId]]);
    }
    pay_out(['cancel_order' => 1]);
}

if ($base === 'order_cancel') {
    if ($orderId <= 0) pay_err(11, 'no order', true);
    pay_out(['cancel_order' => 1]);
}

// неизвестный тип — не критично, просто подтверждаем получение
if ($orderId > 0) pay_out(['response' => ['order_id' => $orderId, 'app_order_id' => $orderId]]);
pay_err(11, 'unknown notification', false);
