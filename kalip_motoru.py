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

# Ses kontrol komutları
SES_KOMUTLARI = {
    "sesi aç": "nircmd.exe mutesysvolume 0",
    "sesi kapat": "nircmd.exe mutesysvolume 1",
    "sesi kıs": "nircmd.exe changesysvolume -5000",
    "sesi ac": "nircmd.exe mutesysvolume 0",
    "sesi yükselt": "nircmd.exe changesysvolume 5000",
    "sesi arttır": "nircmd.exe changesysvolume 5000",
    "sesi azalt": "nircmd.exe changesysvolume -5000",
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
        for anahtar, komut in SES_KOMUTLARI.items():
            if anahtar in metin or turkce_normalize(anahtar) in metin_norm:
                try:
                    subprocess.Popen(komut, shell=True)
                    return f"Tamam {ad}, {anahtar}ıyorum.", "ses_kontrol", 0.95
                except Exception:
                    pass

        # ── 2. Ekran görüntüsü ──
        if any(k in metin for k in ["ekran görüntüsü", "ekran goruntusu", "screenshot", "ekran al"]):
            basarili, mesaj = bk.ekran_goruntusu()
            if basarili:
                return f"{mesaj} {ad}.", "ekran_goruntusu", 0.95
            else:
                return f"Ekran görüntüsü alınamadı: {mesaj}", "hata", 0.9

        # ── 3. Klasör açma komutları ──
        if "masaüstü" in metin or "masaustu" in metin_norm:
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

        # ── 4. Web arama ──
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

        # ── 8. Bilgisayarı kapat / yeniden başlat ──
        if "bilgisayar" in metin or "bilgisayari" in metin_norm:
            if any(f in metin for f in KAPAT_FIILLERI):
                return f"Bilgisayarı kapatma komutunu güvenlik nedeniyle sesli olarak çalıştırmıyorum {ad}. Bunu manuel yapmanı öneririm.", "guvenlik", 0.95
            if "yeniden" in metin and ("başlat" in metin or "baslat" in metin):
                return f"Bilgisayarı yeniden başlatma komutunu güvenlik nedeniyle çalıştırmıyorum {ad}.", "guvenlik", 0.95

        # ── 9. Kısayollar ──
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
        'X yaz', 'şunu yaz: X', 'yaz X' gibi komutları algıla ve gerçekten yaz.
        """
        yazilacak = None

        # "şunu yaz: merhaba dünya" / "bunu yaz merhaba"
        m = re.search(r"(?:şunu|bunu|su|bu)\s+yaz\s*:?\s*(.+)", metin)
        if m:
            yazilacak = m.group(1).strip()

        # "merhaba dünya yaz" / "test mesajı yaz"
        if not yazilacak:
            m = re.search(r"^(.+?)\s+yaz(?:dır)?$", metin)
            if m:
                kalan = m.group(1).strip()
                # "yaz" ile biten ama program açma/kapatma değilse
                if not any(f in kalan for f in AC_FIILLERI | KAPAT_FIILLERI):
                    if kalan not in PROGRAM_HARITASI and len(kalan) > 1:
                        yazilacak = kalan

        # "yaz: merhaba" / "yaz merhaba dünya"
        if not yazilacak:
            m = re.search(r"^yaz\s*:?\s+(.+)", metin)
            if m:
                yazilacak = m.group(1).strip()

        # "söylediklerimi yaz" / "söylediğimi yaz" → bunlar özel durum, yazılacak metin yok
        if yazilacak and any(k in yazilacak for k in ["söylediklerimi", "söylediğimi", "dediklerimi", "dediğimi"]):
            return f"Ne yazmamı istiyorsun {ad}? Yazmamı istediğin metni söyle.", "metin_soru", 0.95

        if yazilacak and len(yazilacak) > 0:
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
