@echo off
chcp 65001 >nul 2>&1
title ATLAS v8.0
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo HATA: Sanal ortam bulunamadi! Once kur.bat calistirin.
    pause
    exit /b 1
)

venv\Scripts\python.exe main.py
if errorlevel 1 (
    echo.
    echo ATLAS beklenmedik bir hata ile kapandi.
    pause
)
