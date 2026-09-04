@echo off
rem Тестовый бой со скриншотом (как у Кими): сохраняет docs\test_play.png
cd /d "G:\Kimi project\Drop Zone"
"Godot_std\Godot_v4.7.2-stable_win64_console.exe" --path game -- --testplay --seed 555
pause
