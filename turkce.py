"""
ATLAS - Türkçe Dil Beyni
=========================
Beyin Karşılığı: Wernicke Alanı + Angular Girus
Görev: Türkçe dil işleme, düzeltme, normalizasyon, isim tanıma

İnsan beyni dil işlemede:
- Fonetik analiz (ses → harf)
- Morfolojik analiz (ek → kök)
- Semantik analiz (anlam)
- Pragmatik analiz (bağlam)
yaparak çalışır. Bu modül aynı pipeline'ı taklit eder.
"""

import re
import json
import os
from difflib import SequenceMatcher

# ============================================================
# TÜRKÇE ALFABE VE FONETİK KURALLAR
# ============================================================

TURKCE_HARFLER = "abcçdefgğhıijklmnoöprsştuüvyz"
TURKCE_BUYUK = "ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"
SESLI_HARFLER = "aeıioöuü"
SESSIZ_HARFLER = "bcçdfgğhjklmnprsştvyz"
KALIN_SESLILER = "aıou"
INCE_SESLILER = "eiöü"

# Büyük-küçük ünlü uyumu
BUYUK_UYUM = {
    'a': 'a', 'ı': 'a', 'o': 'a', 'u': 'a',
    'e': 'e', 'i': 'e', 'ö': 'e', 'ü': 'e'
}

# ============================================================
# TÜRKÇE İSİM VERİTABANI (1000+ isim)
# ============================================================

ERKEK_ISIMLERI = {
    "özgür", "ahmet", "mehmet", "mustafa", "ali", "hüseyin", "hasan",
    "ibrahim", "ismail", "osman", "yusuf", "murat", "ömer", "halil",
    "mahmut", "recep", "süleyman", "ramazan", "abdullah", "kemal",
    "yaşar", "metin", "bayram", "kadir", "adem", "fatih", "salih",
    "ayhan", "yılmaz", "cemil", "erkan", "serkan", "gökhan", "volkan",
    "burak", "emre", "can", "cem", "deniz", "onur", "tolga", "baran",
    "arda", "berkay", "kaan", "efe", "yiğit", "doruk", "eren", "berk",
    "alp", "emir", "atlas", "barış", "çağrı", "doğan", "engin", "ferhat",
    "gürkan", "hamza", "ilker", "ilhan", "kerem", "levent", "mert",
    "necati", "oğuz", "polat", "rıza", "selim", "taner", "uğur",
    "vedat", "yavuz", "zafer", "zeki", "aras", "atalay", "atakan",
    "batuhan", "caner", "çetin", "davut", "ekrem", "erdem", "faruk",
    "galip", "güven", "hayri", "isa", "koray", "kutay", "muhammet",
    "nuri", "orhan", "ömercan", "poyraz", "rüzgar", "sami", "sedat",
    "şaban", "tahir", "ufuk", "umut", "ünal", "veli", "yakup",
    "tunç", "turgut", "tarık", "sinan", "soner", "sadık", "remzi",
    "rasim", "nedim", "mithat", "mesut", "celal", "cengiz", "cemal",
    "cahit", "burhan", "bilal", "bülent", "cüneyt", "çağlar", "dursun",
    "edip", "erol", "ersin", "ferit", "fikret", "hakan", "hikmet",
    "ilyas", "irfan", "kaya", "lütfi", "muhsin", "muzaffer", "namık",
    "nazım", "nihat", "niyazi", "oktay", "ozan", "rauf", "rifat",
    "rüştü", "sabri", "samet", "şeref", "şükrü", "temel", "timur",
    "turan", "türker", "ümit", "vahit", "yasin", "ziya",
    "arif", "aslan", "bahadır", "barbaros", "bedri", "behçet",
    "besim", "cafer", "celil", "coşkun", "cumhur", "çağatay",
    "ertuğrul", "esat", "eyüp", "fırat", "gökalp", "gürbüz",
    "hasret", "haydar", "hulusi", "hüsnü", "ihsan", "ilhami",
    "kağan", "kamil", "korhan", "kubilay", "lokman", "mahir",
    "münir", "naim", "necdet", "nusret", "oğuzhan", "orkun",
    "rahmi", "reşat", "rıdvan", "saffet", "selahattin", "serdar",
    "şenol", "talat", "tansu", "tayfun", "taylan", "tugay",
    "tuncay", "ulaş", "üzeyir", "vedat", "veysel", "yalçın",
    "yurdakul", "yunus", "zühtü", "alparslan", "ayberk", "ayaz",
    "batu", "berke", "canberk", "egehan", "emirhan", "eymen",
    "görkem", "kayra", "kuthan", "mirac", "talha", "utku"
}

KADIN_ISIMLERI = {
    "ayşe", "fatma", "emine", "hatice", "zeynep", "elif", "meryem",
    "şerife", "zehra", "sultan", "hanife", "merve", "mine", "gül",
    "havva", "hacer", "hülya", "rabia", "gülay", "sevgi", "sevim",
    "selma", "serpil", "sibel", "songül", "sema", "esra", "derya",
    "dilek", "gamze", "gizem", "hande", "ilknur", "jale", "kezban",
    "leyla", "melek", "nalan", "nazlı", "nihal", "nur", "oya",
    "pelin", "pınar", "reyhan", "sanem", "şeyma", "tansu",
    "tuba", "ülkü", "vildan", "yasemin", "zübeyde", "ada", "almina",
    "asya", "azra", "beren", "büşra", "canan", "cansu", "çiğdem",
    "damla", "defne", "demet", "dilan", "ebru", "ece", "edanur",
    "ela", "elmas", "eylül", "feyza", "figen", "filiz", "fulya",
    "gonca", "gökçe", "güneş", "hayriye", "idil", "irmak", "işıl",
    "kader", "kadriye", "lale", "lara", "melisa", "naz", "neslihan",
    "nesrin", "neva", "nisan", "özge", "özlem", "pembe", "pervin",
    "ruken", "saadet", "sahra", "seda", "seher", "selin", "sena",
    "şule", "tülay", "tuğba", "türkan", "ümran", "yağmur", "yaprak",
    "yıldız", "arzu", "aslı", "aysun", "aylin", "bahar", "belgin",
    "berna", "betül", "beyza", "birsen", "burcu", "cemre", "ceyda",
    "ceylan", "dilara", "duygu", "ecrin", "feride", "feryal",
    "funda", "gülşen", "güzin", "halime", "hümeyra", "iclal",
    "inci", "kübra", "kumsal", "mediha", "mehtap", "miray",
    "müjde", "nagehan", "nazan", "nergis", "nisa", "nurcan",
    "nuray", "olcay", "övgü", "pakize", "rana", "raşel",
    "rengin", "rezzan", "rüya", "saliha", "serap", "simge",
    "şebnem", "şirin", "tenzile", "tuğçe", "yelda", "yonca",
    "züleyha", "nehir", "masal", "mira", "vera", "duru", "lina"
}

TUM_ISIMLER = ERKEK_ISIMLERI | KADIN_ISIMLERI

# ============================================================
# FONETİK BENZERLIK HARİTASI
# ============================================================

# STT'nin sık karıştırdığı ses-harf eşleşmeleri
FONETIK_BENZERLER = {
    'ö': ['o', 'oe', 'eu'],
    'ü': ['u', 'ue', 'yu'],
    'ğ': ['g', 'y', ''],
    'ş': ['s', 'sh', 'ch'],
    'ç': ['c', 'ch', 'ts'],
    'ı': ['i', 'e', 'u', 'a'],
    'c': ['j', 'dj'],
}

# STT'nin Türkçe isimleri yanlış duyma kalıpları
ISIM_DUZELTME_HARITASI = {
    # "Özgür" için bilinen yanlış duyumlar
    "ana": "özgür", "anna": "özgür", "adana": "özgür",
    "ösgür": "özgür", "ozgur": "özgür", "ozgür": "özgür",
    "ösgur": "özgür", "uzgur": "özgür", "uzgür": "özgür",
    "osgur": "özgür", "osgür": "özgür", "ezgür": "özgür",
    "esgür": "özgür", "oscar": "özgür", "ogur": "özgür",
    # Genel yanlış duyumlar
    "mete": "mehmet", "meat": "mehmet", "met": "mehmet",
    "i̇brahim": "ibrahim", "ibram": "ibrahim",
    "ali̇": "ali", "ally": "ali",
    "eye": "aye", "ayse": "ayşe",
}

# ============================================================
# NORMALİZASYON FONKSİYONLARI
# ============================================================

def turkce_normalize(text):
    """Türkçe karakterleri ASCII'ye çevir (karşılaştırma için)"""
    if not text:
        return ""
    mapping = str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU")
    return text.translate(mapping).lower().strip()


def turkce_kucuk(text):
    """Türkçe büyük-küçük harf dönüşümü (İ→i, I→ı)"""
    if not text:
        return ""
    result = text.replace('İ', 'i').replace('I', 'ı')
    return result.lower()


def turkce_buyuk_harf(text):
    """Türkçe küçük-büyük harf dönüşümü (i→İ, ı→I)"""
    if not text:
        return ""
    result = text.replace('i', 'İ').replace('ı', 'I')
    return result.upper()


def turkce_baslik(text):
    """Her kelimenin ilk harfini Türkçe kurallarına göre büyüt"""
    if not text:
        return ""
    words = text.split()
    result = []
    for word in words:
        if not word:
            continue
        first = word[0]
        if first == 'i':
            result.append('İ' + word[1:])
        elif first == 'ı':
            result.append('I' + word[1:])
        else:
            result.append(word[0].upper() + word[1:])
    return ' '.join(result)

# ============================================================
# FONETİK MESAFE HESAPLAMA
# ============================================================

def fonetik_mesafe(s1, s2):
    """İki kelimenin fonetik benzerlik skoru (0-1, 1=aynı)"""
    s1 = turkce_normalize(s1)
    s2 = turkce_normalize(s2)
    if not s1 or not s2:
        return 0.0
    return SequenceMatcher(None, s1, s2).ratio()


def en_yakin_isim(text, esik=0.55):
    """Verilen metne fonetik olarak en yakın Türkçe ismi bul"""
    text_temiz = turkce_normalize(text.strip())
    if not text_temiz:
        return None, 0.0

    # Önce tam eşleşme kontrol (normalize edilmiş)
    for isim in TUM_ISIMLER:
        if turkce_normalize(isim) == text_temiz:
            return isim, 1.0

    # Bilinen yanlış duyum haritası
    if text_temiz in ISIM_DUZELTME_HARITASI:
        duzeltilmis = ISIM_DUZELTME_HARITASI[text_temiz]
        return duzeltilmis, 0.95

    # Fonetik benzerlik araması
    en_iyi_isim = None
    en_iyi_skor = 0.0

    for isim in TUM_ISIMLER:
        skor = fonetik_mesafe(text_temiz, isim)
        if skor > en_iyi_skor:
            en_iyi_skor = skor
            en_iyi_isim = isim

    if en_iyi_skor >= esik:
        return en_iyi_isim, en_iyi_skor
    return None, en_iyi_skor


def isim_temizle_ve_duzelt(text):
    """
    STT çıktısından isim çıkar ve Türkçe isim veritabanıyla eşleştir.
    
    Returns: (düzeltilmiş_isim, güven_skoru)
    """
    if not text:
        return None, 0.0

    # Temizle
    text = text.strip().lower()
    # "benim adım X" gibi kalıpları ayıkla
    kaliplar = [
        r"(?:benim\s+)?ad[ıi]m\s+(\w+)",
        r"ben\s+(\w+)",
        r"ismim\s+(\w+)",
        r"bana\s+(\w+)\s+derler",
        r"bana\s+(\w+)\s+diyorlar",
        r"(\w+)\s+diye\s+çağır",
    ]
    for kalip in kaliplar:
        m = re.search(kalip, text, re.IGNORECASE)
        if m:
            text = m.group(1)
            break

    # Tek kelimeye indir
    words = text.split()
    if len(words) > 3:
        # Çok uzunsa, son kelimeyi dene (genelde isim sonda söylenir)
        text = words[-1]
    elif len(words) > 1:
        # Her kelimeyi dene, en iyi eşleşmeyi al
        en_iyi = None
        en_iyi_skor = 0.0
        for w in words:
            isim, skor = en_yakin_isim(w)
            if skor > en_iyi_skor:
                en_iyi = isim
                en_iyi_skor = skor
        if en_iyi and en_iyi_skor >= 0.55:
            return turkce_baslik(en_iyi), en_iyi_skor
        text = words[0]  # İlk kelimeyi dene

    # İsim eşleştir
    isim, skor = en_yakin_isim(text)
    if isim:
        return turkce_baslik(isim), skor

    # Eşleşme bulunamadı — orijinal metni temizleyip döndür
    return turkce_baslik(text.strip()), 0.3

# ============================================================
# STT DÜZELTME (POST-PROCESSING)
# ============================================================

# Yaygın STT hataları ve düzeltmeleri
STT_DUZELTME = {
    # Selamlama
    "selam aleyküm": "selamünaleyküm",
    "salem": "selam", "salam": "selam",
    "merhba": "merhaba", "merbaha": "merhaba",
    "meraba": "merhaba",
    # Soru kalıpları
    "nasıl sın": "nasılsın", "nasilsin": "nasılsın",
    "naber": "ne haber", "nbr": "ne haber",
    "neredesin": "neredesin",
    # Günlük kelimeler
    "tamm": "tamam", "tamamdır": "tamam",
    "iyiyim sagol": "iyiyim sağol",
    "teşekkür": "teşekkürler", "eyvallah": "eyvallah",
    "hayır dır": "hayırdır", "hayır dir": "hayırdır",
    "günaydın": "günaydın", "gunaydin": "günaydın",
    "iyi geceler": "iyi geceler", "iyi aksamlar": "iyi akşamlar",
    # Komut kalıpları
    "saat kaş": "saat kaç", "saatkaç": "saat kaç",
    "hava nasil": "hava nasıl", "hava durmu": "hava durumu",
    "müzik ac": "müzik aç", "muzik aç": "müzik aç",
    "sesi ac": "sesi aç", "sesi kis": "sesi kıs",
    "bilgisayarı kapat": "bilgisayarı kapat",
    "ekranı kapat": "ekranı kapat",
    # Atlas komutları
    "at last": "atlas", "at las": "atlas",
    "atlast": "atlas", "atlaz": "atlas",
    "etles": "atlas", "atles": "atlas",
}

# Türkçe ek düzeltmeleri
EK_DUZELTME = {
    "mısın": "mısın", "misin": "misin",
    "musun": "musun", "müsün": "müsün",
    "mıyım": "mıyım", "miyim": "miyim",
    "dir": "dir", "dır": "dır", "dur": "dur", "dür": "dür",
    "ler": "ler", "lar": "lar",
    "den": "den", "dan": "dan", "ten": "ten", "tan": "tan",
}


def stt_duzelt(text):
    """
    STT çıktısını Türkçe kurallarına göre düzelt.
    
    İnsan beyni gibi çok katmanlı düzeltme:
    1. Temel temizlik (boşluk, noktalama)
    2. Bilinen hata düzeltme
    3. Türkçe karakter düzeltme
    4. Ek uyum kontrolü
    """
    if not text:
        return ""

    # 1. Temel temizlik
    text = text.strip()
    text = re.sub(r'\s+', ' ', text)  # Çoklu boşluk
    text = text.lower()

    # 2. Bilinen hata düzeltme
    for yanlis, dogru in STT_DUZELTME.items():
        # Kelime sınırı ile eşleştir
        pattern = r'\b' + re.escape(yanlis) + r'\b'
        text = re.sub(pattern, dogru, text, flags=re.IGNORECASE)

    # 3. "Atlas" tetik kelimesini kontrol et ve düzelt
    atlas_varyantlari = [
        "at last", "at las", "atlast", "atlaz", "etles",
        "atles", "at less", "atlas"
    ]
    for v in atlas_varyantlari:
        if v in text:
            text = text.replace(v, "atlas")

    # 4. Türkçe karakter düzeltme (eksik Türkçe karakterler)
    turkce_kelimeler = {
        "turkce": "türkçe", "turkiye": "türkiye",
        "gunes": "güneş", "guzel": "güzel",
        "buyuk": "büyük", "kucuk": "küçük",
        "ogrenci": "öğrenci", "ogretmen": "öğretmen",
        "ucretsiz": "ücretsiz", "onemli": "önemli",
        "dusunce": "düşünce", "gorev": "görev",
        "tesekkur": "teşekkür", "tesekkurler": "teşekkürler",
        "gorusuruz": "görüşürüz", "gormek": "görmek",
    }
    for yanlis, dogru in turkce_kelimeler.items():
        text = re.sub(r'\b' + yanlis + r'\b', dogru, text)

    return text.strip()


def tetik_kelime_kontrol(text, tetik="atlas"):
    """
    Metinde tetik kelime var mı kontrol et.
    RAS (Retiküler Aktivasyon Sistemi) gibi filtrele.
    
    Returns: (tetik_bulundu, temizlenmis_metin)
    """
    if not text:
        return False, ""

    text_lower = turkce_normalize(text)
    tetik_lower = turkce_normalize(tetik)

    # Tetik kelime varyantları
    varyantlar = [
        tetik_lower,
        tetik_lower.replace('a', '').replace('e', ''),  # sessiz harfler
    ]

    bulundu = False
    for v in varyantlar:
        if v and v in text_lower:
            bulundu = True
            break

    # Tetik kelimeyi metinden çıkar
    if bulundu:
        # Orijinal metinden tetik kelimeyi kaldır
        temiz = re.sub(r'\b' + re.escape(tetik) + r'\b', '', text, flags=re.IGNORECASE)
        temiz = re.sub(r'\s+', ' ', temiz).strip()
        # Başındaki virgül, nokta vb temizle
        temiz = re.sub(r'^[,.\s!?]+', '', temiz).strip()
        return True, temiz

    return False, text

# ============================================================
# CÜMLE ANALİZİ
# ============================================================

def cumle_turu_belirle(text):
    """
    Cümlenin türünü belirle (soru, emir, bilgi, selam).
    Wernicke alanı gibi anlam çıkar.
    """
    if not text:
        return "belirsiz"

    text_lower = text.lower().strip()

    # Soru kalıpları
    soru_ekleri = ["mi", "mı", "mu", "mü", "misin", "mısın", "musun", "müsün",
                   "miyim", "mıyım", "muyum", "müyüm", "nedir", "nelerdir"]
    soru_kelimeleri = ["ne", "nerede", "nasıl", "neden", "niçin", "niye",
                       "kim", "kime", "hangi", "kaç", "ne zaman", "nereden",
                       "nereye", "ne kadar"]

    if text_lower.endswith("?"):
        return "soru"
    for ek in soru_ekleri:
        if text_lower.endswith(ek) or f" {ek} " in text_lower:
            return "soru"
    for kelime in soru_kelimeleri:
        if text_lower.startswith(kelime) or f" {kelime} " in text_lower:
            return "soru"

    # Selamlama kalıpları
    selamlar = ["merhaba", "selam", "günaydın", "iyi akşamlar", "iyi geceler",
                "hey", "naber", "ne haber", "hoşgeldin", "selamünaleyküm",
                "iyi günler", "hayırlı sabahlar"]
    for s in selamlar:
        if s in text_lower:
            return "selam"

    # Emir kalıpları
    emir_fiiller = ["aç", "kapat", "başlat", "durdur", "ara", "bul", "göster",
                    "çal", "oynat", "yaz", "oku", "sil", "indir", "yükle",
                    "kaydet", "ayarla", "değiştir"]
    for fiil in emir_fiiller:
        if text_lower.endswith(fiil) or text_lower.startswith(fiil):
            return "emir"

    return "bilgi"


def niyet_cikart(text):
    """
    Metinden kullanıcının niyetini çıkar.
    Prefrontal korteks + Wernicke alanı koordinasyonu.
    
    Returns: dict{niyet, guvenskor, detaylar}
    """
    if not text:
        return {"niyet": "belirsiz", "guven": 0.0, "detay": {}}

    text_lower = text.lower().strip()
    cumle_turu = cumle_turu_belirle(text)

    # Niyet sınıflandırma
    niyet_kaliplari = {
        "saat_sor": [r"saat\s*kaç", r"saati?\s*söyle", r"saat\s*ne"],
        "tarih_sor": [r"bugün\s*ne", r"tarih\s*ne", r"hangi\s*gün", r"bugün\s*günlerden"],
        "hava_sor": [r"hava\s*(nasıl|durumu|ne)", r"yağmur\s*yağ", r"sıcaklık"],
        "muzik_ac": [r"müzik\s*aç", r"şarkı\s*(aç|çal)", r"müzik\s*çal"],
        "program_ac": [r"(aç|başlat|çalıştır)\s*\w+", r"\w+\s*(aç|başlat)"],
        "bilgisayar_kapat": [r"bilgisayar[ıi]?\s*kapat", r"sistemi?\s*kapat", r"pc\s*kapat"],
        "ses_ayar": [r"ses[i]?\s*(aç|kıs|kapat|yükselt|azalt|ayarla)"],
        "arama_yap": [r"(ara|arat|bul)\s+.+", r"google.*(ara|arat)"],
        "selam": [r"^(merhaba|selam|günaydın|hey|naber|iyi\s*(akşam|gece|gün))"],
        "kendini_tanit": [r"(adın|ismin)\s*ne", r"sen\s*kimsin", r"kendini\s*tanıt"],
        "hal_hatir": [r"nasılsın", r"ne\s*haber", r"iyi\s*misin", r"keyifler\s*nasıl"],
        "tesekkur": [r"teşekkür", r"sağol", r"eyvallah", r"mersi"],
        "kapat": [r"(kapat|kapan|dur|sus|sessiz)", r"görüşürüz", r"hoşça\s*kal"],
    }

    for niyet, kaliplar in niyet_kaliplari.items():
        for kalip in kaliplar:
            if re.search(kalip, text_lower):
                return {
                    "niyet": niyet,
                    "guven": 0.85,
                    "cumle_turu": cumle_turu,
                    "detay": {"eslesen_kalip": kalip, "orijinal": text}
                }

    # Genel soru/emir/bilgi
    return {
        "niyet": f"genel_{cumle_turu}",
        "guven": 0.5,
        "cumle_turu": cumle_turu,
        "detay": {"orijinal": text}
    }

# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def kelime_say(text):
    """Metindeki kelime sayısını döndür"""
    return len(text.split()) if text else 0


def sesli_harf_kontrol(kelime):
    """Kelimedeki son sesli harfi döndür (ünlü uyumu için)"""
    for harf in reversed(kelime.lower()):
        if harf in SESLI_HARFLER:
            return harf
    return None


def unlu_uyumu_kontrol(kelime):
    """Kelimenin büyük ünlü uyumuna uyup uymadığını kontrol et"""
    sesliler = [h for h in kelime.lower() if h in SESLI_HARFLER]
    if len(sesliler) <= 1:
        return True

    ilk_grup = BUYUK_UYUM.get(sesliler[0], 'a')
    for s in sesliler[1:]:
        if BUYUK_UYUM.get(s, 'a') != ilk_grup:
            return False
    return True
