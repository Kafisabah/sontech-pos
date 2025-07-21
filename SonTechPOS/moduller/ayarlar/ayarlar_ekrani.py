# Dosya Adı: moduller/ayarlar/ayarlar_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 16:45
# Yapılan İşlem: Sayısal ayar değerleri setText() öncesi string'e dönüştürüldü.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QFormLayout, QLineEdit, QMessageBox)
from PyQt5.QtCore import Qt

from moduller.ayarlar import ayarlar_mantik

# ===== AyarlarEkrani SINIFI BAŞLANGICI =====
class AyarlarEkrani(QWidget):
    """Ayarlar modülünün ana arayüz widget'ı."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arayuzu_olustur()
        self.ayarlari_yukle()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        self.ana_layout.setAlignment(Qt.AlignTop)

        baslik = QLabel("Uygulama Ayarları")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.ana_layout.addWidget(baslik)

        form_layout = QFormLayout()
        self.magaza_adi_input = QLineEdit()
        self.kdv_orani_input = QLineEdit()
        self.puan_katsayisi_input = QLineEdit() # Yeni eklendi

        form_layout.addRow("Mağaza Adı:", self.magaza_adi_input)
        form_layout.addRow("Varsayılan KDV Oranı (%):", self.kdv_orani_input)
        form_layout.addRow("Sadakat Puanı Katsayısı:", self.puan_katsayisi_input) # Yeni eklendi
        
        self.ana_layout.addLayout(form_layout)
        
        self.kaydet_btn = QPushButton("Ayarları Kaydet")
        self.kaydet_btn.clicked.connect(self.ayarlari_kaydet)
        
        buton_layout = QHBoxLayout()
        buton_layout.addStretch()
        buton_layout.addWidget(self.kaydet_btn)
        
        self.ana_layout.addLayout(buton_layout)
        self.ana_layout.addStretch()

    def ayarlari_yukle(self):
        """Mevcut ayarları yükler ve form alanlarına doldurur."""
        print("DEBUG: AyarlarEkrani.ayarlari_yukle() çağrıldı.")
        try:
            mevcut_ayarlar = ayarlar_mantik.ayarlari_getir()
            self.magaza_adi_input.setText(mevcut_ayarlar.get('magaza_adi', ''))
            # Sayısal değerleri setText() öncesi string'e dönüştür
            self.kdv_orani_input.setText(str(mevcut_ayarlar.get('varsayilan_kdv', '')))
            self.puan_katsayisi_input.setText(str(mevcut_ayarlar.get('puan_katsayisi', ''))) # Yeni eklendi
            print("DEBUG: Ayarlar form alanlarına başarıyla yüklendi.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ayarlar yüklenirken bir sorun oluştu:\n{e}")

    def ayarlari_kaydet(self):
        """Formdaki yeni ayarları kaydeder."""
        print("DEBUG: AyarlarEkrani.ayarlari_kaydet() çağrıldı.")
        yeni_ayarlar = {
            'magaza_adi': self.magaza_adi_input.text(),
            'varsayilan_kdv': float(self.kdv_orani_input.text().replace(',', '.')), # Float'a dönüştür
            'puan_katsayisi': float(self.puan_katsayisi_input.text().replace(',', '.')) # Float'a dönüştür
        }
        try:
            # Kullanıcı ID'si şimdilik sabit 1 olarak gönderiliyor, gerçekte aktif kullanıcı ID'si olmalı
            if ayarlar_mantik.ayarlari_kaydet(yeni_ayarlar, 1):
                QMessageBox.information(self, "Başarılı", "Ayarlar başarıyla kaydedildi.")
            else:
                QMessageBox.warning(self, "Başarısız", "Ayarlar kaydedilirken bir sorun oluştu.")
        except ValueError as e:
            QMessageBox.warning(self, "Geçersiz Giriş", f"Sayısal bir değer bekleniyor: {e}")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Ayarlar kaydedilirken beklenmedik bir hata oluştu:\n{e}")

# ===== AyarlarEkrani SINIFI BİTİŞİ =====
