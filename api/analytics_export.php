<?php
// Drop Zone Royal Battle — АНАЛИТИКА: CSV-экспорт для владельца.
// GET ?key=СЕКРЕТ&day=YYYY-MM-DD -> CSV (id,user_id,event,json,at). Без day — последние 5000.

header('Content-Type: text/csv; charset=utf-8');

$DZ_CFG = [];
if (file_exists(__DIR__ . '/config.php')) {
    $tmp = include __DIR__ . '/config.php';
    if (is_array($tmp)) $DZ_CFG = $tmp;
}
$KEY = $DZ_CFG['analytics_key'] ?? 'dz_analytics_2026';
if (($_GET['key'] ?? '') !== $KEY) {
    http_response_code(403);
    echo "forbidden";
    exit;
}

try {
    $db = new PDO('sqlite:' . __DIR__ . '/data.sqlite');
    $db->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $day = (string)($_GET['day'] ?? '');
    if (preg_match('/^\d{4}-\d{2}-\d{2}$/', $day)) {
        $st = $db->prepare("SELECT id, user_id, event, json, at FROM events WHERE at LIKE ? ORDER BY id ASC");
        $st->execute([$day . '%']);
    } else {
        $st = $db->query("SELECT id, user_id, event, json, at FROM events ORDER BY id DESC LIMIT 5000");
    }
    $out = fopen('php://output', 'w');
    fputcsv($out, ['id', 'user_id', 'event', 'json', 'at'], ';');
    while ($row = $st->fetch(PDO::FETCH_ASSOC)) {
        fputcsv($out, [$row['id'], $row['user_id'], $row['event'], $row['json'], $row['at']], ';');
    }
    fclose($out);
} catch (Exception $e) {
    http_response_code(500);
    echo "export error";
}
