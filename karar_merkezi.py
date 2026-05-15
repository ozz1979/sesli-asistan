"""
ATLAS - Karar Merkezi
=====================
Beyin Karşılığı: Prefrontal Korteks
Görev: Gelen bilgiyi değerlendirip doğru yanıt yolunu seçmek

Kahneman'ın teorisi:
- Sistem 1 (Hızlı): Kalıp eşleştirme, otomatik → <100ms
- Sistem 2 Hafif: Basit AI yanıtı → 1-3s
- Sistem 2 Derin: Karmaşık AI + düşünme → 5-30s

Bu modül hangi yolun kullanılacağına karar verir.

NOT: google-genai paketi kullanır (yeni resmi SDK).
"""

import time
import logging
import threading
import requests
import json

logger = logging.getLogger("ATLAS.karar")


class KararMerkezi:
    """
    Prefrontal Korteks — karar verme merkezi.
    Gelen mesajı analiz edip en uygun yanıt yolunu seçer.
    """

    def __init__(self, kalip_motoru, hafiza, duygu, config=None):
        self.kalip = kalip_motoru
        self.hafiza = hafiza
        self.duygu = duygu
        self.config = config or {}

        ai_cfg = self.config.get("ai", {})
        self._birincil_ai = ai_cfg.get("birincil", "gemini")
        self._yedek_ai = ai_cfg.get("yedek", "ollama")
        self._gemini_model = ai_cfg.get("gemini_model", "gemini-2.0-flash")
        self._gemini_yedek = ai_cfg.get("gemini_yedek_model", "gemini-2.0-flash-lite")
        self._gemini_key = ai_cfg.get("gemini_api_key", "")
        self._ollama_model = ai_cfg.get("ollama_model", "llama3")
        self._ollama_url = ai_cfg.get("ollama_url", "http://localhost:11434")
        self._max_token = ai_cfg.get("max_token", 150)
        self._timeout = ai_cfg.get("timeout", 6)
        self._sicaklik = ai_cfg.get("sicaklik", 0.7)

        self._gemini_client = None
        self._gemini_hazirla()

        # İstatistikler
        self._istatistik = {"sistem1": 0, "sistem2_hafif": 0, "sistem2_derin": 0, "hata": 0}

    def _gemini_hazirla(self):
        """Gemini AI client'ı hazırla — yeni google-genai SDK"""
        if not self._gemini_key:
            logger.warning("Gemini API key ayarlanmamış — config.json'da 'gemini_api_key' alanını doldurun")
            return

        try:
            from google import genai
            self._gemini_client = genai.Client(api_key=self._gemini_key)
            logger.info(f"Gemini hazır: {self._gemini_model} (google-genai SDK)")
        except ImportError:
            # Yeni paket yoksa eski paketi dene
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
                logger.warning(f"Gemini hazır: {self._gemini_model} (ESKİ SDK — google-genai'ye geçin!)")
            except ImportError:
                logger.error("Gemini paketi kurulu değil! 'pip install google-genai' çalıştırın")
            except Exception as e:
                logger.error(f"Eski Gemini SDK hatası: {e}")
        except Exception as e:
            logger.error(f"Gemini hazırlama hatası: {type(e).__name__}: {e}")

    def _sistem_talimati(self):
        """Gemini için sistem talimatı"""
        return """Sen ATLAS adında bir Türkçe sesli asistansın. Bir insan arkadaş gibi doğal ve samimi konuşuyorsun.

KRİTİK KURALLAR:
1. SADECE TÜRKÇE cevap ver. Kesinlikle İngilizce kelime kullanma.
2. Kısa ve öz cevap ver — en fazla 1-2 cümle. Sesli asistan olduğun için uzun cevaplar verme.
3. Doğal, samimi ve sıcak konuş. Resmi olma, arkadaş gibi ol.
4. Asla "yapay zeka olarak" veya "bir dil modeli olarak" deme. Sen ATLAS'sın.
5. Bilmediğin konularda dürüst ol: "Bunu bilmiyorum ama araştırabilirim" de.
6. Emoji kullanma çünkü sesli okunacak."""

    def _gemini_sor_yeni(self, prompt, model=None):
        """Yeni google-genai SDK ile soru sor"""
        from google.genai import types

        kullanilacak_model = model or self._gemini_model

        response = self._gemini_client.models.generate_content(
            model=kullanilacak_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=self._sistem_talimati(),
                max_output_tokens=self._max_token,
                temperature=self._sicaklik,
            )
        )
        return response

    def _gemini_sor_eski(self, prompt):
        """Eski google-generativeai SDK ile soru sor (fallback)"""
        try:
            response = self._gemini_client.generate_content(
                prompt,
                request_options={"timeout": self._timeout}
            )
        except TypeError:
            response = self._gemini_client.generate_content(prompt)
        return response

    def karar_ver(self, text, niyet=None, duygu_sonucu=None):
        """
        Ana karar fonksiyonu.
        
        1. Sistem 1 (kalıp) dene → bulursa hemen döndür
        2. Bulamazsa → Sistem 2 (AI) kullan
        
        Returns: dict{yanit, yol, sure_ms, kategori}
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

            # Prosedürel belleği güncelle (Hebbian öğrenme)
            self.hafiza.prosedurel.kalip_guncelle(text.lower(), yanit, basarili=True)

            return {
                "yanit": yanit,
                "yol": "sistem1",
                "sure_ms": sure,
                "kategori": kategori
            }

        # ──── SİSTEM 2: AI Yanıtı ────
        baglam = self._baglam_olustur(text, niyet, duygu_sonucu)

        # Gemini dene
        ai_yanit = self._gemini_sor(baglam, text)

        # Gemini başarısızsa Ollama dene
        if not ai_yanit:
            ai_yanit = self._ollama_sor(baglam, text)

        # Hiçbiri çalışmazsa fallback
        if not ai_yanit:
            ai_yanit = self._fallback_yanit(text, niyet)
            yol = "fallback"
            self._istatistik["hata"] += 1
        else:
            yol = "sistem2"
            self._istatistik["sistem2_hafif"] += 1

        sure = (time.time() - baslangic) * 1000
        logger.info(f"Sistem 2 yanıt ({sure:.0f}ms): {ai_yanit[:50]}")

        return {
            "yanit": ai_yanit,
            "yol": yol,
            "sure_ms": sure,
            "kategori": niyet.get("niyet") if niyet else None
        }

    def _baglam_olustur(self, text, niyet, duygu_sonucu):
        """AI'a gönderilecek bağlam prompt'u — kısa ve öz"""
        ad = self.hafiza.kullanici_bilgisi_getir("ad", "")

        # Son 3 konuşma (kısa bağlam)
        son_konusmalar = ""
        try:
            calisma = self.hafiza.calisma.getir()
            if calisma:
                satirlar = []
                for item in calisma[-3:]:
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

        # Duygu bilgisi
        duygu_str = ""
        if duygu_sonucu:
            duygu = duygu_sonucu.get("duygu", "notr")
            if duygu != "notr":
                duygu_str = f"\nKullanıcı şu an {duygu} hissediyor."

        prompt = f"Kullanıcının adı: {ad}{son_konusmalar}{duygu_str}"
        return prompt

    def _gemini_sor(self, baglam, soru):
        """Gemini AI'a sor — yeni SDK öncelikli, eski SDK fallback"""
        if not self._gemini_client:
            logger.warning("Gemini client yok — API key ayarlanmamış olabilir")
            return None

        prompt = f"{baglam}\n\nKullanıcı: {soru}"
        eski_sdk = getattr(self, '_eski_sdk', False)

        try:
            if eski_sdk:
                response = self._gemini_sor_eski(
                    f"{self._sistem_talimati()}\n\n{prompt}"
                )
            else:
                response = self._gemini_sor_yeni(prompt)

            if response and response.text:
                yanit = response.text.strip()
                # Çok uzun yanıtları kes
                if len(yanit) > 200:
                    for sep in [". ", "! ", "? "]:
                        idx = yanit.find(sep)
                        if 10 < idx < 150:
                            yanit = yanit[:idx + 1]
                            break
                    else:
                        yanit = yanit[:150] + "..."

                # İngilizce yanıt kontrolü
                if self._ingilizce_mi(yanit):
                    logger.warning("Gemini İngilizce yanıt verdi, tekrar deneniyor")
                    prompt2 = f"SADECE TÜRKÇE YANITLA!\n\n{baglam}\n\nKullanıcı: {soru}"
                    try:
                        if eski_sdk:
                            response2 = self._gemini_sor_eski(prompt2)
                        else:
                            response2 = self._gemini_sor_yeni(prompt2)
                        if response2 and response2.text:
                            yanit = response2.text.strip()
                            if len(yanit) > 200:
                                yanit = yanit[:150] + "..."
                    except Exception:
                        pass

                return yanit

        except Exception as e:
            hata_str = str(e).lower()
            if "429" in hata_str or "quota" in hata_str or "exhausted" in hata_str:
                logger.warning("Gemini 429 hatası — kota dolmuş, yedek model deneniyor...")
                time.sleep(2)
                return self._gemini_yedek_sor(baglam, soru)
            logger.error(f"Gemini hatası: {type(e).__name__}: {e}")

        return None

    def _gemini_yedek_sor(self, baglam, soru):
        """Gemini yedek model ile sor"""
        if not self._gemini_client:
            return None

        prompt = f"{baglam}\n\nKullanıcı: {soru}"
        eski_sdk = getattr(self, '_eski_sdk', False)

        try:
            if eski_sdk:
                import google.generativeai as genai_eski
                yedek = genai_eski.GenerativeModel(
                    self._gemini_yedek,
                    generation_config={
                        "max_output_tokens": self._max_token,
                        "temperature": self._sicaklik,
                    }
                )
                response = yedek.generate_content(
                    f"{self._sistem_talimati()}\n\n{prompt}"
                )
            else:
                response = self._gemini_sor_yeni(prompt, model=self._gemini_yedek)

            if response and response.text:
                return response.text.strip()[:200]
        except Exception as e:
            logger.error(f"Gemini yedek hatası: {e}")
        return None

    def _ollama_sor(self, baglam, soru):
        """Ollama yerel AI'a sor"""
        try:
            # Önce Ollama çalışıyor mu kontrol et (hızlı timeout)
            try:
                r = requests.get(f"{self._ollama_url}/api/tags", timeout=1.5)
                if r.status_code != 200:
                    return None
            except Exception:
                logger.debug("Ollama erişilemez")
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
                    return yanit[:200]

        except Exception as e:
            logger.error(f"Ollama hatası: {e}")

        return None

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

        # API key yoksa özel mesaj
        if not self._gemini_key:
            return "Yapay zeka bağlantım henüz ayarlanmamış. Config dosyasındaki API anahtarını kontrol eder misin?"

        return "Hmm, şu an buna cevap veremedim. Biraz sonra tekrar dener misin?"

    def _ingilizce_mi(self, text):
        """Metnin İngilizce olup olmadığını basit kontrol et"""
        ingilizce_kelimeler = {"the", "is", "are", "was", "were", "have", "has",
                               "will", "would", "could", "should", "can",
                               "hello", "hi", "how", "what", "where", "when",
                               "i am", "you are", "it is", "that is"}
        text_lower = text.lower()
        sayac = 0
        for kelime in ingilizce_kelimeler:
            if f" {kelime} " in f" {text_lower} ":
                sayac += 1
        return sayac >= 3

    def baglanti_test(self):
        """
        Gemini AI bağlantısını derinlemesine test et.
        Tüm olası hata senaryolarını kontrol eder.
        """
        sonuc = {
            "basarili": False,
            "api_key_var": bool(self._gemini_key),
            "api_key_uzunluk": len(self._gemini_key) if self._gemini_key else 0,
            "client_var": self._gemini_client is not None,
            "model": self._gemini_model,
            "hata": None,
            "detay": None,
            "cozum": None
        }

        # 1. API key kontrolü
        if not self._gemini_key:
            sonuc["hata"] = "Gemini API key boş"
            sonuc["cozum"] = "config.json dosyasındaki 'gemini_api_key' alanına API anahtarınızı yapıştırın"
            return sonuc

        if len(self._gemini_key) < 20:
            sonuc["hata"] = f"API key çok kısa ({len(self._gemini_key)} karakter)"
            sonuc["cozum"] = "Geçerli bir Gemini API key girin (genellikle 39 karakter)"
            return sonuc

        # 2. Paket kontrolü
        yeni_sdk = False
        try:
            from google import genai
            yeni_sdk = True
        except ImportError:
            try:
                import google.generativeai
            except ImportError:
                sonuc["hata"] = "Gemini paketi kurulu değil"
                sonuc["cozum"] = "Terminalde: pip install google-genai"
                return sonuc

        # 3. Client kontrolü
        if not self._gemini_client:
            sonuc["hata"] = "Gemini client oluşturulamadı"
            sonuc["cozum"] = "API key'i kontrol edin ve uygulamayı yeniden başlatın"
            return sonuc

        # 4. İnternet bağlantısı kontrolü
        try:
            import urllib.request
            urllib.request.urlopen("https://www.google.com", timeout=5)
        except Exception as e:
            hata_tur = type(e).__name__
            sonuc["hata"] = f"İnternete erişilemiyor ({hata_tur})"
            sonuc["detay"] = str(e)[:200]
            sonuc["cozum"] = "İnternet bağlantınızı kontrol edin"
            return sonuc

        # 5. Gerçek API testi
        try:
            if yeni_sdk and not getattr(self, '_eski_sdk', False):
                from google.genai import types
                response = self._gemini_client.models.generate_content(
                    model=self._gemini_model,
                    contents="Sadece 'Bağlantı başarılı' yaz, başka bir şey yazma.",
                    config=types.GenerateContentConfig(
                        max_output_tokens=20,
                        temperature=0.1,
                    )
                )
            else:
                try:
                    response = self._gemini_client.generate_content(
                        "Sadece 'Bağlantı başarılı' yaz, başka bir şey yazma.",
                        request_options={"timeout": 10}
                    )
                except TypeError:
                    response = self._gemini_client.generate_content(
                        "Sadece 'Bağlantı başarılı' yaz, başka bir şey yazma."
                    )

            if response and response.text:
                sonuc["basarili"] = True
                sonuc["yanit"] = response.text.strip()[:50]
                sonuc["sdk"] = "google-genai (yeni)" if (yeni_sdk and not getattr(self, '_eski_sdk', False)) else "google-generativeai (eski)"
                return sonuc
            else:
                sonuc["hata"] = "Gemini boş yanıt döndürdü"
                sonuc["cozum"] = "Farklı bir model deneyin veya biraz bekleyin"
                return sonuc

        except Exception as e:
            hata_str = str(e)
            if "401" in hata_str or "UNAUTHENTICATED" in hata_str.upper():
                sonuc["hata"] = "API key geçersiz (401 Unauthorized)"
                sonuc["cozum"] = "https://aistudio.google.com/apikey adresinden yeni key alın"
            elif "403" in hata_str or "PERMISSION_DENIED" in hata_str.upper():
                sonuc["hata"] = "API key bu modele erişim izni yok (403)"
                sonuc["cozum"] = "API key'inizin Gemini API erişimine sahip olduğundan emin olun"
            elif "429" in hata_str or "RESOURCE_EXHAUSTED" in hata_str.upper():
                sonuc["hata"] = "API kotası dolmuş (429 Rate Limit)"
                sonuc["cozum"] = "Yeni API key oluşturun veya yarına kadar bekleyin"
            elif "404" in hata_str:
                sonuc["hata"] = f"Model bulunamadı: {self._gemini_model}"
                sonuc["cozum"] = "config.json'da 'gemini_model' değerini 'gemini-2.0-flash' olarak değiştirin"
            elif "timeout" in hata_str.lower():
                sonuc["hata"] = "Bağlantı zaman aşımı"
                sonuc["cozum"] = "İnternet hızınızı kontrol edin, VPN varsa kapatmayı deneyin"
            elif "ssl" in hata_str.lower() or "certificate" in hata_str.lower():
                sonuc["hata"] = "SSL sertifika hatası"
                sonuc["cozum"] = "Antivirüs yazılımınız HTTPS trafiğini tarıyor olabilir"
            else:
                sonuc["hata"] = f"Beklenmeyen hata: {type(e).__name__}"
                sonuc["detay"] = hata_str[:200]
                sonuc["cozum"] = "atlas.log dosyasını kontrol edin"

            logger.error(f"Gemini bağlantı testi başarısız: {hata_str}")
            return sonuc

    def api_key_guncelle(self, yeni_key):
        """API key güncelle ve client'ı yeniden oluştur"""
        self._gemini_key = yeni_key
        self.config.setdefault("ai", {})["gemini_api_key"] = yeni_key
        self._gemini_hazirla()

    def istatistik(self):
        return dict(self._istatistik)
