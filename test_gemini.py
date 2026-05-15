"""
ATLAS — Gemini AI Bağlantı Teşhis Aracı
Bu dosyayı çalıştırarak Gemini bağlantınızı test edin.
"""
import sys
import os
import json
import traceback

print("=" * 60)
print("  ATLAS — Gemini AI Bağlantı Teşhis Aracı")
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
        print(f"  ✅ API Key: {masked} ({len(api_key)} karakter)")
    else:
        print("  ❌ API Key: BOŞ!")
        hatalar.append("API key config.json'da boş")
    print(f"  Model: {model}")
    print(f"  Yedek: {yedek_model}")
    print(f"  Timeout: {timeout}s")
except FileNotFoundError:
    print("  ❌ config.json bulunamadı!")
    hatalar.append("config.json yok")
except json.JSONDecodeError as e:
    print(f"  ❌ config.json geçersiz JSON!")
    print(f"     Hata satırı: {e.lineno}, kolon: {e.colno}")
    print(f"     Hata: {e.msg}")
    hatalar.append(f"config.json JSON hatası: satır {e.lineno}")
except Exception as e:
    print(f"  ❌ Hata: {e}")
    hatalar.append(str(e))
print()

# ──────── 3. Paket kontrolü ────────
print("[3/7] google-generativeai paketi kontrol ediliyor...")
genai = None
try:
    import google.generativeai as genai
    try:
        ver = genai.__version__
    except:
        ver = "bilinmiyor"
    print(f"  ✅ Paket yüklü: google-generativeai v{ver}")
except ImportError as e:
    print(f"  ❌ Paket bulunamadı: {e}")
    print()
    print("  Çözüm: Komut satırında şunu çalıştırın:")
    print("  pip install google-generativeai")
    hatalar.append("google-generativeai paketi yok")
print()

# ──────── 4. Alt bağımlılıklar ────────
print("[4/7] Alt bağımlılıklar kontrol ediliyor...")
for pkg, isim in [("google.api_core", "google-api-core"), ("google.protobuf", "protobuf"), ("grpc", "grpcio")]:
    try:
        __import__(pkg)
        print(f"  ✅ {isim}")
    except ImportError:
        print(f"  ⚠️ {isim} — eksik olabilir")
print()

# ──────── 5. İnternet bağlantısı ────────
print("[5/7] İnternet bağlantısı test ediliyor...")
internet_ok = False
try:
    import urllib.request
    # Google genel
    urllib.request.urlopen("https://www.google.com", timeout=10)
    print("  ✅ İnternet bağlantısı var (google.com)")
    internet_ok = True
except Exception as e:
    print(f"  ❌ İnternet bağlantısı yok: {e}")
    hatalar.append("İnternet bağlantısı yok")

if internet_ok:
    try:
        r = urllib.request.urlopen("https://generativelanguage.googleapis.com", timeout=10)
        print(f"  ✅ Gemini API erişilebilir (HTTP {r.status})")
    except Exception as e:
        tur = type(e).__name__
        print(f"  ❌ Gemini API erişilemez ({tur}): {e}")
        hatalar.append(f"Gemini API erişilemez: {tur}")
print()

# ──────── 6. Client oluşturma ────────
print("[6/7] Gemini client oluşturuluyor...")
client = None
if not genai:
    print("  ⏭️ Atlandı (paket yok)")
elif not api_key:
    print("  ⏭️ Atlandı (API key yok)")
else:
    # İlk deneme: system_instruction ile
    try:
        genai.configure(api_key=api_key)
        client = genai.GenerativeModel(
            model,
            generation_config={
                "max_output_tokens": 100,
                "temperature": 0.7,
            },
            system_instruction="Sen ATLAS adında bir Türkçe sesli asistansın."
        )
        print(f"  ✅ Client oluşturuldu (system_instruction ile)")
    except TypeError as e:
        # Eski sürüm — system_instruction desteklemiyor
        print(f"  ⚠️ system_instruction desteklenmiyor: {e}")
        print("  → system_instruction olmadan deneniyor...")
        try:
            client = genai.GenerativeModel(
                model,
                generation_config={
                    "max_output_tokens": 100,
                    "temperature": 0.7,
                }
            )
            print(f"  ✅ Client oluşturuldu (system_instruction olmadan)")
            hatalar.append("system_instruction DESTEKLENMIYOR — paket eski sürüm")
        except Exception as e2:
            print(f"  ❌ Client oluşturulamadı: {e2}")
            hatalar.append(f"Client oluşturulamadı: {e2}")
    except Exception as e:
        print(f"  ❌ Client oluşturma hatası: {type(e).__name__}: {e}")
        hatalar.append(f"Client hatası: {e}")
print()

# ──────── 7. Test mesajı ────────
print("[7/7] Gemini'ye test mesajı gönderiliyor...")
if not client:
    print("  ⏭️ Atlandı (client yok)")
else:
    # Deneme 1: request_options ile
    try:
        response = client.generate_content(
            "Sadece 'Bağlantı başarılı' yaz, başka bir şey yazma.",
            request_options={"timeout": 15}
        )
        if response and response.text:
            print(f"  ✅ Gemini yanıt verdi: '{response.text.strip()[:80]}'")
            print()
            print("  🎉 TÜM TESTLER BAŞARILI — Gemini bağlantısı çalışıyor!")
        else:
            print("  ❌ Gemini boş yanıt döndü")
            hatalar.append("Gemini boş yanıt")
    except TypeError as te:
        # request_options desteklenmiyor olabilir
        print(f"  ⚠️ request_options hatası: {te}")
        print("  → request_options olmadan deneniyor...")
        try:
            response = client.generate_content(
                "Sadece 'Bağlantı başarılı' yaz, başka bir şey yazma."
            )
            if response and response.text:
                print(f"  ✅ Gemini yanıt verdi: '{response.text.strip()[:80]}'")
                hatalar.append("request_options DESTEKLENMIYOR — paket eski sürüm")
            else:
                print("  ❌ Gemini boş yanıt döndü")
                hatalar.append("Gemini boş yanıt")
        except Exception as e2:
            print(f"  ❌ Hata: {type(e2).__name__}: {e2}")
            hatalar.append(str(e2))
    except Exception as e:
        hata_str = str(e)
        tur = type(e).__name__
        print(f"  ❌ {tur}: {hata_str[:200]}")

        if "401" in hata_str or "UNAUTHENTICATED" in hata_str.upper():
            print("  💡 API key geçersiz! Yeni key alın: https://aistudio.google.com/apikey")
            hatalar.append("API key geçersiz (401)")
        elif "403" in hata_str or "PERMISSION" in hata_str.upper():
            print("  💡 API key'in izni yok! Google AI Studio'dan kontrol edin")
            hatalar.append("API key izin hatası (403)")
        elif "429" in hata_str or "EXHAUSTED" in hata_str.upper():
            print("  💡 API kotası dolmuş! Biraz bekleyin veya kota sınırını kontrol edin")
            hatalar.append("API kota dolmuş (429)")
        elif "404" in hata_str:
            print(f"  💡 Model bulunamadı: {model}")
            hatalar.append(f"Model bulunamadı: {model}")
        elif "ssl" in hata_str.lower() or "certificate" in hata_str.lower():
            print("  💡 SSL hatası — antivirüs veya proxy sorunu olabilir")
            hatalar.append("SSL sertifika hatası")
        else:
            hatalar.append(f"{tur}: {hata_str[:100]}")
            print()
            print("  Detaylı hata:")
            traceback.print_exc()

print()
print("=" * 60)
if hatalar:
    print(f"  BULUNAN SORUNLAR ({len(hatalar)}):")
    for i, h in enumerate(hatalar, 1):
        print(f"  {i}. {h}")
else:
    print("  ✅ Tüm testler başarılı!")
print("=" * 60)
print()
input("Kapatmak için Enter'a basın...")
