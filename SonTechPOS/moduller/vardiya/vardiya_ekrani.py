# Dosya Adı: moduller/vardiya/vardiya_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 17:55
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, QMessageBox ve print kullanıldı.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QDoubleSpinBox, QTextEdit, QInputDialog) # QInputDialog eklendi
from PyQt5.QtCore import Qt
from decimal import Decimal
import datetime

from moduller.vardiya import vardiya_mantik
from moduller.kullanici import kullanici_mantik # Kullanıcı seçimi için
from sqlalchemy.orm import joinedload # joinedload eklendi

# ===== VardiyaBaslatDialog SINIFI BAŞLANGICI (Aynı kalıyor) =====
class VardiyaBaslatDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Vardiya Başlat")
        self.setMinimumWidth(350)
        self._arayuzu_olustur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)
        self.kullanici_id_input = QLineEdit()
        self.kullanici_adi_label = QLabel("Kullanıcı Adı: Yok")
        self.kullanici_sec_btn = QPushButton("Kullanıcı Seç")
        self.kullanici_sec_btn.clicked.connect(self._kullanici_sec_dialogu)

        self.baslangic_kasa_nakiti_input = QDoubleSpinBox()
        self.baslangic_kasa_nakiti_input.setDecimals(2)
        self.baslangic_kasa_nakiti_input.setMaximum(999999.99)
        self.baslangic_kasa_nakiti_input.setSuffix(" ₺")
        self.baslangic_kasa_nakiti_input.setValue(0.00)

        kullanici_layout = QHBoxLayout()
        kullanici_layout.addWidget(self.kullanici_id_input)
        kullanici_layout.addWidget(self.kullanici_sec_btn)

        self.layout.addRow("Kullanıcı ID:", kullanici_layout)
        self.layout.addRow("", self.kullanici_adi_label)
        self.layout.addRow("Başlangıç Kasa Nakiti:", self.baslangic_kasa_nakiti_input)

        self.baslat_btn = QPushButton("Vardiya Başlat")
        self.iptal_btn = QPushButton("İptal")
        self.baslat_btn.clicked.connect(self.accept)
        self.iptal_btn.clicked.connect(self.reject)

        buton_layout = QHBoxLayout()
        buton_layout.addStretch()
        buton_layout.addWidget(self.baslat_btn)
        buton_layout.addWidget(self.iptal_btn)
        self.layout.addRow(buton_layout)

    def _kullanici_sec_dialogu(self):
        # QInputDialog.getText kullanarak metin girişi al
        kullanici_id_str, ok = QInputDialog.getText(self, "Kullanıcı Seç", "Lütfen kullanıcı ID'sini girin:")
        if ok and kullanici_id_str.isdigit():
            kullanici_id = int(kullanici_id_str)
            kullanici = kullanici_mantik.kullanici_getir_by_id(kullanici_id)
            if kullanici:
                self.kullanici_id_input.setText(str(kullanici_id))
                self.kullanici_adi_label.setText(f"Kullanıcı Adı: {kullanici.kullanici_adi}")
            else:
                QMessageBox.warning(self, "Kullanıcı Bulunamadı", "Belirtilen ID'ye sahip kullanıcı bulunamadı.")
                self.kullanici_id_input.clear()
                self.kullanici_adi_label.setText("Kullanıcı Adı: Yok")

    def bilgileri_al(self):
        return {
            "kullanici_id": int(self.kullanici_id_input.text()) if self.kullanici_id_input.text().isdigit() else None,
            "baslangic_kasa_nakiti": Decimal(str(self.baslangic_kasa_nakiti_input.value()))
        }
# ===== VardiyaBaslatDialog SINIFI BİTİŞİ =====

# ===== VardiyaBitirDialog SINIFI BAŞLANGICI (Aynı kalıyor) =====
class VardiyaBitirDialog(QDialog):
    def __init__(self, aktif_vardiya_verisi, parent=None):
        super().__init__(parent)
        self.aktif_vardiya_verisi = aktif_vardiya_verisi
        self.setWindowTitle(f"Vardiya Bitir - ID: {aktif_vardiya_verisi.id}")
        self.setMinimumWidth(400)
        self._arayuzu_olustur()
        self._ozet_bilgileri_goster()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)

        self.layout.addRow("Kullanıcı:", QLabel(self.aktif_vardiya_verisi.kullanici.tam_ad or self.aktif_vardiya_verisi.kullanici.kullanici_adi))
        self.layout.addRow("Başlangıç Zamanı:", QLabel(self.aktif_vardiya_verisi.baslangic_zamani.strftime('%Y-%m-%d %H:%M:%S')))
        self.layout.addRow("Başlangıç Nakiti:", QLabel(f"{self.aktif_vardiya_verisi.baslangic_kasa_nakiti:.2f} ₺"))
        
        self.layout.addRow(QLabel("--- Vardiya Özeti ---"))
        self.toplam_satis_label = QLabel("Toplam Satış: 0.00 ₺")
        self.nakit_satis_label = QLabel("Nakit Satış: 0.00 ₺")
        self.kart_satis_label = QLabel("Kart Satış: 0.00 ₺")
        self.veresiye_satis_label = QLabel("Veresiye Satış: 0.00 ₺")
        self.alinan_nakit_odeme_label = QLabel("Alınan Nakit Ödeme: 0.00 ₺")
        self.alinan_kart_odeme_label = QLabel("Alınan Kart Ödeme: 0.00 ₺")
        
        self.layout.addRow(self.toplam_satis_label)
        self.layout.addRow(self.nakit_satis_label)
        self.layout.addRow(self.kart_satis_label)
        self.layout.addRow(self.veresiye_satis_label)
        self.layout.addRow(self.alinan_nakit_odeme_label)
        self.layout.addRow(self.alinan_kart_odeme_label)

        self.layout.addRow(QLabel("--- Kasa Kapanış ---"))
        self.bitis_kasa_nakiti_input = QDoubleSpinBox()
        self.bitis_kasa_nakiti_input.setDecimals(2)
        self.bitis_kasa_nakiti_input.setMaximum(999999.99)
        self.bitis_kasa_nakiti_input.setSuffix(" ₺")
        self.bitis_kasa_nakiti_input.setValue(float(self.aktif_vardiya_verisi.baslangic_kasa_nakiti)) # Başlangıç nakitini varsayılan yap

        self.notlar_input = QTextEdit()
        self.notlar_input.setFixedHeight(50)

        self.layout.addRow("Bitiş Kasa Nakiti:", self.bitis_kasa_nakiti_input)
        self.layout.addRow("Notlar:", self.notlar_input)

        self.bitir_btn = QPushButton("Vardiyayı Bitir")
        self.iptal_btn = QPushButton("İptal")
        self.bitir_btn.clicked.connect(self.accept)
        self.iptal_btn.clicked.connect(self.reject)

        buton_layout = QHBoxLayout()
        buton_layout.addStretch()
        buton_layout.addWidget(self.bitir_btn)
        buton_layout.addWidget(self.iptal_btn)
        self.layout.addRow(buton_layout)

    def _ozet_bilgileri_goster(self):
        try:
            ozet = vardiya_mantik.vardiya_ozeti_hesapla(self.aktif_vardiya_verisi.id)
            musteri_odeme_ozeti = vardiya_mantik.vardiya_musteri_odeme_ozeti_hesapla(self.aktif_vardiya_verisi.id)

            self.toplam_satis_label.setText(f"Toplam Satış: {ozet['total_sales']:.2f} ₺")
            self.nakit_satis_label.setText(f"Nakit Satış: {ozet['cash_sales']:.2f} ₺")
            self.kart_satis_label.setText(f"Kart Satış: {ozet['card_sales']:.2f} ₺")
            self.veresiye_satis_label.setText(f"Veresiye Satış: {ozet['veresiye_sales']:.2f} ₺")
            self.alinan_nakit_odeme_label.setText(f"Alınan Nakit Ödeme: {musteri_odeme_ozeti['cash_payments_received']:.2f} ₺")
            self.alinan_kart_odeme_label.setText(f"Alınan Kart Ödeme: {musteri_odeme_ozeti['card_payments_received']:.2f} ₺")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Vardiya özeti hesaplanırken bir sorun oluştu:\n{e}")

    def bilgileri_al(self):
        return {
            "bitis_kasa_nakiti": Decimal(str(self.bitis_kasa_nakiti_input.value())),
            "notlar": self.notlar_input.toPlainText().strip() or None
        }
# ===== VardiyaBitirDialog SINIFI BİTİŞİ =====


# ===== VardiyaEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class VardiyaEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Vardiya Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.vardiya_baslat_btn = QPushButton("Vardiya Başlat")
        self.vardiya_baslat_btn.clicked.connect(self.vardiya_baslat_dialogu)
        
        self.vardiya_bitir_btn = QPushButton("Aktif Vardiyayı Bitir")
        self.vardiya_bitir_btn.clicked.connect(self.aktif_vardiyayi_bitir_dialogu)

        self.yenile_btn = QPushButton("Yenile")
        self.yenile_btn.clicked.connect(self.yenile)

        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.vardiya_baslat_btn)
        ust_panel_layout.addWidget(self.vardiya_bitir_btn)
        ust_panel_layout.addWidget(self.yenile_btn)
        self.ana_layout.addLayout(ust_panel_layout)

        self.vardiya_tablosu = QTableWidget()
        self.vardiya_tablosu.setColumnCount(6)
        self.vardiya_tablosu.setHorizontalHeaderLabels(["ID", "Kullanıcı", "Başlangıç", "Bitiş", "Kasa Nakiti (Baş/Bit)", "Aktif"])
        self.vardiya_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.vardiya_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.vardiya_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.vardiya_tablosu)

    def yenile(self):
        self._tabloyu_doldur()

    def _tabloyu_doldur(self):
        try:
            oturum = vardiya_mantik.OturumYerel()
            # joinedload import edildiği için burada kullanılabilir
            vardiyalar = oturum.query(vardiya_mantik.Vardiya).options(joinedload(vardiya_mantik.Vardiya.kullanici)).order_by(vardiya_mantik.Vardiya.baslangic_zamani.desc()).all()
            oturum.close()

            self.vardiya_tablosu.setRowCount(len(vardiyalar))
            for i, vardiya in enumerate(vardiyalar):
                self.vardiya_tablosu.setItem(i, 0, QTableWidgetItem(str(vardiya.id)))
                self.vardiya_tablosu.setItem(i, 1, QTableWidgetItem(vardiya.kullanici.tam_ad or vardiya.kullanici.kullanici_adi))
                self.vardiya_tablosu.setItem(i, 2, QTableWidgetItem(vardiya.baslangic_zamani.strftime('%Y-%m-%d %H:%M')))
                self.vardiya_tablosu.setItem(i, 3, QTableWidgetItem(vardiya.bitis_zamani.strftime('%Y-%m-%d %H:%M') if vardiya.bitis_zamani else "Devam Ediyor"))
                kasa_nakiti_str = f"{vardiya.baslangic_kasa_nakiti:.2f}₺ / {vardiya.bitis_kasa_nakiti:.2f}₺" if vardiya.bitis_kasa_nakiti is not None else f"{vardiya.baslangic_kasa_nakiti:.2f}₺"
                self.vardiya_tablosu.setItem(i, 4, QTableWidgetItem(kasa_nakiti_str))
                aktif_durum_str = "Evet" if vardiya.aktif else "Hayır"
                self.vardiya_tablosu.setItem(i, 5, QTableWidgetItem(aktif_durum_str))
                # Tüm vardiya nesnesini UserRole'a kaydet
                self.vardiya_tablosu.item(i, 0).setData(Qt.UserRole, vardiya)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Vardiyalar yüklenirken bir sorun oluştu:\n{e}")

    def vardiya_baslat_dialogu(self):
        dialog = VardiyaBaslatDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            vardiya_bilgileri = dialog.bilgileri_al()
            kullanici_id = vardiya_bilgileri.get('kullanici_id')
            baslangic_kasa_nakiti = vardiya_bilgileri.get('baslangic_kasa_nakiti')
            
            if not kullanici_id:
                QMessageBox.warning(self, "Eksik Bilgi", "Lütfen bir kullanıcı seçin."); return

            try:
                vardiya_mantik.vardiya_baslat(kullanici_id, baslangic_kasa_nakiti)
                QMessageBox.information(self, "Başarılı", "Vardiya başarıyla başlatıldı.")
                self.yenile()
            except ValueError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Vardiya başlatılırken bir hata oluştu:\n{e}")

    def aktif_vardiyayi_bitir_dialogu(self):
        # Aktif vardiyayı bul
        # Şimdilik sadece ilk aktif vardiyayı alıyoruz, gerçekte kullanıcıya seçtirilebilir veya oturumdaki kullanıcıya göre belirlenir.
        # Varsayılan olarak 1 numaralı kullanıcıya ait aktif vardiyayı arayalım
        aktif_kullanici_id = 1 # Bu değeri oturum açmış kullanıcıdan almalıyız
        aktif_vardiya = vardiya_mantik.aktif_vardiya_getir(aktif_kullanici_id)

        if not aktif_vardiya:
            QMessageBox.information(self, "Bilgi", "Şu anda aktif bir vardiya bulunmuyor.")
            return

        dialog = VardiyaBitirDialog(aktif_vardiya_verisi=aktif_vardiya, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            bitis_bilgileri = dialog.bilgileri_al()
            try:
                vardiya_mantik.vardiya_bitir(
                    vardiya_id=aktif_vardiya.id,
                    bitis_kasa_nakiti=bitis_bilgileri['bitis_kasa_nakiti'],
                    notlar=bitis_bilgileri['notlar'],
                    kullanici_id=aktif_kullanici_id # Loglama için kullanıcı ID'sini geç
                )
                QMessageBox.information(self, "Başarılı", "Vardiya başarıyla bitirildi.")
                self.yenile()
            except ValueError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Vardiya bitirilirken bir hata oluştu:\n{e}")

# ===== VardiyaEkrani SINIFI BİTİŞİ =====
