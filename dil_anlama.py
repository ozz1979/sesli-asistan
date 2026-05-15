"""
ATLAS - Dil Anlama
==================
Beyin Karşılığı: Wernicke Alanı + Angular Girus
Görev: STT sonuçlarını anlamlandırma, Türkçe düzeltme, niyet çıkarma

İnsan beyninde Wernicke alanı kelimelerin anlamını çözer,
angular girus çoklu-modal entegrasyon yapar.
Bu modül STT çıktısını anlamlı, düzeltilmiş Türkçe'ye çevirir.
"""

import logging
from turkce import stt_duzelt, niyet_cikart, cumle_turu_belirle, isim_temizle_ve_duzelt
from ses_algilama import SesAlgilama

logger = logging.getLogger("ATLAS.dil")


class DilAnlama:
    """
    Wernicke Alanı — dil anlama merkezi.
    Ham STT çıktısını anlamlı, düzeltilmiş metne çevirir.
    """

    def __init__(self, ses_algilama: SesAlgilama, config=None):
        self.ses = ses_algilama
        self.config = config or {}
        self._son_metin = ""
        self._son_niyet = None

    def dinle_ve_anla(self, timeout=None):
        """
        Tam pipeline: Dinle → STT → Düzelt → Anla
        
        Returns: dict{
            ham_metin: STT'den gelen orijinal metin,
            duzeltilmis: Türkçe düzeltme sonrası,
            niyet: niyet analizi sonucu,
            cumle_turu: soru/emir/bilgi/selam,
            basarili: bool
        }
        """
        # 1. Ses yakala
        audio = self.ses.dinle(timeout=timeout)
        if not audio:
            return {
                "ham_metin": "",
                "duzeltilmis": "",
                "niyet": None,
                "cumle_turu": "belirsiz",
                "basarili": False
            }

        # 2. STT — ses → metin
        ham = self.ses.stt_google(audio)
        if not ham:
            return {
                "ham_metin": "",
                "duzeltilmis": "",
                "niyet": None,
                "cumle_turu": "belirsiz",
                "basarili": False
            }

        # 3. Türkçe düzeltme
        duzeltilmis = stt_duzelt(ham)
        logger.info(f"Ham: '{ham}' → Düzeltilmiş: '{duzeltilmis}'")

        # 4. Niyet çıkarma
        niyet = niyet_cikart(duzeltilmis)
        cumle_turu = cumle_turu_belirle(duzeltilmis)

        self._son_metin = duzeltilmis
        self._son_niyet = niyet

        return {
            "ham_metin": ham,
            "duzeltilmis": duzeltilmis,
            "niyet": niyet,
            "cumle_turu": cumle_turu,
            "basarili": True
        }

    def isim_dinle(self, timeout=None):
        """
        İsim dinleme modu — ilk tanışma için.
        STT sonucunu isim veritabanıyla eşleştirir.
        
        Returns: (isim, guven_skoru) veya (None, 0)
        """
        audio = self.ses.dinle(timeout=timeout or 5)
        if not audio:
            return None, 0.0

        ham = self.ses.stt_google(audio)
        if not ham:
            return None, 0.0

        logger.info(f"İsim STT ham: '{ham}'")

        # Türkçe isim eşleştirme
        isim, guven = isim_temizle_ve_duzelt(ham)
        logger.info(f"İsim düzeltme: '{ham}' → '{isim}' (güven: {guven:.2f})")

        return isim, guven

    @property
    def son_metin(self):
        return self._son_metin

    @property
    def son_niyet(self):
        return self._son_niyet
