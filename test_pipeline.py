# -*- coding: utf-8 -*-
"""
ATLAS Tam Pipeline Testi v3
"""
import sys, os, json, time

print("=" * 60)
print("  ATLAS TAM PIPELINE TESTi v3")
print("=" * 60)

# Config yukle
print("\n[1/5] Config yukleniyor...")
try:
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    print("  Config: OK")
except Exception as e:
    print(f"  Config HATA: {e}")
    input("\nKapatmak icin Enter'a bas...")
    sys.exit(1)

# Web arama testi
print("\n[2/5] Web arama testi...")
try:
    import web_arama
    for s in ["Elon Musk kimdir", "yapay zeka nedir", "Turkiye nufusu"]:
        gerekli, sorgu = web_arama.arama_gerekli_mi(s)
        if gerekli:
            sonuc = web_arama.arastir(sorgu)
            d = "OK" if sonuc["basarili"] else "BASARISIZ"
            print(f"  '{s}' -> {d} ({len(sonuc.get('sonuclar',[]))} sonuc, {sonuc['sure_ms']}ms)")
        else:
            print(f"  '{s}' -> arama gereksiz")
except Exception as e:
    print(f"  HATA: {e}")
    import traceback; traceback.print_exc()

# Groq direkt testi
print("\n[3/5] Groq direkt testi...")
ai_cfg = config.get("ai", {})
groq_key = ai_cfg.get("groq_api_key", "")
groq_model = ai_cfg.get("groq_model", "llama-3.3-70b-versatile")
if groq_key:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=groq_key, base_url="https://api.groq.com/openai/v1")
        t0 = time.time()
        resp = client.chat.completions.create(
            model=groq_model,
            messages=[
                {"role": "system", "content": "Sen ATLAS, Turkce sesli asistansin. Kisa ve oz yanitla."},
                {"role": "user", "content": "Elon Musk kimdir? 2 cumle ile anlat."}
            ],
            max_tokens=200, temperature=0.7, timeout=10
        )
        sure = (time.time() - t0) * 1000
        yanit = resp.choices[0].message.content if resp.choices else "BOS"
        print(f"  Groq: OK ({sure:.0f}ms)")
        print(f"  Yanit: {yanit[:200]}")
    except Exception as e:
        print(f"  Groq HATA: {e}")
else:
    print("  Groq key YOK!")

# Karar merkezi test
print("\n[4/5] Karar merkezi yukleniyor...")
try:
    from karar_merkezi import KararMerkezi
    from kalip_motoru import KalipMotoru
    from hafiza_sistemi import HafizaSistemi
    from duygu_analizi import DuyguAnalizi

    kalip = KalipMotoru(config)
    hafiza = HafizaSistemi(config)
    duygu = DuyguAnalizi()
    km = KararMerkezi(kalip, hafiza, duygu, config)
    print("  Karar merkezi: OK")
    print(f"  Gemini client: {'VAR' if km._gemini_client else 'YOK'}")
    print(f"  DeepSeek client: {'VAR' if km._deepseek_client else 'YOK'}")
    print(f"  Groq client: {'VAR' if km._groq_client else 'YOK'}")
    print(f"  Gemini devre disi: {getattr(km, '_gemini_devre_disi', 'ATTR YOK')}")
    print(f"  DeepSeek devre disi: {getattr(km, '_deepseek_devre_disi', 'ATTR YOK')}")
except Exception as e:
    print(f"  HATA: {e}")
    import traceback; traceback.print_exc()
    input("\nKapatmak icin Enter'a bas...")
    sys.exit(1)

# Tam pipeline testi
print("\n[5/5] Tam pipeline testi...")
test_sorular = [
    "Elon Musk kimdir",
    "yapay zeka nedir",
    "Turkiye nufusu kac"
]

for i, soru in enumerate(test_sorular, 1):
    print(f"\n  --- Soru {i}: '{soru}' ---")
    t0 = time.time()
    try:
        karar = km.karar_ver(soru)
        sure = (time.time() - t0) * 1000
        print(f"  Yol: {karar['yol']}")
        print(f"  Sure: {sure:.0f}ms")
        yanit = karar['yanit']
        print(f"  Yanit ({len(yanit)} kar): {yanit[:250]}")
        print(f"  Gemini devre disi: {km._gemini_devre_disi}")
        print(f"  DeepSeek devre disi: {km._deepseek_devre_disi}")
    except Exception as e:
        print(f"  HATA: {e}")
        import traceback; traceback.print_exc()

print("\n" + "=" * 60)
print("  TEST TAMAMLANDI")
print("=" * 60)

input("\nKapatmak icin Enter'a bas...")
