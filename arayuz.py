"""
ATLAS - AURA Arayüz v8.2c
==========================
AURA tarzı 3 sütunlu layout:
  Sol menü | Ortada büyük organik küre | Sağda sohbet
Küre tek ses göstergesi — konuşmaya göre hareket eder.
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
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QRectF, QPointF, QSize
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QRadialGradient, QPixmap, QIcon,
    QPainterPath, QLinearGradient, QBrush
)

logger = logging.getLogger("ATLAS.arayuz")

# ─── RENK PALETİ (AURA tarzı derin mavi) ───
C = {
    "bg":         "#050a18",
    "bg2":        "#081024",
    "sidebar":    "#060c1c",
    "panel":      "#0a1228",
    "chat_bg":    "#070e20",
    "border":     "#0c1a30",
    "cyan":       "#00d4ff",
    "cyan2":      "#00c0ee",
    "cyan_dim":   "#005878",
    "cyan_glow":  "#0098cc",
    "teal":       "#00e8d0",
    "green":      "#00ff88",
    "orange":     "#ff8800",
    "red":        "#ff3333",
    "text":       "#b8d4e6",
    "text_hi":    "#daeeff",
    "dim":        "#3e5a72",
    "menu_active":"#0a1838",
}


# ═══════════════════════════════════════════════════════
#  ORGANİK KÜRE — AURA tarzı, ses tepkili
# ═══════════════════════════════════════════════════════

class OrganikKureWidget(QWidget):
    """
    AURA benzeri organik parlayan küre.
    Ses seviyesine göre: boyut, deformasyon, hız, parıltı değişir.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 300)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._angle = 0.0
        self._pulse = 0.0
        self._mod = "pasif"
        self._durum_text = "Başlatılıyor..."
        self._ses_seviyesi = 0.0
        self._ses_hedef = 0.0
        self._ses_smooth = 0.0

        self._hizlar = {
            "pasif":  {"donus": 0.10, "nabiz": 0.7},
            "aktif":  {"donus": 0.30, "nabiz": 1.4},
            "isim":   {"donus": 0.25, "nabiz": 1.1},
            "mesgul": {"donus": 0.70, "nabiz": 2.2},
        }

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(30)

    def set_mod(self, mod):
        self._mod = mod

    def set_durum(self, text):
        self._durum_text = text

    def set_ses_seviyesi(self, seviye):
        self._ses_hedef = max(0.0, min(1.0, seviye))

    def _animate(self):
        hiz = self._hizlar.get(self._mod, self._hizlar["pasif"])
        self._ses_smooth += (self._ses_hedef - self._ses_smooth) * 0.16
        ses = self._ses_smooth

        if self._mod == "mesgul" and self._ses_hedef < 0.05:
            t = time.time()
            ses = 0.25 + 0.45 * abs(math.sin(t * 3.8)) * abs(math.sin(t * 1.5))
            self._ses_smooth = ses

        ses_bonus = ses * 1.6
        self._angle = (self._angle + hiz["donus"] + ses_bonus * 0.5) % 360
        self._pulse = (self._pulse + hiz["nabiz"] + ses_bonus) % 360
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        base_r = min(w, h) / 2 - 20
        ses = self._ses_smooth
        pv = (math.sin(math.radians(self._pulse)) + 1) / 2
        max_r = base_r * (0.82 + 0.18 * ses + 0.05 * pv)

        # Renkler
        hr, hg, hb = 0, 212, 255
        br, bg_, bb = 120, 240, 255

        def rc(r, g, b, a):
            return QColor(r, g, b, max(0, min(255, int(a))))

        # ── 1. Geniş dış parıltı ──
        gr = max_r * (1.6 + 0.4 * ses)
        glow = QRadialGradient(cx, cy, gr)
        glow.setColorAt(0.0, rc(hr, hg, hb, 22 + 30 * ses))
        glow.setColorAt(0.25, rc(hr, hg, hb, 10 + 16 * ses))
        glow.setColorAt(0.6, rc(hr, hg, hb, 3 + 5 * ses))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), glow)

        # ── 2. Organik halkalar (6 katman — daha zengin) ──
        for layer in range(6, 0, -1):
            r = max_r * (0.12 + layer * 0.14)
            sp = 0.25 + layer * 0.055
            dr = 1 if layer % 2 == 0 else -1
            rot = self._angle * sp * dr

            deform = (0.035 + layer * 0.022) * (1.0 + ses * 2.2)
            path = QPainterPath()
            n = 90
            for s in range(n + 1):
                theta = s * 2 * math.pi / n
                d = 1.0
                d += deform * math.sin(3 * theta + rot * 0.05)
                d += (deform * 0.6) * math.sin(5 * theta - rot * 0.03 + layer)
                d += (deform * 0.4) * math.sin(7 * theta + rot * 0.018 + layer * 0.7)
                d += (deform * 0.25) * math.sin(2 * theta + rot * 0.04)
                rx = r * d
                x = cx + rx * math.cos(theta)
                y = cy + rx * math.sin(theta)
                if s == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            path.closeSubpath()

            a_fill = int(12 + (6 - layer) * 6 + 14 * ses + 3 * pv)
            a_line = int(25 + (6 - layer) * 12 + 25 * ses + 5 * pv)
            p.setPen(QPen(rc(hr, hg, hb, a_line), 1.0 + 0.4 * ses))
            p.setBrush(rc(hr, hg, hb, a_fill))
            p.drawPath(path)

        # ── 3. Çiçek yaprakları (8 adet — AURA gülü) ──
        for i in range(8):
            p.save()
            p.translate(cx, cy)
            angle = self._angle * 0.3 + i * 45
            p.rotate(angle)

            pw = max_r * (0.18 + 0.07 * ses)
            ph = max_r * (0.52 + 0.12 * ses)
            pa = int(16 + 18 * ses + 6 * pv)

            pg = QRadialGradient(0, 0, ph)
            pg.setColorAt(0.0, rc(br, bg_, bb, pa + 8))
            pg.setColorAt(0.4, rc(hr, hg, hb, pa))
            pg.setColorAt(1.0, QColor(0, 0, 0, 0))

            p.setPen(QPen(rc(hr, hg, hb, int(pa * 0.4)), 0.6))
            p.setBrush(pg)
            p.drawEllipse(QRectF(-pw / 2, -ph / 2, pw, ph))
            p.restore()

        # ── 4. İç çiçek yaprakları (5 adet — iç katman) ──
        for i in range(5):
            p.save()
            p.translate(cx, cy)
            angle = -self._angle * 0.5 + i * 72 + 20
            p.rotate(angle)

            pw = max_r * (0.10 + 0.04 * ses)
            ph = max_r * (0.30 + 0.06 * ses)
            pa = int(20 + 20 * ses + 8 * pv)

            pg = QRadialGradient(0, 0, ph)
            pg.setColorAt(0.0, rc(200, 255, 255, pa + 10))
            pg.setColorAt(0.5, rc(hr, hg, hb, pa))
            pg.setColorAt(1.0, QColor(0, 0, 0, 0))

            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(pg)
            p.drawEllipse(QRectF(-pw / 2, -ph / 2, pw, ph))
            p.restore()

        # ── 5. Parlayan merkez ──
        cr = max_r * (0.18 + 0.10 * ses)
        ca = int(120 + 110 * ses + 25 * pv)
        cg = QRadialGradient(cx, cy, cr)
        cg.setColorAt(0.0, rc(230, 255, 255, min(255, ca)))
        cg.setColorAt(0.2, rc(br, bg_, bb, int(ca * 0.75)))
        cg.setColorAt(0.55, rc(hr, hg, hb, int(ca * 0.3)))
        cg.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cg)
        p.drawEllipse(QPointF(cx, cy), cr, cr)

        # ── 6. Parçacıklar (dış yörünge) ──
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(28):
            orbit = max_r * (0.55 + 0.40 * abs(math.sin(i * 1.3 + self._pulse * 0.006)))
            orbit += ses * max_r * 0.12 * math.sin(i * 2.0 + self._angle * 0.018)
            ang = math.radians(i * (360 / 28) + self._angle * 0.06)
            px = cx + orbit * math.cos(ang)
            py = cy + orbit * math.sin(ang)
            da = int(35 + 80 * abs(math.sin(self._pulse * 0.012 + i * 0.65)))
            dr = 1.2 + 1.0 * abs(math.sin(self._pulse * 0.008 + i * 1.0))
            p.setBrush(rc(br, bg_, bb, da))
            p.drawEllipse(QPointF(px, py), dr, dr)

        # ── 7. Yıldız parçacıkları (uzak, ince) ──
        for i in range(14):
            far = max_r * (0.92 + 0.18 * abs(math.sin(i * 2.7 + self._pulse * 0.004)))
            ang = math.radians(i * 25.7 + self._angle * 0.03 + 10)
            px = cx + far * math.cos(ang)
            py = cy + far * math.sin(ang)
            da = int(18 + 35 * abs(math.sin(self._pulse * 0.009 + i * 1.4)))
            p.setBrush(rc(200, 255, 255, da))
            p.drawEllipse(QPointF(px, py), 0.8, 0.8)

        # ── 8. ATLAS yazısı ──
        text_a = int(195 + 45 * pv)
        p.setPen(QColor(220, 245, 255, text_a))
        fa = QFont("Consolas", 14, QFont.Weight.Bold)
        fa.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 6)
        p.setFont(fa)
        p.drawText(QRectF(cx - 100, cy - 12, 200, 28),
                   Qt.AlignmentFlag.AlignCenter, "ATLAS")

        # ── 9. Durum metni ──
        p.setPen(rc(hr, hg, hb, int(130 + 70 * pv)))
        fd = QFont("Segoe UI", 9)
        p.setFont(fd)
        p.drawText(QRectF(cx - 140, cy + 18, 280, 22),
                   Qt.AlignmentFlag.AlignCenter, self._durum_text)

        p.end()

    def sizeHint(self):
        return QSize(450, 420)


# ═══════════════════════════════════════════════════════
#  SİNYAL KÖPRÜsü
# ═══════════════════════════════════════════════════════

class GuiSinyalleri(QObject):
    mesaj_ekle = pyqtSignal(str, str)
    durum_guncelle = pyqtSignal(str)
    mod_guncelle = pyqtSignal(str)
    bellek_guncelle = pyqtSignal(dict)
    hata_goster = pyqtSignal(str)
    surum_goster = pyqtSignal(str)
    duygu_guncelle = pyqtSignal(str)
    ses_seviyesi = pyqtSignal(float)


# ═══════════════════════════════════════════════════════
#  SOL MENÜ ÖĞESİ — AURA tarzı
# ═══════════════════════════════════════════════════════

class MenuOgesi(QFrame):
    def __init__(self, ikon, etiket, aktif=False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(20, 0, 10, 0)
        lay.setSpacing(14)

        ikon_l = QLabel(ikon)
        ikon_l.setFont(QFont("Segoe UI", 15))
        ikon_l.setFixedWidth(28)
        ikon_l.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(ikon_l)

        text_l = QLabel(etiket)
        wt = QFont.Weight.DemiBold if aktif else QFont.Weight.Normal
        text_l.setFont(QFont("Segoe UI", 11, wt))
        renk = C["text_hi"] if aktif else C["dim"]
        text_l.setStyleSheet(f"color:{renk}; background:transparent; border:none;")
        lay.addWidget(text_l)
        lay.addStretch()

        if aktif:
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0,x2:1,
                        stop:0 rgba(0,180,255,25), stop:1 transparent);
                    border-left: 2px solid {C['cyan']};
                }}
            """)
        else:
            self.setStyleSheet("QFrame { background:transparent; border-left:2px solid transparent; }")


# ═══════════════════════════════════════════════════════
#  ANA PENCERE — 3 Sütun Layout (AURA gibi)
# ═══════════════════════════════════════════════════════

class AtlasArayuz(QMainWindow):

    def __init__(self):
        super().__init__()
        self.sinyaller = GuiSinyalleri()
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setWindowTitle("ATLAS — Sesli AI Asistan")
        self.setMinimumSize(1000, 640)
        self.resize(1120, 720)
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

        # ── 3 SÜTUN GÖVDE ──
        govde = QWidget()
        govde_l = QHBoxLayout(govde)
        govde_l.setContentsMargins(0, 0, 0, 0)
        govde_l.setSpacing(0)

        # Sol: Menü
        govde_l.addWidget(self._build_sidebar())

        # Orta: Küre (büyük, bol alan)
        kure_container = QWidget()
        kure_container.setStyleSheet(f"background: {C['bg']};")
        kure_lay = QVBoxLayout(kure_container)
        kure_lay.setContentsMargins(0, 0, 0, 0)
        kure_lay.setSpacing(0)
        self.kure = OrganikKureWidget()
        kure_lay.addWidget(self.kure)
        govde_l.addWidget(kure_container, stretch=5)

        # Sağ: Sohbet paneli
        govde_l.addWidget(self._build_chat_panel(), stretch=3)

        ana.addWidget(govde, stretch=1)

        # ── ALT BAR ──
        ana.addWidget(self._build_bottom_bar())

        # Saat timer
        self._saat_timer = QTimer()
        self._saat_timer.timeout.connect(self._saat_guncelle)
        self._saat_timer.start(1000)
        self._saat_guncelle()

    def _set_window_icon(self):
        base = os.path.dirname(os.path.abspath(__file__))
        for ext in ("atlas_logo.ico", "atlas_logo.png"):
            p = os.path.join(base, ext)
            if os.path.exists(p):
                self.setWindowIcon(QIcon(p))
                return
        px = QPixmap(64, 64)
        px.fill(Qt.GlobalColor.transparent)
        pp = QPainter(px)
        pp.setRenderHint(QPainter.RenderHint.Antialiasing)
        pp.setPen(QPen(QColor(0, 200, 255), 3))
        pp.setBrush(QColor(0, 50, 100, 160))
        pp.drawEllipse(5, 5, 54, 54)
        pp.setPen(QColor(255, 255, 255))
        pp.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        pp.drawText(px.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        pp.end()
        self.setWindowIcon(QIcon(px))

    # ─────────────── ÜST BAR ───────────────

    def _build_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(50)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(y1:0, y2:1,
                    stop:0 {C['panel']}, stop:1 {C['bg']});
                border-bottom: 1px solid {C['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(22, 0, 22, 0)

        logo = QLabel("A T L A S")
        logo.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        logo.setStyleSheet(f"color:{C['cyan']}; letter-spacing:5px; background:transparent;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(24)
        glow.setColor(QColor(0, 212, 255, 120))
        glow.setOffset(0, 0)
        logo.setGraphicsEffect(glow)
        lay.addWidget(logo)

        lay.addStretch()

        self.surum_label = QLabel("v8.2")
        self.surum_label.setFont(QFont("Consolas", 9))
        self.surum_label.setStyleSheet(f"color:{C['dim']}; background:transparent;")
        lay.addWidget(self.surum_label)

        sep = QLabel("│")
        sep.setStyleSheet(f"color:{C['border']}; background:transparent; margin:0 8px;")
        lay.addWidget(sep)

        self.saat_ust = QLabel("--:--")
        self.saat_ust.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.saat_ust.setStyleSheet(f"color:{C['text_hi']}; background:transparent;")
        lay.addWidget(self.saat_ust)

        return bar

    # ─────────────── SOL MENÜ ───────────────

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(170)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, x2:1,
                    stop:0 {C['sidebar']}, stop:1 {C['bg']});
                border-right: 1px solid {C['border']};
            }}
        """)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 18, 0, 14)
        lay.setSpacing(2)

        lay.addWidget(MenuOgesi("🏠", "Ana Sayfa", aktif=True))
        lay.addWidget(MenuOgesi("🧠", "Beyin"))
        lay.addWidget(MenuOgesi("💬", "Sohbet"))
        lay.addWidget(MenuOgesi("⚙️", "Ayarlar"))

        lay.addStretch()

        # Alt durum bilgileri — bütünleşik, kutu yok
        self.dikkat_val = QLabel("  🔇 Pasif")
        self.dikkat_val.setFont(QFont("Segoe UI", 8))
        self.dikkat_val.setStyleSheet(f"color:{C['dim']}; padding-left:16px;")
        lay.addWidget(self.dikkat_val)

        self.duygu_val = QLabel("  😐 —")
        self.duygu_val.setFont(QFont("Segoe UI", 8))
        self.duygu_val.setStyleSheet(f"color:{C['dim']}; padding-left:16px;")
        lay.addWidget(self.duygu_val)

        self.hafiza_val = QLabel("  💬 0")
        self.hafiza_val.setFont(QFont("Segoe UI", 8))
        self.hafiza_val.setStyleSheet(f"color:{C['dim']}; padding-left:16px;")
        lay.addWidget(self.hafiza_val)

        spacer = QWidget()
        spacer.setFixedHeight(6)
        lay.addWidget(spacer)

        self.tarih_label = QLabel("")
        self.tarih_label.setFont(QFont("Consolas", 8))
        self.tarih_label.setStyleSheet(f"color:{C['dim']};")
        self.tarih_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.tarih_label)

        return sidebar

    # ─────────────── SAĞ SOHBET PANELİ ───────────────

    def _build_chat_panel(self):
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, x2:1,
                    stop:0 {C['bg']}, stop:1 {C['chat_bg']});
                border-left: 1px solid {C['border']};
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 14, 14, 10)
        lay.setSpacing(6)

        # Başlık
        header_lay = QHBoxLayout()
        header_lay.setSpacing(8)

        mic_icon = QLabel("🎙️")
        mic_icon.setFont(QFont("Segoe UI", 13))
        mic_icon.setStyleSheet("background:transparent;")
        header_lay.addWidget(mic_icon)

        header = QLabel("KONUŞMA")
        header.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        header.setStyleSheet(f"color:{C['cyan']}; letter-spacing:2px; background:transparent;")
        hglow = QGraphicsDropShadowEffect()
        hglow.setBlurRadius(14)
        hglow.setColor(QColor(0, 212, 255, 70))
        hglow.setOffset(0, 0)
        header.setGraphicsEffect(hglow)
        header_lay.addWidget(header)

        header_lay.addStretch()
        lay.addLayout(header_lay)

        # İnce çizgi
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            f"background: qlineargradient(x1:0,x2:1,"
            f"stop:0 transparent, stop:0.2 {C['cyan_dim']},"
            f"stop:0.8 {C['cyan_dim']}, stop:1 transparent);"
        )
        lay.addWidget(sep)

        # Sohbet alanı
        self.konusma_alani = QTextEdit()
        self.konusma_alani.setReadOnly(True)
        self.konusma_alani.setFont(QFont("Segoe UI", 10))
        self.konusma_alani.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                color: {C['text']};
                border: none;
                padding: 6px;
                selection-background-color: {C['cyan_dim']};
            }}
            QScrollBar:vertical {{
                background: {C['sidebar']};
                width: 4px;
                border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {C['cyan_dim']};
                border-radius: 2px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)
        lay.addWidget(self.konusma_alani)

        return panel

    # ─────────────── ALT BAR ───────────────

    def _build_bottom_bar(self):
        bar = QFrame()
        bar.setFixedHeight(30)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {C['sidebar']};
                border-top: 1px solid {C['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        self.durum_nokta = QLabel("●")
        self.durum_nokta.setFont(QFont("Segoe UI", 8))
        self.durum_nokta.setStyleSheet(f"color:{C['green']}; background:transparent;")
        lay.addWidget(self.durum_nokta)

        self.durum_label = QLabel("Başlatılıyor...")
        self.durum_label.setFont(QFont("Segoe UI", 8))
        self.durum_label.setStyleSheet(f"color:{C['dim']}; background:transparent;")
        lay.addWidget(self.durum_label)

        lay.addStretch()
        return bar

    # ─────────────── SİNYALLER ───────────────

    def _connect_signals(self):
        self.sinyaller.mesaj_ekle.connect(self._mesaj_ekle)
        self.sinyaller.durum_guncelle.connect(self._durum_guncelle)
        self.sinyaller.mod_guncelle.connect(self._mod_guncelle)
        self.sinyaller.bellek_guncelle.connect(self._bellek_guncelle)
        self.sinyaller.hata_goster.connect(self._hata_goster)
        self.sinyaller.surum_goster.connect(self._surum_goster)
        self.sinyaller.duygu_guncelle.connect(self._duygu_guncelle)
        self.sinyaller.ses_seviyesi.connect(self._ses_seviyesi_slot)

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
            f'<div style="margin:5px 0; font-family:Segoe UI,sans-serif;">'
            f'<span style="color:{C["dim"]}; font-size:9px; font-family:Consolas;">{zaman}</span>'
            f'<span style="color:{renk}; font-weight:600;"> {ikon} {isim}</span><br/>'
            f'<span style="color:{C["text"]}; margin-left:40px;"> {mesaj}</span>'
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
            self.durum_nokta.setStyleSheet(f"color:{C['red']}; background:transparent;")
        elif "dinl" in dl or "bekl" in dl or "hazır" in dl:
            self.durum_nokta.setStyleSheet(f"color:{C['green']}; background:transparent;")
        elif "düşün" in dl or "işlen" in dl:
            self.durum_nokta.setStyleSheet(f"color:{C['orange']}; background:transparent;")
        else:
            self.durum_nokta.setStyleSheet(f"color:{C['cyan']}; background:transparent;")

    def _mod_guncelle(self, mod):
        mod_str = {
            "pasif": "🔇 Pasif",
            "aktif": "🎙️ Aktif",
            "isim": "👤 İsim",
            "mesgul": "💭 Meşgul",
        }
        self.dikkat_val.setText(f"  {mod_str.get(mod, mod)}")
        self.kure.set_mod(mod)

    def _bellek_guncelle(self, durum):
        toplam = durum.get("toplam_etkilesim", 0)
        calisma = durum.get("calisma_bellegi", 0)
        self.hafiza_val.setText(f"  💬 {calisma}/7 | {toplam}")

    def _duygu_guncelle(self, duygu):
        emojiler = {
            "mutlu": "😊 Mutlu", "uzgun": "😔 Üzgün",
            "sinirli": "😤 Sinirli", "merakli": "🤔 Meraklı",
            "aceleci": "⚡ Aceleci", "notr": "😐 Nötr",
        }
        self.duygu_val.setText(f"  {emojiler.get(duygu, f'❓ {duygu}')}")

    def _hata_goster(self, hata):
        self._mesaj_ekle("sistem", f"⚠️ {hata}")

    def _surum_goster(self, surum):
        self.surum_label.setText(f"v{surum}")

    def _ses_seviyesi_slot(self, seviye):
        self.kure.set_ses_seviyesi(seviye)

    def _saat_guncelle(self):
        simdi = datetime.now()
        self.saat_ust.setText(simdi.strftime("%H:%M"))
        gunler = {0:"Pzt",1:"Sal",2:"Çar",3:"Per",4:"Cum",5:"Cmt",6:"Paz"}
        aylar = {1:"Oca",2:"Şub",3:"Mar",4:"Nis",5:"May",6:"Haz",
                 7:"Tem",8:"Ağu",9:"Eyl",10:"Eki",11:"Kas",12:"Ara"}
        self.tarih_label.setText(
            f"{gunler.get(simdi.weekday(),'')}  {simdi.day} {aylar.get(simdi.month,'')}"
        )
