"""
ATLAS - Bilgi Bankası (Kişisel Gelişim & Genel Kültür)
======================================================
Beyin Karşılığı: Temporal Lob + Neokorteks
Görev: Zengin bilgi deposu — özellikle kişisel gelişim, iletişim, insan anlama

İnsan beyni bilgiyi kategoriler halinde depolar.
Bu modül ATLAS'a geniş bir bilgi tabanı kazandırır.
Kullanıcı soru sorduğunda AI'a ek bağlam sağlar.
"""

import re
import json
import os
import logging
import random
from datetime import datetime

logger = logging.getLogger("ATLAS.bilgi")


# ============================================================
# KİŞİSEL GELİŞİM BİLGİ BANKASI
# ============================================================

KISISEL_GELISIM = {
    "insanlari_anlama": {
        "baslik": "İnsanları Doğru Anlama",
        "icerik": [
            "İnsanları anlamanın temeli empatidir. Kendini karşındakinin yerine koy.",
            "Aktif dinleme: Karşındaki konuşurken söyleyeceğin şeyi düşünme, onu dinle.",
            "İnsanların söyledikleri ile demek istedikleri farklı olabilir. Ses tonu ve beden diline dikkat et.",
            "Herkes farklı bir geçmişten gelir. Yargılamadan önce anlamaya çalış.",
            "İnsanlar genellikle anlaşılmak ister. Bazen çözüm değil, sadece dinlenme isterler.",
            "Birine 'Seni anlıyorum' demek yerine, gerçekten anladığını göster. Duyduklarını özetle.",
            "İnsanların davranışlarının altında her zaman bir ihtiyaç vardır. O ihtiyacı bul.",
            "Sabırlı ol. Herkes düşüncelerini aynı hızda ifade edemez.",
        ],
    },
    "etkili_iletisim": {
        "baslik": "Etkili İletişim Teknikleri",
        "icerik": [
            "İletişimin yüzde 55'i beden dili, yüzde 38'i ses tonu, sadece yüzde 7'si kelimelerdir.",
            "Ben dili kullan: 'Sen hep yapıyorsun' yerine 'Ben bunu yaşadığımda üzülüyorum' de.",
            "Açık uçlu sorular sor: 'Evet/Hayır' yerine 'Bu konuda ne düşünüyorsun?' gibi.",
            "Geri bildirim verirken sandviç tekniği: Olumlu şey, geliştirilecek şey, olumlu şey.",
            "Karşındakini dinlerken göz teması kur ama baskı hissettirme.",
            "Empati kurarken 'Anlıyorum, bu zor olmalı' gibi doğrulayıcı ifadeler kullan.",
            "İletişimde sessizlik de güçlüdür. Her boşluğu doldurmak zorunda değilsin.",
            "Eleştiri yaparken davranışı eleştir, kişiyi değil. 'Sen tembelsin' değil, 'Bu iş geç kaldı' de.",
            "Karşındaki kızgınken savunmaya geçme. Önce duygusunu kabul et, sonra konuş.",
            "İyi iletişimci olmak için önce iyi bir dinleyici ol.",
        ],
    },
    "duygusal_zeka": {
        "baslik": "Duygusal Zeka (EQ)",
        "icerik": [
            "Duygusal zeka 5 bileşenden oluşur: Öz farkındalık, öz düzenleme, motivasyon, empati, sosyal beceriler.",
            "Öz farkındalık: Duygularını tanı. 'Şu an ne hissediyorum?' diye sor kendine.",
            "Öz düzenleme: Duyguların seni yönetmesin, sen duygularını yönet.",
            "Kızgınlık hissedince 10'a kadar say. Bu basit teknik beynine düşünme zamanı verir.",
            "Başkalarının duygularını okumak için yüz ifadelerine ve ses tonuna dikkat et.",
            "Duygusal zekası yüksek insanlar hem kendilerini hem başkalarını daha iyi anlar.",
            "Stresli anlarda derin nefes al. 4 saniye nefes al, 4 saniye tut, 4 saniye ver.",
            "Duygularını günlüğe yaz. Bu öz farkındalığı artırır.",
            "Empati kurabilmek için kendi duygularınla barışık olmalısın.",
            "Hata yaptığında kendine kızma, hatadan öğren. Bu da duygusal zekanın bir parçası.",
        ],
    },
    "beden_dili": {
        "baslik": "Beden Dili Okuma",
        "icerik": [
            "Kollarını kavuşturan biri savunmada veya kapalı hissediyor olabilir.",
            "Göz teması güven gösterir. Ama aşırısı tehdit olarak algılanır.",
            "Gerçek gülümseme gözleri de içerir. Sahte gülümsemede sadece dudaklar hareket eder.",
            "Ayaklar gerçeği söyler. Ayakları kapıya dönükse gitmek istiyor olabilir.",
            "Ellerini ovuşturan biri heyecanlı veya tedirgin olabilir — bağlama bak.",
            "Başını hafifçe eğen biri seni dinlediğini gösterir.",
            "Birisi yalan söylerken genelde doğal olmayan hareketler yapar: burnunu dokunma, gözlerini kaçırma.",
            "Ayna tekniği: Karşındakinin duruşunu bilinçsizce taklit ediyorsan uyum içindesiniz.",
            "Güçlü duruş: Omuzları açık, dik durmak hem sana hem karşına güven verir.",
            "Beden dili tek başına yeterli değil. Her zaman bağlamla birlikte oku.",
        ],
    },
    "motivasyon": {
        "baslik": "Motivasyon ve Hedef Belirleme",
        "icerik": [
            "Büyük hedefleri küçük adımlara böl. Her gün bir adım bile ilerleme demektir.",
            "SMART hedefler koy: Spesifik, Ölçülebilir, Ulaşılabilir, İlgili, Zamanlı.",
            "Motivasyon geçicidir, disiplin kalıcıdır. Disiplin kas gibidir, çalıştıkça güçlenir.",
            "Neden'ini bil. Bir işi neden yaptığını bilirsen nasıl yapacağını bulursun.",
            "Başarısızlık son değil, geri bildirimdir. Edison ampulü bulana kadar bin kez başarısız oldu.",
            "Kendini başarılı insanlarla karşılaştırma. Dünkü kendinle karşılaştır.",
            "Her sabah 3 şey yaz: Bugün başaracağım 3 şey. Akşam kontrol et.",
            "Ödül sistemi kur. Küçük başarıları kutla, beynin dopamin salgılar ve devam etmek ister.",
            "Erteleme düşmanıdır. '5 dakika kuralı' uygula: Sadece 5 dakika başla, genelde devam edersin.",
            "Vizyon panosu oluştur. Hedeflerini görselleştirmek motivasyonu artırır.",
        ],
    },
    "zaman_yonetimi": {
        "baslik": "Zaman Yönetimi",
        "icerik": [
            "Eisenhower Matrisi: İşleri acil-önemli, acil-önemsiz, önemli-acil değil, önemsiz-acil değil olarak sınıfla.",
            "Pomodoro tekniği: 25 dakika çalış, 5 dakika mola ver. 4 turun sonunda 15 dakika uzun mola.",
            "Sabahları en zor işi yap. Willpower sabahları en yüksektir.",
            "Hayır demeyi öğren. Her evet, başka bir şeye hayır demektir.",
            "Multitasking verimli değildir. Tek işe odaklan, bitir, sonrakine geç.",
            "Parkinson kanunu: Bir iş, kendisine ayrılan sürenin tamamını dolduracak şekilde genişler. Sıkı deadline koy.",
            "2 dakika kuralı: 2 dakikadan kısa sürecek işi hemen yap, erteleme.",
            "Haftanın başında haftalık plan yap. Günlük planları önceki gece hazırla.",
            "Enerjini yönet, sadece zamanını değil. Enerji düşükken kolay işler yap.",
            "Dijital detoks yap. Telefon bildirimleri en büyük zaman hırsızıdır.",
        ],
    },
    "stres_yonetimi": {
        "baslik": "Stres Yönetimi",
        "icerik": [
            "Stres tamamen kötü değildir. Kontrollü stres performansı artırır.",
            "4-7-8 nefes tekniği: 4 saniye nefes al, 7 saniye tut, 8 saniye ver. Hemen sakinleştirir.",
            "Egzersiz en iyi doğal antidepresandır. Günde 30 dakika yürüyüş bile yeter.",
            "Kontrolün dışındaki şeyler için endişelenme. Kontrol edebildiklerin için harekete geç.",
            "Doğada vakit geçirmek kortizol seviyesini düşürür. Haftada en az bir doğa yürüyüşü yap.",
            "Uyku kalitesi her şeyin temeli. 7-8 saat uyumaya çalış.",
            "Müzik dinlemek stresi azaltır. Özellikle 60 BPM tempodaki müzikler rahatlatıcıdır.",
            "Kafandaki düşünceleri kağıda dök. Yazmak zihni rahatlatır.",
            "Sosyal destek önemli. Güvendiğin birisiyle konuş.",
            "Minnet duygusu strese iyi gelir. Her gün 3 şükür sebebi yaz.",
        ],
    },
    "ikna_ve_etkileme": {
        "baslik": "İkna ve Etkileme Sanatı",
        "icerik": [
            "Karşılıklılık ilkesi: Birine iyilik yap, doğal olarak karşılık vermek ister.",
            "Sosyal kanıt: İnsanlar başkalarının yaptığını yapmaya meyillidir. 'Herkes bunu tercih ediyor' güçlü bir argümandır.",
            "Otoriteye saygı: Konunda uzman olduğunu göster, insanlar sana güvensin.",
            "Azlık ilkesi: Bir şey az bulunursa değeri artar. 'Son fırsat' güçlü bir ikna aracıdır.",
            "Tutarlılık: İnsanlar daha önce söyledikleriyle tutarlı olmak ister. Küçük bir evet büyük evete yol açar.",
            "Empati kurarak ikna et. Karşındakinin ihtiyacını anla, çözümünü ona göre sun.",
            "Hikaye anlat. İnsanlar istatistiklerden çok hikayelere tepki verir.",
            "Önce dinle, sonra konuş. Karşındaki anlaşıldığını hissedince sana açılır.",
            "Beden dilini kullan. Güvenli duruş ve göz teması ikna gücünü artırır.",
            "Asla baskı yapma. İnsanlar zorlama hissedince kaçar. Seçim hissi ver.",
        ],
    },
    "ozsaygı_guveni": {
        "baslik": "Özsaygı ve Özgüven",
        "icerik": [
            "Özgüven bir kas gibidir. Küçük başarılarla gelişir.",
            "Kendine olumlu konuş. İç sesin en çok duyduğun sestir.",
            "Hata yapmak insanlıktır. Kendini affetmeyi öğren.",
            "Başkalarının seni nasıl gördüğü senin sorumluluğun değil. Kendi değerini kendin bil.",
            "Konfor alanından çık. Her yeni deneyim özgüveni artırır.",
            "Bedenine dikkat et. Düzgün duruş ve bakım özgüveni etkiler.",
            "Kıyaslamayı bırak. Herkesin yolculuğu farklıdır.",
            "Başarılarını kaydet. Küçük de olsa her başarı önemlidir.",
            "Hayır demeyi öğren. Sınırlarını korumak özsaygının temelidir.",
            "Yeni beceriler öğren. Bir şeyde iyi olmak özgüveni doğrudan artırır.",
        ],
    },
    "liderlik": {
        "baslik": "Liderlik Becerileri",
        "icerik": [
            "Liderlik pozisyon değil, davranıştır. Herkes bulunduğu yerde lider olabilir.",
            "İyi lider dinler. Ekibinin sesini duymak en önemli liderlik becerisidir.",
            "Örnek ol. Sözlerinle değil, davranışlarınla liderlik et.",
            "Başarıyı paylaş, hatayı sahiplen. Bu güven inşa eder.",
            "Vizyonunu paylaş. İnsanlar nereye gittiklerini bilmek ister.",
            "Delegasyon yap. Her şeyi kendin yapmaya çalışma, güven ve sorumluluk ver.",
            "Geri bildirim ver ve al. Gelişim geri bildirimle gelir.",
            "Kriz anında sakin kal. Lider panik yaparsa herkes panik yapar.",
            "Empatik ol ama kararlı ol. Duygusal zeka güçlü liderlik için şarttır.",
            "Sürekli öğren. İyi liderler hayat boyu öğrencidir.",
        ],
    },
}

# ============================================================
# HIZLI BİLGİ KALIPLARI (Kalıp motoruna eklenecek)
# ============================================================

BILGI_KALIPLARI = {
    # Kişisel gelişim soruları
    r"(?:insanları?|karşımdaki(?:ni)?|birini)\s*(?:nasıl)?\s*(?:anla[rmy]|anlamak)": "insanlari_anlama",
    r"(?:etkili|iyi|doğru)\s*(?:iletişim|konuşma|anlatma)": "etkili_iletisim",
    r"(?:duygusal|emotional)\s*(?:zeka|zekanın|eq)": "duygusal_zeka",
    r"(?:beden\s*dili|vücut\s*dili|jest|mimik)": "beden_dili",
    r"(?:motivasyon|motive|hedef\s*belirle)": "motivasyon",
    r"(?:zaman\s*yönetimi|vakit|zamanı?\s*(?:nasıl|iyi)\s*kullan)": "zaman_yonetimi",
    r"(?:stres|gerginlik|kaygı|endişe)\s*(?:yönetimi|azalt|ile\s*başa\s*çık)": "stres_yonetimi",
    r"(?:ikna|etkileme|insanları?\s*ikna)": "ikna_ve_etkileme",
    r"(?:özsaygı|özgüven|kendime?\s*güven)": "ozsaygı_guveni",
    r"(?:liderlik|lider\s*olmak|yöneticilik)": "liderlik",
    r"(?:kişisel\s*gelişim|kendimi?\s*geliştir)": None,  # Genel — tüm kategoriler
}


class BilgiBankasi:
    """
    Temporal Lob Bilgi Deposu.
    Yerleşik bilgi + kullanıcıdan öğrenilen bilgi.
    AI'a zengin bağlam sağlar.
    """

    def __init__(self, dizin="hafiza/bilgi_bankasi"):
        self._dizin = dizin
        os.makedirs(dizin, exist_ok=True)

        self._ozel_dosya = os.path.join(dizin, "kullanici_bilgileri.json")
        self._ozel_bilgiler = self._yukle(self._ozel_dosya, {})

        # Yerleşik bilgiler
        self._yerlesik = KISISEL_GELISIM

        logger.info(f"Bilgi bankası hazır: {len(self._yerlesik)} yerleşik kategori, "
                     f"{len(self._ozel_bilgiler)} özel bilgi")

    def _yukle(self, dosya, varsayilan):
        try:
            if os.path.exists(dosya):
                with open(dosya, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception:
            pass
        return varsayilan

    def _kaydet(self):
        try:
            with open(self._ozel_dosya, 'w', encoding='utf-8') as f:
                json.dump(self._ozel_bilgiler, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Bilgi bankası kayıt hatası: {e}")

    # ============================================================
    # BİLGİ SORGULAMA
    # ============================================================

    def konu_bul(self, metin):
        """
        Metinden ilgili kişisel gelişim konusunu bul.
        Returns: kategori_adi veya None
        """
        metin_lower = metin.lower().strip()

        for kalip, kategori in BILGI_KALIPLARI.items():
            if re.search(kalip, metin_lower):
                return kategori  # None dönerse = genel kişisel gelişim
        return None

    def bilgi_getir(self, kategori, sayi=3):
        """
        Bir kategoriden rastgele bilgi getir.
        Returns: list[str]
        """
        if not kategori:
            # Genel — her kategoriden birer tane
            sonuc = []
            for kat, veri in self._yerlesik.items():
                sonuc.append(random.choice(veri["icerik"]))
                if len(sonuc) >= sayi:
                    break
            return sonuc

        veri = self._yerlesik.get(kategori)
        if not veri:
            return []

        icerikler = veri["icerik"]
        if len(icerikler) <= sayi:
            return list(icerikler)
        return random.sample(icerikler, sayi)

    def kategori_bilgisi(self, kategori):
        """Bir kategorinin başlığını ve tüm içeriğini döndür"""
        veri = self._yerlesik.get(kategori)
        if veri:
            return veri
        return None

    def tum_kategoriler(self):
        """Tüm bilgi kategorilerini listele"""
        return {k: v["baslik"] for k, v in self._yerlesik.items()}

    # ============================================================
    # AI BAĞLAM ENRİCHMENT
    # ============================================================

    def ai_baglam_olustur(self, metin):
        """
        Kullanıcının sorusuna göre AI'a ek bilgi bağlamı oluştur.
        Returns: str veya None
        """
        kategori = self.konu_bul(metin)

        if kategori is False:
            return None  # Kişisel gelişim sorusu değil

        if kategori is None:
            # Genel kişisel gelişim sorusu — seçkin bilgiler ekle
            bilgiler = self.bilgi_getir(None, 4)
            if bilgiler:
                return (
                    "Kişisel gelişim bilgi bankasından:\n" +
                    "\n".join(f"- {b}" for b in bilgiler)
                )
            return None

        # Spesifik kategori
        veri = self._yerlesik.get(kategori)
        if not veri:
            return None

        bilgiler = self.bilgi_getir(kategori, 5)
        return (
            f"{veri['baslik']} hakkında bilgiler:\n" +
            "\n".join(f"- {b}" for b in bilgiler)
        )

    # ============================================================
    # ÖĞRENME — Konuşmalardan yeni bilgi ekle
    # ============================================================

    def bilgi_ekle(self, kategori, bilgi_metni):
        """Yeni bir bilgi ekle (konuşmadan öğrenilen)"""
        if kategori not in self._ozel_bilgiler:
            self._ozel_bilgiler[kategori] = []

        # Tekrar kontrolü
        for mevcut in self._ozel_bilgiler[kategori]:
            if isinstance(mevcut, str) and bilgi_metni.lower() in mevcut.lower():
                return False

        self._ozel_bilgiler[kategori].append({
            "metin": bilgi_metni,
            "tarih": datetime.now().isoformat(),
            "kaynak": "konusma"
        })

        # Son 100 bilgi tut
        self._ozel_bilgiler[kategori] = self._ozel_bilgiler[kategori][-100:]
        self._kaydet()

        logger.info(f"Yeni bilgi öğrenildi [{kategori}]: {bilgi_metni[:50]}")
        return True

    def ozel_bilgi_getir(self, kategori, sayi=3):
        """Konuşmalardan öğrenilmiş bilgileri getir"""
        bilgiler = self._ozel_bilgiler.get(kategori, [])
        if not bilgiler:
            return []

        metinler = []
        for b in bilgiler[-sayi:]:
            if isinstance(b, dict):
                metinler.append(b.get("metin", ""))
            elif isinstance(b, str):
                metinler.append(b)
        return metinler
