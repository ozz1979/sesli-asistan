@echo off
echo ========================================
echo   ATLAS - Otomatik Baslatma Kurulumu
echo ========================================
echo.

set "ATLAS_DIR=%~dp0"
set "VBS_FILE=%ATLAS_DIR%atlas_baslat.vbs"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

echo [1/3] Eski dosyalar temizleniyor...
if exist "%STARTUP%\atlas_startup.vbs" del "%STARTUP%\atlas_startup.vbs"
if exist "%STARTUP%\SesliAsistan.vbs" del "%STARTUP%\SesliAsistan.vbs"
if exist "%STARTUP%\ATLAS.lnk" del "%STARTUP%\ATLAS.lnk"
if exist "%STARTUP%\atlas_baslat.vbs" del "%STARTUP%\atlas_baslat.vbs"
echo     Eski dosyalar temizlendi.

echo [2/3] VBS dosyasi kopyalaniyor...
copy /Y "%VBS_FILE%" "%STARTUP%\atlas_baslat.vbs" >nul

if exist "%STARTUP%\atlas_baslat.vbs" (
    echo [3/3] Basarili!
    echo.
    echo     Bilgisayar acildiginda ATLAS arka planda calisacak.
    echo     "Atlas" dediginizde kendini gosterecek.
) else (
    echo [HATA] Dosya kopyalanamadi!
)

echo.
echo ========================================
echo Kaldirmak icin: startup_kaldir.bat
echo ========================================
pause
