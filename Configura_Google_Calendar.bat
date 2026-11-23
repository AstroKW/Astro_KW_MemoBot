@echo off
chcp 65001 >nul
title Autorizzazione Google Calendar - Astro_KW MemoBot
echo ===================================================
echo   Astro_KW MemoBot - Collegamento Google Calendar
echo ===================================================
echo.
cd /d "%~dp0"

:: Rilevamento dell'ambiente Python (venv locale, Anaconda, Miniconda o Python di sistema)
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
) else if exist "D:\anaconda3\Scripts\activate.bat" (
    call "D:\anaconda3\Scripts\activate.bat"
) else if exist "%USERPROFILE%\anaconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat"
) else if exist "C:\anaconda3\Scripts\activate.bat" (
    call "C:\anaconda3\Scripts\activate.bat"
) else if exist "%USERPROFILE%\miniconda3\Scripts\activate.bat" (
    call "%USERPROFILE%\miniconda3\Scripts\activate.bat"
)

where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [ERRORE] Python non trovato! Assicurati che Python sia installato e nel PATH.
    echo.
    pause
    exit /b 1
)

python setup_google_calendar.py
echo.
pause
