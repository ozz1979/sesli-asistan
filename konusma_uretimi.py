"""
ATLAS - Konuşma Üretimi
========================
Beyin Karşılığı: Broca Alanı + Motor Korteks
Görev: Yanıt metni → doğal Türkçe konuşma (TTS)

İnsan beyninde Broca alanı cümleleri yapılandırır,
motor korteks konuşma kaslarını kontrol eder.
Bu modül metin → ses dönüşümü ve ön-bellek yönetimi yapar.
"""

import asyncio
import hashlib
import os
import threading
import time
import logging
import re
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("ATLAS.konusma")

# Ön bellek — sık kullanılan yanıtlar önceden hazırlanır
ON_BELLEK_YANITLARI = [
    "Evet, buradayım! Seni dinliyorum.",
    "Evet buradayım! Ne yapabilirim senin için?",
    "Buradayım! Ne yapabilirim?",
    "Merhaba! Seninle tanışmak istiyorum. Adın ne?",
    "Rica ederim!",
    "Tamam, anladım.",
    "Bir saniye düşüneyim.",
]


class KonusmaUretimi:
    """
    Broca Alanı — konuşma üretim merkezi.
    Metin → ses dönüşümü, ön-bellek, ses çalma.
    """

    def __init__(self, config=None):
        config = config or {}
        tts_cfg = config.get("tts", {})

        self._ses = tts_cfg.get("ses", "tr-TR-AhmetNeural")
        self._hiz = tts_cfg.get("hiz", "+0%")
        self._on_bellek_aktif = tts_cfg.get("on_bellek", True)
        self._on_bellek_esik = tts_cfg.get("on_bellek_esik", 25)

        self._cache_dir = "ses_cache"
        os.makedirs(self._cache_dir, exist_ok=True)

        self._executor = ThreadPoolExecutor(max_workers=2)
        self._lock = threading.Lock()
        self._caliniyor = False

        # Pygame mixer
        self._mixer_hazir = False
        self._mixer_baslat()

        # Ön bellek hazırlığı
        self.on_bellek_hazir = threading.Event()
        if self._on_bellek_aktif:
            self._executor.submit(self._on_bellek_hazirla)

    def _mixer_baslat(self):
        """Pygame mixer'ı başlat"""
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=24000, size=-16, channels=1, buffer=2048)
            self._mixer_hazir = True
        except Exception as e:
            logger.warning(f"Pygame mixer hatası: {e}")
            self._mixer_hazir = False

    def _cache_yolu(self, text):
        """Metin için cache dosya yolu"""
        h = hashlib.md5(text.encode()).hexdigest()[:12]
        return os.path.join(self._cache_dir, f"{h}.mp3")

    def _cache_var_mi(self, text):
        """Cache'de bu metin var mı?"""
        yol = self._cache_yolu(text)
        return os.path.exists(yol)

    async def _tts_olustur_async(self, text, dosya_yolu):
        """Edge-TTS ile ses oluştur (async)"""
        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                text, self._ses, rate=self._hiz
            )
            await communicate.save(dosya_yolu)
            return True
        except Exception as e:
            logger.error(f"Edge-TTS hatası: {e}")
            # Tekrar dene
            try:
                import edge_tts
                await asyncio.sleep(1)
                communicate = edge_tts.Communicate(
                    text, self._ses, rate=self._hiz
                )
                await communicate.save(dosya_yolu)
                return True
            except Exception as e2:
                logger.error(f"Edge-TTS 2. deneme hatası: {e2}")
                return False

    def _tts_olustur(self, text, dosya_yolu):
        """Edge-TTS ile ses oluştur (sync wrapper)"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            sonuc = loop.run_until_complete(self._tts_olustur_async(text, dosya_yolu))
            loop.close()
            return sonuc
        except Exception as e:
            logger.error(f"TTS oluşturma hatası: {e}")
            return False

    def _on_bellek_hazirla(self):
        """Sık kullanılan yanıtları önceden hazırla"""
        logger.info("Ön bellek hazırlanıyor...")
        for yanit in ON_BELLEK_YANITLARI:
            if not self._cache_var_mi(yanit):
                dosya = self._cache_yolu(yanit)
                self._tts_olustur(yanit, dosya)
        self.on_bellek_hazir.set()
        logger.info(f"Ön bellek hazır ({len(ON_BELLEK_YANITLARI)} yanıt)")

    def _ses_cal(self, dosya_yolu):
        """Ses dosyasını çal"""
        if not self._mixer_hazir:
            self._mixer_baslat()
        if not self._mixer_hazir:
            logger.warning("Mixer hazır değil, ses çalınamıyor")
            return False

        try:
            import pygame
            with self._lock:
                self._caliniyor = True
            pygame.mixer.music.load(dosya_yolu)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            with self._lock:
                self._caliniyor = False
            return True
        except Exception as e:
            logger.error(f"Ses çalma hatası: {e}")
            with self._lock:
                self._caliniyor = False
            return False

    def konus(self, text, bekle=True):
        """
        Metin → konuş.
        
        1. Cache'de varsa hemen çal
        2. Yoksa oluştur ve çal
        
        Args:
            text: Söylenecek metin
            bekle: True ise ses bitene kadar bekle
        """
        if not text:
            return

        text = text.strip()
        dosya = self._cache_yolu(text)

        # Cache kontrol
        if not os.path.exists(dosya):
            logger.debug(f"TTS oluşturuluyor: '{text[:50]}...'")
            basarili = self._tts_olustur(text, dosya)
            if not basarili:
                logger.error(f"TTS oluşturulamadı: '{text[:50]}'")
                return

        # Çal
        if bekle:
            self._ses_cal(dosya)
        else:
            self._executor.submit(self._ses_cal, dosya)

    def on_bellekten_konus(self, text):
        """
        Ön bellekteki yanıtı hemen çal (daha hızlı).
        Eğer tam eşleşme yoksa, en kısa benzer yanıtı bul.
        """
        # Tam eşleşme
        if self._cache_var_mi(text):
            self._ses_cal(self._cache_yolu(text))
            return True

        # Benzer eşleşme (kısa metinler için substring)
        if len(text) <= self._on_bellek_esik:
            text_lower = text.lower().strip()
            for onb in ON_BELLEK_YANITLARI:
                if text_lower in onb.lower():
                    if self._cache_var_mi(onb):
                        self._ses_cal(self._cache_yolu(onb))
                        return True

        # Cache'de yok, normal konuş
        self.konus(text)
        return True

    def arka_planda_hazirla(self, text):
        """Bir yanıtı arka planda hazırla (konuşmadan)"""
        if not self._cache_var_mi(text):
            self._executor.submit(self._tts_olustur, text, self._cache_yolu(text))

    @property
    def caliniyor(self):
        with self._lock:
            return self._caliniyor

    def durdur(self):
        """Sesi durdur"""
        try:
            import pygame
            pygame.mixer.music.stop()
            with self._lock:
                self._caliniyor = False
        except Exception:
            pass

    def temizle(self):
        """Kaynakları temizle"""
        self._executor.shutdown(wait=False)
        try:
            import pygame
            pygame.mixer.quit()
        except Exception:
            pass
