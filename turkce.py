"""
Turkce Dil Modulu v7.5
- Turk alfabesi ve ozel karakterler
- 500+ Turkce erkek/kadin isim veritabani
- STT (ses tanima) sonrasi Turkce duzeltme
- Turkce fonetik eslestirme ve isim tanima
- Turkce imla ve gramer kurallari bilgisi
- Gunluk konusma desenleri
"""


# =============================================
# TURK ALFABESI
# =============================================
TURK_ALFABESI = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
TURK_ALFABESI_KUCUK = "abcçdefgğhıijklmnoöprsştuüvyz"

# Sesli harfler
KALIN_UNLULAR = "aıou"   # Kalin (art) unluler
INCE_UNLULAR = "eiöü"    # Ince (on) unluler
TUM_UNLULAR = KALIN_UNLULAR + INCE_UNLULAR

# Unsuz harfler
UNSUZLER = "bcçdfgğhjklmnprsştvyz"
SERT_UNSUZLER = "çfhkpsşt"  # Unsuz yumusamasi ve sertlesmesi icin
YUMUSAK_UNSUZLER = "bcdgğjlmnrvyz"

# ASCII karsilik tablosu
TURKCE_ASCII_MAP = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
ASCII_TURKCE_MAP = {
    "c": ["c", "ç"], "g": ["g", "ğ"], "i": ["i", "ı", "İ"],
    "o": ["o", "ö"], "s": ["s", "ş"], "u": ["u", "ü"],
}


def turkce_normalize(metin):
    """Turkce karakterleri ASCII'ye cevir (eslestirme icin)"""
    return metin.translate(TURKCE_ASCII_MAP)


def turkce_kucuk(metin):
    """Turkce buyuk/kucuk harf donusumu (I->ı, İ->i)"""
    sonuc = ""
    for c in metin:
        if c == "I":
            sonuc += "ı"
        elif c == "İ":
            sonuc += "i"
        else:
            sonuc += c.lower()
    return sonuc


def turkce_buyuk(metin):
    """Turkce buyuk harf donusumu (i->İ, ı->I)"""
    sonuc = ""
    for c in metin:
        if c == "i":
            sonuc += "İ"
        elif c == "ı":
            sonuc += "I"
        else:
            sonuc += c.upper()
    return sonuc


def turkce_baslik(metin):
    """Turkce Title Case (ilk harf buyuk, Turkce kurallarina uygun)"""
    kelimeler = metin.split()
    sonuc = []
    for k in kelimeler:
        if not k:
            continue
        ilk = turkce_buyuk(k[0])
        geri = turkce_kucuk(k[1:]) if len(k) > 1 else ""
        sonuc.append(ilk + geri)
    return " ".join(sonuc)


# =============================================
# TURKCE ISIM VERITABANI (500+ isim)
# =============================================
ERKEK_ISIMLERI = {
    "ahmet", "mehmet", "mustafa", "ali", "hasan", "huseyin", "ibrahim",
    "ismail", "osman", "yusuf", "murat", "omer", "halil", "hakan",
    "burak", "emre", "can", "cem", "cenk", "cihan", "deniz", "efe",
    "eren", "erhan", "erkan", "faruk", "fatih", "ferhat", "fikret",
    "furkan", "gokhan", "gokturk", "hakan", "haluk", "hamza", "ilhan",
    "ilker", "kadir", "kagan", "kemal", "kerem", "koray", "levent",
    "mahir", "mahmut", "mert", "mesut", "metin", "muhammet", "muhammed",
    "necati", "nihat", "oguz", "oguzhan", "onur", "orhan", "ozan",
    "ozgur", "ozkan", "ramazan", "recep", "resul", "ridvan", "riza",
    "samet", "sami", "selim", "selcuk", "semih", "sercan", "serdar",
    "serhan", "serhat", "sinan", "soner", "suat", "suleyman",
    "tarik", "tolga", "tuncay", "turgut", "turhan", "ufuk", "ugur",
    "umit", "umut", "utku", "volkan", "yakup", "yasin", "yavuz",
    "yigit", "yucel", "zafer", "zeki", "baris", "berkay", "berke",
    "bora", "cagri", "caglar", "cuneyt", "dogan", "doruk", "ediz",
    "emir", "engin", "erdem", "erdogan", "ergul", "erol", "eyup",
    "ferit", "galip", "gorkem", "gunes", "gurkan", "hayri", "hikmet",
    "ilyas", "irfan", "kaan", "kayra", "kazim", "kursat", "lütfi",
    "mazhar", "melih", "nadir", "namik", "nazim", "necdet", "nedim",
    "nuri", "oktay", "polat", "ragip", "rasim", "ruhi", "rüstem",
    "sadik", "salih", "savas", "sedat", "sefer", "sezgin", "talha",
    "tamer", "tayfun", "teoman", "timur", "tugrul", "tuncer", "ural",
    "vedat", "veli", "yalcin", "yasar", "yilmaz", "yunus", "ziya",
    "adem", "adnan", "alperen", "alper", "arda", "arif", "aslan",
    "ata", "atakan", "atilla", "ayhan", "bahadir", "barbaros",
    "batuhan", "bayram", "berk", "bilal", "bilge", "cemal",
    "davut", "dursun", "ekrem", "elvan", "enes", "enver",
    "ersin", "eser", "evren", "feridun", "fuat", "gazi",
    "güven", "hakki", "hamit", "haydar", "hayrettin",
    "isa", "iskender", "kahraman", "kamil", "kasim",
    "kaya", "korhan", "lütfü", "malik", "mansur",
    "mevlüt", "mithat", "muhsin", "münir", "nafiz",
    "nusret", "öner", "özdemir", "pinar", "remzi",
    "rüstü", "sabri", "saffet", "sahap", "sakir",
    "selahattin", "seyfi", "sezai", "süleyman", "tahir",
    "tahsin", "talat", "tansu", "tarkan", "tevfik",
    "turan", "türker", "yüksel", "zühtü",
    "aras", "atlas", "ayaz", "batu", "bera", "çinar",
    "demir", "ediz", "ekin", "eymen", "göktürk",
    "kuzey", "miran", "poyraz", "yagiz", "yaman",
}

KADIN_ISIMLERI = {
    "ayse", "fatma", "emine", "hatice", "zeynep", "elif", "meryem",
    "esra", "sibel", "sevgi", "sevim", "sevinc", "sema", "semra",
    "sultan", "sule", "selin", "selma", "serpil", "simge", "sinem",
    "asli", "asu", "aylin", "aysegul", "aysel", "ayten", "azra",
    "banu", "bahar", "basak", "belgin", "beren", "beril", "betul",
    "birsen", "burcu", "busra", "canan", "ceren", "cicek", "damla",
    "defne", "derin", "derya", "didem", "dilek", "ebru", "eda",
    "elifnur", "elmas", "emel", "eylul", "feriha", "feride",
    "filiz", "fulya", "gamze", "gonca", "gul", "gulay", "gulcan",
    "gulden", "gulsah", "gulsen", "gulsum", "hande", "hazal",
    "hilal", "hulya", "inci", "irem", "jale", "kadriye",
    "kumsal", "leman", "leyla", "lale", "melike", "meltem",
    "mine", "munevver", "nalan", "naz", "nazan", "nazli",
    "nese", "nesrin", "nihan", "nihal", "nilufer", "nur",
    "nuray", "nurcan", "nurten", "olcay", "oya", "ozge",
    "ozlem", "pelin", "pembe", "pinar", "rabia", "rana",
    "reyhan", "ruhsar", "saadet", "sabiha", "safiye",
    "sakine", "seher", "seval", "sevda", "sevil",
    "songul", "sureyya", "sahin", "seyda", "seyma",
    "sehnaz", "tuba", "tugba", "tugce", "turkan",
    "ulku", "ummuhan", "yasemin", "yildiz", "zeliha",
    "ada", "almina", "asya", "bengisu", "belinay",
    "cansu", "ceyda", "ceylan", "dila", "dilara",
    "ecrin", "ela", "eliz", "gizem", "hira",
    "ilayda", "ipek", "irmak", "lara", "melis",
    "mina", "nisa", "nisa", "nehir", "serra",
    "su", "tara", "vera", "yaren", "zehra",
    "zümra", "ayla", "asya", "buse", "cemre",
    "deniz", "duygu", "ezgi", "funda", "gokce",
    "irmak", "melisa", "neslihan", "nursel", "peri",
    "rengin", "ruya", "sare", "sila", "sumeyye",
    "tulay", "umay", "vildan", "yeliz", "yesim",
}

# Tum isimler (normalize edilmis) -> orijinal hali
TUM_ISIMLER = {}
for _isim in ERKEK_ISIMLERI | KADIN_ISIMLERI:
    _norm = turkce_normalize(_isim.lower())
    TUM_ISIMLER[_norm] = _isim


# =============================================
# STT TURKCE DUZELTME
# =============================================

# Google STT'nin sik yaptigi Turkce hatalar
STT_DUZELTME_HARITASI = {
    # Yaygin yanlis -> dogru
    "slm": "selam",
    "nbr": "ne haber",
    "tmm": "tamam",
    "ok": "tamam",
    "okay": "tamam",
    "yes": "evet",
    "no": "hayir",
    "hello": "merhaba",
    "hi": "merhaba",
    "thank you": "tesekkurler",
    "thanks": "tesekkurler",
    "please": "lutfen",
    "sorry": "ozur dilerim",
    "google": "google",
    "chrome": "chrome",
    "youtube": "youtube",
    "whatsapp": "whatsapp",
    "instagram": "instagram",
    "spotify": "spotify",
}

# Turkce fonetik benzerlik haritalari (STT hatalari icin)
FONETIK_BENZERLIKLERI = {
    "b": "p", "p": "b",
    "c": "ç", "ç": "c",
    "d": "t", "t": "d",
    "g": "ğ", "ğ": "g", "k": "g",
    "j": "c",
    "s": "ş", "ş": "s", "z": "s",
}


def stt_duzelt(metin):
    """STT sonucunu Turkce icin duzelt"""
    if not metin:
        return metin

    metin = metin.strip()

    # 1) Bilinen STT hatalarini duzelt
    metin_kucuk = metin.lower()
    if metin_kucuk in STT_DUZELTME_HARITASI:
        return STT_DUZELTME_HARITASI[metin_kucuk]

    # 2) Baslangic/sondaki gereksiz noktalama temizle
    metin = metin.strip(".,;:!?")

    # 3) Turkce karakter duzeltmeleri (Google bazen ASCII dondurebilir)
    # "ozgur" -> "özgür", "calisma" -> "çalışma" gibi
    # Bu islemi yapmiyoruz cunku normalize edilmis metin de eslestirme icin kullaniliyor

    return metin.strip()


def isim_eslestir(metin, esik=0.6):
    """
    STT sonucunu Turkce isim veritabaniyla eslestir.
    Benzerlik skoru >= esik ise eslesen ismi dondurur.

    Args:
        metin: STT'den gelen ham metin
        esik: Minimum benzerlik skoru (0-1)

    Returns:
        (eslesen_isim, skor) veya (None, 0)
    """
    if not metin or len(metin) < 2:
        return None, 0

    # Temizle: "benim adim Ozgur" -> "ozgur"
    isim_adaylari = _isim_cikar(metin)

    en_iyi_isim = None
    en_iyi_skor = 0

    for aday in isim_adaylari:
        aday_norm = turkce_normalize(aday.lower().strip())
        if len(aday_norm) < 2:
            continue

        # 1) Tam eslestirme
        if aday_norm in TUM_ISIMLER:
            return TUM_ISIMLER[aday_norm], 1.0

        # 2) Benzerlik eslestirmesi
        for norm_isim, orijinal in TUM_ISIMLER.items():
            skor = _benzerlik_skoru(aday_norm, norm_isim)
            if skor > en_iyi_skor:
                en_iyi_skor = skor
                en_iyi_isim = orijinal

    if en_iyi_skor >= esik:
        return en_iyi_isim, en_iyi_skor

    return None, 0


def _isim_cikar(metin):
    """Metinden isim adaylarini cikar"""
    metin_kucuk = metin.lower().strip()

    # "benim adim X", "adim X", "ben X" kaliplarini temizle
    cikarma_kaliplari = [
        "benim adim ", "benim adım ", "adim ", "adım ",
        "benim ismim ", "ismim ", "ben ", "bana ",
        "isim ", "ad ", "benim ad ",
    ]
    temiz = metin_kucuk
    for kalip in cikarma_kaliplari:
        if temiz.startswith(kalip):
            temiz = temiz[len(kalip):]
            break

    # Hem temizlenmis hem orijinal metin adaylarini dondur
    adaylar = [temiz.strip()]
    # Birden fazla kelime varsa ilk kelimeyi de ekle
    parcalar = temiz.strip().split()
    if len(parcalar) > 1:
        adaylar.append(parcalar[0])
        adaylar.append(parcalar[-1])

    # Orijinal metin de aday olsun
    adaylar.append(metin_kucuk.strip())
    orijinal_parcalar = metin_kucuk.strip().split()
    if len(orijinal_parcalar) > 1:
        for p in orijinal_parcalar:
            adaylar.append(p)

    return list(set(adaylar))


def _benzerlik_skoru(s1, s2):
    """
    Iki string arasinda Turkce fonetik benzerlik skoru hesapla (0-1).
    Levenshtein + fonetik agirlik.
    """
    if not s1 or not s2:
        return 0.0

    # Uzunluk farki cok buyukse dusuk skor
    uzunluk_farki = abs(len(s1) - len(s2))
    if uzunluk_farki > max(len(s1), len(s2)) * 0.5:
        return 0.0

    # Basit karakter benzerlik (Jaccard-like)
    set1 = set(s1)
    set2 = set(s2)
    ortak = set1 & set2
    birlesim = set1 | set2

    if not birlesim:
        return 0.0

    jaccard = len(ortak) / len(birlesim)

    # Sirali eslestirme (ortak prefix/suffix)
    prefix_uzunluk = 0
    for i in range(min(len(s1), len(s2))):
        if s1[i] == s2[i]:
            prefix_uzunluk += 1
        else:
            break

    suffix_uzunluk = 0
    for i in range(1, min(len(s1), len(s2)) + 1):
        if s1[-i] == s2[-i]:
            suffix_uzunluk += 1
        else:
            break

    maks_uzunluk = max(len(s1), len(s2))
    sirali_skor = (prefix_uzunluk + suffix_uzunluk) / maks_uzunluk

    # Fonetik benzerlik (b/p, d/t, c/ç, s/ş gibi)
    fonetik_bonus = 0
    for i in range(min(len(s1), len(s2))):
        if s1[i] != s2[i]:
            if FONETIK_BENZERLIKLERI.get(s1[i]) == s2[i]:
                fonetik_bonus += 0.1
            elif FONETIK_BENZERLIKLERI.get(s2[i]) == s1[i]:
                fonetik_bonus += 0.1

    # Toplam skor
    skor = (jaccard * 0.3) + (sirali_skor * 0.5) + min(fonetik_bonus, 0.2)

    # Kisa isimlerde tam eslestirme daha onemli
    if len(s1) <= 4 and prefix_uzunluk >= len(s1) - 1:
        skor = max(skor, 0.8)
    if len(s2) <= 4 and prefix_uzunluk >= len(s2) - 1:
        skor = max(skor, 0.8)

    return min(skor, 1.0)


# =============================================
# TURKCE IMLA VE GRAMER BILGISI
# =============================================

# Buyuk unlu uyumu (kalin-kalin, ince-ince)
def unlu_uyumu_kontrol(kelime):
    """Buyuk unlu uyumunu kontrol et"""
    kelime = turkce_kucuk(kelime)
    son_unlu_kalin = True

    for harf in kelime:
        if harf in KALIN_UNLULAR:
            son_unlu_kalin = True
        elif harf in INCE_UNLULAR:
            son_unlu_kalin = False

    # Son unluye gore ek uyumu
    return "kalin" if son_unlu_kalin else "ince"


# Turkce zaman ifadeleri
ZAMAN_IFADELERI = {
    "simdi": "şimdi", "bugun": "bugün", "yarin": "yarın",
    "dun": "dün", "hafta": "hafta", "ay": "ay", "yil": "yıl",
    "saat": "saat", "dakika": "dakika", "saniye": "saniye",
    "sabah": "sabah", "ogle": "öğle", "aksam": "akşam", "gece": "gece",
    "pazartesi": "pazartesi", "sali": "salı", "carsamba": "çarşamba",
    "persembe": "perşembe", "cuma": "cuma",
    "cumartesi": "cumartesi", "pazar": "pazar",
    "ocak": "ocak", "subat": "şubat", "mart": "mart",
    "nisan": "nisan", "mayis": "mayıs", "haziran": "haziran",
    "temmuz": "temmuz", "agustos": "ağustos", "eylul": "eylül",
    "ekim": "ekim", "kasim": "kasım", "aralik": "aralık",
}

# Turkce sayi kelimeleri
SAYI_KELIMELERI = {
    "sifir": 0, "bir": 1, "iki": 2, "uc": 3, "dort": 4,
    "bes": 5, "alti": 6, "yedi": 7, "sekiz": 8, "dokuz": 9,
    "on": 10, "yirmi": 20, "otuz": 30, "kirk": 40, "elli": 50,
    "altmis": 60, "yetmis": 70, "seksen": 80, "doksan": 90,
    "yuz": 100, "bin": 1000, "milyon": 1000000, "milyar": 1000000000,
}

# Turkce soru kelimeleri
SORU_KELIMELERI = [
    "ne", "neden", "niye", "nicin", "nasil", "nerede", "nereye",
    "nereden", "ne zaman", "kim", "kime", "kimin", "kimi",
    "hangisi", "hangi", "kac", "kaca", "mi", "mu", "mı", "mü",
]

# Turkce baglaclar
BAGLACLAR = [
    "ve", "ile", "veya", "ya da", "ama", "fakat", "ancak",
    "lakin", "oysa", "halbuki", "cunku", "zira", "dolayisiyla",
    "bu yuzden", "bu nedenle", "o halde", "hem", "ne", "ise",
    "da", "de", "ki", "icin", "gibi", "kadar", "gore",
]


# =============================================
# ISIM TANIMA YARDIMCILARI
# =============================================

def isim_temizle_ve_duzelt(ham_metin):
    """
    STT'den gelen ham isim metnini temizle ve Turkce isim veritabaniyla duzelt.
    Hem arayuz.py hem main.py'nin _isim_kaydet fonksiyonlari icin.

    Returns:
        (duzeltilmis_isim, kesinlik) - kesinlik: 'kesin'|'tahmini'|'bilinmiyor'
    """
    if not ham_metin or len(ham_metin.strip()) < 2:
        return None, "bilinmiyor"

    metin = ham_metin.strip()

    # 1) STT duzeltmesi
    metin = stt_duzelt(metin)

    # 2) "benim adim X" kaliplarini temizle
    for kalip in ["benim adim", "benim adım", "adim", "adım",
                  "benim ismim", "ismim", "ben", "isim", "ad"]:
        if turkce_normalize(metin.lower()).startswith(turkce_normalize(kalip)):
            metin = metin[len(kalip):].strip()
            break

    if not metin or len(metin) < 2:
        return None, "bilinmiyor"

    # 3) Ilk kelimeyi al (isim genelde tek kelime)
    parcalar = metin.strip().split()
    isim_aday = parcalar[0] if parcalar else metin

    # 4) Isim veritabaninda ara
    eslesen, skor = isim_eslestir(isim_aday)

    if eslesen and skor >= 0.8:
        # Yuksek guven - ismi duzelt
        dogru_isim = turkce_baslik(eslesen)
        print(f"[TURKCE] Isim duzeltme: '{isim_aday}' -> '{dogru_isim}' (skor: {skor:.2f})")
        return dogru_isim, "kesin"
    elif eslesen and skor >= 0.6:
        # Orta guven - tahmini duzelt
        dogru_isim = turkce_baslik(eslesen)
        print(f"[TURKCE] Isim tahmini: '{isim_aday}' -> '{dogru_isim}' (skor: {skor:.2f})")
        return dogru_isim, "tahmini"
    else:
        # Veritabaninda yok - orijinali kullan
        isim = turkce_baslik(isim_aday)
        print(f"[TURKCE] Isim bilinmiyor: '{isim_aday}' -> '{isim}' (veritabaninda yok)")
        return isim, "bilinmiyor"


def metin_turkce_mi(metin):
    """Metnin Turkce olup olmadigini kontrol et"""
    if not metin:
        return False

    metin_kucuk = metin.lower()
    turkce_kelimeler = [
        "merhaba", "nasil", "evet", "hayir", "tamam", "tesekkur",
        "lutfen", "bir", "bu", "ve", "ile", "icin", "ben", "sen",
        "biz", "var", "yok", "ne", "neden", "nerede", "kim",
        "iyi", "kotu", "guzel", "buyuk", "kucuk", "yeni", "eski",
    ]

    sayac = sum(1 for k in turkce_kelimeler if k in turkce_normalize(metin_kucuk))
    kelime_sayisi = len(metin_kucuk.split())

    if kelime_sayisi == 0:
        return False

    # En az 1 Turkce kelime varsa veya tek kelimeyse
    return sayac >= 1 or kelime_sayisi <= 2
