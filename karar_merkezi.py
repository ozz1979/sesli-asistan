"""
ATLAS - Karar Merkezi
=====================
Beyin Karşılığı: Prefrontal Korteks
Görev: Gelen bilgiyi değerlendirip doğru yanıt yolunu seçmek

Kahneman'ın teorisi:
- Sistem 1 (Hızlı): Kalıp eşleştirme, otomatik → <100ms
- Sistem 2 Hafif: Basit AI yanıtı → 1-3s
- Sistem 2 Derin: Karmaşık AI + düşünme → 5-30s

AI Zinciri: Gemini → DeepSeek → Ollama → Fallback
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
    AI Zinciri: Gemini → DeepSeek → Ollama → Fallback
    """

    def __init__(self, kalip_motoru, hafiza, duygu, config=None):
        self.kalip = kalip_motoru
        self.hafiza = hafiza
        self.duygu = duygu
        self.config = config or {}

        ai_cfg = self.config.get("ai", {})
        self._gemini_model = ai_cfg.get("gemini_model", "gemini-2.0-flash")
        self._gemini_yedek = ai_cfg.get("gemini_yedek_model", "gemini-2.0-flash-lite")
        self._gemini_key = ai_cfg.get("gemini_api_key", "")
        self._deepseek_key = ai_cfg.get("deepseek_api_key", "")
        self._deepseek_model = ai_cfg.get("deepseek_model", "deepseek-chat")
        self._ollama_model = ai_cfg.get("ollama_model", "llama3")
        self._ollama_url = ai_cfg.get("ollama_url", "http://localhost:11434")
        self._max_token = ai_cfg.get("max_token", 150)
        self._timeout = ai_cfg.get("timeout", 8)
        self._sicaklik = ai_cfg.get("sicaklik", 0.7)

        self._gemini_client = None
        self._deepseek_client = None
        self._eski_sdk = False
        self._gemini_hazirla()
        self._deepseek_hazirla()

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

    # ══════════════════════════════════════════════════
    # SİSTEM TALİMATI
    # ══════════════════════════════════════════════════

    def _sistem_talimati(self):
        """AI modelleri için sistem talimatı"""
        return """Sen ATLAS adında bir Türkçe sesli asistansın. Bir insan arkadaş gibi doğal ve samimi konuşuyorsun.

KRİTİK KURALLAR:
1. SADECE TÜRKÇE cevap ver. Kesinlikle İngilizce kelime kullanma.
2. Kısa ve öz cevap ver — en fazla 1-2 cümle. Sesli asistan olduğun için uzun cevaplar verme.
3. Doğal, samimi ve sıcak konuş. Resmi olma, arkadaş gibi ol.
4. Asla "yapay zeka olarak" veya "bir dil modeli olarak" deme. Sen ATLAS'sın.
5. Bilmediğin konularda dürüst ol: "Bunu bilmiyorum ama araştırabilirim" de.
6. Emoji kullanma çünkü sesli okunacak."""

    # ══════════════════════════════════════════════════
    # ANA KARAR FONKSİYONU
    # ══════════════════════════════════════════════════

    def karar_ver(self, text, niyet=None, duygu_sonucu=None):
        """
        Ana karar fonksiyonu.
        1. Sistem 1 (kalıp) dene → bulursa hemen döndür
        2. Bulamazsa → Sistem 2 (AI zinciri) kullan
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

        # ──── SİSTEM 2: AI Zinciri ────
        baglam = self._baglam_olustur(text, niyet, duygu_sonucu)

        # Zincir: Gemini → DeepSeek → Ollama → Fallback
        ai_yanit = self._gemini_sor(baglam, text)

        if not ai_yanit:
            ai_yanit = self._deepseek_sor(baglam, text)

        if not ai_yanit:
            ai_yanit = self._ollama_sor(baglam, text)

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

    # ══════════════════════════════════════════════════
    # BAĞLAM OLUŞTURMA
    # ══════════════════════════════════════════════════

    def _baglam_olustur(self, text, niyet, duygu_sonucu):
        """AI'a gönderilecek bağlam prompt'u — kısa ve öz"""
        ad = self.hafiza.kullanici_bilgisi_getir("ad", "")

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

        duygu_str = ""
        if duygu_sonucu:
            duygu = duygu_sonucu.get("duygu", "notr")
            if duygu != "notr":
                duygu_str = f"\nKullanıcı şu an {duygu} hissediyor."

        return f"Kullanıcının adı: {ad}{son_konusmalar}{duygu_str}"

    # ══════════════════════════════════════════════════
    # YANITLARI TEMİZLEME
    # ══════════════════════════════════════════════════

    def _yanit_temizle(self, yanit):
        """Uzun yanıtları kes, temizle"""
        yanit = yanit.strip()
        if len(yanit) > 200:
            for sep in [". ", "! ", "? "]:
                idx = yanit.find(sep)
                if 10 < idx < 150:
                    yanit = yanit[:idx + 1]
                    break
            else:
                yanit = yanit[:150] + "..."
        return yanit

    def _ingilizce_mi(self, text):
        """Metnin İngilizce olup olmadığını basit kontrol et"""
        ingilizce_kelimeler = {"the", "is", "are", "was", "were", "have", "has",
                               "will", "would", "could", "should", "can",
                               "hello", "hi", "how", "what", "where", "when",
                               "i am", "you are", "it is", "that is"}
        text_lower = text.lower()
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
        if not self._gemini_client:
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
                logger.warning("Gemini kota dolmuş — DeepSeek'e geçiliyor...")
            else:
                logger.error(f"Gemini hatası: {type(e).__name__}: {e}")

        return None

    # ══════════════════════════════════════════════════
    # DEEPSEEK AI
    # ══════════════════════════════════════════════════

    def _deepseek_sor(self, baglam, soru):
        """DeepSeek AI'a sor — OpenAI uyumlu API"""
        if not self._deepseek_client:
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
            if "429" in hata_str or "quota" in hata_str:
                logger.warning("DeepSeek kota dolmuş — Ollama'ya geçiliyor...")
            else:
                logger.error(f"DeepSeek hatası: {type(e).__name__}: {e}")

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
                    return yanit[:200]

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

        if not self._gemini_key and not self._deepseek_key:
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

        # Sonuç
        if not sonuc["basarili"]:
            sonuc["hata"] = "Hiçbir AI bağlantısı çalışmıyor"
            sonuc["cozum"] = "config.json'da gemini_api_key veya deepseek_api_key girin"

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

    def istatistik(self):
        return dict(self._istatistik)
