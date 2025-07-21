# Dosya Adı: arayuz/giris_ekrani.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 11:45
# Yapılan İşlem: Klavyeden rakam girişi ve Enter tuşu ile giriş yapma işlevselliği eklendi.

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                             QPushButton, QMessageBox, QGridLayout, QFrame)
from PyQt5.QtGui import QIcon, QFont, QColor, QPixmap
from PyQt5.QtCore import Qt, pyqtSignal
from moduller.kullanici import kullanici_mantik

# ===== GirisEkrani SINIFI BAŞLANGICI =====
class GirisEkrani(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SonTechPOS - PIN Girişi")
        self.setFixedSize(320, 480)
        self.kullanici_verisi = None
        self._arayuzu_olustur()

    def _arayuzu_olustur(self):
        self.setStyleSheet("background-color: #ffffff;")
        self.ana_layout = QVBoxLayout(self)
        self.ana_layout.setContentsMargins(20, 20, 20, 20)
        self.ana_layout.setAlignment(Qt.AlignCenter)

        logo_label = QLabel(self)
        logo_label.setText("SonTechPOS")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #333; margin-bottom: 20px;")
        self.ana_layout.addWidget(logo_label)

        self.pin_display = QLineEdit(self)
        self.pin_display.setReadOnly(True)
        self.pin_display.setAlignment(Qt.AlignCenter)
        self.pin_display.setEchoMode(QLineEdit.Password)
        self.pin_display.setFixedHeight(50)
        self.pin_display.setStyleSheet("""
            QLineEdit {
                border: 2px solid #007bff;
                border-radius: 10px;
                font-size: 28px;
                background-color: #f8f9fa;
            }
        """)
        self.ana_layout.addWidget(self.pin_display)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        
        butonlar = [
            '7', '8', '9',
            '4', '5', '6',
            '1', '2', '3',
            'C', '0', '⌫'
        ]
        
        pozisyonlar = [(i, j) for i in range(4) for j in range(3)]

        for pozisyon, metin in zip(pozisyonlar, butonlar):
            buton = QPushButton(metin)
            buton.setFixedSize(80, 60)
            buton.setStyleSheet("""
                QPushButton {
                    font-size: 22px; font-weight: bold; border-radius: 10px;
                    background-color: #e9ecef; color: #495057;
                }
                QPushButton:hover { background-color: #ced4da; }
            """)
            if metin == 'C' or metin == '⌫':
                buton.setStyleSheet(buton.styleSheet() + "QPushButton { background-color: #ffc107; } QPushButton:hover { background-color: #e0a800; }")

            buton.clicked.connect(self.buton_tiklandi)
            grid_layout.addWidget(buton, *pozisyon)

        self.ana_layout.addLayout(grid_layout)

    def buton_tiklandi(self):
        gonderen_buton = self.sender()
        deger = gonderen_buton.text()
        self.pin_guncelle(deger)

    def pin_guncelle(self, karakter):
        """PIN ekranını güncelleyen merkezi fonksiyon."""
        mevcut_pin = self.pin_display.text()
        if karakter.isdigit():
            self.pin_display.setText(mevcut_pin + karakter)
        elif karakter == 'C':
            self.pin_display.clear()
        elif karakter == '⌫':
            self.pin_display.setText(mevcut_pin[:-1])

    def keyPressEvent(self, event):
        """Klavye olaylarını yakalar."""
        key_text = event.text()
        if key_text.isdigit():
            self.pin_guncelle(key_text)
        elif event.key() == Qt.Key_Backspace:
            self.pin_guncelle('⌫')
        elif event.key() in (Qt.Key_Return, Qt.Key_Enter):
            self._giris_yapmayi_dene()
        else:
            super().keyPressEvent(event)

    def _giris_yapmayi_dene(self):
        girilen_pin = self.pin_display.text()
        if not girilen_pin:
            return

        try:
            dogrulanan_kullanici = kullanici_mantik.kullanici_dogrula_pin(girilen_pin)
            if dogrulanan_kullanici:
                self.kullanici_verisi = dogrulanan_kullanici
                self.accept()
            else:
                QMessageBox.warning(self, "Hatalı PIN", "Girilen PIN hatalı veya kullanıcı pasif.")
                self.pin_display.clear()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Giriş sırasında bir hata oluştu: {e}")
