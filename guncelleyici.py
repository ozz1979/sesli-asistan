"""
ATLAS - Otomatik Güncelleyici
==============================
Görev: GitHub releases'den otomatik güncelleme kontrolü ve uygulama

Asistan açıldığında ve periyodik olarak güncelleme kontrol eder.
Yeni sürüm varsa dosyaları günceller ve yeniden başlatma önerir.
"""

import json
import os
import sys
import time
import zipfile
import shutil
import logging
import threading
import requests

logger = logging.getLogger("ATLAS.guncelleme")

CONFIG_DOSYA = "config.json"


class Guncelleyici:
    """GitHub releases tabanlı otomatik güncelleyici"""

    def __init__(self, config=None):
        config = config or {}
        sistem = config.get("sistem", {})
        self._repo = sistem.get("github_repo", "ozz1979/sesli-asistan")
        self._aktif = sistem.get("guncelleme_kontrol", True)
        self._mevcut_surum = config.get("version", "0.0")
        self._kontrol_araligi = 3600  # 1 saat
        self._timer = None

        # Durum
        self.guncelleme_var = False
        self.yeni_surum = ""
        self.guncelleme_durumu = ""

    def kontrol_et(self):
        """GitHub'da yeni sürüm var mı kontrol et"""
        if not self._aktif:
            return False

        try:
            url = f"https://api.github.com/repos/{self._repo}/releases/latest"
            r = requests.get(url, timeout=10)
            if r.status_code != 200:
                logger.debug(f"GitHub API hatası: {r.status_code}")
                return False

            data = r.json()
            tag = data.get("tag_name", "").lstrip("v")

            if self._surum_karsilastir(tag, self._mevcut_surum) > 0:
                self.guncelleme_var = True
                self.yeni_surum = tag
                logger.info(f"Yeni sürüm bulundu: v{tag} (mevcut: v{self._mevcut_surum})")

                # ZIP dosyasını bul
                assets = data.get("assets", [])
                for asset in assets:
                    if asset["name"].endswith(".zip"):
                        return self._guncelle(asset["browser_download_url"], tag)

                logger.warning("Release'de ZIP dosyası bulunamadı")
                return False
            else:
                logger.debug(f"Güncel sürüm: v{self._mevcut_surum}")
                return False

        except Exception as e:
            logger.error(f"Güncelleme kontrol hatası: {e}")
            return False

    def _surum_karsilastir(self, s1, s2):
        """Sürüm numaralarını karşılaştır. >0: s1 daha yeni"""
        try:
            p1 = [int(x) for x in str(s1).split(".")]
            p2 = [int(x) for x in str(s2).split(".")]
            # Eşit uzunluğa getir
            max_len = max(len(p1), len(p2))
            p1.extend([0] * (max_len - len(p1)))
            p2.extend([0] * (max_len - len(p2)))
            for a, b in zip(p1, p2):
                if a > b: return 1
                if a < b: return -1
            return 0
        except Exception:
            return 0

    def _guncelle(self, zip_url, yeni_surum):
        """ZIP indir, dosyaları güncelle"""
        try:
            self.guncelleme_durumu = "İndiriliyor..."
            logger.info(f"Güncelleme indiriliyor: {zip_url}")

            # İndir
            r = requests.get(zip_url, timeout=60, stream=True)
            if r.status_code != 200:
                self.guncelleme_durumu = "İndirme hatası"
                return False

            zip_dosya = "guncelleme.zip"
            with open(zip_dosya, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.guncelleme_durumu = "Kuruluyor..."

            # Mevcut config'i yedekle (API key korunmalı)
            mevcut_config = {}
            if os.path.exists(CONFIG_DOSYA):
                with open(CONFIG_DOSYA, 'r', encoding='utf-8') as f:
                    mevcut_config = json.load(f)

            # ZIP'i aç
            gecici_dir = "guncelleme_gecici"
            with zipfile.ZipFile(zip_dosya, 'r') as z:
                z.extractall(gecici_dir)

            # Dosyaları kopyala
            kaynak_dir = gecici_dir
            # ZIP içinde tek klasör varsa onu kullan
            icerik = os.listdir(gecici_dir)
            if len(icerik) == 1 and os.path.isdir(os.path.join(gecici_dir, icerik[0])):
                kaynak_dir = os.path.join(gecici_dir, icerik[0])

            korunan_dosyalar = {"hafiza", "ses_cache", "atlas.log", "guncelleme.zip",
                                "guncelleme_gecici", "venv", "__pycache__"}

            for dosya in os.listdir(kaynak_dir):
                if dosya in korunan_dosyalar:
                    continue
                kaynak = os.path.join(kaynak_dir, dosya)
                hedef = dosya
                if os.path.isfile(kaynak):
                    shutil.copy2(kaynak, hedef)
                    logger.info(f"Güncellendi: {dosya}")

            # Config'i güncelle — API key'i koru
            if os.path.exists(CONFIG_DOSYA):
                with open(CONFIG_DOSYA, 'r', encoding='utf-8') as f:
                    yeni_config = json.load(f)
                # Eski config'den korunacak değerleri aktar
                if mevcut_config.get("ai", {}).get("gemini_api_key"):
                    yeni_config.setdefault("ai", {})["gemini_api_key"] = \
                        mevcut_config["ai"]["gemini_api_key"]
                if mevcut_config.get("kullanici", {}).get("ad"):
                    yeni_config.setdefault("kullanici", {})["ad"] = \
                        mevcut_config["kullanici"]["ad"]
                yeni_config["version"] = yeni_surum
                with open(CONFIG_DOSYA, 'w', encoding='utf-8') as f:
                    json.dump(yeni_config, f, ensure_ascii=False, indent=4)

            # Temizlik
            try:
                os.remove(zip_dosya)
                shutil.rmtree(gecici_dir, ignore_errors=True)
            except Exception:
                pass

            self.guncelleme_durumu = f"v{yeni_surum} kuruldu! Yeniden başlatma önerilir."
            self._mevcut_surum = yeni_surum
            logger.info(f"Güncelleme tamamlandı: v{yeni_surum}")
            return True

        except Exception as e:
            self.guncelleme_durumu = f"Güncelleme hatası: {e}"
            logger.error(f"Güncelleme hatası: {e}")
            return False

    def periyodik_kontrol_baslat(self):
        """Arka planda periyodik güncelleme kontrolü başlat"""
        def kontrol_dongusu():
            while self._aktif:
                self.kontrol_et()
                time.sleep(self._kontrol_araligi)

        t = threading.Thread(target=kontrol_dongusu, daemon=True)
        t.start()
        logger.info("Periyodik güncelleme kontrolü başlatıldı")
