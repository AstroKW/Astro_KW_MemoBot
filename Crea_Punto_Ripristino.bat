@echo off
title MemoBot - Crea Punto di Ripristino
color 0B

echo ===================================================
echo        CREAZIONE PUNTO DI RIPRISTINO MEMOBOT
echo ===================================================
echo.

set "TIMESTAMP=%date:~6,4%%date:~3,2%%date:~0,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "TIMESTAMP=%TIMESTAMP: =0%"
set "BACKUP_DIR=backups\checkpoint_%TIMESTAMP%"

echo 1. Creazione backup fisico in %BACKUP_DIR%...
mkdir "%BACKUP_DIR%" 2>nul
copy *.py "%BACKUP_DIR%\" >nul
copy *.bat "%BACKUP_DIR%\" >nul
copy *.txt "%BACKUP_DIR%\" >nul
copy *.db "%BACKUP_DIR%\" >nul
copy .env.example "%BACKUP_DIR%\" >nul

echo 2. Creazione snapshot Git locale...
git add .
git commit -m "checkpoint automatico: %TIMESTAMP%"
git tag "checkpoint_%TIMESTAMP%"

echo.
echo ===================================================
echo   [OK] Punto di ripristino salvato con successo!
echo   Cartella: %BACKUP_DIR%
echo   Tag Git : checkpoint_%TIMESTAMP%
echo ===================================================
echo.
pause
