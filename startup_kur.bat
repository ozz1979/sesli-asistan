@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════
echo   ATLAS - Otomatik Başlatma Kurulumu
echo ═══════════════════════════════════════════
echo.

set "ATLAS_DIR=%~dp0"
set "VBS_FILE=%ATLAS_DIR%atlas_baslat.vbs"
set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT=%STARTUP%\ATLAS.lnk"

echo [1/2] Kısayol oluşturuluyor...

:: PowerShell ile kısayol oluştur
powershell -Command "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut('%SHORTCUT%'); $s.TargetPath = '%VBS_FILE%'; $s.WorkingDirectory = '%ATLAS_DIR%'; $s.Description = 'ATLAS Sesli Asistan'; $s.Save()"

if exist "%SHORTCUT%" (
    echo [2/2] Basarili! ATLAS otomatik baslatmaya eklendi.
    echo.
    echo Konum: %SHORTCUT%
    echo.
    echo Bilgisayar acildiginda ATLAS arka planda calisacak.
    echo "Atlas" dediginizde kendini gosterecek.
) else (
    echo [HATA] Kisayol olusturulamadi!
)

echo.
echo ═══════════════════════════════════════════
echo Kaldirmak icin: startup_kaldir.bat
echo ═══════════════════════════════════════════
pause
