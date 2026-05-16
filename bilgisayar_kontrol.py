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
    """Ekran görüntüsü alır, masaüstüne kaydeder. DPI-aware — tam çözünürlük yakalar."""
    try:
        from datetime import datetime
        masaustu = os.path.expanduser("~\\Desktop")
        dosya = os.path.join(masaustu, f"ekran_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        dosya_ps = dosya.replace("\\", "\\\\")

        # DPI-aware ekran görüntüsü — gerçek piksel çözünürlüğü kullanır
        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# DPI farkındalığı etkinleştir — tam çözünürlük yakala
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class DpiHelper {{
    [DllImport("user32.dll")]
    public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")]
    public static extern int GetSystemMetrics(int nIndex);
}}
"@
[DpiHelper]::SetProcessDPIAware()

# Gerçek fiziksel çözünürlüğü al
$width = [DpiHelper]::GetSystemMetrics(0)   # SM_CXSCREEN
$height = [DpiHelper]::GetSystemMetrics(1)  # SM_CYSCREEN

$bitmap = New-Object System.Drawing.Bitmap($width, $height)
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.CopyFromScreen(0, 0, 0, 0, (New-Object System.Drawing.Size($width, $height)))
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


def resim_kapat():
    """Açık resim/fotoğraf görüntüleyici uygulamalarını kapatır."""
    try:
        # Windows'taki yaygın resim görüntüleyiciler
        resim_programlari = [
            "Microsoft.Photos.exe",      # Windows Fotoğraflar
            "PhotosApp.exe",             # Windows Fotoğraflar (eski)
            "mspaint.exe",               # Paint
            "IrfanView.exe",             # IrfanView
            "i_view64.exe",              # IrfanView 64-bit
            "PhotoViewer.dll",           # Eski Windows Fotoğraf Görüntüleyici
            "dllhost.exe",               # Bazen resim için kullanılır
            "imageglass.exe",            # ImageGlass
        ]
        kapatilan = []
        for prog in resim_programlari:
            try:
                result = subprocess.run(
                    ["taskkill", "/IM", prog, "/F"],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    kapatilan.append(prog.replace(".exe", ""))
            except Exception:
                pass

        if kapatilan:
            return True, f"Resim görüntüleyici kapatıldı ({', '.join(kapatilan)})"

        # Hiçbir resim programı bulunamadıysa aktif pencereyi kapat (fallback)
        import pyautogui
        pyautogui.hotkey("alt", "F4")
        return True, "Pencere kapatıldı"
    except Exception as e:
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
    GÜVENLİK: ATLAS, explorer ve sistem süreçlerini KORUR.
    Yöntem: taskkill ile bilinen kullanıcı programlarını kapatır.
    """
    try:
        # Bilinen kullanıcı programları — sadece bunları kapat
        kullanici_programlari = [
            "chrome", "msedge", "firefox", "opera", "brave",
            "notepad", "wordpad", "mspaint",
            "WINWORD", "EXCEL", "POWERPNT", "OUTLOOK", "ONENOTE",
            "vlc", "wmplayer", "Spotify",
            "Discord", "Telegram", "WhatsApp", "Teams",
            "Code", "devenv",
            "GIMP", "Photoshop",
            "Steam", "EpicGamesLauncher",
            "Acrobat", "AcroRd32", "FoxitReader",
            "WinRAR", "7zFM",
        ]

        kapatilan = []
        for prog in kullanici_programlari:
            # Programın çalışıp çalışmadığını kontrol et
            check = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {prog}.exe", "/NH"],
                capture_output=True, text=True, timeout=3
            )
            if prog.lower() in check.stdout.lower() and "no tasks" not in check.stdout.lower():
                # Çalışıyor → kapat (nazikçe)
                subprocess.run(
                    ["taskkill", "/IM", f"{prog}.exe", "/F"],
                    capture_output=True, timeout=5
                )
                kapatilan.append(prog)

        if kapatilan:
            logger.info(f"Programlar kapatıldı: {kapatilan}")
            return True, f"{len(kapatilan)} program kapatıldı ({', '.join(kapatilan)})"
        else:
            return True, "Kapatılacak açık program bulunamadı"
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


# ============================================================
# HAVA DURUMU (wttr.in - ücretsiz, API key gerektirmez)
# ============================================================

def hava_durumu(sehir="Denizli"):
    """
    wttr.in API ile hava durumu sorgula.
    Returns: (True, dict) veya (False, hata_mesajı)
    """
    import urllib.request
    import json as j

    try:
        # Türkçe şehir adını URL-safe yap
        sehir_url = sehir.replace(" ", "+").replace("ı", "i").replace("ş", "s")
        sehir_url = sehir_url.replace("ç", "c").replace("ü", "u").replace("ö", "o")
        sehir_url = sehir_url.replace("ğ", "g").replace("İ", "I").replace("Ş", "S")
        sehir_url = sehir_url.replace("Ç", "C").replace("Ü", "U").replace("Ö", "O")
        sehir_url = sehir_url.replace("Ğ", "G")

        url = f"https://wttr.in/{sehir_url}?format=j1&lang=tr"
        req = urllib.request.Request(url, headers={"User-Agent": "ATLAS/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = j.loads(resp.read().decode("utf-8"))

        current = data.get("current_condition", [{}])[0]
        sicaklik = current.get("temp_C", "?")
        hissedilen = current.get("FeelsLikeC", "?")
        nem = current.get("humidity", "?")
        ruzgar = current.get("windspeedKmph", "?")

        # Türkçe hava açıklaması
        aciklama_tr = current.get("lang_tr", [{}])
        if aciklama_tr:
            durum = aciklama_tr[0].get("value", "Bilinmiyor")
        else:
            durum = current.get("weatherDesc", [{}])[0].get("value", "Bilinmiyor")

        sonuc = {
            "sehir": sehir,
            "sicaklik": sicaklik,
            "hissedilen": hissedilen,
            "durum": durum,
            "nem": nem,
            "ruzgar": ruzgar,
        }

        logger.info(f"Hava durumu: {sehir} → {sicaklik}°C, {durum}")
        return True, sonuc

    except Exception as e:
        logger.error(f"Hava durumu hatası: {e}")
        return False, str(e)
