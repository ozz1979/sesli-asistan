"""
ATLAS - Hafıza Sistemi
======================
Beyin Karşılığı: Hipokampüs + Neokorteks + Bazal Ganglia
Görev: Çoklu hafıza yönetimi — kayıt, geri çağırma, konsolidasyon

İnsan beyni 5 farklı hafıza sistemi kullanır:
1. Çalışma Belleği (Working Memory) — anlık, 7±2 öğe
2. Oturum Belleği (Short-term) — bu konuşma
3. Epizodik Bellek — geçmiş deneyimler
4. Semantik Bellek — genel bilgi ve tercihler
5. Prosedürel Bellek — öğrenilmiş kalıplar
"""

import json
import os
import time
import threading
from datetime import datetime, timedelta
from collections import deque


class CalismaBellegi:
    """
    Prefrontal korteksteki çalışma belleği.
    Anlık konuşma bağlamını tutar. Son N mesajı hafızada tutar.
    """

    def __init__(self, kapasite=7):
        self.kapasite = kapasite
        self._tampon = deque(maxlen=kapasite)
        self._lock = threading.Lock()

    def ekle(self, rol, mesaj, meta=None):
        """Yeni bir mesajı çalışma belleğine ekle"""
        with self._lock:
            self._tampon.append({
                "rol": rol,  # "kullanici" veya "asistan"
                "mesaj": mesaj,
                "zaman": datetime.now().isoformat(),
                "meta": meta or {}
            })

    def getir(self):
        """Tüm çalışma belleğini döndür"""
        with self._lock:
            return list(self._tampon)

    def son_mesaj(self, rol=None):
        """Son mesajı döndür"""
        with self._lock:
            if not self._tampon:
                return None
            if rol:
                for m in reversed(self._tampon):
                    if m["rol"] == rol:
                        return m
                return None
            return self._tampon[-1]

    def temizle(self):
        """Çalışma belleğini temizle"""
        with self._lock:
            self._tampon.clear()

    def boyut(self):
        return len(self._tampon)

    def baglamstring(self):
        """AI'a gönderilecek bağlam metni oluştur"""
        with self._lock:
            if not self._tampon:
                return ""
            satirlar = []
            for m in self._tampon:
                rol = "Kullanıcı" if m["rol"] == "kullanici" else "ATLAS"
                satirlar.append(f"{rol}: {m['mesaj']}")
            return "\n".join(satirlar)


class OturumBellegi:
    """
    Hipokampüsteki kısa süreli bellek.
    Bu oturumdaki tüm konuşmayı kayıt altına alır.
    Oturum kapandığında epizodik belleğe aktarılır.
    """

    def __init__(self):
        self._kayitlar = []
        self._baslangic = datetime.now()
        self._konu = "genel"
        self._lock = threading.Lock()

    def ekle(self, rol, mesaj, niyet=None, duygu=None):
        with self._lock:
            self._kayitlar.append({
                "rol": rol,
                "mesaj": mesaj,
                "niyet": niyet,
                "duygu": duygu,
                "zaman": datetime.now().isoformat()
            })

    def konu_guncelle(self, yeni_konu):
        self._konu = yeni_konu

    def getir(self):
        with self._lock:
            return list(self._kayitlar)

    def ozet(self):
        """Oturum özetini oluştur (epizodik belleğe aktarım için)"""
        with self._lock:
            if not self._kayitlar:
                return None
            mesaj_sayisi = len(self._kayitlar)
            sure = (datetime.now() - self._baslangic).total_seconds() / 60
            konular = set()
            for k in self._kayitlar:
                if k.get("niyet"):
                    konular.add(k["niyet"])
            return {
                "tarih": self._baslangic.isoformat(),
                "sure_dk": round(sure, 1),
                "mesaj_sayisi": mesaj_sayisi,
                "konular": list(konular),
                "konu": self._konu,
                "ilk_mesaj": self._kayitlar[0]["mesaj"] if self._kayitlar else "",
                "son_mesaj": self._kayitlar[-1]["mesaj"] if self._kayitlar else ""
            }

    def temizle(self):
        with self._lock:
            self._kayitlar.clear()
            self._baslangic = datetime.now()


class EpizodikBellek:
    """
    Hipokampüs → Neokorteks uzun süreli epizodik bellek.
    Geçmiş oturumları ve önemli olayları saklar.
    'Dün bana şunu sormuştun' gibi hatırlama sağlar.
    """

    def __init__(self, dosya="hafiza/epizodik.json"):
        self._dosya = dosya
        self._kayitlar = []
        self._lock = threading.Lock()
        self._yukle()

    def _yukle(self):
        try:
            if os.path.exists(self._dosya):
                with open(self._dosya, 'r', encoding='utf-8') as f:
                    self._kayitlar = json.load(f)
        except Exception:
            self._kayitlar = []

    def _kaydet(self):
        try:
            os.makedirs(os.path.dirname(self._dosya), exist_ok=True)
            with open(self._dosya, 'w', encoding='utf-8') as f:
                json.dump(self._kayitlar, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def oturum_kaydet(self, oturum_ozeti):
        """Bir oturum özetini epizodik belleğe kaydet"""
        if not oturum_ozeti:
            return
        with self._lock:
            self._kayitlar.append(oturum_ozeti)
            # Son 100 oturumu tut
            if len(self._kayitlar) > 100:
                self._kayitlar = self._kayitlar[-100:]
            self._kaydet()

    def olay_kaydet(self, olay_turu, detay):
        """Önemli bir olayı kaydet (düzeltme, tercih değişikliği vb)"""
        with self._lock:
            self._kayitlar.append({
                "tarih": datetime.now().isoformat(),
                "tur": "olay",
                "olay_turu": olay_turu,
                "detay": detay
            })
            self._kaydet()

    def ara(self, anahtar_kelime, son_n=10):
        """Epizodik bellekte anahtar kelime ile ara"""
        with self._lock:
            sonuclar = []
            for kayit in reversed(self._kayitlar):
                text = json.dumps(kayit, ensure_ascii=False).lower()
                if anahtar_kelime.lower() in text:
                    sonuclar.append(kayit)
                    if len(sonuclar) >= son_n:
                        break
            return sonuclar

    def son_oturumlar(self, n=5):
        """Son N oturum özetini döndür"""
        with self._lock:
            return self._kayitlar[-n:]

    def toplam_oturum(self):
        return len(self._kayitlar)


class SemantikBellek:
    """
    Temporal lob semantik bellek.
    Genel bilgi ve kullanıcı tercihleri.
    'Kullanıcının adı Özgür', 'Sabahları kahve içer' gibi bilgiler.
    """

    def __init__(self, dosya="hafiza/semantik.json"):
        self._dosya = dosya
        self._bilgiler = {}
        self._lock = threading.Lock()
        self._yukle()

    def _yukle(self):
        try:
            if os.path.exists(self._dosya):
                with open(self._dosya, 'r', encoding='utf-8') as f:
                    self._bilgiler = json.load(f)
        except Exception:
            self._bilgiler = {}

    def _kaydet(self):
        try:
            os.makedirs(os.path.dirname(self._dosya), exist_ok=True)
            with open(self._dosya, 'w', encoding='utf-8') as f:
                json.dump(self._bilgiler, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def kaydet(self, kategori, anahtar, deger):
        """Semantik bilgi kaydet"""
        with self._lock:
            if kategori not in self._bilgiler:
                self._bilgiler[kategori] = {}
            self._bilgiler[kategori][anahtar] = {
                "deger": deger,
                "guncelleme": datetime.now().isoformat(),
                "erisim_sayisi": 0
            }
            self._kaydet()

    def getir(self, kategori, anahtar, varsayilan=None):
        """Semantik bilgi getir"""
        with self._lock:
            if kategori in self._bilgiler and anahtar in self._bilgiler[kategori]:
                bilgi = self._bilgiler[kategori][anahtar]
                bilgi["erisim_sayisi"] = bilgi.get("erisim_sayisi", 0) + 1
                self._kaydet()
                return bilgi["deger"]
            return varsayilan

    def kategori_getir(self, kategori):
        """Bir kategorideki tüm bilgileri döndür"""
        with self._lock:
            if kategori in self._bilgiler:
                return {k: v["deger"] for k, v in self._bilgiler[kategori].items()}
            return {}

    def sil(self, kategori, anahtar):
        with self._lock:
            if kategori in self._bilgiler and anahtar in self._bilgiler[kategori]:
                del self._bilgiler[kategori][anahtar]
                self._kaydet()

    def tum_kategoriler(self):
        return list(self._bilgiler.keys())


class ProsedurelBellek:
    """
    Bazal ganglia + serebellum prosedürel bellek.
    Öğrenilmiş kalıplar: sık kullanılan komutlar, düzeltmeler.
    'Özgür sabah saat sorar' → Sabah "saat kaç" gelince hızlı cevap ver.
    """

    def __init__(self, dosya="hafiza/prosedurel.json"):
        self._dosya = dosya
        self._kaliplar = {}
        self._lock = threading.Lock()
        self._yukle()

    def _yukle(self):
        try:
            if os.path.exists(self._dosya):
                with open(self._dosya, 'r', encoding='utf-8') as f:
                    self._kaliplar = json.load(f)
        except Exception:
            self._kaliplar = {}

    def _kaydet(self):
        try:
            os.makedirs(os.path.dirname(self._dosya), exist_ok=True)
            with open(self._dosya, 'w', encoding='utf-8') as f:
                json.dump(self._kaliplar, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def kalip_guncelle(self, tetik, yanit, basarili=True):
        """
        Bir kalıbı güncelle (Hebbian öğrenme).
        Başarılı kullanım → güç artar, başarısız → güç azalır.
        """
        with self._lock:
            if tetik not in self._kaliplar:
                self._kaliplar[tetik] = {
                    "yanit": yanit,
                    "guc": 1.0,
                    "kullanim": 0,
                    "son_kullanim": None
                }

            kalip = self._kaliplar[tetik]
            kalip["kullanim"] += 1
            kalip["son_kullanim"] = datetime.now().isoformat()

            if basarili:
                # Hebbian güçlendirme — sık kullanılan kalıplar güçlenir
                kalip["guc"] = min(kalip["guc"] + 0.1, 5.0)
                kalip["yanit"] = yanit  # En son başarılı yanıtı güncelle
            else:
                # Zayıflama
                kalip["guc"] = max(kalip["guc"] - 0.2, 0.1)

            self._kaydet()

    def kalip_bul(self, tetik):
        """Bir tetik için en güçlü kalıbı bul"""
        with self._lock:
            if tetik in self._kaliplar:
                return self._kaliplar[tetik]
            # Benzer tetik ara
            from turkce import turkce_normalize
            tetik_n = turkce_normalize(tetik)
            for k, v in self._kaliplar.items():
                if turkce_normalize(k) == tetik_n:
                    return v
            return None

    def en_guclu_kaliplar(self, n=10):
        """En güçlü N kalıbı döndür"""
        with self._lock:
            sirali = sorted(
                self._kaliplar.items(),
                key=lambda x: x[1].get("guc", 0),
                reverse=True
            )
            return sirali[:n]

    def duzeltme_kaydet(self, yanlis, dogru):
        """STT düzeltme kalıbı kaydet (hata → doğru eşleştirme)"""
        with self._lock:
            if "_duzeltmeler" not in self._kaliplar:
                self._kaliplar["_duzeltmeler"] = {}
            self._kaliplar["_duzeltmeler"][yanlis] = {
                "dogru": dogru,
                "tarih": datetime.now().isoformat()
            }
            self._kaydet()

    def duzeltme_getir(self, yanlis):
        """Kayıtlı STT düzeltme var mı kontrol et"""
        with self._lock:
            duzeltmeler = self._kaliplar.get("_duzeltmeler", {})
            return duzeltmeler.get(yanlis, {}).get("dogru")


class HafizaSistemi:
    """
    Ana hafıza yöneticisi — Hipokampüs.
    Tüm hafıza alt sistemlerini koordine eder.
    Konsolidasyon (pekiştirme) yapar.
    """

    def __init__(self, config=None):
        config = config or {}
        hafiza_cfg = config.get("hafiza", {})

        # Alt sistemleri oluştur
        self.calisma = CalismaBellegi(
            kapasite=hafiza_cfg.get("calisma_bellegi_boyutu", 7)
        )
        self.oturum = OturumBellegi()
        self.epizodik = EpizodikBellek()
        self.semantik = SemantikBellek()
        self.prosedurel = ProsedurelBellek()

        self._konsolidasyon_esigi = hafiza_cfg.get("konsolidasyon_esigi", 3)
        self._etkileşim_sayaci = 0

    def kullanici_soyledi(self, mesaj, niyet=None, duygu=None):
        """Kullanıcı bir şey söyledi — tüm hafıza katmanlarına kaydet"""
        self.calisma.ekle("kullanici", mesaj, {"niyet": niyet, "duygu": duygu})
        self.oturum.ekle("kullanici", mesaj, niyet, duygu)
        self._etkileşim_sayaci += 1

        # Periyodik konsolidasyon (beyin uykuda yapar, biz her N etkileşimde)
        if self._etkileşim_sayaci % self._konsolidasyon_esigi == 0:
            self._konsolide_et()

    def asistan_soyledi(self, mesaj, niyet=None):
        """Asistan yanıt verdi — kaydet"""
        self.calisma.ekle("asistan", mesaj, {"niyet": niyet})
        self.oturum.ekle("asistan", mesaj, niyet)

    def oturum_kapat(self):
        """Oturumu kapat ve epizodik belleğe aktar"""
        ozet = self.oturum.ozet()
        if ozet and ozet["mesaj_sayisi"] > 0:
            self.epizodik.oturum_kaydet(ozet)
        self.oturum.temizle()
        self.calisma.temizle()

    def kullanici_bilgisi_kaydet(self, anahtar, deger):
        """Kullanıcı hakkında kalıcı bilgi kaydet"""
        self.semantik.kaydet("kullanici", anahtar, deger)

    def kullanici_bilgisi_getir(self, anahtar, varsayilan=None):
        """Kullanıcı hakkında bilgi getir"""
        return self.semantik.getir("kullanici", anahtar, varsayilan)

    def tercih_kaydet(self, anahtar, deger):
        """Kullanıcı tercihi kaydet"""
        self.semantik.kaydet("tercihler", anahtar, deger)

    def tercih_getir(self, anahtar, varsayilan=None):
        """Kullanıcı tercihi getir"""
        return self.semantik.getir("tercihler", anahtar, varsayilan)

    def baglam_olustur(self):
        """
        AI'a gönderilecek tam bağlam oluştur.
        Çalışma belleği + kullanıcı bilgileri + son oturumlar.
        """
        parcalar = []

        # Kullanıcı bilgileri
        kullanici = self.semantik.kategori_getir("kullanici")
        if kullanici:
            parcalar.append("Kullanıcı Bilgileri:")
            for k, v in kullanici.items():
                parcalar.append(f"  - {k}: {v}")

        # Son oturumlardan özet
        son_oturumlar = self.epizodik.son_oturumlar(3)
        if son_oturumlar:
            parcalar.append("\nGeçmiş Konuşmalar:")
            for ot in son_oturumlar:
                if isinstance(ot, dict) and "tarih" in ot:
                    parcalar.append(f"  - {ot.get('tarih', '?')}: {ot.get('konu', '?')}")

        # Çalışma belleği (aktif konuşma)
        calisma = self.calisma.baglamstring()
        if calisma:
            parcalar.append(f"\nAktif Konuşma:\n{calisma}")

        return "\n".join(parcalar)

    def _konsolide_et(self):
        """
        Hafıza konsolidasyonu — beyin uykuda yapar.
        Sık tekrarlanan kalıpları güçlendir, kullanılmayanları zayıflat.
        """
        # Oturumdaki tekrarlanan niyetleri prosedürel belleğe aktar
        kayitlar = self.oturum.getir()
        niyet_sayac = {}
        for k in kayitlar:
            niyet = k.get("niyet")
            if niyet:
                niyet_sayac[niyet] = niyet_sayac.get(niyet, 0) + 1

        for niyet, sayi in niyet_sayac.items():
            if sayi >= 2:  # Aynı niyet 2+ kez → kalıp olarak kaydet
                self.prosedurel.kalip_guncelle(
                    niyet, f"sik_kullanilan_{niyet}", basarili=True
                )

    def durum_ozeti(self):
        """Hafıza sistemi durumunu döndür"""
        return {
            "calisma_bellegi": self.calisma.boyut(),
            "oturum_kayit": len(self.oturum.getir()),
            "epizodik_oturum": self.epizodik.toplam_oturum(),
            "semantik_kategori": len(self.semantik.tum_kategoriler()),
            "toplam_etkilesim": self._etkileşim_sayaci
        }
