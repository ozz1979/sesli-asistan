# -*- coding: utf-8 -*-
"""
ATLAS Baglanti Testi
=====================
Bu script ATLAS'in tum bilesenlerini tek tek test eder.
Hangi adimda sorun oldugunu gosterir.

Kullanim: python test_baglanti.py
"""

import sys
import os
import json
import time

print("=" * 60)
print("  ATLAS BAGLANTI TESTi")
print("=" * 60)
print()

sonuclar = {}

# ════════════════════════════════════════════════════════════
# 1. PYTHON BILGILERI
# ════════════════════════════════════════════════════════════
print("[1/8] Python bilgileri...")
print(f"  Python: {sys.version}")
print(f"  Calisma klasoru: {os.getcwd()}")
print(f"  Karakter kodlama: {sys.getdefaultencoding()}")
sonuclar["python"] = "OK"
print()

# ════════════════════════════════════════════════════════════
# 2. INTERNET BAGLANTISI
# ════════════════════════════════════════════════════════════
print("[2/8] Internet baglantisi...")
try:
    import urllib.request
    import ssl
    
    # SSL context (Windows uyumlu)
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request("https://www.google.com", headers={"User-Agent": "ATLAS-Test/1.0"})
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        print(f"  BASARILI — Google erisim: {resp.status}")
        sonuclar["internet"] = "OK"
    except Exception as e1:
        # SSL fallback
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        req = urllib.request.Request("https://www.google.com", headers={"User-Agent": "ATLAS-Test/1.0"})
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
        print(f"  BASARILI (SSL fallback) — Google erisim: {resp.status}")
        sonuclar["internet"] = "OK (SSL fallback)"
except Exception as e:
    print(f"  BASARISIZ — {type(e).__name__}: {e}")
    sonuclar["internet"] = f"HATA: {e}"
print()

# ════════════════════════════════════════════════════════════
# 3. WIKIPEDIA API TESTI
# ════════════════════════════════════════════════════════════
print("[3/8] Wikipedia TR API testi...")
try:
    import urllib.parse
    import ssl
    
    sorgu = "Elon Musk"
    params = urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": sorgu,
        "format": "json",
        "utf8": "1",
        "srlimit": "3",
    })
    url = f"https://tr.wikipedia.org/w/api.php?{params}"
    
    headers = {"User-Agent": "ATLAS-Sesli-Asistan/1.0 (Windows; Python)"}
    req = urllib.request.Request(url, headers=headers)
    
    try:
        resp = urllib.request.urlopen(req, timeout=10)
    except Exception:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        resp = urllib.request.urlopen(req, timeout=10, context=ctx)
    
    charset = resp.headers.get_content_charset() or "utf-8"
    data = json.loads(resp.read().decode(charset, errors="replace"))
    results = data.get("query", {}).get("search", [])
    
    print(f"  BASARILI — '{sorgu}' icin {len(results)} sonuc bulundu")
    for r in results[:2]:
        print(f"    - {r['title']}")
    sonuclar["wikipedia"] = f"OK ({len(results)} sonuc)"
except Exception as e:
    print(f"  BASARISIZ — {type(e).__name__}: {e}")
    sonuclar["wikipedia"] = f"HATA: {e}"
print()

# ════════════════════════════════════════════════════════════
# 4. WEB_ARAMA MODULU TESTI
# ════════════════════════════════════════════════════════════
print("[4/8] web_arama modulu testi...")
try:
    import web_arama
    print("  Modul yuklendi: BASARILI")
    
    # arama_gerekli_mi testi
    gerekli, sorgu = web_arama.arama_gerekli_mi("Elon Musk kimdir")
    print(f"  arama_gerekli_mi('Elon Musk kimdir') → gerekli={gerekli}, sorgu={sorgu}")
    
    # Gercek arama testi
    t0 = time.time()
    sonuc = web_arama.arastir("Elon Musk")
    sure = int((time.time() - t0) * 1000)
    
    print(f"  arastir('Elon Musk') → basarili={sonuc['basarili']}, {len(sonuc['sonuclar'])} sonuc, {sure}ms")
    if sonuc["basarili"] and sonuc["sonuclar"]:
        ilk = sonuc["sonuclar"][0]
        print(f"    Ilk sonuc: {ilk['baslik']}")
        print(f"    Ozet: {ilk['ozet'][:120]}...")
        sonuclar["web_arama"] = f"OK ({len(sonuc['sonuclar'])} sonuc, {sure}ms)"
    else:
        print(f"  UYARI — Arama basarisiz veya sonuc yok")
        sonuclar["web_arama"] = "BASARISIZ (sonuc yok)"
except ImportError as e:
    print(f"  BASARISIZ — Modul yuklenemedi: {e}")
    sonuclar["web_arama"] = f"IMPORT HATA: {e}"
except Exception as e:
    print(f"  BASARISIZ — {type(e).__name__}: {e}")
    sonuclar["web_arama"] = f"HATA: {e}"
print()

# ════════════════════════════════════════════════════════════
# 5. OPENAI PAKETI (Groq icin gerekli)
# ════════════════════════════════════════════════════════════
print("[5/8] openai paketi kontrol...")
try:
    from openai import OpenAI
    print("  openai paketi: YUKLÜ")
    sonuclar["openai_paket"] = "OK"
except ImportError:
    print("  openai paketi: EKSIK — 'pip install openai' calistir")
    sonuclar["openai_paket"] = "EKSIK"
print()

# ════════════════════════════════════════════════════════════
# 6. GROQ API TESTI
# ════════════════════════════════════════════════════════════
print("[6/8] Groq API testi...")
try:
    # Config dosyasindan API key oku
    config_yollari = [
        "config.json",
        os.path.join(os.path.dirname(__file__), "config.json"),
    ]
    
    config = {}
    config_yol = None
    for yol in config_yollari:
        if os.path.exists(yol):
            with open(yol, "r", encoding="utf-8") as f:
                config = json.load(f)
            config_yol = yol
            break
    
    groq_key = config.get("ai", {}).get("groq_api_key", "")
    
    if not groq_key:
        print(f"  Config dosyasi: {config_yol or 'BULUNAMADI'}")
        print(f"  Config icerik (ai bolumu): {json.dumps(config.get('ai', {}), indent=2)[:200]}")
        print("  Groq API key: BULUNAMADI")
        sonuclar["groq"] = "API KEY YOK"
    else:
        print(f"  Groq API key: ...{groq_key[-8:]}")
        
        from openai import OpenAI
        client = OpenAI(
            api_key=groq_key,
            base_url="https://api.groq.com/openai/v1"
        )
        
        t0 = time.time()
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Sen Turkce konusan bir asistansin. Kisa cevap ver."},
                {"role": "user", "content": "Elon Musk kimdir? 2 cumlede cevapla."}
            ],
            max_tokens=150,
            temperature=0.7,
            timeout=15,
        )
        sure = int((time.time() - t0) * 1000)
        
        if response and response.choices:
            yanit = response.choices[0].message.content
            print(f"  BASARILI — {sure}ms")
            print(f"  Groq yanit: {yanit[:200]}")
            sonuclar["groq"] = f"OK ({sure}ms)"
        else:
            print("  BASARISIZ — Bos yanit")
            sonuclar["groq"] = "BASARISIZ (bos yanit)"
            
except ImportError:
    print("  BASARISIZ — openai paketi eksik")
    sonuclar["groq"] = "openai paketi eksik"
except Exception as e:
    print(f"  BASARISIZ — {type(e).__name__}: {e}")
    sonuclar["groq"] = f"HATA: {e}"
print()

# ════════════════════════════════════════════════════════════
# 7. GEMINI API TESTI
# ════════════════════════════════════════════════════════════
print("[7/8] Gemini API testi...")
try:
    gemini_key = config.get("ai", {}).get("gemini_api_key", "")
    if not gemini_key:
        print("  Gemini API key: BULUNAMADI")
        sonuclar["gemini"] = "API KEY YOK"
    else:
        print(f"  Gemini API key: ...{gemini_key[-8:]}")
        try:
            from google import genai
            client = genai.Client(api_key=gemini_key)
            t0 = time.time()
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents="Merhaba, test mesaji. Kisa cevap ver."
            )
            sure = int((time.time() - t0) * 1000)
            print(f"  BASARILI — {sure}ms: {response.text[:100]}")
            sonuclar["gemini"] = f"OK ({sure}ms)"
        except Exception as e:
            hata = str(e)
            if "429" in hata:
                print(f"  BASARISIZ — Rate limit (429)")
                sonuclar["gemini"] = "RATE LIMIT (429)"
            else:
                print(f"  BASARISIZ — {type(e).__name__}: {hata[:150]}")
                sonuclar["gemini"] = f"HATA: {hata[:100]}"
except Exception as e:
    print(f"  BASARISIZ — {type(e).__name__}: {e}")
    sonuclar["gemini"] = f"HATA: {e}"
print()

# ════════════════════════════════════════════════════════════
# 8. CONFIG DOSYASI OZET
# ════════════════════════════════════════════════════════════
print("[8/8] Config dosyasi ozet...")
if config:
    ai = config.get("ai", {})
    print(f"  Gemini key: {'VAR' if ai.get('gemini_api_key') else 'YOK'}")
    print(f"  DeepSeek key: {'VAR' if ai.get('deepseek_api_key') else 'YOK'}")
    print(f"  Groq key: {'VAR' if ai.get('groq_api_key') else 'YOK'}")
    print(f"  Gemini model: {ai.get('gemini_model', 'TANIMLANMAMIS')}")
    print(f"  Groq model: {ai.get('groq_model', 'TANIMLANMAMIS')}")
    
    # TTS ayarlari
    tts = config.get("tts", {})
    if tts:
        print(f"  TTS motor: {tts.get('motor', 'TANIMLANMAMIS')}")
        print(f"  TTS hiz: {tts.get('hiz', 'TANIMLANMAMIS')}")
else:
    print("  Config dosyasi bulunamadi!")
    sonuclar["config"] = "BULUNAMADI"
print()

# ════════════════════════════════════════════════════════════
# SONUC RAPORU
# ════════════════════════════════════════════════════════════
print("=" * 60)
print("  SONUC RAPORU")
print("=" * 60)
for ad, durum in sonuclar.items():
    ikon = "OK" if "OK" in str(durum) else "XX"
    print(f"  [{ikon}] {ad}: {durum}")

# Dosyaya kaydet
rapor_dosya = "test_sonuc.txt"
with open(rapor_dosya, "w", encoding="utf-8") as f:
    f.write("ATLAS BAGLANTI TEST SONUCLARI\n")
    f.write(f"Tarih: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.write(f"Python: {sys.version}\n")
    f.write(f"Klasor: {os.getcwd()}\n\n")
    for ad, durum in sonuclar.items():
        f.write(f"{ad}: {durum}\n")

print(f"\nSonuclar '{rapor_dosya}' dosyasina kaydedildi.")
print("Bu dosyayi bana gonder, sorunu tespit edebilirim.")
print()
input("Kapatmak icin Enter'a bas...")
