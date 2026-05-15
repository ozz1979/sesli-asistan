"""
Sesli Yanit Modulu v6.0
- ON-BELLEKLI TTS: Sik kullanilan yanitlar onceden olusturulur
- pyttsx3 ANINDA yanit: Kisa yanitlar icin Windows yerel TTS (50ms!)
- edge-tts KUTUPHANE: Uzun yanitlar icin (subprocess YOK!)
- pygame ile mp3 calma
"""
import asyncio
import tempfile
import os
import time
import sys
import threading


# Sik kullanilan yanitlar - baslangicta onceden olusturulur
ON_BELLEK_YANITLARI = {
    # Temel aksiyonlar
    "aciyorum": "Aciyorum!",
    "tamam": "Tamam!",
    "anladim": "Anladim!",
    "bir saniye": "Bir saniye...",
    "hazir": "Hazir!",
    "kapattim": "Kapattim!",
    "kapatiyorum": "Kapatiyorum!",
    "ariyorum": "Ariyorum!",
    "kaydettim": "Kaydettim!",
    "kopyaladim": "Kopyaladim!",
    "yapistirdim": "Yapistirdim!",
    "geri aldim": "Geri aldim!",
    # Selamlama / Gunluk
    "merhaba": "Merhaba! Seni duyuyorum, nasil yardimci olabilirim?",
    "gunaydin": "Gunaydin! Bugun sana nasil yardimci olabilirim?",
    "iyi aksamlar": "Iyi aksamlar! Bir seyler yapmami ister misin?",
    "iyi geceler": "Iyi geceler! Yarin gorusmek uzere.",
    "gorusmek uzere": "Gorusmek uzere! Kendine iyi bak.",
    "rica ederim": "Rica ederim! Baska bir sey var mi?",
    "sorun degil": "Sorun degil! Nasil yardimci olabilirim?",
    "buradayim": "Tamam, buradayim ihtiyacin olursa!",
    # Hata / Sistem
    "anlayamadim": "Anlayamadim, baska turlu soyler misin?",
    "baglanti sorunu": "Baglanti sorunu var, tekrar dener misin?",
    # Ses kontrol
    "sesi kapatiyorum": "Sesi kapatiyorum",
    "sesi yukseltiyorum": "Sesi yukseltiyorum",
    "sesi kisiyorum": "Sesi kisiyorum",
    "ekran goruntusu": "Ekran goruntusu aliyorum",
}


class SesliYanit:
    def __init__(self, config):
        self.ses = config.get("tts_ses", "tr-TR-AhmetNeural")
        self.tts_bekleme = config.get("tts_bekleme", 0.3)
        self._pygame_hazir = False
        self._edge_tts_hazir = False
        self._pyttsx3_hazir = False
        self._loop = None
        self._on_bellek = {}  # anahtar -> dosya yolu
        self._on_bellek_klasor = None

        self._pygame_init()
        self._edge_tts_init()
        self._pyttsx3_init()

        # On-bellek olusturma (arka planda)
        if self._edge_tts_hazir:
            t = threading.Thread(target=self._on_bellek_olustur, daemon=True)
            t.start()

    def _pygame_init(self):
        try:
            import pygame
            pygame.mixer.init()
            self._pygame_hazir = True
            print("[OK] pygame ses sistemi hazir")
        except ImportError:
            print("[!] pygame yuklenmemis - kur.bat calistirin")
        except Exception as e:
            print(f"[!] pygame mixer hatasi: {e}")

    def _edge_tts_init(self):
        try:
            import edge_tts
            self._edge_tts_hazir = True
            self._loop = asyncio.new_event_loop()
            print("[OK] edge-tts kutuphane modu hazir")
        except ImportError:
            print("[!] edge-tts yuklenmemis - kur.bat calistirin")

    def _pyttsx3_init(self):
        try:
            import pyttsx3
            motor = pyttsx3.init()
            # Turkce ses var mi kontrol et
            sesler = motor.getProperty('voices')
            turkce_ses = None
            for s in sesler:
                lang_list = getattr(s, 'languages', [])
                name_lower = s.name.lower() if s.name else ""
                sid_lower = s.id.lower() if s.id else ""
                if ("tr" in name_lower or "turkish" in name_lower or
                    "tr" in sid_lower or "tolga" in name_lower or
                    any("tr" in str(l).lower() for l in lang_list)):
                    turkce_ses = s.id
                    break
            if turkce_ses:
                motor.setProperty('voice', turkce_ses)
                motor.setProperty('rate', 175)
                motor.setProperty('volume', 0.9)
                self._pyttsx3_motor = motor
                self._pyttsx3_hazir = True
                print(f"[OK] pyttsx3 Turkce ses hazir (aninda yanit)")
            else:
                # Turkce ses YOK - pyttsx3 devre disi birak
                # Ingilizce sesle konusmak yerine edge-tts'e birak
                print("[!] pyttsx3: Turkce ses bulunamadi, edge-tts kullanilacak")
                print("    Turkce ses icin: Windows Ayarlar > Zaman ve Dil > Konusma > Turkce ekleyin")
                self._pyttsx3_hazir = False
                try:
                    motor.stop()
                except:
                    pass
        except ImportError:
            print("[!] pyttsx3 yuklenmemis (opsiyonel)")
        except Exception as e:
            print(f"[!] pyttsx3 hatasi: {e}")

    def _on_bellek_olustur(self):
        """Arka planda sik kullanilan yanitlari onceden olustur"""
        try:
            import edge_tts
            self._on_bellek_klasor = os.path.join(tempfile.gettempdir(), "sesli-asistan-cache")
            os.makedirs(self._on_bellek_klasor, exist_ok=True)

            loop = asyncio.new_event_loop()
            toplam = len(ON_BELLEK_YANITLARI)
            sayac = 0

            for anahtar, metin in ON_BELLEK_YANITLARI.items():
                dosya = os.path.join(self._on_bellek_klasor, f"{anahtar}.mp3")
                if os.path.exists(dosya) and os.path.getsize(dosya) > 1000:
                    self._on_bellek[anahtar] = dosya
                    sayac += 1
                    continue
                try:
                    communicate = edge_tts.Communicate(metin, self.ses)
                    loop.run_until_complete(communicate.save(dosya))
                    if os.path.exists(dosya) and os.path.getsize(dosya) > 100:
                        self._on_bellek[anahtar] = dosya
                        sayac += 1
                except Exception as e:
                    print(f"[!] On-bellek hatasi ({anahtar}): {e}")

            loop.close()
            print(f"[OK] On-bellek hazir: {sayac}/{toplam} yanit")
        except Exception as e:
            print(f"[!] On-bellek olusturulamadi: {e}")

    def konus(self, metin):
        if not metin or not metin.strip():
            return

        kisa_metin = metin.strip()
        baslangic = time.time()

        # STRATEJI 1: On-bellekte var mi?
        bellek_anahtar = self._on_bellek_bul(kisa_metin)
        if bellek_anahtar and bellek_anahtar in self._on_bellek:
            dosya = self._on_bellek[bellek_anahtar]
            if os.path.exists(dosya):
                print(f"[TTS] On-bellekten: '{bellek_anahtar}' ({time.time()-baslangic:.0f}ms)")
                self._mp3_cal(dosya)
                return

        # STRATEJI 2: Kisa metin + pyttsx3 hazir -> aninda konuş
        if self._pyttsx3_hazir and len(kisa_metin) < 60:
            try:
                print(f"[TTS] pyttsx3 aninda: '{kisa_metin[:30]}...'")
                self._pyttsx3_motor.say(kisa_metin)
                self._pyttsx3_motor.runAndWait()
                print(f"[TTS] pyttsx3: {(time.time()-baslangic)*1000:.0f}ms")
                return
            except Exception as e:
                print(f"[!] pyttsx3 hatasi: {e}")
                # Devam et, edge-tts dene

        # STRATEJI 3: edge-tts kutuphane (hizli, yuksek kalite)
        if self._edge_tts_hazir:
            try:
                import edge_tts
                dosya = os.path.join(tempfile.gettempdir(), "asistan_yanit.mp3")
                communicate = edge_tts.Communicate(kisa_metin, self.ses)
                self._loop.run_until_complete(communicate.save(dosya))
                print(f"[TTS] edge-tts: {(time.time()-baslangic)*1000:.0f}ms")
                self._mp3_cal(dosya)
                try:
                    os.remove(dosya)
                except:
                    pass
                return
            except Exception as e:
                print(f"[!] edge-tts hatasi: {e}")

        # STRATEJI 4: Fallback - PowerShell
        self._powershell_tts(kisa_metin)

    def _on_bellek_bul(self, metin):
        """Metni on-bellek anahtariyla eslestir"""
        metin_kucuk = metin.lower().strip().rstrip("!.?,")
        # Tam eslestirme
        for anahtar, tam_metin in ON_BELLEK_YANITLARI.items():
            if metin_kucuk == tam_metin.lower().rstrip("!.?,"):
                return anahtar
        # Icerik eslestirme
        for anahtar in ON_BELLEK_YANITLARI:
            if anahtar in metin_kucuk:
                return anahtar
        return None

    def _mp3_cal(self, dosya):
        """pygame ile mp3 dosyasi cal"""
        if self._pygame_hazir:
            try:
                import pygame
                pygame.mixer.music.load(dosya)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.wait(50)
                time.sleep(self.tts_bekleme)
                return
            except Exception as e:
                print(f"[!] pygame cal hatasi: {e}")

        # Fallback: PowerShell ile cal
        try:
            import subprocess
            subprocess.run(
                ["powershell", "-Command",
                 f'(New-Object Media.SoundPlayer "{dosya}").PlaySync()'],
                timeout=30, capture_output=True
            )
        except:
            pass

    def _powershell_tts(self, metin):
        """Son care: PowerShell ile seslendir (Turkce ses tercih edilir)"""
        try:
            import subprocess
            temiz = metin.replace("'", "").replace('"', '').replace('\n', ' ').replace('`', '')[:200]
            # Once Turkce ses bulmaya calis, bulamazsa varsayilani kullan
            ps_script = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$voices = $s.GetInstalledVoices(); "
                "foreach($v in $voices){ "
                "  if($v.VoiceInfo.Culture.Name -like 'tr*'){ "
                "    $s.SelectVoice($v.VoiceInfo.Name); break "
                "  } "
                "}; "
                f"$s.Speak('{temiz}')"
            )
            subprocess.run(
                ["powershell", "-Command", ps_script],
                timeout=15, capture_output=True
            )
        except Exception as e:
            print(f"[!] PowerShell TTS hatasi: {e}")
