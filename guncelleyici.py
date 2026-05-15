"""
Otomatik Guncelleme Modulu v6.0
- GitHub'dan otomatik guncelleme kontrolu
- Dosya bazli guncelleme (sadece degisen dosyalar indirilir)
- Yedekleme + geri alma destegi
"""
import json
import os
import sys
import shutil
import urllib.request
import hashlib
import time


class Guncelleyici:
    def __init__(self, config):
        self.surum = config.get("surum", "6.0")
        self.repo = config.get("guncelleme_repo", "")
        self.guncelleme_url = config.get("guncelleme_url", "")
        self.otomatik_guncelle = config.get("otomatik_guncelle", True)
        self.uygulama_klasoru = os.path.dirname(os.path.abspath(__file__))
        self.yedek_klasoru = os.path.join(self.uygulama_klasoru, "_yedek")

    def baslangicta_kontrol(self):
        """Baslangicta guncelleme kontrolu yap"""
        print("[*] Guncelleme kontrol ediliyor...")

        # 1) GitHub repo kontrolu
        if self.repo:
            self._github_kontrol()
            return

        # 2) Direkt URL kontrolu
        if self.guncelleme_url:
            self._url_kontrol()
            return

        # 3) Repo/URL yoksa atla
        print("[!] Guncelleme deposu ayarlanmamis (opsiyonel)")

    def _github_kontrol(self):
        """GitHub releases'tan guncelleme kontrolu"""
        try:
            url = f"https://api.github.com/repos/{self.repo}/releases/latest"
            req = urllib.request.Request(url, headers={"User-Agent": "SesliAsistan/6.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                son_surum = data.get("tag_name", "").lstrip("v")

                if not son_surum:
                    return

                if self._surum_karsilastir(son_surum, self.surum) > 0:
                    print(f"\n{'='*50}")
                    print(f"  YENI SURUM MEVCUT: v{son_surum}")
                    print(f"  Mevcut surum: v{self.surum}")
                    print(f"{'='*50}")

                    if self.otomatik_guncelle:
                        # Otomatik guncelle
                        assets = data.get("assets", [])
                        zip_asset = None
                        for asset in assets:
                            if asset["name"].endswith(".zip"):
                                zip_asset = asset
                                break

                        if zip_asset:
                            print(f"[*] Otomatik guncelleme indiriliyor...")
                            self._indir_ve_guncelle(zip_asset["browser_download_url"])
                        else:
                            print(f"    Manuel indirme: {data.get('html_url', '')}")
                    else:
                        print(f"    Indirmek icin: {data.get('html_url', '')}")
                        print(f"    Otomatik guncelleme icin config.json'da")
                        print(f"    'otomatik_guncelle': true yapin")
                else:
                    print(f"[OK] Guncel surum kullaniliyor (v{self.surum})")

        except urllib.error.URLError:
            print("[!] Guncelleme sunucusuna ulasilamadi (internet?)")
        except Exception as e:
            print(f"[!] Guncelleme kontrolu basarisiz: {e}")

    def _url_kontrol(self):
        """Direkt URL'den versiyon kontrolu"""
        try:
            req = urllib.request.Request(
                self.guncelleme_url,
                headers={"User-Agent": "SesliAsistan/6.0"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                son_surum = data.get("surum", "")
                if son_surum and self._surum_karsilastir(son_surum, self.surum) > 0:
                    print(f"[!] Yeni surum mevcut: v{son_surum}")
                    indirme_url = data.get("indirme_url", "")
                    if indirme_url and self.otomatik_guncelle:
                        self._indir_ve_guncelle(indirme_url)
                    elif indirme_url:
                        print(f"    Indirme: {indirme_url}")
                else:
                    print(f"[OK] Guncel surum (v{self.surum})")
        except:
            pass

    def _indir_ve_guncelle(self, url):
        """ZIP dosyasini indir ve guncelle"""
        try:
            import zipfile
            import tempfile

            # Indir
            gecici = os.path.join(tempfile.gettempdir(), "sesli-asistan-update.zip")
            print(f"[*] Indiriliyor: {url[:60]}...")
            urllib.request.urlretrieve(url, gecici)
            print(f"[OK] Indirildi!")

            # Yedekle
            self._yedekle()

            # Cikar
            print("[*] Dosyalar guncelleniyor...")
            with zipfile.ZipFile(gecici, 'r') as zf:
                # ZIP icindeki dosyalari bul
                dosyalar = [f for f in zf.namelist()
                           if f.endswith(('.py', '.bat', '.md', '.txt'))
                           and not f.startswith('__')
                           and '/' not in f]  # sadece kok dizin

                guncellenen = 0
                for dosya in dosyalar:
                    # config.json ve hafiza.json'u GUNCELLEME
                    if dosya in ['config.json', 'hafiza.json']:
                        continue
                    hedef = os.path.join(self.uygulama_klasoru, dosya)
                    icerik = zf.read(dosya)
                    # Sadece degismis dosyalari guncelle
                    if os.path.exists(hedef):
                        mevcut = open(hedef, 'rb').read()
                        if mevcut == icerik:
                            continue
                    with open(hedef, 'wb') as f:
                        f.write(icerik)
                    guncellenen += 1
                    print(f"   [+] {dosya}")

            # Temizle
            try:
                os.remove(gecici)
            except:
                pass

            if guncellenen > 0:
                # config.json'daki surum numarasini guncelle
                try:
                    config_yolu = os.path.join(self.uygulama_klasoru, "config.json")
                    with open(config_yolu, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    # ZIP icindeki config'den surum al
                    if "config.json" in zf.namelist():
                        yeni_config = json.loads(zf.read("config.json").decode("utf-8"))
                        yeni_surum = yeni_config.get("surum", "")
                        if yeni_surum:
                            config["surum"] = yeni_surum
                            with open(config_yolu, "w", encoding="utf-8") as f:
                                json.dump(config, f, ensure_ascii=False, indent=4)
                            print(f"   [+] Surum guncellendi: v{yeni_surum}")
                except Exception as e2:
                    print(f"   [!] Surum guncelleme hatasi: {e2}")

                print(f"\n[OK] {guncellenen} dosya guncellendi!")
                print("[!] Degisikliklerin aktif olmasi icin programi yeniden baslatin.")
            else:
                print("[OK] Tum dosyalar zaten guncel.")

        except Exception as e:
            print(f"[HATA] Guncelleme basarisiz: {e}")
            self._geri_al()

    def _yedekle(self):
        """Mevcut dosyalari yedekle"""
        try:
            os.makedirs(self.yedek_klasoru, exist_ok=True)
            for dosya in os.listdir(self.uygulama_klasoru):
                if dosya.endswith('.py') and dosya != '__pycache__':
                    kaynak = os.path.join(self.uygulama_klasoru, dosya)
                    hedef = os.path.join(self.yedek_klasoru, dosya)
                    shutil.copy2(kaynak, hedef)
        except Exception as e:
            print(f"[!] Yedekleme hatasi: {e}")

    def _geri_al(self):
        """Yedekten geri al"""
        if not os.path.exists(self.yedek_klasoru):
            return
        try:
            print("[*] Yedekten geri aliniyor...")
            for dosya in os.listdir(self.yedek_klasoru):
                kaynak = os.path.join(self.yedek_klasoru, dosya)
                hedef = os.path.join(self.uygulama_klasoru, dosya)
                shutil.copy2(kaynak, hedef)
            print("[OK] Geri alindi!")
        except Exception as e:
            print(f"[HATA] Geri alma basarisiz: {e}")

    def _surum_karsilastir(self, a, b):
        """Surum karsilastir: a > b ise 1, esit 0, kucuk -1"""
        try:
            pa = [int(x) for x in a.split(".")]
            pb = [int(x) for x in b.split(".")]
            # Uzunluk esitle
            while len(pa) < len(pb):
                pa.append(0)
            while len(pb) < len(pa):
                pb.append(0)
            for i in range(len(pa)):
                if pa[i] > pb[i]:
                    return 1
                elif pa[i] < pb[i]:
                    return -1
            return 0
        except:
            return 0
