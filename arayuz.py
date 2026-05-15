"""
ATLAS - Arayüz
===============
ATLAS sesli asistan GUI — JARVIS tarzı modern arayüz.
PyQt6 tabanlı, karanlık tema, beyin durumu göstergeleri.
"""

import sys
import threading
import time
import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor, QPalette, QLinearGradient, QPainter, QFontDatabase

logger = logging.getLogger("ATLAS.arayuz")

# ============================================================
# RENKLER
# ============================================================

RENKLER = {
    "arkaplan": "#0a0a0f",
    "panel": "#12121a",
    "panel_border": "#1a1a2e",
    "metin": "#e0e0e0",
    "metin_soluk": "#888899",
    "vurgu": "#00c8ff",
    "vurgu_koyu": "#0088aa",
    "basari": "#00ff88",
    "uyari": "#ffaa00",
    "hata": "#ff4444",
    "kullanici": "#00c8ff",
    "asistan": "#00ff88",
}


# ============================================================
# SİNYAL KÖPRÜSÜn(Thread → GUI iletişimi)
# ============================================================

class GuiSinyalleri(QObject):
    """Thread-safe GUI güncellemeleri için sinyal köprüsü"""
    mesaj_ekle = pyqtSignal(str, str)       # (rol, mesaj)
    durum_guncelle = pyqtSignal(str)         # durum metni
    mod_guncelle = pyqtSignal(str)           # dikkat modu
    bellek_guncelle = pyqtSignal(dict)       # bellek durumu
    hata_goster = pyqtSignal(str)            # hata mesajı
    surum_goster = pyqtSignal(str)           # sürüm bilgisi
    duygu_guncelle = pyqtSignal(str)         # duygu durumu


# ============================================================
# ANA PENCERE
# ============================================================

class AtlasArayuz(QMainWindow):
    """ATLAS Ana Pencere — JARVIS tarzı arayüz"""

    def __init__(self):
        super().__init__()
        self.sinyaller = GuiSinyalleri()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Arayüzü oluştur"""
        self.setWindowTitle("ATLAS — Sesli AI Asistan")
        self.setMinimumSize(700, 500)
        self.resize(800, 600)

        # Ana widget
        merkez = QWidget()
        self.setCentralWidget(merkez)
        ana_layout = QVBoxLayout(merkez)
        ana_layout.setContentsMargins(0, 0, 0, 0)
        ana_layout.setSpacing(0)

        # Stil
        self._stil_uygula()

        # ── Üst Bar ──
        ust_bar = QFrame()
        ust_bar.setFixedHeight(56)
        ust_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['panel']};
                border-bottom: 1px solid {RENKLER['panel_border']};
            }}
        """)
        ust_layout = QHBoxLayout(ust_bar)
        ust_layout.setContentsMargins(20, 0, 20, 0)

        # Logo / İsim
        logo_label = QLabel("⬡ ATLAS")
        logo_label.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        logo_label.setStyleSheet(f"color: {RENKLER['vurgu']}; letter-spacing: 3px;")
        ust_layout.addWidget(logo_label)

        ust_layout.addStretch()

        # Sürüm
        self.surum_label = QLabel("v8.0")
        self.surum_label.setFont(QFont("Consolas", 9))
        self.surum_label.setStyleSheet(f"color: {RENKLER['metin_soluk']};")
        ust_layout.addWidget(self.surum_label)

        ana_layout.addWidget(ust_bar)

        # ── Orta Alan ──
        orta = QWidget()
        orta_layout = QHBoxLayout(orta)
        orta_layout.setContentsMargins(0, 0, 0, 0)
        orta_layout.setSpacing(0)

        # Sol panel — Konuşma
        sol_panel = QFrame()
        sol_panel.setStyleSheet(f"background-color: {RENKLER['arkaplan']};")
        sol_layout = QVBoxLayout(sol_panel)
        sol_layout.setContentsMargins(16, 12, 8, 12)

        # Konuşma alanı
        self.konusma_alani = QTextEdit()
        self.konusma_alani.setReadOnly(True)
        self.konusma_alani.setFont(QFont("Segoe UI", 10))
        self.konusma_alani.setStyleSheet(f"""
            QTextEdit {{
                background-color: {RENKLER['arkaplan']};
                color: {RENKLER['metin']};
                border: none;
                padding: 8px;
                selection-background-color: {RENKLER['vurgu_koyu']};
            }}
            QScrollBar:vertical {{
                background: {RENKLER['panel']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {RENKLER['panel_border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        sol_layout.addWidget(self.konusma_alani)

        orta_layout.addWidget(sol_panel, stretch=3)

        # Sağ panel — Durum
        sag_panel = QFrame()
        sag_panel.setFixedWidth(220)
        sag_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['panel']};
                border-left: 1px solid {RENKLER['panel_border']};
            }}
        """)
        sag_layout = QVBoxLayout(sag_panel)
        sag_layout.setContentsMargins(16, 16, 16, 16)
        sag_layout.setSpacing(12)

        # Beyin durumu başlığı
        beyin_baslik = QLabel("BEYİN DURUMU")
        beyin_baslik.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
        beyin_baslik.setStyleSheet(f"color: {RENKLER['vurgu']}; letter-spacing: 2px;")
        sag_layout.addWidget(beyin_baslik)

        # Dikkat modu
        self.mod_label = self._durum_karti_olustur("DİKKAT", "Başlatılıyor...")
        sag_layout.addWidget(self.mod_label)

        # Duygu
        self.duygu_label = self._durum_karti_olustur("DUYGU", "—")
        sag_layout.addWidget(self.duygu_label)

        # Hafıza
        self.hafiza_label = self._durum_karti_olustur("HAFIZA", "0 kayıt")
        sag_layout.addWidget(self.hafiza_label)

        # Sistem 1/2
        self.sistem_label = self._durum_karti_olustur("KARAR", "Hazır")
        sag_layout.addWidget(self.sistem_label)

        sag_layout.addStretch()

        # Saat
        self.saat_label = QLabel("")
        self.saat_label.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        self.saat_label.setStyleSheet(f"color: {RENKLER['vurgu']};")
        self.saat_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sag_layout.addWidget(self.saat_label)

        # Tarih
        self.tarih_label = QLabel("")
        self.tarih_label.setFont(QFont("Consolas", 9))
        self.tarih_label.setStyleSheet(f"color: {RENKLER['metin_soluk']};")
        self.tarih_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sag_layout.addWidget(self.tarih_label)

        orta_layout.addWidget(sag_panel)
        ana_layout.addWidget(orta, stretch=1)

        # ── Alt Bar ──
        alt_bar = QFrame()
        alt_bar.setFixedHeight(40)
        alt_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['panel']};
                border-top: 1px solid {RENKLER['panel_border']};
            }}
        """)
        alt_layout = QHBoxLayout(alt_bar)
        alt_layout.setContentsMargins(20, 0, 20, 0)

        # Durum göstergesi
        self.durum_nokta = QLabel("●")
        self.durum_nokta.setFont(QFont("Segoe UI", 10))
        self.durum_nokta.setStyleSheet(f"color: {RENKLER['basari']};")
        alt_layout.addWidget(self.durum_nokta)

        self.durum_label = QLabel("Başlatılıyor...")
        self.durum_label.setFont(QFont("Segoe UI", 9))
        self.durum_label.setStyleSheet(f"color: {RENKLER['metin_soluk']};")
        alt_layout.addWidget(self.durum_label)

        alt_layout.addStretch()

        ana_layout.addWidget(alt_bar)

        # Saat timer
        self._saat_timer = QTimer()
        self._saat_timer.timeout.connect(self._saat_guncelle)
        self._saat_timer.start(1000)
        self._saat_guncelle()

    def _durum_karti_olustur(self, baslik, deger):
        """Sağ paneldeki durum kartı"""
        kart = QFrame()
        kart.setStyleSheet(f"""
            QFrame {{
                background-color: {RENKLER['arkaplan']};
                border: 1px solid {RENKLER['panel_border']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        layout = QVBoxLayout(kart)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(2)

        baslik_l = QLabel(baslik)
        baslik_l.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        baslik_l.setStyleSheet(f"color: {RENKLER['metin_soluk']}; letter-spacing: 1px; border: none;")
        layout.addWidget(baslik_l)

        deger_l = QLabel(deger)
        deger_l.setObjectName("deger")
        deger_l.setFont(QFont("Segoe UI", 10))
        deger_l.setStyleSheet(f"color: {RENKLER['metin']}; border: none;")
        layout.addWidget(deger_l)

        return kart

    def _kart_deger_guncelle(self, kart, yeni_deger):
        """Durum kartının değerini güncelle"""
        deger_label = kart.findChild(QLabel, "deger")
        if deger_label:
            deger_label.setText(yeni_deger)

    def _stil_uygula(self):
        """Global stil"""
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {RENKLER['arkaplan']};
            }}
            QWidget {{
                background-color: transparent;
                color: {RENKLER['metin']};
            }}
        """)

    def _connect_signals(self):
        """Sinyalleri bağla"""
        self.sinyaller.mesaj_ekle.connect(self._mesaj_ekle)
        self.sinyaller.durum_guncelle.connect(self._durum_guncelle)
        self.sinyaller.mod_guncelle.connect(self._mod_guncelle)
        self.sinyaller.bellek_guncelle.connect(self._bellek_guncelle)
        self.sinyaller.hata_goster.connect(self._hata_goster)
        self.sinyaller.surum_goster.connect(self._surum_goster)
        self.sinyaller.duygu_guncelle.connect(self._duygu_guncelle)

    def _saat_guncelle(self):
        """Saat ve tarihi güncelle"""
        simdi = datetime.now()
        self.saat_label.setText(simdi.strftime("%H:%M"))

        gunler = {0:"Pzt", 1:"Sal", 2:"Çar", 3:"Per", 4:"Cum", 5:"Cmt", 6:"Paz"}
        aylar = {1:"Oca", 2:"Şub", 3:"Mar", 4:"Nis", 5:"May", 6:"Haz",
                 7:"Tem", 8:"Ağu", 9:"Eyl", 10:"Eki", 11:"Kas", 12:"Ara"}
        gun = gunler.get(simdi.weekday(), "")
        ay = aylar.get(simdi.month, "")
        self.tarih_label.setText(f"{gun}, {simdi.day} {ay}")

    # ── Sinyal Slotları ──

    def _mesaj_ekle(self, rol, mesaj):
        """Konuşma alanına mesaj ekle"""
        zaman = datetime.now().strftime("%H:%M")

        if rol == "kullanici":
            renk = RENKLER['kullanici']
            ikon = "👤"
            isim = "SEN"
        elif rol == "asistan":
            renk = RENKLER['asistan']
            ikon = "⬡"
            isim = "ATLAS"
        elif rol == "sistem":
            renk = RENKLER['metin_soluk']
            ikon = "⚙️"
            isim = "SİSTEM"
        else:
            renk = RENKLER['metin']
            ikon = ""
            isim = rol

        html = f"""
        <div style="margin: 4px 0; padding: 4px 0;">
            <span style="color: {RENKLER['metin_soluk']}; font-size: 9px; font-family: Consolas;">{zaman}</span>
            <span style="color: {renk}; font-weight: bold;"> {ikon} {isim}:</span>
            <span style="color: {RENKLER['metin']};">{mesaj}</span>
        </div>
        """
        self.konusma_alani.append(html)

        # Otomatik scroll
        sb = self.konusma_alani.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _durum_guncelle(self, durum):
        """Alt bar durum metni"""
        self.durum_label.setText(durum)

        # Durum noktası rengi
        if "hata" in durum.lower() or "bağlantı" in durum.lower():
            self.durum_nokta.setStyleSheet(f"color: {RENKLER['hata']};")
        elif "dinl" in durum.lower() or "bekl" in durum.lower():
            self.durum_nokta.setStyleSheet(f"color: {RENKLER['basari']};")
        elif "düşün" in durum.lower() or "oluştur" in durum.lower():
            self.durum_nokta.setStyleSheet(f"color: {RENKLER['uyari']};")
        else:
            self.durum_nokta.setStyleSheet(f"color: {RENKLER['vurgu']};")

    def _mod_guncelle(self, mod):
        """Dikkat modu kartını güncelle"""
        mod_metinleri = {
            "pasif": "🔇 Pasif",
            "aktif": "🎙️ Aktif Dinleme",
            "isim": "👤 İsim Öğrenme",
            "mesgul": "💭 Düşünüyor",
        }
        self._kart_deger_guncelle(self.mod_label, mod_metinleri.get(mod, mod))

    def _bellek_guncelle(self, durum):
        """Hafıza kartını güncelle"""
        toplam = durum.get("toplam_etkilesim", 0)
        calisma = durum.get("calisma_bellegi", 0)
        self._kart_deger_guncelle(
            self.hafiza_label,
            f"💬 {calisma}/7 aktif | 📊 {toplam} toplam"
        )

    def _duygu_guncelle(self, duygu):
        """Duygu kartını güncelle"""
        duygu_emojileri = {
            "mutlu": "😊 Mutlu", "uzgun": "😔 Üzgün",
            "sinirli": "😤 Sinirli", "merakli": "🤔 Meraklı",
            "aceleci": "⚡ Aceleci", "notr": "😐 Nötr",
        }
        self._kart_deger_guncelle(
            self.duygu_label,
            duygu_emojileri.get(duygu, f"❓ {duygu}")
        )

    def _hata_goster(self, hata):
        """Hata mesajı göster"""
        self._mesaj_ekle("sistem", f"⚠️ {hata}")

    def _surum_goster(self, surum):
        """Sürüm bilgisi güncelle"""
        self.surum_label.setText(f"v{surum}")
