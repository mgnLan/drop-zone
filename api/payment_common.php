<?php
// Единый серверный каталог и строгая проверка заказов VK Payments.
// Клиент присылает только order_id и идентификатор пака; сумма и товар — отсюда.

function dz_payment_packs(): array {
    return [
        0 => ['item' => 'Пак 150 монет', 'price' => 129, 'coins' => 150],
        1 => ['item' => 'Пак 750 монет', 'price' => 549, 'coins' => 750],
        2 => ['item' => 'Пак 1800 монет', 'price' => 1199, 'coins' => 1800],
        3 => ['item' => 'Пак 3750 монет', 'price' => 2299, 'coins' => 3750],
    ];
}

// Первая монетная покупка аккаунта. BP (pack=-1) не расходует скидку.
// Клиентский флаг нигде не используется: источник истины — серверная таблица orders.
function dz_first_purchase_available(PDO $db, int $userId): bool {
    if ($userId <= 0) return false;
    dz_orders_init($db);
    $st = $db->prepare('SELECT 1 FROM orders WHERE user_id = ? AND pack >= 0 LIMIT 1');
    $st->execute([$userId]);
    return $st->fetchColumn() === false;
}

function dz_payment_pack_for_user(array $pack, bool $firstPurchase): array {
    if ($firstPurchase) $pack['price'] = (int)round(((int)$pack['price']) * 0.75);
    $pack['first_purchase'] = $firstPurchase ? 1 : 0;
    return $pack;
}

function dz_profile_with_payment_flag(PDO $db, int $userId, $profile): array {
    if (!is_array($profile)) $profile = [];
    $profile['first_purchase_discount'] = dz_first_purchase_available($db, $userId) ? 1 : 0;
    return $profile;
}

function dz_payment_bp(): array {
    return ['item' => 'Premium Battle Pass · сезон 1', 'price' => 399, 'coins' => 0];
}

function dz_vk_order_fetch(string $orderId, string $appToken) {
    if ($orderId === '' || !ctype_digit($orderId) || $appToken === '') return null;
    $query = http_build_query([
        'order_id' => $orderId,
        'access_token' => $appToken,
        'v' => '5.199',
    ]);
    $ctx = stream_context_create(['http' => ['timeout' => 10]]);
    $raw = @file_get_contents('https://api.vk.com/method/orders.getById?' . $query, false, $ctx);
    if ($raw === false) return null;
    $decoded = json_decode($raw, true);
    return is_array($decoded) ? $decoded : null;
}

// Возвращает [true, заказ] либо [false, понятная ошибка].
// orders.getById возвращает МАССИВ заказов: response[0], а не response.status.
function dz_vk_order_verify($vkr, string $orderId, array $expected, string $vkUserId): array {
    if (!is_array($vkr) || !isset($vkr['response'][0]) || !is_array($vkr['response'][0])) {
        return [false, 'Заказ не найден ВК'];
    }
    $order = $vkr['response'][0];
    if ((string)($order['id'] ?? '') !== $orderId) {
        return [false, 'Номер заказа не совпал'];
    }
    // charged — строковый статус оплаченного заказа VK;
    // число 1 оставлено только для совместимости со старым ответом API.
    $status = strtolower((string)($order['status'] ?? ''));
    if ($status !== 'charged' && $status !== '1') {
        return [false, 'Заказ не оплачен'];
    }
    if ((int)($order['cancel_transaction_id'] ?? 0) > 0) {
        return [false, 'Заказ отменён'];
    }
    if ($vkUserId === '' || !ctype_digit($vkUserId)
        || (string)($order['user_id'] ?? '') !== $vkUserId) {
        return [false, 'Заказ принадлежит другому пользователю'];
    }
    $item = (string)($order['item'] ?? '');
    if ($item === '' || !hash_equals((string)$expected['item'], $item)) {
        return [false, 'Товар заказа не совпал'];
    }
    if (!isset($order['amount']) || !is_numeric($order['amount'])
        || (int)$order['amount'] !== (int)$expected['price']) {
        return [false, 'Сумма заказа не совпала'];
    }
    return [true, $order];
}

function dz_orders_init(PDO $db): void {
    $db->exec("CREATE TABLE IF NOT EXISTS orders (
        order_id TEXT PRIMARY KEY,
        user_id INTEGER,
        pack INTEGER,
        coins INTEGER,
        created_at TEXT
    )");
}
