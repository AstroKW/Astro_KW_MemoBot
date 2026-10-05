@echo off
title Spegni MemoBot
color 0C

echo ===================================================
echo             ARRESTO DI MEMOBOT IN CORSO
echo ===================================================
echo.

echo Chiusura di Streamlit e dei processi di sincronizzazione...
taskkill /F /IM streamlit.exe /T 2>nul
taskkill /FI "WINDOWTITLE eq MemoBot - Sincronizzazione e Dashboard*" /F /T 2>nul

echo.
echo ===================================================
echo   ✅ MemoBot e Dashboard arrestati con successo!
echo ===================================================
echo.
timeout /t 3