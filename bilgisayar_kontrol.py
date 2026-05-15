"""
Bilgisayar Kontrol Modulu v6.0-fix5
- Windows uyumlu uygulama acma (tam yol arama)
- start komutu + webbrowser fallback
- Bilgisayar kapat/yeniden baslat
"""
import subprocess
import os
import sys
import webbrowser


# Populer uygulamalarin Windows'taki bilinen yollari
UYGULAMA_YOLLARI = {
    "chrome": [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    ],
    "firefox": [
        os.path.expandvars(r"%ProgramFiles%\Mozilla Firefox\firefox.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Mozilla Firefox\firefox.exe"),
    ],
    "word": [
        os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\WINWORD.EXE"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\WINWORD.EXE"),
    ],
    "excel": [
        os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\EXCEL.EXE"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\EXCEL.EXE"),
    ],
    "powerpoint": [
        os.path.expandvars(r"%ProgramFiles%\Microsoft Office\root\Office16\POWERPNT.EXE"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Office\root\Office16\POWERPNT.EXE"),
    ],
    "discord": [
        os.path.expandvars(r"%LocalAppData%\Discord\Update.exe"),
    ],
    "spotify": [
        os.path.expandvars(r"%AppData%\Spotify\Spotify.exe"),
    ],
    "vlc": [
        os.path.expandvars(r"%ProgramFiles%\VideoLAN\VLC\vlc.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\VideoLAN\VLC\vlc.exe"),
    ],
    "telegram": [
        os.path.expandvars(r"%AppData%\Telegram Desktop\Telegram.exe"),
    ],
}

# Windows'ta dogrudan calistirilabilen uygulamalar (PATH'te olan)
DOGRUDAN_CALISTIR = {
    "notepad": "notepad.exe",
    "not defteri": "notepad.exe",
    "hesap makinesi": "calc.exe",
    "calculator": "calc.exe",
    "cmd": "cmd.exe",
    "komut satiri": "cmd.exe",
    "terminal": "cmd.exe",
    "dosya yoneticisi": "explorer.exe",
    "explorer": "explorer.exe",
    "paint": "mspaint.exe",
    "gorev yoneticisi": "taskmgr.exe",
}

# Windows URI protokolleri (ms-settings: vb.)
URI_HARITASI = {
    "ayarlar": "ms-settings:",
}

# URL olarak acilacaklar
URL_HARITASI = {
    "youtube": "https://www.youtube.com",
    "whatsapp": "https://web.whatsapp.com",
}


class BilgisayarKontrol:
    def __init__(self):
        pass

    def calistir(self, fonksiyon, parametreler):
        fonksiyonlar = {
            "uygulama_ac": self._uygulama_ac,
            "web_ara": self._web_ara,
            "url_ac": self._url_ac,
            "dosya_bul": self._dosya_bul,
            "ses_ayarla": self._ses_ayarla,
            "ekran_goruntusu": self._ekran_goruntusu,
            "metin_yaz": self._metin_yaz,
            "tus_bas": self._tus_bas,
            "bilgisayar_bilgi": self._bilgisayar_bilgi,
            "islem_listele": self._islem_listele,
            "islem_kapat": self._islem_kapat,
            "bilgisayar_kapat": self._bilgisayar_kapat,
        }

        fn = fonksiyonlar.get(fonksiyon)
        if fn:
            try:
                sonuc = fn(parametreler)
                return True, sonuc
            except Exception as e:
                return False, str(e)
        return False, f"Bilinmeyen fonksiyon: {fonksiyon}"

    def _uygulama_bul(self, isim):
        """Uygulamanin tam yolunu bul"""
        isim_kucuk = isim.lower().strip()

        # 1) Windows PATH'te dogrudan calisanlar
        if isim_kucuk in DOGRUDAN_CALISTIR:
            return ("dogrudan", DOGRUDAN_CALISTIR[isim_kucuk])

        # 2) URI protokolleri (ms-settings: vb.)
        if isim_kucuk in URI_HARITASI:
            return ("uri", URI_HARITASI[isim_kucuk])

        # 3) URL olarak acilacaklar
        if isim_kucuk in URL_HARITASI:
            return ("url", URL_HARITASI[isim_kucuk])

        # 4) Bilinen yollardan ara
        if isim_kucuk in UYGULAMA_YOLLARI:
            for yol in UYGULAMA_YOLLARI[isim_kucuk]:
                if os.path.exists(yol):
                    return ("yol", yol)

        # 5) Discord ozel durumu (Update.exe --processStart Discord.exe)
        if isim_kucuk == "discord":
            discord_update = os.path.expandvars(r"%LocalAppData%\Discord\Update.exe")
            if os.path.exists(discord_update):
                return ("discord", discord_update)

        # 6) Bulunamadi
        return ("yok", isim)

    def _uygulama_ac(self, params):
        isim = params.get("isim", "").strip()
        if not isim:
            return "Uygulama ismi bos"

        tip, yol = self._uygulama_bul(isim)

        try:
            if tip == "dogrudan":
                # notepad, calc, mspaint vb. - Windows PATH'te
                subprocess.Popen(yol, shell=False)
                return f"{isim} acildi"

            elif tip == "uri":
                # ms-settings: vb.
                os.system(f"start {yol}")
                return f"{isim} acildi"

            elif tip == "url":
                # Web URL
                webbrowser.open(yol)
                return f"{isim} acildi"

            elif tip == "yol":
                # Tam yol bulundu
                subprocess.Popen([yol], shell=False)
                return f"{isim} acildi"

            elif tip == "discord":
                subprocess.Popen([yol, "--processStart", "Discord.exe"], shell=False)
                return f"{isim} acildi"

            else:
                # Son care: start komutuyla dene
                ret = os.system(f'start "" "{isim}"')
                if ret == 0:
                    return f"{isim} acildi"
                return f"{isim} bulunamadi"

        except Exception as e:
            # Son fallback: start komutu
            try:
                os.system(f'start "" "{isim}"')
                return f"{isim} acildi"
            except:
                return f"{isim} acilamadi: {e}"

    def _web_ara(self, params):
        sorgu = params.get("sorgu", "")
        if sorgu:
            import urllib.parse
            url = f"https://www.google.com/search?q={urllib.parse.quote(sorgu)}"
            webbrowser.open(url)
            return f"'{sorgu}' aratildi"
        return "Arama sorgusu bos"

    def _url_ac(self, params):
        url = params.get("url", "")
        if url:
            webbrowser.open(url)
            return f"{url} acildi"
        return "URL bos"

    def _dosya_bul(self, params):
        isim = params.get("isim", "")
        if isim:
            try:
                sonuc = subprocess.run(
                    ['where', '/r', 'C:\\Users', isim],
                    capture_output=True, text=True, timeout=15
                )
                dosyalar = sonuc.stdout.strip().split('\n')[:5]
                if dosyalar and dosyalar[0]:
                    return f"Bulunan: {', '.join(dosyalar)}"
            except subprocess.TimeoutExpired:
                return f"Arama zaman asimi"
            return f"'{isim}' bulunamadi"
        return "Dosya adi bos"

    def _ses_ayarla(self, params):
        seviye = params.get("seviye", 50)
        try:
            seviye = max(0, min(100, int(seviye)))
            adim_sayisi = seviye // 2
            ps_cmd = (
                f'$ws = New-Object -ComObject WScript.Shell; '
                f'for($i=0; $i -lt 50; $i++) {{ $ws.SendKeys([char]174) }}; '
                f'for($i=0; $i -lt {adim_sayisi}; $i++) {{ $ws.SendKeys([char]175) }}'
            )
            subprocess.run(
                ["powershell", "-Command", ps_cmd],
                capture_output=True,
                timeout=10
            )
            return f"Ses %{seviye} olarak ayarlandi"
        except Exception as e:
            return f"Ses ayarlanamadi: {e}"

    def _ekran_goruntusu(self, params):
        try:
            import pyautogui
            dosya = os.path.join(os.path.expanduser("~"), "Desktop", "ekran_goruntusu.png")
            pyautogui.screenshot(dosya)
            return f"Ekran goruntusu kaydedildi: {dosya}"
        except Exception as e:
            return f"Ekran goruntusu alinamadi: {e}"

    def _metin_yaz(self, params):
        try:
            import pyautogui
            import pyperclip
            metin = params.get("metin", "")
            pyperclip.copy(metin)
            pyautogui.hotkey('ctrl', 'v')
            return f"Metin yazildi"
        except Exception as e:
            return f"Metin yazilamadi: {e}"

    def _tus_bas(self, params):
        try:
            import pyautogui
            tuslar = params.get("tuslar", [])
            if tuslar:
                pyautogui.hotkey(*tuslar)
                return f"Tuslar basildi: {'+'.join(tuslar)}"
            return "Tus belirtilmedi"
        except Exception as e:
            return f"Tus basilamadi: {e}"

    def _bilgisayar_bilgi(self, params):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('C:\\')
            return (
                f"CPU: %{cpu}, "
                f"RAM: %{ram.percent} ({ram.used // (1024**3)}/{ram.total // (1024**3)} GB), "
                f"Disk: %{disk.percent}"
            )
        except Exception as e:
            return f"Bilgi alinamadi: {e}"

    def _islem_listele(self, params):
        try:
            import psutil
            islemler = []
            for p in psutil.process_iter(['name', 'cpu_percent']):
                islemler.append(p.info)
            islemler.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            sonuc = []
            for p in islemler[:10]:
                sonuc.append(f"{p['name']} (CPU: %{p.get('cpu_percent', 0)})")
            return ", ".join(sonuc)
        except Exception as e:
            return f"Islem listesi alinamadi: {e}"

    def _islem_kapat(self, params):
        isim = params.get("isim", "")
        if isim:
            os.system(f'taskkill /f /im {isim}')
            return f"{isim} kapatildi"
        return "Islem adi bos"

    def _bilgisayar_kapat(self, params):
        os.system("shutdown /s /t 5")
        return "Bilgisayar 5 saniye icinde kapanacak"
