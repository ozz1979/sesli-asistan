@echo off
chcp 65001 >nul 2>&1
title Sesli AI Asistan v7.0
cd /d "%~dp0"
if not exist "venv\Scripts\python.exe" (
    echo [HATA] Sanal ortam bulunamadi! Once kur.bat calistirin.
    pause
    exit /b
)
venv\Scripts\python.exe main.py %*
