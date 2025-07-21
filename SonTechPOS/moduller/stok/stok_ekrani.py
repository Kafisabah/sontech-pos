# Dosya Adı: moduller/stok/stok_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 13:40
# Yapılan İşlem: Stok raporu ve sipariş önerisi butonları ile işlevleri eklendi.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QInputDialog,
                             QMessageBox, QDialog, QCheckBox) # QDialog, QCheckBox eklendi
from PyQt5.QtCore import Qt
from decimal import Decimal

# Düzeltme: Modül yerine doğrudan fonksiyonlar import edildi.
from moduller.stok.stok_mantik import stoklari_getir, stok_duzelt
from moduller.urun import urun_mantik # Stok raporu ve sipariş önerisi için
from sqlalchemy.orm import joinedload # joinedload eklendi

# ===== StokRaporuDialog SINIFI BAŞLANGICI (YENİ) =====
class StokRaporuDialog(QDialog):
    def __init__(self, sube_id: int, parent=None):
        super().__init__(parent)
        self.sube_id = sube_id
        self.setWindowTitle("Stok Raporu")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self._arayuzu_olustur()
        self.raporu_getir()

    def _arayuzu_olustur(self):
        self.main_layout = QVBoxLayout(self)
        control_layout = QHBoxLayout()

        self.kritik_stok_checkbox = QCheckBox("Sadece Kritik Stoktakiler")
        self.kritik_stok_checkbox.clicked.connect(self.raporu_getir)
        
        self.pasif_urun_checkbox = QCheckBox("Pasif Ürünleri Dahil Et")
        self.pasif_urun_checkbox.clicked.connect(self.raporu_getir)

        self.yenile_btn = QPushButton("Yenile")
        self.yenile_btn.clicked.connect(self.raporu_getir)

        control_layout.addWidget(self.kritik_stok_checkbox)
        control_layout.addWidget(self.pasif_urun_checkbox)
        control_layout.addStretch()
        control_layout.addWidget(self.yenile_btn)
        self.main_layout.addLayout(control_layout)

        self.rapor_tablosu = QTableWidget()
        self.rapor_tablosu.setColumnCount(8)
        self.rapor_tablosu.setHorizontalHeaderLabels(["ID", "Barkod", "Ürün Adı", "Marka", "Kategori", "Mevcut Stok", "Min. Stok", "Aktif"])
        self.rapor_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rapor_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.main_layout.addWidget(self.rapor_tablosu)

    def raporu_getir(self):
        kritik_seviye_altinda_olanlar = self.kritik_stok_checkbox.isChecked()
        pasif_urunleri_dahil_et = self.pasif_urun_checkbox.isChecked()
        try:
            rapor_verisi = urun_mantik.stok_raporu_getir(
                self.sube_id,
                kritik_seviye_altinda_olanlar=kritik_seviye_altinda_olanlar,
                pasif_urunleri_dahil_et=pasif_urunleri_dahil_et
            )
            self.rapor_tablosu.setRowCount(len(rapor_verisi))
            for i, urun_data in enumerate(rapor_verisi):
                self.rapor_tablosu.setItem(i, 0, QTableWidgetItem(str(urun_data['id'])))
                self.rapor_tablosu.setItem(i, 1, QTableWidgetItem(urun_data['barkod']))
                self.rapor_tablosu.setItem(i, 2, QTableWidgetItem(urun_data['ad']))
                self.rapor_tablosu.setItem(i, 3, QTableWidgetItem(urun_data['marka_adi']))
                self.rapor_tablosu.setItem(i, 4, QTableWidgetItem(urun_data['kategori_adi']))
                self.rapor_tablosu.setItem(i, 5, QTableWidgetItem(str(urun_data['mevcut_stok'])))
                self.rapor_tablosu.setItem(i, 6, QTableWidgetItem(str(urun_data['min_stok_seviyesi'])))
                aktif_str = "Evet" if urun_data['aktif'] else "Hayır"
                self.rapor_tablosu.setItem(i, 7, QTableWidgetItem(aktif_str))
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Stok raporu oluşturulurken bir sorun oluştu:\n{e}")
# ===== StokRaporuDialog SINIFI BİTİŞİ =====

# ===== SiparisOneriDialog SINIFI BAŞLANGICI (YENİ) =====
class SiparisOneriDialog(QDialog):
    def __init__(self, sube_id: int, parent=None):
        super().__init__(parent)
        self.sube_id = sube_id
        self.setWindowTitle("Sipariş Önerileri")
        self.setMinimumWidth(900)
        self.setMinimumHeight(500)
        self._arayuzu_olustur()
        self.onerileri_getir()

    def _arayuzu_olustur(self):
        self.main_layout = QVBoxLayout(self)
        control_layout = QHBoxLayout()

        self.yenile_btn = QPushButton("Yenile")
        self.yenile_btn.clicked.connect(self.onerileri_getir)

        control_layout.addStretch()
        control_layout.addWidget(self.yenile_btn)
        self.main_layout.addLayout(control_layout)

        self.oneri_tablosu = QTableWidget()
        self.oneri_tablosu.setColumnCount(7)
        self.oneri_tablosu.setHorizontalHeaderLabels(["ID", "Barkod", "Ürün Adı", "Mevcut Stok", "Min. Stok", "Son Alış F.", "Son Tedarikçi", "Tahmini Tükenme (Gün)"])
        self.oneri_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.oneri_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.main_layout.addWidget(self.oneri_tablosu)

    def onerileri_getir(self):
        try:
            oneriler = urun_mantik.siparis_onerisi_getir(self.sube_id)
            self.oneri_tablosu.setRowCount(len(oneriler))
            for i, oneri_data in enumerate(oneriler):
                self.oneri_tablosu.setItem(i, 0, QTableWidgetItem(str(oneri_data['id'])))
                self.oneri_tablosu.setItem(i, 1, QTableWidgetItem(oneri_data['barkod']))
                self.oneri_tablosu.setItem(i, 2, QTableWidgetItem(oneri_data['ad']))
                self.oneri_tablosu.setItem(i, 3, QTableWidgetItem(str(oneri_data['mevcut_stok'])))
                self.oneri_tablosu.setItem(i, 4, QTableWidgetItem(str(oneri_data['min_stok_seviyesi'])))
                self.oneri_tablosu.setItem(i, 5, QTableWidgetItem(f"{oneri_data['son_alis_fiyati']:.2f} ₺" if oneri_data['son_alis_fiyati'] else "N/A"))
                self.oneri_tablosu.setItem(i, 6, QTableWidgetItem(oneri_data['son_tedarikci'] or "N/A"))
                # Tahmini tükenme süresi şimdilik N/A, ileride hesaplanabilir
                self.oneri_tablosu.setItem(i, 7, QTableWidgetItem(str(oneri_data['tahmini_tukenme_suresi'])))
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Sipariş önerileri oluşturulurken bir sorun oluştu:\n{e}")
# ===== SiparisOneriDialog SINIFI BİTİŞİ =====


# ===== StokEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class StokEkrani(QWidget):
    """Stok yönetimi modülünün ana arayüz widget'ı."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aktif_sube_id = 1
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Stok Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.stok_duzelt_btn = QPushButton("Stok Düzeltme")
        self.stok_duzelt_btn.clicked.connect(self.stok_duzeltme_dialogu)

        self.stok_raporu_btn = QPushButton("Stok Raporu") # Yeni buton
        self.stok_raporu_btn.clicked.connect(self.stok_raporu_goster) # Yeni işlev

        self.siparis_oneri_btn = QPushButton("Sipariş Önerileri") # Yeni buton
        self.siparis_oneri_btn.clicked.connect(self.siparis_onerileri_goster) # Yeni işlev

        self.yenile_btn = QPushButton("Yenile")
        self.yenile_btn.clicked.connect(self.yenile)
        
        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.stok_duzelt_btn)
        ust_panel_layout.addWidget(self.stok_raporu_btn) # Butonu ekle
        ust_panel_layout.addWidget(self.siparis_oneri_btn) # Butonu ekle
        ust_panel_layout.addWidget(self.yenile_btn)
        self.ana_layout.addLayout(ust_panel_layout)
        self.stok_tablosu = QTableWidget()
        self.stok_tablosu.setColumnCount(5)
        self.stok_tablosu.setHorizontalHeaderLabels(["Ürün Adı", "Marka", "Şube", "Mevcut Stok", "Min. Stok"])
        self.stok_tablosu.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stok_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.stok_tablosu)

    def yenile(self):
        """Veritabanından stokları çeker ve tabloyu doldurur."""
        try:
            # Düzeltme: Fonksiyon doğrudan çağrıldı
            stoklar = stoklari_getir(self.aktif_sube_id)
            self.stok_tablosu.setRowCount(len(stoklar))
            for satir_index, stok in enumerate(stoklar):
                urun_adi = stok.urun.ad if stok.urun else "Bilinmeyen Ürün"
                marka_adi = stok.urun.marka.ad if stok.urun and stok.urun.marka else "N/A"
                sube_adi = stok.sube.ad if stok.sube else "N/A"
                self.stok_tablosu.setItem(satir_index, 0, QTableWidgetItem(urun_adi))
                self.stok_tablosu.setItem(satir_index, 1, QTableWidgetItem(marka_adi))
                self.stok_tablosu.setItem(satir_index, 2, QTableWidgetItem(sube_adi))
                self.stok_tablosu.setItem(satir_index, 3, QTableWidgetItem(str(stok.miktar)))
                # Min stok seviyesi artık Stok modelinde değil, Urun modelinde
                min_stok_seviyesi = str(stok.urun.min_stok_seviyesi) if stok.urun and hasattr(stok.urun, 'min_stok_seviyesi') else "0"
                self.stok_tablosu.setItem(satir_index, 4, QTableWidgetItem(min_stok_seviyesi))
                self.stok_tablosu.item(satir_index, 0).setData(Qt.UserRole, stok.id)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Stoklar yüklenirken bir sorun oluştu:\n{e}")

    def stok_duzeltme_dialogu(self):
        """Seçili ürünün stoğunu düzeltmek için bir diyalog açar."""
        secili_satirlar = self.stok_tablosu.selectedItems()
        if not secili_satirlar:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen stoğunu düzeltmek istediğiniz ürünü seçin.")
            return
        secili_satir = secili_satirlar[0].row()
        stok_id = self.stok_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        urun_adi = self.stok_tablosu.item(secili_satirlar[0].row(), 0).text() # Ürün adını alırken ilk sütunu kullan
        mevcut_stok = self.stok_tablosu.item(secili_satir, 3).text()
        yeni_miktar_str, ok = QInputDialog.getText(self, "Stok Düzeltme", f"'{urun_adi}' için yeni stok miktarını girin:\n(Mevcut: {mevcut_stok})")
        if ok and yeni_miktar_str:
            try:
                yeni_miktar = Decimal(yeni_miktar_str.replace(',', '.'))
                # Düzeltme: Fonksiyon doğrudan çağrıldı
                stok_duzelt(stok_id, yeni_miktar)
                QMessageBox.information(self, "Başarılı", "Stok miktarı güncellendi.")
                self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Stok güncellenirken bir hata oluştu:\n{e}")

    def stok_raporu_goster(self): # Yeni metod
        dialog = StokRaporuDialog(self.aktif_sube_id, parent=self)
        dialog.exec_()

    def siparis_onerileri_goster(self): # Yeni metod
        dialog = SiparisOneriDialog(self.aktif_sube_id, parent=self)
        dialog.exec_()

# ===== StokEkrani SINIFI BİTİŞİ =====
