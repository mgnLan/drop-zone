DROP ZONE — 3D вертикальный срез (тест визуала)
================================================

Что это:
  Тестовая 3D-сцена ночной арены для игры Drop Zone.
  Модели: Quaternius (лицензия CC0, бесплатно для любого использования):
    - Animated Mech Pack (мехи George и Mike, с анимациями: Idle, Walk, Run, Shoot, Death и др.)
    - Cyberpunk Game Kit (платформы, знаки, экраны, антенны, пропсы)

Как открыть:
  1. Установите Godot 4.7 (https://godotengine.org/download) — обычная или mono-версия.
  2. В менеджере проектов: «Импорт» → выберите файл game/project.godot из этого архива.
  3. При первом открытии Godot пересоберёт кэш импорта (1-2 минуты).
  4. Нажмите F5 (запуск) — откроется сцена арены (scenes/arena3d.tscn).
  5. Старая 2D-версия на тайлах Kenney осталась в scenes/main.tscn.

Скриншоты (папка docs/):
  slice_3d_v1.png — 3D версия (текущая)
  slice_v1.png    — старая 2D версия для сравнения

Структура:
  game/project.godot        — проект Godot
  game/scenes/arena3d.tscn  — 3D арена (главная сцена)
  game/scripts/arena3d.gd   — код сцены (вся арена собирается из кода)
  game/assets/models/       — мехи (.gltf, с анимациями)
  game/assets/models/cyberpunk/ — структуры киберпанк-кита
  game/assets/tiles/        — 2D тайлы Kenney (старая версия)

Дата: 2026-08-26
