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

# ── Müzik modu takibi ──
_muzik_modu = False

def muzik_durumu():
    """Müzik çalıyor mu? (müzik modu aktif mi)"""
    return _muzik_modu

def _muzik_modu_ac():
    """Müzik modu aktif et"""
    global _muzik_modu
    _muzik_modu = True
    logger.info("Müzik modu: AKTİF")

def _muzik_modu_kapat():
    """Müzik modu kapat"""
    global _muzik_modu
    _muzik_modu = False
    logger.info("Müzik modu: KAPALI")


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
        kapatildi = False

        # Yöntem 1: PowerShell ile resim dosyası açık pencere bul ve kapat
        # Bu yöntem UWP uygulamaları dahil tüm pencerelerle çalışır
        ps_script = """
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WinHelper {
    [DllImport("user32.dll")]
    public static extern IntPtr FindWindow(string lpClassName, string lpWindowName);
    [DllImport("user32.dll")]
    public static extern bool PostMessage(IntPtr hWnd, uint Msg, IntPtr wParam, IntPtr lParam);
}
"@

$kapatilan = 0
# Resim uzantılarını pencere başlıklarında ara
$procs = Get-Process | Where-Object { $_.MainWindowTitle -ne '' }
foreach ($p in $procs) {
    $title = $p.MainWindowTitle.ToLower()
    if ($title -match '\\.(png|jpg|jpeg|bmp|gif|webp|tiff)' -or
        $title -match 'photos' -or $title -match 'fotoğraf' -or
        $title -match 'resim' -or $title -match 'ekran_') {
        try {
            # WM_CLOSE gönder (nazikçe kapat)
            $hWnd = $p.MainWindowHandle
            if ($hWnd -ne [IntPtr]::Zero) {
                [WinHelper]::PostMessage($hWnd, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
                $kapatilan++
            }
        } catch {}
    }
}

# Yöntem 2: Bilinen resim programlarını doğrudan kapat
$resim_procs = @('Microsoft.Photos', 'PhotosApp', 'mspaint', 'IrfanView',
                  'i_view64', 'imageglass', 'nomacs', 'XnView', 'FastStone')
foreach ($name in $resim_procs) {
    try {
        $found = Get-Process -Name $name -ErrorAction SilentlyContinue
        if ($found) {
            $found | Stop-Process -Force
            $kapatilan++
        }
    } catch {}
}

Write-Output $kapatilan
"""
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, timeout=10, text=True
        )
        output = result.stdout.strip()
        try:
            kapatilan_sayisi = int(output)
            if kapatilan_sayisi > 0:
                kapatildi = True
        except (ValueError, TypeError):
            pass

        if kapatildi:
            return True, "Resim kapatıldı"

        # Yöntem 3: Fallback — aktif pencereyi Alt+F4 ile kapat
        import pyautogui
        import time
        time.sleep(0.3)
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


def ses_seviye_ayarla(yuzde):
    """
    Sistem sesini belirli yüzdeye ayarla (0-100).
    pyautogui ile hızlı ses tuşu basımı kullanır.
    """
    yuzde = max(0, min(100, yuzde))
    try:
        import pyautogui
        # Sesi sıfırla (50 kere azalt → %0), sonra hedef yüzdeye çıkar (her basış ≈ %2)
        pyautogui.press("volumedown", presses=50, interval=0.01)
        if yuzde > 0:
            pyautogui.press("volumeup", presses=yuzde // 2, interval=0.01)
        logger.info(f"Ses seviyesi: ~%{yuzde}")
        return True, f"Ses %{yuzde}'e ayarlandı"
    except Exception as e:
        logger.error(f"Ses ayarı hatası: {e}")
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


# ============================================================
# MÜZİK / MEDYA KONTROL
# ============================================================

def muzik_cal(sorgu):
    """
    YouTube'da müzik ara ve ilk videoyu doğrudan aç.
    Koordinat tıklaması yerine video ID'sini programatik alır.
    1. YouTube arama HTML'inden ilk video ID'si çekilir
    2. youtube.com/watch?v=ID ile doğrudan video açılır
    Fallback: ID bulunamazsa arama sayfasını açar
    """
    import urllib.request, urllib.parse, re

    try:
        query = urllib.parse.quote(sorgu)
        search_url = f"https://www.youtube.com/results?search_query={query}"

        # YouTube arama sayfasının HTML'ini al
        req = urllib.request.Request(search_url, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
        })
        logger.info(f"YouTube müzik arama: {sorgu}")
        resp = urllib.request.urlopen(req, timeout=10)
        html = resp.read().decode("utf-8", errors="ignore")

        # İlk video ID'sini bul (11 karakter, YouTube standart format)
        match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
        if match:
            video_id = match.group(1)
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            os.startfile(video_url)
            logger.info(f"YouTube video açıldı: {video_url}")

            # Müzik modu: sesi düşür + flag aç — mikrofon kullanıcıyı duyabilsin
            _muzik_modu_ac()
            import threading
            def _ses_kis():
                time.sleep(2)  # Video yüklensin
                ses_seviye_ayarla(20)
                logger.info("Müzik modu: ses %20'ye düşürüldü (mikrofon için)")
            threading.Thread(target=_ses_kis, daemon=True).start()

            return True, f"YouTube'da '{sorgu}' çalınıyor"
        else:
            # Fallback: video ID bulunamadı, arama sayfasını aç
            logger.warning("YouTube video ID bulunamadı, arama sayfası açılıyor")
            os.startfile(search_url)
            return True, f"YouTube'da '{sorgu}' araması yapıldı"

    except Exception as e:
        logger.error(f"Müzik çalma hatası: {e}")
        # Son fallback: arama URL'sini doğrudan aç
        try:
            import urllib.parse as up
            os.startfile(f"https://www.youtube.com/results?search_query={up.quote(sorgu)}")
        except Exception:
            pass
        return False, str(e)


def medya_oynat_duraklat():
    """Medya oynat/duraklat — YouTube, Spotify, VLC vb."""
    try:
        import pyautogui
        pyautogui.press("playpause")
        return True, "Oynat/Duraklat"
    except Exception as e:
        return False, str(e)


def medya_sonraki():
    """Sonraki parça / video"""
    try:
        import pyautogui
        pyautogui.press("nexttrack")
        return True, "Sonraki parça"
    except Exception as e:
        return False, str(e)


def medya_onceki():
    """Önceki parça / video"""
    try:
        import pyautogui
        pyautogui.press("prevtrack")
        return True, "Önceki parça"
    except Exception as e:
        return False, str(e)


def doviz_kuru(birim="USD"):
    """
    Güncel döviz kuru sorgula (TRY bazlı).
    birim: USD, EUR, GBP, vb.
    Returns: (True, dict) veya (False, hata_mesajı)
    """
    import urllib.request
    import json as j

    birim = birim.upper().strip()

    apis = [
        f"https://open.er-api.com/v6/latest/{birim}",
        f"https://api.exchangerate-api.com/v4/latest/{birim}",
    ]

    for api_url in apis:
        try:
            req = urllib.request.Request(api_url, headers={"User-Agent": "ATLAS/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = j.loads(resp.read().decode("utf-8"))

            rates = data.get("rates", {})
            try_rate = rates.get("TRY")
            if try_rate:
                sonuc = {
                    "birim": birim,
                    "kur": round(float(try_rate), 2),
                    "tum_kurlar": {
                        "TRY": rates.get("TRY"),
                        "EUR": rates.get("EUR"),
                        "USD": rates.get("USD"),
                        "GBP": rates.get("GBP"),
                    }
                }
                logger.info(f"Döviz kuru: 1 {birim} = {sonuc['kur']} TRY")
                return True, sonuc
        except Exception as e:
            logger.warning(f"Döviz API hatası ({api_url}): {e}")
            continue

    return False, "Döviz kuru alınamadı"
