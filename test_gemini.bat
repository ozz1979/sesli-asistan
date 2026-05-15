@echo off
chcp 65001 >nul
title ATLAS — Gemini Bağlantı Testi
cd /d "%~dp0"

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe test_gemini.py
) else (
    python test_gemini.py
)

pause
