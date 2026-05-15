@echo off
chcp 65001 >nul 2>&1
title Sesli AI Asistan v7.0 - Kurulum

echo ================================================
echo    SESLI AI ASISTAN v7.0 - KURULUM
echo    Kullanici Tanima + Derin Hata Analizi
echo ================================================
echo.

:: Python kontrol
echo [1/7] Python kontrol ediliyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo [HATA] Python bulunamadi!
    echo Python 3.10+ yukleyin: https://www.python.org/downloads/
    echo ONEMLI: Kurulumda "Add Python to PATH" secin!
    pause
    exit /b
)
python --version
echo [OK] Python bulundu!
echo.

:: Sanal ortam
echo [2/7] Sanal ortam olusturuluyor...
if not exist "venv" (
    python -m venv venv
    echo [OK] Sanal ortam olusturuldu!
) else (
    echo [OK] Sanal ortam zaten var.
)
echo.

:: pip guncelle
echo [3/7] pip guncelleniyor...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet
echo.

:: Paketler
echo [4/7] Gerekli paketler yukleniyor...
echo    (Her paket ayri yuklenir - hata olursa devam eder)
echo.

echo    numpy yukleniyor...
venv\Scripts\pip.exe install numpy --quiet 2>nul
echo    sounddevice yukleniyor...
venv\Scripts\pip.exe install sounddevice --quiet 2>nul
echo    scipy yukleniyor...
venv\Scripts\pip.exe install scipy --quiet 2>nul
echo    SpeechRecognition yukleniyor...
venv\Scripts\pip.exe install SpeechRecognition --quiet 2>nul
echo    PyQt6 yukleniyor...
venv\Scripts\pip.exe install PyQt6 --quiet 2>nul
echo    requests yukleniyor...
venv\Scripts\pip.exe install requests --quiet 2>nul
echo    edge-tts yukleniyor...
venv\Scripts\pip.exe install edge-tts --quiet 2>nul
echo    pyttsx3 yukleniyor...
venv\Scripts\pip.exe install pyttsx3 --quiet 2>nul
echo    pyautogui yukleniyor...
venv\Scripts\pip.exe install pyautogui --quiet 2>nul
echo    pyperclip yukleniyor...
venv\Scripts\pip.exe install pyperclip --quiet 2>nul
echo    psutil yukleniyor...
venv\Scripts\pip.exe install psutil --quiet 2>nul
echo    pygame-ce yukleniyor...
venv\Scripts\pip.exe install pygame-ce --quiet 2>nul

echo.
echo [OK] Paketler yuklendi!
echo.

:: API Key kontrol
echo [5/7] API anahtari kontrol ediliyor...
venv\Scripts\python.exe -c "import json; c=json.load(open('config.json','r',encoding='utf-8')); k=c.get('gemini_api_key',''); print('KEY_SET' if k and k!='BURAYA_API_ANAHTARINIZI_YAZIN' else 'KEY_MISSING')" > _keycheck.tmp 2>nul
set /p KEY_STATUS=<_keycheck.tmp
del _keycheck.tmp >nul 2>&1
if "%KEY_STATUS%"=="KEY_MISSING" (
    echo [!] Gemini API anahtari ayarlanmamis!
    echo     1. https://aistudio.google.com/apikey adresine gidin
    echo     2. "Create API key" tiklayin
    echo     3. Anahtari kopyalayin
    echo.
    set /p API_KEY="API anahtarini yapiştirin: "
    if defined API_KEY (
        venv\Scripts\python.exe -c "import json; c=json.load(open('config.json','r',encoding='utf-8')); c['gemini_api_key']='%API_KEY%'; json.dump(c,open('config.json','w',encoding='utf-8'),ensure_ascii=False,indent=4)" 2>nul
        echo [OK] API anahtari kaydedildi!
    )
) else (
    echo [OK] API anahtari ayarli!
)
echo.

:: Otomatik baslatma
echo [6/7] Windows ile otomatik baslatma...
echo.
echo Bilgisayar acildiginda asistan otomatik baslasin mi?
echo (Istediginiz zaman iptal edebilirsiniz)
echo.
set /p OTO_BASLAT="Otomatik baslat? (E/H): "
if /i "%OTO_BASLAT%"=="E" (
    echo Set WshShell = CreateObject("WScript.Shell") > "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SesliAsistan.vbs"
    echo WshShell.CurrentDirectory = "%CD%" >> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SesliAsistan.vbs"
    echo WshShell.Run "baslat.bat", 0, False >> "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SesliAsistan.vbs"
    echo [OK] Otomatik baslatma ayarlandi!
    echo     Dosya: %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\SesliAsistan.vbs
    echo     Iptal: Bu dosyayi silmeniz yeterli.
) else (
    echo [OK] Otomatik baslatma atlandı.
    echo     Istediginizde tekrar kur.bat calistirarak aktif edebilirsiniz.
)
echo.

:: Baslat
echo [7/7] Kurulum tamamlandi!
echo.
echo ================================================
echo   KURULUM BASARILI! v7.0
echo   Yenilikler:
echo   - Kullanici tanima (isim sorar)
echo   - Derin baglanti analizi
echo   - 184+ yerel Turkce kalip
echo   - Otomatik guncelleme
echo ================================================
echo.
echo Asistani baslatmak icin: baslat.bat
echo.
pause
