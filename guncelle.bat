@echo off
chcp 65001 >nul
cd /d C:\Users\LENOVO\Desktop\atlas-v8.2\sesli-asistan

echo.
echo ========================================
echo   ATLAS GUNCELLEME BASLADI
echo ========================================
echo.

venv\Scripts\python.exe -c "import urllib.request as u; dosyalar=['bilgisayar_kontrol.py','kalip_motoru.py','main.py','karar_merkezi.py','hafiza_sistemi.py','bilgisayar_tarama.py']; [open(f,'wb').write(u.urlopen('https://raw.githubusercontent.com/ozz1979/sesli-asistan/main/'+f).read()) for f in dosyalar]; print(str(len(dosyalar))+' DOSYA GUNCELLENDI')"

echo.
echo ========================================
echo   GUNCELLEME TAMAMLANDI
echo ========================================
echo.
pause
