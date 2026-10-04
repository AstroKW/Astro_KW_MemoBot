@echo off
chcp 65001 >nul
title Autorizzazione Google Calendar - Astro_KW MemoBot
echo ===================================================
echo   Astro_KW MemoBot - Collegamento Google Calendar
echo ===================================================
echo.
cd /d "%~dp0"
if exist "D:\anaconda3\Scripts\activate.bat" (
    call "D:\anaconda3\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)
python setup_google_calendar.py
echo.
pause
