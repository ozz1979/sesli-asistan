"""
ATLAS - Kimlik Tanıma
=====================
Beyin Karşılığı: Temporal Lob (ses tanıma alanı)
Görev: Konuşmacı ses profili oluşturma ve doğrulama

İnsan beyni sağ temporal lobda konuşmacının ses özelliklerini
(pitch, formant, hız) analiz ederek kimlik belirler.

Faz 1: Temel yapı (placeholder)
Faz 4: Tam ses profili ve çoklu konuşmacı desteği
"""

import logging

logger = logging.getLogger("ATLAS.kimlik")


YASAK_ISIMLER = {
    "dolar", "euro", "sterlin", "atlas", "google", "chrome", "hesap",
    "not", "kur", "para", "hava", "saat", "tarih", "ekran", "ses",
    "tamam", "evet", "hayır", "merhaba", "selam", "günaydın",
}


class KimlikTanima:
    """
    Temporal Lob — konuşmacı tanıma.
    Faz 1'de sadece isim tabanlı tanıma.
    Faz 4'te ses profili eklenecek.
    """

    def __init__(self, hafiza):
        self.hafiza = hafiza
        # Başlangıçta hatalı isim kontrolü
        mevcut = self.kullanici_adi()
        if mevcut and mevcut.lower().strip() in YASAK_ISIMLER:
            logger.warning(f"Hatalı isim tespit edildi: '{mevcut}' — siliniyor")
            self.hafiza.kullanici_bilgisi_kaydet("ad", "")

    def kullanici_tanimli_mi(self):
        """Kullanıcı daha önce tanımlanmış mı?"""
        ad = self.hafiza.kullanici_bilgisi_getir("ad", "")
        return bool(ad)

    def kullanici_adi(self):
        """Kullanıcının adını döndür"""
        return self.hafiza.kullanici_bilgisi_getir("ad", "")

    def kullanici_kaydet(self, ad):
        """Kullanıcı adını kaydet (yasak kelime kontrolü ile)"""
        if not ad or ad.lower().strip() in YASAK_ISIMLER:
            logger.warning(f"Geçersiz isim reddedildi: '{ad}'")
            return False
        self.hafiza.kullanici_bilgisi_kaydet("ad", ad)
        self.hafiza.epizodik.olay_kaydet("ilk_tanisma", {
            "ad": ad,
            "aciklama": f"Kullanıcı kendini {ad} olarak tanıttı"
        })
        logger.info(f"Kullanıcı kaydedildi: {ad}")

    def profil_ozeti(self):
        """Kullanıcı profil özetini döndür"""
        return {
            "ad": self.kullanici_adi(),
            "tanimli": self.kullanici_tanimli_mi(),
        }
