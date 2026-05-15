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
    (r"(hava\s*(nasıl|durumu)|hava\s*kaç\s*derece)", [
        "Hava durumu bilgisi için internet bağlantısı gerekiyor. Şu an yerel bilgim yok, ama araştırabilirim {ad}.",
    ], "hava"),

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

        # ── Ses komutları ──
        for anahtar, komut in SES_KOMUTLARI.items():
            if anahtar in metin or turkce_normalize(anahtar) in metin_norm:
                try:
                    subprocess.Popen(komut, shell=True)
                    return f"Tamam {ad}, {anahtar}ıyorum.", "ses_kontrol", 0.95
                except Exception:
                    pass

        # ── Program açma ──
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

        # ── Bilgisayarı kapat / yeniden başlat ──
        if "bilgisayar" in metin or "bilgisayari" in metin_norm:
            if any(f in metin for f in KAPAT_FIILLERI):
                return f"Bilgisayarı kapatma komutunu güvenlik nedeniyle sesli olarak çalıştırmıyorum {ad}. Bunu manuel yapmanı öneririm.", "guvenlik", 0.95
            if "yeniden" in metin and ("başlat" in metin or "baslat" in metin):
                return f"Bilgisayarı yeniden başlatma komutunu güvenlik nedeniyle çalıştırmıyorum {ad}.", "guvenlik", 0.95

        return None, None, 0.0

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
