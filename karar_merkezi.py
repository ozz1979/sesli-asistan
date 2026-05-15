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
        self._gemini_yedek = ai_cfg.get("gemini_yedek_model", "gemini-1.5-flash")
        self._gemini_key = ai_cfg.get("gemini_api_key", "")
        self._ollama_model = ai_cfg.get("ollama_model", "llama3")
        self._ollama_url = ai_cfg.get("ollama_url", "http://localhost:11434")
        self._max_token = ai_cfg.get("max_token", 150)
        self._timeout = ai_cfg.get("timeout", 10)
        self._sicaklik = ai_cfg.get("sicaklik", 0.7)

        self._gemini_client = None
        self._gemini_hazirla()

        # İstatistikler
        self._istatistik = {"sistem1": 0, "sistem2_hafif": 0, "sistem2_derin": 0, "hata": 0}

    def _gemini_hazirla(self):
        """Gemini AI client'ı hazırla"""
        if not self._gemini_key:
            logger.warning("Gemini API key ayarlanmamış")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self._gemini_key)
            self._gemini_client = genai.GenerativeModel(
                self._gemini_model,
                generation_config={
                    "max_output_tokens": self._max_token,
                    "temperature": self._sicaklik,
                }
            )
            logger.info(f"Gemini hazır: {self._gemini_model}")
        except Exception as e:
            logger.error(f"Gemini hazırlama hatası: {e}")

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
        # Bağlam oluştur
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
        """AI'a gönderilecek bağlam prompt'u oluştur"""
        ad = self.hafiza.kullanici_bilgisi_getir("ad", "")

        # Hafıza bağlamı
        hafiza_baglam = self.hafiza.baglam_olustur()

        # Duygu bilgisi
        duygu_str = ""
        if duygu_sonucu:
            duygu = duygu_sonucu.get("duygu", "notr")
            if duygu != "notr":
                duygu_str = f"\nKullanıcının mevcut duygu durumu: {duygu}"

        prompt = f"""Sen ATLAS adında bir Türkçe sesli asistansın. 
Kullanıcının adı: {ad}
{hafiza_baglam}
{duygu_str}

KRİTİK KURALLAR:
1. SADECE TÜRKÇE YANITLA. Kesinlikle İngilizce kullanma.
2. Kısa ve öz cevap ver (1-3 cümle).
3. Doğal, samimi ve sıcak bir dil kullan.
4. Kullanıcıya adıyla hitap et.
5. Bilmediğin konularda dürüst ol, "Bunu bilmiyorum ama araştırabilirim" de.
6. Asla "yapay zeka olarak" veya "bir dil modeli olarak" deme. Sen ATLAS'sın.
"""
        return prompt

    def _gemini_sor(self, baglam, soru):
        """Gemini AI'a sor"""
        if not self._gemini_client:
            return None

        try:
            prompt = f"{baglam}\n\nKullanıcı: {soru}\nATLAS:"
            response = self._gemini_client.generate_content(
                prompt,
                request_options={"timeout": self._timeout}
            )

            if response and response.text:
                yanit = response.text.strip()
                # İngilizce yanıt kontrolü
                if self._ingilizce_mi(yanit):
                    logger.warning("Gemini İngilizce yanıt verdi, tekrar deneniyor")
                    prompt2 = f"{baglam}\n\nÖNEMLİ: SADECE TÜRKÇE YANITLA!\n\nKullanıcı: {soru}\nATLAS:"
                    response2 = self._gemini_client.generate_content(
                        prompt2,
                        request_options={"timeout": self._timeout}
                    )
                    if response2 and response2.text:
                        yanit = response2.text.strip()

                return yanit

        except Exception as e:
            hata_str = str(e).lower()
            if "429" in hata_str or "quota" in hata_str:
                logger.warning("Gemini 429 hatası, 3s bekleniyor...")
                time.sleep(3)
                # Yedek model dene
                return self._gemini_yedek_sor(baglam, soru)
            logger.error(f"Gemini hatası: {e}")

        return None

    def _gemini_yedek_sor(self, baglam, soru):
        """Gemini yedek model ile sor"""
        try:
            import google.generativeai as genai
            yedek = genai.GenerativeModel(
                self._gemini_yedek,
                generation_config={
                    "max_output_tokens": self._max_token,
                    "temperature": self._sicaklik,
                }
            )
            prompt = f"{baglam}\n\nKullanıcı: {soru}\nATLAS:"
            response = yedek.generate_content(
                prompt,
                request_options={"timeout": self._timeout}
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            logger.error(f"Gemini yedek hatası: {e}")
        return None

    def _ollama_sor(self, baglam, soru):
        """Ollama yerel AI'a sor"""
        try:
            # Önce Ollama çalışıyor mu kontrol et
            try:
                r = requests.get(f"{self._ollama_url}/api/tags", timeout=2)
                if r.status_code != 200:
                    return None
            except Exception:
                logger.debug("Ollama erişilemez")
                return None

            prompt = f"{baglam}\n\nKullanıcı: {soru}\nATLAS:"
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
                timeout=20
            )

            if response.status_code == 200:
                data = response.json()
                yanit = data.get("response", "").strip()
                if yanit:
                    return yanit

        except Exception as e:
            logger.error(f"Ollama hatası: {e}")

        return None

    def _fallback_yanit(self, text, niyet):
        """AI'lar çalışmıyorsa fallback yanıt"""
        niyet_adi = niyet.get("niyet", "") if niyet else ""

        fallback = {
            "saat_sor": None,  # kalıp motorunda halledilmeli
            "tarih_sor": None,
            "selam": "Merhaba! Sana nasıl yardımcı olabilirim?",
            "hal_hatir": "İyiyim, teşekkürler! Sen nasılsın?",
            "tesekkur": "Rica ederim!",
        }

        yanit = fallback.get(niyet_adi)
        if yanit:
            return yanit

        return "Şu an cevap veremiyorum, biraz sonra tekrar dener misin?"

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

    def api_key_guncelle(self, yeni_key):
        """API key güncelle ve client'ı yeniden oluştur"""
        self._gemini_key = yeni_key
        self.config.setdefault("ai", {})["gemini_api_key"] = yeni_key
        self._gemini_hazirla()

    def istatistik(self):
        return dict(self._istatistik)
