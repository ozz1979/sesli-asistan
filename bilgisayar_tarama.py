"""
ATLAS - Bilgisayar Tarama Modülü
=================================
Beyin Karşılığı: Duyu Korteksi (Somatosensory Cortex)
Görev: Bilgisayarı tarayarak tanımak, tüm bilgileri hafızaya kaydetmek

İlk açılışta detaylı tarama yapar, sonra her açılışta hızlı güncelleme.
Bilgiler AI'ın bağlamına eklenir → komutları daha iyi anlar.
"""

import os
import json
import time
import subprocess
import logging
import platform
from datetime import datetime

logger = logging.getLogger("ATLAS.tarama")

TARAMA_DOSYASI = "hafiza/bilgisayar.json"


def bilgisayar_tara():
    """
    Bilgisayarı detaylı tara ve tüm bilgileri döndür.
    İlk çalıştırma ~3-5 saniye sürer.
    """
    logger.info("Bilgisayar taraması başlıyor...")
    baslangic = time.time()

    bilgi = {
        "tarama_tarihi": datetime.now().isoformat(),
        "sistem": _sistem_bilgisi(),
        "programlar": _kurulu_programlar(),
        "masaustu": _masaustu_dosyalari(),
        "klasorler": _onemli_klasorler(),
        "diskler": _disk_bilgisi(),
        "ag": _ag_bilgisi(),
        "ekran": _ekran_bilgisi(),
        "varsayilan_tarayici": _varsayilan_tarayici(),
    }

    sure = time.time() - baslangic
    bilgi["tarama_suresi_sn"] = round(sure, 1)
    logger.info(f"Bilgisayar taraması tamamlandı ({sure:.1f}s)")
    logger.info(f"  Sistem: {bilgi['sistem'].get('bilgisayar_adi', '?')}")
    logger.info(f"  Programlar: {len(bilgi['programlar'])} adet")
    logger.info(f"  Masaüstü: {len(bilgi['masaustu'])} dosya/klasör")

    return bilgi


def _sistem_bilgisi():
    """İşletim sistemi, CPU, RAM bilgileri"""
    bilgi = {
        "bilgisayar_adi": platform.node(),
        "isletim_sistemi": f"{platform.system()} {platform.release()}",
        "isletim_surumu": platform.version(),
        "islemci": platform.processor(),
        "mimari": platform.machine(),
        "python_surumu": platform.python_version(),
        "kullanici_adi": os.environ.get("USERNAME", os.environ.get("USER", "")),
        "kullanici_dizini": os.path.expanduser("~"),
    }

    # RAM bilgisi — PowerShell ile
    try:
        r = subprocess.run(
            ["powershell", "-Command",
             "(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            ram_byte = int(r.stdout.strip())
            bilgi["ram_toplam_gb"] = round(ram_byte / (1024 ** 3), 1)
    except Exception:
        pass

    # CPU adı
    try:
        r = subprocess.run(
            ["powershell", "-Command",
             "(Get-CimInstance Win32_Processor).Name"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            bilgi["islemci_adi"] = r.stdout.strip()
    except Exception:
        pass

    return bilgi


def _kurulu_programlar():
    """Windows'ta kurulu programları bul — Registry + Start Menu"""
    programlar = set()

    # 1. Registry'den kurulu programlar
    reg_yollar = [
        r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
        r"HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall",
        r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
    ]

    for reg_yol in reg_yollar:
        try:
            r = subprocess.run(
                ["powershell", "-Command",
                 f"Get-ItemProperty '{reg_yol}\\*' -ErrorAction SilentlyContinue | "
                 f"Where-Object {{ $_.DisplayName }} | "
                 f"Select-Object -ExpandProperty DisplayName"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                for satir in r.stdout.strip().split("\n"):
                    ad = satir.strip()
                    if ad and len(ad) > 1:
                        programlar.add(ad)
        except Exception:
            pass

    # 2. Start Menu kısayolları
    start_yollar = [
        os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs"),
        r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs",
    ]

    for start_yol in start_yollar:
        try:
            if os.path.isdir(start_yol):
                for root, dirs, files in os.walk(start_yol):
                    for f in files:
                        if f.endswith(".lnk"):
                            ad = f.replace(".lnk", "").strip()
                            if ad and len(ad) > 1:
                                programlar.add(ad)
        except Exception:
            pass

    return sorted(programlar)


def _masaustu_dosyalari():
    """Masaüstündeki dosya ve klasörleri listele"""
    masaustu = os.path.expanduser("~\\Desktop")
    dosyalar = []

    try:
        for item in os.listdir(masaustu):
            tam_yol = os.path.join(masaustu, item)
            tip = "klasor" if os.path.isdir(tam_yol) else "dosya"
            uzanti = os.path.splitext(item)[1].lower() if tip == "dosya" else ""
            boyut = 0
            try:
                if tip == "dosya":
                    boyut = os.path.getsize(tam_yol)
            except Exception:
                pass

            dosyalar.append({
                "ad": item,
                "tip": tip,
                "uzanti": uzanti,
                "boyut_kb": round(boyut / 1024, 1) if boyut else 0,
            })
    except Exception as e:
        logger.error(f"Masaüstü tarama hatası: {e}")

    return dosyalar


def _onemli_klasorler():
    """Kullanıcının önemli klasörlerini kontrol et"""
    ev = os.path.expanduser("~")
    klasorler = {}

    kontrol = {
        "masaustu": os.path.join(ev, "Desktop"),
        "belgelerim": os.path.join(ev, "Documents"),
        "indirilenler": os.path.join(ev, "Downloads"),
        "resimler": os.path.join(ev, "Pictures"),
        "muzik": os.path.join(ev, "Music"),
        "videolar": os.path.join(ev, "Videos"),
    }

    for ad, yol in kontrol.items():
        if os.path.isdir(yol):
            try:
                dosya_sayisi = len(os.listdir(yol))
                klasorler[ad] = {
                    "yol": yol,
                    "dosya_sayisi": dosya_sayisi,
                    "mevcut": True,
                }
            except Exception:
                klasorler[ad] = {"yol": yol, "mevcut": True, "dosya_sayisi": 0}
        else:
            klasorler[ad] = {"yol": yol, "mevcut": False, "dosya_sayisi": 0}

    return klasorler


def _disk_bilgisi():
    """Disk sürücüleri ve boş alan"""
    diskler = []

    try:
        r = subprocess.run(
            ["powershell", "-Command",
             "Get-PSDrive -PSProvider FileSystem | "
             "Select-Object Name, @{N='UsedGB';E={[math]::Round($_.Used/1GB,1)}}, "
             "@{N='FreeGB';E={[math]::Round($_.Free/1GB,1)}} | "
             "ConvertTo-Json"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            veri = json.loads(r.stdout.strip())
            if isinstance(veri, dict):
                veri = [veri]
            for d in veri:
                if d.get("FreeGB", 0) > 0 or d.get("UsedGB", 0) > 0:
                    diskler.append({
                        "surucu": d.get("Name", "?") + ":",
                        "kullanilan_gb": d.get("UsedGB", 0),
                        "bos_gb": d.get("FreeGB", 0),
                    })
    except Exception:
        pass

    return diskler


def _ag_bilgisi():
    """Ağ bağlantısı bilgisi"""
    bilgi = {"bagli": False, "tip": "bilinmiyor"}

    try:
        r = subprocess.run(
            ["powershell", "-Command",
             "(Get-NetConnectionProfile -ErrorAction SilentlyContinue | "
             "Select-Object Name, InterfaceAlias, NetworkCategory | "
             "ConvertTo-Json)"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            veri = json.loads(r.stdout.strip())
            if isinstance(veri, dict):
                veri = [veri]
            if veri:
                bilgi["bagli"] = True
                bilgi["ag_adi"] = veri[0].get("Name", "")
                bilgi["arayuz"] = veri[0].get("InterfaceAlias", "")
                bilgi["tip"] = "WiFi" if "Wi-Fi" in bilgi.get("arayuz", "") else "Ethernet"
    except Exception:
        pass

    return bilgi


def _ekran_bilgisi():
    """Ekran çözünürlüğü"""
    bilgi = {}

    try:
        r = subprocess.run(
            ["powershell", "-Command",
             "Add-Type -AssemblyName System.Windows.Forms; "
             "$s = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds; "
             "\"$($s.Width)x$($s.Height)\""],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            bilgi["cozunurluk"] = r.stdout.strip()
    except Exception:
        pass

    return bilgi


def _varsayilan_tarayici():
    """Varsayılan web tarayıcıyı bul"""
    try:
        r = subprocess.run(
            ["powershell", "-Command",
             "(Get-ItemProperty 'HKCU:\\Software\\Microsoft\\Windows\\Shell\\Associations\\UrlAssociations\\http\\UserChoice' -ErrorAction SilentlyContinue).ProgId"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            prog_id = r.stdout.strip().lower()
            if "chrome" in prog_id:
                return "Google Chrome"
            elif "firefox" in prog_id:
                return "Firefox"
            elif "edge" in prog_id or "msedge" in prog_id:
                return "Microsoft Edge"
            elif "opera" in prog_id:
                return "Opera"
            elif "brave" in prog_id:
                return "Brave"
            else:
                return prog_id
    except Exception:
        pass

    return "bilinmiyor"


# ══════════════════════════════════════════════════
# HAFIZAYA KAYDETME / YÜKLEME
# ══════════════════════════════════════════════════

def tarama_kaydet(bilgi):
    """Tarama sonuçlarını dosyaya kaydet"""
    try:
        os.makedirs(os.path.dirname(TARAMA_DOSYASI), exist_ok=True)
        with open(TARAMA_DOSYASI, 'w', encoding='utf-8') as f:
            json.dump(bilgi, f, ensure_ascii=False, indent=2)
        logger.info(f"Tarama sonuçları kaydedildi: {TARAMA_DOSYASI}")
    except Exception as e:
        logger.error(f"Tarama kaydetme hatası: {e}")


def tarama_yukle():
    """Önceki tarama sonuçlarını yükle"""
    try:
        if os.path.exists(TARAMA_DOSYASI):
            with open(TARAMA_DOSYASI, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def tarama_gerekli_mi():
    """Yeni tarama gerekli mi kontrol et (ilk kez veya 24 saatten eski)"""
    bilgi = tarama_yukle()
    if not bilgi:
        return True

    try:
        tarih_str = bilgi.get("tarama_tarihi", "")
        tarih = datetime.fromisoformat(tarih_str)
        fark_saat = (datetime.now() - tarih).total_seconds() / 3600
        return fark_saat > 24  # 24 saatten eski → yeniden tara
    except Exception:
        return True


def tarama_ozeti_olustur(bilgi):
    """
    AI'ın system prompt'unda kullanılacak kısa özet oluştur.
    Token tasarrufu için sadece en önemli bilgiler.
    """
    if not bilgi:
        return ""

    satirlar = []
    satirlar.append("BİLGİSAYAR BİLGİLERİ:")

    # Sistem
    sis = bilgi.get("sistem", {})
    if sis:
        satirlar.append(f"- Bilgisayar: {sis.get('bilgisayar_adi', '?')}")
        satirlar.append(f"- Sistem: {sis.get('isletim_sistemi', '?')}")
        if sis.get("islemci_adi"):
            satirlar.append(f"- İşlemci: {sis.get('islemci_adi', '?')}")
        if sis.get("ram_toplam_gb"):
            satirlar.append(f"- RAM: {sis.get('ram_toplam_gb', '?')} GB")
        satirlar.append(f"- Kullanıcı: {sis.get('kullanici_adi', '?')}")

    # Diskler
    diskler = bilgi.get("diskler", [])
    if diskler:
        disk_str = ", ".join(f"{d['surucu']} {d.get('bos_gb',0)}GB boş" for d in diskler)
        satirlar.append(f"- Diskler: {disk_str}")

    # Ekran
    ekran = bilgi.get("ekran", {})
    if ekran.get("cozunurluk"):
        satirlar.append(f"- Ekran: {ekran['cozunurluk']}")

    # Ağ
    ag = bilgi.get("ag", {})
    if ag.get("bagli"):
        satirlar.append(f"- İnternet: {ag.get('tip', '?')} ({ag.get('ag_adi', '')})")

    # Varsayılan tarayıcı
    tarayici = bilgi.get("varsayilan_tarayici", "")
    if tarayici and tarayici != "bilinmiyor":
        satirlar.append(f"- Varsayılan tarayıcı: {tarayici}")

    # Kurulu programlar — en bilinenleri listele
    programlar = bilgi.get("programlar", [])
    if programlar:
        satirlar.append(f"- Kurulu program sayısı: {len(programlar)}")
        # Bilinen programlar
        bilinen = []
        anahtar_kelimeler = [
            "chrome", "firefox", "edge", "opera", "brave",
            "word", "excel", "powerpoint", "office",
            "visual studio", "vs code", "vscode",
            "discord", "telegram", "whatsapp", "teams", "zoom", "skype",
            "spotify", "steam", "epic", "vlc",
            "photoshop", "illustrator", "gimp",
            "python", "java", "node",
            "winrar", "7-zip", "notepad++",
        ]
        for prog in programlar:
            prog_lower = prog.lower()
            for ak in anahtar_kelimeler:
                if ak in prog_lower:
                    bilinen.append(prog)
                    break

        if bilinen:
            # En fazla 20 program göster
            satirlar.append(f"- Bazı kurulu programlar: {', '.join(bilinen[:20])}")

    # Masaüstü dosyaları (kısa)
    masaustu = bilgi.get("masaustu", [])
    if masaustu:
        klasorler = [d["ad"] for d in masaustu if d["tip"] == "klasor"]
        dosyalar = [d["ad"] for d in masaustu if d["tip"] == "dosya"]
        satirlar.append(f"- Masaüstü: {len(klasorler)} klasör, {len(dosyalar)} dosya")
        if klasorler:
            satirlar.append(f"  Klasörler: {', '.join(klasorler[:10])}")

    return "\n".join(satirlar)
