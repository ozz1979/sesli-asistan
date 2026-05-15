"""
ATLAS — Gemini AI Bağlantı Teşhis Aracı
Bu dosyayı çalıştırarak Gemini bağlantınızı test edin.
"""
import sys
import os
import json
import traceback

print("=" * 60)
print("  ATLAS — Gemini AI Bağlantı Teşhis Aracı v2")
print("=" * 60)
print()

hatalar = []

# ──────── 1. Python sürümü ────────
print(f"[1/7] Python: {sys.version}")
print(f"       Yol: {sys.executable}")
print()

# ──────── 2. Config dosyası ────────
print("[2/7] config.json kontrol ediliyor...")
api_key = ""
model = ""
try:
    cfg_yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(cfg_yol, "r", encoding="utf-8") as f:
        raw = f.read()
    print(f"  Dosya boyutu: {len(raw)} byte")
    config = json.loads(raw)
    ai = config.get("ai", {})
    api_key = ai.get("gemini_api_key", "")
    model = ai.get("gemini_model", "gemini-2.0-flash")
    yedek_model = ai.get("gemini_yedek_model", "gemini-1.5-flash")
    timeout = ai.get("timeout", 8)

    if api_key:
        masked = api_key[:6] + "..." + api_key[-4:] if len(api_key) > 10 else "***"
        print(f"  API Key: {masked} ({len(api_key)} karakter)")
    else:
        print("  API Key: BOS!")
        hatalar.append("API key config.json'da bos")
    print(f"  Model: {model}")
    print(f"  Yedek: {yedek_model}")
except FileNotFoundError:
    print("  config.json bulunamadi!")
    hatalar.append("config.json yok")
except json.JSONDecodeError as e:
    print(f"  config.json gecersiz JSON! Satir: {e.lineno}")
    hatalar.append(f"config.json JSON hatasi")
print()

# ──────── 3. Paket kontrolü ────────
print("[3/7] Gemini paketi kontrol ediliyor...")
yeni_sdk = False
eski_sdk = False
genai = None

# Önce yeni SDK dene
try:
    from google import genai
    yeni_sdk = True
    print(f"  YENI SDK yuklu: google-genai")
    try:
        print(f"  Surum: {genai.__version__}")
    except:
        pass
except ImportError:
    pass

# Yeni yoksa eski SDK kontrol
if not yeni_sdk:
    try:
        import google.generativeai as genai_eski
        eski_sdk = True
        print(f"  ESKI SDK yuklu: google-generativeai v{getattr(genai_eski, '__version__', '?')}")
        print("  UYARI: Bu paket artik desteklenmiyor!")
        print("  Cozum: pip install google-genai")
        hatalar.append("Eski SDK kullaniliyor (google-generativeai)")
    except ImportError:
        print("  HATA: Hicbir Gemini paketi kurulu degil!")
        print("  Cozum: pip install google-genai")
        hatalar.append("Gemini paketi yok")
print()

# ──────── 4. İnternet bağlantısı ────────
print("[4/7] Internet baglantisi test ediliyor...")
internet_ok = False
try:
    import urllib.request
    urllib.request.urlopen("https://www.google.com", timeout=10)
    print("  Internet baglantisi var")
    internet_ok = True
except Exception as e:
    print(f"  Internet baglantisi yok: {e}")
    hatalar.append("Internet baglantisi yok")
print()

# ──────── 5. Client oluşturma ────────
print("[5/7] Gemini client olusturuluyor...")
client = None

if not api_key:
    print("  Atlandi (API key yok)")
elif yeni_sdk:
    try:
        client = genai.Client(api_key=api_key)
        print(f"  Client olusturuldu (yeni SDK)")
    except Exception as e:
        print(f"  Client olusturma hatasi: {e}")
        hatalar.append(f"Client hatasi: {e}")
elif eski_sdk:
    try:
        genai_eski.configure(api_key=api_key)
        client = genai_eski.GenerativeModel(model)
        print(f"  Client olusturuldu (eski SDK)")
    except Exception as e:
        print(f"  Client olusturma hatasi: {e}")
        hatalar.append(f"Client hatasi: {e}")
else:
    print("  Atlandi (paket yok)")
print()

# ──────── 6. Test mesajı ────────
print("[6/7] Gemini'ye test mesaji gonderiliyor...")
if not client:
    print("  Atlandi (client yok)")
else:
    try:
        if yeni_sdk:
            from google.genai import types
            response = client.models.generate_content(
                model=model,
                contents="Sadece 'Baglanti basarili' yaz, baska bir sey yazma.",
                config=types.GenerateContentConfig(
                    max_output_tokens=20,
                    temperature=0.1,
                )
            )
        else:
            response = client.generate_content(
                "Sadece 'Baglanti basarili' yaz, baska bir sey yazma."
            )

        if response and response.text:
            print(f"  Gemini yanit verdi: '{response.text.strip()[:80]}'")
            print()
            print("  TUM TESTLER BASARILI - Gemini baglantisi calisiyor!")
        else:
            print("  Gemini bos yanit dondurdu")
            hatalar.append("Gemini bos yanit")

    except Exception as e:
        hata_str = str(e)
        tur = type(e).__name__
        print(f"  HATA {tur}: {hata_str[:200]}")

        if "401" in hata_str or "UNAUTHENTICATED" in hata_str.upper():
            print("  >> API key gecersiz! Yeni key alin: https://aistudio.google.com/apikey")
            hatalar.append("API key gecersiz (401)")
        elif "403" in hata_str or "PERMISSION" in hata_str.upper():
            print("  >> API key izni yok!")
            hatalar.append("API key izin hatasi (403)")
        elif "429" in hata_str or "EXHAUSTED" in hata_str.upper():
            print("  >> API kotasi dolmus! Bekleyin veya yeni API key olusturun")
            print("  >> Yeni key: https://aistudio.google.com/apikey")
            hatalar.append("API kota dolmus (429)")
        elif "404" in hata_str:
            print(f"  >> Model bulunamadi: {model}")
            hatalar.append(f"Model bulunamadi: {model}")
        else:
            hatalar.append(f"{tur}: {hata_str[:100]}")
            traceback.print_exc()
print()

# ──────── 7. Yedek model test ────────
if hatalar and any("429" in h for h in hatalar):
    print("[7/7] Yedek model deneniyor...")
    yedek = config.get("ai", {}).get("gemini_yedek_model", "gemini-1.5-flash")
    try:
        if yeni_sdk:
            from google.genai import types
            response = client.models.generate_content(
                model=yedek,
                contents="Sadece 'Yedek basarili' yaz.",
                config=types.GenerateContentConfig(max_output_tokens=20)
            )
        else:
            yedek_client = genai_eski.GenerativeModel(yedek)
            response = yedek_client.generate_content("Sadece 'Yedek basarili' yaz.")

        if response and response.text:
            print(f"  Yedek model ({yedek}) calisiyor: '{response.text.strip()[:50]}'")
        else:
            print(f"  Yedek model de bos yanit")
    except Exception as e:
        print(f"  Yedek model de basarisiz: {type(e).__name__}: {str(e)[:100]}")
    print()
else:
    print("[7/7] Yedek model testi - Atlandi (gerek yok)")
    print()

print("=" * 60)
if hatalar:
    print(f"  BULUNAN SORUNLAR ({len(hatalar)}):")
    for i, h in enumerate(hatalar, 1):
        print(f"  {i}. {h}")
    print()
    if any("429" in h or "kota" in h for h in hatalar):
        print("  COZUM: API kotasi dolmus.")
        print("  1. https://aistudio.google.com/apikey adresine gidin")
        print("  2. 'Create API Key' ile YENI bir key olusturun")
        print("  3. config.json'daki gemini_api_key'i yeni key ile degistirin")
        print("  4. ATLAS'i yeniden baslatin")
    if any("paket" in h.lower() or "sdk" in h.lower() for h in hatalar):
        print("  COZUM: Komut satirinda su komutu calistirin:")
        print("  venv\\Scripts\\pip.exe install google-genai")
else:
    print("  TUM TESTLER BASARILI!")
print("=" * 60)
print()
input("Kapatmak icin Enter'a basin...")
