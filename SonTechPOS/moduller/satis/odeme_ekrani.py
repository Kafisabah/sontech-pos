# Dosya Adı: moduller/satis/odeme_ekrani.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 15:30
# Yapılan İşlem: Arayüz, gönderilen görsellere uygun, modern bir ödeme paneline dönüştürüldü. Klavye kontrolleri ve kısayollar eklendi.

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QGridLayout, QFrame, QSizePolicy, QApplication, QShortcut)
from PyQt5.QtGui import QFont, QKeySequence
from PyQt5.QtCore import Qt
from decimal import Decimal, InvalidOperation

# ===== OdemeEkraniDialog SINIFI BAŞLANGICI =====
class OdemeEkraniDialog(QDialog):
    def __init__(self, toplam_tutar: Decimal, musteri_adi: str | None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ödeme")
        self.setMinimumSize(650, 450)
        
        self.toplam_tutar = toplam_tutar
        self.musteri_adi = musteri_adi
        self.odemeler = {} 
        self.aktif_odeme_tipi = 'Nakit'

        self._arayuzu_olustur()
        self._tutar_guncelle()
        self.girilen_tutar_display.setFocus()
        self.girilen_tutar_display.selectAll()

    def _arayuzu_olustur(self):
        self.setStyleSheet("QDialog { background-color: #f0f2f5; }")
        self.ana_layout = QHBoxLayout(self)
        self.ana_layout.setSpacing(15)

        sol_panel = self._sol_panel_olustur()
        sag_panel = self._sag_panel_olustur()

        self.ana_layout.addWidget(sol_panel, 1)
        self.ana_layout.addWidget(sag_panel, 1)
        
        self._odeme_tipi_sec('Nakit')
        self._kisayollari_ayarla()

    def _sol_panel_olustur(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)
        font_buyuk = QFont(); font_buyuk.setPointSize(22); font_buyuk.setBold(True)
        font_normal = QFont(); font_normal.setPointSize(14)
        
        self.toplam_tutar_label = QLabel(f"Toplam Tutar\n<span style='font-size: 28px; color: #007bff;'>{self.toplam_tutar:.2f} ₺</span>")
        self.toplam_tutar_label.setFont(font_buyuk)
        
        self.odenen_tutar_label = QLabel("Ödenen: 0.00 ₺"); self.odenen_tutar_label.setFont(font_normal)
        self.kalan_tutar_label = QLabel(f"Kalan: {self.toplam_tutar:.2f} ₺"); self.kalan_tutar_label.setFont(font_normal)
        self.kalan_tutar_label.setStyleSheet("color: red; font-weight: bold;")
        self.para_ustu_label = QLabel("Para Üstü: 0.00 ₺"); self.para_ustu_label.setFont(font_normal)
        self.para_ustu_label.setStyleSheet("color: blue; font-weight: bold;")

        layout.addWidget(self.toplam_tutar_label); layout.addSpacing(20)
        layout.addWidget(self.odenen_tutar_label); layout.addWidget(self.kalan_tutar_label)
        layout.addWidget(self.para_ustu_label); layout.addStretch()

        self.nakit_btn = QPushButton("Nakit (F1)")
        self.kart_btn = QPushButton("Kredi Kartı (F2)")
        self.veresiye_btn = QPushButton("Veresiye (F3)")
        
        for btn in [self.nakit_btn, self.kart_btn, self.veresiye_btn]:
            btn.setFixedHeight(50)
            btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        self.nakit_btn.clicked.connect(lambda: self._odeme_tipi_sec('Nakit'))
        self.kart_btn.clicked.connect(lambda: self._odeme_tipi_sec('Kredi Kartı'))
        self.veresiye_btn.clicked.connect(self._veresiye_ekle)
        
        if not self.musteri_adi: self.veresiye_btn.setEnabled(False)

        layout.addWidget(self.nakit_btn); layout.addWidget(self.kart_btn); layout.addWidget(self.veresiye_btn)
        return panel

    def _sag_panel_olustur(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        self.girilen_tutar_display = QLineEdit()
        self.girilen_tutar_display.setAlignment(Qt.AlignRight)
        self.girilen_tutar_display.setFixedHeight(50)
        self.girilen_tutar_display.setStyleSheet("font-size: 24px; background-color: #fff; border: 1px solid #ccc; border-radius: 5px;")
        self.girilen_tutar_display.textChanged.connect(self._odeme_listesini_guncelle)
        layout.addWidget(self.girilen_tutar_display)

        numpad_layout = QGridLayout()
        butonlar = ['7', '8', '9', '4', '5', '6', '1', '2', '3', 'C', '0', '.']
        pozisyonlar = [(i, j) for i in range(4) for j in range(3)]
        for poz, metin in zip(pozisyonlar, butonlar):
            buton = QPushButton(metin)
            buton.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            buton.clicked.connect(self._numpad_tiklandi)
            numpad_layout.addWidget(buton, *poz)
        
        hizli_para_layout = QHBoxLayout()
        for tutar in [5, 10, 20, 50, 100, 200]:
            buton = QPushButton(str(tutar))
            buton.clicked.connect(self._hizli_para_ekle)
            hizli_para_layout.addWidget(buton)

        layout.addLayout(numpad_layout)
        layout.addLayout(hizli_para_layout)

        self.onayla_btn = QPushButton("Satışı Tamamla (Enter)")
        self.onayla_btn.setFixedHeight(50)
        self.onayla_btn.setStyleSheet("background-color: #28a745; color: white; font-size: 16px; font-weight: bold;")
        self.onayla_btn.clicked.connect(self.accept)
        layout.addWidget(self.onayla_btn)
        return panel
    
    def _odeme_tipi_sec(self, tip):
        self.aktif_odeme_tipi = tip
        self.nakit_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.kart_btn.setStyleSheet("font-size: 14px; font-weight: bold;")
        if tip == 'Nakit':
            self.nakit_btn.setStyleSheet("background-color: #007bff; color: white; font-size: 14px; font-weight: bold;")
        else:
            self.kart_btn.setStyleSheet("background-color: #007bff; color: white; font-size: 14px; font-weight: bold;")
        self.girilen_tutar_display.setText(str(float(self.odemeler.get(tip, 0))))
        self.girilen_tutar_display.setFocus()
        self.girilen_tutar_display.selectAll()

    def _numpad_tiklandi(self):
        gonderen_buton = self.sender()
        deger = gonderen_buton.text()
        self.klavye_girdisi_isle(deger)

    def _hizli_para_ekle(self):
        gonderen_buton = self.sender()
        deger = Decimal(gonderen_buton.text())
        mevcut_tutar = Decimal(self.girilen_tutar_display.text().replace(',', '.'))
        self.girilen_tutar_display.setText(str(mevcut_tutar + deger))
        self._odeme_listesini_guncelle()

    def klavye_girdisi_isle(self, karakter):
        mevcut_deger = self.girilen_tutar_display.text()
        if karakter.isdigit():
            if mevcut_deger == "0":
                self.girilen_tutar_display.setText(karakter)
            else:
                self.girilen_tutar_display.setText(mevcut_deger + karakter)
        elif karakter in ('.', ',') and '.' not in mevcut_deger:
            self.girilen_tutar_display.setText(mevcut_deger + '.')
        elif karakter == 'C':
            self.girilen_tutar_display.setText("0")
        elif karakter == '⌫':
            yeni_deger = mevcut_deger[:-1]
            self.girilen_tutar_display.setText(yeni_deger if yeni_deger else "0")
        self._odeme_listesini_guncelle()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F1: self._odeme_tipi_sec('Nakit')
        elif event.key() == Qt.Key_F2: self._odeme_tipi_sec('Kredi Kartı')
        elif event.key() == Qt.Key_F3: self._veresiye_ekle()
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter): self.accept()
        else: super().keyPressEvent(event)

    def _odeme_listesini_guncelle(self):
        try:
            girilen_tutar = Decimal(self.girilen_tutar_display.text().replace(',', '.'))
        except InvalidOperation:
            girilen_tutar = Decimal('0.00')
        self.odemeler[self.aktif_odeme_tipi] = girilen_tutar
        self._tutar_guncelle()

    def _tutar_guncelle(self):
        odenen_tutar = sum(self.odemeler.values())
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
        kalan_tutar = self.toplam_tutar - sum(self.odemeler.values())
        if kalan_tutar > 0:
            self.odemeler['Veresiye'] = kalan_tutar
            self._tutar_guncelle()
            self.accept()
        
    def bilgileri_al(self):
        self._odeme_listesini_guncelle()
        return [{'yontem': k, 'tutar': v} for k, v in self.odemeler.items() if v > 0]
    
    def _kisayollari_ayarla(self):
        QShortcut(QKeySequence("F1"), self, lambda: self._odeme_tipi_sec('Nakit'))
        QShortcut(QKeySequence("F2"), self, lambda: self._odeme_tipi_sec('Kredi Kartı'))
        if self.musteri_adi:
            QShortcut(QKeySequence("F3"), self, self._veresiye_ekle)
