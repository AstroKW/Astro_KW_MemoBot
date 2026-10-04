@echo off
title Astro_KW MemoBot
color 0A

echo ===================================================
echo             AVVIO DI ASTRO_KW MEMOBOT
echo ===================================================
echo.

:: Spostamento automatico nella cartella del progetto
cd /d "%~dp0"

:: Rilevamento dell'ambiente Python/Anaconda
if exist "D:\anaconda3\Scripts\activate.bat" (
    call "D:\anaconda3\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

echo Avvio della Dashboard Streamlit...
python -m streamlit run app.py

pause