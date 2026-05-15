"""
JARVIS Tarzi Arayuz v7.3
- 3 Katmanli Akilli Mimari
- Kullanici tanima (ilk acilista isim sorar)
- Baslangic kontrolleri ayri thread'de (GUI donmuyor)
- Mikrofon otomatik baslar
- Non-blocking mimari
"""
import sys
import math
import time
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QSystemTrayIcon, QMenu,
    QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QSize, QPoint, QRectF
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QBrush, QLinearGradient,
    QRadialGradient, QIcon, QPixmap, QPainterPath, QAction
)


class Renkler:
    ANA = QColor(0, 200, 255)
    ANA_KOYU = QColor(0, 120, 180)
    ANA_ACIK = QColor(100, 220, 255)
    TURUNCU = QColor(255, 160, 0)
    YESIL = QColor(0, 255, 120)
    KIRMIZI = QColor(255, 60, 60)
    ARKAPLAN = QColor(10, 12, 20)
    PANEL = QColor(15, 20, 35)
    METIN = QColor(200, 220, 240)
    METIN_SOLUK = QColor(80, 100, 130)


class DalgaWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(80)
        self.aktif = False
        self.faz = 0.0
        self.genlik = 0.0
        self.hedef_genlik = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._guncelle)
        self.timer.start(30)

    def dinlemeye_basla(self):
        self.aktif = True
        self.hedef_genlik = 1.0

    def dinlemeyi_durdur(self):
        self.aktif = False
        self.hedef_genlik = 0.0

    def _guncelle(self):
        self.faz += 0.08
        if self.genlik < self.hedef_genlik:
            self.genlik = min(self.genlik + 0.05, self.hedef_genlik)
        elif self.genlik > self.hedef_genlik:
            self.genlik = max(self.genlik - 0.03, self.hedef_genlik)
        self.update()

    def paintEvent(self, event):
        if self.genlik < 0.01:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(Renkler.ANA_KOYU, 1)
            painter.setPen(pen)
            y_merkez = self.height() // 2
            painter.drawLine(0, y_merkez, self.width(), y_merkez)
            painter.end()
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        y_merkez = h / 2
        katmanlar = [
            (Renkler.ANA, 2.5, 1.0, 0.0),
            (Renkler.ANA_ACIK, 1.5, 0.6, 1.0),
            (Renkler.ANA_KOYU, 1.0, 0.8, 2.0),
        ]
        for renk, kalinlik, genlik_carpan, faz_kayma in katmanlar:
            renk_kopya = QColor(renk)
            renk_kopya.setAlpha(int(180 * self.genlik))
            pen = QPen(renk_kopya, kalinlik)
            painter.setPen(pen)
            path = QPainterPath()
            ilk = True
            for x in range(0, w + 1, 2):
                t = x / w
                dalga1 = math.sin(t * 4 * math.pi + self.faz + faz_kayma) * 0.5
                dalga2 = math.sin(t * 7 * math.pi + self.faz * 1.3 + faz_kayma) * 0.3
                dalga3 = math.sin(t * 11 * math.pi + self.faz * 0.7 + faz_kayma) * 0.2
                dalga = (dalga1 + dalga2 + dalga3) * genlik_carpan * self.genlik
                y = y_merkez + dalga * (h * 0.35)
                if ilk:
                    path.moveTo(x, y)
                    ilk = False
                else:
                    path.lineTo(x, y)
            painter.drawPath(path)
        painter.end()


class DaireGosterge(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(160, 160)
        self.durum = "bekliyor"
        self.aci = 0
        self.nabiz = 0.0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animasyon)
        self.timer.start(30)

    def durum_ayarla(self, durum):
        self.durum = durum

    def _animasyon(self):
        self.aci = (self.aci + 2) % 360
        self.nabiz = (math.sin(time.time() * 3) + 1) / 2
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w = self.width()
        h = self.height()
        merkez_x = w / 2
        merkez_y = h / 2
        yaricap = min(w, h) / 2 - 10
        renk_haritasi = {
            "bekliyor": Renkler.ANA_KOYU,
            "dinliyor": Renkler.ANA,
            "isliyor": Renkler.TURUNCU,
            "konusuyor": Renkler.YESIL,
            "hata": Renkler.KIRMIZI,
            "yukleniyor": Renkler.TURUNCU,
        }
        renk = renk_haritasi.get(self.durum, Renkler.ANA)
        pen = QPen(QColor(renk.red(), renk.green(), renk.blue(), 60), 2)
        painter.setPen(pen)
        painter.drawEllipse(QRectF(merkez_x - yaricap, merkez_y - yaricap, yaricap * 2, yaricap * 2))
        pen2 = QPen(renk, 3)
        painter.setPen(pen2)
        painter.drawArc(int(merkez_x - yaricap), int(merkez_y - yaricap), int(yaricap * 2), int(yaricap * 2), self.aci * 16, 90 * 16)
        ic_yaricap = yaricap * 0.7
        nabiz_r = ic_yaricap + self.nabiz * 5
        gradient = QRadialGradient(merkez_x, merkez_y, nabiz_r)
        gradient.setColorAt(0, QColor(renk.red(), renk.green(), renk.blue(), 30))
        gradient.setColorAt(0.7, QColor(renk.red(), renk.green(), renk.blue(), 15))
        gradient.setColorAt(1, QColor(0, 0, 0, 0))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(QRectF(merkez_x - nabiz_r, merkez_y - nabiz_r, nabiz_r * 2, nabiz_r * 2))
        pen3 = QPen(QColor(renk.red(), renk.green(), renk.blue(), 120), 1.5)
        painter.setPen(pen3)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QRectF(merkez_x - ic_yaricap, merkez_y - ic_yaricap, ic_yaricap * 2, ic_yaricap * 2))
        durum_metinleri = {
            "bekliyor": "HAZIR",
            "dinliyor": "DINLIYOR",
            "isliyor": "ISLIYOR",
            "konusuyor": "KONUSUYOR",
            "hata": "HATA",
            "yukleniyor": "YUKLENIYOR",
        }
        metin = durum_metinleri.get(self.durum, "---")
        font = QFont("Consolas", 11, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(renk)
        painter.drawText(QRectF(0, 0, w, h), Qt.AlignmentFlag.AlignCenter, metin)
        painter.end()


class LogPaneli(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Consolas", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: rgba(10, 15, 25, 200);
                color: #c8dce0;
                border: 1px solid rgba(0, 200, 255, 0.2);
                border-radius: 8px;
                padding: 10px;
            }
            QScrollBar:vertical {
                background: rgba(10, 15, 25, 150); width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 200, 255, 0.3); border-radius: 4px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

    def log_ekle(self, metin, tip="bilgi"):
        renk_haritasi = {
            "bilgi": "#c8dce0",
            "kullanici": "#00c8ff",
            "asistan": "#00ff78",
            "hata": "#ff3c3c",
            "sistem": "#ffa000",
            "soluk": "#506882",
        }
        renk = renk_haritasi.get(tip, "#c8dce0")
        zaman = time.strftime("%H:%M:%S")
        if tip == "kullanici":
            self.append(f'<span style="color:#506882;">[{zaman}]</span> <span style="color:{renk};">SEN:</span> <span style="color:#e0e8f0;">{metin}</span>')
        elif tip == "asistan":
            self.append(f'<span style="color:#506882;">[{zaman}]</span> <span style="color:{renk};">ASISTAN:</span> <span style="color:#e0e8f0;">{metin}</span>')
        else:
            self.append(f'<span style="color:#506882;">[{zaman}]</span> <span style="color:{renk};">{metin}</span>')
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())


class BaslangicThread(QThread):
    """Baslangic kontrollerini ayri thread'de yapar"""
    tamamlandi = pyqtSignal(bool, str)
    ilerleme = pyqtSignal(str)

    def __init__(self, asistan):
        super().__init__()
        self.asistan = asistan

    def run(self):
        try:
            self.ilerleme.emit("Guncelleme kontrol ediliyor...")
            try:
                self.asistan.guncelleyici.baslangicta_kontrol()
            except:
                pass

            ai_motor = self.asistan.config.get("ai_motor", "gemini")
            if ai_motor == "gemini":
                self.ilerleme.emit("Google Gemini AI kontrol ediliyor...")
                bagli, modeller = self.asistan.yapay_zeka.baglanti_kontrol()
                if not bagli:
                    self.ilerleme.emit("[!] Gemini baglantisi yok - sadece yerel komutlar")
                else:
                    self.ilerleme.emit("[OK] Gemini bagli!")

                # GERCEK Gemini testi
                self.ilerleme.emit("Gemini API test ediliyor...")
                test_ok, test_mesaj = self.asistan.yapay_zeka.gemini_test()
                if test_ok:
                    self.ilerleme.emit(f"[OK] {test_mesaj}")
                else:
                    self.ilerleme.emit(f"[!] {test_mesaj}")
                    self.ilerleme.emit("Yerel komutlar (184+) yine de calisir!")
            else:
                self.ilerleme.emit("Ollama baglantisi kontrol ediliyor...")
                bagli, modeller = self.asistan.yapay_zeka.baglanti_kontrol()
                if not bagli:
                    self.ilerleme.emit("[!] Ollama calismiyor - sadece yerel komutlar")

            self.ilerleme.emit("Mikrofon kontrol ediliyor...")
            mikrofonlar = self.asistan.ses_tanima.mikrofon_listele()
            if not mikrofonlar:
                self.tamamlandi.emit(False, "Mikrofon bulunamadi!")
                return

            motor = self.asistan.config.get("stt_motor", "google")
            if motor == "google":
                self.ilerleme.emit("Google Ses Tanima hazirlaniyor...")
            else:
                self.ilerleme.emit("Whisper modeli yukleniyor...")
            self.asistan.ses_tanima.modeli_yukle()

            # Kullanici tanima durumu
            if self.asistan.kullanici_adi:
                self.ilerleme.emit(f"Kullanici: {self.asistan.kullanici_adi}")
            else:
                self.ilerleme.emit("Ilk kullanim - adiniz sorulacak")
                self.asistan.isim_bekleniyor = True

            self.tamamlandi.emit(True, "Tum kontroller basarili! (v7.3)")

        except Exception as e:
            self.tamamlandi.emit(False, f"Hata: {str(e)}")


class AsistanThread(QThread):
    metin_algilandi = pyqtSignal(str)
    yanit_geldi = pyqtSignal(str)
    durum_degisti = pyqtSignal(str)
    aksiyon_yapildi = pyqtSignal(str)
    hata_olustu = pyqtSignal(str)

    def __init__(self, asistan):
        super().__init__()
        self.asistan = asistan
        self.calistir = True

    def run(self):
        self.asistan.ses_tanima.tekrar_baslat()

        # Karsilama mesaji
        if self.asistan.isim_bekleniyor:
            self.durum_degisti.emit("konusuyor")
            self.yanit_geldi.emit("Merhaba! Adini ogrenebilir miyim?")
            self.asistan.sesli_yanit.konus("Merhaba! Ben senin sesli asistaninim. Adini ogrenebilir miyim?")
            # Hoparlor yankisi mikrofona dusmesin diye bekle
            time.sleep(1.5)
        elif self.asistan.kullanici_adi:
            self.durum_degisti.emit("konusuyor")
            karsilama = f"Merhaba {self.asistan.kullanici_adi}! Seni dinliyorum."
            self.yanit_geldi.emit(karsilama)
            self.asistan.sesli_yanit.konus(karsilama)
            time.sleep(0.5)
        else:
            self.durum_degisti.emit("konusuyor")
            self.yanit_geldi.emit("Merhaba! Seni dinliyorum.")
            self.asistan.sesli_yanit.konus("Merhaba! Seni dinliyorum.")
            time.sleep(0.5)

        while self.calistir:
            try:
                self.durum_degisti.emit("dinliyor")
                metin = self.asistan.ses_tanima.dinle_ve_cevir()

                if not self.calistir:
                    break

                if metin:
                    # Isim bekleniyor mu?
                    if self.asistan.isim_bekleniyor:
                        self._isim_kaydet(metin)
                        continue

                    from yapay_zeka import turkce_normalize
                    metin_kucuk = turkce_normalize(metin.lower().strip())
                    cikis_komutlari = ["kapat kendini", "kendini kapat", "cikis", "gule gule"]
                    if any(k in metin_kucuk for k in cikis_komutlari):
                        self.yanit_geldi.emit("Gorusmek uzere!")
                        self.durum_degisti.emit("konusuyor")
                        self.asistan.sesli_yanit.konus("Gorusmek uzere!")
                        self.durum_degisti.emit("bekliyor")
                        self.calistir = False
                        break

                    self.metin_algilandi.emit(metin)
                    self._komut_islet(metin)
            except Exception as e:
                if self.calistir:
                    self.hata_olustu.emit(str(e))
                    self.durum_degisti.emit("hata")
                    import traceback
                    traceback.print_exc()
                    time.sleep(1)

    def _isim_kaydet(self, metin):
        """Ilk acilista isim kaydet - yankı ve gurultu filtreli"""
        isim = metin.strip()

        # Temizle: "benim adim Ahmet" -> "Ahmet"
        for kalip in ["benim adim", "adim", "ben", "benim ismim", "ismim"]:
            if kalip in isim.lower():
                isim = isim.lower().replace(kalip, "").strip()
                break
        isim = isim.strip().title()

        # Gurultu/yanki filtresi: isim en az 2 harf olmali ve
        # asistanin kendi sorusu olmamali (hoparlor yankisi)
        yanki_kelimeleri = ["merhaba", "asistan", "ogrenebilir", "yardimci",
                           "dinliyorum", "miyim", "hello", "assist", "help",
                           "nasil", "olabilirim", "senin", "sesli"]
        isim_kucuk = isim.lower()
        yanki_mi = any(k in isim_kucuk for k in yanki_kelimeleri)

        if isim and len(isim) >= 2 and not yanki_mi:
            # Sadece ilk kelimeyi al (isim genelde tek kelime)
            isim_parca = isim.split()[0] if " " in isim else isim
            self.asistan.hafiza.kullanici_adi_kaydet(isim_parca)
            self.asistan.kullanici_adi = isim_parca
            self.asistan.yapay_zeka.kullanici_adi = isim_parca
            self.asistan.isim_bekleniyor = False

            karsilama = f"Memnun oldum {isim_parca}! Sana nasil yardimci olabilirim?"
            self.metin_algilandi.emit(f"[Isim: {isim_parca}]")
            self.yanit_geldi.emit(karsilama)
            self.durum_degisti.emit("konusuyor")
            self.asistan.sesli_yanit.konus(karsilama)
            time.sleep(0.5)
        else:
            # Yanki veya gurultu - tekrar sor
            if yanki_mi:
                print(f"[!] Yanki algilandi, tekrar sorulacak: '{metin}'")
            self.yanit_geldi.emit("Adini net duyamadim. Sadece adini soyler misin?")
            self.durum_degisti.emit("konusuyor")
            self.asistan.sesli_yanit.konus("Adini net duyamadim. Sadece adini soyler misin?")
            time.sleep(1.0)

    def _komut_islet(self, metin):
        self.durum_degisti.emit("isliyor")
        baslangic = time.time()

        hafiza_ozeti = self.asistan.hafiza.hafiza_ozeti()
        yanit = self.asistan.yapay_zeka.komut_isle(metin, hafiza_ozeti)

        ai_sure = time.time() - baslangic

        if not yanit:
            self.yanit_geldi.emit("Anlayamadim, tekrar soyler misin?")
            self.durum_degisti.emit("dinliyor")
            return

        if yanit.get("soru_sor"):
            self.yanit_geldi.emit(yanit["soru_sor"])
            self.durum_degisti.emit("dinliyor")
            return

        # Isim degistirme komutu
        yanit_metni_kontrol = yanit.get("yanit", "")
        if yanit_metni_kontrol == "__ISIM_DEGISTIR__":
            self.asistan.isim_bekleniyor = True
            soru = "Tabii! Adini soyler misin?"
            self.yanit_geldi.emit(soru)
            self.durum_degisti.emit("konusuyor")
            self.asistan.sesli_yanit.konus(soru)
            self.durum_degisti.emit("dinliyor")
            return

        # Aksiyonlari isle
        aksiyonlar = yanit.get("aksiyonlar", [])
        tum_basarili = True
        for aksiyon in aksiyonlar:
            fonk = aksiyon.get("fonksiyon")
            params = aksiyon.get("parametreler", {})
            if fonk:
                basarili, sonuc = self.asistan.bilgisayar.calistir(fonk, params)
                if basarili:
                    self.aksiyon_yapildi.emit(f"{fonk}: {sonuc}")
                else:
                    tum_basarili = False
                    self.hata_olustu.emit(f"{fonk}: {sonuc}")

        # Hafiza islemleri
        tercih = yanit.get("tercih_kaydet")
        if tercih and isinstance(tercih, dict):
            for k, v in tercih.items():
                self.asistan.hafiza.tercih_kaydet(k, v)

        rutin = yanit.get("rutin_kaydet")
        if rutin and isinstance(rutin, dict):
            self.asistan.hafiza.rutin_kaydet(rutin.get("isim", ""), rutin.get("komutlar", []))

        ogrenme = yanit.get("ogren")
        if ogrenme and isinstance(ogrenme, dict):
            for k, v in ogrenme.items():
                self.asistan.hafiza.ogren(k, v)

        self.asistan.hafiza.gecmis_ekle(metin, str(aksiyonlar), tum_basarili)

        # Sesli yanit
        yanit_metni = yanit.get("yanit", "Tamam!")
        self.durum_degisti.emit("konusuyor")

        katman = "Yerel" if ai_sure < 0.05 else "AI"
        self.yanit_geldi.emit(f"{yanit_metni}  [{katman} {ai_sure:.1f}sn]")

        self.asistan.sesli_yanit.konus(yanit_metni)

        toplam = time.time() - baslangic
        print(f"[SURE] {katman}:{ai_sure:.1f}s Toplam:{toplam:.1f}s")

        self.durum_degisti.emit("dinliyor")

    def durdur(self):
        self.calistir = False
        self.asistan.ses_tanima.durdur()


class JarvisPencere(QMainWindow):
    def __init__(self, asistan):
        super().__init__()
        self.asistan = asistan
        self.asistan_thread = None
        self.baslangic_thread = None
        self._pencere_ayarla()
        self._arayuz_olustur()
        self._sistem_tepsisi_olustur()

    def _pencere_ayarla(self):
        self.setWindowTitle("SESLI AI ASISTAN")
        self.setMinimumSize(500, 650)
        self.resize(520, 700)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._surukle_pos = None

    def _arayuz_olustur(self):
        ana_widget = QWidget()
        self.setCentralWidget(ana_widget)
        ana_layout = QVBoxLayout(ana_widget)
        ana_layout.setContentsMargins(15, 15, 15, 15)
        ana_layout.setSpacing(0)

        self.panel = QFrame()
        self.panel.setStyleSheet("QFrame { background-color: rgba(10, 12, 20, 230); border: 1px solid rgba(0, 200, 255, 0.3); border-radius: 16px; }")
        panel_layout = QVBoxLayout(self.panel)
        panel_layout.setContentsMargins(20, 15, 20, 20)
        panel_layout.setSpacing(12)

        # Baslik bar
        baslik_bar = QHBoxLayout()
        baslik = QLabel("SESLI AI ASISTAN")
        baslik.setFont(QFont("Consolas", 14, QFont.Weight.Bold))
        baslik.setStyleSheet("color: #00c8ff; background: transparent; border: none;")
        baslik_bar.addWidget(baslik)
        baslik_bar.addStretch()
        surum_label = QLabel(f"v{self.asistan.config.get('surum', '7.0')}")
        surum_label.setFont(QFont("Consolas", 9))
        surum_label.setStyleSheet("color: #506882; background: transparent; border: none;")
        baslik_bar.addWidget(surum_label)

        btn_kucult = QPushButton("-")
        btn_kucult.setFixedSize(30, 30)
        btn_kucult.setStyleSheet(self._buton_stili("#506882"))
        btn_kucult.clicked.connect(self.showMinimized)
        baslik_bar.addWidget(btn_kucult)

        btn_kapat = QPushButton("X")
        btn_kapat.setFixedSize(30, 30)
        btn_kapat.setStyleSheet(self._buton_stili("#ff3c3c"))
        btn_kapat.clicked.connect(self._kapat)
        baslik_bar.addWidget(btn_kapat)
        panel_layout.addLayout(baslik_bar)

        # Ayirici
        ayirici = QFrame()
        ayirici.setFixedHeight(1)
        ayirici.setStyleSheet("background-color: rgba(0, 200, 255, 0.15); border: none;")
        panel_layout.addWidget(ayirici)

        # Daire gosterge
        gosterge_layout = QHBoxLayout()
        gosterge_layout.addStretch()
        self.daire = DaireGosterge()
        gosterge_layout.addWidget(self.daire)
        gosterge_layout.addStretch()
        panel_layout.addLayout(gosterge_layout)

        # Dalga animasyonu
        self.dalga = DalgaWidget()
        panel_layout.addWidget(self.dalga)

        # Durum label
        self.durum_label = QLabel("Baslatiliyor...")
        self.durum_label.setFont(QFont("Consolas", 10))
        self.durum_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.durum_label.setStyleSheet("color: #ffa000; background: transparent; border: none;")
        panel_layout.addWidget(self.durum_label)

        # Butonlar
        buton_layout = QHBoxLayout()
        buton_layout.setSpacing(10)

        self.btn_baslat = QPushButton("BASLATIYOR...")
        self.btn_baslat.setFixedHeight(40)
        self.btn_baslat.setFont(QFont("Consolas", 11, QFont.Weight.Bold))
        self.btn_baslat.setStyleSheet(self._ana_buton_stili("#ffa000"))
        self.btn_baslat.setEnabled(False)
        self.btn_baslat.clicked.connect(self._baslat_durdur)
        buton_layout.addWidget(self.btn_baslat)

        self.btn_sifirla = QPushButton("SIFIRLA")
        self.btn_sifirla.setFixedHeight(40)
        self.btn_sifirla.setFont(QFont("Consolas", 11))
        self.btn_sifirla.setStyleSheet(self._ana_buton_stili("#506882"))
        self.btn_sifirla.clicked.connect(self._sohbet_sifirla)
        buton_layout.addWidget(self.btn_sifirla)
        panel_layout.addLayout(buton_layout)

        # Log panel
        self.log = LogPaneli()
        self.log.setMinimumHeight(180)
        panel_layout.addWidget(self.log)

        # Istatistik
        istat_layout = QHBoxLayout()
        self.istat_label = QLabel("Komut: 0 | Basarili: 0")
        self.istat_label.setFont(QFont("Consolas", 8))
        self.istat_label.setStyleSheet("color: #506882; background: transparent; border: none;")
        istat_layout.addWidget(self.istat_label)
        istat_layout.addStretch()
        ai_motor = self.asistan.config.get("ai_motor", "gemini")
        if ai_motor == "gemini":
            model_adi = f"Gemini {self.asistan.config.get('gemini_model', 'flash')}"
        else:
            model_adi = self.asistan.config.get("ollama_model", "llama3")
        self.model_label = QLabel(f"Model: {model_adi}")
        self.model_label.setFont(QFont("Consolas", 8))
        self.model_label.setStyleSheet("color: #506882; background: transparent; border: none;")
        istat_layout.addWidget(self.model_label)
        panel_layout.addLayout(istat_layout)

        ana_layout.addWidget(self.panel)

        # Baslangic
        self.log.log_ekle("Sesli AI Asistan v7.3 baslatildi", "sistem")
        self.log.log_ekle("Sistem kontrolleri yapiliyor...", "soluk")
        self.daire.durum_ayarla("yukleniyor")

        # Otomatik baslat
        QTimer.singleShot(500, self._otomatik_baslat)

    def _buton_stili(self, renk):
        r = int(renk.lstrip('#')[0:2], 16)
        g = int(renk.lstrip('#')[2:4], 16)
        b = int(renk.lstrip('#')[4:6], 16)
        return f"""
            QPushButton {{ background: transparent; color: {renk}; border: 1px solid {renk}; border-radius: 6px; font-family: Consolas; font-size: 12px; font-weight: bold; }}
            QPushButton:hover {{ background: rgba({r}, {g}, {b}, 30); }}
        """

    def _ana_buton_stili(self, renk):
        r = int(renk.lstrip('#')[0:2], 16)
        g = int(renk.lstrip('#')[2:4], 16)
        b = int(renk.lstrip('#')[4:6], 16)
        return f"""
            QPushButton {{ background: rgba({r}, {g}, {b}, 25); color: {renk}; border: 1px solid {renk}; border-radius: 8px; }}
            QPushButton:hover {{ background: rgba({r}, {g}, {b}, 50); }}
            QPushButton:pressed {{ background: rgba({r}, {g}, {b}, 80); }}
        """

    def _sistem_tepsisi_olustur(self):
        self.tray = QSystemTrayIcon(self)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(Renkler.ANA))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        self.tray.setIcon(QIcon(pixmap))

        menu = QMenu()
        goster_action = QAction("Goster", self)
        goster_action.triggered.connect(self.show)
        menu.addAction(goster_action)
        kapat_action = QAction("Kapat", self)
        kapat_action.triggered.connect(self._kapat)
        menu.addAction(kapat_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_tiklandi)
        self.tray.show()

    def _tray_tiklandi(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            if self.isVisible():
                self.hide()
            else:
                self.show()
                self.activateWindow()

    def _otomatik_baslat(self):
        self.baslangic_thread = BaslangicThread(self.asistan)
        self.baslangic_thread.ilerleme.connect(self._baslangic_ilerleme)
        self.baslangic_thread.tamamlandi.connect(self._baslangic_tamamlandi)
        self.baslangic_thread.start()

    def _baslangic_ilerleme(self, mesaj):
        self.log.log_ekle(mesaj, "soluk")
        self.durum_label.setText(mesaj)

    def _baslangic_tamamlandi(self, basarili, mesaj):
        if basarili:
            self.log.log_ekle(mesaj, "sistem")

            # Mikrofon otomatik baslar - BASLAT butonu yok
            self.btn_baslat.setText("DURDUR")
            self.btn_baslat.setStyleSheet(self._ana_buton_stili("#ff3c3c"))
            self.btn_baslat.setEnabled(True)
            self.durum_label.setText("Seni dinliyorum...")
            self.durum_label.setStyleSheet("color: #00c8ff; background: transparent; border: none;")
            self.dalga.dinlemeye_basla()
            self.daire.durum_ayarla("dinliyor")

            self.asistan_thread = AsistanThread(self.asistan)
            self.asistan_thread.metin_algilandi.connect(self._metin_algilandi)
            self.asistan_thread.yanit_geldi.connect(self._yanit_geldi)
            self.asistan_thread.durum_degisti.connect(self._durum_degisti)
            self.asistan_thread.aksiyon_yapildi.connect(self._aksiyon_yapildi)
            self.asistan_thread.hata_olustu.connect(self._hata_olustu)
            self.asistan_thread.finished.connect(self._thread_bitti)
            self.asistan_thread.start()
        else:
            self.log.log_ekle(mesaj, "hata")
            self.daire.durum_ayarla("hata")
            self.durum_label.setText("Hata!")
            self.durum_label.setStyleSheet("color: #ff3c3c; background: transparent; border: none;")
            self.btn_baslat.setText("TEKRAR DENE")
            self.btn_baslat.setStyleSheet(self._ana_buton_stili("#ffa000"))
            self.btn_baslat.setEnabled(True)

    def _baslat_durdur(self):
        if self.asistan_thread and self.asistan_thread.isRunning():
            self._durdur()
        else:
            self._baslat()

    def _baslat(self):
        self.btn_baslat.setText("BASLATIYOR...")
        self.btn_baslat.setEnabled(False)
        self.daire.durum_ayarla("yukleniyor")
        self._otomatik_baslat()

    def _durdur(self):
        if self.asistan_thread:
            self.asistan_thread.durdur()
        self.btn_baslat.setText("BASLAT")
        self.btn_baslat.setStyleSheet(self._ana_buton_stili("#00c8ff"))
        self.durum_label.setText("Durduruldu")
        self.durum_label.setStyleSheet("color: #506882; background: transparent; border: none;")
        self.dalga.dinlemeyi_durdur()
        self.daire.durum_ayarla("bekliyor")
        self.log.log_ekle("Dinleme durduruldu.", "sistem")

    def _sohbet_sifirla(self):
        self.asistan.yapay_zeka.sohbet_sifirla()
        self.log.log_ekle("Sohbet gecmisi sifirlandi.", "sistem")

    def _metin_algilandi(self, metin):
        self.log.log_ekle(metin, "kullanici")

    def _yanit_geldi(self, yanit):
        self.log.log_ekle(yanit, "asistan")

    def _durum_degisti(self, durum):
        self.daire.durum_ayarla(durum)
        metinler = {
            "dinliyor": "Seni dinliyorum...",
            "isliyor": "Komut isleniyor...",
            "konusuyor": "Konusuyor...",
            "bekliyor": "Hazir",
            "hata": "Hata olustu!",
        }
        self.durum_label.setText(metinler.get(durum, ""))

        if durum == "dinliyor":
            self.durum_label.setStyleSheet("color: #00c8ff; background: transparent; border: none;")
            self.dalga.dinlemeye_basla()
        elif durum == "konusuyor":
            self.durum_label.setStyleSheet("color: #00ff78; background: transparent; border: none;")
            self.dalga.dinlemeyi_durdur()
        elif durum == "isliyor":
            self.durum_label.setStyleSheet("color: #ffa000; background: transparent; border: none;")
            self.dalga.dinlemeyi_durdur()
        else:
            self.dalga.dinlemeyi_durdur()

        istat = self.asistan.hafiza.istatistikler()
        self.istat_label.setText(f"Komut: {istat.get('toplam_komut', 0)} | Basarili: {istat.get('basarili_komut', 0)}")

    def _aksiyon_yapildi(self, mesaj):
        self.log.log_ekle(mesaj, "bilgi")

    def _hata_olustu(self, mesaj):
        self.log.log_ekle(mesaj, "hata")

    def _thread_bitti(self):
        self._durdur()

    def _kapat(self):
        if self.asistan_thread and self.asistan_thread.isRunning():
            self.asistan_thread.durdur()
            self.asistan_thread.wait(3000)
        self.tray.hide()
        QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._surukle_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._surukle_pos and event.buttons() == Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._surukle_pos)

    def mouseReleaseEvent(self, event):
        self._surukle_pos = None

    def closeEvent(self, event):
        event.ignore()
        self.hide()
