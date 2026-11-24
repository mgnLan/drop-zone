<?php
// Запуск: php tools/test_payments.php
// Реальные config.php, data.sqlite и HTTP VK не используются.

require_once __DIR__ . '/../api/payment_common.php';

$failures = [];
$count = 0;
function check_case($condition, $name) {
    global $failures, $count;
    $count++;
    if (!$condition) $failures[] = $name;
    echo ($condition ? 'OK ' : 'FAIL ') . $name . PHP_EOL;
}

function test_order(array $patch = []): array {
    return array_merge([
        'id' => 900001,
        'status' => 'charged',
        'user_id' => 13091533,
        'item' => 'Пак 150 монет',
        'amount' => 129,
        'cancel_transaction_id' => 0,
    ], $patch);
}

$packs = dz_payment_packs();
$bp = dz_payment_bp();
$expected = [129, 549, 1199, 2299];
$coins = [150, 750, 1800, 3750];
$catalogOk = true;
$discountOk = true;
$previousUnitPrice = INF;
foreach ($packs as $i => $pack) {
    $catalogOk = $catalogOk && $pack['price'] === $expected[$i] && $pack['coins'] === $coins[$i];
    $unitPrice = $pack['price'] / $pack['coins'];
    $discountOk = $discountOk && $unitPrice < $previousUnitPrice;
    $previousUnitPrice = $unitPrice;
}
check_case($catalogOk, 'каталог: цены и монеты совпадают');
check_case($discountOk, 'каталог: цена одной монеты снижается с ростом пакета');
check_case($bp['price'] === 399 && $bp['coins'] === 0, 'Battle Pass: 399 ₽, без монет');
$firstPrices = [97, 412, 899, 1724];
foreach ($packs as $i => $pack) {
    $first = dz_payment_pack_for_user($pack, true);
    check_case($first['price'] === $firstPrices[$i] && $first['coins'] === $pack['coins'],
        'первая покупка: пак ' . $i . ' стоит ' . $firstPrices[$i] . ' ₽, объём не изменён');
    check_case(dz_payment_pack_for_user($pack, false)['price'] === $expected[$i],
        'повторная покупка: пак ' . $i . ' по полной цене');
}
$firstOrder = test_order(['amount' => 97]);
check_case(dz_vk_order_verify(['response' => [$firstOrder]], '900001', dz_payment_pack_for_user($packs[0], true), '13091533')[0],
    'оплаченный заказ со скидкой 25% принят');
check_case(!dz_vk_order_verify(['response' => [$firstOrder]], '900001', $packs[0], '13091533')[0],
    'заказ со скидкой отклонён после использования первой покупки');

$valid = ['response' => [test_order()]];
check_case(dz_vk_order_verify($valid, '900001', $packs[0], '13091533')[0], 'оплаченный заказ response[0] принят');
$legacy = ['response' => [test_order(['status' => 1])]];
check_case(dz_vk_order_verify($legacy, '900001', $packs[0], '13091533')[0], 'legacy status=1 принят');
$malformed = ['response' => test_order()];
check_case(!dz_vk_order_verify($malformed, '900001', $packs[0], '13091533')[0], 'старая неправильная форма response отклонена');

$cases = [
    'подмена дешёвого пака дорогим' => [test_order(), $packs[3], '13091533', '900001'],
    'чужой VK user_id' => [test_order(), $packs[0], '999', '900001'],
    'неверная цена' => [test_order(['amount' => 1]), $packs[0], '13091533', '900001'],
    'неверный товар' => [test_order(['item' => 'Пак 750 монет']), $packs[0], '13091533', '900001'],
    'неоплаченный статус' => [test_order(['status' => 'created']), $packs[0], '13091533', '900001'],
    'отменённый заказ' => [test_order(['cancel_transaction_id' => 123]), $packs[0], '13091533', '900001'],
    'другой номер заказа' => [test_order(['id' => 900002]), $packs[0], '13091533', '900001'],
    'монетный заказ нельзя использовать для BP' => [test_order(['amount' => 399]), $bp, '13091533', '900001'],
];
foreach ($cases as $name => $case) {
    $response = ['response' => [$case[0]]];
    check_case(!dz_vk_order_verify($response, $case[3], $case[1], $case[2])[0], $name);
}

// Повторная обработка тестового callback: только один order и одна строка wallet.
define('DZ_PAYMENT_FUNCTIONS_ONLY', true);
require __DIR__ . '/../api/payment_vk.php';
$legacyDisabled = !isset($ITEMS['Пак 600 монет'], $ITEMS['Пак 2250 монет'], $ITEMS['Пак 5100 монет'], $ITEMS['Пак 12000 монет'])
    && !isset($CREDIT_BY_ITEM['Пак 600 монет'], $CREDIT_BY_ITEM['Пак 2250 монет'], $CREDIT_BY_ITEM['Пак 5100 монет'], $CREDIT_BY_ITEM['Пак 12000 монет']);
check_case($legacyDisabled, 'устаревшие дешёвые SKU отключены');
$db = new PDO('sqlite::memory:');
$db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$db->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, vk_id TEXT)');
$db->exec("INSERT INTO users (id, vk_id) VALUES (1, '13091533')");
check_case(dz_first_purchase_available($db, 1), 'orders: новый аккаунт имеет скидку');
$quoteFirst = vk_pay_item_quote($db, 'Пак 150 монет', 13091533, $ITEMS);
check_case($quoteFirst && $quoteFirst['price'] === 97 && $quoteFirst['expiration'] === 30,
    'get_item: первая цена 97 ₽ и короткий кэш');
$params = ['order_id' => '900001', 'item' => 'Пак 150 монет', 'user_id' => 13091533];
vk_pay_credit_test($db, $params, $CREDIT_BY_ITEM);
check_case(!dz_first_purchase_available($db, 1), 'orders: монетный заказ расходует скидку');
$quoteRepeat = vk_pay_item_quote($db, 'Пак 150 монет', 13091533, $ITEMS);
check_case($quoteRepeat && $quoteRepeat['price'] === 129, 'get_item: повторная цена 129 ₽');
vk_pay_credit_test($db, $params, $CREDIT_BY_ITEM);
check_case((int)$db->query('SELECT COUNT(*) FROM orders')->fetchColumn() === 1, 'повтор callback: один заказ');
check_case((int)$db->query("SELECT COUNT(*) FROM wallet WHERE kind = 'coins'")->fetchColumn() === 1, 'повтор callback: одно начисление');
check_case((int)$db->query("SELECT SUM(amount) FROM wallet WHERE kind = 'coins'")->fetchColumn() === 150, 'повтор callback: ровно 150 монет');

$pack750Params = ['order_id' => '900003', 'item' => 'Пак 750 монет', 'user_id' => 13091533];
vk_pay_credit_test($db, $pack750Params, $CREDIT_BY_ITEM);
$st = $db->prepare('SELECT pack, coins FROM orders WHERE order_id = ?');
$st->execute(['900003']);
$pack750Order = $st->fetch(PDO::FETCH_ASSOC);
check_case($pack750Order && (int)$pack750Order['pack'] === 1 && (int)$pack750Order['coins'] === 750,
    'пак 750: в заказе сохраняются индекс 1 и 750 монет');

$bpParams = ['order_id' => '900002', 'item' => $BP_ITEM_NAME, 'user_id' => 13091533];
vk_pay_credit_test($db, $bpParams, $CREDIT_BY_ITEM);
check_case((int)$db->query("SELECT SUM(amount) FROM wallet WHERE kind = 'bp'")->fetchColumn() === 1, 'BP: одна активация через wallet');

// Модель гонки: оба запроса получили discounted snapshot, первый записал заказ;
// повторная проверка того же ответа VK против expectedNow обязана упасть.
$raceDb = new PDO('sqlite::memory:');
$raceDb->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$raceDb->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, vk_id TEXT)');
$raceDb->exec("INSERT INTO users (id, vk_id) VALUES (1, '13091533'), (2, '999')");
dz_orders_init($raceDb);
$expectedSnapshot = dz_payment_pack_for_user($packs[0], dz_first_purchase_available($raceDb, 1));
$raceResponse = ['response' => [test_order(['amount' => 97])]];
check_case(dz_vk_order_verify($raceResponse, '900001', $expectedSnapshot, '13091533')[0], 'гонка: первый snapshot допускает скидку');
$raceDb->exec("INSERT INTO orders (order_id, user_id, pack, coins, created_at) VALUES ('900000', 1, 0, 150, datetime('now'))");
$expectedNow = dz_payment_pack_for_user($packs[0], dz_first_purchase_available($raceDb, 1));
check_case(!dz_vk_order_verify($raceResponse, '900001', $expectedNow, '13091533')[0], 'гонка: второй discounted-заказ отклонён под lock');
check_case(dz_first_purchase_available($raceDb, 2), 'скидка проверяется отдельно для каждого аккаунта');
$bpOnlyDb = new PDO('sqlite::memory:');
$bpOnlyDb->exec('CREATE TABLE users (id INTEGER PRIMARY KEY, vk_id TEXT)');
dz_orders_init($bpOnlyDb);
$bpOnlyDb->exec("INSERT INTO orders (order_id, user_id, pack, coins, created_at) VALUES ('b1', 1, -1, 0, datetime('now'))");
check_case(dz_first_purchase_available($bpOnlyDb, 1), 'BP не расходует скидку первой монетной покупки');

echo 'PAYMENT_TEST ' . ($failures ? 'FAIL' : 'SAVED') . ' — ' . ($count - count($failures)) . '/' . $count . PHP_EOL;
exit($failures ? 1 : 0);
