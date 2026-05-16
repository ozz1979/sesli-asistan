"""
ATLAS - Öğrenme Motoru (Kendi Kendine Öğrenme)
===============================================
Beyin Karşılığı: Nöroplastisite + Hipokampüs + Prefrontal Korteks
Görev: Hatalardan öğrenme, kullanıcıyı daha iyi anlama, sürekli gelişim

İnsan beyni her deneyimden öğrenir:
- Hata yapınca → sinaptik bağlantılar güncellenir
- Tekrar edince → kalıplar güçlenir
- Geri bildirim → davranış düzeltilir
Bu modül aynı prensibi ATLAS'a kazandırır.
"""

import json
import os
import re
import time
import logging
from datetime import datetime, timedelta
from collections import Counter
from difflib import SequenceMatcher

logger = logging.getLogger("ATLAS.ogrenme")


# ============================================================
# DÜZELTME ALGILAMA
# ============================================================

# Kullanıcının "yanlış anladın" dediğini gösteren ifadeler
DUZELTME_TETIKLERI = [
    r"hayır\s+(?:dedim|öyle\s+değil|yanlış)",
    r"öyle\s+değil",
    r"yanlış\s+anlad[ıi]n?",
    r"anlamad[ıi]n",
    r"(?:onu|bunu)\s+demedim",
    r"tekrar\s+(?:söylüyorum|ediyorum)",
    r"(?:hayır|yok)\s+(?:ben|benim)",
    r"demek\s+istediğim",
    r"(?:şunu|bunu)\s+(?:kastetmiştim|kastettim|demek\s+istedim)",
    r"sana\s+(?:onu|bunu)\s+demedim",
    r"(?:hayır|yok)\s*,?\s*(?:ben\s+)?(?:dedim|söyledim)",
]

# Beğeni/onay ifadeleri — doğru anladığını gösteren
ONAY_TETIKLERI = [
    r"^(evet|tamam|doğru|aynen|güzel|harika|süper|bravo|helal)\b",
    r"^(teşekkür|sağol|sağ\s+ol|eyvallah|mersi)\b",
    r"işte\s+(?:bu|tam\s+bu|böyle)",
    r"(?:doğru|haklı)s[ıi]n",
    r"^(mükemmel|muhteşem|perfect)\b",
]

# Sabırsızlık/tekrar ifadeleri
SABIR_TETIKLERI = [
    r"(?:tekrar|gene|yine)\s+(?:söylüyorum|ediyorum|diyorum)",
    r"(?:bir\s+daha|tekrar)\s+dene",
    r"(?:niye|neden)\s+anlamıyorsun",
    r"(?:dinle|duy)\s+beni",
    r"(?:sana|hep)\s+(?:aynı\s+şeyi|aynısını)\s+söylüyorum",
]


class OgrenmeBellegi:
    """
    Öğrenme verilerini kalıcı olarak saklayan bellek.
    Her şeyi JSON dosyalarında tutar.
    """

    def __init__(self, dizin="hafiza/ogrenme"):
        self._dizin = dizin
        os.makedirs(dizin, exist_ok=True)

        # Alt dosyalar
        self._stt_dosya = os.path.join(dizin, "stt_duzeltmeleri.json")
        self._tercih_dosya = os.path.join(dizin, "tercihler.json")
        self._kalip_dosya = os.path.join(dizin, "ogrenilen_kaliplar.json")
        self._istatistik_dosya = os.path.join(dizin, "istatistikler.json")
        self._bilgi_dosya = os.path.join(dizin, "ogrenilen_bilgiler.json")

        # Bellek yükle
        self.stt_duzeltmeleri = self._yukle(self._stt_dosya, {})
        self.tercihler = self._yukle(self._tercih_dosya, {
            "yanit_stili": "samimi",      # samimi / resmi / kisa / detayli
            "tercih_konular": [],           # sık sorulan konular
            "sevdigi_yanitlar": [],         # beğendiği yanıt tipleri
            "sevmedigi_yanitlar": [],       # beğenmediği yanıt tipleri
            "gunluk_rutinler": {},          # saat bazlı rutinler
        })
        self.kaliplar = self._yukle(self._kalip_dosya, {})
        self.istatistikler = self._yukle(self._istatistik_dosya, {
            "toplam_etkilesim": 0,
            "basarili_anlama": 0,
            "basarisiz_anlama": 0,
            "duzeltme_sayisi": 0,
            "onay_sayisi": 0,
            "gunluk": {},
        })
        self.bilgiler = self._yukle(self._bilgi_dosya, {
            "kullanici_hakkinda": {},       # Kullanıcıdan öğrenilen bilgiler
            "ogrenilen_konular": [],        # Konuşmalardan öğrenilen konular
        })

    def _yukle(self, dosya, varsayilan):
        try:
            if os.path.exists(dosya):
                with open(dosya, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return varsayilan

    def _kaydet_dosya(self, dosya, veri):
        try:
            with open(dosya, 'w', encoding='utf-8') as f:
                json.dump(veri, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Öğrenme kayıt hatası: {e}")

    def kaydet_hepsi(self):
        """Tüm öğrenme verilerini diske kaydet"""
        self._kaydet_dosya(self._stt_dosya, self.stt_duzeltmeleri)
        self._kaydet_dosya(self._tercih_dosya, self.tercihler)
        self._kaydet_dosya(self._kalip_dosya, self.kaliplar)
        self._kaydet_dosya(self._istatistik_dosya, self.istatistikler)
        self._kaydet_dosya(self._bilgi_dosya, self.bilgiler)


class OgrenmeMotoru:
    """
    Nöroplastisite Motoru — ATLAS'ın kendi kendine öğrenme sistemi.

    3 katmanlı öğrenme:
    1. Anlık Öğrenme: Düzeltmelerden hemen öğren
    2. Oturum Öğrenme: Konuşma boyunca kalıpları fark et
    3. Uzun Vadeli Öğrenme: Günler boyunca tercihleri, rutinleri öğren
    """

    def __init__(self, hafiza=None, config=None):
        self.hafiza = hafiza
        self.config = config or {}
        self.bellek = OgrenmeBellegi()

        # Oturum içi takip
        self._son_kullanici_mesaji = ""
        self._son_asistan_yaniti = ""
        self._son_niyet = None
        self._duzeltme_modu = False
        self._oturum_konulari = Counter()
        self._oturum_basarili = 0
        self._oturum_basarisiz = 0

        logger.info(f"Öğrenme motoru başlatıldı — "
                     f"{len(self.bellek.stt_duzeltmeleri)} STT düzeltmesi, "
                     f"{len(self.bellek.kaliplar)} öğrenilmiş kalıp")

    # ============================================================
    # 1. ANLIK ÖĞRENME — Her mesajdan sonra
    # ============================================================

    def mesaj_analiz_et(self, kullanici_mesaji, asistan_yaniti, niyet=None):
        """
        Her etkileşimden sonra çağrılır.
        Kullanıcının tepkisini analiz et ve öğren.
        """
        self.bellek.istatistikler["toplam_etkilesim"] += 1
        bugun = datetime.now().strftime("%Y-%m-%d")
        gunluk = self.bellek.istatistikler.setdefault("gunluk", {})
        gunluk.setdefault(bugun, {"etkilesim": 0, "basarili": 0, "basarisiz": 0})
        gunluk[bugun]["etkilesim"] += 1

        # Niyet takibi
        if niyet:
            niyet_adi = niyet.get("niyet", "genel") if isinstance(niyet, dict) else str(niyet)
            self._oturum_konulari[niyet_adi] += 1

        # Önceki mesaja tepki analizi
        if self._son_kullanici_mesaji:
            tepki = self._tepki_analiz_et(kullanici_mesaji)

            if tepki == "duzeltme":
                self._duzeltme_isle(kullanici_mesaji)
            elif tepki == "onay":
                self._onay_isle()
            elif tepki == "sabirsizlik":
                self._sabirsizlik_isle(kullanici_mesaji)

        # Saat bazlı rutin öğrenme
        self._rutin_ogren(kullanici_mesaji, niyet)

        # Bilgi çıkarma
        self._bilgi_cikar(kullanici_mesaji)

        # Güncelle
        self._son_kullanici_mesaji = kullanici_mesaji
        self._son_asistan_yaniti = asistan_yaniti
        self._son_niyet = niyet

        # Periyodik kaydet (her 5 etkileşimde)
        if self.bellek.istatistikler["toplam_etkilesim"] % 5 == 0:
            self.bellek.kaydet_hepsi()

    def _tepki_analiz_et(self, mesaj):
        """Kullanıcının mesajının bir düzeltme mi, onay mı, sabırsızlık mı olduğunu belirle"""
        mesaj_lower = mesaj.lower().strip()

        for kalip in DUZELTME_TETIKLERI:
            if re.search(kalip, mesaj_lower):
                return "duzeltme"

        for kalip in SABIR_TETIKLERI:
            if re.search(kalip, mesaj_lower):
                return "sabirsizlik"

        for kalip in ONAY_TETIKLERI:
            if re.search(kalip, mesaj_lower):
                return "onay"

        return "notr"

    def _duzeltme_isle(self, duzeltme_mesaji):
        """Kullanıcı bizi düzeltti — öğren!"""
        logger.info(f"DÜZELTME ALGILANDI: '{duzeltme_mesaji}' (önceki: '{self._son_kullanici_mesaji}')")

        self.bellek.istatistikler["duzeltme_sayisi"] += 1
        self.bellek.istatistikler["basarisiz_anlama"] += 1
        self._oturum_basarisiz += 1

        bugun = datetime.now().strftime("%Y-%m-%d")
        gunluk = self.bellek.istatistikler.get("gunluk", {}).get(bugun, {})
        gunluk["basarisiz"] = gunluk.get("basarisiz", 0) + 1

        # STT düzeltme kalıbı kaydet
        # Eğer kullanıcı bir kelimeyi tekrar söylediyse, önceki STT çıktısı yanlıştı
        self._stt_duzeltme_ogren(self._son_kullanici_mesaji, duzeltme_mesaji)

        # Başarısız yanıt kalıbını kaydet (bir daha aynı hatayı yapma)
        self._basarisiz_yanit_kaydet(
            self._son_kullanici_mesaji,
            self._son_asistan_yaniti,
            duzeltme_mesaji
        )

        # Tercih güncelle — beğenmediği yanıt tipi
        if self._son_asistan_yaniti:
            sevmedigi = self.bellek.tercihler.setdefault("sevmedigi_yanitlar", [])
            sevmedigi.append({
                "soru": self._son_kullanici_mesaji,
                "yanit": self._son_asistan_yaniti[:100],
                "tarih": datetime.now().isoformat()
            })
            # Son 50 kayıt tut
            self.bellek.tercihler["sevmedigi_yanitlar"] = sevmedigi[-50:]

        self._duzeltme_modu = True

    def _onay_isle(self):
        """Kullanıcı yanıtımızı beğendi — bu kalıbı güçlendir"""
        logger.info(f"ONAY ALGILANDI: Önceki yanıt beğenildi")

        self.bellek.istatistikler["onay_sayisi"] += 1
        self.bellek.istatistikler["basarili_anlama"] += 1
        self._oturum_basarili += 1

        bugun = datetime.now().strftime("%Y-%m-%d")
        gunluk = self.bellek.istatistikler.get("gunluk", {}).get(bugun, {})
        gunluk["basarili"] = gunluk.get("basarili", 0) + 1

        # Başarılı kalıp güçlendir
        if self._son_kullanici_mesaji and self._son_asistan_yaniti:
            anahtar = self._son_kullanici_mesaji.lower().strip()
            kalip = self.bellek.kaliplar.get(anahtar, {
                "yanit": self._son_asistan_yaniti,
                "guc": 0.5,
                "basari": 0,
                "basarisizlik": 0,
            })
            kalip["guc"] = min(kalip.get("guc", 0.5) + 0.2, 5.0)
            kalip["basari"] = kalip.get("basari", 0) + 1
            kalip["yanit"] = self._son_asistan_yaniti
            kalip["son_onay"] = datetime.now().isoformat()
            self.bellek.kaliplar[anahtar] = kalip

            # Tercih — beğendiği yanıt tipi
            sevdigi = self.bellek.tercihler.setdefault("sevdigi_yanitlar", [])
            sevdigi.append({
                "soru": self._son_kullanici_mesaji,
                "yanit": self._son_asistan_yaniti[:100],
                "tarih": datetime.now().isoformat()
            })
            self.bellek.tercihler["sevdigi_yanitlar"] = sevdigi[-50:]

        self._duzeltme_modu = False

    def _sabirsizlik_isle(self, mesaj):
        """Kullanıcı sabırsız — anlama sorunu var"""
        logger.warning(f"SABIRSIZLIK ALGILANDI: '{mesaj}'")
        self.bellek.istatistikler["basarisiz_anlama"] += 1
        self._oturum_basarisiz += 1
        self._duzeltme_modu = True

    # ============================================================
    # STT DÜZELTME ÖĞRENME
    # ============================================================

    def _stt_duzeltme_ogren(self, yanlis_metin, duzeltme_mesaji):
        """STT'nin yanlış duyduğu kalıpları öğren"""
        if not yanlis_metin or not duzeltme_mesaji:
            return

        yanlis_lower = yanlis_metin.lower().strip()
        duzeltme_lower = duzeltme_mesaji.lower().strip()

        # Eğer düzeltme mesajında açık bir doğru versiyon varsa
        # "hayır, X dedim" → X'i öğren
        m = re.search(r"(?:hayır|yok),?\s*(.+?)\s+(?:dedim|söyledim|demek\s+istedim)", duzeltme_lower)
        if m:
            dogru = m.group(1).strip()
            if dogru and dogru != yanlis_lower:
                self.bellek.stt_duzeltmeleri[yanlis_lower] = {
                    "dogru": dogru,
                    "tarih": datetime.now().isoformat(),
                    "sayi": self.bellek.stt_duzeltmeleri.get(yanlis_lower, {}).get("sayi", 0) + 1
                }
                logger.info(f"STT düzeltme öğrenildi: '{yanlis_lower}' → '{dogru}'")

        # "demek istediğim X" kalıbı
        m = re.search(r"demek\s+istediğim\s+(.+)", duzeltme_lower)
        if m:
            dogru = m.group(1).strip()
            if dogru:
                self.bellek.stt_duzeltmeleri[yanlis_lower] = {
                    "dogru": dogru,
                    "tarih": datetime.now().isoformat(),
                    "sayi": self.bellek.stt_duzeltmeleri.get(yanlis_lower, {}).get("sayi", 0) + 1
                }

    def stt_duzelt(self, ham_metin):
        """Öğrenilmiş STT düzeltmelerini uygula"""
        if not ham_metin:
            return ham_metin

        metin_lower = ham_metin.lower().strip()

        # Tam eşleşme
        duzeltme = self.bellek.stt_duzeltmeleri.get(metin_lower)
        if duzeltme:
            logger.info(f"Öğrenilmiş STT düzeltme uygulandı: '{metin_lower}' → '{duzeltme['dogru']}'")
            return duzeltme["dogru"]

        # Kelime bazlı düzeltme
        kelimeler = metin_lower.split()
        degisti = False
        for i, kelime in enumerate(kelimeler):
            duzeltme = self.bellek.stt_duzeltmeleri.get(kelime)
            if duzeltme and duzeltme.get("sayi", 0) >= 2:  # En az 2 kez düzeltilmiş olmalı
                kelimeler[i] = duzeltme["dogru"]
                degisti = True

        if degisti:
            return " ".join(kelimeler)

        return ham_metin

    # ============================================================
    # BAŞARISIZ YANIT KAYDI
    # ============================================================

    def _basarisiz_yanit_kaydet(self, soru, yanit, duzeltme):
        """Başarısız yanıtı kaydet — bir daha aynı hatayı yapma"""
        anahtar = soru.lower().strip()
        kalip = self.bellek.kaliplar.get(anahtar, {
            "guc": 0.5,
            "basari": 0,
            "basarisizlik": 0,
        })
        kalip["guc"] = max(kalip.get("guc", 0.5) - 0.3, 0.0)
        kalip["basarisizlik"] = kalip.get("basarisizlik", 0) + 1
        kalip["yanlis_yanit"] = yanit[:100]
        kalip["duzeltme"] = duzeltme[:100]
        kalip["son_hata"] = datetime.now().isoformat()
        self.bellek.kaliplar[anahtar] = kalip

    # ============================================================
    # 2. RUTİN ÖĞRENME — Zaman bazlı kalıplar
    # ============================================================

    def _rutin_ogren(self, mesaj, niyet):
        """Saat bazlı kullanıcı rutinlerini öğren"""
        saat = datetime.now().hour
        saat_str = str(saat)

        rutinler = self.bellek.tercihler.setdefault("gunluk_rutinler", {})
        saat_veri = rutinler.setdefault(saat_str, Counter())

        # Niyet adını kaydet
        niyet_adi = "genel"
        if niyet:
            niyet_adi = niyet.get("niyet", "genel") if isinstance(niyet, dict) else str(niyet)

        if isinstance(saat_veri, dict):
            saat_veri[niyet_adi] = saat_veri.get(niyet_adi, 0) + 1
        rutinler[saat_str] = saat_veri

    def rutin_tahmin(self):
        """Şu anki saate göre kullanıcının ne yapacağını tahmin et"""
        saat = str(datetime.now().hour)
        rutinler = self.bellek.tercihler.get("gunluk_rutinler", {})
        saat_veri = rutinler.get(saat, {})

        if not saat_veri:
            return None

        # En sık yapılan aktivite
        if isinstance(saat_veri, dict):
            en_sik = max(saat_veri.items(), key=lambda x: x[1], default=(None, 0))
            if en_sik[1] >= 3:  # En az 3 kez yapılmış
                return en_sik[0]
        return None

    # ============================================================
    # 3. BİLGİ ÇIKARMA — Konuşmadan bilgi öğren
    # ============================================================

    def _semantik_kaydet(self, anahtar, deger):
        """Hafıza sisteminin semantik belleğine de kaydet (kalıcı)"""
        if self.hafiza:
            try:
                self.hafiza.kullanici_bilgisi_kaydet(anahtar, deger)
            except Exception:
                pass

    def _bilgi_cikar(self, mesaj):
        """Kullanıcının mesajından kişisel bilgi çıkar ve kaydet"""
        mesaj_lower = mesaj.lower().strip()

        # İsim öğrenme
        m = re.search(r"(?:benim?\s+)?ad[ıi]m\s+(\w+)", mesaj_lower)
        if m:
            isim = m.group(1).strip().title()
            self.bellek.bilgiler["kullanici_hakkinda"]["ad"] = isim
            self._semantik_kaydet("ad", isim)

        # Şehir öğrenme
        m = re.search(r"(?:ben\s+)?(\w+)['\']?(?:da|de|dan|den|lı|li|lu|lü)\s*(?:yaşıyorum|oturuyorum|kalıyorum)", mesaj_lower)
        if m:
            sehir = m.group(1).strip().title()
            self.bellek.bilgiler["kullanici_hakkinda"]["sehir"] = sehir
            self._semantik_kaydet("sehir", sehir)

        # Meslek öğrenme
        m = re.search(r"(?:ben\s+)?(\w+(?:\s+\w+)?)\s*(?:olarak\s+)?çalışıyorum", mesaj_lower)
        if m:
            meslek = m.group(1).strip()
            self.bellek.bilgiler["kullanici_hakkinda"]["meslek"] = meslek
            self._semantik_kaydet("meslek", meslek)

        # Yaş öğrenme
        m = re.search(r"(\d{1,3})\s*yaşındayım", mesaj_lower)
        if m:
            yas = int(m.group(1))
            if 5 < yas < 120:
                self.bellek.bilgiler["kullanici_hakkinda"]["yas"] = yas
                self._semantik_kaydet("yas", str(yas))

        # Doğum tarihi öğrenme
        # "4 temmuz 1979", "doğum tarihim 4 temmuz", "4/7/1979" vb.
        aylar = {"ocak":"01","şubat":"02","mart":"03","nisan":"04","mayıs":"05",
                 "haziran":"06","temmuz":"07","ağustos":"08","eylül":"09",
                 "ekim":"10","kasım":"11","aralık":"12"}
        m = re.search(r"(\d{1,2})\s+(ocak|şubat|mart|nisan|mayıs|haziran|temmuz|ağustos|eylül|ekim|kasım|aralık)\s*(\d{4})?", mesaj_lower)
        if m:
            gun, ay_ad = m.group(1), m.group(2)
            yil = m.group(3) if m.group(3) else ""
            tarih_str = f"{gun} {ay_ad.title()}" + (f" {yil}" if yil else "")
            self.bellek.bilgiler["kullanici_hakkinda"]["dogum_tarihi"] = tarih_str
            self._semantik_kaydet("dogum_tarihi", tarih_str)
        # Sayısal format: 4/7/1979
        m2 = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", mesaj_lower)
        if m2:
            tarih_str2 = f"{m2.group(1)}/{m2.group(2)}/{m2.group(3)}"
            self.bellek.bilgiler["kullanici_hakkinda"]["dogum_tarihi"] = tarih_str2
            self._semantik_kaydet("dogum_tarihi", tarih_str2)

        # Hobi öğrenme
        m = re.search(r"(?:hobim|hobilerim|severim|seviyorum)\s+(.+?)(?:\.|$)", mesaj_lower)
        if m:
            hobi = m.group(1).strip()
            hobiler = self.bellek.bilgiler["kullanici_hakkinda"].setdefault("hobiler", [])
            if hobi not in hobiler:
                hobiler.append(hobi)
                self.bellek.bilgiler["kullanici_hakkinda"]["hobiler"] = hobiler[-20:]
                self._semantik_kaydet("hobiler", ", ".join(hobiler[-20:]))

        # İlgi alanı öğrenme (soru konularından)
        konular_counter = self._oturum_konulari
        if konular_counter:
            sik_konular = [k for k, v in konular_counter.most_common(5) if v >= 2]
            if sik_konular:
                mevcut = set(self.bellek.tercihler.get("tercih_konular", []))
                mevcut.update(sik_konular)
                self.bellek.tercihler["tercih_konular"] = list(mevcut)[-30:]

    # ============================================================
    # AI BAĞLAM ENRİCHMENT — Öğrenilenleri AI'a aktar
    # ============================================================

    def baglam_zenginlestir(self, mevcut_baglam):
        """
        Öğrenilmiş bilgileri AI bağlamına ekle.
        AI daha iyi yanıt verebilsin.
        """
        ekler = []

        # Kullanıcı bilgileri
        bilgiler = self.bellek.bilgiler.get("kullanici_hakkinda", {})
        if bilgiler:
            bilgi_satirlari = []
            for k, v in bilgiler.items():
                if isinstance(v, list):
                    bilgi_satirlari.append(f"  - {k}: {', '.join(str(x) for x in v)}")
                else:
                    bilgi_satirlari.append(f"  - {k}: {v}")
            if bilgi_satirlari:
                ekler.append("Kullanıcı hakkında öğrendiklerim:\n" + "\n".join(bilgi_satirlari))

        # Tercih bilgisi
        tercih_konular = self.bellek.tercihler.get("tercih_konular", [])
        if tercih_konular:
            ekler.append(f"İlgi alanları: {', '.join(tercih_konular[:10])}")

        # Yanıt stili tercihi
        stil = self.bellek.tercihler.get("yanit_stili", "samimi")
        if stil != "samimi":
            ekler.append(f"Yanıt stili tercihi: {stil}")

        # Son başarısız anlama uyarısı
        if self._duzeltme_modu:
            ekler.append("DİKKAT: Kullanıcı az önce yanlış anlaşıldığını belirtti. Çok dikkatli dinle ve anla.")

        # Başarı oranı
        toplam = self.bellek.istatistikler.get("toplam_etkilesim", 0)
        if toplam > 10:
            basari = self.bellek.istatistikler.get("basarili_anlama", 0)
            oran = (basari / toplam * 100) if toplam > 0 else 0
            if oran < 70:
                ekler.append(f"Anlama başarı oranı düşük ({oran:.0f}%). Daha dikkatli ol.")

        if ekler:
            return mevcut_baglam + "\n\n" + "\n".join(ekler)
        return mevcut_baglam

    # ============================================================
    # YANIT KALİTESİ DEĞERLENDİRME
    # ============================================================

    def yanit_kalitesi_puanla(self, soru, yanit):
        """
        Bir yanıtın kalitesini önceki öğrenmelere göre puanla.
        Returns: float 0.0-1.0
        """
        puan = 0.7  # Başlangıç puanı

        soru_lower = soru.lower().strip()

        # Önceden başarısız olmuş kalıp mı?
        kalip = self.bellek.kaliplar.get(soru_lower)
        if kalip:
            if kalip.get("basarisizlik", 0) > kalip.get("basari", 0):
                puan -= 0.2
                # Önceki yanlış yanıtla aynıysa → çok düşük puan
                if kalip.get("yanlis_yanit") and SequenceMatcher(
                    None, yanit[:50], kalip["yanlis_yanit"][:50]
                ).ratio() > 0.8:
                    puan -= 0.3
            elif kalip.get("basari", 0) > 2:
                puan += 0.2

        # Beğenilmeyen yanıt tipine benziyor mu?
        sevmedigi = self.bellek.tercihler.get("sevmedigi_yanitlar", [])
        for kayit in sevmedigi[-10:]:
            if SequenceMatcher(None, yanit[:50], kayit.get("yanit", "")[:50]).ratio() > 0.7:
                puan -= 0.15
                break

        return max(0.0, min(1.0, puan))

    # ============================================================
    # ÖĞRENME RAPORU
    # ============================================================

    def rapor(self):
        """Öğrenme durumu raporu"""
        ist = self.bellek.istatistikler
        toplam = ist.get("toplam_etkilesim", 0)
        basarili = ist.get("basarili_anlama", 0)
        basarisiz = ist.get("basarisiz_anlama", 0)
        duzeltme = ist.get("duzeltme_sayisi", 0)

        oran = (basarili / (basarili + basarisiz) * 100) if (basarili + basarisiz) > 0 else 0

        return {
            "toplam_etkilesim": toplam,
            "basarili_anlama": basarili,
            "basarisiz_anlama": basarisiz,
            "anlama_orani": f"{oran:.1f}%",
            "duzeltme_sayisi": duzeltme,
            "ogrenilen_stt": len(self.bellek.stt_duzeltmeleri),
            "ogrenilen_kalip": len(self.bellek.kaliplar),
            "bilinen_tercihler": len(self.bellek.tercihler.get("tercih_konular", [])),
            "bilinen_bilgiler": len(self.bellek.bilgiler.get("kullanici_hakkinda", {})),
        }

    def oturum_kapat(self):
        """Oturum kapanırken çağrılır — tüm öğrenmeleri kaydet"""
        self.bellek.kaydet_hepsi()
        rapor = self.rapor()
        logger.info(f"Öğrenme oturumu kapandı: {rapor}")
        return rapor

    def durum_ozeti(self):
        """GUI'de göstermek için kısa özet"""
        ist = self.bellek.istatistikler
        stt_sayi = len(self.bellek.stt_duzeltmeleri)
        kalip_sayi = len(self.bellek.kaliplar)
        return f"📚 {stt_sayi} düzeltme, {kalip_sayi} kalıp öğrenildi"
