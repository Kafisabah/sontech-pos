# Dosya Adı: moduller/tedarikci/tedarikci_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 15:55
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, QMessageBox ve print kullanıldı.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from sqlalchemy.exc import IntegrityError

from moduller.tedarikci import tedarikci_mantik

# ===== TedarikciDuzenlemeDialog SINIFI BAŞLANGICI (Aynı kalıyor) =====
class TedarikciDuzenlemeDialog(QDialog):
    def __init__(self, tedarikci_verisi=None, parent=None):
        super().__init__(parent)
        self.tedarikci_verisi = tedarikci_verisi
        self.setWindowTitle("Tedarikçi Düzenle" if tedarikci_verisi else "Yeni Tedarikçi Ekle")
        self.setMinimumWidth(450)
        self._arayuzu_olustur()
        if tedarikci_verisi:
            self._formu_doldur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)
        self.ad_input = QLineEdit()
        self.iletisim_yetkilisi_input = QLineEdit()
        self.telefon_input = QLineEdit()
        self.email_input = QLineEdit()
        self.adres_input = QLineEdit()
        self.aktif_checkbox = QCheckBox("Aktif")
        self.aktif_checkbox.setChecked(True) # Varsayılan olarak aktif

        self.layout.addRow("Ad:", self.ad_input)
        self.layout.addRow("İletişim Yetkilisi:", self.iletisim_yetkilisi_input)
        self.layout.addRow("Telefon:", self.telefon_input)
        self.layout.addRow("E-posta:", self.email_input)
        self.layout.addRow("Adres:", self.adres_input)
        self.layout.addRow("Durum:", self.aktif_checkbox)

        self.kaydet_btn = QPushButton("Kaydet")
        self.iptal_btn = QPushButton("İptal")
        self.kaydet_btn.clicked.connect(self.accept)
        self.iptal_btn.clicked.connect(self.reject)

        buton_layout = QHBoxLayout()
        buton_layout.addStretch()
        buton_layout.addWidget(self.kaydet_btn)
        buton_layout.addWidget(self.iptal_btn)
        self.layout.addRow(buton_layout)

    def _formu_doldur(self):
        """Mevcut tedarikçi verilerini forma yükler."""
        self.ad_input.setText(self.tedarikci_verisi.ad)
        self.iletisim_yetkilisi_input.setText(self.tedarikci_verisi.iletisim_yetkilisi or "")
        self.telefon_input.setText(self.tedarikci_verisi.telefon or "")
        self.email_input.setText(self.tedarikci_verisi.email or "")
        self.adres_input.setText(self.tedarikci_verisi.adres or "")
        self.aktif_checkbox.setChecked(self.tedarikci_verisi.aktif)

    def bilgileri_al(self):
        return {
            "ad": self.ad_input.text().strip(),
            "iletisim_yetkilisi": self.iletisim_yetkilisi_input.text().strip() or None,
            "telefon": self.telefon_input.text().strip() or None,
            "email": self.email_input.text().strip() or None,
            "adres": self.adres_input.text().strip() or None,
            "aktif": self.aktif_checkbox.isChecked()
        }
# ===== TedarikciDuzenlemeDialog SINIFI BİTİŞİ =====


# ===== TedarikciEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class TedarikciEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Tedarikçi Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.arama_input = QLineEdit()
        self.arama_input.setPlaceholderText("Tedarikçi Adı veya Telefon Ara...")
        self.arama_input.textChanged.connect(self.arama_yap)

        self.yeni_tedarikci_btn = QPushButton("Yeni Tedarikçi Ekle")
        self.yeni_tedarikci_btn.clicked.connect(self.yeni_tedarikci_ekle_dialogu)
        
        self.duzenle_btn = QPushButton("Seçili Tedarikçiyi Düzenle")
        self.duzenle_btn.clicked.connect(self.secili_tedarikciyi_duzenle_dialogu)

        self.durum_degistir_btn = QPushButton("Durumu Değiştir")
        self.durum_degistir_btn.clicked.connect(self.secili_tedarikci_durum_degistir)

        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.arama_input)
        ust_panel_layout.addWidget(self.yeni_tedarikci_btn)
        ust_panel_layout.addWidget(self.duzenle_btn)
        ust_panel_layout.addWidget(self.durum_degistir_btn)
        self.ana_layout.addLayout(ust_panel_layout)

        self.tedarikci_tablosu = QTableWidget()
        self.tedarikci_tablosu.setColumnCount(6)
        self.tedarikci_tablosu.setHorizontalHeaderLabels(["ID", "Ad", "Telefon", "E-posta", "Adres", "Aktif"])
        self.tedarikci_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tedarikci_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.tedarikci_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.tedarikci_tablosu)

    def yenile(self):
        self._tabloyu_doldur()

    def arama_yap(self, text):
        self._tabloyu_doldur(arama_terimi=text)

    def _tabloyu_doldur(self, arama_terimi: str = None):
        try:
            tedarikciler = tedarikci_mantik.tedarikcileri_getir(include_inactive=True, arama_terimi=arama_terimi)
            self.tedarikci_tablosu.setRowCount(len(tedarikciler))
            for i, tedarikci in enumerate(tedarikciler):
                self.tedarikci_tablosu.setItem(i, 0, QTableWidgetItem(str(tedarikci.id)))
                self.tedarikci_tablosu.setItem(i, 1, QTableWidgetItem(tedarikci.ad))
                self.tedarikci_tablosu.setItem(i, 2, QTableWidgetItem(tedarikci.telefon or "N/A"))
                self.tedarikci_tablosu.setItem(i, 3, QTableWidgetItem(tedarikci.email or "N/A"))
                self.tedarikci_tablosu.setItem(i, 4, QTableWidgetItem(tedarikci.adres or "N/A"))
                aktif_durum_str = "Evet" if tedarikci.aktif else "Hayır"
                self.tedarikci_tablosu.setItem(i, 5, QTableWidgetItem(aktif_durum_str))
                # Tüm tedarikçi nesnesini UserRole'a kaydet
                self.tedarikci_tablosu.item(i, 0).setData(Qt.UserRole, tedarikci)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Tedarikçiler yüklenirken bir sorun oluştu:\n{e}")

    def yeni_tedarikci_ekle_dialogu(self):
        dialog = TedarikciDuzenlemeDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            tedarikci_bilgileri = dialog.bilgileri_al()
            try:
                tedarikci_mantik.tedarikci_ekle(
                    ad=tedarikci_bilgileri['ad'],
                    iletisim_yetkilisi=tedarikci_bilgileri['iletisim_yetkilisi'],
                    telefon=tedarikci_bilgileri['telefon'],
                    email=tedarikci_bilgileri['email'],
                    adres=tedarikci_bilgileri['adres']
                )
                QMessageBox.information(self, "Başarılı", "Tedarikçi başarıyla eklendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Tedarikçi eklenirken bir hata oluştu:\n{e}")

    def secili_tedarikciyi_duzenle_dialogu(self):
        secili_satir = self.tedarikci_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz tedarikçiyi seçin.")
            return
        
        # UserRole'dan tedarikçi nesnesini al
        tedarikci_nesnesi = self.tedarikci_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not tedarikci_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili tedarikçi verisi bulunamadı.")
            return

        dialog = TedarikciDuzenlemeDialog(tedarikci_verisi=tedarikci_nesnesi, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            yeni_bilgiler = dialog.bilgileri_al()
            try:
                tedarikci_mantik.tedarikci_guncelle(
                    tedarikci_id=tedarikci_nesnesi.id,
                    ad=yeni_bilgiler['ad'],
                    iletisim_yetkilisi=yeni_bilgiler['iletisim_yetkilisi'],
                    telefon=yeni_bilgiler['telefon'],
                    email=yeni_bilgiler['email'],
                    adres=yeni_bilgiler['adres']
                )
                # Aktiflik durumunu da güncelle
                if tedarikci_nesnesi.aktif != yeni_bilgiler['aktif']:
                    tedarikci_mantik.tedarikci_durum_degistir(tedarikci_nesnesi.id, yeni_bilgiler['aktif'])

                QMessageBox.information(self, "Başarılı", "Tedarikçi başarıyla güncellendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Tedarikçi güncellenirken bir hata oluştu:\n{e}")

    def secili_tedarikci_durum_degistir(self):
        secili_satir = self.tedarikci_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen durumunu değiştirmek istediğiniz tedarikçiyi seçin.")
            return
        
        tedarikci_nesnesi = self.tedarikci_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not tedarikci_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili tedarikçi verisi bulunamadı.")
            return

        yeni_durum = not tedarikci_nesnesi.aktif
        durum_str = "pasif" if yeni_durum else "aktif"
        cevap = QMessageBox.question(self, "Durum Değiştirme Onayı", 
                                     f"'{tedarikci_nesnesi.ad}' tedarikçisini {durum_str} yapmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                tedarikci_mantik.tedarikci_durum_degistir(tedarikci_nesnesi.id, yeni_durum)
                QMessageBox.information(self, "Başarılı", "Tedarikçi durumu başarıyla güncellendi.")
                self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Tedarikçi durumu değiştirilirken bir hata oluştu:\n{e}")

# ===== TedarikciEkrani SINIFI BİTİŞİ =====
