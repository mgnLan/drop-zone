<?php
// Drop Zone Royal Battle — ASYNC PvP: общие константы и валидация снапшотов.
// Подключается из pvp_push/pvp_match/pvp_result/pvp_top (недоступен извне напрямую).

// --- таблица оружия (зеркало data/items.json): id => [тир, урон, обойма, запас] ---
const DZ_WEAPONS = [
    'Pistol' => [1, 16, 12, 12],
    'Revolver_Small' => [1, 18, 6, 6],
    'Revolver' => [1, 24, 6, 6],
    'SMG' => [1, 12, 30, 30],
    'Shotgun' => [1, 30, 6, 6],
    'AK' => [2, 22, 10, 20],
    'Sniper' => [2, 38, 5, 5],
    'Sniper_2' => [2, 48, 3, 3],
    'GrenadeLauncher' => [2, 34, 3, 2],
    'ShortCannon' => [2, 36, 3, 2],
    'RocketLauncher' => [2, 55, 1, 1],
];
// минимальный уровень бойца для тира оружия
const DZ_WEAPON_TIER_LVL = [1 => 1, 2 => 5];
// таланты (зеркало константы TALENTS клиента): id => макс. ранг
const DZ_TALENTS = [
    'reload1' => 1, 'sapper' => 1, 'steady' => 1, 'marathon' => 1,
    'medic' => 3, 'scout' => 3, 'mule' => 3, 'lucky' => 3,
];
const DZ_STAT_KEYS = ['str', 'agi', 'end', 'per', 'int', 'lck'];

// гейт грейда брони по уровню (зеркало _armor_grade_cap клиента)
function dz_armor_grade_cap(int $lvl): int {
    if ($lvl >= 20) return 5;
    if ($lvl >= 10) return 4;
    return 3;
}

// потолок суммы статов по уровню (константа пака «ASYNC PvP»)
function dz_stat_cap(int $lvl): int {
    return 30 + 8 * $lvl;
}

// полная валидация снапшота. Возвращает [true, ''] или [false, причина].
function dz_validate_snapshot($snap): array {
    if (!is_array($snap)) return [false, 'snapshot not object'];
    $fighters = $snap['fighters'] ?? null;
    if (!is_array($fighters) || count($fighters) < 1 || count($fighters) > 4) {
        return [false, 'fighters count'];
    }
    foreach ($fighters as $f) {
        if (!is_array($f)) return [false, 'fighter not object'];
        $lvl = (int)($f['lvl'] ?? 0);
        if ($lvl < 1 || $lvl > 100) return [false, 'lvl'];
        $stats = $f['stats'] ?? null;
        if (!is_array($stats)) return [false, 'stats'];
        $sum = 0;
        foreach (DZ_STAT_KEYS as $k) {
            $v = $stats[$k] ?? 0;
            if (!is_numeric($v) || (int)$v < 0 || (int)$v > 200) return [false, "stat $k"];
            $sum += (int)$v;
        }
        if ($sum > dz_stat_cap($lvl)) return [false, "stat sum $sum > cap"];
        $w = (string)($f['weapon'] ?? '');
        if (!isset(DZ_WEAPONS[$w])) return [false, "weapon $w"];
        $tier = DZ_WEAPONS[$w][0];
        if ($lvl < DZ_WEAPON_TIER_LVL[$tier]) return [false, "weapon tier $tier at lvl $lvl"];
        $ag = (int)($f['armor_grade'] ?? 0);
        if ($ag < 0 || $ag > 5) return [false, 'armor_grade'];
        if ($ag > dz_armor_grade_cap($lvl)) return [false, 'armor_grade > cap'];
        $cls = (int)($f['cls'] ?? 0);
        if ($cls < 0 || $cls > 3) return [false, 'cls'];
        $talents = $f['talents'] ?? [];
        if (!is_array($talents)) return [false, 'talents'];
        $ranks = 0;
        foreach ($talents as $tid => $rank) {
            if (!isset(DZ_TALENTS[$tid])) return [false, "talent $tid"];
            $r = (int)$rank;
            if ($r < 1 || $r > DZ_TALENTS[$tid]) return [false, "talent $tid rank"];
            $ranks += $r;
        }
        if ($ranks > 1 + intdiv($lvl, 4)) return [false, 'talent ranks'];
        $nm = (string)($f['name'] ?? '');
        if (mb_strlen($nm) > 32) return [false, 'name len'];
    }
    return [true, ''];
}

// теоретический потолок урона за бой: обоймы×урон оружия снапшота×ходы (с запасом на криты ×1.6)
function dz_dmg_cap(array $snap, int $turns): int {
    $arsenal = 0;
    foreach (($snap['fighters'] ?? []) as $f) {
        $w = (string)($f['weapon'] ?? '');
        if (isset(DZ_WEAPONS[$w])) {
            $arsenal += DZ_WEAPONS[$w][1] * (DZ_WEAPONS[$w][2] + DZ_WEAPONS[$w][3]);
        }
    }
    return (int)ceil($arsenal * max(1, $turns) * 1.6);
}

// генерация серверного претендента (пустой пул): отряд под уровень и размер
function dz_make_pretender(int $size, int $squad_lvl): array {
    $fighters = [];
    $names_a = ['Шакал', 'Гюрза', 'Каспий', 'Буран', 'Стервятник', 'Тайфун'];
    $w_low = ['Pistol', 'Revolver_Small', 'Revolver', 'SMG', 'Shotgun'];
    $w_high = ['AK', 'Sniper', 'Shotgun', 'SMG', 'GrenadeLauncher'];
    for ($i = 0; $i < $size; $i++) {
        $lvl = max(1, min(100, $squad_lvl + ($i === 0 ? 0 : rand(-1, 1))));
        $points = 5 + 5 * min($lvl - 1, 4) + 3 * max(0, $lvl - 5);
        $end = (int)round($points * 0.4);
        $str = (int)round($points * 0.25);
        $agi = (int)round($points * 0.2);
        $per = (int)floor(($points - $end - $str - $agi) / 2);
        $lck = max(0, $points - $end - $str - $agi - $per);
        $stats = ['str' => $str, 'agi' => $agi, 'end' => $end, 'per' => $per, 'int' => 0, 'lck' => $lck];
        $talents = [];
        if ($lvl >= 6) {
            $pick = ['medic', 'scout', 'mule'][rand(0, 2)];
            $talents = [$pick => 1];
        }
        $fighters[] = [
            'name' => $names_a[array_rand($names_a)],
            'cls' => rand(0, 3),
            'lvl' => $lvl,
            'stats' => $stats,
            'talents' => $talents,
            'weapon' => $lvl >= 5 ? $w_high[array_rand($w_high)] : $w_low[array_rand($w_low)],
            'armor_grade' => min(dz_armor_grade_cap($lvl), max(1, 1 + intdiv($lvl, 6))),
        ];
    }
    return $fighters;
}
