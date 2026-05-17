"""
ATLAS - Web Arama Motoru
=========================
Beyin Karsiligi: Duyusal Korteks + Islem Bellegi Genisletmesi
Gorev: Internetten bilgi toplama, ozet cikarma, AI'a baglam saglama

DuckDuckGo arama (API key gerektirmez) + basit web kazima.
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
        # Fallback: regex ile temizle
        metin = re.sub(r'<script[^>]*>.*?</script>', '', html_text, flags=re.DOTALL | re.IGNORECASE)
        metin = re.sub(r'<style[^>]*>.*?</style>', '', metin, flags=re.DOTALL | re.IGNORECASE)
        metin = re.sub(r'<[^>]+>', ' ', metin)
        metin = re.sub(r'\s+', ' ', metin)
        return metin.strip()


def _url_getir(url, timeout=8):
    """URL icerigini indir. Basit HTTP GET."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/json",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.5",
        }
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=timeout)
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")
    except Exception as e:
        logger.debug(f"URL indirme hatasi ({url[:60]}): {e}")
        return None


# ═════════════════════════════════════════════════════════
# DUCKDUCKGO ARAMA (API KEY GEREKTIRMEZ)
# ═════════════════════════════════════════════════════════

def duckduckgo_ara(sorgu, max_sonuc=5):
    """
    DuckDuckGo Instant Answer API + HTML arama.
    Returns: list of {"baslik": str, "url": str, "ozet": str}
    """
    sonuclar = []

    # 1. DuckDuckGo Instant Answer API (hizli, yapilandirilmis)
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

        if icerik:
            data = json.loads(icerik)

            # Abstract (Wikipedia vs.)
            abstract = data.get("AbstractText", "").strip()
            abstract_url = data.get("AbstractURL", "")
            if abstract:
                sonuclar.append({
                    "baslik": data.get("Heading", sorgu),
                    "url": abstract_url,
                    "ozet": abstract[:500],
                    "kaynak": "duckduckgo_instant"
                })

            # Answer (direkt cevap)
            answer = data.get("Answer", "").strip()
            if answer:
                sonuclar.append({
                    "baslik": "Direkt Cevap",
                    "url": "",
                    "ozet": answer[:500],
                    "kaynak": "duckduckgo_answer"
                })

            # Related Topics
            for topic in data.get("RelatedTopics", [])[:3]:
                if isinstance(topic, dict) and "Text" in topic:
                    sonuclar.append({
                        "baslik": topic.get("Text", "")[:80],
                        "url": topic.get("FirstURL", ""),
                        "ozet": topic.get("Text", "")[:300],
                        "kaynak": "duckduckgo_related"
                    })

    except Exception as e:
        logger.debug(f"DuckDuckGo Instant API hatasi: {e}")

    # 2. DuckDuckGo HTML arama (fallback — daha fazla sonuc)
    if len(sonuclar) < 2:
        try:
            params = urllib.parse.urlencode({"q": sorgu})
            url = f"https://html.duckduckgo.com/html/?{params}"
            html = _url_getir(url, timeout=8)

            if html:
                # Basit regex ile sonuc cikar
                # DuckDuckGo HTML sayfasindaki sonuc bloklari
                bloklar = re.findall(
                    r'<a[^>]*class="result__a"[^>]*href="([^"]*)"[^>]*>(.*?)</a>.*?'
                    r'<a[^>]*class="result__snippet"[^>]*>(.*?)</a>',
                    html, re.DOTALL
                )

                for href, baslik_html, ozet_html in bloklar[:max_sonuc]:
                    baslik = _html_temizle(baslik_html).strip()
                    ozet = _html_temizle(ozet_html).strip()
                    # DuckDuckGo redirect URL'sini coz
                    gercek_url = href
                    if "uddg=" in href:
                        m = re.search(r'uddg=([^&]+)', href)
                        if m:
                            gercek_url = urllib.parse.unquote(m.group(1))

                    if baslik and ozet:
                        sonuclar.append({
                            "baslik": baslik[:100],
                            "url": gercek_url,
                            "ozet": ozet[:300],
                            "kaynak": "duckduckgo_html"
                        })

        except Exception as e:
            logger.debug(f"DuckDuckGo HTML arama hatasi: {e}")

    # 3. Wikipedia Turkce fallback (eger hala az sonuc varsa)
    if len(sonuclar) < 2:
        try:
            wiki_sorgu = urllib.parse.quote(sorgu)
            wiki_url = f"https://tr.wikipedia.org/api/rest_v1/page/summary/{wiki_sorgu}"
            wiki_icerik = _url_getir(wiki_url, timeout=5)
            if wiki_icerik:
                wiki_data = json.loads(wiki_icerik)
                wiki_ozet = wiki_data.get("extract", "")
                wiki_baslik = wiki_data.get("title", sorgu)
                if wiki_ozet and len(wiki_ozet) > 30:
                    sonuclar.append({
                        "baslik": wiki_baslik,
                        "url": wiki_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "ozet": wiki_ozet[:500],
                        "kaynak": "wikipedia_tr"
                    })
        except Exception as e:
            logger.debug(f"Wikipedia fallback hatasi: {e}")

    # 4. Wikipedia EN fallback (Turkce yoksa)
    if len(sonuclar) < 1:
        try:
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{wiki_sorgu}"
            wiki_icerik = _url_getir(wiki_url, timeout=5)
            if wiki_icerik:
                wiki_data = json.loads(wiki_icerik)
                wiki_ozet = wiki_data.get("extract", "")
                wiki_baslik = wiki_data.get("title", sorgu)
                if wiki_ozet and len(wiki_ozet) > 30:
                    sonuclar.append({
                        "baslik": wiki_baslik,
                        "url": wiki_data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                        "ozet": wiki_ozet[:500],
                        "kaynak": "wikipedia_en"
                    })
        except Exception as e:
            logger.debug(f"Wikipedia EN fallback hatasi: {e}")

    # Tekrar eden sonuclari kaldir
    gorulen = set()
    benzersiz = []
    for s in sonuclar:
        anahtar = s["ozet"][:100]
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            benzersiz.append(s)

    logger.info(f"Web arama: '{sorgu}' -> {len(benzersiz)} sonuc")
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

        # Cok kisa icerik anlamsiz olabilir
        if len(metin) < 50:
            return None

        # Max karakter siniri
        if len(metin) > max_karakter:
            # Cumle sonunda kes
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
    1. DuckDuckGo'da ara
    2. En iyi 1-2 sonucun sayfasini oku (detayli modda)
    3. AI'a gonderilebilecek yapilandirilmis baglam dondur

    Returns: dict {
        "sorgu": str,
        "sonuclar": list,
        "baglam": str,  # AI'a gonderilecek metin
        "basarili": bool
    }
    """
    baslangic = time.time()

    # 1. Arama yap
    sonuclar = duckduckgo_ara(sorgu)

    if not sonuclar:
        return {
            "sorgu": sorgu,
            "sonuclar": [],
            "baglam": "",
            "basarili": False,
            "sure_ms": int((time.time() - baslangic) * 1000)
        }

    # 2. Baglam olustur
    baglam_parcalari = [f"Web arama sonuclari ({sorgu}):"]

    for i, s in enumerate(sonuclar[:5], 1):
        baglam_parcalari.append(f"\n{i}. {s['baslik']}")
        baglam_parcalari.append(f"   {s['ozet']}")

    # 3. Detayli modda ilk sonucun sayfasini da oku
    if detayli and sonuclar:
        for s in sonuclar[:2]:
            url = s.get("url", "")
            if url and url.startswith("http"):
                icerik = sayfa_oku(url, max_karakter=1500)
                if icerik:
                    baglam_parcalari.append(f"\nDetay ({s['baslik'][:50]}):")
                    baglam_parcalari.append(icerik[:1500])
                    break  # Bir sayfa yeterli

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

    Gerekli olan durumlar:
    - Guncel bilgi (fiyat, haber, skor, hava durumu, deprem, nufus)
    - "arastir", "bul", "nedir" gibi arastirma niyeti
    - Nadir/spesifik bilgi sorulari
    - "kimdir", "ne zaman", "nerede", "kac", "nasil" gibi ansiklopedik sorular
    - "son X" gibi guncel durum sorulari

    Gerekli OLMAYAN durumlar:
    - Sohbet ("nasilsin", "merhaba")
    - Komut ("chrome ac", "sesi kapat", "muzik ac")
    - Basit matematik
    - Kisisel bilgi ("adim ne")
    """
    metin_lower = metin.lower().strip()

    # 0. Once kesinlikle ARAMA GEREKTIRMEYEN durumlar (erken cikis)
    # Komutlar, sohbet, kisisel sorular
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

    # 2. Bilgi sorulari — ansiklopedik (genis kaliplar)
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

    # 3. Guncel veri sorulari (fiyat, deprem, mac, secim, hava...)
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

    # 4. "son X" kalıbı — genellikle güncel bilgi ister
    if re.search(r"^son\s+\w+", metin_lower):
        return True, metin_lower

    # 5. Soru kalıbı tespiti — genel bilgi soruları
    # "X nedir", "X kim", "X nerede", "X ne zaman", "X kaç", "X nasıl"
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

    # Test aramalari
    testler = [
        "Python programlama dili nedir",
        "Turkiye nufusu kac",
        "yapay zeka son gelismeler",
    ]

    for test in testler:
        print(f"\n{'='*60}")
        print(f"Sorgu: {test}")
        sonuc = arastir(test)
        print(f"Basarili: {sonuc['basarili']}")
        print(f"Sure: {sonuc['sure_ms']}ms")
        print(f"Sonuc sayisi: {len(sonuc['sonuclar'])}")
        if sonuc["baglam"]:
            print(f"Baglam (ilk 500):\n{sonuc['baglam'][:500]}")
