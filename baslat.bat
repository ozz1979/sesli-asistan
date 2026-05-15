@echo off
echo SESLI AI ASISTAN v6.0 baslatiliyor...
echo.
if not exist "venv\Scripts\python.exe" (
    echo [HATA] Once kur.bat calistirin!
    pause
    exit /b 1
)
venv\Scripts\python.exe main.py
pause
