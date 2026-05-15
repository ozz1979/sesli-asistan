"""
ATLAS — Gemini Model Deneme Aracı
Hangi modelin çalıştığını bulur.
"""
import json, os, sys, time

print("=" * 60)
print("  ATLAS — Gemini Model Deneme Aracı")
print("=" * 60)
print()

# Config oku
cfg_yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(cfg_yol, "r", encoding="utf-8") as f:
    config = json.load(f)
api_key = config.get("ai", {}).get("gemini_api_key", "")
if not api_key:
    print("HATA: config.json'da API key yok!")
    input("Enter...")
    sys.exit(1)

print(f"API Key: {api_key[:6]}...{api_key[-4:]}")
print()

# Client oluştur
try:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=api_key)
except ImportError:
    print("HATA: google-genai paketi yok! pip install google-genai")
    input("Enter...")
    sys.exit(1)

# Test edilecek modeller
modeller = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-1.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro",
    "gemini-2.0-flash-exp",
]

calisan = []

for i, model in enumerate(modeller, 1):
    print(f"[{i}/{len(modeller)}] {model} deneniyor...", end=" ", flush=True)
    try:
        t0 = time.time()
        response = client.models.generate_content(
            model=model,
            contents="Sadece 'merhaba' yaz.",
            config=types.GenerateContentConfig(
                max_output_tokens=10,
                temperature=0.1,
            )
        )
        sure = time.time() - t0
        if response and response.text:
            yanit = response.text.strip()[:30]
            print(f"BASARILI ({sure:.1f}s) -> '{yanit}'")
            calisan.append((model, sure))
        else:
            print("Bos yanit")
    except Exception as e:
        hata = str(e)[:80]
        if "429" in hata:
            print("KOTA DOLMUS (429)")
        elif "404" in hata:
            print("MODEL YOK (404)")
        elif "403" in hata:
            print("IZIN YOK (403)")
        else:
            print(f"HATA: {hata}")
    time.sleep(1)

print()
print("=" * 60)
if calisan:
    print(f"  CALISAN MODELLER ({len(calisan)}):")
    for m, s in calisan:
        print(f"    - {m} ({s:.1f}s)")
    en_hizli = min(calisan, key=lambda x: x[1])
    print()
    print(f"  EN HIZLI: {en_hizli[0]} ({en_hizli[1]:.1f}s)")
    print()
    print(f"  config.json'da gemini_model olarak '{en_hizli[0]}' kullanin")
else:
    print("  HICBIR MODEL CALISMADI!")
    print()
    print("  Cozum secenekleri:")
    print("  1. Farkli bir Google hesabi ile aistudio.google.com'a giris yapin")
    print("  2. Yeni hesapta 'Create API Key in new project' secin")
    print("  3. Yeni key'i config.json'a yapisitirin")
    print("  4. Bu testi tekrar calistirin")
    print()
    print("  VEYA yarin sabaha kadar bekleyin (kota gunluk sifirlanir)")
print("=" * 60)
print()
input("Kapatmak icin Enter'a basin...")
