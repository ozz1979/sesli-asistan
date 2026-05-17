"""
ATLAS - Karar Merkezi
=====================
Beyin Karşılığı: Prefrontal Korteks
Görev: Gelen bilgiyi değerlendirip doğru yanıt yolunu seçmek

Kahneman'ın teorisi:
- Sistem 1 (Hızlı): Kalıp eşleştirme, otomatik → <100ms
- Sistem 2 Hafif: Basit AI yanıtı → 1-3s
- Sistem 2 Derin: Karmaşık AI + düşünme → 5-30s

AI Zinciri: Gemini → DeepSeek → Groq → Ollama → Fallback
AI Bilgisayar Kontrolü: AI komut etiketleri [KOMUT:...] ile bilgisayarı yönetir
"""

import re
import time
import logging
import threading
import requests
import json
import subprocess
import os

logger = logging.getLogger("ATLAS.karar")

# Web arama modulu
try:
    import web_arama
    WEB_ARAMA_AKTIF = True
    logger.info("Web arama modulu yuklendi")
except ImportError:
    WEB_ARAMA_AKTIF = False
    logger.info("Web arama modulu bulunamadi — web arama devre disi")


class KararMerkezi:
    """
    Prefrontal Korteks — karar verme merkezi.
    Gelen mesajı analiz edip en uygun yanıt yolunu seçer.
    AI Zinciri: Gemini → DeepSeek → Groq → Ollama → Fallback
    """

    def __init__(self, kalip_motoru, hafiza, duygu, config=None, ogrenme=None, bilgi_bankasi=None):
        self.kalip = kalip_motoru
        self.hafiza = hafiza
        self.duygu = duygu
        self.config = config or {}
        self.ogrenme = ogrenme          # Öğrenme motoru
        self.bilgi_bankasi = bilgi_bankasi  # Bilgi bankası
        self._bilgisayar_ozeti = ""  # Tarama özeti — system prompt'a eklenir

        ai_cfg = self.config.get("ai", {})
        self._gemini_model = ai_cfg.get("gemini_model", "gemini-2.0-flash")
        self._gemini_yedek = ai_cfg.get("gemini_yedek_model", "gemini-2.0-flash-lite")
        self._gemini_key = ai_cfg.get("gemini_api_key", "")
        self._deepseek_key = ai_cfg.get("deepseek_api_key", "")
        self._deepseek_model = ai_cfg.get("deepseek_model", "deepseek-chat")
        self._groq_key = ai_cfg.get("groq_api_key", "")
        self._groq_model = ai_cfg.get("groq_model", "llama-3.3-70b-versatile")
        self._ollama_model = ai_cfg.get("ollama_model", "llama3")
        self._ollama_url = ai_cfg.get("ollama_url", "http://localhost:11434")
        self._max_token = ai_cfg.get("max_token", 300)
        self._timeout = ai_cfg.get("timeout", 8)
        self._sicaklik = ai_cfg.get("sicaklik", 0.7)

        self._gemini_client = None
        self._deepseek_client = None
        self._groq_client = None
        self._eski_sdk = False
        self._gemini_devre_disi = False
        self._deepseek_devre_disi = False
        self._groq_devre_disi = False
        self._gemini_hazirla()
        self._deepseek_hazirla()
        self._groq_hazirla()

        # İstatistikler
        self._istatistik = {"sistem1": 0, "sistem2_hafif": 0, "sistem2_derin": 0, "hata": 0}

    # ══════════════════════════════════════════════════
    # AI HAZIRLAMA
    # ══════════════════════════════════════════════════

    def _gemini_hazirla(self):
        """Gemini AI client'ı hazırla — yeni google-genai SDK"""
        if not self._gemini_key:
            logger.warning("Gemini API key ayarlanmamış")
            return

        try:
            from google import genai
            self._gemini_client = genai.Client(api_key=self._gemini_key)
            self._eski_sdk = False
            logger.info(f"Gemini hazır: {self._gemini_model} (google-genai SDK)")
        except ImportError:
            try:
                import google.generativeai as genai_eski
                genai_eski.configure(api_key=self._gemini_key)
                self._gemini_client = genai_eski.GenerativeModel(
                    self._gemini_model,
                    generation_config={
                        "max_output_tokens": self._max_token,
                        "temperature": self._sicaklik,
                    }
                )
                self._eski_sdk = True
                logger.warning(f"Gemini hazır: {self._gemini_model} (ESKİ SDK)")
            except ImportError:
                logger.error("Gemini paketi kurulu değil! 'pip install google-genai'")
            except Exception as e:
                logger.error(f"Eski Gemini SDK hatası: {e}")
        except Exception as e:
            logger.error(f"Gemini hazırlama hatası: {type(e).__name__}: {e}")

    def _deepseek_hazirla(self):
        """DeepSeek AI client'ı hazırla — OpenAI uyumlu API"""
        if not self._deepseek_key:
            logger.info("DeepSeek API key ayarlanmamış — atlanıyor")
            return

        try:
            from openai import OpenAI
            self._deepseek_client = OpenAI(
                api_key=self._deepseek_key,
                base_url="https://api.deepseek.com"
            )
            logger.info(f"DeepSeek hazır: {self._deepseek_model}")
        except ImportError:
            logger.warning("DeepSeek için openai paketi gerekli: pip install openai")
        except Exception as e:
            logger.error(f"DeepSeek hazırlama hatası: {e}")

    def _groq_hazirla(self):
        """Groq AI client'ı hazırla — OpenAI uyumlu API"""
        if not self._groq_key:
            logger.info("Groq API key ayarlanmamış — atlanıyor")
            return

        try:
            from openai import OpenAI
            self._groq_client = OpenAI(
                api_key=self._groq_key,
                base_url="https://api.groq.com/openai/v1"
            )
            logger.info(f"Groq hazır: {self._groq_model}")
        except ImportError:
            logger.warning("Groq için openai paketi gerekli: pip install openai")
        except Exception as e:
            logger.error(f"Groq hazırlama hatası: {e}")

    # ══════════════════════════════════════════════════
    # SİSTEM TALİMATI
    # ══════════════════════════════════════════════════

    def bilgisayar_bilgisi_yukle(self, ozet_text):
        """Bilgisayar tarama özetini yükle — AI system prompt'a eklenecek"""
        self._bilgisayar_ozeti = ozet_text
        logger.info(f"Bilgisayar bilgisi yüklendi ({len(ozet_text)} karakter)")

    def _sistem_talimati(self):
        """AI modelleri icin sistem talimati — dogal konusma + akilli komut sistemi"""
        bilgisayar_bolum = ""
        if self._bilgisayar_ozeti:
            bilgisayar_bolum = "\nKullanicinin bilgisayar bilgisi:\n" + self._bilgisayar_ozeti + "\n"

        return f"""Sen ATLAS adinda bir Turkce sesli asistansin. Kullanicinin ismi Ozgur, Denizli'de yasiyor. Sen onun arkadasi ve yardimcisisin.{bilgisayar_bolum}

KIMLIGIN:
- Adin ATLAS. Bir insan arkadas gibi dogal ve samimi konus.
- Asla "yapay zeka", "dil modeli", "AI" deme. Sen ATLAS'sin, hepsi bu.
- Kendinden emin, rahat ve yardimsever ol. Asiri ozur dileme.
- Emoji kullanma cunku sesli okunacaksin.

KONUSMA KURALLARI:
1. SADECE TURKCE cevap ver. Ingilizce kelime kullanma.
2. Kisa ve oz cevap ver — en fazla 2-3 cumle. Uzun konusma yapma.
3. Sorulara dogrudan cevap ver. Laf dolandirma.
4. Bilmedigin veya emin olmadigin konularda "Bunu kesin bilmiyorum ama arastirabilirim" de. ASLA tahminle yanlis bilgi verme.
5. Kullanicinin onceki mesajlarina dikkat et, baglami koru.
6. Tekrar sorma gerekmiyorsa "tekrar eder misin" deme.

DOGRULUK KURALLARI (COK ONEMLI):
- Tarihi bilgiler, bilimsel bilgiler, matematik, tarihler, burclar, cografya gibi SOMUT SORULARDA mutlaka dogru bilgi ver.
- Emin degilsen "kesin bilmiyorum" de, ASLA uydurma.
- BURC HESABI YAPMA! Burc sorusu gelirse sadece "Burcunu hesapliyorum" de, sistem otomatik halleder. Sen ASLA burc hesaplama.
- Matematik hesaplarinda dikkatli ol, yanlis sonuc verme.
- DOVIZ KURU, DOLAR KURU, EURO KURU gibi GUNCEL FIYAT sorularinda ASLA tahmin yapma, ASLA eski bilgi verme. Sadece "kur bilgisini aliyorum" de, sistem otomatik guncel veriyi ceker.
- Yanlislikla yanlis bir sey soylersen, kullanici duzeltince "haklisin, duzeltiyorum" de.

WEB ARAMA SONUCLARI:
- Baglamda "Web arama sonuclari" bolumu varsa, bu internetten gelen GUNCEL bilgidir.
- Bu bilgileri kullanarak dogru ve guncel cevap ver.
- Kaynak gosterme, sadece bilgiyi dogal bir sekilde aktar.
- Web sonuclari yoksa kendi bilginle cevapla.

EN ONEMLI KURAL — SOYLE vs GOSTER AYRIMI:
- Kullanici "soyle", "anlat", "ne", "nedir", "kac", "nasil" derse → SOZLU CEVAP VER, komut KULLANMA.
- Kullanici "goster", "ara", "ac", "bak", "internette" derse → KOMUT kullan.
- Bilgi sorusu varsa (tarih, bilim, kultur, matematik, genel kultur) → KENDIN CEVAPLA, tarayici acma.
- SADECE kullanici acikca "ara", "goster", "internette bak", "Google'da ara" dediginde [KOMUT:ara:] kullan.
- Cevabini bildigin sorulari KENDIN YANITLA. Her seyi Google'a yonlendirme.

BILGISAYAR KOMUTLARI:
Kullanici bilgisayarda fiziksel bir sey yapmani istediginde yanit metninin SONUNA komut etiketi ekle.
Kullanici sadece sohbet ediyorsa veya soru soruyorsa komut KULLANMA.

Format: [KOMUT:tip:parametre]

Komutlar:
- [KOMUT:calistir:KOMUT] → Program calistir (notepad, calc, start chrome, start excel, explorer, taskmgr)
- [KOMUT:yaz:METIN] → Aktif pencereye metin yaz
- [KOMUT:ara:SORGU] → Google'da arama ac (SADECE kullanici acikca isterse!)
- [KOMUT:klasor:YOL] → Klasor ac (masaustu, belgelerim, indirilenler)
- [KOMUT:ekran] → Ekran goruntusu al
- [KOMUT:kisayol:TUS1+TUS2] → Klavye kisayolu (ctrl+s, ctrl+z, ctrl+c, ctrl+v, alt+F4)
- [KOMUT:pencere:ISLEM] → Pencere: kucult, buyut, kapat
- [KOMUT:ses:ISLEM] → Ses: yukselt, azalt, kapat, ac
- [KOMUT:kapat_program:ISIM] → Program kapat (chrome, notepad, excel)
- [KOMUT:dosya_oku:YOL] → Dosya icerigini oku (txt, py, json, csv vb.)
- [KOMUT:dosya_yaz:YOL|ICERIK] → Dosyaya yaz (uzerine yazar, yedek alir)
- [KOMUT:dosya_ekle:YOL|ICERIK] → Dosya sonuna ekle
- [KOMUT:dosya_sil:YOL] → Dosyayi cop kutusuna gonder
- [KOMUT:dosya_listele:YOL] → Klasordeki dosyalari listele
- [KOMUT:dosya_tasi:KAYNAK|HEDEF] → Dosya tasi
- [KOMUT:dosya_kopyala:KAYNAK|HEDEF] → Dosya kopyala
- [KOMUT:dosya_adlandir:YOL|YENI_ISIM] → Dosya yeniden adlandir
- [KOMUT:klasor_olustur:YOL] → Yeni klasor olustur
- [KOMUT:wifi:ac] veya [KOMUT:wifi:kapat] → Wi-Fi ac/kapat
- [KOMUT:bluetooth:ac] → Bluetooth ayarlarini ac
- [KOMUT:parlaklik:YUZDE] → Ekran parlakligini ayarla (0-100)
- [KOMUT:kilit] → Ekrani kilitle
- [KOMUT:cop_bosalt] → Cop kutusunu bosalt
- [KOMUT:pil] → Pil durumunu sorgula
- [KOMUT:not:BASLIK|ICERIK] → Masaustune not dosyasi olustur
- [KOMUT:alarm:SANIYE:MESAJ] → Zamanlayici/hatirlatici kur
- [KOMUT:masaustu_goster] → Tum pencereleri kucultup masaustunu goster
- [KOMUT:pencere_degistir] → Sonraki pencereye gec (Alt+Tab)
- [KOMUT:yakalama] → Ekran yakalama araci ac
- [KOMUT:emoji] → Emoji panelini ac
- [KOMUT:web_ara:SORGU] → Internette arastirma yap (sonuclari sesli oku)

KURALLAR:
- Komut etiketini yanitin SONUNA yaz. Kullanici etiketi duymaz.
- Sohbet mesajlarinda etiket KULLANMA.
- TEHLIKELI komutlar YASAK: format, del, rmdir, shutdown, reg delete.
- Kullanici "resmi kapat", "fotografı kapat" derse [KOMUT:pencere:kapat] kullan, ASLA bilgisayari kapatma.
- Kullanici sadece "kapat" derse aktif pencereyi kapat: [KOMUT:pencere:kapat]. ASLA bilgisayari kapatma!
- Bilgisayari kapatma komutu SADECE kullanici acikca "bilgisayarı kapat" dediginde kullanilabilir.
- Birden fazla komut olabilir: "Aciyorum! [KOMUT:calistir:notepad] [KOMUT:yaz:merhaba]"
- Dosya yollarinda | ayirici kullan: [KOMUT:dosya_yaz:C:\\dosya.txt|icerik buraya]
- Dosya islemlerinde kullanicinin masaustu yolu: ~\\Desktop

ORNEK DIYALOGLAR:

Kullanici: "Turkiye'nin baskenti neresi?"
ATLAS: "Turkiye'nin baskenti Ankara."
(Komut YOK — bilgi sorusu, kendim cevapladim)

Kullanici: "2 arti 2 kac eder?"
ATLAS: "4 eder."
(Komut YOK — matematik sorusu)

Kullanici: "Dunya'nin en buyuk okyanusu hangisi?"
ATLAS: "Buyuk Okyanus, yani Pasifik Okyanusu."
(Komut YOK — genel kultur)

Kullanici: "Chrome'u ac"
ATLAS: "Chrome aciliyor! [KOMUT:calistir:start chrome]"

Kullanici: "Internette kediler ara"
ATLAS: "Hemen ariyorum! [KOMUT:ara:kediler]"
(Komut VAR — acikca "ara" dedi)

Kullanici: "Nasilsin?"
ATLAS: "Iyiyim, sen nasilsin Ozgur?"
(Komut YOK — sohbet)

Kullanici: "Bir sarki oner"
ATLAS: "Tarkan'in Kuzu Kuzu sarkisini oneririm, cok guzel bir parca."
(Komut YOK — oneri sorusu)

Kullanici: "YouTube'da muzik goster"
ATLAS: "YouTube'u aciyorum! [KOMUT:calistir:start https://www.youtube.com]"
(Komut VAR — "goster" dedi)

Kullanici: "Bu dosyayi kaydet"
ATLAS: "Kaydediyorum! [KOMUT:kisayol:ctrl+s]"

Kullanici: "Seni kim yapti?"
ATLAS: "Beni Ozgur yapti. Ben ATLAS'im, senin kisisel asistanin."
"""


    # ══════════════════════════════════════════════════
    # KOMUT ÇALIŞTIRMA
    # ══════════════════════════════════════════════════

    # Tehlikeli komutlar — bunları çalıştırma
    _TEHLIKELI = {"format", "del ", "rmdir", "rd ", "shutdown", "rm ", "deltree",
                  "reg delete", "net user", "cipher /w"}

    def _komut_calistir(self, yanit_text):
        """
        AI yanıtındaki [KOMUT:...] etiketlerini parse et ve çalıştır.
        Returns: (temiz_yanit, komut_sonuclari_listesi)
        """
        import bilgisayar_kontrol as bk

        # Tüm komut etiketlerini bul
        komut_pattern = r'\[KOMUT:([^\]]+)\]'
        komutlar = re.findall(komut_pattern, yanit_text)

        # Etiketleri yanıttan temizle (kullanıcı duymayacak)
        temiz = re.sub(komut_pattern, '', yanit_text).strip()
        temiz = re.sub(r'\s{2,}', ' ', temiz)  # çoklu boşluk temizle

        sonuclar = []

        for komut_str in komutlar:
            parcalar = komut_str.split(":", 1)
            tip = parcalar[0].strip().lower()
            param = parcalar[1].strip() if len(parcalar) > 1 else ""

            try:
                if tip == "calistir":
                    # Tehlike kontrolü
                    if any(t in param.lower() for t in self._TEHLIKELI):
                        logger.warning(f"Tehlikeli komut engellendi: {param}")
                        sonuclar.append(("engellendi", param))
                        continue
                    subprocess.Popen(param, shell=True)
                    logger.info(f"Komut çalıştırıldı: {param}")
                    sonuclar.append(("ok", param))

                elif tip == "yaz":
                    if param:
                        # Kısa gecikme — önceki komut (notepad açma vs) tamamlansın
                        if sonuclar:
                            import time as t
                            t.sleep(1.5)
                        basarili, mesaj = bk.metin_yaz(param)
                        sonuclar.append(("ok" if basarili else "hata", mesaj))
                    else:
                        sonuclar.append(("hata", "Yazılacak metin boş"))

                elif tip == "ara":
                    if param:
                        basarili, mesaj = bk.web_ara(param)
                        sonuclar.append(("ok" if basarili else "hata", mesaj))

                elif tip == "klasor":
                    ozel = {
                        "masaustu": bk.masaustu_ac,
                        "masaüstü": bk.masaustu_ac,
                        "belgelerim": bk.belgelerim_ac,
                        "indirilenler": bk.indirilenler_ac,
                    }
                    if param.lower() in ozel:
                        basarili, mesaj = ozel[param.lower()]()
                    else:
                        basarili, mesaj = bk.klasor_ac(param)
                    sonuclar.append(("ok" if basarili else "hata", mesaj))

                elif tip == "ekran":
                    basarili, mesaj = bk.ekran_goruntusu()
                    sonuclar.append(("ok" if basarili else "hata", mesaj))

                elif tip == "kisayol":
                    tuslar = param.replace("+", " ").split()
                    if tuslar:
                        basarili, mesaj = bk.kisayol_bas(*tuslar)
                        sonuclar.append(("ok" if basarili else "hata", mesaj))

                elif tip == "pencere":
                    islem_map = {
                        "kucult": bk.pencere_kucult,
                        "küçült": bk.pencere_kucult,
                        "buyut": bk.pencere_buyut,
                        "büyüt": bk.pencere_buyut,
                        "kapat": bk.pencere_kapat,
                    }
                    fn = islem_map.get(param.lower())
                    if fn:
                        basarili, mesaj = fn()
                        sonuclar.append(("ok" if basarili else "hata", mesaj))

                elif tip == "ses":
                    islem_map = {
                        "yukselt": "yukselt", "yükselt": "yukselt",
                        "azalt": "azalt", "kıs": "azalt",
                        "kapat": "kapat", "ac": "ac", "aç": "ac",
                    }
                    islem = islem_map.get(param.lower())
                    if islem:
                        basarili, mesaj = bk.ses_ayarla(islem)
                        sonuclar.append(("ok" if basarili else "hata", mesaj))

                elif tip == "dosya_oku":
                    basarili, sonuc = bk.dosya_oku(param)
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "dosya_yaz":
                    parcalar2 = param.split("|", 1)
                    if len(parcalar2) == 2:
                        basarili, sonuc = bk.dosya_yaz(parcalar2[0].strip(), parcalar2[1])
                        sonuclar.append(("ok" if basarili else "hata", sonuc))
                    else:
                        sonuclar.append(("hata", "Format: YOL|ICERIK"))

                elif tip == "dosya_ekle":
                    parcalar2 = param.split("|", 1)
                    if len(parcalar2) == 2:
                        basarili, sonuc = bk.dosya_ekle(parcalar2[0].strip(), parcalar2[1])
                        sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "dosya_sil":
                    basarili, sonuc = bk.dosya_sil(param)
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "dosya_listele":
                    basarili, sonuc = bk.dosya_listele(param or None)
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "dosya_tasi":
                    parcalar2 = param.split("|", 1)
                    if len(parcalar2) == 2:
                        basarili, sonuc = bk.dosya_tasi(parcalar2[0].strip(), parcalar2[1].strip())
                        sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "dosya_kopyala":
                    parcalar2 = param.split("|", 1)
                    if len(parcalar2) == 2:
                        basarili, sonuc = bk.dosya_kopyala(parcalar2[0].strip(), parcalar2[1].strip())
                        sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "dosya_adlandir":
                    parcalar2 = param.split("|", 1)
                    if len(parcalar2) == 2:
                        basarili, sonuc = bk.dosya_yeniden_adlandir(parcalar2[0].strip(), parcalar2[1].strip())
                        sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "klasor_olustur":
                    basarili, sonuc = bk.klasor_olustur(param)
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "wifi":
                    basarili, sonuc = bk.wifi_kontrol(param.lower().replace("aç", "ac"))
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "bluetooth":
                    basarili, sonuc = bk.bluetooth_kontrol(param.lower())
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "parlaklik":
                    basarili, sonuc = bk.parlaklik_ayarla(param)
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "kilit":
                    basarili, sonuc = bk.ekran_kilitle()
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "cop_bosalt":
                    basarili, sonuc = bk.cop_bosalt()
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "pil":
                    basarili, sonuc = bk.pil_durumu()
                    if basarili:
                        sonuclar.append(("ok", f"Pil %{sonuc['yuzde']}, {sonuc['durum']}"))
                    else:
                        sonuclar.append(("hata", sonuc))

                elif tip == "not":
                    parcalar2 = param.split("|", 1)
                    baslik = parcalar2[0].strip()
                    icerik = parcalar2[1].strip() if len(parcalar2) > 1 else ""
                    basarili, sonuc = bk.not_al(baslik, icerik)
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "alarm":
                    parcalar2 = param.split(":", 1)
                    try:
                        saniye = int(parcalar2[0].strip())
                        mesaj = parcalar2[1].strip() if len(parcalar2) > 1 else "Sure doldu!"
                        basarili, sonuc = bk.alarm_kur(saniye, mesaj)
                        sonuclar.append(("ok" if basarili else "hata", sonuc))
                    except ValueError:
                        sonuclar.append(("hata", "Gecersiz sure"))

                elif tip == "masaustu_goster":
                    basarili, sonuc = bk.masaustu_goster()
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "pencere_degistir":
                    basarili, sonuc = bk.pencere_degistir()
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "yakalama":
                    basarili, sonuc = bk.yakalama_araci()
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "emoji":
                    basarili, sonuc = bk.emoji_paneli()
                    sonuclar.append(("ok" if basarili else "hata", sonuc))

                elif tip == "web_ara":
                    if WEB_ARAMA_AKTIF and param:
                        try:
                            arama_sonuc = web_arama.arastir(param, detayli=True)
                            if arama_sonuc["basarili"] and arama_sonuc["sonuclar"]:
                                ozet = arama_sonuc["sonuclar"][0].get("ozet", "")
                                sonuclar.append(("ok", ozet[:300]))
                            else:
                                sonuclar.append(("hata", "Sonuc bulunamadi"))
                        except Exception as e2:
                            sonuclar.append(("hata", str(e2)))
                    else:
                        sonuclar.append(("hata", "Web arama devre disi"))

                elif tip == "kapat_program":
                    # Program kapatma — taskkill kullan
                    exe_map = {
                        "chrome": "chrome.exe", "notepad": "notepad.exe",
                        "word": "WINWORD.EXE", "excel": "EXCEL.EXE",
                        "firefox": "firefox.exe", "edge": "msedge.exe",
                        "paint": "mspaint.exe", "calculator": "Calculator.exe",
                        "hesap makinesi": "Calculator.exe",
                        "explorer": "explorer.exe", "spotify": "Spotify.exe",
                        "discord": "Discord.exe", "teams": "Teams.exe",
                        "whatsapp": "WhatsApp.exe", "telegram": "Telegram.exe",
                        "opera": "opera.exe", "cmd": "cmd.exe",
                        "powershell": "powershell.exe",
                    }
                    exe = exe_map.get(param.lower(), f"{param}.exe")
                    subprocess.Popen(
                        f"taskkill /im {exe} /f",
                        shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    logger.info(f"Program kapatıldı: {exe}")
                    sonuclar.append(("ok", f"{param} kapatıldı"))

                else:
                    logger.warning(f"Bilinmeyen komut tipi: {tip}")
                    sonuclar.append(("bilinmeyen", tip))

            except Exception as e:
                logger.error(f"Komut hatası [{tip}:{param}]: {e}")
                sonuclar.append(("hata", str(e)))

        return temiz, sonuclar

    # ══════════════════════════════════════════════════
    # ANA KARAR FONKSİYONU
    # ══════════════════════════════════════════════════

    def karar_ver(self, text, niyet=None, duygu_sonucu=None):
        """
        Ana karar fonksiyonu.
        1. Sistem 1 (kalıp) dene → bulursa hemen döndür
        2. Bulamazsa → Sistem 2 (AI zinciri) kullan
        3. AI yanıtındaki komutları çalıştır
        """
        baslangic = time.time()

        if not text:
            return {
                "yanit": "Seni duyamadım, tekrar eder misin?",
                "yol": "hata",
                "sure_ms": 0,
                "kategori": None
            }

        # ──── SİSTEM 1: Kalıp Eşleştirme ────
        yanit, kategori, guven = self.kalip.eslestirir(text)
        if yanit and guven >= 0.7:
            sure = (time.time() - baslangic) * 1000
            self._istatistik["sistem1"] += 1
            logger.info(f"Sistem 1 yanıt ({sure:.0f}ms): [{kategori}] {yanit[:50]}")
            self.hafiza.prosedurel.kalip_guncelle(text.lower(), yanit, basarili=True)
            return {
                "yanit": yanit,
                "yol": "sistem1",
                "sure_ms": sure,
                "kategori": kategori
            }

        # ──── WEB ARAMA: Gerekiyorsa internetten bilgi topla ────
        web_baglam = ""
        if WEB_ARAMA_AKTIF:
            try:
                gerekli, sorgu = web_arama.arama_gerekli_mi(text)
                if gerekli and sorgu:
                    logger.info(f"Web arama tetiklendi: '{sorgu}'")
                    arama_sonuc = web_arama.arastir(sorgu)
                    if arama_sonuc["basarili"]:
                        web_baglam = "\n\n" + arama_sonuc["baglam"]
                        logger.info(f"Web arama baglami eklendi ({arama_sonuc['sure_ms']}ms, {len(arama_sonuc['sonuclar'])} sonuc)")
            except Exception as e:
                logger.debug(f"Web arama hatasi (kritik degil): {e}")

        # ──── SİSTEM 2: AI Zinciri ────
        baglam = self._baglam_olustur(text, niyet, duygu_sonucu)

        # Web arama baglami varsa ekle
        if web_baglam:
            baglam = baglam + web_baglam

        # Zincir: Gemini → DeepSeek → Groq → Ollama → Fallback
        ai_yanit = self._gemini_sor(baglam, text)

        if not ai_yanit:
            ai_yanit = self._deepseek_sor(baglam, text)

        if not ai_yanit:
            ai_yanit = self._groq_sor(baglam, text)

        if not ai_yanit:
            ai_yanit = self._ollama_sor(baglam, text)

        if not ai_yanit:
            ai_yanit = self._fallback_yanit(text, niyet)
            yol = "fallback"
            self._istatistik["hata"] += 1
        else:
            yol = "sistem2"
            self._istatistik["sistem2_hafif"] += 1

        # ──── BURÇ DÜZELTME — AI yanlış burç söylerse düzelt ────
        ai_yanit = self._burc_duzelt(ai_yanit)

        # ──── KOMUT ÇALIŞTIRMA ────
        # AI yanıtında [KOMUT:...] etiketi varsa çalıştır
        if "[KOMUT:" in ai_yanit:
            temiz_yanit, sonuclar = self._komut_calistir(ai_yanit)
            if sonuclar:
                logger.info(f"AI komut sonuçları: {sonuclar}")
            ai_yanit = temiz_yanit

        sure = (time.time() - baslangic) * 1000
        logger.info(f"Sistem 2 yanıt ({sure:.0f}ms): {ai_yanit[:50]}")

        return {
            "yanit": ai_yanit,
            "yol": yol,
            "sure_ms": sure,
            "kategori": niyet.get("niyet") if niyet else None
        }

    # ══════════════════════════════════════════════════
    # BAĞLAM OLUŞTURMA
    # ══════════════════════════════════════════════════

    def _baglam_olustur(self, text, niyet, duygu_sonucu):
        """AI'a gönderilecek bağlam prompt'u — kısa ve öz"""
        ad = self.hafiza.kullanici_bilgisi_getir("ad", "")

        # Semantik bellekten tüm kullanıcı bilgilerini çek
        kullanici_bilgileri = ""
        try:
            bilgiler = self.hafiza.semantik.kategori_getir("kullanici")
            ekstra = {k: v for k, v in bilgiler.items() if k != "ad" and v}
            if ekstra:
                satirlar = [f"  - {k}: {v}" for k, v in ekstra.items()]
                kullanici_bilgileri = "\nBilinen bilgiler:\n" + "\n".join(satirlar)
        except Exception:
            pass

        son_konusmalar = ""
        try:
            calisma = self.hafiza.calisma.getir()
            if calisma:
                satirlar = []
                for item in calisma[-5:]:
                    rol = item.get("rol", "?")
                    mesaj = item.get("mesaj", "")[:80]
                    if rol == "kullanici":
                        satirlar.append(f"Kullanıcı: {mesaj}")
                    elif rol == "asistan":
                        satirlar.append(f"ATLAS: {mesaj}")
                if satirlar:
                    son_konusmalar = "\nSon konuşma:\n" + "\n".join(satirlar)
        except Exception:
            pass

        duygu_str = ""
        if duygu_sonucu:
            duygu = duygu_sonucu.get("duygu", "notr")
            if duygu != "notr":
                duygu_str = f"\nKullanıcı şu an {duygu} hissediyor."

        baglam = f"Kullanıcının adı: {ad}{kullanici_bilgileri}{son_konusmalar}{duygu_str}"

        # Öğrenme motoru bağlam zenginleştirme
        if self.ogrenme:
            try:
                baglam = self.ogrenme.baglam_zenginlestir(baglam)
            except Exception:
                pass

        # Bilgi bankası — kişisel gelişim bağlamı
        if self.bilgi_bankasi:
            try:
                bilgi_baglam = self.bilgi_bankasi.ai_baglam_olustur(text)
                if bilgi_baglam:
                    baglam = baglam + "\n\n" + bilgi_baglam
            except Exception:
                pass

        return baglam

    # ══════════════════════════════════════════════════
    # YANITLARI TEMİZLEME
    # ══════════════════════════════════════════════════

    def _burc_duzelt(self, yanit):
        """AI yanıtında yanlış burç varsa deterministic olarak düzelt"""
        try:
            from kalip_motoru import burc_hesapla, burc_tarih_cikar, AY_ISIMLERI
            yanit_lower = yanit.lower()

            # Yanıtta burç kelimesi var mı?
            burc_kelimeler = ["koç", "boğa", "ikizler", "yengeç", "aslan", "başak",
                              "terazi", "akrep", "yay", "oğlak", "kova", "balık"]
            burc_var = any(b in yanit_lower for b in burc_kelimeler)
            if not burc_var:
                return yanit

            # Yanıttaki tarihi bul
            sonuc = burc_tarih_cikar(yanit_lower + " burc")
            if sonuc:
                dogru_burc, gun, ay_adi, yil = sonuc
            else:
                # Hafızadan doğum tarihini al
                dogum = self.hafiza.kullanici_bilgisi_getir("dogum_tarihi", "")
                if dogum:
                    sonuc = burc_tarih_cikar(dogum + " burc")
                    if sonuc:
                        dogru_burc = sonuc[0]
                    else:
                        return yanit
                else:
                    return yanit

            # Yanlış burç varsa düzelt
            for yanlis_burc in burc_kelimeler:
                if yanlis_burc in yanit_lower and yanlis_burc != dogru_burc.lower():
                    # Büyük/küçük harf uyumlu değiştir
                    import re as re2
                    pattern = re2.compile(re2.escape(yanlis_burc), re2.IGNORECASE)
                    yanit = pattern.sub(dogru_burc, yanit)
                    logger.warning(f"Burç düzeltildi: {yanlis_burc} → {dogru_burc}")
                    break

            return yanit
        except Exception as e:
            logger.debug(f"Burç düzeltme hatası (kritik değil): {e}")
            return yanit

    def _yanit_temizle(self, yanit):
        """Uzun yanıtları kes, temizle — KOMUT etiketlerini koru"""
        yanit = yanit.strip()

        # Komut etiketlerini ayır
        komut_pattern = r'\[KOMUT:[^\]]+\]'
        komutlar = re.findall(komut_pattern, yanit)
        temiz = re.sub(komut_pattern, '', yanit).strip()

        # Metin kısmını kısalt
        if len(temiz) > 200:
            for sep in [". ", "! ", "? "]:
                idx = temiz.find(sep)
                if 10 < idx < 150:
                    temiz = temiz[:idx + 1]
                    break
            else:
                temiz = temiz[:150] + "..."

        # Komut etiketlerini geri ekle
        if komutlar:
            temiz = temiz + " " + " ".join(komutlar)

        return temiz

    def _ingilizce_mi(self, text):
        """Metnin İngilizce olup olmadığını basit kontrol et"""
        # Komut etiketlerini temizle
        temiz = re.sub(r'\[KOMUT:[^\]]+\]', '', text)
        ingilizce_kelimeler = {"the", "is", "are", "was", "were", "have", "has",
                               "will", "would", "could", "should", "can",
                               "hello", "hi", "how", "what", "where", "when",
                               "i am", "you are", "it is", "that is"}
        text_lower = temiz.lower()
        sayac = sum(1 for k in ingilizce_kelimeler if f" {k} " in f" {text_lower} ")
        return sayac >= 3

    # ══════════════════════════════════════════════════
    # GEMİNİ AI
    # ══════════════════════════════════════════════════

    def _gemini_sor_yeni(self, prompt, model=None):
        """Yeni google-genai SDK ile soru sor"""
        from google.genai import types
        return self._gemini_client.models.generate_content(
            model=model or self._gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self._sistem_talimati(),
                max_output_tokens=self._max_token,
                temperature=self._sicaklik,
            )
        )

    def _gemini_sor_eski(self, prompt):
        """Eski google-generativeai SDK ile soru sor"""
        try:
            return self._gemini_client.generate_content(
                prompt, request_options={"timeout": self._timeout}
            )
        except TypeError:
            return self._gemini_client.generate_content(prompt)

    def _gemini_sor(self, baglam, soru):
        """Gemini AI'a sor"""
        if not self._gemini_client or self._gemini_devre_disi:
            return None

        prompt = f"{baglam}\n\nKullanıcı: {soru}"

        try:
            if self._eski_sdk:
                response = self._gemini_sor_eski(
                    f"{self._sistem_talimati()}\n\n{prompt}"
                )
            else:
                response = self._gemini_sor_yeni(prompt)

            if response and response.text:
                yanit = self._yanit_temizle(response.text)
                if self._ingilizce_mi(yanit):
                    logger.warning("Gemini İngilizce yanıt verdi, tekrar deneniyor")
                    prompt2 = f"SADECE TÜRKÇE YANITLA!\n\n{baglam}\n\nKullanıcı: {soru}"
                    try:
                        if self._eski_sdk:
                            r2 = self._gemini_sor_eski(prompt2)
                        else:
                            r2 = self._gemini_sor_yeni(prompt2)
                        if r2 and r2.text:
                            yanit = self._yanit_temizle(r2.text)
                    except Exception:
                        pass
                return yanit

        except Exception as e:
            hata_str = str(e).lower()
            if "429" in hata_str or "quota" in hata_str or "exhausted" in hata_str:
                logger.warning("Gemini kota dolmuş — bu oturumda devre dışı bırakılıyor")
                self._gemini_devre_disi = True
            else:
                logger.error(f"Gemini hatası: {type(e).__name__}: {e}")
                self._gemini_devre_disi = True

        return None

    # ══════════════════════════════════════════════════
    # DEEPSEEK AI
    # ══════════════════════════════════════════════════

    def _deepseek_sor(self, baglam, soru):
        """DeepSeek AI'a sor — OpenAI uyumlu API"""
        if not self._deepseek_client or self._deepseek_devre_disi:
            return None

        prompt = f"{baglam}\n\nKullanıcı: {soru}"

        try:
            response = self._deepseek_client.chat.completions.create(
                model=self._deepseek_model,
                messages=[
                    {"role": "system", "content": self._sistem_talimati()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self._max_token,
                temperature=self._sicaklik,
                timeout=self._timeout,
            )

            if response and response.choices:
                yanit = response.choices[0].message.content
                if yanit:
                    yanit = self._yanit_temizle(yanit)
                    logger.info(f"DeepSeek yanıt: {yanit[:50]}")
                    return yanit

        except Exception as e:
            hata_str = str(e).lower()
            if "429" in hata_str or "quota" in hata_str or "402" in hata_str or "balance" in hata_str:
                logger.warning("DeepSeek kota/bakiye sorunu — bu oturumda devre dışı bırakılıyor")
                self._deepseek_devre_disi = True
            elif "401" in hata_str or "auth" in hata_str or "invalid" in hata_str:
                logger.warning("DeepSeek API key geçersiz — bu oturumda devre dışı bırakılıyor")
                self._deepseek_devre_disi = True
            else:
                logger.error(f"DeepSeek hatası: {type(e).__name__}: {e}")
                self._deepseek_devre_disi = True

        return None

    # ══════════════════════════════════════════════════
    # GROQ AI (ÜCRETSİZ)
    # ══════════════════════════════════════════════════

    def _groq_sor(self, baglam, soru):
        """Groq AI'a sor — OpenAI uyumlu API, ücretsiz"""
        if not self._groq_client or self._groq_devre_disi:
            return None

        prompt = f"{baglam}\n\nKullanıcı: {soru}"

        try:
            response = self._groq_client.chat.completions.create(
                model=self._groq_model,
                messages=[
                    {"role": "system", "content": self._sistem_talimati()},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self._max_token,
                temperature=self._sicaklik,
                timeout=self._timeout,
            )

            if response and response.choices:
                yanit = response.choices[0].message.content
                if yanit:
                    yanit = self._yanit_temizle(yanit)
                    logger.info(f"Groq yanıt: {yanit[:50]}")
                    return yanit

        except Exception as e:
            hata_str = str(e).lower()
            if "429" in hata_str or "rate" in hata_str:
                logger.warning("Groq rate limit — sonraki AI'a geçiliyor...")
            else:
                logger.error(f"Groq hatası: {type(e).__name__}: {e}")

        return None

    # ══════════════════════════════════════════════════
    # OLLAMA (YEREL AI)
    # ══════════════════════════════════════════════════

    def _ollama_sor(self, baglam, soru):
        """Ollama yerel AI'a sor"""
        try:
            try:
                r = requests.get(f"{self._ollama_url}/api/tags", timeout=1.5)
                if r.status_code != 200:
                    return None
            except Exception:
                return None

            sistem = self._sistem_talimati()
            prompt = f"{sistem}\n\n{baglam}\n\nKullanıcı: {soru}\nATLAS:"
            response = requests.post(
                f"{self._ollama_url}/api/generate",
                json={
                    "model": self._ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "num_predict": self._max_token,
                        "temperature": self._sicaklik,
                    }
                },
                timeout=15
            )

            if response.status_code == 200:
                data = response.json()
                yanit = data.get("response", "").strip()
                if yanit:
                    return self._yanit_temizle(yanit)

        except Exception as e:
            logger.error(f"Ollama hatası: {e}")

        return None

    # ══════════════════════════════════════════════════
    # FALLBACK
    # ══════════════════════════════════════════════════

    def _fallback_yanit(self, text, niyet):
        """AI'lar çalışmıyorsa fallback yanıt"""
        niyet_adi = niyet.get("niyet", "") if niyet else ""

        fallback = {
            "saat_sor": None,
            "tarih_sor": None,
            "selam": "Merhaba! Sana nasıl yardımcı olabilirim?",
            "hal_hatir": "İyiyim, teşekkürler! Sen nasılsın?",
            "tesekkur": "Rica ederim!",
        }

        yanit = fallback.get(niyet_adi)
        if yanit:
            return yanit

        if not self._gemini_key and not self._deepseek_key and not self._groq_key:
            return "Yapay zeka bağlantım ayarlanmamış. Config dosyasındaki API anahtarlarını kontrol eder misin?"

        return "Şu an buna cevap veremedim. Biraz sonra tekrar dener misin?"

    # ══════════════════════════════════════════════════
    # BAĞLANTI TESTİ
    # ══════════════════════════════════════════════════

    def baglanti_test(self):
        """Tüm AI bağlantılarını test et"""
        sonuc = {
            "basarili": False,
            "gemini": {"durum": "yok", "detay": ""},
            "deepseek": {"durum": "yok", "detay": ""},
            "groq": {"durum": "yok", "detay": ""},
            "hata": None,
            "cozum": None,
        }

        # ── Gemini test ──
        if self._gemini_key and self._gemini_client:
            try:
                if not self._eski_sdk:
                    from google.genai import types
                    r = self._gemini_client.models.generate_content(
                        model=self._gemini_model,
                        contents="Sadece 'OK' yaz.",
                        config=types.GenerateContentConfig(max_output_tokens=5, temperature=0.1)
                    )
                else:
                    r = self._gemini_client.generate_content("Sadece 'OK' yaz.")
                if r and r.text:
                    sonuc["gemini"] = {"durum": "ok", "detay": r.text.strip()[:20]}
                    sonuc["basarili"] = True
            except Exception as e:
                hata = str(e)[:100]
                if "429" in hata:
                    sonuc["gemini"] = {"durum": "kota_dolmus", "detay": "429"}
                else:
                    sonuc["gemini"] = {"durum": "hata", "detay": hata}
        elif not self._gemini_key:
            sonuc["gemini"] = {"durum": "key_yok", "detay": "API key girilmemiş"}

        # ── DeepSeek test ──
        if self._deepseek_key and self._deepseek_client:
            try:
                r = self._deepseek_client.chat.completions.create(
                    model=self._deepseek_model,
                    messages=[{"role": "user", "content": "Sadece 'OK' yaz."}],
                    max_tokens=5,
                    temperature=0.1,
                    timeout=8,
                )
                if r and r.choices:
                    sonuc["deepseek"] = {"durum": "ok", "detay": r.choices[0].message.content.strip()[:20]}
                    sonuc["basarili"] = True
            except Exception as e:
                hata = str(e)[:100]
                sonuc["deepseek"] = {"durum": "hata", "detay": hata}
        elif not self._deepseek_key:
            sonuc["deepseek"] = {"durum": "key_yok", "detay": "API key girilmemiş"}

        # ── Groq test ──
        if self._groq_key and self._groq_client:
            try:
                r = self._groq_client.chat.completions.create(
                    model=self._groq_model,
                    messages=[{"role": "user", "content": "Sadece 'OK' yaz."}],
                    max_tokens=5,
                    temperature=0.1,
                    timeout=8,
                )
                if r and r.choices:
                    sonuc["groq"] = {"durum": "ok", "detay": r.choices[0].message.content.strip()[:20]}
                    sonuc["basarili"] = True
            except Exception as e:
                hata = str(e)[:100]
                sonuc["groq"] = {"durum": "hata", "detay": hata}
        elif not self._groq_key:
            sonuc["groq"] = {"durum": "key_yok", "detay": "API key girilmemiş"}

        # Sonuç
        if not sonuc["basarili"]:
            sonuc["hata"] = "Hiçbir AI bağlantısı çalışmıyor"
            sonuc["cozum"] = "config.json'da en az bir API key girin (gemini, deepseek veya groq)"

        return sonuc

    def api_key_guncelle(self, yeni_key, servis="gemini"):
        """API key güncelle ve client'ı yeniden oluştur"""
        if servis == "gemini":
            self._gemini_key = yeni_key
            self.config.setdefault("ai", {})["gemini_api_key"] = yeni_key
            self._gemini_hazirla()
        elif servis == "deepseek":
            self._deepseek_key = yeni_key
            self.config.setdefault("ai", {})["deepseek_api_key"] = yeni_key
            self._deepseek_hazirla()
        elif servis == "groq":
            self._groq_key = yeni_key
            self.config.setdefault("ai", {})["groq_api_key"] = yeni_key
            self._groq_hazirla()

    def istatistik(self):
        return dict(self._istatistik)
