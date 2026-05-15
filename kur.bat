@echo off
echo ==========================================
echo   SESLI AI ASISTAN v6.0 - KURULUM
echo   3 Katmanli Akilli Mimari
echo ==========================================
echo.

echo [1/5] Python kontrol ediliyor...
python --version
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo Python yukleyin: https://www.python.org/downloads/
    echo ONEMLI: Kurulumda "Add to PATH" secenegini isaretleyin!
    pause
    exit /b 1
)
echo [OK] Python bulundu!

echo.
echo [2/5] Eski venv siliniyor (temiz kurulum)...
if exist "venv" (
    rmdir /s /q venv
    echo [OK] Eski venv silindi!
)

echo.
echo [3/5] Sanal ortam olusturuluyor...
python -m venv venv
if errorlevel 1 (
    echo [HATA] Sanal ortam olusturulamadi!
    pause
    exit /b 1
)
echo [OK] Sanal ortam olusturuldu!

echo.
echo [4/5] Kutuphaneler tek tek yukleniyor...
echo.

echo --- numpy ---
venv\Scripts\pip.exe install numpy
echo.

echo --- sounddevice ---
venv\Scripts\pip.exe install sounddevice
echo.

echo --- scipy ---
venv\Scripts\pip.exe install scipy
echo.

echo --- SpeechRecognition ---
venv\Scripts\pip.exe install SpeechRecognition
echo.

echo --- edge-tts ---
venv\Scripts\pip.exe install edge-tts
echo.

echo --- pygame-ce (Python 3.14 uyumlu) ---
venv\Scripts\pip.exe install pygame-ce
echo.

echo --- PyQt6 ---
venv\Scripts\pip.exe install PyQt6
echo.

echo --- requests ---
venv\Scripts\pip.exe install requests
echo.

echo --- pyautogui ---
venv\Scripts\pip.exe install pyautogui
echo.

echo --- pyttsx3 ---
venv\Scripts\pip.exe install pyttsx3
echo.

echo ==========================================
echo [5/5] KONTROL
echo ==========================================
venv\Scripts\python.exe -c "import numpy; print('[OK] numpy')"
venv\Scripts\python.exe -c "import sounddevice; print('[OK] sounddevice')"
venv\Scripts\python.exe -c "import scipy; print('[OK] scipy')"
venv\Scripts\python.exe -c "import speech_recognition; print('[OK] SpeechRecognition')"
venv\Scripts\python.exe -c "import edge_tts; print('[OK] edge-tts')"
venv\Scripts\python.exe -c "import pygame; print('[OK] pygame-ce')"
venv\Scripts\python.exe -c "import PyQt6; print('[OK] PyQt6')"
venv\Scripts\python.exe -c "import pyttsx3; print('[OK] pyttsx3')"

echo.
echo ==========================================
echo   KURULUM TAMAMLANDI!
echo ==========================================
echo.
echo ONEMLI: config.json dosyasina Gemini API anahtarinizi yazin!
echo Ucretsiz anahtar: https://aistudio.google.com/apikey
echo.
echo Baslatmak icin: baslat.bat
echo.
pause
