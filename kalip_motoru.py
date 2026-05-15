"""
ATLAS - Kalıp Motoru (Sistem 1 - Hızlı Düşünme)
=================================================
Beyin Karşılığı: Bazal Ganglia
Görev: Bilinen sorulara anında yanıt (<100ms)

Kahneman'ın Sistem 1'i: Otomatik, bilinçdışı, kalıp tabanlı.
"Saat kaç?" → Düşünmeden saate bak
"Merhaba" → Hemen "Merhaba" de
"""

import re
import time
import random
from datetime import datetime
from turkce import turkce_normalize

# ============================================================
# KALIP VERİTABANI
# ============================================================

# Her kalıp: (regex_pattern, yanıt_listesi, kategori)
# Yanıt listesinden rastgele seçilir (doğallık için)

KALIPLAR = [
    # ──── SELAMLAŞMA ────
    (r"^(merhaba|meraba|mrb)\b", [
        "Merhaba {ad}! Nasılsın?",
        "Merhaba! Sana nasıl yardımcı olabilirim?",
        "Merhaba {ad}! Bugün sana ne yapabilirim?",
    ], "selam"),

    (r"^selam\b", [
        "Selam {ad}! Ne var ne yok?",
        "Selam! Nasılsın?",
        "Selamlar {ad}!",
    ], "selam"),

    (r"^(günaydın|gunaydin)\b", [
        "Günaydın {ad}! Umarım güzel bir güne başlıyorsun.",
        "Günaydın! Bugün hava {hava_emoji}. Hayırlı bir gün olsun!",
        "Günaydın {ad}! Kahve zamanı mı?",
    ], "selam"),

    (r"^iyi akşamlar\b", [
        "İyi akşamlar {ad}! Günün nasıl geçti?",
        "İyi akşamlar! Sana yardımcı olabilir miyim?",
    ], "selam"),

    (r"^iyi geceler\b", [
        "İyi geceler {ad}! Tatlı rüyalar.",
        "İyi geceler! Yarın görüşürüz.",
    ], "selam"),

    (r"^(hayırlı sabahlar|hayırlı günler)\b", [
        "Hayırlı günler {ad}! Bugün sana nasıl yardım edebilirim?",
        "Hayırlı günler! Her şey yolunda mı?",
    ], "selam"),

    # ──── HAL HATIR ────
    (r"(nasılsın|nasilsin|nası[l]sın)", [
        "İyiyim, teşekkür ederim! Sen nasılsın {ad}?",
        "Harikayım! Sen nasıl hissediyorsun?",
        "Çok iyiyim, sağol! Senin günün nasıl gidiyor?",
    ], "hal_hatir"),

    (r"(ne haber|naber|ne var ne yok)", [
        "İyilik! Senden ne haber {ad}?",
        "Her şey yolunda! Sen anlatsana, ne var ne yok?",
        "Bomba gibi! Sana ne yapabilirim?",
    ], "hal_hatir"),

    (r"(iyi misin|iyimisin)", [
        "Evet, gayet iyiyim! Teşekkürler. Sen nasılsın?",
        "Süper iyiyim! Senin için ne yapabilirim?",
    ], "hal_hatir"),

    (r"(keyifler nasıl|moraller nasıl)", [
        "Keyifler yerinde! Sen nasıl hissediyorsun?",
        "Moraller çok iyi! Seninkiler nasıl {ad}?",
    ], "hal_hatir"),

    # ──── TEŞEKKÜR / VEDALAŞMA ────
    (r"(teşekkür|sağol|sağ ol|eyvallah|mersi)", [
        "Rica ederim {ad}! Başka bir şey var mı?",
        "Ne demek, her zaman!",
        "Rica ederim! Yardımcı olabildiysem ne mutlu.",
    ], "tesekkur"),

    (r"(görüşürüz|hoşça kal|hoşçakal|bay bay|bye)", [
        "Görüşürüz {ad}! İyi günler!",
        "Hoşça kal! Bana ihtiyacın olursa buradayım.",
        "Görüşmek üzere {ad}!",
    ], "veda"),

    # ──── SAAT / TARİH ────
    (r"saat\s*kaç", [
        "Şu an saat {saat}.",
        "Saat {saat} {ad}.",
    ], "saat"),

    (r"(bugün\s*(günlerden|ne\s*gün|hangi\s*gün)|hangi\s*gün)", [
        "Bugün {gun}, {tarih}.",
        "Bugün {gun}. {tarih}.",
    ], "tarih"),

    (r"(bugün\s*ayın\s*kaçı|tarih\s*ne|bugünün\s*tarihi)", [
        "Bugünün tarihi {tarih}.",
        "{tarih}, {gun}.",
    ], "tarih"),

    # ──── KENDİNİ TANITMA ────
    (r"(adın\s*ne|ismin\s*ne|sen\s*kimsin|kendini\s*tanıt)", [
        "Ben ATLAS! Senin kişisel yapay zeka asistanınım. Her konuda sana yardımcı olmak için buradayım.",
        "Adım ATLAS. Senin dijital asistanınım {ad}. Bana her şeyi sorabilirsin!",
    ], "tanitim"),

    (r"(ne yapabilirsin|neler yapabilirsin|yeteneklerin)", [
        "Saat ve tarih söyleyebilir, müzik açabilir, program çalıştırabilir, internette araştırma yapabilir, sorularını cevaplayabilir ve seninle sohbet edebilirim! Ne yapmamı istersin?",
        "Bilgisayarını kontrol edebilir, sorularına cevap verebilir, hesap yapabilir, hatırlatma kurabilir ve seninle her konuda sohbet edebilirim {ad}!",
    ], "tanitim"),

    # ──── OLUMLU YANIT ────
    (r"^(evet|tamam|olur|peki|tabi|tabii|elbette)\b", [
        "Tamam {ad}, devam ediyorum!",
        "Anladım, hemen yapıyorum!",
    ], "onay"),

    # ──── OLUMSUZ YANIT ────
    (r"^(hayır|yok|istemiyorum|olmaz|iptal)\b", [
        "Tamam, anladım. Başka bir isteğin var mı?",
        "Peki, iptal ediyorum. Başka ne yapabilirim?",
    ], "ret"),

    # ──── BASİT HESAPLAMALAR ────
    (r"(\d+)\s*[\+\+artı]\s*(\d+)", [
        "Sonuç: {hesap_sonuc}",
        "{hesap_sonuc}.",
    ], "hesap"),

    (r"(\d+)\s*[\-\-eksi]\s*(\d+)", [
        "Sonuç: {hesap_sonuc}",
        "{hesap_sonuc}.",
    ], "hesap"),

    (r"(\d+)\s*[çarpıx\*]\s*(\d+)", [
        "Sonuç: {hesap_sonuc}",
        "{hesap_sonuc}.",
    ], "hesap"),

    # ──── ESPRI / ŞAKA ────
    (r"(bir? (fıkra|şaka|espri)\s*(anlat|söyle))", [
        "Bilgisayar neden üşümez? Çünkü Windows'u var! 😄",
        "Yapay zeka neden yorulmaz? Çünkü hep şarjda! 😄",
        "Robot doktora gider. Doktor sorar: 'Neyin var?' Robot: 'Virusum var doktor!' 😄",
    ], "espri"),

    # ──── ATLAS'A SESLENME ────
    (r"^atlas\s*$", [
        "Evet {ad}, buradayım! Seni dinliyorum.",
        "Buradayım! Ne yapabilirim senin için?",
        "Evet, buradayım {ad}! Söyle bakalım.",
    ], "tetik"),
]

# ============================================================
# GÜNLER VE AYLAR (Türkçe)
# ============================================================

GUNLER = {
    0: "Pazartesi", 1: "Salı", 2: "Çarşamba", 3: "Perşembe",
    4: "Cuma", 5: "Cumartesi", 6: "Pazar"
}

AYLAR = {
    1: "Ocak", 2: "Şubat", 3: "Mart", 4: "Nisan",
    5: "Mayıs", 6: "Haziran", 7: "Temmuz", 8: "Ağustos",
    9: "Eylül", 10: "Ekim", 11: "Kasım", 12: "Aralık"
}


class KalipMotoru:
    """
    Bazal Ganglia — otomatik kalıp eşleştirme motoru.
    Bilinen sorulara düşünmeden anında cevap verir (Sistem 1).
    """

    def __init__(self, hafiza=None):
        self.hafiza = hafiza
        self._kaliplar = KALIPLAR
        self._sayac = {}  # Kalıp kullanım sayacı

    def eslestirir(self, text):
        """
        Metni kalıplarla eşleştir.
        
        Returns: (yanit_metni, kategori, guven) veya (None, None, 0)
        """
        if not text:
            return None, None, 0.0

        text_lower = text.lower().strip()
        text_norm = turkce_normalize(text)

        for pattern, yanitlar, kategori in self._kaliplar:
            try:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if not match:
                    match = re.search(pattern, text_norm, re.IGNORECASE)
                if match:
                    # Yanıt seç
                    yanit = random.choice(yanitlar)
                    # Değişkenleri doldur
                    yanit = self._degisken_doldur(yanit, text, match)
                    # Sayacı güncelle
                    self._sayac[kategori] = self._sayac.get(kategori, 0) + 1
                    return yanit, kategori, 0.9
            except Exception:
                continue

        # Prosedürel bellekte ara
        if self.hafiza:
            kalip = self.hafiza.prosedurel.kalip_bul(text_lower)
            if kalip and kalip.get("guc", 0) >= 1.0:
                return kalip["yanit"], "prosedurel", 0.7

        return None, None, 0.0

    def _degisken_doldur(self, yanit, text, match=None):
        """Yanıt şablonundaki değişkenleri doldur"""
        simdi = datetime.now()

        # Kullanıcı adı
        ad = ""
        if self.hafiza:
            ad = self.hafiza.kullanici_bilgisi_getir("ad", "")
        yanit = yanit.replace("{ad}", ad)

        # Saat
        saat = simdi.strftime("%H:%M")
        yanit = yanit.replace("{saat}", saat)

        # Gün
        gun = GUNLER.get(simdi.weekday(), "")
        yanit = yanit.replace("{gun}", gun)

        # Tarih
        ay = AYLAR.get(simdi.month, "")
        tarih = f"{simdi.day} {ay} {simdi.year}"
        yanit = yanit.replace("{tarih}", tarih)

        # Hava emoji (basit saat bazlı)
        if simdi.hour < 6:
            hava = "🌙"
        elif simdi.hour < 12:
            hava = "☀️"
        elif simdi.hour < 18:
            hava = "🌤️"
        else:
            hava = "🌙"
        yanit = yanit.replace("{hava_emoji}", hava)

        # Hesaplama
        if "{hesap_sonuc}" in yanit and match:
            try:
                groups = match.groups()
                if len(groups) >= 2:
                    a, b = int(groups[0]), int(groups[1])
                    if "artı" in text or "+" in text:
                        sonuc = a + b
                    elif "eksi" in text or "-" in text:
                        sonuc = a - b
                    elif "çarpı" in text or "*" in text or "x" in text:
                        sonuc = a * b
                    else:
                        sonuc = a + b
                    yanit = yanit.replace("{hesap_sonuc}", str(sonuc))
            except Exception:
                yanit = yanit.replace("{hesap_sonuc}", "hesaplayamadım")

        # Boş değişkenleri temizle
        yanit = re.sub(r'\{[^}]+\}', '', yanit)
        yanit = re.sub(r'\s+', ' ', yanit).strip()

        return yanit

    def istatistik(self):
        """Kalıp kullanım istatistiklerini döndür"""
        return dict(self._sayac)
