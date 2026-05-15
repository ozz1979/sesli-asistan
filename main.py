"""
Sesli AI Asistan v6.0 - Ana Program
- 3 Katmanli Akilli Mimari (yerel + Gemini + yedek)
- On-bellekli TTS (aninda ses)
- Google Speech Recognition (STT)
- Minimum CPU kullanimi
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

    def _config_yukle(self):
        config_yolu = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(config_yolu):
            with open(config_yolu, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def baslangic_kontrolleri(self):
        print("\n[*] Sistem kontrolleri yapiliyor...\n")

        print("0) Guncelleme kontrol ediliyor...")
        self.guncelleyici.baslangicta_kontrol()

        ai_motor = self.config.get("ai_motor", "gemini")
        if ai_motor == "gemini":
            print("1) Google Gemini AI kontrol ediliyor...")
            bagli, modeller = self.yapay_zeka.baglanti_kontrol()
            if not bagli:
                print("[UYARI] Gemini baglantisi yok - sadece yerel komutlar calisacak")
            else:
                print(f"   [OK] Gemini bagli!")
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

        print("\n3) Mikrofonlar kontrol ediliyor...")
        mikrofonlar = self.ses_tanima.mikrofon_listele()
        if not mikrofonlar:
            print("[HATA] Mikrofon bulunamadi!")
            return False
        for idx, isim in mikrofonlar[:5]:
            print(f"   [MIC {idx}] {isim}")

        stt_motor = self.config.get("stt_motor", "google")
        if stt_motor == "google":
            print("\n4) Google Ses Tanima hazirlaniyor...")
        else:
            print("\n4) Ses tanima modeli yukleniyor...")
        self.ses_tanima.modeli_yukle()

        # Ollama arka plan kontrolu (RAM tasarrufu)
        self._ollama_kontrol()

        print("\n[OK] Tum kontroller basarili! (v6.0 - 3 Katmanli Mimari)\n")
        return True

    def _ollama_kontrol(self):
        """Ollama arka planda calisiyor mu? Gemini kullaniliyorsa uyar."""
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
       SESLI AI ASISTAN v6.0
  3 Katmanli Akilli Mimari
  Yerel + Gemini + Hizli TTS
================================================
"""
    print(LOGO)

    if not asistan.baslangic_kontrolleri():
        print("\n[HATA] Baslangic kontrolleri basarisiz.")
        input("\nCikmak icin Enter'a basin...")
        return

    asistan.sesli_yanit.konus("Merhaba! Ben senin sesli asistaninim.")

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

    # AI isleme
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

    # Sesli yanit
    t2 = time.time()
    asistan.sesli_yanit.konus(yanit.get("yanit", "Tamam!"))
    tts_sure = time.time() - t2

    toplam = time.time() - baslangic
    print(f"[SURE] AI:{ai_sure:.1f}s + Aksiyon:{aksiyon_sure:.1f}s + TTS:{tts_sure:.1f}s = Toplam:{toplam:.1f}s")


def main():
    print("Sesli AI Asistan v6.0 baslatiliyor...")
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
