"""
ATLAS - Kalıp Motoru (Sistem 1 - Hızlı Düşünme)
=================================================
Beyin Karşılığı: Bazal Ganglia
Görev: Bilinen sorulara anında yanıt (<100ms)

Kahneman'ın Sistem 1'i: Otomatik, bilinçdışı, kalıp tabanlı.
"Saat kaç?" → Düşünmeden saate bak
"Merhaba" → Hemen "Merhaba" de
"Chrome'u aç" → Düşünmeden çalıştır
"""

import re
import time
import random
import subprocess
import logging
from datetime import datetime
from turkce import turkce_normalize
import bilgisayar_kontrol as bk

logger = logging.getLogger("ATLAS.kalip")

# ============================================================
# BİLGİSAYAR KOMUTLARI — Windows program haritası
# ============================================================

PROGRAM_HARITASI = {
    # Tarayıcılar
    "chrome": "start chrome",
    "google chrome": "start chrome",
    "google": "start chrome",
    "krom": "start chrome",
    "tarayıcı": "start chrome",
    "tarayici": "start chrome",
    "firefox": "start firefox",
    "edge": "start msedge",
    "opera": "start opera",
    # Ofis
    "not defteri": "notepad",
    "notepad": "notepad",
    "metin belgesi": "notepad",
    "metin dosyası": "notepad",
    "metin dosyasi": "notepad",
    "yazı editörü": "notepad",
    "yazi editoru": "notepad",
    "word": "start winword",
    "excel": "start excel",
    "powerpoint": "start powerpnt",
    # Sistem araçları
    "hesap makinesi": "calc",
    "hesap makinası": "calc",
    "hesap makinesini": "calc",
    "calculator": "calc",
    "paint": "mspaint",
    "dosya gezgini": "explorer",
    "gezgin": "explorer",
    "explorer": "explorer",
    "ayarlar": "start ms-settings:",
    "windows ayarları": "start ms-settings:",
    "görev yöneticisi": "taskmgr",
    "denetim masası": "control",
    "ekran alıntısı": "snippingtool",
    # Terminal
    "komut satırı": "start cmd",
    "cmd": "start cmd",
    "terminal": "start cmd",
    "powershell": "start powershell",
    # Medya
    "spotify": "start spotify",
    "müzik çalar": "start wmplayer",
    "media player": "start wmplayer",
    # İletişim
    "whatsapp": "start whatsapp:",
    "telegram": "start telegram",
    "discord": "start discord",
    "teams": "start msteams",
}

# Açma/kapatma fiilleri
AC_FIILLERI = {"aç", "ac", "başlat", "baslat", "çalıştır", "calistir", "getir", "göster", "goster"}
KAPAT_FIILLERI = {"kapat", "kapa", "sonlandır", "bitir", "durdur"}

# Ses kontrol komutları → islem adı (bilgisayar_kontrol.ses_ayarla kullanılacak)
SES_KOMUTLARI = {
    "sesi aç": "ac",
    "sesi kapat": "kapat",
    "sesi kıs": "azalt",
    "sesi ac": "ac",
    "sesi yükselt": "yukselt",
    "sesi arttır": "yukselt",
    "sesi azalt": "azalt",
    "ses aç": "ac",
    "ses kapat": "kapat",
    "ses kıs": "azalt",
    "ses yükselt": "yukselt",
    "ses azalt": "azalt",
}


# ============================================================
# KALIP VERİTABANI
# ============================================================

# Her kalıp: (regex_pattern, yanıt_listesi, kategori)

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
        "Günaydın! Hayırlı bir gün olsun!",
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
    (r"(nasılsın|nasilsin|nasıl\s*sın)", [
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
        "Bilgisayarını kontrol edebilir, program açıp kapatabilir, sorularına cevap verebilir ve seninle her konuda sohbet edebilirim {ad}! Ne yapmamı istersin?",
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

    # ──── ESPRİ / ŞAKA ────
    (r"(bir? (fıkra|şaka|espri)\s*(anlat|söyle))", [
        "Bilgisayar neden üşümez? Çünkü Windows'u var!",
        "Yapay zeka neden yorulmaz? Çünkü hep şarjda!",
        "Robot doktora gider. Doktor sorar: Neyin var? Robot: Virusum var doktor!",
    ], "espri"),

    # ──── ATLAS'A SESLENME ────
    (r"^atlas\s*$", [
        "Evet {ad}, buradayım! Seni dinliyorum.",
        "Buradayım! Ne yapabilirim senin için?",
        "Evet, buradayım {ad}! Söyle bakalım.",
    ], "tetik"),

    # ──── GÜNCEL BİLGİ SORULARI ────
    # NOT: Hava durumu, haberler gibi bilgi gerektiren sorular Sistem 2 (AI) tarafından cevaplanır.
    # Kalıp motorunda yakalamıyoruz çünkü Gemini daha iyi yanıt verebilir.

    (r"(kendine\s*iyi\s*bak|iyi\s*bak\s*kendine)", [
        "Sen de kendine iyi bak {ad}! Her zaman buradayım.",
    ], "veda"),

    (r"(seni\s*seviyorum|seviyorum\s*seni)", [
        "Çok teşekkür ederim {ad}! Ben de seni çok seviyorum! Senin için her zaman buradayım.",
    ], "duygu"),

    (r"(çok\s*teşekkürler|çok\s*sağol)", [
        "Ne demek {ad}, ben teşekkür ederim! Başka bir şey lazım olursa söyle.",
        "Rica ederim, her zaman yardıma hazırım!",
    ], "tesekkur"),
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


def eylem_varmi(metin, fiiller):
    """Metinde verilen fiillerden biri var mı kontrol et"""
    return any(f in metin for f in fiiller)


# ============================================================
# BURÇ HESAPLAMA — %100 doğru, AI'a güvenme
# ============================================================

BURC_TARIHLERI = [
    ((1, 20), "Oğlak"),    # 1 Ocak - 19 Ocak → Oğlak
    ((2, 18), "Kova"),      # 20 Ocak - 18 Şubat → Kova
    ((3, 20), "Balık"),     # 19 Şubat - 20 Mart → Balık
    ((4, 19), "Koç"),       # 21 Mart - 19 Nisan → Koç
    ((5, 20), "Boğa"),      # 20 Nisan - 20 Mayıs → Boğa
    ((6, 20), "İkizler"),   # 21 Mayıs - 20 Haziran → İkizler
    ((7, 22), "Yengeç"),    # 21 Haziran - 22 Temmuz → Yengeç
    ((8, 22), "Aslan"),     # 23 Temmuz - 22 Ağustos → Aslan
    ((9, 22), "Başak"),     # 23 Ağustos - 22 Eylül → Başak
    ((10, 22), "Terazi"),   # 23 Eylül - 22 Ekim → Terazi
    ((11, 21), "Akrep"),    # 23 Ekim - 21 Kasım → Akrep
    ((12, 21), "Yay"),      # 22 Kasım - 21 Aralık → Yay
    ((12, 31), "Oğlak"),   # 22 Aralık - 31 Aralık → Oğlak
]

AY_ISIMLERI = {
    "ocak": 1, "şubat": 2, "mart": 3, "nisan": 4,
    "mayıs": 5, "mayis": 5, "haziran": 6, "temmuz": 7,
    "ağustos": 8, "agustos": 8, "eylül": 9, "eylul": 9,
    "ekim": 10, "kasım": 11, "kasim": 11, "aralık": 12, "aralik": 12,
}


def burc_hesapla(gun, ay):
    """Gün ve ay'a göre burç hesapla — kesin doğru"""
    for (son_ay, son_gun), burc in BURC_TARIHLERI:
        if ay < son_ay or (ay == son_ay and gun <= son_gun):
            return burc
    return "Oğlak"


def burc_tarih_cikar(metin):
    """
    Metinden tarih çıkar ve burç hesapla.
    "4 temmuz 1979", "4 temmuz", "4/7/1979" gibi formatları destekler.
    Returns: (burc, gun, ay_adi, yil) veya None
    """
    metin_lower = metin.lower().strip()

    # Format 1: "4 temmuz 1979" veya "4 temmuz"
    m = re.search(r"(\d{1,2})\s+(ocak|şubat|subat|mart|nisan|mayıs|mayis|haziran|temmuz|ağustos|agustos|eylül|eylul|ekim|kasım|kasim|aralık|aralik)\s*(\d{4})?", metin_lower)
    if m:
        gun = int(m.group(1))
        ay_adi = m.group(2)
        yil = m.group(3) if m.group(3) else ""
        ay = AY_ISIMLERI.get(ay_adi, 0)
        if ay and 1 <= gun <= 31:
            burc = burc_hesapla(gun, ay)
            return burc, gun, ay_adi.title(), yil

    # Format 2: "4/7/1979" veya "4.7.1979"
    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", metin_lower)
    if m:
        gun, ay, yil = int(m.group(1)), int(m.group(2)), m.group(3)
        if 1 <= gun <= 31 and 1 <= ay <= 12:
            burc = burc_hesapla(gun, ay)
            ay_adi_tr = AYLAR.get(ay, str(ay))
            return burc, gun, ay_adi_tr, yil

    return None


class KalipMotoru:
    """
    Bazal Ganglia — otomatik kalıp eşleştirme motoru.
    Bilinen sorulara düşünmeden anında cevap verir (Sistem 1).
    + Bilgisayar komutlarını algılar ve çalıştırır.
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

        # ──── 0. BURÇ HESAPLAMA (deterministic — AI'a güvenme) ────
        burc_sorumu = bool(re.search(r"(burc|burç|burcu|burcum|burcunu)", text_lower))
        tarih_sonuc = burc_tarih_cikar(text_lower)
        if tarih_sonuc and burc_sorumu:
            burc, gun, ay_adi, yil = tarih_sonuc
            ad = ""
            if self.hafiza:
                ad = self.hafiza.kullanici_bilgisi_getir("ad", "")
            if yil:
                yanit_str = f"{gun} {ay_adi} {yil} tarihine göre burcun {burc} burcu{', ' + ad if ad else ''}."
            else:
                yanit_str = f"{gun} {ay_adi} tarihine göre burcun {burc} burcu{', ' + ad if ad else ''}."
            logger.info(f"Burç hesaplandı: {gun} {ay_adi} → {burc}")
            return yanit_str, "burc_hesaplama", 0.99
        elif tarih_sonuc and not burc_sorumu:
            # Tarih var ama burç sorulmamış — doğum tarihiyse kaydet
            dogum_kontrol = any(k in text_lower for k in ["doğum", "dogum", "doğdum", "dogdum", "dünyaya geldim"])
            if dogum_kontrol and self.hafiza:
                burc, gun, ay_adi, yil = tarih_sonuc
                tarih_kayit = f"{gun} {ay_adi}" + (f" {yil}" if yil else "")
                self.hafiza.kullanici_bilgisi_kaydet("dogum_tarihi", tarih_kayit)
                ad = self.hafiza.kullanici_bilgisi_getir("ad", "")
                yanit_str = f"Tamam, doğum tarihini kaydettim{', ' + ad if ad else ''}. Burcun {burc} burcu."
                return yanit_str, "dogum_tarihi_kaydet", 0.95
        elif burc_sorumu and not tarih_sonuc:
            # "burcum ne" dedi ama tarih vermedi — hafızadan bak
            if self.hafiza:
                dogum = self.hafiza.kullanici_bilgisi_getir("dogum_tarihi", "")
                if dogum:
                    # Hafızadan tarih çek ve hesapla
                    tarih_sonuc2 = burc_tarih_cikar(f"{dogum} burcum")
                    if tarih_sonuc2:
                        burc, gun, ay_adi, yil = tarih_sonuc2
                        ad = self.hafiza.kullanici_bilgisi_getir("ad", "")
                        yanit_str = f"Senin doğum tarihin {dogum}, burcun {burc} burcu{', ' + ad if ad else ''}."
                        return yanit_str, "burc_hesaplama", 0.99

        # ──── 0b. KİŞİSEL BİLGİ SORGULARI (hafızadan cevapla) ────
        if self.hafiza:
            soru_mu = any(k in text_lower for k in ["ne", "nedir", "kaç", "kim", "nere", "söyle", "hatırlıyor musun", "biliyor musun"])
            if soru_mu:
                ad = self.hafiza.kullanici_bilgisi_getir("ad", "")
                # Doğum tarihi sorusu
                if any(k in text_lower for k in ["doğum tarihi", "dogum tarihi", "doğum günü", "dogum gunu",
                                                   "doğum günüm", "doğum tarihim", "dogum tarihim",
                                                   "ne zaman doğdum", "ne zaman dogdum"]):
                    dogum = self.hafiza.kullanici_bilgisi_getir("dogum_tarihi", "")
                    if dogum:
                        tarih_sonuc2 = burc_tarih_cikar(f"{dogum} burcum")
                        if tarih_sonuc2:
                            burc, gun, ay_adi, yil = tarih_sonuc2
                            return f"Senin doğum tarihin {dogum}, burcun {burc} burcu{', ' + ad if ad else ''}.", "hafiza_sorgulama", 0.99
                        return f"Senin doğum tarihin {dogum}{', ' + ad if ad else ''}.", "hafiza_sorgulama", 0.99
                    else:
                        return f"Doğum tarihini henüz bilmiyorum{', ' + ad if ad else ''}. Söylersen kaydedeyim!", "hafiza_sorgulama", 0.9

                # Yaş sorusu
                if any(k in text_lower for k in ["kaç yaşında", "kac yasinda", "yaşım", "yasim", "yaşım kaç", "yasim kac"]):
                    yas = self.hafiza.kullanici_bilgisi_getir("yas", "")
                    if yas:
                        return f"Sen {yas} yaşındasın{', ' + ad if ad else ''}.", "hafiza_sorgulama", 0.99
                    dogum = self.hafiza.kullanici_bilgisi_getir("dogum_tarihi", "")
                    if dogum:
                        return f"Doğum tarihin {dogum}{', ' + ad if ad else ''}.", "hafiza_sorgulama", 0.9
                    return f"Yaşını henüz bilmiyorum{', ' + ad if ad else ''}. Söylersen kaydedeyim!", "hafiza_sorgulama", 0.9

                # İsim sorusu
                if any(k in text_lower for k in ["adım ne", "adim ne", "ismim ne", "ismim nedir", "benim adım"]):
                    if ad:
                        return f"Senin adın {ad}.", "hafiza_sorgulama", 0.99
                    return "Adını henüz bilmiyorum. Söylersen kaydedeyim!", "hafiza_sorgulama", 0.9

                # Şehir sorusu
                if any(k in text_lower for k in ["nerede yaşıyorum", "nerede yasiyorum", "şehrim", "sehrim", "hangi şehir"]):
                    sehir = self.hafiza.kullanici_bilgisi_getir("sehir", "")
                    if sehir:
                        return f"Sen {sehir}'da yaşıyorsun{', ' + ad if ad else ''}.", "hafiza_sorgulama", 0.99
                    return f"Hangi şehirde yaşadığını bilmiyorum{', ' + ad if ad else ''}. Söylersen kaydedeyim!", "hafiza_sorgulama", 0.9

                # Meslek sorusu
                if any(k in text_lower for k in ["mesleğim", "meslegim", "ne iş yapıyorum", "ne is yapiyorum", "işim ne", "isim ne"]):
                    meslek = self.hafiza.kullanici_bilgisi_getir("meslek", "")
                    if meslek:
                        return f"Senin mesleğin {meslek}{', ' + ad if ad else ''}.", "hafiza_sorgulama", 0.99
                    return f"Mesleğini henüz bilmiyorum{', ' + ad if ad else ''}. Söylersen kaydedeyim!", "hafiza_sorgulama", 0.9

        # ──── 1. BİLGİSAYAR KOMUTLARI (en yüksek öncelik) ────
        yanit, kat, guven = self._bilgisayar_komutu_kontrol(text_lower, text_norm)
        if yanit:
            self._sayac[kat] = self._sayac.get(kat, 0) + 1
            logger.info(f"Bilgisayar komutu: [{kat}] {yanit}")
            return yanit, kat, guven

        # ──── 2. KALIP EŞLEŞTİRME ────
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

        # ──── 3. PROSEDÜREL BELLEK ────
        if self.hafiza:
            kalip = self.hafiza.prosedurel.kalip_bul(text_lower)
            if kalip and kalip.get("guc", 0) >= 1.0:
                return kalip["yanit"], "prosedurel", 0.7

        return None, None, 0.0

    # ============================================================
    # BİLGİSAYAR KOMUTU İŞLEME
    # ============================================================

    def _bilgisayar_komutu_kontrol(self, metin, metin_norm):
        """Bilgisayar komutlarını algıla ve çalıştır."""
        ad = ""
        if self.hafiza:
            ad = self.hafiza.kullanici_bilgisi_getir("ad", "")

        # ── 0. METİN YAZMA KOMUTLARI (en yüksek öncelik) ──
        yanit = self._metin_yazma_kontrol(metin, metin_norm, ad)
        if yanit:
            return yanit

        # ── 1. Ses komutları ──
        for anahtar, islem in SES_KOMUTLARI.items():
            if anahtar in metin or turkce_normalize(anahtar) in metin_norm:
                basarili, mesaj = bk.ses_ayarla(islem)
                if basarili:
                    return f"Tamam {ad}, {anahtar}ıyorum.", "ses_kontrol", 0.95
                else:
                    return f"Ses ayarlanamadı: {mesaj}", "hata", 0.9

        # ── 2. Ekran görüntüsü ──
        ekran_tetik = any(k in metin for k in ["ekran görüntüsü", "ekran goruntusu", "screenshot", "ekran al",
                                                 "ekran görüntüsü al", "ekran yakala", "ekranı yakala"])
        if ekran_tetik:
            al_istegi = any(k in metin for k in ["al", "çek", "cek", "yakala", "kaydet"])
            goster_istegi = any(k in metin for k in ["göster", "goster", "bak", "aç", "ac"])

            # "al ve göster" → önce al, sonra göster
            if al_istegi and goster_istegi:
                basarili, mesaj = bk.ekran_goruntusu()
                if basarili:
                    import glob as g
                    import os
                    import time as t
                    t.sleep(0.5)
                    masaustu = os.path.expanduser("~\\Desktop")
                    dosyalar = sorted(g.glob(os.path.join(masaustu, "ekran_*.png")), reverse=True)
                    if dosyalar:
                        try:
                            os.startfile(dosyalar[0])
                        except Exception:
                            pass
                    return f"Ekran görüntüsünü aldım ve açıyorum {ad}.", "ekran_goruntusu", 0.95
                else:
                    return f"Ekran görüntüsü alınamadı: {mesaj}", "hata", 0.9

            # Sadece "al" → yeni ekran görüntüsü çek
            elif al_istegi or (not goster_istegi):
                basarili, mesaj = bk.ekran_goruntusu()
                if basarili:
                    return f"{mesaj} {ad}.", "ekran_goruntusu", 0.95
                else:
                    return f"Ekran görüntüsü alınamadı: {mesaj}", "hata", 0.9

            # Sadece "göster" → mevcut olanı aç
            else:
                import glob as g
                import os
                masaustu = os.path.expanduser("~\\Desktop")
                dosyalar = sorted(g.glob(os.path.join(masaustu, "ekran_*.png")), reverse=True)
                if dosyalar:
                    try:
                        os.startfile(dosyalar[0])
                        return f"Son ekran görüntüsünü açıyorum {ad}.", "ekran_goster", 0.95
                    except Exception:
                        pass
                return f"Masaüstünde ekran görüntüsü bulamadım {ad}. Önce 'ekran görüntüsü al' de.", "hata", 0.9

        # ── 2.5. Resim/fotoğraf kapatma ──
        resim_kelimeleri = ["resmi", "resim", "resimi", "fotoğrafı", "fotografı",
                            "fotoğraf", "fotograf", "görüntüyü", "goruntüyü",
                            "görsel", "resimleri", "fotoğrafları"]
        kapat_kelimeleri = ["kapat", "kapa", "kapatsana", "kapatır mısın",
                            "kapatırmısın", "kapat"]
        resim_var = any(k in metin for k in resim_kelimeleri)
        kapat_var = any(k in metin for k in kapat_kelimeleri)
        if resim_var and kapat_var:
            basarili, mesaj = bk.resim_kapat()
            if basarili:
                return f"Resim kapatıldı {ad}.", "resim_kapat", 0.95
            else:
                return f"Resim kapatılamadı: {mesaj}", "hata", 0.9

        # ── 3. Klasör açma komutları ──
        if "masaüstü" in metin or "masaustu" in metin_norm:
            # Yeni klasör oluşturma: "masaüstünde yeni klasör aç/oluştur"
            if "yeni" in metin and ("klasör" in metin or "klasor" in metin_norm):
                import os
                masaustu = os.path.expanduser("~\\Desktop")
                # İsimsiz klasör adı bul (Yeni Klasör, Yeni Klasör 2, ...)
                isim = "Yeni Klasör"
                sayac = 1
                while os.path.exists(os.path.join(masaustu, isim)):
                    sayac += 1
                    isim = f"Yeni Klasör {sayac}"
                yol = os.path.join(masaustu, isim)
                try:
                    os.makedirs(yol)
                    os.startfile(yol)
                    return f"Masaüstünde '{isim}' oluşturdum ve açtım {ad}!", "klasor_olustur", 0.95
                except Exception as e:
                    return f"Klasör oluşturulamadı: {e}", "hata", 0.9
            if eylem_varmi(metin, AC_FIILLERI):
                basarili, mesaj = bk.masaustu_ac()
                return f"Masaüstü açılıyor {ad}!", "klasor_ac", 0.95 if basarili else 0.5

        if "belgelerim" in metin or "dökümanlar" in metin or "dokumanlar" in metin_norm or "documents" in metin:
            if eylem_varmi(metin, AC_FIILLERI):
                basarili, mesaj = bk.belgelerim_ac()
                return f"Belgelerim açılıyor {ad}!", "klasor_ac", 0.95 if basarili else 0.5

        if "indirilenler" in metin or "downloads" in metin:
            if eylem_varmi(metin, AC_FIILLERI):
                basarili, mesaj = bk.indirilenler_ac()
                return f"İndirilenler açılıyor {ad}!", "klasor_ac", 0.95 if basarili else 0.5

        # ── 4. Hava durumu ──
        hava_kalip = re.search(
            r"(?:hava\s*durumu|hava\s*nas[ıi]l|hava\s*ne\s*durumda|hava\s*ne\s*olacak|hava\s*raporu)",
            metin
        )
        if hava_kalip or ("hava" in metin and any(k in metin for k in ["nasıl", "nasil", "kaç derece", "kac derece", "söyle", "soyle", "sıcaklık", "sicaklik"])):
            # Şehir adı bul — varsa kullan, yoksa Denizli
            sehir = "Denizli"
            # Bilinen Türkiye şehirleri
            sehirler = [
                "istanbul", "ankara", "izmir", "denizli", "antalya", "bursa",
                "adana", "konya", "gaziantep", "mersin", "kayseri", "eskişehir",
                "diyarbakır", "samsun", "trabzon", "malatya", "erzurum", "van",
                "muğla", "aydın", "manisa", "balıkesir", "tekirdağ", "hatay",
                "sakarya", "kahramanmaraş", "afyon", "şanlıurfa", "elazığ",
                "mardin", "bolu", "düzce", "edirne", "çanakkale", "bodrum",
                "alanya", "fethiye", "marmaris", "kuşadası", "çeşme", "pamukkale",
            ]
            metin_lower = metin.lower()
            for s in sehirler:
                s_norm = turkce_normalize(s)
                if s in metin_lower or s_norm in turkce_normalize(metin_lower):
                    sehir = s.title()
                    break

            # "göster" varsa → tarayıcıda aç
            if any(k in metin for k in ["göster", "goster", "ara", "bak", "internette"]):
                basarili, mesaj = bk.web_ara(f"{sehir} hava durumu")
                if basarili:
                    return f"{sehir} hava durumunu gösteriyorum {ad}.", "hava_goster", 0.95

            # "söyle" veya varsayılan → sesli cevap
            basarili, veri = bk.hava_durumu(sehir)
            if basarili:
                return (
                    f"{veri['sehir']}'de hava {veri['durum'].lower()}, "
                    f"sıcaklık {veri['sicaklik']} derece, "
                    f"hissedilen {veri['hissedilen']} derece {ad}.",
                    "hava_durumu", 0.95
                )
            else:
                return f"Hava durumunu şu an öğrenemedim {ad}, interneti kontrol eder misin?", "hata", 0.85

        # ── 4b. Döviz kuru ──
        doviz_kaliplari = [
            (r"(?:dolar|usd)\s*(?:kuru?|kaç|kac|ne\s*kadar|fiyat)", "USD", "Dolar"),
            (r"(?:euro?|eur)\s*(?:kuru?|kaç|kac|ne\s*kadar|fiyat)", "EUR", "Euro"),
            (r"(?:sterlin|pound|gbp)\s*(?:kuru?|kaç|kac|ne\s*kadar|fiyat)", "GBP", "Sterlin"),
            (r"(?:kaç|kac|ne\s*kadar)\s*(?:tl|lira).*(?:dolar|usd)", "USD", "Dolar"),
            (r"(?:kaç|kac|ne\s*kadar)\s*(?:tl|lira).*(?:euro?|eur)", "EUR", "Euro"),
            (r"(?:kaç|kac|ne\s*kadar)\s*(?:tl|lira).*(?:sterlin|gbp)", "GBP", "Sterlin"),
            (r"(?:dolar|usd)\s*(?:kaç|kac)\s*(?:tl|lira)", "USD", "Dolar"),
            (r"(?:euro?|eur)\s*(?:kaç|kac)\s*(?:tl|lira)", "EUR", "Euro"),
            (r"1\s*(?:dolar|usd)", "USD", "Dolar"),
            (r"1\s*(?:euro?|eur)", "EUR", "Euro"),
            (r"(?:döviz|doviz)\s*(?:kuru?|fiyat)", "USD", "Dolar"),
        ]

        metin_lower_doviz = turkce_normalize(metin.lower())
        for kalip, birim, birim_adi in doviz_kaliplari:
            if re.search(kalip, metin_lower_doviz):
                basarili, veri = bk.doviz_kuru(birim)
                if basarili:
                    return (
                        f"Güncel {birim_adi} kuru: 1 {birim} = {veri['kur']} TL {ad}.",
                        "doviz_kuru", 0.95
                    )
                else:
                    return f"Döviz kurunu şu an öğrenemedim {ad}, interneti kontrol eder misin?", "hata", 0.85
                break

        # ── 4c. Müzik / Medya kontrol ──
        # "müzik aç", "şarkı çal", "YouTube'da X çal" vb.
        muzik_tetik = False
        # "X müzik aç/çal" veya "müzik aç/çal X"
        if re.search(r"(?:müzik|muzik|şarkı|sarki)\s*(?:aç|ac|çal|cal|başlat|baslat|oynat)", metin):
            muzik_tetik = True
        elif re.search(r"(?:aç|ac|çal|cal|oynat)\s*(?:müzik|muzik|şarkı|sarki)", metin):
            muzik_tetik = True
        elif re.search(r"(?:youtube|yutup|yutube).{0,8}(?:aç|ac|çal|cal|oynat)\s+.+", metin):
            muzik_tetik = True
        elif re.search(r".+\s+(?:youtube|yutup|yutube).{0,5}(?:aç|ac|çal|cal|oynat)", metin):
            muzik_tetik = True

        if muzik_tetik:
            # Arama sorgusunu çıkar (komut kelimelerini temizle)
            sorgu = metin
            temizle = ["müzik", "muzik", "şarkı", "sarki", "aç", "açar mısın",
                        "açarmısın", "açabilir misin", "ac", "çal", "cal",
                        "başlat", "baslat", "oynat", "youtube", "yutup", "yutube",
                        "bana", "benim için", "biraz", "güzel", "lütfen"]
            for sil in temizle:
                sorgu = re.sub(r'\b' + re.escape(sil) + r'\b', '', sorgu, flags=re.IGNORECASE)
            sorgu = re.sub(r'\s+', ' ', sorgu).strip()
            if not sorgu:
                sorgu = "popüler türkçe müzik"
            basarili, mesaj = bk.muzik_cal(sorgu)
            if basarili:
                return f"YouTube'da {sorgu} çalınıyor {ad}!", "muzik_cal", 0.95
            else:
                return f"Müzik açılamadı: {mesaj}", "hata", 0.9

        # Medya kontrol: "çal", "oynat", "duraklat", "durdur" (tek kelime)
        metin_strip = metin.strip()
        if metin_strip in ("çal", "cal", "oynat", "devam", "devam et"):
            bk.medya_oynat_duraklat()
            return f"Oynatıyorum {ad}!", "medya_kontrol", 0.95
        if metin_strip in ("duraklat", "durdur", "bekle", "dur", "pause"):
            bk.medya_oynat_duraklat()
            return f"Duraklatıyorum {ad}.", "medya_kontrol", 0.95
        if metin_strip in ("sonraki", "sonraki şarkı", "sonraki sarki", "sıradaki", "atla"):
            bk.medya_sonraki()
            return f"Sonraki parçaya geçiyorum {ad}.", "medya_kontrol", 0.95
        if metin_strip in ("önceki", "önceki şarkı", "onceki sarki", "geri"):
            bk.medya_onceki()
            return f"Önceki parçaya dönüyorum {ad}.", "medya_kontrol", 0.95

        # ── 5. Web arama ──
        m = re.search(r"(?:internette?|google.?da|web.?de|araştır)\s+(.+?)(?:\s+ara)?$", metin)
        if not m:
            m = re.search(r"(.+?)\s+(?:ara|arat|araştır)$", metin)
        if m:
            sorgu = m.group(1).strip()
            if len(sorgu) > 2:
                basarili, mesaj = bk.web_ara(sorgu)
                if basarili:
                    return f"'{sorgu}' için arama yapıyorum {ad}.", "web_arama", 0.95
                else:
                    return f"Arama yapamadım: {mesaj}", "hata", 0.9

        # ── 5. URL açma ──
        m = re.search(r"([\w.-]+\.(?:com|net|org|io|tr|edu)(?:\.\w+)?)\s*(?:aç|ac|git)?", metin)
        if m:
            url = m.group(1)
            basarili, mesaj = bk.web_ac(url)
            if basarili:
                return f"{url} açılıyor {ad}!", "web_ac", 0.95

        # ── 6. Pencere yönetimi ──
        if "pencere" in metin or "ekran" in metin:
            if "küçült" in metin or "kucult" in metin_norm or "minimize" in metin:
                bk.pencere_kucult()
                return f"Pencere küçültülüyor {ad}.", "pencere", 0.95
            if "büyüt" in metin or "buyut" in metin_norm or "maximize" in metin:
                bk.pencere_buyut()
                return f"Pencere büyütülüyor {ad}.", "pencere", 0.95

        if "masaüstünü göster" in metin or "masaustunu goster" in metin_norm:
            bk.tum_pencereleri_kucult()
            return f"Masaüstü gösteriliyor {ad}.", "pencere", 0.95

        # ── 7. Program açma/kapatma ──
        eylem_ac = any(f in metin for f in AC_FIILLERI)
        eylem_kapat = any(f in metin for f in KAPAT_FIILLERI)

        if eylem_ac or eylem_kapat:
            # Program adı bul (en uzun eşleşme önce)
            for program_adi in sorted(PROGRAM_HARITASI.keys(), key=len, reverse=True):
                prog_norm = turkce_normalize(program_adi)
                if program_adi in metin or prog_norm in metin_norm:
                    if eylem_ac:
                        return self._program_ac(program_adi, ad)
                    elif eylem_kapat:
                        return self._program_kapat(program_adi, ad)

        # ── 8. Tüm programları kapat ──
        tum_kapat_kaliplari = [
            "açık programları kapat", "acik programlari kapat",
            "açık programları kapa", "acik programlari kapa",
            "tüm programları kapat", "tum programlari kapat",
            "programları kapat", "programlari kapat",
            "hepsini kapat", "hep kapat",
            "her şeyi kapat", "herseyi kapat", "herşeyi kapat",
        ]
        if any(k in metin or turkce_normalize(k) in metin_norm for k in tum_kapat_kaliplari):
            basarili, sonuc = bk.tum_programlari_kapat()
            if basarili:
                return f"Açık programlar kapatılıyor {ad}. {sonuc}.", "tum_kapat", 0.95
            else:
                return f"Programları kapatırken sorun oluştu {ad}.", "hata", 0.9

        # ── 9. Tek kelime "kapat" → aktif pencereyi kapat ──
        if metin.strip() in ("kapat", "kapa", "pencereyi kapat", "bunu kapat"):
            bk.pencere_kapat()
            return f"Pencere kapatıldı {ad}.", "pencere_kapat", 0.95

        # ── 10. Bilgisayarı kapat / yeniden başlat / uyut / iptal ──
        if "bilgisayar" in metin or "bilgisayari" in metin_norm or "bilgisayarı" in metin:
            # Kapatma iptal
            if "iptal" in metin:
                bk.kapatma_iptal()
                return f"Kapatma işlemi iptal edildi {ad}.", "kapatma_iptal", 0.95

            # Yeniden başlat
            if "yeniden" in metin and ("başlat" in metin or "baslat" in metin_norm):
                basarili, sonuc = bk.bilgisayari_yeniden_baslat(30)
                if basarili:
                    return f"Bilgisayar 30 saniye sonra yeniden başlayacak {ad}. İptal etmek istersen 'iptal et' de.", "yeniden_baslat", 0.95
                return f"Yeniden başlatma başarısız oldu {ad}.", "hata", 0.9

            # Uyku modu
            if "uyut" in metin or "uyku" in metin:
                basarili, sonuc = bk.uyku_modu()
                if basarili:
                    return f"Bilgisayar uyku moduna geçiyor {ad}.", "uyku", 0.95
                return f"Uyku modu hatası {ad}.", "hata", 0.9

            # Kapat
            if any(f in metin for f in KAPAT_FIILLERI):
                basarili, sonuc = bk.bilgisayari_kapat(30)
                if basarili:
                    return f"Bilgisayar 30 saniye sonra kapanacak {ad}. İptal etmek istersen 'iptal et' de.", "bilgisayar_kapat", 0.95
                return f"Kapatma başarısız oldu {ad}.", "hata", 0.9

        # ── 10b. Kapatma iptal (bilgisayar kelimesi olmadan) ──
        if "iptal" in metin and ("kapat" in metin or "kapatma" in metin):
            bk.kapatma_iptal()
            return f"Kapatma işlemi iptal edildi {ad}.", "kapatma_iptal", 0.95

        # ── 11. Kısayollar ──
        if "kaydet" in metin and ("dosya" in metin or "belge" in metin):
            bk.kisayol_bas("ctrl", "s")
            return f"Kaydedildi {ad}!", "kisayol", 0.95

        if "geri al" in metin:
            bk.kisayol_bas("ctrl", "z")
            return f"Geri alındı {ad}.", "kisayol", 0.95

        if "kopyala" in metin and "yapıştır" not in metin:
            bk.kisayol_bas("ctrl", "c")
            return f"Kopyalandı {ad}.", "kisayol", 0.95

        if "yapıştır" in metin:
            bk.kisayol_bas("ctrl", "v")
            return f"Yapıştırıldı {ad}.", "kisayol", 0.95

        return None, None, 0.0

    def _metin_yazma_kontrol(self, metin, metin_norm, ad):
        """
        Metin yazma komutlarını algıla ve gerçekten yaz.
        
        Desteklenen kalıplar:
        - "merhaba dünya yaz"
        - "şunu yaz: merhaba dünya"
        - "yaz merhaba dünya"
        - "devamını yaz benim adım Özgür"
        - "yazının devamını yaz test metni"
        - "not defterine yaz merhaba"
        """
        yazilacak = None

        # "söylediklerimi yaz" / "devamını yaz" (metin belirtilmemiş) → özel durum
        if any(k in metin for k in ["söylediklerimi yaz", "söylediğimi yaz", "dediklerimi yaz", "dediğimi yaz"]):
            return f"Ne yazmamı istiyorsun {ad}? Yazmamı istediğin metni söyle.", "metin_soru", 0.95

        # "devamını yaz" / "yazının devamını yaz" — tek başına, yazılacak metin yok
        if re.match(r"^(yazının\s+)?devam[ıi]n[ıi]\s+yaz$", metin.strip()):
            return f"Ne yazmamı istiyorsun {ad}? Metni söyle, yazayım.", "metin_soru", 0.95

        # 1. "şunu yaz: merhaba dünya" / "bunu yaz merhaba"
        m = re.search(r"(?:şunu|bunu|su|bu)\s+yaz\s*:?\s*(.+)", metin)
        if m:
            yazilacak = m.group(1).strip()

        # 2. "devamını yaz X" / "yazının devamını yaz X" / "not defterine yaz X"
        if not yazilacak:
            m = re.search(r"(?:devam[ıi]n[ıi]|not\s*defter[ie]ne?)\s+yaz\s+(.+)", metin)
            if m:
                yazilacak = m.group(1).strip()

        # 3. "... yaz ..." — "yaz" ortada, sonrası yazılacak metin (en az 3 karakter)
        if not yazilacak:
            m = re.search(r"\byaz\b\s+(.{3,})", metin)
            if m:
                kalan = m.group(1).strip()
                # "yaz" dan sonraki kısım program adı veya eylem değilse
                if kalan not in PROGRAM_HARITASI:
                    # "yazı" kelimesiyle karışmasın — "yazısı", "yazıyı" gibi
                    # "yaz" dan önceki karakter boşluk veya satır başı olmalı
                    yazilacak = kalan

        # 4. "merhaba dünya yaz" — sondaki "yaz" ile biter
        if not yazilacak:
            m = re.search(r"^(.+?)\s+yaz(?:dır)?$", metin)
            if m:
                kalan = m.group(1).strip()
                # Fiil veya program adı değilse
                if not any(f in kalan for f in AC_FIILLERI | KAPAT_FIILLERI):
                    if kalan not in PROGRAM_HARITASI and len(kalan) > 1:
                        # "yazının devamını" gibi sadece talimat olan kısımları atla
                        if not re.match(r"^(yazının\s+devamını|devamını)$", kalan):
                            yazilacak = kalan

        # 5. "yaz: merhaba" / "yaz merhaba dünya" — başta "yaz"
        if not yazilacak:
            m = re.search(r"^yaz\s*:?\s+(.+)", metin)
            if m:
                yazilacak = m.group(1).strip()

        # Yazılacak metin bulundu → yaz
        if yazilacak and len(yazilacak) > 0:
            # "yazısı" gibi kalıntıları temizle
            yazilacak = re.sub(r'\s+yazısı$', '', yazilacak).strip()
            if len(yazilacak) > 0:
                basarili, mesaj = bk.metin_yaz(yazilacak)
                if basarili:
                    logger.info(f"Metin yazıldı: {yazilacak[:50]}")
                    return f"Yazdım {ad}.", "metin_yaz", 0.95
                else:
                    logger.error(f"Metin yazma hatası: {mesaj}")
                    return f"Yazamadım: {mesaj}", "metin_hata", 0.9

        return None

    def _program_ac(self, program_adi, ad):
        """Program aç."""
        komut = PROGRAM_HARITASI[program_adi]
        try:
            subprocess.Popen(komut, shell=True)
            # Güzel isim
            guzel_isim = program_adi.replace("google chrome", "Chrome").replace("google", "Chrome")
            guzel_isim = guzel_isim.title()
            logger.info(f"Program açıldı: {program_adi} → {komut}")
            return f"{guzel_isim} açılıyor {ad}!", "program_ac", 0.95
        except Exception as e:
            logger.error(f"Program açma hatası: {program_adi} → {e}")
            return f"{program_adi.title()} açılırken hata oluştu.", "program_hata", 0.9

    def _program_kapat(self, program_adi, ad):
        """Program kapat."""
        komut = PROGRAM_HARITASI[program_adi]
        # Komuttan exe adını çıkar
        exe = komut.replace("start ", "").strip()
        # Bazı özel durumlar
        exe_haritasi = {
            "chrome": "chrome", "msedge": "msedge", "firefox": "firefox",
            "notepad": "notepad", "calc": "Calculator",
            "mspaint": "mspaint", "explorer": "explorer",
            "calc": "CalculatorApp",
        }
        exe_adi = exe_haritasi.get(exe, exe)
        try:
            subprocess.Popen(f"taskkill /im {exe_adi}.exe /f", shell=True,
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"Program kapatıldı: {program_adi}")
            return f"{program_adi.title()} kapatılıyor {ad}.", "program_kapat", 0.95
        except Exception as e:
            logger.error(f"Program kapatma hatası: {program_adi} → {e}")
            return f"{program_adi.title()} kapatılırken hata oluştu.", "program_hata", 0.9

    # ============================================================
    # DEĞİŞKEN DOLDURMA
    # ============================================================

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
