"""
ATLAS - AURA Arayüz v8.2b
==========================
AURA tarzı organik parlayan küre animasyonu.
Küre = tek ses göstergesi, konuşmaya göre hareket eder.
Sol navigasyon bütün/akıcı, dalga formu barları yok.
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
    QPainterPath, QLinearGradient
)

logger = logging.getLogger("ATLAS.arayuz")

# ─── RENK PALETİ ───
C = {
    "bg":        "#06091a",
    "bg2":       "#0a0f22",
    "sidebar":   "#080d20",
    "panel":     "#0c1228",
    "border":    "#0e1a30",
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
    "menu_active": "#0d1a38",
}


# ═══════════════════════════════════════════════════════
#  ORGANİK KÜRE — Tek ses göstergesi
# ═══════════════════════════════════════════════════════

class OrganikKureWidget(QWidget):
    """
    AURA tarzı organik küre. Atlas konuştukça ses seviyesine
    göre nabız atar, büyür-küçülür, daha hızlı döner.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(280, 260)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._angle = 0.0
        self._pulse = 0.0
        self._mod = "pasif"
        self._durum_text = "Başlatılıyor..."
        self._ses_seviyesi = 0.0       # 0..1 — gerçek zamanlı ses
        self._ses_hedef = 0.0
        self._ses_smooth = 0.0         # yumuşatılmış ses

        self._hizlar = {
            "pasif":  {"donus": 0.12, "nabiz": 0.8},
            "aktif":  {"donus": 0.35, "nabiz": 1.5},
            "isim":   {"donus": 0.30, "nabiz": 1.2},
            "mesgul": {"donus": 0.80, "nabiz": 2.5},
        }

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(33)

    def set_mod(self, mod):
        self._mod = mod

    def set_durum(self, text):
        self._durum_text = text

    def set_ses_seviyesi(self, seviye):
        """0.0 - 1.0 arası ses seviyesi (TTS çıkışı veya mikrofon)"""
        self._ses_hedef = max(0.0, min(1.0, seviye))

    def _animate(self):
        hiz = self._hizlar.get(self._mod, self._hizlar["pasif"])

        # Ses seviyesi yumuşatma
        self._ses_smooth += (self._ses_hedef - self._ses_smooth) * 0.18
        ses = self._ses_smooth

        # Meşgul modda (konuşurken) otomatik ses simülasyonu
        if self._mod == "mesgul" and self._ses_hedef < 0.05:
            t = time.time()
            ses = 0.3 + 0.4 * abs(math.sin(t * 4.2)) * abs(math.sin(t * 1.7))
            self._ses_smooth = ses

        # Ses seviyesine göre hız artışı
        ses_bonus = ses * 1.5
        self._angle = (self._angle + hiz["donus"] + ses_bonus * 0.6) % 360
        self._pulse = (self._pulse + hiz["nabiz"] + ses_bonus) % 360

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2
        base_r = min(w, h) / 2 - 30

        ses = self._ses_smooth
        pv = (math.sin(math.radians(self._pulse)) + 1) / 2

        # Ses seviyesine göre küre boyutu (nefes alır gibi)
        max_r = base_r * (0.85 + 0.15 * ses + 0.04 * pv)

        # Renk
        hue = (0, 212, 255)
        hue_b = (140, 240, 255)

        def rc(r, g, b, a):
            return QColor(r, g, b, max(0, min(255, int(a))))

        # ── 1. Dış parıltı ──
        glow_r = max_r * (1.4 + 0.3 * ses)
        glow = QRadialGradient(cx, cy, glow_r)
        glow.setColorAt(0, rc(*hue, 20 + 25 * ses))
        glow.setColorAt(0.35, rc(*hue, 6 + 12 * ses))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), glow)

        # ── 2. Organik halkalar (5 katman) ──
        for layer in range(5, 0, -1):
            r = max_r * (0.18 + layer * 0.15)
            speed = 0.3 + layer * 0.06
            dirn = 1 if layer % 2 == 0 else -1
            rot = self._angle * speed * dirn

            # Ses seviyesine göre deformasyon artışı
            deform_base = (0.04 + layer * 0.02) * (1.0 + ses * 1.8)

            path = QPainterPath()
            n = 72
            for s in range(n + 1):
                theta = s * 2 * math.pi / n
                d = 1.0
                d += deform_base * math.sin(3 * theta + rot * 0.05)
                d += (deform_base * 0.65) * math.sin(5 * theta - rot * 0.035 + layer)
                d += (deform_base * 0.35) * math.sin(2 * theta + rot * 0.02)
                rx = r * d
                x = cx + rx * math.cos(theta)
                y = cy + rx * math.sin(theta)
                if s == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            path.closeSubpath()

            a_fill = int(15 + (5 - layer) * 7 + 10 * ses + 4 * pv)
            a_stroke = int(30 + (5 - layer) * 12 + 20 * ses + 6 * pv)
            p.setPen(QPen(rc(*hue, a_stroke), 1.2 + 0.3 * ses))
            p.setBrush(rc(*hue, a_fill))
            p.drawPath(path)

        # ── 3. Çiçek yaprakları (7 adet) ──
        for i in range(7):
            p.save()
            p.translate(cx, cy)
            angle = self._angle * 0.35 + i * (360 / 7)
            p.rotate(angle)

            pw = max_r * (0.20 + 0.06 * ses)
            ph = max_r * (0.55 + 0.10 * ses)
            pa = int(18 + 15 * ses + 8 * pv)

            pg = QRadialGradient(0, 0, ph)
            pg.setColorAt(0, rc(*hue_b, pa + 5))
            pg.setColorAt(0.5, rc(*hue, pa))
            pg.setColorAt(1, QColor(0, 0, 0, 0))

            p.setPen(QPen(rc(*hue, int(pa * 0.5)), 0.7))
            p.setBrush(pg)
            p.drawEllipse(QRectF(-pw / 2, -ph / 2, pw, ph))
            p.restore()

        # ── 4. Parlayan merkez ──
        cr = max_r * (0.20 + 0.08 * ses)
        ca = int(130 + 100 * ses + 25 * pv)
        cg = QRadialGradient(cx, cy, cr)
        cg.setColorAt(0, rc(220, 255, 255, ca))
        cg.setColorAt(0.25, rc(*hue_b, int(ca * 0.7)))
        cg.setColorAt(0.65, rc(*hue, int(ca * 0.25)))
        cg.setColorAt(1, QColor(0, 0, 0, 0))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(cg)
        p.drawEllipse(QPointF(cx, cy), cr, cr)

        # ── 5. Parçacıklar ──
        p.setPen(Qt.PenStyle.NoPen)
        n_dots = 24
        for i in range(n_dots):
            orbit = max_r * (0.5 + 0.4 * abs(math.sin(i * 1.37 + self._pulse * 0.007)))
            orbit += ses * max_r * 0.15 * math.sin(i * 2.1 + self._angle * 0.02)
            ang = math.radians(i * (360 / n_dots) + self._angle * 0.08)
            px = cx + orbit * math.cos(ang)
            py = cy + orbit * math.sin(ang)
            da = int(40 + 80 * abs(math.sin(self._pulse * 0.013 + i * 0.7)))
            dr = 1.3 + 1.2 * abs(math.sin(self._pulse * 0.009 + i * 1.1))
            p.setBrush(rc(*hue_b, da))
            p.drawEllipse(QPointF(px, py), dr, dr)

        # ── 6. ATLAS yazısı ──
        p.setPen(QColor(230, 248, 255, int(200 + 40 * pv)))
        fa = QFont("Consolas", 13, QFont.Weight.Bold)
        fa.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5)
        p.setFont(fa)
        p.drawText(QRectF(cx - 90, cy - 10, 180, 24),
                   Qt.AlignmentFlag.AlignCenter, "ATLAS")

        # ── 7. Durum metni ──
        p.setPen(rc(*hue, int(140 + 60 * pv)))
        fd = QFont("Segoe UI", 9)
        p.setFont(fd)
        p.drawText(QRectF(cx - 130, cy + 16, 260, 20),
                   Qt.AlignmentFlag.AlignCenter, self._durum_text)

        p.end()

    def sizeHint(self):
        return QSize(400, 360)


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
#  SOL MENÜ ÖĞESİ
# ═══════════════════════════════════════════════════════

class MenuOgesi(QFrame):
    def __init__(self, ikon, etiket, aktif=False, parent=None):
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(22, 0, 14, 0)
        lay.setSpacing(14)

        ikon_l = QLabel(ikon)
        ikon_l.setFont(QFont("Segoe UI", 14))
        ikon_l.setFixedWidth(26)
        ikon_l.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(ikon_l)

        text_l = QLabel(etiket)
        text_l.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium if aktif else QFont.Weight.Normal))
        renk = C["text_hi"] if aktif else C["dim"]
        text_l.setStyleSheet(f"color:{renk}; background:transparent; border:none;")
        lay.addWidget(text_l)
        lay.addStretch()

        if aktif:
            self.setStyleSheet(f"""
                QFrame {{
                    background: qlineargradient(x1:0, x2:1,
                        stop:0 {C['menu_active']}, stop:1 transparent);
                    border-left: 3px solid {C['cyan']};
                }}
            """)
        else:
            self.setStyleSheet("QFrame { background:transparent; border-left:3px solid transparent; }")


# ═══════════════════════════════════════════════════════
#  ANA PENCERE
# ═══════════════════════════════════════════════════════

class AtlasArayuz(QMainWindow):

    def __init__(self):
        super().__init__()
        self.sinyaller = GuiSinyalleri()
        self._setup_ui()
        self._connect_signals()

    # ─────────────── UI ───────────────

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

        ana.addWidget(self._build_top_bar())

        # Gövde: sidebar + içerik
        govde = QWidget()
        govde_l = QHBoxLayout(govde)
        govde_l.setContentsMargins(0, 0, 0, 0)
        govde_l.setSpacing(0)

        govde_l.addWidget(self._build_sidebar())

        # İçerik: küre + sohbet
        icerik = QWidget()
        icerik_l = QVBoxLayout(icerik)
        icerik_l.setContentsMargins(0, 0, 0, 0)
        icerik_l.setSpacing(0)

        self.kure = OrganikKureWidget()
        icerik_l.addWidget(self.kure, stretch=3)

        # İnce ayırıcı çizgi (gradient)
        hsep = QFrame()
        hsep.setFixedHeight(1)
        hsep.setStyleSheet(
            f"background: qlineargradient(x1:0,x2:1,"
            f"stop:0 transparent, stop:0.2 {C['border']},"
            f"stop:0.8 {C['border']}, stop:1 transparent);"
        )
        icerik_l.addWidget(hsep)

        icerik_l.addWidget(self._build_conversation(), stretch=2)

        govde_l.addWidget(icerik, stretch=1)
        ana.addWidget(govde, stretch=1)
        ana.addWidget(self._build_bottom_bar())

        # Saat
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
        # Fallback
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
        logo.setStyleSheet(f"color:{C['cyan']}; letter-spacing:6px; background:transparent;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(22)
        glow.setColor(QColor(0, 212, 255, 110))
        glow.setOffset(0, 0)
        logo.setGraphicsEffect(glow)
        lay.addWidget(logo)

        lay.addStretch()

        self.surum_label = QLabel("v8.2")
        self.surum_label.setFont(QFont("Consolas", 9))
        self.surum_label.setStyleSheet(f"color:{C['dim']}; background:transparent;")
        lay.addWidget(self.surum_label)

        sep = QLabel("│")
        sep.setStyleSheet(f"color:{C['border']}; background:transparent; margin:0 10px;")
        lay.addWidget(sep)

        self.saat_ust = QLabel("--:--")
        self.saat_ust.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.saat_ust.setStyleSheet(f"color:{C['text_hi']}; background:transparent;")
        lay.addWidget(self.saat_ust)

        return bar

    # ─────────────── SOL MENÜ (bütün/akıcı) ───────────────

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(180)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: {C['sidebar']};
                border-right: 1px solid {C['border']};
            }}
        """)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 20, 0, 16)
        lay.setSpacing(4)

        lay.addWidget(MenuOgesi("🏠", "Ana Sayfa", aktif=True))
        lay.addWidget(MenuOgesi("🧠", "Beyin Durumu"))
        lay.addWidget(MenuOgesi("💬", "Sohbet"))
        lay.addWidget(MenuOgesi("⚙️", "Ayarlar"))

        lay.addStretch()

        # Alt kısım — küçük durum bilgileri (bütünleşik)
        self.dikkat_val = QLabel("  🔇 Pasif")
        self.dikkat_val.setFont(QFont("Segoe UI", 9))
        self.dikkat_val.setStyleSheet(f"color:{C['dim']}; background:transparent; padding-left:18px;")
        lay.addWidget(self.dikkat_val)

        self.duygu_val = QLabel("  😐 —")
        self.duygu_val.setFont(QFont("Segoe UI", 9))
        self.duygu_val.setStyleSheet(f"color:{C['dim']}; background:transparent; padding-left:18px;")
        lay.addWidget(self.duygu_val)

        self.hafiza_val = QLabel("  💬 0 kayıt")
        self.hafiza_val.setFont(QFont("Segoe UI", 9))
        self.hafiza_val.setStyleSheet(f"color:{C['dim']}; background:transparent; padding-left:18px;")
        lay.addWidget(self.hafiza_val)

        spacer = QWidget()
        spacer.setFixedHeight(8)
        lay.addWidget(spacer)

        self.tarih_label = QLabel("")
        self.tarih_label.setFont(QFont("Consolas", 9))
        self.tarih_label.setStyleSheet(f"color:{C['dim']}; background:transparent;")
        self.tarih_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.tarih_label)

        return sidebar

    # ─────────────── SOHBET ───────────────

    def _build_conversation(self):
        w = QWidget()
        w.setStyleSheet(f"background:{C['bg']};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(18, 8, 18, 8)
        lay.setSpacing(4)

        header = QLabel("── KONUŞMA ──")
        header.setFont(QFont("Consolas", 8))
        header.setStyleSheet(f"color:{C['dim']}; letter-spacing:1px;")
        lay.addWidget(header)

        self.konusma_alani = QTextEdit()
        self.konusma_alani.setReadOnly(True)
        self.konusma_alani.setFont(QFont("Segoe UI", 10))
        self.konusma_alani.setStyleSheet(f"""
            QTextEdit {{
                background:{C['bg']}; color:{C['text']};
                border:none; padding:6px;
                selection-background-color:{C['cyan_dim']};
            }}
            QScrollBar:vertical {{
                background:{C['sidebar']}; width:5px; border-radius:2px;
            }}
            QScrollBar::handle:vertical {{
                background:{C['border']}; border-radius:2px; min-height:30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)
        lay.addWidget(self.konusma_alani)

        return w

    # ─────────────── ALT BAR ───────────────

    def _build_bottom_bar(self):
        bar = QFrame()
        bar.setFixedHeight(32)
        bar.setStyleSheet(f"""
            QFrame {{
                background:{C['sidebar']};
                border-top: 1px solid {C['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        self.durum_nokta = QLabel("●")
        self.durum_nokta.setFont(QFont("Segoe UI", 9))
        self.durum_nokta.setStyleSheet(f"color:{C['green']}; background:transparent;")
        lay.addWidget(self.durum_nokta)

        self.durum_label = QLabel("Başlatılıyor...")
        self.durum_label.setFont(QFont("Segoe UI", 9))
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
        self.sinyaller.ses_seviyesi.connect(self._ses_seviyesi)

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
            f'<span style="color:{C["text"]};"> {mesaj}</span></div>'
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
            "pasif": "🔇 Pasif Dinleme",
            "aktif": "🎙️ Aktif Dinleme",
            "isim": "👤 İsim Öğrenme",
            "mesgul": "💭 İşleniyor...",
        }
        self.dikkat_val.setText(f"  {mod_str.get(mod, mod)}")
        self.kure.set_mod(mod)

    def _bellek_guncelle(self, durum):
        toplam = durum.get("toplam_etkilesim", 0)
        calisma = durum.get("calisma_bellegi", 0)
        self.hafiza_val.setText(f"  💬 {calisma}/7 | 📊 {toplam}")

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

    def _ses_seviyesi(self, seviye):
        self.kure.set_ses_seviyesi(seviye)

    def _saat_guncelle(self):
        simdi = datetime.now()
        self.saat_ust.setText(simdi.strftime("%H:%M"))
        gunler = {0:"Pzt",1:"Sal",2:"Çar",3:"Per",4:"Cum",5:"Cmt",6:"Paz"}
        aylar = {1:"Oca",2:"Şub",3:"Mar",4:"Nis",5:"May",6:"Haz",
                 7:"Tem",8:"Ağu",9:"Eyl",10:"Eki",11:"Kas",12:"Ara"}
        self.tarih_label.setText(f"{gunler.get(simdi.weekday(),'')}  {simdi.day} {aylar.get(simdi.month,'')}")
