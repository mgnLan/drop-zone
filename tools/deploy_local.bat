@echo off
chcp 65001 >nul
rem Drop Zone: сборка web-билда и выкладка на dropzone.local (OSPanel)
rem После первого запуска домена OSPanel нужно один раз перезапустить вручную.

set GODOT=G:\Kimi project\Drop Zone\Godot_std\Godot_v4.7.2-stable_win64_console.exe
set GAME=G:\Kimi project\Drop Zone\game
set BUILD=G:\Kimi project\Drop Zone\web_build
set SITE=C:\OSPanel\home\dropzone.local

echo === Экспорт Web-билда ===
"%GODOT%" --headless --path "%GAME%" --export-release "Web" "%BUILD%\index.html"
if errorlevel 1 (
    echo ОШИБКА экспорта!
    pause
    exit /b 1
)

echo === Копирование на dropzone.local ===
if not exist "%SITE%" mkdir "%SITE%"
xcopy "%BUILD%\*" "%SITE%\" /Y /Q >nul

echo === Готово: http://dropzone.local ===
pause
