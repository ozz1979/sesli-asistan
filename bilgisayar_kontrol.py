"""
ATLAS - Bilgisayar Kontrol Modülü
==================================
Beyin Karşılığı: Motor Korteks
Görev: Bilgisayarda fiziksel işlemler yapmak

Yetenekler:
- Metin yazma (Türkçe destekli, clipboard üzerinden)
- Dosya/klasör açma
- Ekran görüntüsü alma
- Pencere yönetimi (küçült, büyüt, kapat)
- Web arama
- Ses kontrolü
"""

import os
import time
import subprocess
import logging

logger = logging.getLogger("ATLAS.kontrol")


def metin_yaz(text):
    """
    Aktif pencereye metin yazar.
    Türkçe karakter desteği için clipboard + Ctrl+V kullanır.
    """
    if not text or not text.strip():
        return False, "Yazılacak metin boş"

    try:
        import pyautogui
    except ImportError:
        return False, "pyautogui kurulu değil"

    try:
        # Clipboard'a kopyala (PowerShell ile - Türkçe destekli)
        # escape tırnak işaretleri
        safe_text = text.replace('"', '`"').replace("'", "`'")
        subprocess.run(
            ["powershell", "-Command", f"Set-Clipboard -Value \"{safe_text}\""],
            capture_output=True, timeout=3
        )

        # Kısa bekleme
        time.sleep(0.3)

        # Ctrl+V ile yapıştır
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)

        logger.info(f"Metin yazıldı: {text[:50]}...")
        return True, f"Yazıldı: {text[:50]}"

    except Exception as e:
        logger.error(f"Metin yazma hatası: {e}")
        return False, f"Yazma hatası: {e}"


def enter_bas():
    """Enter tuşuna basar"""
    try:
        import pyautogui
        pyautogui.press("enter")
        return True, "Enter basıldı"
    except Exception as e:
        return False, str(e)


def tus_bas(tus):
    """Belirtilen tuşa basar"""
    try:
        import pyautogui
        pyautogui.press(tus)
        return True, f"{tus} basıldı"
    except Exception as e:
        return False, str(e)


def kisayol_bas(*tuslar):
    """Kısayol tuş kombinasyonu (ör: ctrl+s)"""
    try:
        import pyautogui
        pyautogui.hotkey(*tuslar)
        return True, f"Kısayol: {'+'.join(tuslar)}"
    except Exception as e:
        return False, str(e)


def dosya_ac(dosya_yolu):
    """Dosya veya klasör açar"""
    try:
        if os.path.exists(dosya_yolu):
            os.startfile(dosya_yolu)
            logger.info(f"Dosya açıldı: {dosya_yolu}")
            return True, f"Açıldı: {dosya_yolu}"
        else:
            return False, f"Dosya bulunamadı: {dosya_yolu}"
    except Exception as e:
        logger.error(f"Dosya açma hatası: {e}")
        return False, str(e)


def klasor_ac(klasor_yolu=None):
    """Klasör açar. Yol verilmezse Belgelerim açılır."""
    if not klasor_yolu:
        klasor_yolu = os.path.expanduser("~\\Documents")
    try:
        if os.path.isdir(klasor_yolu):
            os.startfile(klasor_yolu)
            return True, f"Klasör açıldı: {klasor_yolu}"
        else:
            return False, f"Klasör bulunamadı: {klasor_yolu}"
    except Exception as e:
        return False, str(e)


def masaustu_ac():
    """Masaüstü klasörünü açar"""
    masaustu = os.path.expanduser("~\\Desktop")
    return klasor_ac(masaustu)


def belgelerim_ac():
    """Belgelerim klasörünü açar"""
    belgeler = os.path.expanduser("~\\Documents")
    return klasor_ac(belgeler)


def indirilenler_ac():
    """İndirilenler klasörünü açar"""
    ind = os.path.expanduser("~\\Downloads")
    return klasor_ac(ind)


def web_ara(sorgu):
    """Varsayılan tarayıcıda web araması yapar"""
    try:
        import urllib.parse
        url = f"https://www.google.com/search?q={urllib.parse.quote(sorgu)}"
        os.startfile(url)
        logger.info(f"Web arama: {sorgu}")
        return True, f"Aranıyor: {sorgu}"
    except Exception as e:
        return False, str(e)


def web_ac(url):
    """URL açar"""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        os.startfile(url)
        return True, f"Açılıyor: {url}"
    except Exception as e:
        return False, str(e)


def ekran_goruntusu():
    """Ekran görüntüsü alır, masaüstüne kaydeder. PowerShell kullanır (Pillow gerekmez)."""
    try:
        from datetime import datetime
        masaustu = os.path.expanduser("~\\Desktop")
        dosya = os.path.join(masaustu, f"ekran_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        dosya_ps = dosya.replace("\\", "\\\\")

        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$screen = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
$bitmap = New-Object System.Drawing.Bitmap($screen.Width, $screen.Height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen($screen.Location, [System.Drawing.Point]::Empty, $screen.Size)
$bitmap.Save("{dosya_ps}")
$graphics.Dispose()
$bitmap.Dispose()
"""
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, timeout=10
        )
        if os.path.exists(dosya):
            logger.info(f"Ekran görüntüsü: {dosya}")
            return True, "Ekran görüntüsü masaüstüne kaydedildi"
        else:
            logger.error(f"Ekran görüntüsü alınamadı: {result.stderr.decode('utf-8', errors='ignore')}")
            return False, "Ekran görüntüsü kaydedilemedi"
    except Exception as e:
        logger.error(f"Ekran görüntüsü hatası: {e}")
        return False, str(e)


def pencere_kapat():
    """Aktif pencereyi kapatır (Alt+F4)"""
    try:
        import pyautogui
        pyautogui.hotkey("alt", "F4")
        return True, "Pencere kapatıldı"
    except Exception as e:
        return False, str(e)


def pencere_kucult():
    """Aktif pencereyi küçültür"""
    try:
        import pyautogui
        pyautogui.hotkey("win", "down")
        return True, "Pencere küçültüldü"
    except Exception as e:
        return False, str(e)


def pencere_buyut():
    """Aktif pencereyi büyütür"""
    try:
        import pyautogui
        pyautogui.hotkey("win", "up")
        return True, "Pencere büyütüldü"
    except Exception as e:
        return False, str(e)


def tum_pencereleri_kucult():
    """Tüm pencereleri küçültür (Win+D)"""
    try:
        import pyautogui
        pyautogui.hotkey("win", "d")
        return True, "Masaüstü gösteriliyor"
    except Exception as e:
        return False, str(e)


def ses_ayarla(islem):
    """
    Ses kontrolü — PowerShell ve pyautogui ile.
    islem: 'ac', 'kapat', 'yukselt', 'azalt'
    """
    try:
        import pyautogui

        if islem == "yukselt":
            # 5 kere ses artır
            for _ in range(5):
                pyautogui.press("volumeup")
            return True, "Ses yükseltildi"

        elif islem == "azalt":
            # 5 kere ses azalt
            for _ in range(5):
                pyautogui.press("volumedown")
            return True, "Ses azaltıldı"

        elif islem == "kapat":
            pyautogui.press("volumemute")
            return True, "Ses kapatıldı"

        elif islem == "ac":
            pyautogui.press("volumemute")  # Mute toggle
            return True, "Ses açıldı"

        return False, f"Bilinmeyen ses işlemi: {islem}"

    except ImportError:
        return False, "pyautogui kurulu değil"
    except Exception as e:
        return False, str(e)


def tum_programlari_kapat():
    """
    Tüm açık kullanıcı pencerelerini kapatır.
    ATLAS'ı (kendi PID + python), explorer shell'i ve sistem süreçlerini KORUR.
    """
    try:
        atlas_pid = os.getpid()

        # PowerShell: Sadece kullanıcı programlarını kapat
        # 1. Kendi PID'imizi ve parent PID'imizi koru
        # 2. explorer.exe'yi asla kapatma (Windows shell çöker)
        # 3. Tüm python süreçlerini koru (ATLAS)
        # 4. Sistem süreçlerini koru
        ps_script = f"""
$atlasPid = {atlas_pid}
$sistemSurecler = @(
    'explorer','python','python3','pythonw',
    'cmd','powershell','pwsh','conhost','WindowsTerminal',
    'dwm','csrss','smss','winlogon','wininit',
    'services','lsass','lsaiso','svchost',
    'RuntimeBroker','SearchHost','SearchUI',
    'StartMenuExperienceHost','ShellExperienceHost',
    'TextInputHost','SystemSettings','SettingsHelper',
    'ctfmon','taskhostw','sihost','fontdrvhost',
    'WmiPrvSE','dllhost','SecurityHealthSystray',
    'OneDrive','PhoneExperienceHost','WidgetService',
    'LockApp','LogiOverlay','CompPkgSrv'
)
$pencereli = Get-Process | Where-Object {{
    $_.MainWindowHandle -ne 0 -and
    $_.MainWindowTitle -ne '' -and
    $_.Id -ne $atlasPid -and
    $sistemSurecler -notcontains $_.Name
}}
$kapatilan = @()
foreach ($p in $pencereli) {{
    try {{
        $null = $p.CloseMainWindow()
        $kapatilan += $p.Name
    }} catch {{}}
}}
$kapatilan -join ','
"""
        r = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, text=True, timeout=10
        )
        kapatilan = r.stdout.strip()
        if kapatilan:
            liste = [x.strip() for x in kapatilan.split(",") if x.strip()]
            logger.info(f"Tüm programlar kapatıldı: {liste}")
            return True, f"{len(liste)} program kapatıldı"
        else:
            return True, "Açık program bulunamadı"
    except Exception as e:
        logger.error(f"Tüm programları kapatma hatası: {e}")
        return False, str(e)


def bilgisayari_kapat(gecikme=30):
    """
    Bilgisayarı kapatır.
    Güvenlik: 30 saniye gecikme, iptal edilebilir.
    """
    try:
        subprocess.Popen(f"shutdown /s /t {gecikme}", shell=True)
        logger.info(f"Bilgisayar {gecikme}s sonra kapanacak")
        return True, f"Bilgisayar {gecikme} saniye sonra kapanacak. İptal etmek istersen 'iptal et' de."
    except Exception as e:
        logger.error(f"Bilgisayar kapatma hatası: {e}")
        return False, str(e)


def bilgisayari_yeniden_baslat(gecikme=30):
    """
    Bilgisayarı yeniden başlatır.
    Güvenlik: 30 saniye gecikme, iptal edilebilir.
    """
    try:
        subprocess.Popen(f"shutdown /r /t {gecikme}", shell=True)
        logger.info(f"Bilgisayar {gecikme}s sonra yeniden başlayacak")
        return True, f"Bilgisayar {gecikme} saniye sonra yeniden başlayacak. İptal etmek istersen 'iptal et' de."
    except Exception as e:
        logger.error(f"Bilgisayar yeniden başlatma hatası: {e}")
        return False, str(e)


def kapatma_iptal():
    """Zamanlanmış shutdown/restart'ı iptal eder."""
    try:
        subprocess.Popen("shutdown /a", shell=True)
        logger.info("Kapatma/yeniden başlatma iptal edildi")
        return True, "Kapatma işlemi iptal edildi"
    except Exception as e:
        return False, str(e)


def uyku_modu():
    """Bilgisayarı uyku moduna alır."""
    try:
        subprocess.Popen("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
        logger.info("Uyku moduna geçiliyor")
        return True, "Uyku moduna geçiliyor"
    except Exception as e:
        return False, str(e)


def bilgisayar_bilgisi():
    """Bilgisayar temel bilgilerini döndürür"""
    try:
        import platform
        bilgi = {
            "isim": platform.node(),
            "sistem": platform.system(),
            "surum": platform.version(),
            "islemci": platform.processor(),
            "mimari": platform.machine(),
        }
        # RAM bilgisi
        try:
            import psutil
            ram = psutil.virtual_memory()
            bilgi["ram_toplam"] = f"{ram.total / (1024**3):.1f} GB"
            bilgi["ram_kullanilan"] = f"{ram.used / (1024**3):.1f} GB"
            bilgi["ram_yuzde"] = f"%{ram.percent}"
        except ImportError:
            pass
        return True, bilgi
    except Exception as e:
        return False, str(e)
