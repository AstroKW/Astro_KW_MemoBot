@echo off
chcp 65001 >nul
title Astro_KW MemoBot
color 0A

echo ===================================================
echo             AVVIO DI ASTRO_KW MEMOBOT
echo ===================================================
echo.

:: Spostamento automatico nella cartella del progetto
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

echo Avvio della Dashboard Streamlit...
python -m streamlit run app.py

pause