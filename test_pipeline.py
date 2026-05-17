# -*- coding: utf-8 -*-
"""
ATLAS Tam Pipeline Testi
Bu script tum zinciri test eder: web_arama -> AI yanit
"""
import sys, os, json, time

print("=" * 60)
print("  ATLAS TAM PIPELINE TESTi")
print("=" * 60)

# Config yukle
print("\n[1/4] Config yukleniyor...")
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    print("  Config: OK")
except Exception as e:
    print(f"  Config HATA: {e}")
    print("  COZUM: Bu scripti ATLAS klasorunden calistirin!")
    input("\nKapatmak icin Enter'a bas...")
    sys.exit(1)

# Web arama testi
print("\n[2/4] Web arama testi...")
try:
    import web_arama
    test_sorular = [
        "Elon Musk kimdir",
        "yapay zeka nedir",
        "Turkiyenin nufusu kac"
    ]
    for s in test_sorular:
        gerekli, sorgu = web_arama.arama_gerekli_mi(s)
        if gerekli:
            sonuc = web_arama.arastir(sorgu)
            durum = "OK" if sonuc["basarili"] else "BASARISIZ"
            sayi = len(sonuc.get("sonuclar", []))
            print(f"  '{s}' -> {durum} ({sayi} sonuc, {sonuc['sure_ms']}ms)")
            if sonuc["basarili"] and sonuc.get("baglam"):
                print(f"    Baglam: {sonuc['baglam'][:100]}...")
        else:
            print(f"  '{s}' -> arama gereksiz")
except Exception as e:
    print(f"  Web arama HATA: {e}")
    import traceback
    traceback.print_exc()

# Karar merkezi testi
print("\n[3/4] Karar merkezi yukleniyor...")
try:
    from karar_merkezi import KararMerkezi
    km = KararMerkezi(config)
    print("  Karar merkezi: OK")
    print(f"  Gemini client: {'VAR' if km._gemini_client else 'YOK'}")
    print(f"  DeepSeek client: {'VAR' if km._deepseek_client else 'YOK'}")
    print(f"  Groq client: {'VAR' if km._groq_client else 'YOK'}")
    print(f"  Gemini devre disi: {getattr(km, '_gemini_devre_disi', 'ATTR YOK')}")
    print(f"  DeepSeek devre disi: {getattr(km, '_deepseek_devre_disi', 'ATTR YOK')}")
    print(f"  Groq devre disi: {getattr(km, '_groq_devre_disi', 'ATTR YOK')}")
except Exception as e:
    print(f"  Karar merkezi HATA: {e}")
    import traceback
    traceback.print_exc()
    input("\nKapatmak icin Enter'a bas...")
    sys.exit(1)

# Tam pipeline testi
print("\n[4/4] Tam pipeline testi (AI yanit)...")
test_sorular = [
    "Elon Musk kimdir",
    "yapay zeka nedir",
    "Turkiyenin nufusu kac"
]

for i, soru in enumerate(test_sorular, 1):
    print(f"\n  --- Soru {i}: '{soru}' ---")
    t0 = time.time()
    try:
        karar = km.karar_ver(soru)
        sure = (time.time() - t0) * 1000
        print(f"  Yol: {karar['yol']}")
        print(f"  Sure: {sure:.0f}ms")
        print(f"  Yanit: {karar['yanit'][:200]}")
        print(f"  Gemini devre disi: {km._gemini_devre_disi}")
        print(f"  DeepSeek devre disi: {km._deepseek_devre_disi}")
    except Exception as e:
        print(f"  HATA: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "=" * 60)
print("  TEST TAMAMLANDI")
print("=" * 60)

input("\nKapatmak icin Enter'a bas...")
