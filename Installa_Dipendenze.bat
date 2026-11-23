@echo off
chcp 65001 >nul
title Astro_KW MemoBot - Installazione Dipendenze
color 0B

echo ===================================================
echo     INSTALLAZIONE DIPENDENZE DI ASTRO_KW MEMOBOT
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
    echo [ERRORE] Python non trovato nel sistema!
    echo Installa Python da https://www.python.org/ o Anaconda e assicurati di spuntare "Add to PATH".
    echo.
    pause
    exit /b 1
)

echo Installazione pacchetti da requirements.txt in corso...
pip install -r requirements.txt

echo.
echo ===================================================
echo   Installazione completata! Premi un tasto per uscire.
echo ===================================================
pause
