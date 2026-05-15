"""
ATLAS - JARVIS Arayüz
=====================
Iron Man JARVIS tarzı futuristik GUI.
Animasyonlu Arc Reactor, holografik paneller, ses dalgası göstergesi.
PyQt6 tabanlı.
"""

import math
import random
import sys
import time
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
    QFont, QColor, QPainter, QPen, QRadialGradient, QPixmap, QIcon
)

logger = logging.getLogger("ATLAS.arayuz")


# ============================================================
# JARVIS RENK PALETİ
# ============================================================

J = {
    "bg":        "#05050f",
    "panel":     "#0a0f1a",
    "panel2":    "#0d1525",
    "border":    "#152035",
    "border_hi": "#1a3050",
    "cyan":      "#00c8ff",
    "cyan_dim":  "#005577",
    "cyan_glow": "#0088cc",
    "green":     "#00ff88",
    "green_dim": "#008844",
    "orange":    "#ff8800",
    "red":       "#ff3333",
    "text":      "#c0d0e0",
    "text_hi":   "#e0eeff",
    "dim":       "#4a5a70",
}


# ============================================================
# ARC REACTOR WİDGET — Animasyonlu JARVIS HUD
# ============================================================

class ArcReactorWidget(QWidget):
    """
    Iron Man Arc Reactor animasyonu.
    Dönen halkalar, parlayan merkez, ses dalgası barları.
    Durum moduna göre renk ve hız değişir.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(250, 250)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Animasyon durumu
        self._angle = 0.0
        self._pulse = 0.0
        self._mod = "pasif"
        self._durum_text = "Başlatılıyor..."

        # Mod bazlı hızlar
        self._hizlar = {
            "pasif":  {"donus": 0.3, "nabiz": 1.5},
            "aktif":  {"donus": 1.2, "nabiz": 2.5},
            "isim":   {"donus": 0.8, "nabiz": 2.0},
            "mesgul": {"donus": 2.5, "nabiz": 4.0},
        }

        # Ses dalgası barları
        self._wave_bars = [0.0] * 16
        self._wave_hedef = [0.0] * 16

        # Animasyon timer (~30 FPS)
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

        # Ses dalgası animasyonu
        if self._mod in ("aktif", "isim"):
            self._wave_hedef = [random.uniform(0.15, 0.85) for _ in range(16)]
        elif self._mod == "mesgul":
            t = time.time()
            self._wave_hedef = [
                0.25 + 0.55 * abs(math.sin(t * 3.5 + i * 0.45))
                for i in range(16)
            ]
        else:
            self._wave_hedef = [0.03 + 0.03 * abs(math.sin(time.time() * 0.5 + i * 0.3)) for i in range(16)]

        for i in range(16):
            self._wave_bars[i] += (self._wave_hedef[i] - self._wave_bars[i]) * 0.18

        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w / 2, h / 2 - 10
        max_r = min(w, h) / 2 - 20

        pv = (math.sin(math.radians(self._pulse)) + 1) / 2  # 0..1

        # ── Mod renkleri ──
        if self._mod == "mesgul":
            c_ana = QColor(255, 136, 0)
            c_parlak = QColor(255, 180, 60)
            c_soluk = QColor(180, 80, 0)
        elif self._mod in ("aktif", "isim"):
            c_ana = QColor(0, 200, 255)
            c_parlak = QColor(120, 235, 255)
            c_soluk = QColor(0, 100, 180)
        else:
            c_ana = QColor(0, 120, 180)
            c_parlak = QColor(0, 160, 220)
            c_soluk = QColor(0, 50, 90)

        def renk_alpha(renk, alpha):
            return QColor(renk.red(), renk.green(), renk.blue(), int(alpha))

        # ── 1. Arka plan parıltı ──
        glow = QRadialGradient(cx, cy, max_r * 1.1)
        ga = int(30 + 18 * pv)
        glow.setColorAt(0, renk_alpha(c_ana, ga))
        glow.setColorAt(0.5, renk_alpha(c_ana, ga // 4))
        glow.setColorAt(1, QColor(0, 0, 0, 0))
        p.fillRect(self.rect(), glow)

        # ── 2. Dış halka (ince, soluk) ──
        r1 = max_r * 0.94
        p.setPen(QPen(renk_alpha(c_soluk, int(70 + 40 * pv)), 1.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(cx, cy), r1, r1)

        # ── 3. Çentik işaretleri (36 adet) ──
        r_in = max_r * 0.91
        r_out = max_r * 0.96
        p.setPen(QPen(renk_alpha(c_soluk, 45), 0.8))
        for i in range(36):
            ang = math.radians(i * 10)
            p.drawLine(
                QPointF(cx + r_in * math.cos(ang), cy + r_in * math.sin(ang)),
                QPointF(cx + r_out * math.cos(ang), cy + r_out * math.sin(ang))
            )

        # ── 4. Dış dönen yaylar (4 parça) ──
        r2 = max_r * 0.87
        rect2 = QRectF(cx - r2, cy - r2, r2 * 2, r2 * 2)
        p.setPen(QPen(renk_alpha(c_ana, int(160 + 60 * pv)), 2.5))
        for i in range(4):
            start = int((self._angle + i * 90) * 16)
            p.drawArc(rect2, start, int(55 * 16))

        # ── 5. Orta halka ──
        r3 = max_r * 0.70
        p.setPen(QPen(renk_alpha(c_soluk, int(50 + 30 * pv)), 1))
        p.drawEllipse(QPointF(cx, cy), r3, r3)

        # ── 6. İç dönen yaylar (6 parça, ters yön) ──
        r4 = max_r * 0.60
        rect4 = QRectF(cx - r4, cy - r4, r4 * 2, r4 * 2)
        p.setPen(QPen(renk_alpha(c_parlak, int(140 + 60 * pv)), 2))
        for i in range(6):
            start = int((-self._angle * 1.5 + i * 60) * 16)
            p.drawArc(rect4, start, int(28 * 16))

        # ── 7. İç çekirdek (gradient daire) ──
        r5 = max_r * 0.36
        ca = int(110 + 80 * pv)
        core = QRadialGradient(cx, cy, r5)
        core.setColorAt(0, renk_alpha(c_parlak, ca))
        core.setColorAt(0.5, renk_alpha(c_ana, ca // 2))
        core.setColorAt(1, QColor(0, 0, 0, 0))
        p.setBrush(core)
        p.setPen(QPen(renk_alpha(c_parlak, int(160 + 60 * pv)), 1.5))
        p.drawEllipse(QPointF(cx, cy), r5, r5)

        # ── 8. Artı çizgileri ──
        cr = max_r * 0.33
        p.setPen(QPen(renk_alpha(c_ana, 35), 0.5))
        p.drawLine(QPointF(cx - cr, cy), QPointF(cx + cr, cy))
        p.drawLine(QPointF(cx, cy - cr), QPointF(cx, cy + cr))

        # ── 9. Üçgen detay (iç) ──
        r6 = max_r * 0.22
        p.setPen(QPen(renk_alpha(c_ana, int(60 + 30 * pv)), 1))
        pts = []
        for i in range(3):
            ang = math.radians(self._angle * 0.5 + i * 120 - 90)
            pts.append(QPointF(cx + r6 * math.cos(ang), cy + r6 * math.sin(ang)))
        for i in range(3):
            p.drawLine(pts[i], pts[(i + 1) % 3])

        # ── 10. ATLAS yazısı ──
        p.setPen(QColor(255, 255, 255, int(210 + 30 * pv)))
        font_a = QFont("Consolas", 14, QFont.Weight.Bold)
        font_a.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 5)
        p.setFont(font_a)
        p.drawText(QRectF(cx - 80, cy - 12, 160, 26), Qt.AlignmentFlag.AlignCenter, "ATLAS")

        # ── 11. Durum metni ──
        p.setPen(renk_alpha(c_ana, int(150 + 70 * pv)))
        font_d = QFont("Segoe UI", 9)
        p.setFont(font_d)
        p.drawText(
            QRectF(cx - 130, cy + 18, 260, 22),
            Qt.AlignmentFlag.AlignCenter,
            self._durum_text
        )

        # ── 12. Ses dalgası barları ──
        wave_y = cy + max_r * 0.58
        total_w = max_r * 1.4
        bar_w = total_w / (len(self._wave_bars) + 2)
        x_start = cx - total_w / 2

        for i in range(len(self._wave_bars)):
            bar_h = self._wave_bars[i] * max_r * 0.18
            bx = x_start + (i + 1) * bar_w
            by = wave_y - bar_h / 2
            alpha = int(80 + 120 * self._wave_bars[i])
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(renk_alpha(c_ana, alpha))
            p.drawRoundedRect(QRectF(bx - bar_w * 0.25, by, bar_w * 0.5, bar_h), 2, 2)

        # ── 13. Dış dekoratif çizgiler ──
        for ang_deg in [30, 150, 210, 330]:
            ang = math.radians(ang_deg + self._angle * 0.2)
            r_start = max_r * 0.97
            r_end = max_r * 1.05
            p.setPen(QPen(renk_alpha(c_soluk, 30), 0.8))
            p.drawLine(
                QPointF(cx + r_start * math.cos(ang), cy + r_start * math.sin(ang)),
                QPointF(cx + r_end * math.cos(ang), cy + r_end * math.sin(ang))
            )

        p.end()

    def sizeHint(self):
        return QSize(350, 350)


# ============================================================
# SİNYAL KÖPRÜsü (Thread → GUI)
# ============================================================

class GuiSinyalleri(QObject):
    """Thread-safe sinyal köprüsü"""
    mesaj_ekle = pyqtSignal(str, str)
    durum_guncelle = pyqtSignal(str)
    mod_guncelle = pyqtSignal(str)
    bellek_guncelle = pyqtSignal(dict)
    hata_goster = pyqtSignal(str)
    surum_goster = pyqtSignal(str)
    duygu_guncelle = pyqtSignal(str)


# ============================================================
# ANA PENCERE — JARVIS
# ============================================================

class AtlasArayuz(QMainWindow):
    """ATLAS JARVIS tarzı ana pencere"""

    def __init__(self):
        super().__init__()
        self.sinyaller = GuiSinyalleri()
        self._setup_ui()
        self._connect_signals()

    # ────────────────────────────────────────────
    # UI KURULUMU
    # ────────────────────────────────────────────

    def _setup_ui(self):
        self.setWindowTitle("ATLAS — Sesli AI Asistan")
        self.setMinimumSize(900, 650)
        self.resize(1000, 720)
        self._set_window_icon()

        # Global stil
        self.setStyleSheet(f"""
            QMainWindow {{ background: {J['bg']}; }}
            QWidget {{ background: transparent; color: {J['text']}; }}
        """)

        merkez = QWidget()
        self.setCentralWidget(merkez)
        ana = QVBoxLayout(merkez)
        ana.setContentsMargins(0, 0, 0, 0)
        ana.setSpacing(0)

        # ── ÜST BAR ──
        ana.addWidget(self._build_top_bar())

        # ── ORTA: Arc Reactor + Durum Paneli ──
        orta = QWidget()
        orta.setStyleSheet(f"background: {J['bg']};")
        orta_l = QHBoxLayout(orta)
        orta_l.setContentsMargins(0, 0, 0, 0)
        orta_l.setSpacing(0)

        self.reactor = ArcReactorWidget()
        orta_l.addWidget(self.reactor, stretch=3)
        orta_l.addWidget(self._build_status_panel())

        ana.addWidget(orta, stretch=3)

        # ── AYIRICI ──
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(
            f"background: qlineargradient(x1:0, x2:1, "
            f"stop:0 transparent, stop:0.2 {J['cyan_dim']}, "
            f"stop:0.8 {J['cyan_dim']}, stop:1 transparent);"
        )
        ana.addWidget(sep)

        # ── KONUŞMA ALANI ──
        ana.addWidget(self._build_conversation(), stretch=2)

        # ── ALT BAR ──
        ana.addWidget(self._build_bottom_bar())

        # Saat timer
        self._saat_timer = QTimer()
        self._saat_timer.timeout.connect(self._saat_guncelle)
        self._saat_timer.start(1000)
        self._saat_guncelle()

    def _set_window_icon(self):
        """Pencere ikonu oluştur (A harfli mavi daire)"""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.GlobalColor.transparent)
        pp = QPainter(pixmap)
        pp.setRenderHint(QPainter.RenderHint.Antialiasing)
        pp.setPen(QPen(QColor(0, 200, 255), 3))
        pp.setBrush(QColor(0, 50, 100, 160))
        pp.drawEllipse(5, 5, 54, 54)
        pp.setPen(QPen(QColor(0, 200, 255), 1.5))
        pp.setBrush(QColor(0, 130, 220, 90))
        pp.drawEllipse(16, 16, 32, 32)
        pp.setPen(QColor(255, 255, 255, 240))
        pp.setFont(QFont("Consolas", 22, QFont.Weight.Bold))
        pp.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "A")
        pp.end()
        self.setWindowIcon(QIcon(pixmap))

    def _build_top_bar(self):
        bar = QFrame()
        bar.setFixedHeight(52)
        bar.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(y1:0, y2:1,
                    stop:0 {J['panel2']}, stop:1 {J['panel']});
                border-bottom: 1px solid {J['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(24, 0, 24, 0)

        # Logo
        logo = QLabel("◆ A T L A S")
        logo.setFont(QFont("Consolas", 16, QFont.Weight.Bold))
        logo.setStyleSheet(f"color: {J['cyan']}; letter-spacing: 5px; background: transparent;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setColor(QColor(0, 200, 255, 100))
        glow.setOffset(0, 0)
        logo.setGraphicsEffect(glow)
        lay.addWidget(logo)

        lay.addStretch()

        # Sürüm
        self.surum_label = QLabel("v8.2")
        self.surum_label.setFont(QFont("Consolas", 9))
        self.surum_label.setStyleSheet(f"color: {J['dim']}; background: transparent;")
        lay.addWidget(self.surum_label)

        # Ayırıcı
        sep = QLabel("│")
        sep.setStyleSheet(f"color: {J['border']}; background: transparent; margin: 0 10px;")
        lay.addWidget(sep)

        # Saat
        self.saat_ust = QLabel("--:--")
        self.saat_ust.setFont(QFont("Consolas", 12, QFont.Weight.Bold))
        self.saat_ust.setStyleSheet(f"color: {J['text_hi']}; background: transparent;")
        lay.addWidget(self.saat_ust)

        return bar

    def _build_status_panel(self):
        panel = QFrame()
        panel.setFixedWidth(210)
        panel.setStyleSheet(f"""
            QFrame {{
                background: {J['panel']};
                border-left: 1px solid {J['border']};
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(14, 16, 14, 16)
        lay.setSpacing(10)

        # Başlık
        baslik = QLabel("BEYİN DURUMU")
        baslik.setFont(QFont("Consolas", 8, QFont.Weight.Bold))
        baslik.setStyleSheet(
            f"color: {J['cyan']}; letter-spacing: 2px; border: none; background: transparent;"
        )
        lay.addWidget(baslik)

        # Durum kartları
        self.dikkat_kart = self._build_card("DİKKAT", "Başlatılıyor...", J['cyan'])
        self.duygu_kart = self._build_card("DUYGU", "—", J['green'])
        self.hafiza_kart = self._build_card("HAFIZA", "0 kayıt", J['cyan'])
        self.karar_kart = self._build_card("KARAR", "Hazır", J['orange'])

        lay.addWidget(self.dikkat_kart)
        lay.addWidget(self.duygu_kart)
        lay.addWidget(self.hafiza_kart)
        lay.addWidget(self.karar_kart)

        lay.addStretch()

        # Tarih
        self.tarih_label = QLabel("")
        self.tarih_label.setFont(QFont("Consolas", 9))
        self.tarih_label.setStyleSheet(f"color: {J['dim']}; border: none; background: transparent;")
        self.tarih_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.tarih_label)

        return panel

    def _build_card(self, baslik, deger, accent_color):
        """Holografik durum kartı"""
        kart = QFrame()
        kart.setStyleSheet(f"""
            QFrame {{
                background: {J['bg']};
                border: 1px solid {J['border']};
                border-left: 3px solid {accent_color};
                border-radius: 4px;
            }}
        """)
        lay = QVBoxLayout(kart)
        lay.setContentsMargins(10, 6, 8, 6)
        lay.setSpacing(1)

        b = QLabel(baslik)
        b.setFont(QFont("Consolas", 7, QFont.Weight.Bold))
        b.setStyleSheet(
            f"color: {J['dim']}; letter-spacing: 1px; border: none; background: transparent;"
        )
        lay.addWidget(b)

        d = QLabel(deger)
        d.setObjectName("deger")
        d.setFont(QFont("Segoe UI", 10))
        d.setStyleSheet(f"color: {J['text']}; border: none; background: transparent;")
        lay.addWidget(d)

        return kart

    def _build_conversation(self):
        """Konuşma alanı"""
        w = QWidget()
        w.setStyleSheet(f"background: {J['bg']};")
        lay = QVBoxLayout(w)
        lay.setContentsMargins(20, 8, 20, 8)
        lay.setSpacing(4)

        header = QLabel("── KONUŞMA ──────────────────────────────────")
        header.setFont(QFont("Consolas", 8))
        header.setStyleSheet(f"color: {J['dim']}; letter-spacing: 1px;")
        lay.addWidget(header)

        self.konusma_alani = QTextEdit()
        self.konusma_alani.setReadOnly(True)
        self.konusma_alani.setFont(QFont("Segoe UI", 10))
        self.konusma_alani.setStyleSheet(f"""
            QTextEdit {{
                background: {J['bg']};
                color: {J['text']};
                border: none;
                padding: 6px;
                selection-background-color: {J['cyan_dim']};
            }}
            QScrollBar:vertical {{
                background: {J['panel']};
                width: 6px;
                border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {J['border_hi']};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        lay.addWidget(self.konusma_alani)

        return w

    def _build_bottom_bar(self):
        bar = QFrame()
        bar.setFixedHeight(36)
        bar.setStyleSheet(f"""
            QFrame {{
                background: {J['panel']};
                border-top: 1px solid {J['border']};
            }}
        """)
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(20, 0, 20, 0)

        self.durum_nokta = QLabel("●")
        self.durum_nokta.setFont(QFont("Segoe UI", 9))
        self.durum_nokta.setStyleSheet(f"color: {J['green']}; background: transparent;")
        lay.addWidget(self.durum_nokta)

        self.durum_label = QLabel("Başlatılıyor...")
        self.durum_label.setFont(QFont("Segoe UI", 9))
        self.durum_label.setStyleSheet(f"color: {J['dim']}; background: transparent;")
        lay.addWidget(self.durum_label)

        lay.addStretch()

        return bar

    # ────────────────────────────────────────────
    # SİNYAL BAĞLANTILARI
    # ────────────────────────────────────────────

    def _connect_signals(self):
        self.sinyaller.mesaj_ekle.connect(self._mesaj_ekle)
        self.sinyaller.durum_guncelle.connect(self._durum_guncelle)
        self.sinyaller.mod_guncelle.connect(self._mod_guncelle)
        self.sinyaller.bellek_guncelle.connect(self._bellek_guncelle)
        self.sinyaller.hata_goster.connect(self._hata_goster)
        self.sinyaller.surum_goster.connect(self._surum_goster)
        self.sinyaller.duygu_guncelle.connect(self._duygu_guncelle)

    # ────────────────────────────────────────────
    # SİNYAL SLOTLARI
    # ────────────────────────────────────────────

    def _mesaj_ekle(self, rol, mesaj):
        zaman = datetime.now().strftime("%H:%M")

        if rol == "kullanici":
            renk = J['cyan']
            ikon = "▸"
            isim = "SEN"
        elif rol == "asistan":
            renk = J['green']
            ikon = "◆"
            isim = "ATLAS"
        elif rol == "sistem":
            renk = J['dim']
            ikon = "⚙"
            isim = "SİSTEM"
        else:
            renk = J['text']
            ikon = "•"
            isim = rol.upper()

        html = (
            f'<div style="margin:3px 0; padding:2px 0; font-family:Segoe UI,sans-serif;">'
            f'<span style="color:{J["dim"]}; font-size:9px; font-family:Consolas;">{zaman}</span>'
            f'<span style="color:{renk}; font-weight:600;"> {ikon} {isim}</span>'
            f'<span style="color:{J["text"]};"> {mesaj}</span>'
            f'</div>'
        )
        self.konusma_alani.append(html)
        sb = self.konusma_alani.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _durum_guncelle(self, durum):
        self.durum_label.setText(durum)
        self.reactor.set_durum(durum)

        dl = durum.lower()
        if "hata" in dl or "bağlantı" in dl:
            self.durum_nokta.setStyleSheet(f"color: {J['red']}; background: transparent;")
        elif "dinl" in dl or "bekl" in dl or "hazır" in dl:
            self.durum_nokta.setStyleSheet(f"color: {J['green']}; background: transparent;")
        elif "düşün" in dl or "oluş" in dl or "işlen" in dl:
            self.durum_nokta.setStyleSheet(f"color: {J['orange']}; background: transparent;")
        else:
            self.durum_nokta.setStyleSheet(f"color: {J['cyan']}; background: transparent;")

    def _mod_guncelle(self, mod):
        mod_str = {
            "pasif": "🔇 Pasif Dinleme",
            "aktif": "🎙️ Aktif Dinleme",
            "isim": "👤 İsim Öğrenme",
            "mesgul": "💭 İşleniyor...",
        }
        self._kart_deger(self.dikkat_kart, mod_str.get(mod, mod))
        self.reactor.set_mod(mod)

    def _bellek_guncelle(self, durum):
        toplam = durum.get("toplam_etkilesim", 0)
        calisma = durum.get("calisma_bellegi", 0)
        self._kart_deger(self.hafiza_kart, f"💬 {calisma}/7 | 📊 {toplam}")

    def _duygu_guncelle(self, duygu):
        emojiler = {
            "mutlu": "😊 Mutlu",
            "uzgun": "😔 Üzgün",
            "sinirli": "😤 Sinirli",
            "merakli": "🤔 Meraklı",
            "aceleci": "⚡ Aceleci",
            "notr": "😐 Nötr",
        }
        self._kart_deger(self.duygu_kart, emojiler.get(duygu, f"❓ {duygu}"))

    def _hata_goster(self, hata):
        self._mesaj_ekle("sistem", f"⚠️ {hata}")

    def _surum_goster(self, surum):
        self.surum_label.setText(f"v{surum}")

    # ────────────────────────────────────────────
    # YARDIMCI
    # ────────────────────────────────────────────

    def _kart_deger(self, kart, text):
        d = kart.findChild(QLabel, "deger")
        if d:
            d.setText(text)

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
