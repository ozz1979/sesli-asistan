"""
Sesli AI Asistan v7.3 - Ana Program
- 3 Katmanli Akilli Mimari (yerel + Gemini + yedek)
- Kullanici tanima (ilk acilista isim sorar)
- Derin Gemini baglanti testi
- On-bellekli TTS (aninda ses)
- Google Speech Recognition (STT)
"""
import json
import os
import sys
import time

from ses_tanima import SesTanima
from sesli_yanit import SesliYanit
from yapay_zeka import YapayZeka
from bilgisayar_kontrol import BilgisayarKontrol
from hafiza import Hafiza
from guncelleyici import Guncelleyici


class SesliAsistan:
    def __init__(self):
        self.config = self._config_yukle()
        self.hafiza = Hafiza(self.config.get("hafiza_dosyasi", "hafiza.json"))
        self.ses_tanima = SesTanima(self.config)
        self.sesli_yanit = SesliYanit(self.config)
        self.yapay_zeka = YapayZeka(self.config)
        self.bilgisayar = BilgisayarKontrol()
        self.guncelleyici = Guncelleyici(self.config)

        # Kullanici tanima
        self.kullanici_adi = self.hafiza.kullanici_adi_al()
        self.isim_bekleniyor = False
        self.yapay_zeka.kullanici_adi = self.kullanici_adi

    def _config_yukle(self):
        config_yolu = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_yolu):
            with open(config_yolu, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def baslangic_kontrolleri(self):
        print("\n[*] Sistem kontrolleri yapiliyor...\n")

        # 0) Guncelleme
        print("0) Guncelleme kontrol ediliyor...")
        self.guncelleyici.baslangicta_kontrol()

        ai_motor = self.config.get("ai_motor", "gemini")

        if ai_motor == "gemini":
            # 1) Gemini baglanti kontrolu
            print("\n1) Google Gemini AI kontrol ediliyor...")
            bagli, modeller = self.yapay_zeka.baglanti_kontrol()
            if not bagli:
                print("[UYARI] Gemini baglantisi yok - sadece yerel komutlar calisacak")
            else:
                print(f"   [OK] Gemini bagli!")

            # 2) GERCEK Gemini testi
            print(f"\n2) Gemini API test ediliyor...")
            test_ok, test_mesaj = self.yapay_zeka.gemini_test()
            if test_ok:
                print(f"   [OK] {test_mesaj}")
            else:
                print(f"   [UYARI] {test_mesaj}")
                print(f"   Yerel komutlar (184+) yine de calisir!")
        else:
            print("1) Ollama baglantisi kontrol ediliyor...")
            bagli, modeller = self.yapay_zeka.baglanti_kontrol()
            if not bagli:
                print("[UYARI] Ollama calismiyor - sadece yerel komutlar calisacak")
            else:
                print(f"   [OK] Ollama bagli!")

            print(f"\n2) AI modeli kontrol ediliyor...")
            hazir, mesaj = self.yapay_zeka.model_kontrol()
            if not hazir:
                print(f"   [!] {mesaj} - Yerel komutlar yine de calisir")
            else:
                print(f"   [OK] {mesaj}")

        # 3) Mikrofon
        print("\n3) Mikrofonlar kontrol ediliyor...")
        mikrofonlar = self.ses_tanima.mikrofon_listele()
        if not mikrofonlar:
            print("[HATA] Mikrofon bulunamadi!")
            return False
        for idx, isim in mikrofonlar[:5]:
            print(f"   [MIC {idx}] {isim}")

        # 4) STT
        stt_motor = self.config.get("stt_motor", "google")
        if stt_motor == "google":
            print("\n4) Google Ses Tanima hazirlaniyor...")
        else:
            print("\n4) Ses tanima modeli yukleniyor...")
        self.ses_tanima.modeli_yukle()

        # Ollama RAM uyarisi
        self._ollama_kontrol()

        # 5) Kullanici tanima
        if self.kullanici_adi:
            print(f"\n5) Kullanici: {self.kullanici_adi}")
        else:
            print(f"\n5) Ilk kullanim - kullanici adi sorulacak")
            self.isim_bekleniyor = True

        print(f"\n[OK] Tum kontroller basarili! (v7.3 - 3 Katmanli Mimari)\n")
        return True

    def _ollama_kontrol(self):
        if self.config.get("ai_motor") != "gemini":
            return
        try:
            import subprocess
            result = subprocess.run(
                ["tasklist", "/FI", "IMAGENAME eq ollama.exe"],
                capture_output=True, text=True, timeout=5
            )
            if "ollama.exe" in result.stdout.lower():
                print("\n[!] UYARI: Ollama arka planda calisiyor (~4GB RAM kullaniyor)")
                print("    Gemini kullandiginiz icin Ollama'ya gerek yok.")
                print("    RAM tasarrufu icin: taskkill /f /im ollama.exe")
        except:
            pass


def gui_baslat(asistan):
    from PyQt6.QtWidgets import QApplication
    from arayuz import JarvisPencere

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    pencere = JarvisPencere(asistan)
    pencere.show()
    sys.exit(app.exec())


def konsol_baslat(asistan):
    LOGO = r"""
================================================
       SESLI AI ASISTAN v7.3
  3 Katmanli Akilli Mimari
  Yerel + Gemini + Hizli TTS
  Kullanici Tanima + Otomatik Guncelleme
================================================
"""
    print(LOGO)

    if not asistan.baslangic_kontrolleri():
        print("\n[HATA] Baslangic kontrolleri basarisiz.")
        input("\nCikmak icin Enter'a basin...")
        return

    # Kullanici tanima
    if asistan.isim_bekleniyor:
        asistan.sesli_yanit.konus("Merhaba! Ben senin sesli asistaninim. Adini ogrenebilir miyim?")
        time.sleep(1.5)  # Hoparlor yankisi dusmesin
        print("\n[*] Adinizi soyleyin...")
        # 3 deneme hakkı
        for _deneme in range(3):
            isim = asistan.ses_tanima.dinle_ve_cevir()
            if isim:
                isim = isim.strip().title()
                # Yanki filtresi
                yanki = ["merhaba", "asistan", "ogrenebilir", "yardimci", "miyim", "hello"]
                if len(isim) >= 2 and not any(k in isim.lower() for k in yanki):
                    isim_parca = isim.split()[0] if " " in isim else isim
                    asistan.hafiza.kullanici_adi_kaydet(isim_parca)
                    asistan.kullanici_adi = isim_parca
                    asistan.yapay_zeka.kullanici_adi = isim_parca
                    asistan.isim_bekleniyor = False
                    asistan.sesli_yanit.konus(f"Memnun oldum {isim_parca}! Sana nasil yardimci olabilirim?")
                    break
                else:
                    print(f"[!] Yanki/gurultu algilandi: '{isim}', tekrar soruluyor...")
                    asistan.sesli_yanit.konus("Adini net duyamadim. Sadece adini soyler misin?")
                    time.sleep(1.0)
            else:
                asistan.sesli_yanit.konus("Duyamadim, tekrar soyler misin?")
                time.sleep(1.0)
        else:
            asistan.sesli_yanit.konus("Sorun degil, daha sonra adimi degistir diyebilirsin.")
            asistan.isim_bekleniyor = False
    else:
        asistan.sesli_yanit.konus(f"Merhaba {asistan.kullanici_adi}! Seni dinliyorum.")

    while True:
        try:
            metin = asistan.ses_tanima.dinle_ve_cevir()
            if metin:
                from yapay_zeka import turkce_normalize
                metin_kucuk = turkce_normalize(metin.lower().strip())
                cikis = ["kapat kendini", "kendini kapat", "cikis", "gule gule"]
                if any(k in metin_kucuk for k in cikis):
                    asistan.sesli_yanit.konus("Gorusmek uzere!")
                    break
                _isle(asistan, metin)
        except KeyboardInterrupt:
            asistan.sesli_yanit.konus("Gorusmek uzere!")
            break
        except Exception as e:
            print(f"[HATA] {e}")
            time.sleep(1)


def _isle(asistan, metin):
    baslangic = time.time()

    hafiza_ozeti = asistan.hafiza.hafiza_ozeti()
    t0 = time.time()
    yanit = asistan.yapay_zeka.komut_isle(metin, hafiza_ozeti)
    ai_sure = time.time() - t0

    if not yanit:
        asistan.sesli_yanit.konus("Anlayamadim, tekrar soyler misin?")
        return

    # Aksiyonlari calistir
    t1 = time.time()
    aksiyonlar = yanit.get("aksiyonlar", [])
    basarili = True
    for aksiyon in aksiyonlar:
        fonk = aksiyon.get("fonksiyon")
        params = aksiyon.get("parametreler", {})
        if fonk:
            ok, sonuc = asistan.bilgisayar.calistir(fonk, params)
            if not ok:
                basarili = False
    aksiyon_sure = time.time() - t1

    # Hafiza guncelle
    ogrenme = yanit.get("ogren")
    if ogrenme and isinstance(ogrenme, dict):
        for k, v in ogrenme.items():
            asistan.hafiza.ogren(k, v)
    asistan.hafiza.gecmis_ekle(metin, str(aksiyonlar), basarili)

    # Isim degistirme komutu
    yanit_metni = yanit.get("yanit", "Tamam!")
    if yanit_metni == "__ISIM_DEGISTIR__":
        asistan.sesli_yanit.konus("Tabii! Adini soyler misin?")
        print("\n[*] Adinizi soyleyin...")
        isim = asistan.ses_tanima.dinle_ve_cevir()
        if isim:
            isim = isim.strip().title()
            asistan.hafiza.kullanici_adi_kaydet(isim)
            asistan.kullanici_adi = isim
            asistan.yapay_zeka.kullanici_adi = isim
            asistan.sesli_yanit.konus(f"Memnun oldum {isim}! Seni hatirlayacagim.")
        else:
            asistan.sesli_yanit.konus("Duyamadim, daha sonra tekrar dene.")
        return

    # Sesli yanit
    t2 = time.time()
    asistan.sesli_yanit.konus(yanit_metni)
    tts_sure = time.time() - t2

    toplam = time.time() - baslangic
    print(f"[SURE] AI:{ai_sure:.1f}s + Aksiyon:{aksiyon_sure:.1f}s + TTS:{tts_sure:.1f}s = Toplam:{toplam:.1f}s")


def main():
    print("Sesli AI Asistan v7.3 baslatiliyor...")
    asistan = SesliAsistan()

    gui_var = True
    try:
        from PyQt6.QtWidgets import QApplication
    except ImportError:
        gui_var = False
        print("[!] PyQt6 bulunamadi, konsol modunda baslatiliyor...")

    if "--konsol" in sys.argv:
        gui_var = False

    if gui_var:
        gui_baslat(asistan)
    else:
        konsol_baslat(asistan)


if __name__ == "__main__":
    main()
