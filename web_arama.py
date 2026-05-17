"""
ATLAS - Web Arama Motoru v2
============================
Beyin Karsiligi: Duyusal Korteks + Islem Bellegi Genisletmesi
Gorev: Internetten bilgi toplama, ozet cikarma, AI'a baglam saglama

Arama Hiyerarsisi:
1. Wikipedia TR Arama + Icerik Cikarma (en guvenilir)
2. Wikipedia EN Fallback (Turkce yoksa)
3. DuckDuckGo Instant Answer API (hizli direkt cevaplar)
4. Web sayfa okuma (detayli bilgi icin)

ATLAS artik internetteki guncel bilgilere erisebilir.
"""

import re
import time
import json
import logging
import urllib.request
import urllib.parse
from html.parser import HTMLParser

logger = logging.getLogger("ATLAS.web_arama")


# ═════════════════════════════════════════════════════════
# HTML TEMİZLEME
# ═════════════════════════════════════════════════════════

class HTMLMetinCikarici(HTMLParser):
    """HTML'den saf metin cikarir."""

    def __init__(self):
        super().__init__()
        self._metin = []
        self._atla = False
        self._atlanacak = {"script", "style", "noscript", "iframe", "svg"}

    def handle_starttag(self, tag, attrs):
        if tag in self._atlanacak:
            self._atla = True

    def handle_endtag(self, tag):
        if tag in self._atlanacak:
            self._atla = False

    def handle_data(self, data):
        if not self._atla:
            temiz = data.strip()
            if temiz:
                self._metin.append(temiz)

    def getir(self):
        return " ".join(self._metin)


def _html_temizle(html_text):
    """HTML icerikten saf metin cikar."""
    try:
        cikarici = HTMLMetinCikarici()
        cikarici.feed(html_text)
        return cikarici.getir()
    except Exception:
        metin = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        metin = re.sub(r'<style[^>]*>.*?</style>', '', metin, flags=re.DOTALL | re.IGNORECASE)
        metin = re.sub(r'<[^>]+>', ' ', metin)
        metin = re.sub(r'\s+', ' ', metin)
        return metin.strip()


def _url_getir(url, timeout=8):
    """URL icerigini indir. Basit HTTP GET. Windows SSL uyumlu."""
    try:
        headers = {
            "User-Agent": "ATLAS-Sesli-Asistan/1.0 (Windows; Python) — bilgi arama botu",
            "Accept": "text/html,application/xhtml+xml,application/json",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
        except Exception:
            # Windows SSL sertifika hatasi fallback
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            resp = urllib.request.urlopen(req, timeout=timeout, context=ctx)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")
    except Exception as e:
        logger.debug(f"URL indirme hatasi ({url[:60]}): {e}")
        return None


# ═════════════════════════════════════════════════════════
# WIKIPEDIA ARAMA (EN GÜVENİLİR KAYNAK)
# ═════════════════════════════════════════════════════════

def _wikipedia_ara(sorgu, dil="tr", max_sonuc=3):
    """
    Wikipedia Search API + Extract API.
    En guvenilir arama kaynagi — her zaman calisir, API key gerektirmez.

    Returns: list of {"baslik": str, "url": str, "ozet": str, "kaynak": str}
    """
    sonuclar = []

    try:
        # Adim 1: Arama yap
        arama_params = urllib.parse.urlencode({
            "action": "query",
            "list": "search",
            "srsearch": sorgu,
            "format": "json",
            "utf8": "1",
            "srlimit": str(max_sonuc),
        })
        arama_url = f"https://{dil}.wikipedia.org/w/api.php?{arama_params}"
        arama_icerik = _url_getir(arama_url, timeout=8)

        if not arama_icerik:
            return sonuclar

        arama_data = json.loads(arama_icerik)
        arama_sonuclari = arama_data.get("query", {}).get("search", [])

        if not arama_sonuclari:
            return sonuclar

        # Adim 2: Bulunan sayfalarin iceriklerini al
        basliklar = "|".join(s["title"] for s in arama_sonuclari)
        icerik_params = urllib.parse.urlencode({
            "action": "query",
            "prop": "extracts",
            "exintro": "1",
            "explaintext": "1",
            "titles": basliklar,
            "format": "json",
            "utf8": "1",
        })
        icerik_url = f"https://{dil}.wikipedia.org/w/api.php?{icerik_params}"
        icerik_data_str = _url_getir(icerik_url, timeout=8)

        if not icerik_data_str:
            # Icerik alinamazsa arama snippet'lerini kullan
            for sr in arama_sonuclari:
                snippet = re.sub(r'<[^>]+>', '', sr.get("snippet", "")).strip()
                if snippet:
                    baslik = sr["title"]
                    sonuclar.append({
                        "baslik": baslik,
                        "url": f"https://{dil}.wikipedia.org/wiki/{urllib.parse.quote(baslik.replace(' ', '_'))}",
                        "ozet": snippet[:500],
                        "kaynak": f"wikipedia_{dil}_snippet"
                    })
            return sonuclar

        icerik_data = json.loads(icerik_data_str)
        sayfalar = icerik_data.get("query", {}).get("pages", {})

        for sayfa_id, sayfa in sayfalar.items():
            if sayfa_id == "-1":
                continue
            baslik = sayfa.get("title", "")
            icerik = sayfa.get("extract", "")
            if icerik and len(icerik) > 30:
                sonuclar.append({
                    "baslik": baslik,
                    "url": f"https://{dil}.wikipedia.org/wiki/{urllib.parse.quote(baslik.replace(' ', '_'))}",
                    "ozet": icerik[:800],
                    "kaynak": f"wikipedia_{dil}"
                })

    except Exception as e:
        logger.debug(f"Wikipedia {dil} arama hatasi: {e}")

    return sonuclar


# ═════════════════════════════════════════════════════════
# DUCKDUCKGO INSTANT ANSWER API
# ═════════════════════════════════════════════════════════

def _duckduckgo_instant(sorgu):
    """
    DuckDuckGo Instant Answer API — direkt cevaplar icin.
    API key gerektirmez, ama sadece bazi sorgularda sonuc verir.

    Returns: list of {"baslik": str, "url": str, "ozet": str, "kaynak": str}
    """
    sonuclar = []

    try:
        params = urllib.parse.urlencode({
            "q": sorgu,
            "format": "json",
            "no_redirect": "1",
            "no_html": "1",
            "skip_disambig": "1",
        })
        url = f"https://api.duckduckgo.com/?{params}"
        icerik = _url_getir(url, timeout=6)

        if not icerik:
            return sonuclar

        data = json.loads(icerik)

        # Abstract (genellikle Wikipedia'dan)
        abstract = data.get("AbstractText", "").strip()
        abstract_url = data.get("AbstractURL", "")
        heading = data.get("Heading", "").strip()
        if abstract and len(abstract) > 20:
            sonuclar.append({
                "baslik": heading or sorgu,
                "url": abstract_url,
                "ozet": abstract[:500],
                "kaynak": "duckduckgo_instant"
            })

        # Direkt cevap
        answer = data.get("Answer", "").strip()
        if answer and len(answer) > 5:
            sonuclar.append({
                "baslik": "Direkt Cevap",
                "url": "",
                "ozet": answer[:500],
                "kaynak": "duckduckgo_answer"
            })

    except Exception as e:
        logger.debug(f"DuckDuckGo Instant API hatasi: {e}")

    return sonuclar


# ═════════════════════════════════════════════════════════
# ANA ARAMA FONKSİYONU
# ═════════════════════════════════════════════════════════

def duckduckgo_ara(sorgu, max_sonuc=5):
    """
    Birlesik arama: Wikipedia TR → Wikipedia EN → DuckDuckGo Instant
    Returns: list of {"baslik": str, "url": str, "ozet": str, "kaynak": str}
    """
    tum_sonuclar = []

    # 1. Wikipedia TR (en guvenilir)
    wiki_tr = _wikipedia_ara(sorgu, dil="tr", max_sonuc=3)
    tum_sonuclar.extend(wiki_tr)
    logger.info(f"Wikipedia TR: '{sorgu}' -> {len(wiki_tr)} sonuc")

    # 2. DuckDuckGo Instant (hizli direkt cevaplar)
    ddg = _duckduckgo_instant(sorgu)
    tum_sonuclar.extend(ddg)
    logger.info(f"DuckDuckGo Instant: '{sorgu}' -> {len(ddg)} sonuc")

    # 3. Wikipedia EN fallback (Turkce sonuc azsa)
    if len(tum_sonuclar) < 2:
        wiki_en = _wikipedia_ara(sorgu, dil="en", max_sonuc=2)
        tum_sonuclar.extend(wiki_en)
        logger.info(f"Wikipedia EN: '{sorgu}' -> {len(wiki_en)} sonuc")

    # Tekrar eden sonuclari kaldir
    gorulen = set()
    benzersiz = []
    for s in tum_sonuclar:
        anahtar = s["ozet"][:80].lower()
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            benzersiz.append(s)

    logger.info(f"Toplam arama: '{sorgu}' -> {len(benzersiz)} benzersiz sonuc")
    return benzersiz[:max_sonuc]


# ═════════════════════════════════════════════════════════
# SAYFA İÇERİĞİ OKUMA (WEB KAZIMA)
# ═════════════════════════════════════════════════════════

def sayfa_oku(url, max_karakter=2000):
    """
    Bir web sayfasinin icerigini oku ve ozet cikar.
    Returns: str (temiz metin) veya None
    """
    try:
        html = _url_getir(url, timeout=8)
        if not html:
            return None

        metin = _html_temizle(html)

        if len(metin) < 50:
            return None

        if len(metin) > max_karakter:
            kesim = metin[:max_karakter]
            son_nokta = kesim.rfind(".")
            if son_nokta > max_karakter * 0.5:
                metin = kesim[:son_nokta + 1]
            else:
                metin = kesim + "..."

        return metin

    except Exception as e:
        logger.debug(f"Sayfa okuma hatasi ({url[:60]}): {e}")
        return None


# ═════════════════════════════════════════════════════════
# AKILLI ARAMA — AI İÇİN BAĞLAM OLUŞTUR
# ═════════════════════════════════════════════════════════

def arastir(sorgu, detayli=True):
    """
    Ana arastirma fonksiyonu.
    1. Wikipedia + DuckDuckGo'da ara
    2. En iyi sonucun sayfasini oku (detayli modda)
    3. AI'a gonderilebilecek yapilandirilmis baglam dondur

    Returns: dict {
        "sorgu": str,
        "sonuclar": list,
        "baglam": str,
        "basarili": bool,
        "sure_ms": int
    }
    """
    baslangic = time.time()

    # 1. Arama yap
    sonuclar = duckduckgo_ara(sorgu)

    if not sonuclar:
        sure = int((time.time() - baslangic) * 1000)
        return {
            "sorgu": sorgu,
            "sonuclar": [],
            "baglam": "",
            "basarili": False,
            "sure_ms": sure
        }

    # 2. Baglam olustur
    baglam_parcalari = [f"Web arama sonuclari ({sorgu}):"]

    for i, s in enumerate(sonuclar[:5], 1):
        baglam_parcalari.append(f"\n{i}. {s['baslik']}")
        baglam_parcalari.append(f"   {s['ozet']}")

    # 3. Detayli modda ek sayfa oku (Wikipedia zaten icerik veriyor,
    #    bu sadece Wikipedia disindaki kaynaklar icin)
    if detayli and sonuclar:
        for s in sonuclar[:2]:
            url = s.get("url", "")
            kaynak = s.get("kaynak", "")
            # Wikipedia zaten tam icerik verdi, tekrar okumaya gerek yok
            if "wikipedia" in kaynak:
                continue
            if url and url.startswith("http"):
                icerik = sayfa_oku(url, max_karakter=1500)
                if icerik:
                    baglam_parcalari.append(f"\nDetay ({s['baslik'][:50]}):")
                    baglam_parcalari.append(icerik[:1500])
                    break

    baglam = "\n".join(baglam_parcalari)
    sure = int((time.time() - baslangic) * 1000)

    logger.info(f"Arastirma tamamlandi: '{sorgu}' -> {len(sonuclar)} sonuc, {sure}ms")

    return {
        "sorgu": sorgu,
        "sonuclar": sonuclar,
        "baglam": baglam,
        "basarili": True,
        "sure_ms": sure
    }


# ═════════════════════════════════════════════════════════
# SORGU SINIFLANDIRMA — Arama gerekli mi?
# ═════════════════════════════════════════════════════════

def arama_gerekli_mi(metin):
    """
    Kullanicinin sorusunun internet aramasi gerektirip gerektirmedigini belirle.
    Returns: (gerekli: bool, sorgu: str veya None)
    """
    metin_lower = metin.lower().strip()

    # 0. Kesinlikle ARAMA GEREKTIRMEYEN durumlar (erken cikis)
    komut_kelimeleri = [
        r"^(?:aç|ac|kapat|kapa|başlat|baslat|çalıştır|calistir|durdur|küçült|kucult|büyüt|buyut)",
        r"(?:sesi?|sesini?|parlakl|parlaklik|ekran[ıi]?)\s*(?:aç|ac|kapat|kapa|art|azalt|ayarla|düşür|dusur|yükselt|yukselt)",
        r"^(?:merhaba|selam|hey|günaydın|gunaydin|iyi\s*(?:geceler|aksamlar|günler))",
        r"^(?:nasılsın|nasilsin|naber|ne\s*haber|iyi\s*misin)",
        r"^(?:teşekkür|tesekkur|sağ\s*ol|sag\s*ol|eyvallah)",
        r"^(?:tamam|ok|evet|hayır|hayir|olur|olmaz|anladım|anladim)",
        r"(?:müzi[kğ]|şarkı|sarki|video|youtube)",
        r"(?:kendini?\s*güncelle|guncelle)",
        r"(?:alarm|hatırlat|hatırlat|not\s*al|zamanlayıcı|timer)",
        r"^(?:adım|adim|benim\s*ad)",
        r"(?:ekran\s*görüntüsü|screenshot|wifi|bluetooth)",
        r"(?:bilgisayar[ıi]?\s*kapat|sistemi?\s*kapat)",
        r"^(?:kaç|kac|saat\s*kaç|tarih\s*ne|bugün\s*ne)",
    ]
    for kalip in komut_kelimeleri:
        if re.search(kalip, metin_lower):
            return False, None

    # 1. Acik arastirma niyeti
    arastirma_kaliplari = [
        r"(?:araştır|arastır|arastir)",
        r"(?:internette?|google'?da?|webde)\s+(?:ara|bak|bul)",
        r"(?:haber|haberler)\s+(?:ne|neler|var|nedir)",
        r"son\s+(?:haber|gelişm|gelism|durum|deprem|zelzele|olay)",
        r"(?:güncel|guncel|gündem|gundem|günlük|gunluk)\s+",
    ]
    for kalip in arastirma_kaliplari:
        if re.search(kalip, metin_lower):
            sorgu = re.sub(r"(?:atlas|araştır|arastır|arastir|internette?|google'?da?|webde)\s*", "", metin_lower).strip()
            sorgu = re.sub(r"\s*(ara|bak|bul)\s*$", "", sorgu).strip()
            return True, sorgu or metin_lower

    # 2. Ansiklopedik bilgi sorulari
    bilgi_kaliplari = [
        r"(.+?)\s+(?:kimdir|kim(?:miş|mis|dir)?)",
        r"(.+?)\s+(?:nedir|ne(?:ymiş|ymis|dir)?|ne\s+demek)",
        r"(.+?)\s+(?:nerede(?:dir)?|nere(?:de|si|li|ye))",
        r"(.+?)\s+ne\s+zaman",
        r"(.+?)\s+(?:kaç|kac)(?:\s|$)",
        r"(.+?)\s+(?:ne\s*kadar)",
        r"(.+?)\s+(?:nasıl|nasil)\s+(?:çalışır|calisir|yapılır|yapilir|olur|oluşur|olusur)",
        r"(.+?)\s+hakkında",
        r"(.+?)\s+(?:tarihçe|tarihce|tarihi|geçmiş|gecmis)",
        r"(.+?)\s+(?:nüfusu?|nufusu?|başkenti?|baskenti?|para\s*birimi)",
        r"(.+?)\s+(?:anlamı|anlami|manası|manasi)\s+(?:ne|nedir)",
        r"(.+?)\s+(?:kurucusu?|mucidi?|kâşifi?|kasifi?)\s+(?:kim|ne)",
    ]
    for kalip in bilgi_kaliplari:
        m = re.search(kalip, metin_lower)
        if m:
            return True, metin_lower

    # 3. Guncel veri sorulari
    guncel_kaliplari = [
        r"(?:bitcoin|btc|ethereum|eth|kripto)",
        r"(?:altın|altin|gram\s*altın|gram\s*altin)",
        r"(?:hisse|borsa|bist|endeks)",
        r"(?:deprem|zelzele|son\s*deprem)",
        r"(?:seçim|secim|oy)\s*(?:sonuç|sonuc|ne|nasıl|nasil)",
        r"(?:maç|mac)\s*(?:skor|sonuç|sonuc|kaç|kac|ne)",
        r"(?:hava\s*durumu|hava\s*nasıl|hava\s*nasil)",
        r"(?:dolar|euro|sterlin|pound)\s*(?:kaç|kac|ne\s*kadar|fiyat)",
        r"(?:fiyat|ücret|ucret|maliyet)",
    ]
    for kalip in guncel_kaliplari:
        if re.search(kalip, metin_lower):
            return True, metin_lower

    # 4. "son X" kalıbı
    if re.search(r"^son\s+\w+", metin_lower):
        return True, metin_lower

    # 5. Genel soru kelimeleri
    soru_kelimeleri = ["nedir", "kimdir", "nerede", "nereye", "nasıl", "nasil",
                       "neden", "niçin", "nicin", "kaç", "kac", "ne kadar",
                       "hangi", "ne zaman"]
    for kelime in soru_kelimeleri:
        if kelime in metin_lower and len(metin_lower) > 8:
            return True, metin_lower

    # 6. Gerekli degil
    return False, None


# ═════════════════════════════════════════════════════════
# TEST
# ═════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    testler = [
        "Elon Musk kimdir",
        "yapay zeka nedir",
        "Turkiye nufusu kac",
        "son depremler",
        "Bitcoin fiyati ne kadar",
    ]

    for test in testler:
        print(f"\n{'='*60}")
        print(f"Sorgu: {test}")
        sonuc = arastir(test)
        print(f"Basarili: {sonuc['basarili']}")
        print(f"Sure: {sonuc['sure_ms']}ms")
        print(f"Sonuc sayisi: {len(sonuc['sonuclar'])}")
        if sonuc["baglam"]:
            print(f"Baglam (ilk 300):\n{sonuc['baglam'][:300]}")
