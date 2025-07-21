# Dosya Adı: moduller/marka/marka_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 16:05
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, QMessageBox ve print kullanıldı.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QCheckBox)
from PyQt5.QtCore import Qt
from sqlalchemy.exc import IntegrityError

from moduller.marka import marka_mantik

# ===== MarkaDuzenlemeDialog SINIFI BAŞLANGICI (Aynı kalıyor) =====
class MarkaDuzenlemeDialog(QDialog):
    def __init__(self, marka_verisi=None, parent=None):
        super().__init__(parent)
        self.marka_verisi = marka_verisi
        self.setWindowTitle("Marka Düzenle" if marka_verisi else "Yeni Marka Ekle")
        self.setMinimumWidth(350)
        self._arayuzu_olustur()
        if marka_verisi:
            self._formu_doldur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)
        self.ad_input = QLineEdit()
        self.aktif_checkbox = QCheckBox("Aktif")
        self.aktif_checkbox.setChecked(True) # Varsayılan olarak aktif

        self.layout.addRow("Ad:", self.ad_input)
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
        """Mevcut marka verilerini forma yükler."""
        self.ad_input.setText(self.marka_verisi.ad)
        self.aktif_checkbox.setChecked(self.marka_verisi.aktif)

    def bilgileri_al(self):
        return {
            "ad": self.ad_input.text().strip(),
            "aktif": self.aktif_checkbox.isChecked()
        }
# ===== MarkaDuzenlemeDialog SINIFI BİTİŞİ =====


# ===== MarkaEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class MarkaEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Marka Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.arama_input = QLineEdit()
        self.arama_input.setPlaceholderText("Marka Adı Ara...")
        self.arama_input.textChanged.connect(self.arama_yap)

        self.yeni_marka_btn = QPushButton("Yeni Marka Ekle")
        self.yeni_marka_btn.clicked.connect(self.yeni_marka_ekle_dialogu)
        
        self.duzenle_btn = QPushButton("Seçili Markayı Düzenle")
        self.duzenle_btn.clicked.connect(self.secili_markayi_duzenle_dialogu)

        self.durum_degistir_btn = QPushButton("Durumu Değiştir")
        self.durum_degistir_btn.clicked.connect(self.secili_marka_durum_degistir)

        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.arama_input)
        ust_panel_layout.addWidget(self.yeni_marka_btn)
        ust_panel_layout.addWidget(self.duzenle_btn)
        ust_panel_layout.addWidget(self.durum_degistir_btn)
        self.ana_layout.addLayout(ust_panel_layout)

        self.marka_tablosu = QTableWidget()
        self.marka_tablosu.setColumnCount(3)
        self.marka_tablosu.setHorizontalHeaderLabels(["ID", "Ad", "Aktif"])
        self.marka_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.marka_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.marka_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.marka_tablosu)

    def yenile(self):
        self._tabloyu_doldur()

    def arama_yap(self, text):
        self._tabloyu_doldur(arama_terimi=text)

    def _tabloyu_doldur(self, arama_terimi: str = None):
        try:
            markalar = marka_mantik.markalari_getir(include_inactive=True, arama_terimi=arama_terimi)
            self.marka_tablosu.setRowCount(len(markalar))
            for i, marka in enumerate(markalar):
                self.marka_tablosu.setItem(i, 0, QTableWidgetItem(str(marka.id)))
                self.marka_tablosu.setItem(i, 1, QTableWidgetItem(marka.ad))
                aktif_durum_str = "Evet" if marka.aktif else "Hayır"
                self.marka_tablosu.setItem(i, 2, QTableWidgetItem(aktif_durum_str))
                # Tüm marka nesnesini UserRole'a kaydet
                self.marka_tablosu.item(i, 0).setData(Qt.UserRole, marka)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Markalar yüklenirken bir sorun oluştu:\n{e}")

    def yeni_marka_ekle_dialogu(self):
        dialog = MarkaDuzenlemeDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            marka_bilgileri = dialog.bilgileri_al()
            try:
                marka_mantik.marka_ekle(ad=marka_bilgileri['ad'])
                QMessageBox.information(self, "Başarılı", "Marka başarıyla eklendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Marka eklenirken bir hata oluştu:\n{e}")

    def secili_markayi_duzenle_dialogu(self):
        secili_satir = self.marka_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz markayı seçin.")
            return
        
        # UserRole'dan marka nesnesini al
        marka_nesnesi = self.marka_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not marka_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili marka verisi bulunamadı.")
            return

        dialog = MarkaDuzenlemeDialog(marka_verisi=marka_nesnesi, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            yeni_bilgiler = dialog.bilgileri_al()
            try:
                marka_mantik.marka_guncelle(
                    marka_id=marka_nesnesi.id,
                    yeni_ad=yeni_bilgiler['ad']
                )
                # Aktiflik durumunu da güncelle
                if marka_nesnesi.aktif != yeni_bilgiler['aktif']:
                    marka_mantik.marka_durum_degistir(marka_nesnesi.id, yeni_bilgiler['aktif'])

                QMessageBox.information(self, "Başarılı", "Marka başarıyla güncellendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Marka güncellenirken bir hata oluştu:\n{e}")

    def secili_marka_durum_degistir(self):
        secili_satir = self.marka_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen durumunu değiştirmek istediğiniz markayı seçin.")
            return
        
        marka_nesnesi = self.marka_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not marka_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili marka verisi bulunamadı.")
            return

        yeni_durum = not marka_nesnesi.aktif
        durum_str = "pasif" if yeni_durum else "aktif"
        cevap = QMessageBox.question(self, "Durum Değiştirme Onayı", 
                                     f"'{marka_nesnesi.ad}' markasını {durum_str} yapmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                marka_mantik.marka_durum_degistir(marka_nesnesi.id, yeni_durum)
                QMessageBox.information(self, "Başarılı", "Marka durumu başarıyla güncellendi.")
                self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Marka durumu değiştirilirken bir hata oluştu:\n{e}")

# ===== MarkaEkrani SINIFI BİTİŞİ =====
