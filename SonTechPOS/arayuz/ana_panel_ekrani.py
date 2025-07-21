# Dosya Adı: arayuz/ana_panel_ekrani.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 13:00
# Yapılan İşlem: Eksik olan 'QColor' import'u eklendi.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, 
                             QToolButton, QLabel, QFrame, QSpacerItem, QSizePolicy)
from PyQt5.QtGui import QIcon, QFont, QPixmap, QColor # QColor import edildi
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QTime, QDate

class AnaPanelEkrani(QWidget):
    modul_ac_istegi = pyqtSignal(str)

    def __init__(self, kullanici=None, parent=None):
        super().__init__(parent)
        self.aktif_kullanici = kullanici
        self._arayuzu_olustur()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        self.ana_layout.setContentsMargins(20, 10, 20, 20)

        ust_panel_layout = QHBoxLayout()
        self._zaman_etiketi_olustur(ust_panel_layout)
        ust_panel_layout.addStretch()
        self._kullanici_etiketi_olustur(ust_panel_layout)
        self.ana_layout.addLayout(ust_panel_layout)

        self.ana_layout.addStretch() 
        self.buton_grid_layout = QGridLayout()
        self.buton_grid_layout.setSpacing(20)
        self.buton_grid_layout.setAlignment(Qt.AlignCenter)
        self._modul_butonlari_olustur()
        self.ana_layout.addLayout(self.buton_grid_layout)
        self.ana_layout.addStretch()

    def _zaman_etiketi_olustur(self, layout):
        self.zaman_etiketi = QLabel()
        self.zaman_etiketi.setStyleSheet("font-size: 16px; font-weight: bold; color: #555;")
        layout.addWidget(self.zaman_etiketi)
        
        timer = QTimer(self)
        timer.timeout.connect(self._zamani_guncelle)
        timer.start(1000)
        self._zamani_guncelle()

    def _zamani_guncelle(self):
        simdiki_zaman = QTime.currentTime().toString('HH:mm:ss')
        simdiki_tarih = QDate.currentDate().toString('dd.MM.yyyy')
        self.zaman_etiketi.setText(f"{simdiki_tarih}\n{simdiki_zaman}")

    def _kullanici_etiketi_olustur(self, layout):
        kullanici_adi = "Misafir"
        if self.aktif_kullanici:
            kullanici_adi = self.aktif_kullanici.tam_ad or self.aktif_kullanici.kullanici_adi
        
        kullanici_etiketi = QLabel(kullanici_adi)
        kullanici_etiketi.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        kullanici_etiketi.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        ikon_etiketi = QLabel("👤")
        ikon_etiketi.setStyleSheet("font-size: 24px;")

        layout.addWidget(kullanici_etiketi)
        layout.addWidget(ikon_etiketi)

    def _modul_butonlari_olustur(self):
        self.butonlar = {}
        moduller = [
            ("Satış", "🛒", (0, 0), "#3498db", None),
            ("Raporlar", "📊", (0, 1), "#2ecc71", None),
            ("Ürünler", "📦", (0, 2), "#9b59b6", None),
            ("Stok", "📈", (1, 0), "#f1c40f", None),
            ("Alışlar", "🚚", (1, 1), "#e67e22", None),
            ("Müşteriler", "👥", (1, 2), "#1abc9c", None),
            ("Tedarikçiler", "🏭", (2, 0), "#34495e", 'admin'),
            ("Ayarlar", "⚙️", (2, 1), "#95a5a6", 'admin'),
            ("Kapat", "❌", (2, 2), "#e74c3c", None)
        ]

        for isim, ikon, pos, renk, yetki in moduller:
            if yetki == 'admin' and (not self.aktif_kullanici or self.aktif_kullanici.rol != 'admin'):
                continue

            buton = self._tek_buton_olustur(isim, ikon, renk)
            self.butonlar[isim] = buton
            self.buton_grid_layout.addWidget(buton, pos[0], pos[1])

    def _tek_buton_olustur(self, metin, ikon_str, renk):
        buton = QToolButton()
        buton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        buton.setFixedSize(180, 130)

        buton_layout = QVBoxLayout(buton)
        ikon_etiketi = QLabel(ikon_str)
        ikon_etiketi.setStyleSheet("font-size: 48px; color: white;")
        ikon_etiketi.setAlignment(Qt.AlignCenter)
        
        metin_etiketi = QLabel(metin)
        metin_etiketi.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        metin_etiketi.setAlignment(Qt.AlignCenter)
        
        buton_layout.addWidget(ikon_etiketi)
        buton_layout.addWidget(metin_etiketi)
        
        buton.setStyleSheet(f"""
            QToolButton {{
                background-color: {renk};
                border: none;
                border-radius: 10px;
            }}
            QToolButton:hover {{
                background-color: {self._renk_koyulastir(renk)};
            }}
        """)

        buton.clicked.connect(lambda checked, m=metin: self.modul_ac_istegi.emit(m))
        return buton

    def _renk_koyulastir(self, renk_hex, faktor=0.8):
        renk = QColor(renk_hex)
        koyu_renk = renk.darker(int(100 / faktor))
        return koyu_renk.name()
