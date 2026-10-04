@echo off
title Astro_KW MemoBot - Installazione Dipendenze
color 0B

echo ===================================================
echo     INSTALLAZIONE DIPENDENZE DI ASTRO_KW MEMOBOT
echo ===================================================
echo.

cd /d "%~dp0"

:: Rilevamento dell'ambiente Python/Anaconda
if exist "D:\anaconda3\Scripts\activate.bat" (
    call "D:\anaconda3\Scripts\activate.bat"
) else if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else if exist ".venv\Scripts\activate.bat" (
    call ".venv\Scripts\activate.bat"
)

echo Installazione pacchetti da requirements.txt in corso...
pip install -r requirements.txt

echo.
echo ===================================================
echo   Installazione completata! Premi un tasto per uscire.
echo ===================================================
pause
