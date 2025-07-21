# Dosya Adı: arayuz/widgetlar/odeme_paneli.py
# Oluşturma Tarihi / Saati: 17.07.2025 / 11:30
# Yapılan İşlem: Modern, numerik tuş takımlı ödeme paneli oluşturuldu.

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGridLayout, QFrame)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
from decimal import Decimal, InvalidOperation

# ===== OdemePaneli SINIFI BAŞLANGICI =====
class OdemePaneli(QDialog):
    def __init__(self, toplam_tutar: Decimal, musteri_adi: str | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ödeme")
        self.setMinimumSize(600, 400)
        
        self.toplam_tutar = toplam_tutar
        self.musteri_adi = musteri_adi
        self.odemeler = []
        self.aktif_odeme_tipi = 'Nakit'

        self._arayuzu_olustur()
        self._tutar_guncelle()

    def _arayuzu_olustur(self):
        self.ana_layout = QHBoxLayout(self)
        self.ana_layout.setSpacing(15)

        # Sol Panel: Tutar Bilgileri ve Ödeme Tipleri
        sol_panel = QVBoxLayout()
        
        self.toplam_tutar_label = QLabel(f"Toplam Tutar: {self.toplam_tutar:.2f} ₺")
        self.toplam_tutar_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.odenen_tutar_label = QLabel("Ödenen: 0.00 ₺")
        self.odenen_tutar_label.setStyleSheet("font-size: 18px; color: green;")
        
        self.kalan_tutar_label = QLabel(f"Kalan: {self.toplam_tutar:.2f} ₺")
        self.kalan_tutar_label.setStyleSheet("font-size: 18px; color: red;")

        self.para_ustu_label = QLabel("Para Üstü: 0.00 ₺")
        self.para_ustu_label.setStyleSheet("font-size: 18px; color: blue;")
        
        sol_panel.addWidget(self.toplam_tutar_label)
        sol_panel.addWidget(self.odenen_tutar_label)
        sol_panel.addWidget(self.kalan_tutar_label)
        sol_panel.addWidget(self.para_ustu_label)
        sol_panel.addStretch()

        self.nakit_btn = QPushButton("Nakit")
        self.kart_btn = QPushButton("Kredi Kartı")
        self.veresiye_btn = QPushButton("Veresiye")
        
        self.nakit_btn.clicked.connect(lambda: self._odeme_tipi_sec('Nakit'))
        self.kart_btn.clicked.connect(lambda: self._odeme_tipi_sec('Kredi Kartı'))
        self.veresiye_btn.clicked.connect(self._veresiye_ekle)
        
        if not self.musteri_adi:
            self.veresiye_btn.setEnabled(False)

        sol_panel.addWidget(self.nakit_btn)
        sol_panel.addWidget(self.kart_btn)
        sol_panel.addWidget(self.veresiye_btn)

        # Sağ Panel: Numpad ve Onay
        sag_panel = QVBoxLayout()
        self.girilen_tutar_display = QLineEdit("0")
        self.girilen_tutar_display.setAlignment(Qt.AlignRight)
        self.girilen_tutar_display.setReadOnly(True)
        self.girilen_tutar_display.setFixedHeight(40)
        self.girilen_tutar_display.setStyleSheet("font-size: 20px; background-color: #eee;")
        sag_panel.addWidget(self.girilen_tutar_display)

        numpad_layout = QGridLayout()
        butonlar = ['7', '8', '9', '4', '5', '6', '1', '2', '3', 'C', '0', '.']
        pozisyonlar = [(i, j) for i in range(4) for j in range(3)]
        for poz, metin in zip(pozisyonlar, butonlar):
            buton = QPushButton(metin)
            buton.setFixedSize(60, 60)
            buton.clicked.connect(self._numpad_tiklandi)
            numpad_layout.addWidget(buton, *poz)
        sag_panel.addLayout(numpad_layout)

        self.onayla_btn = QPushButton("Satışı Tamamla")
        self.onayla_btn.setFixedHeight(50)
        self.onayla_btn.setStyleSheet("background-color: #28a745; color: white; font-size: 16px; font-weight: bold;")
        self.onayla_btn.clicked.connect(self.accept)
        sag_panel.addWidget(self.onayla_btn)

        self.ana_layout.addLayout(sol_panel, 1)
        self.ana_layout.addLayout(sag_panel, 1)
        
        self._odeme_tipi_sec('Nakit') # Başlangıçta Nakit seçili olsun

    def _odeme_tipi_sec(self, tip):
        self.aktif_odeme_tipi = tip
        self.nakit_btn.setStyleSheet("background-color: lightgray;")
        self.kart_btn.setStyleSheet("background-color: lightgray;")
        if tip == 'Nakit':
            self.nakit_btn.setStyleSheet("background-color: #007bff; color: white;")
        else:
            self.kart_btn.setStyleSheet("background-color: #007bff; color: white;")
        self.girilen_tutar_display.setText("0")

    def _numpad_tiklandi(self):
        gonderen_buton = self.sender()
        deger = gonderen_buton.text()
        mevcut_deger = self.girilen_tutar_display.text()

        if deger == 'C':
            self.girilen_tutar_display.setText("0")
        elif deger == '.' and '.' in mevcut_deger:
            return
        else:
            if mevcut_deger == "0" and deger != '.':
                self.girilen_tutar_display.setText(deger)
            else:
                self.girilen_tutar_display.setText(mevcut_deger + deger)
        
        self._odeme_listesini_guncelle()

    def _odeme_listesini_guncelle(self):
        try:
            girilen_tutar = Decimal(self.girilen_tutar_display.text())
        except InvalidOperation:
            girilen_tutar = Decimal('0.00')

        # Aktif ödeme tipini listeden bul ve güncelle
        found = False
        for odeme in self.odemeler:
            if odeme['yontem'] == self.aktif_odeme_tipi:
                odeme['tutar'] = girilen_tutar
                found = True
                break
        if not found and girilen_tutar > 0:
            self.odemeler.append({'yontem': self.aktif_odeme_tipi, 'tutar': girilen_tutar})
        
        # Sadece 0 olanları listeden çıkar
        self.odemeler = [o for o in self.odemeler if o['tutar'] > 0]
        self._tutar_guncelle()

    def _tutar_guncelle(self):
        odenen_tutar = sum(o['tutar'] for o in self.odemeler)
        kalan_tutar = self.toplam_tutar - odenen_tutar
        para_ustu = Decimal('0.00')

        if kalan_tutar < 0:
            para_ustu = -kalan_tutar
            kalan_tutar = Decimal('0.00')

        self.odenen_tutar_label.setText(f"Ödenen: {odenen_tutar:.2f} ₺")
        self.kalan_tutar_label.setText(f"Kalan: {kalan_tutar:.2f} ₺")
        self.para_ustu_label.setText(f"Para Üstü: {para_ustu:.2f} ₺")

    def _veresiye_ekle(self):
        self._odeme_listesini_guncelle()
        kalan_tutar = self.toplam_tutar - sum(o['tutar'] for o in self.odemeler)
        if kalan_tutar > 0:
            self.odemeler.append({'yontem': 'Veresiye', 'tutar': kalan_tutar})
            self._tutar_guncelle()
            self.accept() # Veresiye eklenince otomatik tamamla
        
    def bilgileri_al(self):
        self._odeme_listesini_guncelle()
        return self.odemeler
