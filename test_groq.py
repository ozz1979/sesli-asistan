"""
ATLAS — Groq AI Bağlantı Testi
Groq = Ücretsiz, çok hızlı AI (Llama 3.3 70B)
"""
import json, os, sys, time

print("=" * 60)
print("  ATLAS — Groq AI Bağlantı Testi")
print("=" * 60)
print()

# Config oku
cfg_yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(cfg_yol, "r", encoding="utf-8") as f:
    config = json.load(f)
api_key = config.get("ai", {}).get("groq_api_key", "")

if not api_key:
    print("HATA: config.json'da groq_api_key bos!")
    print()
    print("Groq API key almak icin (UCRETSIZ):")
    print("1. https://console.groq.com adresine git")
    print("2. Google ile giris yap")
    print("3. Sol menuden 'API Keys' tikla")
    print("4. 'Create API Key' tikla")
    print("5. config.json'da 'groq_api_key' alanina yapistir")
    print()
    input("Enter...")
    sys.exit(1)

print(f"API Key: {api_key[:8]}...{api_key[-4:]}")
print()

# openai paketi kontrol
print("[1/3] openai paketi kontrol ediliyor...", end=" ", flush=True)
try:
    from openai import OpenAI
    import openai
    print(f"OK (v{openai.__version__})")
except ImportError:
    print("YOK!")
    print()
    print("Cozum: venv\\Scripts\\pip.exe install openai")
    input("Enter...")
    sys.exit(1)

# Client oluştur
print("[2/3] Groq client olusturuluyor...", end=" ", flush=True)
try:
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1"
    )
    print("OK")
except Exception as e:
    print(f"HATA: {e}")
    input("Enter...")
    sys.exit(1)

# Test mesajı gönder
print("[3/3] Groq'a test mesaji gonderiliyor...", end=" ", flush=True)
try:
    t0 = time.time()
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Sen ATLAS adında Türkçe sesli asistansın. Kısa cevap ver."},
            {"role": "user", "content": "Merhaba, nasılsın?"}
        ],
        max_tokens=50,
        temperature=0.7,
        timeout=10,
    )
    sure = time.time() - t0

    if response and response.choices:
        yanit = response.choices[0].message.content.strip()
        print(f"BASARILI! ({sure:.1f}s)")
        print()
        print(f"  Groq yaniti: {yanit}")
        print()
        print("=" * 60)
        print("  GROQ CALISIYOR! ATLAS kullanmaya hazir.")
        print(f"  Yanit suresi: {sure:.1f} saniye")
        print("=" * 60)
    else:
        print("Bos yanit")
except Exception as e:
    print(f"HATA: {e}")
    print()
    print("Cozum:")
    print("1. API key'i kontrol edin")
    print("2. https://console.groq.com'da hesabinizi kontrol edin")

print()
input("Kapatmak icin Enter'a basin...")
