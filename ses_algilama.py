"""
ATLAS - Ses Algılama
====================
Beyin Karşılığı: İşitme Korteksi (A1)
Görev: Mikrofon yönetimi, ses aktivite tespiti (VAD), ses yakalama

İnsan kulağı ses dalgalarını elektrik sinyallerine çevirir,
birincil işitme korteksi temel ses özelliklerini (frekans, şiddet) işler.
Bu modül aynı görevi yapar: mikrofon → ham ses verisi.
"""

import threading
import time
import logging
import numpy as np

logger = logging.getLogger("ATLAS.ses")


class SesAlgilama:
    """
    İşitme Korteksi — mikrofon yönetimi ve ses yakalama.
    """

    def __init__(self, config=None):
        config = config or {}
        stt_cfg = config.get("stt", {})

        self._enerji_esigi = stt_cfg.get("enerji_esigi", 300)
        self._dinamik_esik = stt_cfg.get("dinamik_esik", True)
        self._kalibrasyon_suresi = stt_cfg.get("kalibrasyon_suresi", 1.5)
        self._dinleme_suresi = stt_cfg.get("dinleme_suresi", 7)
        self._sessizlik_suresi = stt_cfg.get("sessizlik_suresi", 2)

        self._recognizer = None
        self._mikrofon = None
        self._aktif = False
        self._lock = threading.Lock()

        # Durum
        self.hazir = threading.Event()
        self.hata = None

    def baslat(self):
        """Mikrofonu başlat ve kalibre et"""
        try:
            import speech_recognition as sr

            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = self._enerji_esigi
            self._recognizer.dynamic_energy_threshold = self._dinamik_esik
            self._recognizer.pause_threshold = self._sessizlik_suresi
            self._recognizer.phrase_threshold = 0.3
            self._recognizer.non_speaking_duration = 0.5

            # Mikrofonu test et
            self._mikrofon = sr.Microphone()
            with self._mikrofon as source:
                logger.info(f"Mikrofon kalibre ediliyor ({self._kalibrasyon_suresi}s)...")
                self._recognizer.adjust_for_ambient_noise(
                    source, duration=self._kalibrasyon_suresi
                )
                logger.info(f"Kalibrasyon tamamlandı. Enerji eşiği: {self._recognizer.energy_threshold:.0f}")

            self._aktif = True
            self.hazir.set()
            self.hata = None
            return True

        except Exception as e:
            self.hata = str(e)
            logger.error(f"Mikrofon başlatma hatası: {e}")
            return False

    def dinle(self, timeout=None):
        """
        Mikrofonu dinle ve ses yakala.
        
        Returns: audio verisi veya None (timeout/hata durumunda)
        """
        if not self._aktif or not self._recognizer:
            return None

        timeout = timeout or self._dinleme_suresi

        try:
            import speech_recognition as sr
            with self._mikrofon as source:
                logger.debug("Dinleniyor...")
                audio = self._recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=self._dinleme_suresi
                )
                return audio
        except Exception as e:
            if "timed out" not in str(e).lower():
                logger.warning(f"Dinleme hatası: {e}")
            return None

    def stt_google(self, audio):
        """Google Speech-to-Text ile ses → metin"""
        if not audio or not self._recognizer:
            return None

        try:
            text = self._recognizer.recognize_google(audio, language="tr-TR")
            logger.info(f"STT (Google): '{text}'")
            return text
        except Exception as e:
            logger.debug(f"Google STT hatası: {e}")
            return None

    def durdur(self):
        """Mikrofonu durdur"""
        self._aktif = False
        self.hazir.clear()

    @property
    def aktif(self):
        return self._aktif

    def esik_bilgisi(self):
        """Mevcut enerji eşiği bilgisini döndür"""
        if self._recognizer:
            return {
                "enerji_esigi": self._recognizer.energy_threshold,
                "dinamik": self._dinamik_esik
            }
        return {}
