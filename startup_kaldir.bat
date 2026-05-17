@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════
echo   ATLAS - Otomatik Başlatma Kaldırma
echo ═══════════════════════════════════════════
echo.

set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ATLAS.lnk"

if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo Basarili! ATLAS otomatik baslatmadan kaldirildi.
) else (
    echo ATLAS zaten otomatik baslatmada degil.
)

echo.
pause
