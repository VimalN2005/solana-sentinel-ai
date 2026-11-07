@echo off
title Solana Sentinel AI Server
echo ========================================================
echo   Starting Solana Sentinel AI - Autonomous Agent Server
echo ========================================================
echo.
cd /d "%~dp0backend"
python main.py
pause
