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

def arastir(sorgu, detayli=False):
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
    - Guncel bilgi (fiyat, haber, skor, hava durumu)
    - "arastir", "bul", "nedir" gibi arastirma niyeti
    - Nadir/spesifik bilgi sorulari
    - "kimdir", "ne zaman", "nerede" gibi ansiklopedik sorular

    Gerekli OLMAYAN durumlar:
    - Sohbet ("nasilsin", "merhaba")
    - Komut ("chrome ac", "sesi kapat")
    - Basit matematik
    - Kisisel bilgi ("adim ne")
    """
    metin_lower = metin.lower().strip()

    # 1. Acik arastirma niyeti
    arastirma_kaliplari = [
        r"(?:arastır|araştır|arastir)",
        r"(?:internette?|google'?da?|webde)\s+(?:ara|bak|bul)",
        r"(?:haber|haberler)\s+(?:ne|neler|var)",
        r"son\s+(?:haber|gelism|durum)",
        r"(?:guncel|gundem|gunluk)\s+(?:haber|durum|gelism)",
    ]
    for kalip in arastirma_kaliplari:
        if re.search(kalip, metin_lower):
            # Arama sorgusunu cikar
            sorgu = re.sub(r"(?:atlas|arastır|araştır|arastir|internette|google'?da|webde|ara|bak|bul)\s*", "", metin_lower).strip()
            return True, sorgu or metin_lower

    # 2. Bilgi sorulari — ansiklopedik
    bilgi_kaliplari = [
        r"(.+?)\s+(?:kimdir|kim(?:miş|mis)?|kimin)",
        r"(.+?)\s+(?:nedir|ne(?:ymiş|ymis)?|ne\s+demek)",
        r"(.+?)\s+(?:nerede(?:dir)?|nere(?:de|si))",
        r"(.+?)\s+ne\s+zaman",
        r"(.+?)\s+(?:kac|kaç)\s+(?:yilinda|yılında|yasinda|yaşında)",
        r"(.+?)\s+hakkında\s+bilgi",
        r"(.+?)\s+(?:tarihçe|tarihce|gecmis|geçmiş)",
    ]
    for kalip in bilgi_kaliplari:
        m = re.search(kalip, metin_lower)
        if m:
            return True, metin_lower

    # 3. Guncel fiyat / veri sorulari
    guncel_kaliplari = [
        r"(?:bitcoin|btc|ethereum|eth|kripto)\s*(?:fiyat|kac|kaç|ne\s*kadar)",
        r"(?:altin|altın|gram\s*altin)\s*(?:fiyat|kac|kaç|ne\s*kadar)",
        r"(?:hisse|borsa|bist|endeks)\s*(?:ne|kac|kaç)",
        r"(?:deprem|zelzele)\s*(?:oldu|var|mi|nerede)",
        r"(?:secim|seçim|oy)\s*(?:sonuc|sonuç)",
        r"(?:mac|maç)\s*(?:skor|sonuc|sonuç|kac|kaç)",
    ]
    for kalip in guncel_kaliplari:
        if re.search(kalip, metin_lower):
            return True, metin_lower

    # 4. Gerekli degil — sohbet, komut, basit sorular
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
