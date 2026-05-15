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


class KimlikTanima:
    """
    Temporal Lob — konuşmacı tanıma.
    Faz 1'de sadece isim tabanlı tanıma.
    Faz 4'te ses profili eklenecek.
    """

    def __init__(self, hafiza):
        self.hafiza = hafiza

    def kullanici_tanimli_mi(self):
        """Kullanıcı daha önce tanımlanmış mı?"""
        ad = self.hafiza.kullanici_bilgisi_getir("ad", "")
        return bool(ad)

    def kullanici_adi(self):
        """Kullanıcının adını döndür"""
        return self.hafiza.kullanici_bilgisi_getir("ad", "")

    def kullanici_kaydet(self, ad):
        """Kullanıcı adını kaydet"""
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
