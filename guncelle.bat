@echo off
cd /d C:\Users\LENOVO\Desktop\atlas-v8.2\sesli-asistan

echo.
echo ========================================
echo   ATLAS GUNCELLEME BASLADI
echo ========================================
echo.

echo [1/2] Dosyalar guncelleniyor...
venv\Scripts\python.exe -c "import urllib.request as u; import time; t=str(int(time.time())); dosyalar=['bilgisayar_kontrol.py','kalip_motoru.py','main.py','karar_merkezi.py','hafiza_sistemi.py','bilgisayar_tarama.py','ogrenme_motoru.py','bilgi_bankasi.py','ses_algilama.py','turkce.py','dikkat_filtresi.py','arayuz.py','kimlik_tanima.py','konusma_uretimi.py','dil_anlama.py','oto_guncelleme.py','atlas_baslat.vbs','startup_kur.bat','startup_kaldir.bat','guncelle.bat']; [open(f,'wb').write(u.urlopen(u.Request('https://raw.githubusercontent.com/ozz1979/sesli-asistan/main/'+f+'?v='+t,headers={'Cache-Control':'no-cache'})).read()) for f in dosyalar]; print(str(len(dosyalar))+' DOSYA GUNCELLENDI')"

echo.
echo [2/2] Tamamlandi!

echo.
echo ========================================
echo   TAMAMLANDI!
echo ========================================
echo.
echo Otomatik baslatma icin: startup_kur.bat
echo Kaldirmak icin: startup_kaldir.bat
echo.
pause
