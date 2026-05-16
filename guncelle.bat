@echo off
chcp 65001 >nul
cd /d C:\Users\LENOVO\Desktop\atlas-v8.2\sesli-asistan

echo.
echo ========================================
echo   ATLAS GUNCELLEME BASLADI
echo ========================================
echo.

echo [1/2] Dosyalar guncelleniyor...
venv\Scripts\python.exe -c "import urllib.request as u; dosyalar=['bilgisayar_kontrol.py','kalip_motoru.py','main.py','karar_merkezi.py','hafiza_sistemi.py','bilgisayar_tarama.py','ogrenme_motoru.py','bilgi_bankasi.py','ses_algilama.py','turkce.py','dikkat_filtresi.py']; [open(f,'wb').write(u.urlopen('https://raw.githubusercontent.com/ozz1979/sesli-asistan/main/'+f).read()) for f in dosyalar]; print(str(len(dosyalar))+' DOSYA GUNCELLENDI')"

echo.
echo [2/2] Baslangic kisayolu duzeltiliyor...
venv\Scripts\python.exe -c "import os;q=chr(34);p=os.path.join(os.environ['APPDATA'],'Microsoft','Windows','Start Menu','Programs','Startup','SesliAsistan.vbs');open(p,'w').write('Set WshShell = CreateObject('+q+'WScript.Shell'+q+')\r\nWshShell.CurrentDirectory = '+q+'C:\\Users\\LENOVO\\Desktop\\atlas-v8.2\\sesli-asistan'+q+'\r\nWshShell.Run '+q+'baslat.bat'+q+', 1, False\r\n');print('VBS DUZELTILDI')"

echo.
echo ========================================
echo   TAMAMLANDI!
echo ========================================
echo.
pause
