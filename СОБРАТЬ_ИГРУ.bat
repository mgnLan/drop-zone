@echo off
chcp 65001 >nul
title Сборка Точки Сброса
echo Собираю игру...
"Godot_v4.7.2-stable_mono_win64\Godot_v4.7.2-stable_mono_win64_console.exe" --headless --path game --export-release "Web" web_build\index.html
echo.
if %errorlevel%==0 (echo ГОТОВО! Файлы для загрузки лежат в папке web_build) else (echo ОШИБКА СБОРКИ — пришли скриншот этого окна)
echo.
pause
