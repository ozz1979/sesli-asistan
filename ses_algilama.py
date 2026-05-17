"""
ATLAS - Ses Algılama
====================
Beyin Karşılığı: İşitme Korteksi (A1)
Görev: Mikrofon yönetimi, ses aktivite tespiti (VAD), ses yakalama

İnsan kulağı ses dalgalarını elektrik sinyallerine çevirir,
birincil işitme korteksi temel ses özelliklerini (frekans, şiddet) işler.
Bu modül aynı görevi yapar: mikrofon → ham ses verisi.

NOT: sounddevice kullanır — PyAudio gerektirmez!
"""

import threading
import time
import logging
import numpy as np

logger = logging.getLogger("ATLAS.ses")

# Sabitler
SAMPLE_RATE = 16000      # 16 kHz — Google STT için ideal
CHANNELS = 1             # Mono
DTYPE = "int16"          # 16-bit PCM
CHUNK_DURATION = 0.1     # 100ms chunk'lar halinde oku
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_DURATION)


class SesAlgilama:
    """
    İşitme Korteksi — mikrofon yönetimi ve ses yakalama.
    sounddevice ile çalışır (PyAudio gerektirmez).
    """

    def __init__(self, config=None):
        config = config or {}
        stt_cfg = config.get("stt", {})

        self._enerji_esigi = stt_cfg.get("enerji_esigi", 200)
        self._kalibrasyon_esigi = self._enerji_esigi  # Kalibrasyon bazlını sakla
        self._dinamik_esik = stt_cfg.get("dinamik_esik", True)
        self._kalibrasyon_suresi = stt_cfg.get("kalibrasyon_suresi", 1.5)
        self._dinleme_suresi = stt_cfg.get("dinleme_suresi", 10)
        self._sessizlik_suresi = stt_cfg.get("sessizlik_suresi", 1.5)

        self._aktif = False
        self._lock = threading.Lock()

        # Google STT için recognizer
        self._recognizer = None

        # Durum
        self.hazir = threading.Event()
        self.hata = None

        # Ses seviye callback — GUI küresine bağlanır
        self.ses_seviye_callback = None

    def baslat(self, max_deneme=3):
        """Mikrofonu başlat ve kalibre et (başarısızsa tekrar dene)"""
        import speech_recognition as sr
        self._recognizer = sr.Recognizer()

        for deneme in range(1, max_deneme + 1):
            try:
                import sounddevice as sd

                cihaz = sd.query_devices(kind="input")
                logger.info(f"Mikrofon: {cihaz['name']} (SR: {cihaz['default_samplerate']})")

                # Kısa test kaydı
                logger.info(f"Mikrofon test ediliyor... (deneme {deneme}/{max_deneme})")
                test = sd.rec(int(SAMPLE_RATE * 0.3), samplerate=SAMPLE_RATE,
                             channels=CHANNELS, dtype=DTYPE)
                sd.wait()
                if test is None or len(test) == 0:
                    raise RuntimeError("Mikrofon ses kaydı yapamadı")

                # Kalibrasyon
                logger.info(f"Mikrofon kalibre ediliyor ({self._kalibrasyon_suresi}s)...")
                kalibrasyon = sd.rec(
                    int(SAMPLE_RATE * self._kalibrasyon_suresi),
                    samplerate=SAMPLE_RATE,
                    channels=CHANNELS,
                    dtype=DTYPE
                )
                sd.wait()

                rms = np.sqrt(np.mean(kalibrasyon.astype(np.float64) ** 2))
                if self._dinamik_esik:
                    # Eşik: min 30, max 200 — aşırı yükselmesini engelle
                    self._enerji_esigi = min(max(rms * 1.15, 30), 200)
                self._kalibrasyon_esigi = self._enerji_esigi
                logger.info(f"Kalibrasyon tamamlandı. Ortam RMS: {rms:.0f}, Eşik: {self._enerji_esigi:.0f}")

                self._aktif = True
                self.hazir.set()
                self.hata = None
                return True

            except ImportError as e:
                self.hata = f"Eksik paket: {e}"
                logger.error(f"Import hatası: {e}")
                return False
            except Exception as e:
                self.hata = str(e)
                logger.warning(f"Mikrofon denemesi {deneme}/{max_deneme} başarısız: {e}")
                if deneme < max_deneme:
                    logger.info(f"3 saniye sonra tekrar denenecek...")
                    time.sleep(3)

        logger.error(f"Mikrofon {max_deneme} denemede başlatılamadı: {self.hata}")
        return False

    def dinle(self, timeout=None):
        """
        Mikrofonu dinle ve ses yakala.
        Enerji tabanlı VAD — konuşma başlayınca kaydet, susunca dur.
        Ses seviyesini gerçek zamanlı olarak GUI'ye gönderir.
        
        Returns: speech_recognition.AudioData veya None
        """
        if not self._aktif:
            return None

        import sounddevice as sd
        import speech_recognition as sr

        timeout = timeout or self._dinleme_suresi

        # Her döngüde eşiği kalibrasyon bazlına sıfırla (yükselme sorunu engellenir)
        self._enerji_esigi = self._kalibrasyon_esigi
        esik = self._enerji_esigi

        logger.info(f"Dinleme basliyor (esik: {esik:.0f}, timeout: {timeout}s)")

        baslangic = time.time()
        buffer = []
        konusma_basladi = False
        sessizlik_baslangic = None
        sessizlik_limit = self._sessizlik_suresi
        log_sayac = 0

        try:
            stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SIZE
            )
            stream.start()
            logger.debug("Stream acildi")

            while True:
                gecen = time.time() - baslangic

                if gecen > timeout:
                    if konusma_basladi and len(buffer) > 0:
                        break
                    # Timeout — küreyi sıfırla
                    logger.info(f"Dinleme timeout ({timeout}s) - ses algilanamadi (esik: {esik:.0f})")
                    self._ses_seviye_gonder(0.0)
                    stream.stop()
                    stream.close()
                    return None

                chunk, overflowed = stream.read(CHUNK_SIZE)
                if overflowed:
                    logger.debug("Buffer overflow — chunk atlandı")

                rms = np.sqrt(np.mean(chunk.astype(np.float64) ** 2))

                # Her 2 saniyede bir durum logla
                log_sayac += 1
                if log_sayac % 20 == 1:
                    logger.info(f"Dinleme... RMS: {rms:.0f}, Esik: {esik:.0f}, Gecen: {gecen:.1f}s")

                # ── Ses seviyesini GUI küresine gönder ──
                normalized = min(1.0, rms / max(esik * 3, 1))
                self._ses_seviye_gonder(normalized)

                if rms > esik:
                    if not konusma_basladi:
                        konusma_basladi = True
                        logger.debug(f"Konuşma başladı (RMS: {rms:.0f})")
                    buffer.append(chunk.copy())
                    sessizlik_baslangic = None

                elif konusma_basladi:
                    buffer.append(chunk.copy())
                    if sessizlik_baslangic is None:
                        sessizlik_baslangic = time.time()
                    elif time.time() - sessizlik_baslangic > sessizlik_limit:
                        logger.debug("Sessizlik algılandı — kayıt tamamlandı")
                        break

            stream.stop()
            stream.close()

            # Kayıt bitti, küreyi sıfırla
            self._ses_seviye_gonder(0.0)

            if not buffer:
                return None

            ses_data = np.concatenate(buffer)
            raw_bytes = ses_data.tobytes()
            audio = sr.AudioData(raw_bytes, SAMPLE_RATE, 2)
            logger.debug(f"Ses yakalandı: {len(raw_bytes)} bytes, {len(raw_bytes)/SAMPLE_RATE/2:.1f}s")
            return audio

        except Exception as e:
            logger.warning(f"Dinleme hatası: {e}")
            self._ses_seviye_gonder(0.0)
            try:
                stream.stop()
                stream.close()
            except Exception:
                pass
            return None

    def _ses_seviye_gonder(self, seviye):
        """Ses seviyesini GUI callback'ine gönder"""
        if self.ses_seviye_callback:
            try:
                self.ses_seviye_callback(seviye)
            except Exception:
                pass

    def stt_google(self, audio):
        """Google Speech-to-Text ile ses → metin"""
        if not audio or not self._recognizer:
            return None

        try:
            text = self._recognizer.recognize_google(audio, language="tr-TR")
            logger.info(f"STT (Google): '{text}'")
            return text
        except Exception as e:
            tur = type(e).__name__
            if "UnknownValueError" in tur:
                logger.debug("Google STT: Anlaşılamadı")
            elif "RequestError" in tur:
                logger.warning(f"Google STT bağlantı hatası: {e}")
            else:
                logger.debug(f"Google STT hatası ({tur}): {e}")
            return None

    def durdur(self):
        """Mikrofonu durdur"""
        self._aktif = False
        self.hazir.clear()

    @property
    def aktif(self):
        return self._aktif

    def esik_bilgisi(self):
        return {
            "enerji_esigi": self._enerji_esigi,
            "dinamik": self._dinamik_esik
        }
