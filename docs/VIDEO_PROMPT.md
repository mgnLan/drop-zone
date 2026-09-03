# Промт для генерации короткого видео (тизер Drop Zone)

Подходит для: Kling, Runway Gen-3, Pika, Luma, Sora, Hailuo/MiniMax.
Рекомендуемая длина: 10–15 сек, 16:9 (для ВК-клипа) или 9:16 (для клипов/сторис — обрезать центр).

## Главный промт (EN — видео-ИИ понимают английский лучше)

```
Cinematic teaser, stylized low-poly 3D game graphics, night scene.
A futuristic TV-show battle arena viewed from a high isometric angle:
a glowing pink-and-cyan neon podium ring in the center of a dark city
block, surrounded by small buildings, crates and barriers. Slow camera
orbit around the arena, floodlights sweeping. Two soldiers in tactical
gear step out from behind cover on opposite sides of the neon ring,
raise their rifles — a bright muzzle flash lights up the scene, camera
shakes slightly. Holographic screens on the perimeter display
"DROP ZONE". Volumetric fog, neon reflections on wet asphalt,
dramatic rim lighting, shallow depth of field. Smooth slow motion at
the shot moment. Style: polished indie game render, saturated neon
palette (pink, cyan, amber), dark background, high contrast.
No text artifacts except the holographic title.
```

## Вариант покороче (если лимит символов)

```
Stylized low-poly 3D, night arena of a futuristic TV battle show.
Slow orbit around a glowing pink neon ring; two soldiers emerge from
cover, aim rifles, one bright muzzle flash, slight slow motion.
Holographic "DROP ZONE" screens, volumetric fog, neon reflections,
cinematic lighting, high contrast, 10 seconds.
```

## Русское описание сцены (для ручной сборки/монтажа или для ИИ с русским вводом)

Ночь. Изометрический вид сверху на арену телешоу будущего: в центре тёмного
квартала — ринг с розово-голубой неоновой подсветкой, вокруг невысокие дома,
ящики и барьеры-укрытия. Камера медленно облетает арену по дуге, лучи
прожекторов скользят по земле. С противоположных сторон ринга из-за укрытий
выходят двое бойцов в тактическом снаряжении, поднимают автоматы — яркая
вспышка выстрела освещает сцену, камера слегка вздрагивает, момент выстрела
в лёгком slow-motion. По периметру голографические экраны с надписью
«DROP ZONE». Объёмный туман, неоновые отражения на мокром асфальте.

## Технические советы

- Генерировать 2–3 дубля и брать лучший — вспышка выстрела у видео-ИИ
  получается нестабильно.
- Если модель поддерживает image-to-video: использовать как стартовый кадр
  `docs/slice_3d_v4.png` (реальный скриншот игры) — стиль совпадёт с игрой
  один-в-один.
- Для вертикали (клипы ВК): задать aspect 9:16 и держать ринг в центре кадра.
- Звук: наложить отдельно — глухой басовый пульс + один выстрел + эхо толпы.
