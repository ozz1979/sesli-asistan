"""
Hafiza Modulu v7.5
- Kullanici tanima (isim kayit)
- Tercihler, rutinler ve ogrenme
- Yapilandirilmis hafiza ozeti (AI context icin optimize)
- Son 100 komut gecmisi
"""
import json
import os
import time


class Hafiza:
    def __init__(self, dosya_yolu="hafiza.json"):
        self.dosya = os.path.join(os.path.dirname(os.path.abspath(__file__)), dosya_yolu)
        self.veri = self._yukle()

    def _yukle(self):
        if os.path.exists(self.dosya):
            try:
                with open(self.dosya, "r", encoding="utf-8") as f:
                    veri = json.load(f)
                    # v7.5 alanlari yoksa ekle
                    if "kullanici" not in veri:
                        veri["kullanici"] = {"adi": "", "ilk_kullanim": ""}
                    return veri
            except:
                pass
        return {
            "kullanici": {"adi": "", "ilk_kullanim": ""},
            "tercihler": {},
            "rutinler": {},
            "ogrenme": {},
            "gecmis": [],
            "istatistikler": {"toplam_komut": 0, "basarili_komut": 0}
        }

    def _kaydet(self):
        try:
            with open(self.dosya, "w", encoding="utf-8") as f:
                json.dump(self.veri, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[HATA] Hafiza kaydedilemedi: {e}")

    # =============================================
    # KULLANICI TANIMA
    # =============================================
    def kullanici_adi_al(self):
        """Kayitli kullanici adini dondur"""
        return self.veri.get("kullanici", {}).get("adi", "")

    def kullanici_adi_kaydet(self, isim):
        """Kullanici adini kaydet"""
        if "kullanici" not in self.veri:
            self.veri["kullanici"] = {}
        self.veri["kullanici"]["adi"] = isim
        if not self.veri["kullanici"].get("ilk_kullanim"):
            self.veri["kullanici"]["ilk_kullanim"] = time.strftime("%Y-%m-%d %H:%M")
        self._kaydet()
        print(f"[OK] Kullanici adi kaydedildi: {isim}")

    def ilk_kullanim_mi(self):
        """Ilk kullanim mi kontrol et"""
        return not self.veri.get("kullanici", {}).get("adi", "")

    # =============================================
    # TERCIHLER & OGRENME
    # =============================================
    def tercih_kaydet(self, anahtar, deger):
        self.veri["tercihler"][anahtar] = deger
        self._kaydet()

    def tercih_al(self, anahtar, varsayilan=None):
        return self.veri["tercihler"].get(anahtar, varsayilan)

    def rutin_kaydet(self, isim, komutlar):
        self.veri["rutinler"][isim] = {
            "komutlar": komutlar,
            "tarih": time.strftime("%Y-%m-%d %H:%M")
        }
        self._kaydet()

    def ogren(self, anahtar, deger):
        self.veri["ogrenme"][anahtar] = {
            "deger": deger,
            "tarih": time.strftime("%Y-%m-%d %H:%M")
        }
        self._kaydet()

    def gecmis_ekle(self, komut, sonuc, basarili=True):
        self.veri["gecmis"].append({
            "komut": komut,
            "sonuc": sonuc,
            "basarili": basarili,
            "tarih": time.strftime("%Y-%m-%d %H:%M:%S")
        })
        if len(self.veri["gecmis"]) > 100:
            self.veri["gecmis"] = self.veri["gecmis"][-100:]

        self.veri["istatistikler"]["toplam_komut"] += 1
        if basarili:
            self.veri["istatistikler"]["basarili_komut"] += 1
        self._kaydet()

    def istatistikler(self):
        return self.veri.get("istatistikler", {"toplam_komut": 0, "basarili_komut": 0})

    def hafiza_ozeti(self):
        """AI'ya gonderilecek yapilandirilmis hafiza ozeti"""
        parcalar = []

        # Kullanici bilgisi
        isim = self.kullanici_adi_al()
        if isim:
            parcalar.append(f"KULLANICI: {isim}")

        # Tercihler
        if self.veri["tercihler"]:
            tercih_satirlari = []
            for k, v in self.veri["tercihler"].items():
                tercih_satirlari.append(f"  - {k}: {v}")
            parcalar.append("KULLANICI TERCIHLERI:\n" + "\n".join(tercih_satirlari))

        # Ogrenilen bilgiler
        if self.veri["ogrenme"]:
            ogrenme_satirlari = []
            for k, v in self.veri["ogrenme"].items():
                deger = v.get("deger", v) if isinstance(v, dict) else v
                ogrenme_satirlari.append(f"  - {k}: {deger}")
            parcalar.append("OGRENILEN BILGILER:\n" + "\n".join(ogrenme_satirlari))

        # Rutinler
        if self.veri["rutinler"]:
            rutin_satirlari = []
            for isim_r, bilgi in self.veri["rutinler"].items():
                komutlar = bilgi.get("komutlar", []) if isinstance(bilgi, dict) else []
                rutin_satirlari.append(f"  - {isim_r}: {', '.join(komutlar)}")
            parcalar.append("KAYITLI RUTINLER:\n" + "\n".join(rutin_satirlari))

        # Son komutlar
        son_komutlar = self.veri["gecmis"][-5:]
        if son_komutlar:
            gecmis_satirlari = []
            for k in son_komutlar:
                durum = "basarili" if k.get("basarili", True) else "basarisiz"
                gecmis_satirlari.append(f"  - '{k['komut']}' ({durum})")
            parcalar.append("SON 5 KOMUT:\n" + "\n".join(gecmis_satirlari))

        # Istatistikler
        istat = self.veri.get("istatistikler", {})
        toplam = istat.get("toplam_komut", 0)
        if toplam > 0:
            basarili = istat.get("basarili_komut", 0)
            parcalar.append(f"ISTATISTIK: {toplam} komut, {basarili} basarili")

        return "\n\n".join(parcalar)
