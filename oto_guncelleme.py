"""
ATLAS - Otomatik Guncelleme Sistemi
=====================================
Her baslatmada GitHub'dan guncellemeleri kontrol eder.
Yeni commit varsa dosyalari indirir ve ATLAS yeniden baslar.

Kullanicinin elle guncelleme yapmasina gerek kalmaz.
"""

import os
import time
import json
import logging
import urllib.request

logger = logging.getLogger("ATLAS.oto_guncelleme")

REPO = "ozz1979/sesli-asistan"
BRANCH = "main"
SHA_DOSYA = "son_guncelleme.json"

# GitHub'dan indirilecek tum dosyalar
DOSYALAR = [
    "bilgisayar_kontrol.py",
    "kalip_motoru.py",
    "main.py",
    "karar_merkezi.py",
    "hafiza_sistemi.py",
    "bilgisayar_tarama.py",
    "ogrenme_motoru.py",
    "bilgi_bankasi.py",
    "ses_algilama.py",
    "turkce.py",
    "dikkat_filtresi.py",
    "arayuz.py",
    "kimlik_tanima.py",
    "konusma_uretimi.py",
    "dil_anlama.py",
    "oto_guncelleme.py",
    "web_arama.py",
    "atlas_baslat.vbs",
    "startup_kur.bat",
    "startup_kaldir.bat",
    "guncelle.bat",
]


def _son_commit_sha():
    """GitHub'daki son commit SHA degerini al"""
    try:
        url = f"https://api.github.com/repos/{REPO}/commits/{BRANCH}"
        req = urllib.request.Request(url, headers={
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "ATLAS-AutoUpdate/1.0"
        })
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("sha", "")
    except Exception as e:
        logger.debug(f"GitHub commit SHA alinamadi: {e}")
        return None


def _kayitli_sha():
    """Yerel dosyadan kaydedilmis SHA oku"""
    try:
        if os.path.exists(SHA_DOSYA):
            with open(SHA_DOSYA, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("commit_sha", "")
    except Exception:
        pass
    return ""


def _sha_kaydet(sha):
    """Yeni SHA degerini kaydet"""
    try:
        with open(SHA_DOSYA, "w", encoding="utf-8") as f:
            json.dump({
                "commit_sha": sha,
                "tarih": time.strftime("%Y-%m-%d %H:%M:%S"),
                "dosya_sayisi": len(DOSYALAR)
            }, f, indent=2)
    except Exception as e:
        logger.error(f"SHA kaydetme hatasi: {e}")


def _dosya_indir(dosya_adi):
    """GitHub raw'dan tek dosya indir (cache-busting ile)"""
    try:
        t = str(int(time.time()))
        url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{dosya_adi}?v={t}"
        req = urllib.request.Request(url, headers={"Cache-Control": "no-cache"})
        resp = urllib.request.urlopen(req, timeout=15)
        icerik = resp.read()

        with open(dosya_adi, "wb") as f:
            f.write(icerik)

        return True
    except Exception as e:
        logger.warning(f"Indirme hatasi ({dosya_adi}): {e}")
        return False


def guncelleme_kontrol():
    """
    Guncelleme kontrolu yap.

    Returns: (guncellendi: bool, mesaj: str)
    - guncellendi=True ise ATLAS yeniden baslatilmali
    - guncellendi=False ise normal devam
    """
    logger.info("Otomatik guncelleme kontrolu...")

    # 1. GitHub'daki son commit SHA'sini al
    yeni_sha = _son_commit_sha()
    if yeni_sha is None:
        logger.info("Internet baglantisi yok veya GitHub'a erisilemedi — atlanıyor")
        return False, "Baglanti yok"

    # 2. Kayitli SHA ile karsilastir
    eski_sha = _kayitli_sha()

    # Ilk calistirma — sadece SHA kaydet, indirme yapma
    # (dosyalar zaten guncelle.bat ile indirilmis olmali)
    if not eski_sha:
        _sha_kaydet(yeni_sha)
        logger.info(f"Ilk calistirma — SHA kaydedildi: {yeni_sha[:12]}...")
        return False, "Ilk calistirma, SHA kaydedildi"

    # Degisiklik yoksa devam
    if yeni_sha == eski_sha:
        logger.info("ATLAS guncel, degisiklik yok.")
        return False, "Guncel"

    # 3. Yeni commit var — tum dosyalari indir
    logger.info(f"Guncelleme bulundu! {eski_sha[:12]}... -> {yeni_sha[:12]}...")

    basarili = 0
    hatali = 0
    hatali_dosyalar = []

    for dosya in DOSYALAR:
        if _dosya_indir(dosya):
            basarili += 1
            logger.info(f"  Guncellendi: {dosya}")
        else:
            hatali += 1
            hatali_dosyalar.append(dosya)

    # 4. Tum dosyalar basariyla indiyse SHA kaydet
    if hatali == 0:
        _sha_kaydet(yeni_sha)
        mesaj = f"{basarili} dosya guncellendi"
        logger.info(f"Guncelleme tamamlandi: {mesaj}")
        return True, mesaj
    else:
        # Kismi guncelleme — SHA kaydetme (tekrar denenecek)
        mesaj = f"{basarili} dosya guncellendi, {hatali} hata: {', '.join(hatali_dosyalar)}"
        logger.warning(f"Kismi guncelleme: {mesaj}")
        # Yine de yeniden baslat (basarili dosyalar uygulansin)
        if basarili > 0:
            _sha_kaydet(yeni_sha)
            return True, mesaj
        return False, mesaj
