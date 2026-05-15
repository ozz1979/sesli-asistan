"""
ATLAS — AURA Arayüz v8.2d
==========================
Çerçevesiz tam ekran, AURA tarzı immersive tasarım.
Sol metin menü | Ortada büyük organik küre | Sağda sohbet baloncukları.
Emoji ikon yok — temiz, estetik, bütün görünüm.
"""

import math
import time
import os
import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QFrame, QGraphicsDropShadowEffect,
    QSizePolicy, QPushButton
)
from PyQt6.QtCore import (
    Qt, QTimer, pyqtSignal, QObject, QRectF, QPointF, QSize, QPoint
)
from PyQt6.QtGui import (
    QFont, QColor, QPainter, QPen, QRadialGradient, QPixmap, QIcon,
    QPainterPath, QLinearGradient
)

logger = logging.getLogger("ATLAS.arayuz")

# ─── AURA renk paleti ───
C = {
    "bg":           "#04081a",
    "bg2":          "#060e22",
    "sidebar":      "#050b1a",
    "panel":        "#080f24",
    "chat_bg":      "#060d1e",
    "border":       "#0a1528",
    "cyan":         "#00d4ff",
    "cyan2":        "#00bce8",
    "cyan_dim":     "#00506a",
    "cyan_glow":    "#0098cc",
    "teal":         "#00e0c0",
    "green":        "#00ff88",
    "orange":       "#ff8800",
    "red":          "#ff3344",
    "text":         "#b0cee0",
    "text_hi":      "#d8ecff",
    "dim":          "#3e5a72",
    "dim2":         "#2a3e52",
    "bubble_atlas": "#0a2235",
    "bubble_user":  "#101c32",
}


# ═══════════════════════════════════════════════════════
#  ORGANİK KÜRE — AURA tarzı, ses tepkili
# ═══════════════════════════════════════════════════════

class OrganikKureWidget(QWidget):
    """
    AURA benzeri organik parlayan küre.
    Ses seviyesine göre boyut, deformasyon, hız, parıltı değişir.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 280)
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
        cx, cy = w / 2, h * 0.46          # küreyi biraz yukarı çek
        base_r = min(w, h) / 2 - 24
        ses = self._ses_smooth
        pv = (math.sin(math.radians(self._pulse)) + 1) / 2
        max_r = base_r * (0.82 + 0.18 * ses + 0.05 * pv)

        hr, hg, hb = 0, 212, 255          # cyan
        br, bg_, bb = 120, 240, 255        # açık cyan

        def rc(r, g, b, a):
            return QColor(r, g, b, max(0, min(255, int(a))))

        # ── 1. Geniş dış parıltı ──
        gr = max_r * (1.7 + 0.5 * ses)
        glow = QRadialGradient(cx, cy, gr)
        glow.setColorAt(0.0, rc(hr, hg, hb, 24 + 32 * ses))
        glow.setColorAt(0.2, rc(hr, hg, hb, 12 + 18 * ses))
        glow.setColorAt(0.5, rc(hr, hg, hb, 4 + 6 * ses))
        glow.setColorAt(1.0, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), glow)

        # ── 2. Organik halkalar (6 katman) ──
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

            af = int(12 + (6 - layer) * 6 + 14 * ses + 3 * pv)
            al = int(25 + (6 - layer) * 12 + 25 * ses + 5 * pv)
            p.setPen(QPen(rc(hr, hg, hb, al), 1.0 + 0.4 * ses))
            p.setBrush(rc(hr, hg, hb, af))
            p.drawPath(path)

        # ── 3. Dış çiçek yaprakları (8 adet) ──
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

        # ── 4. İç çiçek yaprakları (5 adet) ──
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

        # ── 6. Parçacıklar ──
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

        # ── 7. Yıldız parçacıkları ──
        for i in range(14):
            far = max_r * (0.92 + 0.18 * abs(math.sin(i * 2.7 + self._pulse * 0.004)))
            ang = math.radians(i * 25.7 + self._angle * 0.03 + 10)
            px = cx + far * math.cos(ang)
            py = cy + far * math.sin(ang)
            da = int(18 + 35 * abs(math.sin(self._pulse * 0.009 + i * 1.4)))
            p.setBrush(rc(200, 255, 255, da))
            p.drawEllipse(QPointF(px, py), 0.8, 0.8)

        p.end()

    def sizeHint(self):
        return QSize(460, 420)


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
#  SÜRÜKLEME BARI (çerçevesiz pencere için)
# ═══════════════════════════════════════════════════════

class SurukleBar(QFrame):
    """Çerçevesiz pencereyi sürüklemek için üst bar."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._drag_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window().pos()
            event.accept()

    def mouseMoveEvent(self, event):
        if self._drag_pos is not None:
            win = self.window()
            if win.isMaximized():
                return
            win.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
        event.accept()

    def mouseDoubleClickEvent(self, event):
        win = self.window()
        if win.isMaximized():
            win.showNormal()
        else:
            win.showMaximized()
        event.accept()


# ═══════════════════════════════════════════════════════
#  ANA PENCERE — AURA tarzı çerçevesiz tam ekran
# ═══════════════════════════════════════════════════════

class AtlasArayuz(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowMinMaxButtonsHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.sinyaller = GuiSinyalleri()
        self._kullanici_adi = ""
        self._setup_ui()
        self._connect_signals()

    def show(self):
        """Varsayılan olarak tam ekran aç."""
        super().showMaximized()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_F11:
            if self.isFullScreen():
                self.showMaximized()
            else:
                self.showFullScreen()
        elif event.key() == Qt.Key.Key_Escape:
            if self.isFullScreen():
                self.showMaximized()
        else:
            super().keyPressEvent(event)

    # ─────────────── UI KURULUMU ───────────────

    def _setup_ui(self):
        self.setWindowTitle("ATLAS")
        self.setMinimumSize(960, 600)
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

        # Sol: Navigasyon
        govde_l.addWidget(self._build_sidebar())

        # Orta: Küre + Karşılama
        govde_l.addWidget(self._build_center(), stretch=5)

        # Sağ: Sohbet
        govde_l.addWidget(self._build_chat_panel())

        ana.addWidget(govde, stretch=1)

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

    # ═══════════════════ ÜST BAR ═══════════════════

    def _build_top_bar(self):
        bar = SurukleBar()
        bar.setFixedHeight(44)
        bar.setStyleSheet(f"""
            SurukleBar {{
                background: qlineargradient(y1:0, y2:1,
                    stop:0 {C['panel']}, stop:1 {C['bg']});
                border-bottom: 1px solid {C['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 8, 0)

        # Logo
        logo = QLabel("ATLAS")
        logo.setFont(QFont("Segoe UI Light", 16))
        logo.setStyleSheet(f"color:{C['cyan']}; letter-spacing:4px; background:transparent;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(0, 212, 255, 100))
        glow.setOffset(0, 0)
        logo.setGraphicsEffect(glow)
        lay.addWidget(logo)

        lay.addStretch()

        # Saat
        self.saat_ust = QLabel("--:--")
        self.saat_ust.setFont(QFont("Consolas", 11))
        self.saat_ust.setStyleSheet(f"color:{C['text_hi']}; background:transparent;")
        lay.addWidget(self.saat_ust)

        # Sürüm
        self.surum_label = QLabel("v8.2")
        self.surum_label.setFont(QFont("Consolas", 8))
        self.surum_label.setStyleSheet(f"color:{C['dim']}; background:transparent; margin-left:14px;")
        lay.addWidget(self.surum_label)

        # Durum noktası
        self.durum_nokta = QLabel("●")
        self.durum_nokta.setFont(QFont("Segoe UI", 8))
        self.durum_nokta.setStyleSheet(f"color:{C['green']}; background:transparent; margin-left:12px;")
        lay.addWidget(self.durum_nokta)

        self.durum_label = QLabel("Başlatılıyor...")
        self.durum_label.setFont(QFont("Segoe UI", 8))
        self.durum_label.setStyleSheet(f"color:{C['dim']}; background:transparent; margin-left:3px;")
        lay.addWidget(self.durum_label)

        spacer = QWidget()
        spacer.setFixedWidth(20)
        lay.addWidget(spacer)

        # Pencere kontrolleri
        btn_style = """
            QPushButton {{
                color: {dim}; font-size: 14px;
                background: transparent; border: none;
                min-width: 36px; max-width: 36px;
                min-height: 28px; max-height: 28px;
            }}
            QPushButton:hover {{ color: {hover}; background: {bg}; }}
        """

        min_btn = QPushButton("─")
        min_btn.setStyleSheet(btn_style.format(dim=C['dim'], hover=C['text_hi'], bg="rgba(255,255,255,0.06)"))
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.clicked.connect(self.showMinimized)
        lay.addWidget(min_btn)

        max_btn = QPushButton("□")
        max_btn.setStyleSheet(btn_style.format(dim=C['dim'], hover=C['text_hi'], bg="rgba(255,255,255,0.06)"))
        max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        max_btn.clicked.connect(lambda: self.showNormal() if self.isMaximized() else self.showMaximized())
        lay.addWidget(max_btn)

        close_btn = QPushButton("✕")
        close_style = """
            QPushButton {
                color: """ + C['dim'] + """; font-size: 14px;
                background: transparent; border: none;
                min-width: 36px; max-width: 36px;
                min-height: 28px; max-height: 28px;
            }
            QPushButton:hover { color: #ffffff; background: rgba(255,50,50,0.55); }
        """
        close_btn.setStyleSheet(close_style)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.close)
        lay.addWidget(close_btn)

        return bar

    # ═══════════════════ SOL NAVİGASYON ═══════════════════

    def _build_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(185)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, x2:1,
                    stop:0 {C['sidebar']}, stop:1 {C['bg']});
                border-right: 1px solid {C['border']};
            }}
        """)
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 22, 0, 16)
        lay.setSpacing(0)

        # ── GEZİNTİ bölümü ──
        lay.addWidget(self._sidebar_header("GEZİNTİ"))
        lay.addWidget(self._sidebar_item("Ana Sayfa", aktif=True))
        lay.addWidget(self._sidebar_item("Geçmiş"))
        lay.addWidget(self._sidebar_item("Ayarlar"))

        lay.addSpacing(20)

        # ── MODÜLLER bölümü — dinamik durum gösterimi ──
        lay.addWidget(self._sidebar_header("MODÜLLER"))

        self.sidebar_beyin = self._sidebar_modul("Beyin", "Başlatılıyor...")
        lay.addWidget(self.sidebar_beyin)

        self.sidebar_hafiza = self._sidebar_modul("Hafıza", "0 kayıt")
        lay.addWidget(self.sidebar_hafiza)

        self.sidebar_duygu = self._sidebar_modul("Duygu", "Nötr")
        lay.addWidget(self.sidebar_duygu)

        lay.addStretch()

        # ── Alt durum bilgisi ──
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"""
            background: qlineargradient(x1:0,x2:1,
                stop:0 transparent, stop:0.3 {C['border']},
                stop:0.7 {C['border']}, stop:1 transparent);
        """)
        lay.addWidget(sep)
        lay.addSpacing(10)

        self.dikkat_val = QLabel("Pasif Dinleme")
        self.dikkat_val.setFont(QFont("Segoe UI", 8))
        self.dikkat_val.setStyleSheet(f"color:{C['dim']}; padding-left:20px;")
        lay.addWidget(self.dikkat_val)

        self.duygu_val = QLabel("Nötr")
        self.duygu_val.setFont(QFont("Segoe UI", 8))
        self.duygu_val.setStyleSheet(f"color:{C['dim']}; padding-left:20px;")
        lay.addWidget(self.duygu_val)

        self.hafiza_val = QLabel("0 kayıt")
        self.hafiza_val.setFont(QFont("Segoe UI", 8))
        self.hafiza_val.setStyleSheet(f"color:{C['dim']}; padding-left:20px;")
        lay.addWidget(self.hafiza_val)

        lay.addSpacing(8)

        self.tarih_label = QLabel("")
        self.tarih_label.setFont(QFont("Consolas", 8))
        self.tarih_label.setStyleSheet(f"color:{C['dim']};")
        self.tarih_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.tarih_label)

        return sidebar

    def _sidebar_header(self, text):
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        lbl.setStyleSheet(f"""
            color: {C['dim']};
            padding: 8px 20px 4px 20px;
            letter-spacing: 2px;
            background: transparent;
        """)
        return lbl

    def _sidebar_item(self, text, aktif=False):
        lbl = QLabel(text)
        lbl.setFixedHeight(38)
        lbl.setCursor(Qt.CursorShape.PointingHandCursor)

        if aktif:
            lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
            lbl.setStyleSheet(f"""
                QLabel {{
                    color: {C['text_hi']};
                    padding-left: 20px;
                    background: qlineargradient(x1:0, x2:1,
                        stop:0 rgba(0,180,255,0.12), stop:1 transparent);
                    border-left: 2px solid {C['cyan']};
                }}
            """)
        else:
            lbl.setFont(QFont("Segoe UI", 10))
            lbl.setStyleSheet(f"""
                QLabel {{
                    color: {C['dim']};
                    padding-left: 22px;
                    background: transparent;
                    border-left: 2px solid transparent;
                }}
            """)
        return lbl

    def _sidebar_modul(self, baslik, deger):
        """Dinamik modül durumu gösteren sidebar öğesi."""
        container = QWidget()
        container.setFixedHeight(52)
        container.setStyleSheet(f"""
            QWidget {{
                background: transparent;
                border-left: 2px solid {C['border']};
            }}
            QWidget:hover {{
                background: rgba(0, 180, 255, 0.04);
                border-left: 2px solid {C['cyan_dim']};
            }}
        """)
        vlay = QVBoxLayout(container)
        vlay.setContentsMargins(18, 5, 10, 5)
        vlay.setSpacing(2)

        baslik_lbl = QLabel(baslik)
        baslik_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        baslik_lbl.setStyleSheet(f"color: {C['text']}; background: transparent; border: none;")
        vlay.addWidget(baslik_lbl)

        deger_lbl = QLabel(deger)
        deger_lbl.setFont(QFont("Consolas", 8))
        deger_lbl.setStyleSheet(f"color: {C['cyan_dim']}; background: transparent; border: none;")
        vlay.addWidget(deger_lbl)

        # Doğrudan referans — findChildren yerine
        container._deger_lbl = deger_lbl

        return container

    # ═══════════════════ ORTA — KÜRE + KARŞILAMA ═══════════════════

    def _build_center(self):
        container = QWidget()
        container.setStyleSheet(f"background: {C['bg']};")
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 16)
        lay.setSpacing(0)

        # Küre
        self.kure = OrganikKureWidget()
        lay.addWidget(self.kure, stretch=1)

        # Karşılama metni
        self.karsilama_label = QLabel("Hoş geldin")
        self.karsilama_label.setFont(QFont("Segoe UI Light", 20))
        self.karsilama_label.setStyleSheet(f"color:{C['cyan']}; background:transparent;")
        self.karsilama_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.karsilama_label)

        self.alt_mesaj = QLabel("ATLAS: Nasıl yardımcı olabilirim?")
        self.alt_mesaj.setFont(QFont("Segoe UI", 10))
        self.alt_mesaj.setStyleSheet(f"color:{C['dim']}; background:transparent;")
        self.alt_mesaj.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.alt_mesaj)

        lay.addSpacing(4)

        self.ipucu_label = QLabel("Soru sor, bilgisayarını yönet veya sohbet et...")
        self.ipucu_label.setFont(QFont("Segoe UI", 9))
        self.ipucu_label.setStyleSheet(f"color:{C['dim2']}; background:transparent;")
        self.ipucu_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.ipucu_label)

        lay.addSpacing(8)

        return container

    # ═══════════════════ SAĞ SOHBET PANELİ ═══════════════════

    def _build_chat_panel(self):
        panel = QFrame()
        panel.setFixedWidth(300)
        panel.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, x2:1,
                    stop:0 {C['bg']}, stop:1 {C['chat_bg']});
                border-left: 1px solid {C['border']};
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 16, 14, 12)
        lay.setSpacing(8)

        # Başlık
        header = QLabel("SOHBET HİKAYESİ")
        header.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        header.setStyleSheet(f"color:{C['dim']}; letter-spacing:2px; background:transparent;")
        lay.addWidget(header)

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            f"background: qlineargradient(x1:0,x2:1,"
            f"stop:0 {C['cyan_dim']}, stop:0.7 {C['border']}, stop:1 transparent);"
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
                padding: 4px;
                selection-background-color: {C['cyan_dim']};
            }}
            QScrollBar:vertical {{
                background: transparent;
                width: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {C['cyan_dim']};
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background:transparent; }}
        """)
        lay.addWidget(self.konusma_alani)

        return panel

    # ═══════════════════ SİNYALLER ═══════════════════

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
            renk_isim = C['cyan']
            isim = "Sen"
            bg_renk = C['bubble_user']
        elif rol == "asistan":
            renk_isim = C['teal']
            isim = "ATLAS"
            bg_renk = C['bubble_atlas']
        elif rol == "sistem":
            renk_isim = C['dim']
            isim = "Sistem"
            bg_renk = "#080e1e"
        else:
            renk_isim = C['text']
            isim = rol.capitalize()
            bg_renk = C['bubble_user']

        html = (
            f'<table width="100%" cellpadding="8" cellspacing="0" border="0" '
            f'style="margin:3px 0;">'
            f'<tr><td bgcolor="{bg_renk}">'
            f'<font color="{renk_isim}" size="2"><b>{isim}</b></font>'
            f'<font color="{C["dim"]}" size="1"> {zaman}</font><br/>'
            f'<font color="{C["text"]}">{mesaj}</font>'
            f'</td></tr></table>'
        )
        self.konusma_alani.append(html)
        sb = self.konusma_alani.verticalScrollBar()
        sb.setValue(sb.maximum())

        # Karşılama metnini güncelle (son Atlas mesajı)
        if rol == "asistan" and len(mesaj) < 80:
            self.alt_mesaj.setText(f"ATLAS: {mesaj}")

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
            "pasif":  "Pasif Dinleme",
            "aktif":  "Aktif Dinleme",
            "isim":   "İsim Öğrenme",
            "mesgul": "İşleniyor...",
        }
        text = mod_str.get(mod, mod)
        self.dikkat_val.setText(text)
        self.kure.set_mod(mod)
        # Sidebar beyin modülü güncelle — aktif modlarda parlak renk
        aktif = mod in ("aktif", "mesgul", "isim")
        self._sidebar_modul_guncelle(self.sidebar_beyin, text, aktif=aktif)

    def _bellek_guncelle(self, durum):
        toplam = durum.get("toplam_etkilesim", 0)
        calisma = durum.get("calisma_bellegi", 0)
        text = f"{calisma}/7 aktif · {toplam} toplam"
        self.hafiza_val.setText(text)
        # Sidebar hafıza modülü güncelle
        self._sidebar_modul_guncelle(self.sidebar_hafiza, text, aktif=toplam > 0)

    def _duygu_guncelle(self, duygu):
        duygular = {
            "mutlu": "Mutlu", "uzgun": "Üzgün",
            "sinirli": "Sinirli", "merakli": "Meraklı",
            "aceleci": "Aceleci", "notr": "Nötr",
        }
        text = duygular.get(duygu, duygu.capitalize())
        self.duygu_val.setText(text)
        # Sidebar duygu modülü güncelle
        self._sidebar_modul_guncelle(self.sidebar_duygu, text, aktif=duygu != "notr")

    def _hata_goster(self, hata):
        self._mesaj_ekle("sistem", f"⚠️ {hata}")

    def _surum_goster(self, surum):
        self.surum_label.setText(f"v{surum}")

    def _ses_seviyesi_slot(self, seviye):
        self.kure.set_ses_seviyesi(seviye)

    def set_kullanici_adi(self, isim):
        self._kullanici_adi = isim
        if isim:
            self.karsilama_label.setText(f"Hoş geldin, {isim}")
        else:
            self.karsilama_label.setText("Hoş geldin")

    def _sidebar_modul_guncelle(self, container, deger_text, aktif=False):
        """Sidebar modül widget'ının değer label'ını güncelle."""
        try:
            lbl = container._deger_lbl
            lbl.setText(deger_text)
            # Aktif durumda parlak, pasif durumda soluk
            if aktif:
                lbl.setStyleSheet(f"color: {C['cyan']}; background: transparent; border: none;")
            else:
                lbl.setStyleSheet(f"color: {C['cyan_dim']}; background: transparent; border: none;")
        except Exception:
            pass

    def _saat_guncelle(self):
        simdi = datetime.now()
        self.saat_ust.setText(simdi.strftime("%H:%M"))
        gunler = {0:"Pzt",1:"Sal",2:"Çar",3:"Per",4:"Cum",5:"Cmt",6:"Paz"}
        aylar = {1:"Oca",2:"Şub",3:"Mar",4:"Nis",5:"May",6:"Haz",
                 7:"Tem",8:"Ağu",9:"Eyl",10:"Eki",11:"Kas",12:"Ara"}
        self.tarih_label.setText(
            f"{gunler.get(simdi.weekday(),'')}  {simdi.day} {aylar.get(simdi.month,'')}"
        )
