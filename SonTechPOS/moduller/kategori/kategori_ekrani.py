# Dosya Adı: moduller/kategori/kategori_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 16:20
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, QMessageBox ve print kullanıldı.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QCheckBox, QTextEdit)
from PyQt5.QtCore import Qt
from sqlalchemy.exc import IntegrityError

from moduller.kategori import kategori_mantik

# ===== KategoriDuzenlemeDialog SINIFI BAŞLANGICI (Aynı kalıyor) =====
class KategoriDuzenlemeDialog(QDialog):
    def __init__(self, kategori_verisi=None, parent=None):
        super().__init__(parent)
        self.kategori_verisi = kategori_verisi
        self.setWindowTitle("Kategori Düzenle" if kategori_verisi else "Yeni Kategori Ekle")
        self.setMinimumWidth(400)
        self._arayuzu_olustur()
        if kategori_verisi:
            self._formu_doldur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)
        self.ad_input = QLineEdit()
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setFixedHeight(60) # Küçük bir metin alanı
        self.aktif_checkbox = QCheckBox("Aktif")
        self.aktif_checkbox.setChecked(True) # Varsayılan olarak aktif

        self.layout.addRow("Ad:", self.ad_input)
        self.layout.addRow("Açıklama:", self.aciklama_input)
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
        """Mevcut kategori verilerini forma yükler."""
        self.ad_input.setText(self.kategori_verisi.ad)
        self.aciklama_input.setText(self.kategori_verisi.aciklama or "")
        self.aktif_checkbox.setChecked(self.kategori_verisi.aktif)

    def bilgileri_al(self):
        return {
            "ad": self.ad_input.text().strip(),
            "aciklama": self.aciklama_input.toPlainText().strip() or None,
            "aktif": self.aktif_checkbox.isChecked()
        }
# ===== KategoriDuzenlemeDialog SINIFI BİTİŞİ =====


# ===== KategoriEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class KategoriEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Kategori Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.arama_input = QLineEdit()
        self.arama_input.setPlaceholderText("Kategori Adı Ara...")
        self.arama_input.textChanged.connect(self.arama_yap)

        self.yeni_kategori_btn = QPushButton("Yeni Kategori Ekle")
        self.yeni_kategori_btn.clicked.connect(self.yeni_kategori_ekle_dialogu)
        
        self.duzenle_btn = QPushButton("Seçili Kategoriyi Düzenle")
        self.duzenle_btn.clicked.connect(self.secili_kategoriyi_duzenle_dialogu)

        self.durum_degistir_btn = QPushButton("Durumu Değiştir")
        self.durum_degistir_btn.clicked.connect(self.secili_kategori_durum_degistir)

        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.arama_input)
        ust_panel_layout.addWidget(self.yeni_kategori_btn)
        ust_panel_layout.addWidget(self.duzenle_btn)
        ust_panel_layout.addWidget(self.durum_degistir_btn)
        self.ana_layout.addLayout(ust_panel_layout)

        self.kategori_tablosu = QTableWidget()
        self.kategori_tablosu.setColumnCount(4)
        self.kategori_tablosu.setHorizontalHeaderLabels(["ID", "Ad", "Açıklama", "Aktif"])
        self.kategori_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.kategori_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.kategori_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.kategori_tablosu)

    def yenile(self):
        self._tabloyu_doldur()

    def arama_yap(self, text):
        self._tabloyu_doldur(arama_terimi=text)

    def _tabloyu_doldur(self, arama_terimi: str = None):
        try:
            kategoriler = kategori_mantik.kategorileri_getir(include_inactive=True, arama_terimi=arama_terimi)
            self.kategori_tablosu.setRowCount(len(kategoriler))
            for i, kategori in enumerate(kategoriler):
                self.kategori_tablosu.setItem(i, 0, QTableWidgetItem(str(kategori.id)))
                self.kategori_tablosu.setItem(i, 1, QTableWidgetItem(kategori.ad))
                self.kategori_tablosu.setItem(i, 2, QTableWidgetItem(kategori.aciklama or "N/A"))
                aktif_durum_str = "Evet" if kategori.aktif else "Hayır"
                self.kategori_tablosu.setItem(i, 3, QTableWidgetItem(aktif_durum_str))
                # Tüm kategori nesnesini UserRole'a kaydet
                self.kategori_tablosu.item(i, 0).setData(Qt.UserRole, kategori)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kategoriler yüklenirken bir sorun oluştu:\n{e}")

    def yeni_kategori_ekle_dialogu(self):
        dialog = KategoriDuzenlemeDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            kategori_bilgileri = dialog.bilgileri_al()
            try:
                kategori_mantik.kategori_ekle(
                    ad=kategori_bilgileri['ad'],
                    aciklama=kategori_bilgileri['aciklama']
                )
                QMessageBox.information(self, "Başarılı", "Kategori başarıyla eklendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kategori eklenirken bir hata oluştu:\n{e}")

    def secili_kategoriyi_duzenle_dialogu(self):
        secili_satir = self.kategori_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz kategoriyi seçin.")
            return
        
        # UserRole'dan kategori nesnesini al
        kategori_nesnesi = self.kategori_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not kategori_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili kategori verisi bulunamadı.")
            return

        dialog = KategoriDuzenlemeDialog(kategori_verisi=kategori_nesnesi, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            yeni_bilgiler = dialog.bilgileri_al()
            try:
                kategori_mantik.kategori_guncelle(
                    kategori_id=kategori_nesnesi.id,
                    yeni_ad=yeni_bilgiler['ad'],
                    yeni_aciklama=yeni_bilgiler['aciklama']
                )
                # Aktiflik durumunu da güncelle
                if kategori_nesnesi.aktif != yeni_bilgiler['aktif']:
                    kategori_mantik.kategori_durum_degistir(kategori_nesnesi.id, yeni_bilgiler['aktif'])

                QMessageBox.information(self, "Başarılı", "Kategori başarıyla güncellendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kategori güncellenirken bir hata oluştu:\n{e}")

    def secili_kategori_durum_degistir(self):
        secili_satir = self.kategori_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen durumunu değiştirmek istediğiniz kategoriyi seçin.")
            return
        
        kategori_nesnesi = self.kategori_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not kategori_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili kategori verisi bulunamadı.")
            return

        yeni_durum = not kategori_nesnesi.aktif
        durum_str = "pasif" if yeni_durum else "aktif"
        cevap = QMessageBox.question(self, "Durum Değiştirme Onayı", 
                                     f"'{kategori_nesnesi.ad}' kategorisini {durum_str} yapmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                kategori_mantik.kategori_durum_degistir(kategori_nesnesi.id, yeni_durum)
                QMessageBox.information(self, "Başarılı", "Kategori durumu başarıyla güncellendi.")
                self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kategori durumu değiştirilirken bir hata oluştu:\n{e}")

# ===== KategoriEkrani SINIFI BİTİŞİ =====
