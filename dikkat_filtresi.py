"""
ATLAS - Dikkat Filtresi
========================
Beyin Karşılığı: Retiküler Aktivasyon Sistemi (RAS)
Görev: Tetik kelime algılama, bağlam izleme, önem filtresi

İnsan beyni saniyede milyonlarca uyaran alır ama sadece önemli olanları
bilinçli farkındalığa yönlendirir. "Kokteyl parti etkisi" — kalabalıkta
isminizi duyarsınız.

ATLAS da aynı şekilde "Atlas" tetik kelimesini bekler.
"""

import time
import threading
from enum import Enum
from turkce import turkce_normalize, tetik_kelime_kontrol


class DikkatModu(Enum):
    """Asistanın dikkat durumu"""
    PASIF = "pasif"         # Sadece tetik kelime bekliyor
    AKTIF = "aktif"         # Aktif dinliyor, her şeyi işliyor
    ISIM_OGRENME = "isim"   # İlk tanışma — isim öğreniyor
    MESGUL = "mesgul"       # Yanıt üretiyor, yeni girdi almıyor


class DikkatFiltresi:
    """
    RAS — Retiküler Aktivasyon Sistemi.
    Neyin önemli olduğuna karar verir.
    """

    def __init__(self, config=None):
        config = config or {}
        dikkat_cfg = config.get("dikkat", {})

        self._tetik_kelime = config.get("tetik_kelime", "atlas")
        self._aktif_sure = dikkat_cfg.get("aktif_mod_suresi", 45)  # saniye
        self._pasif_dinleme = dikkat_cfg.get("pasif_dinleme", True)

        self._mod = DikkatModu.PASIF
        self._son_aktif = 0
        self._lock = threading.Lock()

        # Olay dinleyicileri
        self._mod_degisim_callback = None

    @property
    def mod(self):
        with self._lock:
            # Aktif mod süresi doldu mu?
            if self._mod == DikkatModu.AKTIF:
                if time.time() - self._son_aktif > self._aktif_sure:
                    self._mod = DikkatModu.PASIF
            return self._mod

    @mod.setter
    def mod(self, yeni_mod):
        with self._lock:
            eski = self._mod
            self._mod = yeni_mod
            if yeni_mod == DikkatModu.AKTIF:
                self._son_aktif = time.time()
            if eski != yeni_mod and self._mod_degisim_callback:
                try:
                    self._mod_degisim_callback(eski, yeni_mod)
                except Exception:
                    pass

    def mod_degisim_dinle(self, callback):
        """Mod değişim callback'i ayarla"""
        self._mod_degisim_callback = callback

    def aktif_sure_uzat(self):
        """Aktif mod süresini uzat (kullanıcı konuşmaya devam ediyor)"""
        with self._lock:
            self._son_aktif = time.time()

    def filtrele(self, text):
        """
        Gelen metni filtrele ve nasıl işleneceğine karar ver.
        
        Returns: dict{
            islem: "tetik" | "komut" | "yoksay" | "isim_cevap",
            metin: temizlenmiş metin,
            tetik_bulundu: bool
        }
        """
        if not text:
            return {"islem": "yoksay", "metin": "", "tetik_bulundu": False}

        mevcut_mod = self.mod

        # İsim öğrenme modunda her şeyi isim cevabı olarak al
        if mevcut_mod == DikkatModu.ISIM_OGRENME:
            return {
                "islem": "isim_cevap",
                "metin": text.strip(),
                "tetik_bulundu": False
            }

        # Meşgulken yeni girdi alma
        if mevcut_mod == DikkatModu.MESGUL:
            return {"islem": "yoksay", "metin": text, "tetik_bulundu": False}

        # Tetik kelime kontrolü
        tetik_var, temiz_metin = tetik_kelime_kontrol(text, self._tetik_kelime)

        if tetik_var:
            # Tetik kelime bulundu — aktif moda geç
            self.mod = DikkatModu.AKTIF
            if temiz_metin:
                # "Atlas saat kaç?" → tetik + komut birlikte
                return {
                    "islem": "tetik_komut",
                    "metin": temiz_metin,
                    "tetik_bulundu": True
                }
            else:
                # Sadece "Atlas" dedi
                return {
                    "islem": "tetik",
                    "metin": "",
                    "tetik_bulundu": True
                }

        if mevcut_mod == DikkatModu.AKTIF:
            # Aktif moddayız, her şeyi komut olarak al
            self.aktif_sure_uzat()
            return {
                "islem": "komut",
                "metin": text.strip(),
                "tetik_bulundu": False
            }

        # Pasif mod — tetik kelime olmadan gelen ses
        if self._pasif_dinleme:
            # Pasif dinleme açıksa her şeyi işle (her zaman aktif)
            self.mod = DikkatModu.AKTIF
            return {
                "islem": "komut",
                "metin": text.strip(),
                "tetik_bulundu": False
            }

        # Pasif dinleme kapalı ve tetik yok → yoksay
        return {"islem": "yoksay", "metin": text, "tetik_bulundu": False}

    def kalan_aktif_sure(self):
        """Aktif modda kalan süre (saniye)"""
        with self._lock:
            if self._mod != DikkatModu.AKTIF:
                return 0
            kalan = self._aktif_sure - (time.time() - self._son_aktif)
            return max(0, kalan)
