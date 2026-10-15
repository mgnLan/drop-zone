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

// --- начисление по тестовому уведомлению: имя товара -> монеты (объёмы прод-экономики) ---
// BP отдельно: не монеты, а bp_owned=1. Только для _test-уведомлений, только по флагу.
$CREDIT_BY_ITEM = [
    'Пак 600 монет' => 630,
    'Пак 2250 монет' => 2475,
    'Пак 5100 монет' => 5850,
    'Пак 12000 монет' => 14400,
    'Пак 150 монет' => 150,     // новая экономика (тест-стенд / будущий прод)
    'Пак 750 монет' => 750,
    'Пак 1800 монет' => 1800,
    'Пак 3750 монет' => 3750,
];
$BP_ITEM_NAME = 'Premium Battle Pass · сезон 1';

function pay_out($d) { echo json_encode($d, JSON_UNESCAPED_UNICODE); exit; }
function pay_err($code, $msg, $critical) {
    pay_out(['error' => ['error_code' => $code, 'error_msg' => $msg, 'critical' => $critical]]);
}

// --- начисление по тестовому chargeable: та же таблица orders, что в index.php
// (action=buy) — единый idempotency по order_id, двойного начисления не будет.
function vk_pay_credit_test($db, $params, $coins_by_item) {
    global $BP_ITEM_NAME;
    $orderId = (string)($params['order_id'] ?? '');
    $item = (string)($params['item'] ?? '');
    $vkUid = (int)($params['user_id'] ?? 0);
    if ($orderId === '' || $vkUid <= 0) return;
    $db->exec("CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_id INTEGER,
        pack INTEGER,
        coins INTEGER,
        created_at TEXT
    )");
    $st = $db->prepare("SELECT order_id FROM orders WHERE order_id = ?");
    $st->execute([$orderId]);
    if ($st->fetch()) return;   // уже начислен (в т.ч. клиентским путём)
    $st = $db->prepare("SELECT id, profile FROM users WHERE vk_id = ?");
    $st->execute([$vkUid]);
    $u = $st->fetch(PDO::FETCH_ASSOC);
    if (!$u) return;            // аккаунта с таким vk_id нет — не начисляем
    $profile = $u['profile'] !== '' ? json_decode($u['profile'], true) : [];
    if (!is_array($profile)) $profile = [];
    if ($item === $BP_ITEM_NAME) {
        $profile['bp_owned'] = 1;
        $coins = 0;
    } elseif (isset($coins_by_item[$item])) {
        $coins = (int)$coins_by_item[$item];
        $profile['coins'] = (int)($profile['coins'] ?? 0) + $coins;
    } else {
        return;                 // неизвестный товар — не подтверждаем начисление
    }
    $db->prepare("UPDATE users SET profile = ?, updated_at = datetime('now') WHERE id = ?")
       ->execute([json_encode($profile, JSON_UNESCAPED_UNICODE), $u['id']]);
    $db->prepare("INSERT OR IGNORE INTO orders (order_id, user_id, pack, coins, created_at) VALUES (?, ?, ?, ?, datetime('now'))")
       ->execute([$orderId, $u['id'], 0, $coins]);
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
// Эталон — github.com/SevereCloud/vksdk payments.go (Sign/getConcatenationParams):
// значения ДЕКОДИРОВАННЫЕ (Query() в Go декодирует), конкатенация без разделителей,
// secret в конец. Для GET дополнительно пробуем вариант по сырому QUERY_STRING.
// Безопасность НЕ на sig: начисление только через index.php action=buy/buybp
// с верификацией orders.getById сервисным токеном. Несовпадение sig — только в лог.
function vk_pay_sig_attempts($params, $secret) {
    $sig = (string)($params['sig'] ?? '');
    if ($secret === '' || $sig === '') return [false, ''];
    $cands = [];
    $ks = array_keys($params);
    sort($ks, SORT_STRING);
    $dec = [];
    foreach ($ks as $k) {
        if ($k === 'sig') continue;
        $dec[] = $k . '=' . (is_scalar($params[$k]) ? (string)$params[$k] : '');
    }
    $cands['decoded_concat'] = implode('', $dec);
    $qs = (string)($_SERVER['QUERY_STRING'] ?? '');
    if ($qs !== '') {
        $pairs = [];
        foreach (explode('&', $qs) as $kv) {
            if ($kv === '') continue;
            $p = explode('=', $kv, 2);
            if ($p[0] === 'sig') continue;
            $pairs[] = $p[0] . '=' . (isset($p[1]) ? $p[1] : '');
        }
        sort($pairs, SORT_STRING);
        $cands['raw_qs'] = implode('', $pairs);
    }
    $diag = '';
    foreach ($cands as $name => $s) {
        $diag .= $name . '=' . md5($s . $secret) . ';';
        if (hash_equals(md5($s . $secret), $sig)) return [true, $name];
    }
    return [false, $diag];
}

$sig_res = vk_pay_sig_attempts($params, $SECURE);
$sig_ok = $sig_res[0] ? 1 : 0;
$sig_diag = (string)$sig_res[1];

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
        raw TEXT,
        qs TEXT
    )");
    try { $db->exec("ALTER TABLE vk_pay_log ADD COLUMN qs TEXT"); } catch (Exception $e) { /* колонка уже есть */ }
    try { $db->exec("ALTER TABLE vk_pay_log ADD COLUMN sig_diag TEXT"); } catch (Exception $e) { /* колонка уже есть */ }
    $db->prepare("INSERT INTO vk_pay_log (at, ip, notification_type, order_id, status, item, price, user_id, app_id, sig_ok, raw, qs, sig_diag)
        VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)")
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
            substr((string)($_SERVER['QUERY_STRING'] ?? ''), 0, 2000),
            substr($sig_diag, 0, 500),
        ]);
} catch (Exception $e) { /* лог не критичен */ }

// sig не совпал — НЕ блокируем: реальная защита начисления — orders.getById
// в index.php (action=buy/buybp). Несовпадение только пишем в vk_pay_log (sig_ok=0).
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

if ($base === 'order_state_change' || $base === 'order_status_change') {
    if ($orderId <= 0) pay_err(11, 'no order', true);
    $status = (string)($params['status'] ?? '');
    if ($status === 'chargeable') {
        // тест-режим (приложение на модерации): VK НЕ отдаёт тестовый заказ
        // в orders.getById — клиентский путь buy завершиться не может.
        // Начисляем сами по уведомлению. Только _test, только по флагу в config.php:
        //   'vk_pay_test_credit' => true
        // Реальных денег в тесте нет. ПОСЛЕ прохождения модерации флаг убрать/выключить —
        // реальные заказы подтверждаются здесь, а начисляются клиентским путём
        // (action=buy → orders.getById, тот же idempotency-таблицей orders).
        $is_test = preg_match('/_test$/', $type) === 1;
        if ($is_test && !empty($cfg['vk_pay_test_credit']) && isset($db) && $db instanceof PDO) {
            vk_pay_credit_test($db, $params, $CREDIT_BY_ITEM);
        }
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
