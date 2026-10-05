@echo off
title MemoBot - Ripristina Versione Precedente
color 0E

echo ===================================================
echo        RIPRISTINO PUNTO DI SALVATAGGIO MEMOBOT
echo ===================================================
echo.
echo Punti di ripristino Git disponibili:
echo ---------------------------------------------------
git tag -l "checkpoint*"
echo ---------------------------------------------------
echo.
echo Scrivi il nome esatto del checkpoint da ripristinare
echo (es. checkpoint-v1.0-baseline) oppure premi INVIO per uscire:
set /p CP_TAG="Nome checkpoint: "

if "%CP_TAG%"=="" (
    echo Annullato. Nessuna modifica effettuata.
    pause
    exit /b
)

echo.
echo Ripristino in corso verso: %CP_TAG%...
git checkout %CP_TAG% -- .

echo.
echo ===================================================
echo   [OK] File ripristinati con successo al checkpoint: %CP_TAG%
echo ===================================================
echo.
pause
