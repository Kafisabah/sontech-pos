# Dosya Adı: arayuz/widgetlar/indirim_dialogu.py
# Oluşturma Tarihi / Saati: 17.07.2025 / 11:45
# Yapılan İşlem: Satır indirimi için Tutar/Yüzde girişi sağlayan diyalog oluşturuldu.

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QRadioButton, 
                             QDoubleSpinBox, QPushButton, QMessageBox, QButtonGroup)
from PyQt5.QtCore import Qt
from decimal import Decimal

class IndirimDialogu(QDialog):
    def __init__(self, urun_adi, kalem_toplami, parent=None):
        super().__init__(parent)
        self.setWindowTitle("İndirim Uygula")
        self.setMinimumWidth(300)
        
        self.urun_adi = urun_adi
        self.kalem_toplami = kalem_toplami
        
        self.indirim_tipi = 'tutar'
        self.indirim_degeri = Decimal('0.00')

        self._arayuzu_olustur()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)

        self.urun_label = QLabel(f"<b>Ürün:</b> {self.urun_adi}<br><b>Tutar:</b> {self.kalem_toplami:.2f} ₺")
        self.ana_layout.addWidget(self.urun_label)

        tip_layout = QHBoxLayout()
        self.tip_grup = QButtonGroup(self)
        
        self.tutar_radio = QRadioButton("Tutar (₺)")
        self.tutar_radio.setChecked(True)
        self.tutar_radio.toggled.connect(lambda: self._tip_degisti("tutar"))
        
        self.yuzde_radio = QRadioButton("Yüzde (%)")
        self.yuzde_radio.toggled.connect(lambda: self._tip_degisti("yuzde"))

        self.tip_grup.addButton(self.tutar_radio)
        self.tip_grup.addButton(self.yuzde_radio)
        tip_layout.addWidget(self.tutar_radio)
        tip_layout.addWidget(self.yuzde_radio)
        self.ana_layout.addLayout(tip_layout)

        self.deger_input = QDoubleSpinBox()
        self.deger_input.setDecimals(2)
        self.deger_input.setMinimum(0.01)
        self.deger_input.setMaximum(99999.99)
        self.deger_input.setSuffix(" ₺")
        self.ana_layout.addWidget(self.deger_input)

        buton_layout = QHBoxLayout()
        self.uygula_btn = QPushButton("Uygula")
        self.iptal_btn = QPushButton("İptal")
        self.uygula_btn.clicked.connect(self._uygula)
        self.iptal_btn.clicked.connect(self.reject)
        
        buton_layout.addStretch()
        buton_layout.addWidget(self.iptal_btn)
        buton_layout.addWidget(self.uygula_btn)
        self.ana_layout.addLayout(buton_layout)

    def _tip_degisti(self, tip):
        self.indirim_tipi = tip
        if tip == 'tutar':
            self.deger_input.setSuffix(" ₺")
            self.deger_input.setMaximum(float(self.kalem_toplami) - 0.01)
        else:
            self.deger_input.setSuffix(" %")
            self.deger_input.setMaximum(99.99)

    def _uygula(self):
        deger = Decimal(str(self.deger_input.value()))
        if self.indirim_tipi == 'tutar' and deger >= self.kalem_toplami:
            QMessageBox.warning(self, "Hata", "İndirim tutarı, ürün toplamından büyük veya eşit olamaz.")
            return
        
        self.indirim_degeri = deger
        self.accept()

    def bilgileri_al(self):
        return self.indirim_tipi, self.indirim_degeri
