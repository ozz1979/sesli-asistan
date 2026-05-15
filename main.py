"""
ATLAS - Ana Orkestratör
========================
Beyin Karşılığı: Beyin Sapı + Talamus
Görev: Tüm beyin modüllerini koordine etme, ana döngü

Beyin sapı temel yaşam fonksiyonlarını yönetir,
talamus duyusal bilgiyi doğru bölgelere yönlendirir.
Bu modül tüm ATLAS bileşenlerini başlatır ve koordine eder.
"""

import sys
import os
import json
import time
import threading
import logging
from datetime import datetime

# ============================================================
# LOGGING AYARI
# ============================================================

def logging_ayarla(seviye="INFO"):
    log_format = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, seviye, logging.INFO),
        format=log_format,
        handlers=[
            logging.FileHandler("atlas.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger("ATLAS")

# ============================================================
# CONFIG YÜKLEME
# ============================================================

CONFIG_DOSYA = "config.json"

def config_yukle():
    """Config dosyasını yükle, yoksa varsayılan oluştur"""
    if os.path.exists(CONFIG_DOSYA):
        try:
            with open(CONFIG_DOSYA, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Config yükleme hatası: {e}")

    # Varsayılan config
    varsayilan = {
        "version": "8.2",
        "asistan_adi": "ATLAS",
        "tetik_kelime": "atlas",
        "kullanici": {"ad": "", "ses_profili": {}, "tercihler": {}},
        "stt": {
            "motor": "google", "dil": "tr-TR", "enerji_esigi": 300,
            "dinamik_esik": True, "kalibrasyon_suresi": 1.5,
            "dinleme_suresi": 8, "sessizlik_suresi": 1.5
        },
        "tts": {
            "motor": "edge-tts", "ses": "tr-TR-AhmetNeural",
            "hiz": "+0%", "on_bellek": True, "on_bellek_esik": 25
        },
        "ai": {
            "birincil": "gemini", "yedek": "ollama",
            "gemini_model": "gemini-2.0-flash", "gemini_api_key": "",
            "gemini_yedek_model": "gemini-1.5-flash",
            "ollama_model": "llama3", "ollama_url": "http://localhost:11434",
            "max_token": 100, "sicaklik": 0.7, "timeout": 8
        },
        "hafiza": {
            "calisma_bellegi_boyutu": 7, "oturum_kayit": True,
            "epizodik_kayit": True, "semantik_kayit": True,
            "prosedurel_kayit": True, "konsolidasyon_esigi": 3
        },
        "dikkat": {
            "aktif_mod_suresi": 45, "pasif_dinleme": True,
            "tetik_hassasiyeti": 0.6
        },
        "sistem": {
            "otomatik_baslat": False, "guncelleme_kontrol": True,
            "github_repo": "ozz1979/sesli-asistan", "log_seviyesi": "INFO",
            "log_dosyasi": "atlas.log"
        }
    }
    config_kaydet(varsayilan)
    return varsayilan

def config_kaydet(config):
    """Config dosyasını kaydet"""
    try:
        with open(CONFIG_DOSYA, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Config kaydetme hatası: {e}")


# ============================================================
# ATLAS BEYİN — ANA SINIF
# ============================================================

class AtlasBeyin:
    """
    ATLAS'ın beyni — tüm modülleri koordine eder.
    """

    def __init__(self, config, arayuz=None):
        self.config = config
        self.arayuz = arayuz  # GUI sinyalleri
        self._calisiyor = False
        self._durum = "baslatiyor"

        # Hafıza dizini oluştur
        os.makedirs("hafiza", exist_ok=True)

        # ── Modülleri oluştur ──
        from hafiza_sistemi import HafizaSistemi
        from kalip_motoru import KalipMotoru
        from dikkat_filtresi import DikkatFiltresi
        from duygu_analizi import DuyguAnalizi
        from ses_algilama import SesAlgilama
        from dil_anlama import DilAnlama
        from konusma_uretimi import KonusmaUretimi
        from karar_merkezi import KararMerkezi
        from kisilik_motoru import KisilikMotoru
        from kimlik_tanima import KimlikTanima
        from guncelleyici import Guncelleyici

        self.hafiza = HafizaSistemi(config)
        self.kalip = KalipMotoru(self.hafiza)
        self.dikkat = DikkatFiltresi(config)
        self.duygu = DuyguAnalizi()
        self.ses = SesAlgilama(config)
        self.dil = DilAnlama(self.ses, config)
        self.konusma = KonusmaUretimi(config)
        self.karar = KararMerkezi(self.kalip, self.hafiza, self.duygu, config)
        self.kisilik = KisilikMotoru(self.hafiza)
        self.kimlik = KimlikTanima(self.hafiza)
        self.guncelleyici = Guncelleyici(config)

        # Config'den kullanıcı adını hafızaya aktar
        config_ad = config.get("kullanici", {}).get("ad", "")
        if config_ad:
            self.hafiza.kullanici_bilgisi_kaydet("ad", config_ad)

    def baslat(self):
        """ATLAS'ı başlat"""
        self._calisiyor = True

        # GUI bilgilendir
        self._gui_durum("Başlatılıyor...")
        self._gui_mesaj("sistem", "ATLAS v{} başlatılıyor...".format(
            self.config.get("version", "8.0")))

        # 1. Mikrofon başlat
        self._gui_durum("Mikrofon hazırlanıyor...")
        if not self.ses.baslat():
            self._gui_hata(f"Mikrofon hatası: {self.ses.hata}")
            self._gui_mesaj("sistem", f"⚠️ Mikrofon hatası: {self.ses.hata}")
            return False

        self._gui_mesaj("sistem", "✅ Mikrofon hazır")

        # 2. TTS ön bellek
        self._gui_durum("Ses motoru hazırlanıyor...")
        self._gui_mesaj("sistem", "✅ Ses motoru hazır")

        # 3. AI kontrol
        api_key = self.config.get("ai", {}).get("gemini_api_key", "")
        if api_key:
            masked = api_key[:8] + "..." + api_key[-4:]
            self._gui_mesaj("sistem", f"✅ Gemini AI hazır ({masked})")
        else:
            self._gui_mesaj("sistem", "⚠️ Gemini API key ayarlanmamış — config.json'da 'gemini_api_key' alanını doldurun")

        # 4. Hafıza durumu
        h_durum = self.hafiza.durum_ozeti()
        self._gui_mesaj("sistem", f"✅ Hafıza sistemi hazır (Epizodik: {h_durum['epizodik_oturum']} oturum)")

        # 5. Güncelleme kontrolü
        self._gui_durum("Güncelleme kontrol ediliyor...")
        threading.Thread(target=self._guncelleme_kontrol, daemon=True).start()

        # 6. TTS ön bellek bekle
        self._gui_durum("TTS ön bellek hazırlanıyor...")
        self.konusma.on_bellek_hazir.wait(timeout=15)

        # TÜMLKONTROLLER BAŞARILI
        surum = self.config.get("version", "8.0")
        self._gui_mesaj("sistem", f"🧠 Tüm kontroller başarılı! ATLAS v{surum} hazır.")
        self._gui_surum(surum)

        # 7. İlk tanışma veya karşılama
        if not self.kimlik.kullanici_tanimli_mi():
            self._ilk_tanisma()
        else:
            self._karsilama()

        # 8. Ana döngüyü başlat
        self._ana_dongu_thread = threading.Thread(target=self._ana_dongu, daemon=True)
        self._ana_dongu_thread.start()

        return True

    def _ilk_tanisma(self):
        """İlk kez çalışıyor — kullanıcıdan adını öğren"""
        from dikkat_filtresi import DikkatModu

        self._gui_durum("İlk tanışma — isim öğrenme")
        self._gui_mod("isim")
        self.dikkat.mod = DikkatModu.ISIM_OGRENME

        karsilama = "Merhaba! Ben ATLAS, senin kişisel yapay zeka asistanınım. Seninle tanışmak istiyorum. Adın ne?"
        self._gui_mesaj("asistan", karsilama)
        self.konusma.konus(karsilama)

        # İsim dinle (3 deneme)
        for deneme in range(3):
            self._gui_durum(f"İsim bekleniyor... (deneme {deneme + 1}/3)")
            isim, guven = self.dil.isim_dinle(timeout=10)

            if isim and guven > 0.4:
                # İsmi onayla
                onay_mesaj = f"Adın {isim}, doğru mu?"
                self._gui_mesaj("kullanici", f"[İsim: {isim} (güven: {guven:.0%})]")
                self._gui_mesaj("asistan", onay_mesaj)
                self.konusma.konus(onay_mesaj)

                # Onay dinle
                self._gui_durum("Onay bekleniyor...")
                onay_audio = self.ses.dinle(timeout=5)
                if onay_audio:
                    onay_text = self.ses.stt_google(onay_audio)
                    if onay_text:
                        onay_lower = onay_text.lower()
                        if any(k in onay_lower for k in ["evet", "doğru", "tamam", "aynen", "yes"]):
                            # İsim onaylandı
                            self.kimlik.kullanici_kaydet(isim)
                            self.config.setdefault("kullanici", {})["ad"] = isim
                            config_kaydet(self.config)

                            tebrik = f"Memnun oldum {isim}! Bana istediğin zaman 'Atlas' diye seslenebilirsin."
                            self._gui_mesaj("asistan", tebrik)
                            self.konusma.konus(tebrik)
                            self.dikkat.mod = DikkatModu.AKTIF
                            self._gui_mod("aktif")
                            return
                        elif any(k in onay_lower for k in ["hayır", "yanlış", "değil"]):
                            tekrar = "Pardon, tekrar söyler misin? Adın ne?"
                            self._gui_mesaj("asistan", tekrar)
                            self.konusma.konus(tekrar)
                            continue

                # Onay alınamadı — yine de kaydet
                self.kimlik.kullanici_kaydet(isim)
                self.config.setdefault("kullanici", {})["ad"] = isim
                config_kaydet(self.config)

                mesaj = f"Tamam {isim}, memnun oldum! Bana 'Atlas' diye seslenebilirsin."
                self._gui_mesaj("asistan", mesaj)
                self.konusma.konus(mesaj)
                self.dikkat.mod = DikkatModu.AKTIF
                self._gui_mod("aktif")
                return

        # 3 denemede isim alınamadı
        self._gui_mesaj("asistan", "Şu an adını anlayamadım ama sorun değil. Daha sonra tekrar deneriz. Bana 'Atlas' diye seslenebilirsin!")
        self.konusma.konus("Şu an adını anlayamadım ama sorun değil. Bana Atlas diye seslenebilirsin!")
        self.dikkat.mod = DikkatModu.AKTIF
        self._gui_mod("aktif")

    def _karsilama(self):
        """Tanınan kullanıcıyı karşıla"""
        from dikkat_filtresi import DikkatModu

        ad = self.kimlik.kullanici_adi()
        saat = datetime.now().hour

        if saat < 6:
            selamlama = f"İyi geceler {ad}! Geç saatte mi çalışıyorsun?"
        elif saat < 12:
            selamlama = f"Günaydın {ad}! ATLAS hazır, seni dinliyorum."
        elif saat < 18:
            selamlama = f"İyi günler {ad}! ATLAS hazır, nasıl yardımcı olabilirim?"
        else:
            selamlama = f"İyi akşamlar {ad}! ATLAS hazır, seni dinliyorum."

        self._gui_mesaj("asistan", selamlama)
        self.konusma.konus(selamlama)
        self.dikkat.mod = DikkatModu.AKTIF
        self._gui_mod("aktif")

    def _ana_dongu(self):
        """Ana dinleme döngüsü"""
        from dikkat_filtresi import DikkatModu

        logger.info("Ana döngü başladı")

        while self._calisiyor:
            try:
                # Durum güncelle
                mod = self.dikkat.mod
                self._gui_durum("🎙️ Dinleniyor..." if mod in (DikkatModu.AKTIF, DikkatModu.PASIF) else "Bekliyor...")
                self._gui_mod(mod.value)
                self._gui_bellek(self.hafiza.durum_ozeti())

                # Dinle
                sonuc = self.dil.dinle_ve_anla()

                if not sonuc["basarili"]:
                    continue

                metin = sonuc["duzeltilmis"]
                if not metin:
                    continue

                # Dikkat filtresi — RAS
                filtre = self.dikkat.filtrele(metin)
                islem = filtre["islem"]
                temiz_metin = filtre["metin"]

                logger.info(f"RAS: islem={islem}, metin='{temiz_metin}'")

                if islem == "yoksay":
                    continue

                if islem == "isim_cevap":
                    # İsim öğrenme modunda — main logic'te halledilir
                    continue

                if islem == "tetik":
                    # Sadece "Atlas" dedi — yanıt ver
                    self._gui_mesaj("kullanici", metin)
                    ad = self.kimlik.kullanici_adi()
                    tetik_yanit = f"Evet {ad}, buradayım! Seni dinliyorum." if ad else "Evet, buradayım! Seni dinliyorum."
                    self._gui_mesaj("asistan", tetik_yanit)
                    self._gui_mod("aktif")
                    self.konusma.on_bellekten_konus(tetik_yanit)
                    continue

                if islem in ("komut", "tetik_komut"):
                    # Komutu işle
                    self._komut_isle(sonuc["ham_metin"], temiz_metin, sonuc["niyet"])

            except Exception as e:
                logger.error(f"Ana döngü hatası: {e}", exc_info=True)
                time.sleep(1)

    def _komut_isle(self, ham, metin, niyet):
        """Bir komutu işle — tam beyin pipeline'ı"""
        from dikkat_filtresi import DikkatModu

        # GUI: kullanıcı mesajı
        self._gui_mesaj("kullanici", ham)
        self._gui_durum("💭 Düşünüyor...")
        self._gui_mod("mesgul")
        self.dikkat.mod = DikkatModu.MESGUL

        # 1. Duygu analizi (Amigdala)
        duygu_sonucu = self.duygu.analiz_et(metin)
        self._gui_duygu(duygu_sonucu.get("duygu", "notr"))

        # 2. Hafızaya kaydet
        niyet_adi = niyet.get("niyet") if niyet else None
        self.hafiza.kullanici_soyledi(metin, niyet_adi, duygu_sonucu.get("duygu"))

        # 3. Karar merkezi (Prefrontal Korteks — Sistem 1 veya 2)
        karar = self.karar.karar_ver(metin, niyet, duygu_sonucu)
        yanit = karar["yanit"]
        yol = karar["yol"]

        # 4. Duygu uyumu (Amigdala feedback)
        yanit = self.duygu.yanit_tonu_ayarla(yanit, duygu_sonucu)

        # 5. Kişilik uyumu (Ayna Nöronlar)
        self.kisilik.etkilesim_kaydet(metin, niyet)
        yanit = self.kisilik.yanit_ayarla(yanit)

        # 6. Hafızaya kaydet
        self.hafiza.asistan_soyledi(yanit, niyet_adi)

        # 7. GUI: asistan yanıtı
        yol_emoji = {"sistem1": "⚡", "sistem2": "🧠", "fallback": "🔄"}.get(yol, "")
        self._gui_mesaj("asistan", yanit)
        self._gui_durum(f"{yol_emoji} {yol} ({karar['sure_ms']:.0f}ms)")
        self._gui_mod("aktif")
        self._gui_bellek(self.hafiza.durum_ozeti())

        # 8. Konuş (Broca alanı)
        self.dikkat.mod = DikkatModu.MESGUL  # Konuşurken yeni girdi alma
        self.konusma.konus(yanit)

        # 9. Tekrar aktif moda geç
        self.dikkat.mod = DikkatModu.AKTIF
        self._gui_durum("🎙️ Dinleniyor...")
        self._gui_mod("aktif")

    def _guncelleme_kontrol(self):
        """Arka planda güncelleme kontrolü"""
        try:
            if self.guncelleyici.kontrol_et():
                durum = self.guncelleyici.guncelleme_durumu
                self._gui_mesaj("sistem", f"🔄 {durum}")
            else:
                logger.debug("Güncelleme yok, güncel sürüm")
        except Exception as e:
            logger.debug(f"Güncelleme kontrol hatası: {e}")

        # Periyodik kontrolü başlat
        self.guncelleyici.periyodik_kontrol_baslat()

    def durdur(self):
        """ATLAS'ı durdur"""
        self._calisiyor = False
        self.hafiza.oturum_kapat()
        self.ses.durdur()
        self.konusma.temizle()
        logger.info("ATLAS durduruldu")

    # ── GUI Yardımcıları ──

    def _gui_mesaj(self, rol, mesaj):
        if self.arayuz:
            self.arayuz.mesaj_ekle.emit(rol, mesaj)
        logger.info(f"[{rol}] {mesaj}")

    def _gui_durum(self, durum):
        if self.arayuz:
            self.arayuz.durum_guncelle.emit(durum)

    def _gui_mod(self, mod):
        if self.arayuz:
            self.arayuz.mod_guncelle.emit(mod)

    def _gui_bellek(self, durum):
        if self.arayuz:
            self.arayuz.bellek_guncelle.emit(durum)

    def _gui_hata(self, hata):
        if self.arayuz:
            self.arayuz.hata_goster.emit(hata)

    def _gui_surum(self, surum):
        if self.arayuz:
            self.arayuz.surum_goster.emit(surum)

    def _gui_duygu(self, duygu):
        if self.arayuz:
            self.arayuz.duygu_guncelle.emit(duygu)


# ============================================================
# ANA GİRİŞ NOKTASI
# ============================================================

def main():
    """ATLAS başlat"""
    # Config yükle
    config = config_yukle()
    logging_ayarla(config.get("sistem", {}).get("log_seviyesi", "INFO"))
    logger.info("=" * 50)
    logger.info(f"ATLAS v{config.get('version', '?')} başlatılıyor")
    logger.info("=" * 50)

    # PyQt6 uygulama
    from PyQt6.QtWidgets import QApplication
    from arayuz import AtlasArayuz

    app = QApplication(sys.argv)
    app.setApplicationName("ATLAS")

    # Arayüz oluştur
    pencere = AtlasArayuz()
    pencere.show()

    # Beyin oluştur ve başlat
    beyin = AtlasBeyin(config, pencere.sinyaller)

    def baslat_thread():
        time.sleep(0.5)  # GUI'nin çizmesini bekle
        beyin.baslat()

    threading.Thread(target=baslat_thread, daemon=True).start()

    # Kapanışta temizlik
    def kapanista():
        beyin.durdur()

    app.aboutToQuit.connect(kapanista)

    # Uygulama döngüsü
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
