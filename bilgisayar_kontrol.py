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
    """Ekran görüntüsü alır, masaüstüne kaydeder"""
    try:
        import pyautogui
        from datetime import datetime
        masaustu = os.path.expanduser("~\\Desktop")
        dosya = os.path.join(masaustu, f"ekran_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        ekran = pyautogui.screenshot()
        ekran.save(dosya)
        logger.info(f"Ekran görüntüsü: {dosya}")
        return True, f"Ekran görüntüsü masaüstüne kaydedildi"
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
    Ses kontrolü.
    islem: 'ac', 'kapat', 'yukselt', 'azalt'
    """
    komutlar = {
        "ac": "nircmd.exe mutesysvolume 0",
        "kapat": "nircmd.exe mutesysvolume 1",
        "yukselt": "nircmd.exe changesysvolume 5000",
        "azalt": "nircmd.exe changesysvolume -5000",
    }
    komut = komutlar.get(islem)
    if komut:
        try:
            subprocess.Popen(komut, shell=True)
            return True, f"Ses {islem}"
        except Exception as e:
            return False, str(e)
    return False, f"Bilinmeyen ses işlemi: {islem}"


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
