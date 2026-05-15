# Sesli AI Asistan v6.0 - 3 Katmanli Akilli Mimari

## Kurulum
1. `kur.bat` cift tikla
2. `config.json` icine Gemini API anahtarini yaz
   - Ucretsiz: https://aistudio.google.com/apikey
3. `baslat.bat` cift tikla

## Yenilikler (v6.0)
- 3 Katmanli komut sistemi (yerel + Gemini + yedek)
- On-bellekli TTS (sik yanitlar onceden olusturulur)
- pyttsx3 aninda ses (50ms!)
- Ollama gereksiz - RAM tasarrufu
- 50+ yerel komut kalıbı (AI cagirmadan)
- Detayli sure olcumu

## Dosyalar
- config.json: Ayarlar
- main.py: Ana program
- arayuz.py: JARVIS arayuzu
- yapay_zeka.py: 3 katmanli AI
- ses_tanima.py: Ses tanima
- sesli_yanit.py: TTS (on-bellek + pyttsx3)
- bilgisayar_kontrol.py: Windows kontrol
- hafiza.py: Ogrenme/hafiza
- guncelleyici.py: Guncelleme
