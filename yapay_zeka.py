"""
Yapay Zeka Modulu v6.0
- 3 KATMANLI AKILLI SISTEM:
  Katman 1: Aninda yerel eslestirme (0ms, AI yok, CPU yok)
  Katman 2: Google Gemini Flash (1-2sn, bulut)
  Katman 3: Ollama yedek (internet yoksa)
- 50+ yerel komut kalıbı
- Kisa optimize prompt = hizli yanit
- Guvenilir JSON parse
"""
import json
import requests
import re
import time
from kaliplar import yerel_kalip_esle


# =============================================
# KATMAN 1: YEREL KOMUT HARITASI (ANINDA YANIT)
# =============================================
# Uygulama isimleri -> bilgisayar_kontrol'daki isimler
UYGULAMA_HARITASI = {
    "not defteri": "notepad", "notepad": "notepad", "metin editoru": "notepad",
    "chrome": "chrome", "tarayici": "chrome", "google chrome": "chrome",
    "internet": "chrome", "web": "chrome", "browser": "chrome",
    "hesap makinesi": "hesap makinesi", "hesap makine": "hesap makinesi",
    "kalkulator": "hesap makinesi", "calculator": "hesap makinesi",
    "paint": "paint", "cizim": "paint", "boyama": "paint",
    "word": "word", "excel": "excel", "powerpoint": "powerpoint",
    "dosya": "explorer", "explorer": "explorer", "klasor": "explorer",
    "dosya yoneticisi": "explorer", "belgelerim": "explorer",
    "ayarlar": "ayarlar", "settings": "ayarlar", "sistem ayarlari": "ayarlar",
    "gorev yoneticisi": "gorev yoneticisi", "task manager": "gorev yoneticisi",
    "komut satiri": "cmd", "terminal": "cmd", "cmd": "cmd",
    "powershell": "cmd",
    "spotify": "spotify", "muzik": "spotify",
    "firefox": "firefox",
    "discord": "discord",
    "whatsapp": "whatsapp",
    "telegram": "telegram",
    "youtube": "youtube",
    "vlc": "vlc", "video oynatici": "vlc",
}

# Populer URL kaliplari
URL_HARITASI = {
    "youtube": "https://www.youtube.com",
    "gmail": "https://mail.google.com",
    "google": "https://www.google.com",
    "twitter": "https://twitter.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "whatsapp web": "https://web.whatsapp.com",
    "github": "https://github.com",
    "linkedin": "https://www.linkedin.com",
    "harita": "https://maps.google.com",
    "google maps": "https://maps.google.com",
    "hava durumu": "https://www.google.com/search?q=hava+durumu",
}


# Gemini icin KISA sistem promptu (daha kisa = daha hizli)
SISTEM_PROMPTU = """Turkce sesli asistansin. JSON yanit ver.
{"yanit":"kisa cevap","aksiyonlar":[{"fonksiyon":"ad","parametreler":{}}],"ogren":{"k":"v"}}
Fonksiyonlar: uygulama_ac(isim), web_ara(sorgu), url_ac(url), dosya_bul(isim), ekran_goruntusu(), metin_yaz(metin), tus_bas(tuslar[]), bilgisayar_bilgi(), islem_kapat(isim), ses_ayarla(seviye 0-100)
"ogren": kullanici tercihlerini kaydet. Aksiyon yoksa aksiyonlar:[] yaz."""


def turkce_normalize(metin):
    """Turkce karakterleri ASCII'ye cevir (eslestirme icin)
    ç->c, ğ->g, ı->i, ö->o, ş->s, ü->u, İ->i
    """
    cevrim = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return metin.translate(cevrim)


class YapayZeka:
    def __init__(self, config):
        self.ai_motor = config.get("ai_motor", "gemini")
        self.gemini_api_key = config.get("gemini_api_key", "")
        self.gemini_model = config.get("gemini_model", "gemini-2.0-flash")
        self.model = config.get("ollama_model", "llama3")
        self.url = config.get("ollama_url", "http://localhost:11434")
        self.maks_gecmis = config.get("maks_sohbet_gecmisi", 10)
        self.sohbet_gecmisi = []

    def baglanti_kontrol(self):
        if self.ai_motor == "gemini":
            return self._gemini_kontrol()
        else:
            return self._ollama_kontrol()

    def _gemini_kontrol(self):
        if not self.gemini_api_key or self.gemini_api_key == "BURAYA_API_ANAHTARINIZI_YAZIN":
            print("[!] Gemini API anahtari bos! config.json'a ekleyin.")
            print("    Ucretsiz anahtar: https://aistudio.google.com/apikey")
            return False, []
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={self.gemini_api_key}"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                return True, [self.gemini_model]
            else:
                print(f"[HATA] Gemini API hatasi: {r.status_code}")
                return False, []
        except Exception as e:
            print(f"[HATA] Gemini baglanti hatasi: {e}")
            return False, []

    def _ollama_kontrol(self):
        try:
            r = requests.get(f"{self.url}/api/tags", timeout=5)
            if r.status_code == 200:
                modeller = [m["name"] for m in r.json().get("models", [])]
                return True, modeller
        except:
            pass
        return False, []

    def model_kontrol(self):
        if self.ai_motor == "gemini":
            if not self.gemini_api_key or self.gemini_api_key == "BURAYA_API_ANAHTARINIZI_YAZIN":
                return False, "Gemini API anahtari gerekli! config.json icine yazin."
            return True, f"Gemini {self.gemini_model} hazir"
        else:
            try:
                r = requests.get(f"{self.url}/api/tags", timeout=5)
                if r.status_code == 200:
                    modeller = [m["name"] for m in r.json().get("models", [])]
                    for m in modeller:
                        if self.model in m:
                            return True, "Model hazir"
                    return False, f"'{self.model}' bulunamadi"
            except:
                return False, "Ollama baglantisi yok"

    def model_yukle(self):
        if self.ai_motor == "gemini":
            return True
        print(f"[*] '{self.model}' modeli yukleniyor...")
        try:
            r = requests.post(
                f"{self.url}/api/pull",
                json={"name": self.model},
                timeout=600, stream=True
            )
            for line in r.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        completed = data.get("completed", 0)
                        total = data.get("total", 0)
                        if total > 0:
                            print(f"\r   %{int(completed/total*100)}", end="", flush=True)
                    except:
                        pass
            print("\n[OK] Model yuklendi!")
            return True
        except Exception as e:
            print(f"\n[HATA] Model yuklenemedi: {e}")
            return False

    # =============================================
    # ANA KOMUT ISLEME - 3 KATMANLI
    # =============================================
    def komut_isle(self, metin, hafiza_ozeti=""):
        metin_temiz = metin.strip()
        metin_kucuk = turkce_normalize(metin_temiz.lower())

        # KATMAN 1: Yerel eslestirme (ANINDA - 0ms)
        hizli = self._yerel_esle(metin_kucuk, metin_temiz)
        if hizli:
            print(f"[HIZLI] Yerel eslestirme: '{metin_temiz[:40]}' -> aninda!")
            return hizli

        # KATMAN 2: Gemini AI (HIZLI - 1-2sn)
        if self.ai_motor == "gemini" and self.gemini_api_key:
            sonuc = self._gemini_isle(metin_temiz, hafiza_ozeti)
            if sonuc:
                return sonuc

        # KATMAN 3: Ollama yedek (internet yoksa)
        return self._ollama_isle(metin_temiz, hafiza_ozeti)

    # =============================================
    # KATMAN 1: YEREL ESLESTIRME (50+ KALIP)
    # =============================================
    def _yerel_esle(self, mk, mo):
        """Yerel komut eslestirme - AI cagirmadan aninda yanit
        mk = turkce_normalize edilmis kucuk harf metin, mo = metin orijinal"""

        # ONCE: Turkce gundelik konusma kaliplarini kontrol et (150+ kalip)
        kalip_sonuc = yerel_kalip_esle(mk, mo)
        if kalip_sonuc:
            return kalip_sonuc

        # --- UYGULAMA ACMA ---
        acma_kelimeleri = ["ac", "calistir", "baslat", "getir", "goster"]
        if any(k in mk for k in acma_kelimeleri):
            # Once URL haritasinda ara
            for anahtar, url in URL_HARITASI.items():
                if anahtar in mk:
                    return {
                        "yanit": f"{anahtar.title()} aciyorum",
                        "aksiyonlar": [{"fonksiyon": "url_ac", "parametreler": {"url": url}}]
                    }
            # Sonra uygulama haritasinda ara
            for anahtar, uygulama in UYGULAMA_HARITASI.items():
                if anahtar in mk:
                    return {
                        "yanit": f"{anahtar.title()} aciyorum",
                        "aksiyonlar": [{"fonksiyon": "uygulama_ac", "parametreler": {"isim": uygulama}}]
                    }

        # --- UYGULAMA KAPATMA ---
        if any(k in mk for k in ["kapat", "sonlandir", "bitir"]):
            if any(k in mk for k in ["bilgisayar", "pc", "sistemi"]):
                return {"yanit": "Bilgisayari kapatiyorum", "aksiyonlar": [{"fonksiyon": "bilgisayar_kapat", "parametreler": {}}]}
            for anahtar, uygulama in UYGULAMA_HARITASI.items():
                if anahtar in mk:
                    exe_map = {
                        "chrome": "chrome.exe", "firefox": "firefox.exe",
                        "notepad": "notepad.exe", "word": "winword.exe",
                        "excel": "excel.exe", "paint": "mspaint.exe",
                        "explorer": "explorer.exe", "discord": "discord.exe",
                        "spotify": "spotify.exe", "vlc": "vlc.exe",
                    }
                    exe = exe_map.get(uygulama, f"{uygulama}.exe")
                    return {
                        "yanit": f"{anahtar.title()} kapatiyorum",
                        "aksiyonlar": [{"fonksiyon": "islem_kapat", "parametreler": {"isim": exe}}]
                    }

        # --- WEB ARAMA ---
        arama_kaliplari = [
            ("internette ara", "internette ara"),
            ("googleda ara", "googleda ara"),
            ("webde ara", "webde ara"),
            ("aratir misin", "aratir misin"),
            ("arar misin", "arar misin"),
            ("bak bakalim", "bak bakalim"),
        ]
        for kalip, _ in arama_kaliplari:
            if kalip in mk:
                sorgu = mk
                for sil in ["internette", "webde", "googleda", "ara", "aratir misin",
                            "arar misin", "bak bakalim", "bir", "misin", "lutfen"]:
                    sorgu = sorgu.replace(sil, "")
                sorgu = sorgu.strip()
                if sorgu and len(sorgu) > 1:
                    return {
                        "yanit": f"Ariyorum",
                        "aksiyonlar": [{"fonksiyon": "web_ara", "parametreler": {"sorgu": sorgu}}]
                    }

        # Genel "... ara" kalıbı
        if mk.endswith(" ara") or " ara " in mk or "arat" in mk:
            sorgu = mk.replace("ara", "").replace("arat", "").replace("internette", "").strip()
            if sorgu and len(sorgu) > 2:
                return {
                    "yanit": f"Ariyorum",
                    "aksiyonlar": [{"fonksiyon": "web_ara", "parametreler": {"sorgu": sorgu}}]
                }

        # --- SES KONTROLU ---
        if "ses" in mk or "volume" in mk:
            if any(k in mk for k in ["kapat", "sessiz", "sifir", "kis", "mute"]):
                return {"yanit": "Sesi kapatiyorum", "aksiyonlar": [{"fonksiyon": "ses_ayarla", "parametreler": {"seviye": 0}}]}
            elif any(k in mk for k in ["tam ac", "full", "sonuna kadar"]):
                return {"yanit": "Ses tam acildi", "aksiyonlar": [{"fonksiyon": "ses_ayarla", "parametreler": {"seviye": 100}}]}
            elif any(k in mk for k in ["ac", "yukselt", "arttir", "artir"]):
                return {"yanit": "Sesi yukseltiyorum", "aksiyonlar": [{"fonksiyon": "ses_ayarla", "parametreler": {"seviye": 70}}]}
            elif any(k in mk for k in ["azalt", "dusur", "kisik"]):
                return {"yanit": "Sesi kisiyorum", "aksiyonlar": [{"fonksiyon": "ses_ayarla", "parametreler": {"seviye": 30}}]}

        # --- EKRAN GORUNTUSU ---
        if any(k in mk for k in ["ekran goruntusu", "screenshot", "ekrani kaydet", "ekrani yakala"]):
            return {"yanit": "Ekran goruntusu aliyorum", "aksiyonlar": [{"fonksiyon": "ekran_goruntusu", "parametreler": {}}]}

        # --- BILGISAYAR BILGISI ---
        if any(k in mk for k in ["cpu", "ram", "disk", "bilgisayar bilgi", "sistem bilgi",
                                   "islemci", "bellek", "hafiza kullanim", "ne kadar yer"]):
            return {"yanit": "Sistem bilgilerini getiriyorum", "aksiyonlar": [{"fonksiyon": "bilgisayar_bilgi", "parametreler": {}}]}

        # --- KLAVYE KISAYOLLARI ---
        if any(k in mk for k in ["kopyala", "copy"]):
            return {"yanit": "Kopyaladim", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["ctrl", "c"]}}]}
        if any(k in mk for k in ["yapistir", "paste"]):
            return {"yanit": "Yapistirdim", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["ctrl", "v"]}}]}
        if any(k in mk for k in ["geri al", "undo"]):
            return {"yanit": "Geri aldim", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["ctrl", "z"]}}]}
        if any(k in mk for k in ["tumu sec", "hepsini sec", "select all"]):
            return {"yanit": "Tamam", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["ctrl", "a"]}}]}
        if any(k in mk for k in ["kaydet", "save"]):
            return {"yanit": "Kaydettim", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["ctrl", "s"]}}]}

        # --- PENCERE KONTROLU ---
        if any(k in mk for k in ["pencere kucult", "minimize", "kucult"]):
            return {"yanit": "Pencereyi kucultuyorum", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["win", "down"]}}]}
        if any(k in mk for k in ["pencere buyut", "maximize", "tam ekran"]):
            return {"yanit": "Pencereyi buyutuyorum", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["win", "up"]}}]}
        if any(k in mk for k in ["masaustu goster", "masaustune don", "hepsini kucult"]):
            return {"yanit": "Masaustunu gosteriyorum", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["win", "d"]}}]}

        # --- KILIT / UYKU ---
        if any(k in mk for k in ["kilitle", "ekrani kilitle", "lock"]):
            return {"yanit": "Ekrani kilitliyorum", "aksiyonlar": [{"fonksiyon": "tus_bas", "parametreler": {"tuslar": ["win", "l"]}}]}

        # TESEKKUR artik kaliplar.py'de

        # Eslesmedi - AI'ya gonder
        return None

    # =============================================
    # KATMAN 2: GOOGLE GEMINI (HIZLI BULUT AI)
    # =============================================
    def _gemini_isle(self, metin, hafiza_ozeti=""):
        try:
            prompt_parcalari = [SISTEM_PROMPTU]
            if hafiza_ozeti:
                prompt_parcalari.append(f"Hafiza:{hafiza_ozeti[:300]}")
            if self.sohbet_gecmisi:
                for g in self.sohbet_gecmisi[-3:]:
                    prompt_parcalari.append(f"{g['role']}:{g['content'][:80]}")
            prompt_parcalari.append(f"Kullanici:{metin}")

            tam_prompt = "\n".join(prompt_parcalari)
            baslangic = time.time()

            url = (
                f"https://generativelanguage.googleapis.com/v1beta/models/"
                f"{self.gemini_model}:generateContent?key={self.gemini_api_key}"
            )
            veri = {
                "contents": [{"parts": [{"text": tam_prompt}]}],
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 150,
                    "responseMimeType": "application/json"
                }
            }

            r = requests.post(url, json=veri, timeout=12)
            sure = time.time() - baslangic
            print(f"[AI] Gemini: {sure:.1f}sn")

            if r.status_code == 429:
                # Rate limit - 3sn bekle ve bir kez daha dene
                print("[!] Gemini 429 (rate limit), 3sn bekleyip tekrar deneniyor...")
                time.sleep(3)
                r = requests.post(url, json=veri, timeout=12)
                sure = time.time() - baslangic
                print(f"[AI] Gemini tekrar: {sure:.1f}sn -> {r.status_code}")
                if r.status_code == 429:
                    try:
                        hata = r.json().get("error", {}).get("message", "")
                        print(f"[HATA] Gemini 429 detay: {hata[:120]}")
                    except:
                        pass
                    return None

            if r.status_code != 200:
                print(f"[HATA] Gemini {r.status_code}")
                try:
                    hata = r.json().get("error", {}).get("message", "")
                    print(f"[HATA] Detay: {hata[:120]}")
                except:
                    pass
                return None

            yanit_metni = (
                r.json().get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )
            if not yanit_metni:
                return None

            yanit = self._json_parse(yanit_metni)
            if yanit:
                self.sohbet_gecmisi.append({"role": "user", "content": metin})
                self.sohbet_gecmisi.append({"role": "assistant", "content": yanit_metni[:200]})
                if len(self.sohbet_gecmisi) > self.maks_gecmis:
                    self.sohbet_gecmisi = self.sohbet_gecmisi[-self.maks_gecmis:]
                return yanit
            return self._fallback_yanit(metin, yanit_metni)

        except requests.exceptions.Timeout:
            print("[HATA] Gemini zaman asimi")
            return None
        except Exception as e:
            print(f"[HATA] Gemini: {e}")
            return None

    # =============================================
    # KATMAN 3: OLLAMA YEDEK
    # =============================================
    def _ollama_isle(self, metin, hafiza_ozeti=""):
        # Once Ollama'nin calisiyor olup olmadigini hizlica kontrol et (2sn)
        try:
            r = requests.get(f"{self.url}/api/tags", timeout=2)
            if r.status_code != 200:
                print("[!] Ollama calismiyor, yerel yanit veriliyor")
                return self._fallback_yanit(metin)
        except:
            print("[!] Ollama baglantisi yok, yerel yanit veriliyor")
            return self._fallback_yanit(metin)

        mesajlar = [{"role": "system", "content": SISTEM_PROMPTU}]
        if hafiza_ozeti:
            mesajlar.append({"role": "system", "content": f"Hafiza:{hafiza_ozeti[:300]}"})
        for g in self.sohbet_gecmisi[-4:]:
            mesajlar.append(g)
        mesajlar.append({"role": "user", "content": metin})

        try:
            baslangic = time.time()
            r = requests.post(
                f"{self.url}/api/chat",
                json={"model": self.model, "messages": mesajlar, "stream": False,
                      "options": {"temperature": 0.3, "num_predict": 100}},
                timeout=20
            )
            print(f"[AI] Ollama: {time.time()-baslangic:.1f}sn")

            if r.status_code != 200:
                return self._fallback_yanit(metin)

            yanit_metni = r.json().get("message", {}).get("content", "")
            if not yanit_metni:
                return self._fallback_yanit(metin)

            yanit = self._json_parse(yanit_metni)
            if yanit:
                self.sohbet_gecmisi.append({"role": "user", "content": metin})
                self.sohbet_gecmisi.append({"role": "assistant", "content": yanit_metni[:200]})
                return yanit
            return self._fallback_yanit(metin, yanit_metni)

        except:
            return {"yanit": "Baglanti sorunu var, tekrar dener misin?", "aksiyonlar": []}

    # =============================================
    # YARDIMCILAR
    # =============================================
    def _json_parse(self, metin):
        try:
            return json.loads(metin)
        except:
            pass
        m = re.findall(r'```json\s*(.*?)\s*```', metin, re.DOTALL)
        for eslesme in m:
            try:
                return json.loads(eslesme)
            except:
                pass
        derinlik = 0
        bas = -1
        for i, c in enumerate(metin):
            if c == '{':
                if derinlik == 0: bas = i
                derinlik += 1
            elif c == '}':
                derinlik -= 1
                if derinlik == 0 and bas >= 0:
                    try:
                        return json.loads(metin[bas:i+1])
                    except:
                        pass
        return None

    def _fallback_yanit(self, metin, ai_ham=""):
        if ai_ham:
            temiz = re.sub(r'```.*?```', '', ai_ham, flags=re.DOTALL)
            temiz = re.sub(r'[{}\[\]"]', '', temiz).strip()
            if temiz and len(temiz) < 200:
                return {"yanit": temiz, "aksiyonlar": []}
        yerel = self._yerel_esle(metin.lower(), metin)
        if yerel:
            return yerel
        return {"yanit": "Anlayamadim, baska turlu soyler misin?", "aksiyonlar": []}

    def sohbet_sifirla(self):
        self.sohbet_gecmisi = []
