"""
ATLAS - AURA/JARVIS Arayüz
===========================
AURA tarzı organik parlayan küre animasyonu,
sol navigasyon menüsü, sohbet paneli, dalga formu.
PyQt6 tabanlı futuristik GUI.
"""

import math
import random
import sys
import time
import os
import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QRectF, QPointF, QSize
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QRadialGradient, QPixmap, QIcon,
    QPainterPath
)

logger = logging.getLogger("ATLAS.arayuz")


# ============================================================
# RENK PALETİ
# ============================================================

C = {
    "bg":        "#06091a",
    "bg2":       "#0a0f22",
    "sidebar":   "#080c1e",
    "panel":     "#0c1228",
    "border":    "#12203a",
    "border_hi": "#1a3055",
    "cyan":      "#00d4ff",
    "cyan2":     "#00b8e6",
    "cyan_dim":  "#006080",
    "cyan_glow": "#0090bb",
    "green":     "#00ff88",
    "orange":    "#ff8800",
    "red":       "#ff3333",
    "text":      "#c0d8e8",
    "text_hi":   "#e0f0ff",
    "dim":       "#4a6078",
    "menu_active": "#0d1a35",
}


# ============================================================
# ORGANİK KÜRE WİDGET — AURA tarzı parlayan animasyon
# ============================================================

class OrganikKureWidget(QWidget):
    """
    AURA tarzı organik parlayan küre animasyonu.
    Katmanlı deformasyonlu halkalar, çiçek yaprakları,
    parlayan merkez, parçacıklar, ses dalgası barları.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 280)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._angle = 0.0
        self._pulse = 0.0
        self._mod = "pasif"
        self._durum_text = "Başlatılıyor..."

        self._hizlar = {
            "pasif":  {"donus": 0.15, "nabiz": 1.0},
            "aktif":  {"donus": 0.6,  "nabiz": 2.0},
            "isim":   {"donus": 0.4,  "nabiz": 1.5},
            "mesgul": {"donus": 1.2,  "nabiz": 3.0},
        }

        self._wave_bars = [0.0] * 20
        self._wave_hedef = [0.0] * 20

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)

    def set_mod(self, mod):
        self._mod = mod

    def set_durum(self, text):
        self._durum_text = text

    def _animate(self):
        hiz = self._hizlar.get(self._mod, self._hizlar["pasif"])
        self._angle = (self._angle + hiz["donus"]) % 360
        self._pulse = (self._pulse + hiz["nabiz"]) % 360

        if self._mod in ("aktif", "isim"):
            self._wave_hedef = [random.uniform(0.1, 0.9) for _ in range(20)]
        elif self._mod == "mesgul":
            t = time.time()
            self._wave_hedef = [
                0.2 + 0.6 * abs(math.sin(t * 3.5 + i * 0.4))
                for i in range(20)
            ]
        else:
            t = time.time()
            self._wave_hedef = [
                0.03 + 0.04 * abs(math.sin(t * 0.4 + i * 0.3))
                for i in range(20)
            ]

        for i in range(20):
            self._wave_bars[i] += (self._wave_hedef[i] - self._wave_bars[i]) * 0.16

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 - 15
        max_r = min(w, h) / 2 - 30

        pv = (math.sin(math.radians(self._pulse)) + 1) / 2

        # Mod renkleri
        if self._mod == "mesgul":
            hue = (0, 180, 255)
            hue_bright = (100, 220, 255)
        else:
            hue = (0, 212, 255)
            hue_bright = (140, 240, 255)

        def rc(r, g, b, a):
            return QColor(r, g, b, int(a))

        # ── 1. Dış parıltı ──
        glow = QRadialGradient(cx, cy, max_r * 1.3)
        glow.setColorAt(0, rc(*hue, 25 + 15 * pv))
        glow.setColorAt(0.4, rc(*hue, 8))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), glow)

        # ── 2. Organik halkalar (5 katman, dıştan içe) ──
        for layer in range(5, 0, -1):
            r = max_r * (0.18 + layer * 0.14)
            speed_mult = 0.3 + layer * 0.06
            direction = 1 if layer % 2 == 0 else -1
            rot = self._angle * speed_mult * direction

            deform_base = 0.04 + layer * 0.025
            path = QPainterPath()
            n = 80
            for s in range(n + 1):
                theta = s * 2 * math.pi / n
                d = 1.0
                d += deform_base * math.sin(3 * theta + rot * 0.05)
                d += (deform_base * 0.7) * math.sin(5 * theta - rot * 0.035 + layer)
                d += (deform_base * 0.4) * math.sin(2 * theta + rot * 0.02)
                rx = r * d
                x = cx + rx * math.cos(theta)
                y = cy + rx * math.sin(theta)
                if s == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            path.closeSubpath()

            a_fill = int(18 + (5 - layer) * 8 + 5 * pv)
            a_stroke = int(35 + (5 - layer) * 14 + 8 * pv)
            p.setPen(QPen(rc(*hue, a_stroke), 1.3))
            p.setBrush(rc(*hue, a_fill))
            p.drawPath(path)

        # ── 3. Çiçek yaprakları (7 adet dönen elips) ──
        for i in range(7):
            p.save()
            p.translate(cx, cy)
            angle = self._angle * 0.35 + i * (360 / 7)
            p.rotate(angle)

            pw = max_r * 0.22
            ph = max_r * 0.58
            petal_alpha = int(22 + 10 * pv)

            pg = QRadialGradient(0, 0, ph)
            pg.setColorAt(0, rc(*hue_bright, petal_alpha + 5))
            pg.setColorAt(0.5, rc(*hue, petal_alpha))
            pg.setColorAt(1, QColor(0, 0, 0, 0))

            p.setPen(QPen(rc(*hue, int(petal_alpha * 0.6)), 0.8))
            p.setBrush(pg)
            p.drawEllipse(QRectF(-pw / 2, -ph / 2, pw, ph))
            p.restore()

        # ── 4. Parlayan merkez ──
        cr = max_r * 0.22
        ca = int(140 + 80 * pv)
        cg = QRadialGradient(cx, cy, cr)
        cg.setColorAt(0, rc(200, 255, 255, ca))
        cg.setColorAt(0.3, rc(*hue_bright, int(ca * 0.7)))
        cg.setColorAt(0.7, rc(*hue, int(ca * 0.3)))
        cg.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cg)
        p.drawEllipse(QPointF(cx, cy), cr, cr)

        # ── 5. Parçacık noktaları ──
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(24):
            seed_r = max_r * (0.45 + 0.45 * abs(math.sin(i * 1.37 + self._pulse * 0.008)))
            seed_a = math.radians(i * 15 + self._angle * 0.08)
            px = cx + seed_r * math.cos(seed_a)
            py = cy + seed_r * math.sin(seed_a)
            dot_a = int(50 + 70 * abs(math.sin(self._pulse * 0.015 + i * 0.8)))
            dot_r = 1.5 + 1.0 * abs(math.sin(self._pulse * 0.01 + i * 1.2))
            p.setBrush(rc(*hue_bright, dot_a))
            p.drawEllipse(QPointF(px, py), dot_r, dot_r)

        # ── 6. ATLAS yazısı ──
        p.setPen(QColor(230, 248, 255, int(210 + 30 * pv)))
        fa = QFont("Consolas", 13, QFont.Weight.Bold)
        fa.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5)
        p.setFont(fa)
        p.drawText(QRectF(cx - 90, cy - 10, 180, 24), Qt.AlignmentFlag.AlignCenter, "ATLAS")

        # ── 7. Durum metni ──
        p.setPen(rc(*hue, int(150 + 60 * pv)))
        fd = QFont("Segoe UI", 9)
        p.setFont(fd)
        p.drawText(
            QRectF(cx - 130, cy + 16, 260, 20),
            Qt.AlignmentFlag.AlignCenter,
            self._durum_text
        )

        # ── 8. Dalga formu barları (alt) ──
        wave_y = h - 35
        total_w = w * 0.85
        bar_gap = total_w / (len(self._wave_bars) + 1)
        x_start = (w - total_w) / 2

        for i in range(len(self._wave_bars)):
            bar_h = self._wave_bars[i] * 28
            bx = x_start + (i + 0.5) * bar_gap
            by = wave_y - bar_h / 2
            ba = int(60 + 130 * self._wave_bars[i])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(rc(*hue, ba))
            bw = bar_gap * 0.4
            p.drawRoundedRect(QRectF(bx - bw / 2, by, bw, bar_h), 2, 2)

        # Dalga çizgisi (ince bağlantı)
        if len(self._wave_bars) > 1:
            wave_path = QPainterPath()
            for i in range(len(self._wave_bars)):
                bx = x_start + (i + 0.5) * bar_gap
                by = wave_y - self._wave_bars[i] * 10
                if i == 0:
                    wave_path.moveTo(bx, by)
                else:
                    wave_path.lineTo(bx, by)
            p.setPen(QPen(rc(*hue, 40), 1))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(wave_path)

        p.end()

    def sizeHint(self):
        return QSize(400, 380)


# ============================================================
# SİNYAL KÖPRÜsü
# ============================================================

class GuiSinyalleri(QObject):
    mesaj_ekle = pyqtSignal(str, str)
    durum_guncelle = pyqtSignal(str)
    mod_guncelle = pyqtSignal(str)
    bellek_guncelle = pyqtSignal(dict)
    hata_goster = pyqtSignal(str)
    surum_goster = pyqtSignal(str)
    duygu_guncelle = pyqtSignal(str)


# ============================================================
# SOL MENÜ ÖĞESİ
# ============================================================

class MenuOgesi(QFrame):
    """Tek bir navigasyon menü öğesi"""
    def __init__(self, ikon, etiket, aktif=False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(44)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 12, 0)
        lay.setSpacing(10)

        ikon_l = QLabel(ikon)
        ikon_l.setFont(QFont("Segoe UI", 13))
        ikon_l.setFixedWidth(24)
        ikon_l.setStyleSheet("background: transparent; border: none;")
        lay.addWidget(ikon_l)

        text_l = QLabel(etiket)
        text_l.setFont(QFont("Segoe UI", 10))
        stil = f"color: {C['text_hi'] if aktif else C['dim']}; background: transparent; border: none;"
        text_l.setStyleSheet(stil)
        lay.addWidget(text_l)

        bg = C['menu_active'] if aktif else "transparent"
        border = f"border-left: 3px solid {C['cyan']};" if aktif else "border-left: 3px solid transparent;"
        self.setStyleSheet(f"QFrame {{ background: {bg}; {border} border-radius: 0px; }}")


# ============================================================
# ANA PENCERE
# ============================================================

class AtlasArayuz(QMainWindow):

    def __init__(self):
        super().__init__()
        self.sinyaller = GuiSinyalleri()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle("ATLAS — Sesli AI Asistan")
        self.setMinimumSize(960, 680)
        self.resize(1060, 740)
        self._set_window_icon()

        self.setStyleSheet(f"""
            QMainWindow {{ background: {C['bg']}; }}
            QWidget {{ background: transparent; color: {C['text']}; }}
        """)

        merkez = QWidget()
        self.setCentralWidget(merkez)
        ana = QVBoxLayout(merkez)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)

        # ── ÜST BAR ──
        ana.addWidget(self._build_top_bar())

        # ── ORTA: Sidebar + İçerik ──
        govde = QWidget()
        govde.setStyleSheet(f"background: {C['bg']};")
        govde_l = QHBoxLayout(govde)
        govde_l.setContentsMargins(0, 0, 0, 0)
        govde_l.setSpacing(0)

        govde_l.addWidget(self._build_sidebar())

        # Dikey ayırıcı
        vsep = QFrame()
        vsep.setFixedWidth(1)
        vsep.setStyleSheet(f"background: {C['border']};")
        govde_l.addWidget(vsep)

        # İçerik: Küre + Sohbet
        icerik = QWidget()
        icerik_l = QVBoxLayout(icerik)
        icerik_l.setContentsMargins(0, 0, 0, 0)
        icerik_l.setSpacing(0)

        self.kure = OrganikKureWidget()
        icerik_l.addWidget(self.kure, stretch=3)

        hsep = QFrame()
        hsep.setFixedHeight(1)
        hsep.setStyleSheet(
            f"background: qlineargradient(x1:0, x2:1, "
            f"stop:0 transparent, stop:0.15 {C['cyan_dim']}, "
            f"stop:0.85 {C['cyan_dim']}, stop:1 transparent);"
        )
        icerik_l.addWidget(hsep)

        icerik_l.addWidget(self._build_conversation(), stretch=2)

        govde_l.addWidget(icerik, stretch=1)

        ana.addWidget(govde, stretch=1)

        # ── ALT BAR ──
        ana.addWidget(self._build_bottom_bar())

        # Saat
        self._saat_timer = QTimer()
        self._saat_timer.timeout.connect(self._saat_guncelle)
        self._saat_timer.start(1000)
        self._saat_guncelle()

    def _set_window_icon(self):
        logo_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atlas_logo.ico")
        logo_png = os.path.join(os.path.dirname(os.path.abspath(__file__)), "atlas_logo.png")
        if os.path.exists(logo_ico):
            self.setWindowIcon(QIcon(logo_ico))
        elif os.path.exists(logo_png):
            self.setWindowIcon(QIcon(logo_png))
        else:
            pixmap = QPixmap(64, 64)
            pixmap.fill(Qt.GlobalColor.transparent)
            pp = QPainter(pixmap)
            pp.setRenderHint(QPainter.RenderHint.Antialiasing)
            pp.setPen(QPen(QColor(0, 200, 255), 3))
            pp.setBrush(QColor(0, 50, 100, 160))
            pp.drawEllipse(5, 5, 54, 54)
            pp.setPen(QColor(255, 255, 255, 240))
            pp.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
            pp.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
            pp.end()
            self.setWindowIcon(QIcon(pixmap))

    # ────────────────────────────
    # ÜST BAR
    # ────────────────────────────

    def _build_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(y1:0, y2:1,
                    stop:0 {C['panel']}, stop:1 {C['bg2']});
                border-bottom: 1px solid {C['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(22, 0, 22, 0)

        logo = QLabel("A T L A S")
        logo.setFont(QFont("Consolas", 17, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {C['cyan']}; letter-spacing: 6px; background: transparent;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(22)
        glow.setColor(QColor(0, 212, 255, 110))
        glow.setOffset(0, 0)
        logo.setGraphicsEffect(glow)
        lay.addWidget(logo)

        lay.addStretch()

        self.surum_label = QLabel("v8.2")
        self.surum_label.setFont(QFont("Consolas", 9))
        self.surum_label.setStyleSheet(f"color: {C['dim']}; background: transparent;")
        lay.addWidget(self.surum_label)

        sep = QLabel("│")
        sep.setStyleSheet(f"color: {C['border']}; background: transparent; margin: 0 10px;")
        lay.addWidget(sep)

        self.saat_ust = QLabel("--:--")
        self.saat_ust.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.saat_ust.setStyleSheet(f"color: {C['text_hi']}; background: transparent;")
        lay.addWidget(self.saat_ust)

        return bar

    # ────────────────────────────
    # SOL MENÜ
    # ────────────────────────────

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(170)
        sidebar.setStyleSheet(f"QFrame {{ background: {C['sidebar']}; }}")
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 16, 0, 16)
        lay.setSpacing(2)

        lay.addWidget(MenuOgesi("🏠", "Ana Sayfa", aktif=True))
        lay.addWidget(MenuOgesi("🧠", "Beyin Durumu"))
        lay.addWidget(MenuOgesi("💬", "Sohbet"))
        lay.addWidget(MenuOgesi("⚙️", "Ayarlar"))

        lay.addStretch()

        # Beyin durumu kartları (sidebar alt)
        durum_frame = QFrame()
        durum_frame.setStyleSheet(f"""
            QFrame {{
                background: {C['bg']};
                border: 1px solid {C['border']};
                border-radius: 6px;
                margin: 8px 12px;
            }}
        """)
        dl = QVBoxLayout(durum_frame)
        dl.setContentsMargins(10, 8, 10, 8)
        dl.setSpacing(4)

        d_title = QLabel("BEYİN DURUMU")
        d_title.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        d_title.setStyleSheet(f"color: {C['cyan']}; letter-spacing: 1px; border: none; background: transparent;")
        dl.addWidget(d_title)

        self.dikkat_val = QLabel("🔇 Pasif")
        self.dikkat_val.setFont(QFont("Segoe UI", 9))
        self.dikkat_val.setStyleSheet(f"color: {C['text']}; border: none; background: transparent;")
        dl.addWidget(self.dikkat_val)

        self.duygu_val = QLabel("😐 —")
        self.duygu_val.setFont(QFont("Segoe UI", 9))
        self.duygu_val.setStyleSheet(f"color: {C['text']}; border: none; background: transparent;")
        dl.addWidget(self.duygu_val)

        self.hafiza_val = QLabel("💬 0 kayıt")
        self.hafiza_val.setFont(QFont("Segoe UI", 9))
        self.hafiza_val.setStyleSheet(f"color: {C['text']}; border: none; background: transparent;")
        dl.addWidget(self.hafiza_val)

        lay.addWidget(durum_frame)

        # Tarih
        self.tarih_label = QLabel("")
        self.tarih_label.setFont(QFont("Consolas", 9))
        self.tarih_label.setStyleSheet(f"color: {C['dim']}; border: none; background: transparent;")
        self.tarih_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.tarih_label)

        return sidebar

    # ────────────────────────────
    # SOHBET ALANI
    # ────────────────────────────

    def _build_conversation(self):
        w = QWidget()
        w.setStyleSheet(f"background: {C['bg']};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(4)

        header = QLabel("── KONUŞMA ──")
        header.setFont(QFont("Consolas", 8))
        header.setStyleSheet(f"color: {C['dim']}; letter-spacing: 1px;")
        lay.addWidget(header)

        self.konusma_alani = QTextEdit()
        self.konusma_alani.setReadOnly(True)
        self.konusma_alani.setFont(QFont("Segoe UI", 10))
        self.konusma_alani.setStyleSheet(f"""
            QTextEdit {{
                background: {C['bg']};
                color: {C['text']};
                border: none;
                padding: 6px;
                selection-background-color: {C['cyan_dim']};
            }}
            QScrollBar:vertical {{
                background: {C['sidebar']};
                width: 5px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {C['border_hi']};
                border-radius: 2px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        lay.addWidget(self.konusma_alani)

        return w

    # ────────────────────────────
    # ALT BAR
    # ────────────────────────────

    def _build_bottom_bar(self):
        bar = QFrame()
        bar.setFixedHeight(34)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {C['sidebar']};
                border-top: 1px solid {C['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        self.durum_nokta = QLabel("●")
        self.durum_nokta.setFont(QFont("Segoe UI", 9))
        self.durum_nokta.setStyleSheet(f"color: {C['green']}; background: transparent;")
        lay.addWidget(self.durum_nokta)

        self.durum_label = QLabel("Başlatılıyor...")
        self.durum_label.setFont(QFont("Segoe UI", 9))
        self.durum_label.setStyleSheet(f"color: {C['dim']}; background: transparent;")
        lay.addWidget(self.durum_label)

        lay.addStretch()

        return bar

    # ────────────────────────────
    # SİNYALLER
    # ────────────────────────────

    def _connect_signals(self):
        self.sinyaller.mesaj_ekle.connect(self._mesaj_ekle)
        self.sinyaller.durum_guncelle.connect(self._durum_guncelle)
        self.sinyaller.mod_guncelle.connect(self._mod_guncelle)
        self.sinyaller.bellek_guncelle.connect(self._bellek_guncelle)
        self.sinyaller.hata_goster.connect(self._hata_goster)
        self.sinyaller.surum_goster.connect(self._surum_goster)
        self.sinyaller.duygu_guncelle.connect(self._duygu_guncelle)

    def _mesaj_ekle(self, rol, mesaj):
        zaman = datetime.now().strftime("%H:%M")
        if rol == "kullanici":
            renk, ikon, isim = C['cyan'], "▸", "SEN"
        elif rol == "asistan":
            renk, ikon, isim = C['green'], "◆", "ATLAS"
        elif rol == "sistem":
            renk, ikon, isim = C['dim'], "⚙", "SİSTEM"
        else:
            renk, ikon, isim = C['text'], "•", rol.upper()

        html = (
            f'<div style="margin:4px 0; font-family:Segoe UI,sans-serif;">'
            f'<span style="color:{C["dim"]}; font-size:9px; font-family:Consolas;">{zaman}</span>'
            f'<span style="color:{renk}; font-weight:600;"> {ikon} {isim}</span>'
            f'<span style="color:{C["text"]};"> {mesaj}</span>'
            f'</div>'
        )
        self.konusma_alani.append(html)
        sb = self.konusma_alani.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _durum_guncelle(self, durum):
        self.durum_label.setText(durum)
        self.kure.set_durum(durum)
        dl = durum.lower()
        if "hata" in dl:
            self.durum_nokta.setStyleSheet(f"color: {C['red']}; background: transparent;")
        elif "dinl" in dl or "bekl" in dl or "hazır" in dl:
            self.durum_nokta.setStyleSheet(f"color: {C['green']}; background: transparent;")
        elif "düşün" in dl or "işlen" in dl:
            self.durum_nokta.setStyleSheet(f"color: {C['orange']}; background: transparent;")
        else:
            self.durum_nokta.setStyleSheet(f"color: {C['cyan']}; background: transparent;")

    def _mod_guncelle(self, mod):
        mod_str = {
            "pasif": "🔇 Pasif Dinleme",
            "aktif": "🎙️ Aktif Dinleme",
            "isim": "👤 İsim Öğrenme",
            "mesgul": "💭 İşleniyor...",
        }
        self.dikkat_val.setText(mod_str.get(mod, mod))
        self.kure.set_mod(mod)

    def _bellek_guncelle(self, durum):
        toplam = durum.get("toplam_etkilesim", 0)
        calisma = durum.get("calisma_bellegi", 0)
        self.hafiza_val.setText(f"💬 {calisma}/7 | 📊 {toplam}")

    def _duygu_guncelle(self, duygu):
        emojiler = {
            "mutlu": "😊 Mutlu", "uzgun": "😔 Üzgün",
            "sinirli": "😤 Sinirli", "merakli": "🤔 Meraklı",
            "aceleci": "⚡ Aceleci", "notr": "😐 Nötr",
        }
        self.duygu_val.setText(emojiler.get(duygu, f"❓ {duygu}"))

    def _hata_goster(self, hata):
        self._mesaj_ekle("sistem", f"⚠️ {hata}")

    def _surum_goster(self, surum):
        self.surum_label.setText(f"v{surum}")

    def _saat_guncelle(self):
        simdi = datetime.now()
        self.saat_ust.setText(simdi.strftime("%H:%M"))
        gunler = {0: "Pzt", 1: "Sal", 2: "Çar", 3: "Per", 4: "Cum", 5: "Cmt", 6: "Paz"}
        aylar = {
            1: "Oca", 2: "Şub", 3: "Mar", 4: "Nis", 5: "May", 6: "Haz",
            7: "Tem", 8: "Ağu", 9: "Eyl", 10: "Eki", 11: "Kas", 12: "Ara"
        }
        gun = gunler.get(simdi.weekday(), "")
        ay = aylar.get(simdi.month, "")
        self.tarih_label.setText(f"{gun}, {simdi.day} {ay}")
