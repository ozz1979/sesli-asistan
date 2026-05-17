@echo off
chcp 65001 >nul
echo ═══════════════════════════════════════════
echo   ATLAS - Otomatik Baslatma Kaldirma
echo ═══════════════════════════════════════════
echo.

set "STARTUP=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"

if exist "%STARTUP%\atlas_baslat.vbs" del "%STARTUP%\atlas_baslat.vbs"
if exist "%STARTUP%\atlas_startup.vbs" del "%STARTUP%\atlas_startup.vbs"
if exist "%STARTUP%\SesliAsistan.vbs" del "%STARTUP%\SesliAsistan.vbs"
if exist "%STARTUP%\ATLAS.lnk" del "%STARTUP%\ATLAS.lnk"

echo Basarili! ATLAS otomatik baslatmadan kaldirildi.
echo.
pause
