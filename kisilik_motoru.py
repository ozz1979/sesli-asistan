"""
ATLAS - Kişilik Motoru
======================
Beyin Karşılığı: Ayna Nöronlar + Sosyal Biliş
Görev: Kullanıcı profili oluşturma, iletişim uyumu

Ayna nöronlar başkalarının davranışlarını simüle eder.
Bu modül kullanıcının iletişim tarzını öğrenir ve uyum sağlar.
"""

import json
import logging
from datetime import datetime

logger = logging.getLogger("ATLAS.kisilik")


class KisilikMotoru:
    """
    Ayna Nöronlar — kullanıcıyı tanı ve uyum sağla.
    """

    def __init__(self, hafiza):
        self.hafiza = hafiza
        self._profil = {
            "iletisim_tarzi": "samimi",   # samimi / resmi / kisa
            "detay_tercihi": "orta",      # kisa / orta / detayli
            "kullanim_saatleri": {},       # saat → sayı
            "sik_konular": {},             # konu → sayı
            "toplam_etkilesim": 0
        }
        self._yukle()

    def _yukle(self):
        """Profili semantik bellekten yükle"""
        kayitli = self.hafiza.semantik.getir("kisilik", "profil")
        if kayitli and isinstance(kayitli, dict):
            self._profil.update(kayitli)

    def _kaydet(self):
        """Profili semantik belleğe kaydet"""
        self.hafiza.semantik.kaydet("kisilik", "profil", self._profil)

    def etkilesim_kaydet(self, kullanici_mesaj, niyet=None):
        """Her etkileşimde profili güncelle"""
        self._profil["toplam_etkilesim"] += 1

        # Kullanım saati
        saat = str(datetime.now().hour)
        self._profil["kullanim_saatleri"][saat] = \
            self._profil["kullanim_saatleri"].get(saat, 0) + 1

        # Konu takibi
        if niyet:
            niyet_adi = niyet.get("niyet", "genel")
            self._profil["sik_konular"][niyet_adi] = \
                self._profil["sik_konular"].get(niyet_adi, 0) + 1

        # İletişim tarzı analizi
        if kullanici_mesaj:
            kelime_sayisi = len(kullanici_mesaj.split())
            if kelime_sayisi <= 3:
                self._profil["iletisim_tarzi"] = "kisa"
            elif kelime_sayisi > 10:
                self._profil["iletisim_tarzi"] = "detayli"

        # Her 5 etkileşimde kaydet
        if self._profil["toplam_etkilesim"] % 5 == 0:
            self._kaydet()

    def yanit_ayarla(self, yanit):
        """Yanıtı kullanıcının tercihine göre ayarla"""
        tarz = self._profil.get("iletisim_tarzi", "samimi")

        if tarz == "kisa" and len(yanit) > 100:
            # Kısa cevap tercih eden kullanıcı — ilk cümleyi ver
            cumleler = yanit.split('.')
            if cumleler:
                return cumleler[0].strip() + '.'

        return yanit

    def en_aktif_saat(self):
        """Kullanıcının en aktif olduğu saati döndür"""
        saatler = self._profil.get("kullanim_saatleri", {})
        if not saatler:
            return None
        return max(saatler, key=saatler.get)

    def en_sik_konu(self):
        """En sık sorulan konu"""
        konular = self._profil.get("sik_konular", {})
        if not konular:
            return None
        return max(konular, key=konular.get)

    @property
    def profil(self):
        return dict(self._profil)
