"""
ATLAS - Duygu Analizi
=====================
Beyin Karşılığı: Amigdala
Görev: Kullanıcının duygusal durumunu algılama

İnsan beyni duyguları 2 yoldan işler:
- Alt yol: Çok hızlı, kaba değerlendirme (12ms)
- Üst yol: Detaylı analiz (100ms+)

Bu modül kelime ve bağlam tabanlı basit duygu analizi yapar.
Faz 3'te ses tonu analizi eklenecek.
"""

from turkce import turkce_normalize

# Duygu sözlüğü — kelime → (duygu, şiddet)
DUYGU_SOZLUGU = {
    # Mutlu
    "harika": ("mutlu", 0.9), "süper": ("mutlu", 0.9),
    "muhteşem": ("mutlu", 0.9), "mükemmel": ("mutlu", 0.9),
    "güzel": ("mutlu", 0.6), "iyi": ("mutlu", 0.5),
    "sevindim": ("mutlu", 0.8), "mutluyum": ("mutlu", 0.9),
    "keyifli": ("mutlu", 0.7), "eğlenceli": ("mutlu", 0.7),
    "teşekkür": ("mutlu", 0.5), "sağol": ("mutlu", 0.5),
    "bravo": ("mutlu", 0.8), "helal": ("mutlu", 0.7),

    # Üzgün
    "üzgün": ("uzgun", 0.8), "kötü": ("uzgun", 0.7),
    "berbat": ("uzgun", 0.9), "mutsuz": ("uzgun", 0.8),
    "sıkıldım": ("uzgun", 0.6), "canım sıkılıyor": ("uzgun", 0.7),
    "yoruldum": ("uzgun", 0.5), "bitkin": ("uzgun", 0.7),
    "üzülme": ("uzgun", 0.4), "maalesef": ("uzgun", 0.5),

    # Sinirli
    "sinir": ("sinirli", 0.8), "kızgın": ("sinirli", 0.8),
    "saçmalık": ("sinirli", 0.7), "ya": ("sinirli", 0.3),
    "çalışmıyor": ("sinirli", 0.6), "bozuk": ("sinirli", 0.5),
    "hata": ("sinirli", 0.5), "sorun": ("sinirli", 0.4),
    "olmadı": ("sinirli", 0.4), "yanlış": ("sinirli", 0.5),

    # Meraklı
    "neden": ("merakli", 0.6), "nasıl": ("merakli", 0.5),
    "acaba": ("merakli", 0.7), "merak": ("merakli", 0.8),
    "ilginç": ("merakli", 0.7), "peki": ("merakli", 0.4),

    # Aceleyci
    "hemen": ("aceleci", 0.7), "çabuk": ("aceleci", 0.8),
    "acil": ("aceleci", 0.9), "hızlı": ("aceleci", 0.6),
    "bekleyemem": ("aceleci", 0.8),

    # Nötr
    "tamam": ("notr", 0.3), "evet": ("notr", 0.2),
    "hayır": ("notr", 0.2), "olur": ("notr", 0.2),
}


class DuyguAnalizi:
    """
    Amigdala — duygusal işleme merkezi.
    Kullanıcının duygusal durumunu kelime analizi ile tahmin eder.
    """

    def __init__(self):
        self._son_duygu = "notr"
        self._duygu_gecmisi = []

    def analiz_et(self, text):
        """
        Metinden duygu analizi yap.
        
        Returns: dict{duygu, siddet, guven}
        """
        if not text:
            return {"duygu": "notr", "siddet": 0.0, "guven": 0.0}

        text_lower = text.lower()
        text_norm = turkce_normalize(text)

        bulunan_duygular = []

        for kelime, (duygu, siddet) in DUYGU_SOZLUGU.items():
            kelime_norm = turkce_normalize(kelime)
            if kelime_norm in text_norm or kelime in text_lower:
                bulunan_duygular.append((duygu, siddet))

        if not bulunan_duygular:
            # Bağlamsal ipuçları
            # Kısa cümleler → aceleci veya sinirli olabilir
            if len(text.split()) <= 2 and text.endswith("!"):
                return {"duygu": "aceleci", "siddet": 0.5, "guven": 0.3}
            # Soru → meraklı
            if "?" in text:
                return {"duygu": "merakli", "siddet": 0.4, "guven": 0.3}
            return {"duygu": "notr", "siddet": 0.0, "guven": 0.2}

        # En güçlü duyguyu seç
        duygu_puanlari = {}
        for duygu, siddet in bulunan_duygular:
            if duygu not in duygu_puanlari:
                duygu_puanlari[duygu] = []
            duygu_puanlari[duygu].append(siddet)

        en_guclu = max(duygu_puanlari.items(), key=lambda x: max(x[1]))
        sonuc_duygu = en_guclu[0]
        sonuc_siddet = max(en_guclu[1])
        guven = min(0.9, len(bulunan_duygular) * 0.25 + 0.3)

        # Geçmişi güncelle
        self._son_duygu = sonuc_duygu
        self._duygu_gecmisi.append(sonuc_duygu)
        if len(self._duygu_gecmisi) > 20:
            self._duygu_gecmisi = self._duygu_gecmisi[-20:]

        return {
            "duygu": sonuc_duygu,
            "siddet": sonuc_siddet,
            "guven": guven
        }

    def yanit_tonu_ayarla(self, temel_yanit, duygu_sonucu):
        """Yanıtın tonunu kullanıcının duygusuna göre ayarla"""
        duygu = duygu_sonucu.get("duygu", "notr")
        siddet = duygu_sonucu.get("siddet", 0)

        if duygu == "sinirli" and siddet > 0.6:
            return temel_yanit  # Sakin, kısa cevap ver, emoji ekleme
        elif duygu == "uzgun" and siddet > 0.5:
            return temel_yanit  # Empatik, yumuşak cevap
        elif duygu == "mutlu" and siddet > 0.6:
            return temel_yanit + " 😊"
        elif duygu == "aceleci":
            # Kısa ve öz cevap
            if len(temel_yanit) > 100:
                cumleler = temel_yanit.split('.')
                return cumleler[0] + '.' if cumleler else temel_yanit
            return temel_yanit

        return temel_yanit

    @property
    def son_duygu(self):
        return self._son_duygu

    def genel_duygu_durumu(self):
        """Son konuşmalardaki genel duygu eğilimini döndür"""
        if not self._duygu_gecmisi:
            return "notr"
        sayac = {}
        for d in self._duygu_gecmisi[-10:]:
            sayac[d] = sayac.get(d, 0) + 1
        return max(sayac, key=sayac.get)
