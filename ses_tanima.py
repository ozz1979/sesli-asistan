"""
Ses Tanima Modulu v5.1
- Google Speech Recognition (birincil - ucretsiz)
- Whisper (yedek - internet yoksa)
- HIZLI sessizlik algilama (1.0sn)
- Non-blocking InputStream + pre-buffer
- Thread-safe durdurma
- Zaman olcumu
"""
import numpy as np
import sounddevice as sd
from scipy.io.wavfile import write as wav_write
import tempfile
import os
import time
import threading
import queue
from collections import deque


class SesTanima:
    def __init__(self, config):
        self.stt_motor = config.get("stt_motor", "google")
        self.model = None
        self.model_boyut = config.get("whisper_model", "small")
        self.dil = config.get("whisper_dil", "tr")
        self.ornekleme_hizi = config.get("ornekleme_hizi", 16000)
        self.ses_esik = config.get("ses_esik", 0.008)
        self.sessizlik_suresi = config.get("sessizlik_suresi", 1.0)  # 2.0 -> 1.0
        self.min_kayit = config.get("min_kayit_suresi", 0.3)  # 0.5 -> 0.3
        self.maks_kayit = config.get("maks_kayit_suresi", 15.0)
        self.cihaz_indeksi = config.get("mikrofon_indeksi", None)
        self._aktif = True
        self._kalibrasyon_yapildi = False
        self._ortam_gurultusu = 0.0
        self._lock = threading.Lock()

    def modeli_yukle(self):
        if self.stt_motor == "whisper" and self.model is None:
            print(f"[*] Whisper '{self.model_boyut}' modeli yukleniyor...")
            from faster_whisper import WhisperModel
            self.model = WhisperModel(
                self.model_boyut, device="cpu", compute_type="int8"
            )
            print("[OK] Whisper modeli yuklendi!")
        elif self.stt_motor == "google":
            print("[OK] Google Ses Tanima kullanilacak (internet gerekli)")
        return self.model

    def mikrofon_listele(self):
        try:
            cihazlar = sd.query_devices()
            mikrofonlar = []
            for i, d in enumerate(cihazlar):
                if d['max_input_channels'] > 0:
                    mikrofonlar.append((i, d['name']))
            return mikrofonlar
        except Exception as e:
            print(f"[HATA] Mikrofon listesi alinamadi: {e}")
            return []

    def _kalibre_et(self):
        if self._kalibrasyon_yapildi:
            return
        print("[*] Ortam gurultusu olculuyor (1.5 sn sessiz kalin)...")
        try:
            olcum = sd.rec(
                int(1.5 * self.ornekleme_hizi),
                samplerate=self.ornekleme_hizi,
                channels=1,
                dtype='float32',
                device=self.cihaz_indeksi
            )
            sd.wait()
            self._ortam_gurultusu = float(np.sqrt(np.mean(olcum ** 2)))
            yeni_esik = max(self._ortam_gurultusu * 2.5, 0.003)
            if yeni_esik > self.ses_esik:
                self.ses_esik = yeni_esik
            print(f"   Ortam: {self._ortam_gurultusu:.5f}, Esik: {self.ses_esik:.5f}")
            self._kalibrasyon_yapildi = True
        except Exception as e:
            print(f"[!] Kalibrasyon hatasi: {e}")
            self._kalibrasyon_yapildi = True

    def dinle_ve_cevir(self):
        self.modeli_yukle()
        self._kalibre_et()

        with self._lock:
            if not self._aktif:
                return None

        ses_kuyrugu = queue.Queue()
        parca_suresi = 0.2  # 0.3 -> 0.2 (daha hassas algilama)
        parca_boyutu = int(parca_suresi * self.ornekleme_hizi)

        def ses_callback(indata, frames, time_info, status):
            ses_kuyrugu.put(indata.copy())

        ses_algilandi = False
        parcalar = []
        sessiz_sure = 0
        toplam_sure = 0
        on_tampon = deque(maxlen=3)  # 4 -> 3

        try:
            stream = sd.InputStream(
                samplerate=self.ornekleme_hizi,
                channels=1,
                dtype='float32',
                blocksize=parca_boyutu,
                device=self.cihaz_indeksi,
                callback=ses_callback
            )
            stream.start()

            while self._aktif:
                try:
                    parca = ses_kuyrugu.get(timeout=0.3)
                except queue.Empty:
                    continue

                seviye = float(np.sqrt(np.mean(parca ** 2)))

                if seviye > self.ses_esik:
                    if not ses_algilandi:
                        print(f"[!] Ses algilandi! (seviye: {seviye:.5f})")
                        ses_algilandi = True
                        for eski_parca in on_tampon:
                            parcalar.append(eski_parca)
                            toplam_sure += parca_suresi
                        on_tampon.clear()
                    parcalar.append(parca)
                    sessiz_sure = 0
                    toplam_sure += parca_suresi
                elif ses_algilandi:
                    parcalar.append(parca)
                    sessiz_sure += parca_suresi
                    toplam_sure += parca_suresi
                    if sessiz_sure >= self.sessizlik_suresi and toplam_sure >= self.min_kayit:
                        break
                else:
                    on_tampon.append(parca)

                if toplam_sure >= self.maks_kayit:
                    break

            stream.stop()
            stream.close()

        except Exception as e:
            print(f"[HATA] Ses kayit hatasi: {e}")
            return None

        if not self._aktif:
            return None
        if not ses_algilandi or not parcalar:
            return None

        ses_verisi = np.concatenate(parcalar, axis=0)
        print(f"[*] {toplam_sure:.1f}sn ses kaydedildi, ceviriliyor...")
        baslangic = time.time()

        metin = self._metne_cevir(ses_verisi)

        if metin:
            stt_sure = time.time() - baslangic
            print(f"[*] STT suresi: {stt_sure:.1f}sn")

        return metin

    def _metne_cevir(self, ses_verisi):
        """Sesi metne cevir"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
                tmp_yol = tmp.name
                ses_int16 = (ses_verisi * 32767).astype(np.int16)
                wav_write(tmp_yol, self.ornekleme_hizi, ses_int16)
        except Exception as e:
            print(f"[HATA] WAV hatasi: {e}")
            return None

        metin = None

        if self.stt_motor == "google":
            metin = self._google_cevir(tmp_yol)
            if metin is None and self._whisper_mevcut():
                print("[!] Google basarisiz, Whisper deneniyor...")
                metin = self._whisper_cevir(tmp_yol)
        else:
            metin = self._whisper_cevir(tmp_yol)
            if metin is None:
                metin = self._google_cevir(tmp_yol)

        try:
            os.unlink(tmp_yol)
        except:
            pass

        return metin

    def _google_cevir(self, wav_yol):
        """Google Speech Recognition - ucretsiz"""
        try:
            import speech_recognition as sr
            r = sr.Recognizer()
            with sr.AudioFile(wav_yol) as kaynak:
                ses_verisi = r.record(kaynak)

            metin = r.recognize_google(ses_verisi, language="tr-TR")

            if metin and metin.strip():
                print(f"[SONUC] Google: '{metin}'")
                return metin.strip()
            return None

        except Exception as e:
            hata_tipi = type(e).__name__
            if "UnknownValueError" in hata_tipi:
                print("[!] Google: konusma anlasilamadi")
            elif "RequestError" in hata_tipi:
                print(f"[!] Google API hatasi: {e}")
            else:
                print(f"[!] Google hatasi: {e}")
            return None

    def _whisper_mevcut(self):
        try:
            import faster_whisper
            return True
        except ImportError:
            return False

    def _whisper_cevir(self, wav_yol):
        """Whisper - yerel, internet gerektirmez"""
        try:
            if self.model is None:
                from faster_whisper import WhisperModel
                self.model = WhisperModel(
                    self.model_boyut, device="cpu", compute_type="int8"
                )

            segments, info = self.model.transcribe(
                wav_yol,
                language=self.dil,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                    speech_pad_ms=400
                ),
                initial_prompt="Merhaba, ben bir sesli asistanım.",
                condition_on_previous_text=False,
                no_speech_threshold=0.6
            )

            metin_parcalari = []
            for segment in segments:
                m = segment.text.strip()
                if m and len(m) > 1:
                    metin_parcalari.append(m)

            metin = " ".join(metin_parcalari).strip()
            if metin:
                print(f"[SONUC] Whisper: '{metin}'")
                return metin
            return None

        except ImportError:
            return None
        except Exception as e:
            print(f"[HATA] Whisper hatasi: {e}")
            return None

    def durdur(self):
        self._aktif = False

    def tekrar_baslat(self):
        self._aktif = True
