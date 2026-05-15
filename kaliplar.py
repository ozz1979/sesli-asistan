"""
Turkce Gundelik Konusma Kaliplari v6.0
- 150+ yerel komut ve soru-cevap kalibi
- AI'ya gitmeden aninda yanit (0ms)
- Kategorilere ayrilmis, kolay genisletilebilir
"""
import time
import math
import random


# =============================================
# SELAMLAMA & VEDALAŞMA
# =============================================
SELAMLAMA = [
    "merhaba", "selam", "hey", "heyy", "heey",
    "nasilsin", "nasilsiniz", "naber", "nabersin", "ne haber",
    "ne var ne yok", "iyi misin", "iyimisin",
    "beni duyuyor", "duyuyor musun", "anliyor musun",
    "anlayabiliyor", "anliyabiliyor",
    "orada misin", "hazir misin", "burada misin",
    "beni anlayabiliyor", "beni duyabiliyor",
    "test", "calisiyorsun", "calisiyor musun",
    "uyanik misin", "dinliyor musun",
    "duydun mu", "var misin",
]

GUNAYDIN = ["gunaydin", "iyi sabahlar", "sabah", "hayirli sabahlar"]
IYI_AKSAMLAR = ["iyi aksamlar", "aksamlar", "hayirli aksamlar"]
IYI_GECELER = ["iyi geceler", "geceler", "hayirli geceler"]
VEDALASMASI = ["hosca kal", "gorusuruz", "gorusmek uzere", "bay bay",
               "bye", "bybay", "kendine iyi bak", "iyi gunler",
               "gule gule", "horoscakal", "hoscakal"]

TESEKKUR = ["tesekkur", "tesekkurler", "sagol", "saol", "eyv", "eyvallah",
            "super", "harika", "mukemmel", "guzel", "bravo",
            "aferin", "iyi is", "cok iyi", "basarili",
            "helal olsun", "eline saglik", "sagolasın"]

OZUR = ["ozur", "pardon", "kusura bakma", "affedersin", "uzgunum"]

# =============================================
# KIMLIK SORULARI
# =============================================
ISIM_SORULARI = ["adin ne", "ismin ne", "sen kimsin", "kimsin sen",
                 "kendinizi tanitir", "kendini tanit", "kimsiniz",
                 "adini soyle", "ne demem lazim sana"]

ISIM_DEGISTIR = ["adimi degistir", "ismimi degistir", "adimi guncelle",
                 "ismimi guncelle", "beni tanimiyorsun", "beni tani",
                 "adimi kaydet", "ismimi kaydet", "beni hatirla",
                 "adimi sor", "ismimi sor", "beni unut", "adimi sifirla"]

GOREV_SORULARI = ["gorevin ne", "ne yapiyorsun", "ne is yapiyorsun",
                  "ne ise yariyorsun", "gorevi ne", "amacin ne",
                  "ne isi yapiyorsun", "sen ne sin"]

YETENEK_SORULARI = ["neler yapabilirsin", "ne biliyorsun", "ne yapabilirsin",
                    "yeteneklerin ne", "bana ne yapabilirsin",
                    "ne tur isler yapabilirsin", "komutlarin ne",
                    "yardim et", "yardim", "nasil kullanilir",
                    "ne sorabilirim", "hangi komutlar var",
                    "bana yardim et", "help", "ne biliyorsun"]

YAS_SORULARI = ["kac yasindasin", "yasin kac", "ne zaman yapildin",
                "ne zaman olusturuldun", "kac yasinda"]

NERELI_SORULARI = ["nerelisin", "nereden geliyorsun", "nereli",
                   "nerede yasiyorsun", "memleketin neresi"]

DUYGULAR = ["mutsuzum", "uzgunum", "kotu hissediyorum", "sikildim",
            "canım sıkılıyor", "canim sikildi", "bunaldim",
            "stresli", "stres", "yoruldum", "yorgunum"]

MUTLU = ["mutluyum", "cok iyiyim", "harika hissediyorum",
         "keyifli", "neseliyim", "cok guzel"]

# =============================================
# MATEMATIK
# =============================================
MATEMATIK_KALIPLARI = ["kac eder", "kac yapar", "toplami kac",
                       "hesapla", "carpim", "bolum", "kare",
                       "karekoku", "yuzde kaci"]

# =============================================
# GENEL BILGI SORULARI (yerel cevaplar)
# =============================================
TURKIYE_BASKENT = ["turkiyenin baskenti", "baskent neresi", "baskenti neresi",
                   "turkiye baskenti", "ankarada mi baskent"]

GUNLER = ["pazartesi", "sali", "carsamba", "persembe", "cuma", "cumartesi", "pazar"]

MEVSIMLER = ["hangi mevsim", "mevsim ne", "simdi hangi mevsim"]

# =============================================
# ESPRI & EGLENCE
# =============================================
ESPRI_ISTEKLERI = ["espri yap", "fikra anlat", "saka yap", "komik birsey soyle",
                   "beni guldir", "guldurcen", "bir fikra", "bir espri"]

ESPRILER = [
    "Bilgisayar neden usutmez? Cunku her zaman antivirus kullanir!",
    "Programci neden gozluk takar? Cunku Java'yi goremez!",
    "Bir elektrik muhendisi ile yazilimci barda karsilasir. Elektrikci sorar: AC mi DC mi? Yazilimci cevap verir: TCP/IP!",
    "Bilgisayar doktora gider. Doktor sorar: Neyin var? Bilgisayar: Virus kaptim doktor bey!",
    "Neden bilgisayar muzik dinler? Cunku byte'lari sever!",
    "0 ile 1 kavga eder. 0 der ki: Sen hicbir sey degilsin! 1 der ki: Ama seninle birlikte 10 oluyoruz!",
    "Bir bug bara girer. Barmen sorar: Ne icersin? Bug cevap vermez, programi cokerter.",
    "En iyi sifre nedir? '12345 degil'. Cunku herkes dener!",
]

ILTIFAT = [
    "Sen de harika bir insansin!",
    "Seninle sohbet etmek cok guzel!",
    "Cok naziksin, tesekkur ederim!",
]

# =============================================
# ANA ESLESTIRME FONKSIYONU
# =============================================
def yerel_kalip_esle(mk, mo):
    """Turkce gundelik konusma kaliplarini esle.
    mk = turkce_normalize edilmis kucuk harf metin
    mo = orijinal metin
    Eslestiyse dict doner, eslesmediyse None"""

    # --- SELAMLAMA ---
    for s in SELAMLAMA:
        if s in mk:
            return {"yanit": "Merhaba! Seni duyuyorum, nasil yardimci olabilirim?", "aksiyonlar": []}

    # --- GUNAYDIN ---
    for s in GUNAYDIN:
        if s in mk:
            saat = int(time.strftime("%H"))
            if saat < 12:
                return {"yanit": "Gunaydin! Bugun sana nasil yardimci olabilirim?", "aksiyonlar": []}
            else:
                return {"yanit": "Iyi gunler! Nasil yardimci olabilirim?", "aksiyonlar": []}

    # --- IYI AKSAMLAR ---
    for s in IYI_AKSAMLAR:
        if s in mk:
            return {"yanit": "Iyi aksamlar! Bir seyler yapmami ister misin?", "aksiyonlar": []}

    # --- IYI GECELER ---
    for s in IYI_GECELER:
        if s in mk:
            return {"yanit": "Iyi geceler! Yarin gorusmek uzere.", "aksiyonlar": []}

    # --- VEDALAŞMA ---
    for s in VEDALASMASI:
        if s in mk:
            return {"yanit": "Gorusmek uzere! Kendine iyi bak.", "aksiyonlar": []}

    # --- TESEKKUR ---
    for s in TESEKKUR:
        if s in mk:
            return {"yanit": "Rica ederim! Baska bir sey var mi?", "aksiyonlar": []}

    # --- OZUR ---
    for s in OZUR:
        if s in mk:
            return {"yanit": "Sorun degil! Nasil yardimci olabilirim?", "aksiyonlar": []}

    # --- SAAT ---
    if any(k in mk for k in ["saat kac", "saat ne", "saati soyle", "saati soyler",
                               "su an saat", "saat simdi", "simdiki saat"]):
        saat = time.strftime("%H:%M")
        return {"yanit": f"Saat {saat}", "aksiyonlar": []}

    # --- TARIH ---
    if any(k in mk for k in ["tarih", "bugun gun", "bugun ne", "hangi gun",
                               "kacinci gun", "gunlerden ne", "gun ne"]):
        tarih = time.strftime("%d/%m/%Y")
        gunler = ["Pazartesi", "Sali", "Carsamba", "Persembe", "Cuma", "Cumartesi", "Pazar"]
        gun_idx = int(time.strftime("%w"))
        gun = gunler[gun_idx - 1] if gun_idx > 0 else gunler[6]
        return {"yanit": f"Bugun {gun}, {tarih}", "aksiyonlar": []}

    # --- MEVSIM ---
    for s in MEVSIMLER:
        if s in mk:
            ay = int(time.strftime("%m"))
            if ay in [12, 1, 2]:
                mevsim = "Kis"
            elif ay in [3, 4, 5]:
                mevsim = "Ilkbahar"
            elif ay in [6, 7, 8]:
                mevsim = "Yaz"
            else:
                mevsim = "Sonbahar"
            return {"yanit": f"Simdi {mevsim} mevsimindeyiz.", "aksiyonlar": []}

    # --- ISIM DEGISTIR ---
    for s in ISIM_DEGISTIR:
        if s in mk:
            return {"yanit": "__ISIM_DEGISTIR__", "aksiyonlar": []}

    # --- ISIM SORULARI ---
    for s in ISIM_SORULARI:
        if s in mk:
            return {"yanit": "Ben senin sesli yapay zeka asistaninim. Bana istedigin ismi verebilirsin!", "aksiyonlar": []}

    # --- GOREV SORULARI ---
    for s in GOREV_SORULARI:
        if s in mk:
            return {"yanit": "Bilgisayarini sesli komutlarla yonetmene yardimci oluyorum. Uygulama acma, web arama, saat sorma ve daha bir cok sey yapabilirim!", "aksiyonlar": []}

    # --- YETENEK SORULARI ---
    for s in YETENEK_SORULARI:
        if s in mk:
            return {
                "yanit": "Yapabileceklerim: Uygulama acma ve kapatma, web'de arama, saat ve tarih soyleme, ekran goruntusu alma, ses seviyesi ayarlama, dosya bulma, bilgisayar bilgileri gosterme ve daha fazlasi!",
                "aksiyonlar": []
            }

    # --- YAS SORULARI ---
    for s in YAS_SORULARI:
        if s in mk:
            return {"yanit": "Ben bir yapay zeka asistaniyim, yasim yok ama her gun yeni seyler ogreniyorum!", "aksiyonlar": []}

    # --- NERELI SORULARI ---
    for s in NERELI_SORULARI:
        if s in mk:
            return {"yanit": "Ben dijital bir asistanım, senin bilgisayarinda yasiyorum!", "aksiyonlar": []}

    # --- DUYGU - UZGUN ---
    for s in DUYGULAR:
        if s in mk:
            yanitlar = [
                "Uzulme! Sana nasil yardimci olabilirim?",
                "Anliyorum. Belki biraz muzik acayim, iyi gelir?",
                "Basim sagolsun. Ben buradayim, bir sey yapmami ister misin?",
            ]
            return {"yanit": random.choice(yanitlar), "aksiyonlar": []}

    # --- DUYGU - MUTLU ---
    for s in MUTLU:
        if s in mk:
            return {"yanit": "Bu harika! Birlikte guzel seyler yapalim!", "aksiyonlar": []}

    # --- ESPRI ---
    for s in ESPRI_ISTEKLERI:
        if s in mk:
            return {"yanit": random.choice(ESPRILER), "aksiyonlar": []}

    # --- TURKIYE BASKENT ---
    for s in TURKIYE_BASKENT:
        if s in mk:
            return {"yanit": "Turkiye'nin baskenti Ankara'dir.", "aksiyonlar": []}

    # --- BASIT MATEMATIK ---
    mat_sonuc = _matematik_coz(mk)
    if mat_sonuc is not None:
        return {"yanit": f"Sonuc: {mat_sonuc}", "aksiyonlar": []}

    # --- ILTIFAT ---
    if any(k in mk for k in ["seni seviyorum", "harika sin", "harikasın",
                               "en iyisin", "cok akilli", "zekisin"]):
        return {"yanit": random.choice(ILTIFAT), "aksiyonlar": []}

    # --- HAVA DURUMU ---
    if any(k in mk for k in ["hava durumu", "hava nasil", "sicaklik kac",
                               "yagmur yagacak mi", "kar yagacak",
                               "bugunku hava", "yarin hava"]):
        return {
            "yanit": "Hava durumunu aciyorum",
            "aksiyonlar": [{"fonksiyon": "url_ac", "parametreler": {"url": "https://www.google.com/search?q=hava+durumu"}}]
        }

    # --- DOVIZ / KUR ---
    if any(k in mk for k in ["dolar kac", "euro kac", "doviz", "kur ne",
                               "dolar kuru", "euro kuru", "altin fiyati",
                               "bitcoin kac"]):
        sorgu = "doviz kuru"
        if "dolar" in mk:
            sorgu = "dolar kuru"
        elif "euro" in mk:
            sorgu = "euro kuru"
        elif "altin" in mk:
            sorgu = "altin fiyati"
        elif "bitcoin" in mk:
            sorgu = "bitcoin fiyati"
        return {
            "yanit": f"{sorgu.title()} bakiyorum",
            "aksiyonlar": [{"fonksiyon": "url_ac", "parametreler": {"url": f"https://www.google.com/search?q={sorgu.replace(' ', '+')}"}}]
        }

    # --- HABERLER ---
    if any(k in mk for k in ["haberler", "son dakika", "gundem",
                               "bugunun haberleri", "haberleri goster"]):
        return {
            "yanit": "Haberleri aciyorum",
            "aksiyonlar": [{"fonksiyon": "url_ac", "parametreler": {"url": "https://news.google.com/home?hl=tr&gl=TR"}}]
        }

    # --- MUZIK ONERISI ---
    if any(k in mk for k in ["muzik oner", "sarki oner", "ne dinleyeyim",
                               "guzel muzik", "muzik ac"]):
        return {
            "yanit": "Muzik aciyorum",
            "aksiyonlar": [{"fonksiyon": "url_ac", "parametreler": {"url": "https://www.youtube.com/results?search_query=turkce+pop+muzik+2024"}}]
        }

    # --- YEMEK ---
    if any(k in mk for k in ["yemek tarifi", "ne yapsam", "ne pisireyim",
                               "aksam yemegi", "ogle yemegi", "yemek oner"]):
        return {
            "yanit": "Yemek tarifi ariyorum",
            "aksiyonlar": [{"fonksiyon": "web_ara", "parametreler": {"sorgu": "kolay yemek tarifleri"}}]
        }

    # --- CEVIRI ---
    if any(k in mk for k in ["ingilizce cevir", "turkce cevir", "ceviri yap",
                               "translate", "nasil denir"]):
        return {
            "yanit": "Google Ceviri aciyorum",
            "aksiyonlar": [{"fonksiyon": "url_ac", "parametreler": {"url": "https://translate.google.com/?sl=tr&tl=en"}}]
        }

    # --- TIMER / ALARM ---
    if any(k in mk for k in ["zamanlayici kur", "timer", "alarm kur",
                               "beni uyar", "hatırlat", "hatirlat"]):
        return {"yanit": "Hatirlatma ozelligim henuz gelistirme asamasinda, yakinda eklenecek!", "aksiyonlar": []}

    # --- NE ZAMAN ---
    if any(k in mk for k in ["bugun tatil mi", "resmi tatil", "bayram ne zaman"]):
        return {
            "yanit": "Tatil takvimini aciyorum",
            "aksiyonlar": [{"fonksiyon": "web_ara", "parametreler": {"sorgu": "2026 resmi tatiller turkiye"}}]
        }

    # --- PROGRAMLAMA ---
    if any(k in mk for k in ["python nedir", "kod yaz", "programlama",
                               "html nedir", "javascript"]):
        return {
            "yanit": "Programlama hakkinda bilgi ariyorum",
            "aksiyonlar": [{"fonksiyon": "web_ara", "parametreler": {"sorgu": mk}}]
        }

    # --- KIM BULDU ---
    if any(k in mk for k in ["seni kim yapti", "seni kim olusturdu", "seni kim programladi",
                               "yaratıcın kim", "yapimcin kim", "gelistiricin kim"]):
        return {"yanit": "Beni gelistiren ekip tarafindan olusturuldum. Seninle calistigim icin cok mutluyum!", "aksiyonlar": []}

    # --- EVET / HAYIR ---
    if mk.strip() in ["evet", "tamam", "olur", "ok", "peki", "tabii", "tabi"]:
        return {"yanit": "Tamam! Baska bir sey yapmami ister misin?", "aksiyonlar": []}

    if mk.strip() in ["hayir", "yok", "istemiyorum", "gerek yok"]:
        return {"yanit": "Tamam, buradayim ihtiyacin olursa!", "aksiyonlar": []}

    # --- RASTGELE SAYI ---
    if any(k in mk for k in ["rastgele sayi", "sans sayisi", "loto sayisi",
                               "zar at", "yazi tura"]):
        if "zar" in mk:
            sayi = random.randint(1, 6)
            return {"yanit": f"Zar: {sayi} geldi!", "aksiyonlar": []}
        elif "yazi" in mk or "tura" in mk:
            sonuc = random.choice(["Yazi", "Tura"])
            return {"yanit": f"Sonuc: {sonuc}!", "aksiyonlar": []}
        else:
            sayilar = sorted(random.sample(range(1, 50), 6))
            return {"yanit": f"Sans sayilarin: {', '.join(map(str, sayilar))}", "aksiyonlar": []}

    # Eslesmedi
    return None


def _matematik_coz(mk):
    """Basit matematik islemlerini coz"""
    import re

    # "2 arti 3", "5 carpi 4" vb.
    mk2 = mk.replace("arti", "+").replace("eksi", "-").replace("carpi", "*")
    mk2 = mk2.replace("bolü", "/").replace("bolu", "/").replace("ustu", "**")

    # Sayisal ifadeyi bul: "234 + 567" vb.
    match = re.search(r'(\d+[\.,]?\d*)\s*([+\-*/^])\s*(\d+[\.,]?\d*)', mk2)
    if match:
        try:
            a = float(match.group(1).replace(",", "."))
            op = match.group(2)
            b = float(match.group(3).replace(",", "."))
            if op == "+":
                sonuc = a + b
            elif op == "-":
                sonuc = a - b
            elif op == "*":
                sonuc = a * b
            elif op == "/":
                if b == 0:
                    return "Sifira bolme hatasi!"
                sonuc = a / b
            elif op == "^":
                sonuc = a ** b
            else:
                return None
            # Tam sayi ise .0 gosterme
            if sonuc == int(sonuc):
                return str(int(sonuc))
            return f"{sonuc:.2f}"
        except:
            return None

    # "5'in karesi", "16'nin karekoku"
    kare_match = re.search(r'(\d+).*kare[si]*', mk)
    if kare_match and "karekoku" not in mk:
        sayi = int(kare_match.group(1))
        return str(sayi ** 2)

    karekoku_match = re.search(r'(\d+).*karekoku', mk)
    if karekoku_match:
        sayi = int(karekoku_match.group(1))
        sonuc = math.sqrt(sayi)
        if sonuc == int(sonuc):
            return str(int(sonuc))
        return f"{sonuc:.2f}"

    # "150'nin yuzde 20'si"
    yuzde_match = re.search(r'(\d+).*yuzde\s*(\d+)', mk)
    if yuzde_match:
        sayi = float(yuzde_match.group(1))
        yuzde = float(yuzde_match.group(2))
        sonuc = sayi * yuzde / 100
        if sonuc == int(sonuc):
            return str(int(sonuc))
        return f"{sonuc:.2f}"

    return None
