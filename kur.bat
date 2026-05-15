@echo off
chcp 65001 >nul 2>&1
title ATLAS v8.2 - Kurulum
color 0B

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║       ATLAS v8.2 - JARVIS Beyin Mimarisi         ║
echo  ║       Sesli AI Asistan Kurulumu                   ║
echo  ╚══════════════════════════════════════════════════╝
echo.

:: Python kontrolü
echo [1/6] Python kontrol ediliyor...
python --version >nul 2>&1
if errorlevel 1 (
    echo HATA: Python bulunamadi! python.org adresinden Python yukleyin.
    pause
    exit /b 1
)
python --version
echo.

:: Sanal ortam
echo [2/6] Sanal ortam olusturuluyor...
if not exist "venv" (
    python -m venv venv
    echo Sanal ortam olusturuldu.
) else (
    echo Sanal ortam mevcut.
)
echo.

:: Paketler
echo [3/6] Paketler yukleniyor (bu biraz surebilir)...
echo.

venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1

echo   Eski Gemini paketi kaldirilıyor...
venv\Scripts\python.exe -m pip uninstall google-generativeai -y >nul 2>&1

echo   PyQt6 yukleniyor...
venv\Scripts\python.exe -m pip install PyQt6>=6.6.0 >nul 2>&1
if errorlevel 1 echo   UYARI: PyQt6 yuklenemedi!

echo   SpeechRecognition yukleniyor...
venv\Scripts\python.exe -m pip install SpeechRecognition>=3.10.0 >nul 2>&1
if errorlevel 1 echo   UYARI: SpeechRecognition yuklenemedi!

echo   sounddevice yukleniyor...
venv\Scripts\python.exe -m pip install sounddevice>=0.4.6 >nul 2>&1
if errorlevel 1 echo   UYARI: sounddevice yuklenemedi!

echo   edge-tts yukleniyor...
venv\Scripts\python.exe -m pip install edge-tts>=6.1.0 >nul 2>&1
if errorlevel 1 echo   UYARI: edge-tts yuklenemedi!

echo   pygame-ce yukleniyor...
venv\Scripts\python.exe -m pip install pygame-ce>=2.4.0 >nul 2>&1
if errorlevel 1 echo   UYARI: pygame-ce yuklenemedi!

echo   google-genai (YENI SDK) yukleniyor...
venv\Scripts\python.exe -m pip install google-genai>=1.0.0 >nul 2>&1
if errorlevel 1 echo   UYARI: google-genai yuklenemedi!

echo   numpy yukleniyor...
venv\Scripts\python.exe -m pip install numpy>=1.26.0 >nul 2>&1
if errorlevel 1 echo   UYARI: numpy yuklenemedi!

echo   scipy yukleniyor...
venv\Scripts\python.exe -m pip install scipy>=1.12.0 >nul 2>&1
if errorlevel 1 echo   UYARI: scipy yuklenemedi!

echo   requests yukleniyor...
venv\Scripts\python.exe -m pip install requests>=2.31.0 >nul 2>&1
if errorlevel 1 echo   UYARI: requests yuklenemedi!

echo   aiohttp yukleniyor...
venv\Scripts\python.exe -m pip install aiohttp>=3.9.0 >nul 2>&1
if errorlevel 1 echo   UYARI: aiohttp yuklenemedi!

echo.
echo   Tum paketler yuklendi!
echo.

:: Hafıza dizini
echo [4/6] Hafiza dizini olusturuluyor...
if not exist "hafiza" mkdir hafiza
if not exist "ses_cache" mkdir ses_cache
echo   Dizinler hazir.
echo.

:: Masaüstü kısayolu
echo [5/6] Masaustu kisayolu olusturuluyor...
echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\atlas_kisayol.vbs"
echo Set Shortcut = WshShell.CreateShortcut(WshShell.SpecialFolders("Desktop") ^& "\ATLAS.lnk") >> "%TEMP%\atlas_kisayol.vbs"
echo Shortcut.TargetPath = "%CD%\baslat.bat" >> "%TEMP%\atlas_kisayol.vbs"
echo Shortcut.WorkingDirectory = "%CD%" >> "%TEMP%\atlas_kisayol.vbs"
echo Shortcut.Description = "ATLAS Sesli AI Asistan" >> "%TEMP%\atlas_kisayol.vbs"
echo Shortcut.IconLocation = "%CD%\atlas_logo.ico" >> "%TEMP%\atlas_kisayol.vbs"
echo Shortcut.Save >> "%TEMP%\atlas_kisayol.vbs"
cscript //nologo "%TEMP%\atlas_kisayol.vbs" >nul 2>&1
del "%TEMP%\atlas_kisayol.vbs" >nul 2>&1
echo   Masaustune ATLAS kisayolu eklendi!
echo.

:: Windows başlangıcına ekleme
echo [6/6] Windows baslangicina eklemek ister misiniz?
set /p baslangic="  Bilgisayar acildiginda otomatik baslasin mi? (E/H): "
if /i "%baslangic%"=="E" (
    echo Set WshShell = CreateObject("WScript.Shell") > "%TEMP%\atlas_startup.vbs"
    echo WshShell.Run """%CD%\baslat.bat""", 0, False >> "%TEMP%\atlas_startup.vbs"
    copy "%TEMP%\atlas_startup.vbs" "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\atlas_startup.vbs" >nul 2>&1
    del "%TEMP%\atlas_startup.vbs" >nul 2>&1
    echo   ATLAS Windows baslangicina eklendi!
) else (
    echo   Atlandi.
)

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║            KURULUM TAMAMLANDI!                    ║
echo  ║                                                   ║
echo  ║  Baslatmak icin: Masaustundeki ATLAS ikonuna      ║
echo  ║  veya baslat.bat dosyasina tiklayin.               ║
echo  ║                                                   ║
echo  ║  ONEMLI: config.json dosyasina                     ║
echo  ║  Gemini API anahtarinizi yazmayi unutmayin!        ║
echo  ╚══════════════════════════════════════════════════╝
echo.
pause
