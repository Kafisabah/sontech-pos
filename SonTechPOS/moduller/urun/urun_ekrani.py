# Dosya Adı: moduller/urun/urun_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 15:50
# Yapılan İşlem: Ürün aktif/pasif yapma, etiket basma, CSV aktarım butonları ve işlevleri eklendi.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QDoubleSpinBox, QSpinBox,
                             QFileDialog) # QFileDialog eklendi
from PyQt5.QtCore import Qt
from decimal import Decimal
import datetime # Etiket basımı için

from moduller.urun import urun_mantik
from moduller.veri_aktarim import veri_aktarim_mantik # Veri aktarım için
from moduller.yazdirma import yazdirma_mantik # Yazdırma için
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_PRODUCT_ADD, LOG_ACTION_PRODUCT_UPDATE, LOG_ACTION_PRODUCT_STATUS_CHANGE, LOG_ACTION_PRODUCT_LABEL_PRINT # Log sabitleri


# ===== UrunDuzenlemeDialog SINIFI BAŞLANGICI (Aynı kalıyor) =====
class UrunDuzenlemeDialog(QDialog):
    def __init__(self, urun_verisi=None, parent=None):
        super().__init__(parent)
        self.urun_verisi = urun_verisi
        self.setWindowTitle("Ürün Düzenle" if urun_verisi else "Yeni Ürün Ekle")
        self.setMinimumWidth(400)
        self._arayuzu_olustur()
        if urun_verisi:
            self._formu_doldur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)
        self.barkod_input = QLineEdit()
        self.ad_input = QLineEdit()
        self.marka_input = QLineEdit()
        self.kategori_input = QLineEdit()
        self.alis_fiyati_input = QDoubleSpinBox()
        self.alis_fiyati_input.setDecimals(2); self.alis_fiyati_input.setMaximum(999999.99); self.alis_fiyati_input.setSuffix(" ₺")
        self.satis_fiyati_input = QDoubleSpinBox()
        self.satis_fiyati_input.setDecimals(2); self.satis_fiyati_input.setMaximum(999999.99); self.satis_fiyati_input.setSuffix(" ₺")
        self.kdv_orani_input = QDoubleSpinBox()
        self.kdv_orani_input.setDecimals(2); self.kdv_orani_input.setMaximum(100.00); self.kdv_orani_input.setSuffix(" %")
        self.miktar_input = QSpinBox()
        self.miktar_input.setMaximum(99999)
        self.min_stok_seviyesi_input = QSpinBox()
        self.min_stok_seviyesi_input.setMaximum(99999)


        self.layout.addRow("Barkod:", self.barkod_input)
        self.layout.addRow("Ürün Adı:", self.ad_input)
        self.layout.addRow("Marka:", self.marka_input)
        self.layout.addRow("Kategori:", self.kategori_input)
        self.layout.addRow("Alış Fiyatı:", self.alis_fiyati_input)
        self.layout.addRow("Satış Fiyatı:", self.satis_fiyati_input)
        self.layout.addRow("KDV Oranı:", self.kdv_orani_input)
        self.layout.addRow("Miktar:", self.miktar_input)
        self.layout.addRow("Min Stok Seviyesi:", self.min_stok_seviyesi_input)

        self.kaydet_btn = QPushButton("Kaydet"); self.iptal_btn = QPushButton("İptal")
        self.kaydet_btn.clicked.connect(self.accept); self.iptal_btn.clicked.connect(self.reject)
        buton_layout = QHBoxLayout(); buton_layout.addStretch(); buton_layout.addWidget(self.kaydet_btn); buton_layout.addWidget(self.iptal_btn)
        self.layout.addRow(buton_layout)

    def _formu_doldur(self):
        """Mevcut ürün verilerini forma yükler."""
        self.barkod_input.setText(self.urun_verisi['urun'].barkod)
        self.ad_input.setText(self.urun_verisi['urun'].ad)
        self.marka_input.setText(self.urun_verisi['urun'].marka.ad if self.urun_verisi['urun'].marka else "")
        self.kategori_input.setText(self.urun_verisi['urun'].kategori.ad if self.urun_verisi['urun'].kategori else "")
        self.alis_fiyati_input.setValue(float(self.urun_verisi['urun'].alis_fiyati if self.urun_verisi['urun'].alis_fiyati else 0.0))
        self.satis_fiyati_input.setValue(float(self.urun_verisi['urun'].satis_fiyati if self.urun_verisi['urun'].satis_fiyati else 0.0))
        self.kdv_orani_input.setValue(float(self.urun_verisi['urun'].kdv_orani if self.urun_verisi['urun'].kdv_orani else 0.0))
        self.miktar_input.setValue(int(self.urun_verisi['stok'].miktar if self.urun_verisi.get('stok') else 0))
        self.min_stok_seviyesi_input.setValue(int(self.urun_verisi['urun'].min_stok_seviyesi if self.urun_verisi['urun'].min_stok_seviyesi else 0))


    def bilgileri_al(self):
        return {
            "barkod": self.barkod_input.text().strip(),
            "ad": self.ad_input.text().strip(),
            "marka_adi": self.marka_input.text().strip(),
            "kategori_adi": self.kategori_input.text().strip(),
            "alis_fiyati": Decimal(str(self.alis_fiyati_input.value())),
            "satis_fiyati": Decimal(str(self.satis_fiyati_input.value())),
            "kdv_orani": Decimal(str(self.kdv_orani_input.value())),
            "miktar": self.miktar_input.value(),
            "min_stok_seviyesi": self.min_stok_seviyesi_input.value()
        }
# ===== UrunDuzenlemeDialog SINIFI BİTİŞİ =====


# ===== UrunEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class UrunEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aktif_sube_id = 1
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Ürün Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.yeni_urun_btn = QPushButton("Yeni Ürün Ekle")
        self.yeni_urun_btn.clicked.connect(self.yeni_urun_ekle_dialogu)
        self.duzenle_btn = QPushButton("Seçili Ürünü Düzenle")
        self.duzenle_btn.clicked.connect(self.secili_urunu_duzenle_dialogu)
        self.sil_btn = QPushButton("Seçili Ürünü Sil")
        self.sil_btn.setStyleSheet("background-color: #dc3545;")
        self.sil_btn.clicked.connect(self.secili_urunu_sil)

        self.durum_degistir_btn = QPushButton("Durumu Değiştir")
        self.durum_degistir_btn.clicked.connect(self.secili_urun_durum_degistir)

        self.etiket_bas_btn = QPushButton("Etiket Bas")
        self.etiket_bas_btn.clicked.connect(self.secili_urun_etiket_bas)
        
        self.urun_aktar_btn = QPushButton("Ürünleri Dışa Aktar (CSV)") # Yeni buton
        self.urun_aktar_btn.clicked.connect(self.urunleri_disa_aktar) # Yeni işlev

        self.urun_ice_aktar_btn = QPushButton("Ürünleri İçe Aktar (CSV)") # Yeni buton
        self.urun_ice_aktar_btn.clicked.connect(self.urunleri_ice_aktar) # Yeni işlev


        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.yeni_urun_btn)
        ust_panel_layout.addWidget(self.duzenle_btn)
        ust_panel_layout.addWidget(self.sil_btn)
        ust_panel_layout.addWidget(self.durum_degistir_btn)
        ust_panel_layout.addWidget(self.etiket_bas_btn)
        ust_panel_layout.addWidget(self.urun_aktar_btn) # Butonu ekle
        ust_panel_layout.addWidget(self.urun_ice_aktar_btn) # Butonu ekle

        self.ana_layout.addLayout(ust_panel_layout)
        self.urun_tablosu = QTableWidget()
        self.urun_tablosu.setColumnCount(9)
        self.urun_tablosu.setHorizontalHeaderLabels(["ID", "Barkod", "Ürün Adı", "Marka", "Alış F.", "Satış F.", "Stok", "Min. Stok", "Aktif"])
        self.urun_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.urun_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.urun_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.urun_tablosu)

    def yenile(self): self._tabloyu_doldur()

    def _tabloyu_doldur(self):
        try:
            self.urunler_cache = urun_mantik.urunleri_getir(self.aktif_sube_id)
            self.urun_tablosu.setRowCount(len(self.urunler_cache))
            for i, urun in enumerate(self.urunler_cache):
                self.urun_tablosu.setItem(i, 0, QTableWidgetItem(str(urun.id)))
                self.urun_tablosu.setItem(i, 1, QTableWidgetItem(urun.barkod))
                self.urun_tablosu.setItem(i, 2, QTableWidgetItem(urun.ad))
                self.urun_tablosu.setItem(i, 3, QTableWidgetItem(urun.marka.ad if urun.marka else "N/A"))
                self.urun_tablosu.setItem(i, 4, QTableWidgetItem(f"{urun.alis_fiyati:.2f} ₺" if urun.alis_fiyati else "0.00 ₺"))
                self.urun_tablosu.setItem(i, 5, QTableWidgetItem(f"{urun.satis_fiyati:.2f} ₺" if urun.satis_fiyati else "0.00 ₺"))
                stok_miktari = str(urun.sube_stok.miktar) if hasattr(urun, 'sube_stok') and urun.sube_stok else "0"
                self.urun_tablosu.setItem(i, 6, QTableWidgetItem(stok_miktari))
                self.urun_tablosu.setItem(i, 7, QTableWidgetItem(str(urun.min_stok_seviyesi) if urun.min_stok_seviyesi else "0"))
                aktif_durum_str = "Evet" if urun.aktif else "Hayır"
                self.urun_tablosu.setItem(i, 8, QTableWidgetItem(aktif_durum_str))
                self.urun_tablosu.item(i, 0).setData(Qt.UserRole, urun)

        except Exception as e: QMessageBox.critical(self, "Hata", f"Ürünler yüklenirken bir sorun oluştu:\n{e}")

    def yeni_urun_ekle_dialogu(self):
        dialog = UrunDuzenlemeDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            urun_bilgileri = dialog.bilgileri_al()
            if not urun_bilgileri['barkod'] or not urun_bilgileri['ad']:
                QMessageBox.warning(self, "Eksik Bilgi", "Barkod ve Ürün Adı alanları zorunludur."); return
            try:
                urun_mantik.yeni_urun_ekle(
                    urun_bilgileri, 
                    self.aktif_sube_id
                )
                QMessageBox.information(self, "Başarılı", "Ürün başarıyla eklendi."); self.yenile()
            except Exception as e: QMessageBox.critical(self, "Hata", f"Ürün eklenirken bir hata oluştu:\n{e}")

    def secili_urunu_duzenle_dialogu(self):
        secili_satir = self.urun_tablosu.currentRow()
        if secili_satir < 0: QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz ürünü seçin."); return
        urun = self.urunler_cache[secili_satir]
        urun_verisi = {"urun": urun, "stok": urun.sube_stok, "fiyat": urun.sube_fiyat}
        
        dialog = UrunDuzenlemeDialog(urun_verisi=urun_verisi, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            yeni_bilgiler = dialog.bilgileri_al()
            try:
                urun_mantik.urun_guncelle(
                    urun.id, 
                    yeni_bilgiler, 
                    self.aktif_sube_id
                )
                QMessageBox.information(self, "Başarılı", "Ürün başarıyla güncellendi."); self.yenile()
            except Exception as e: QMessageBox.critical(self, "Hata", f"Ürün güncellenirken bir hata oluştu:\n{e}")

    def secili_urunu_sil(self):
        secili_satir = self.urun_tablosu.currentRow()
        if secili_satir < 0: QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen silmek istediğiniz ürünü seçin."); return
        urun = self.urunler_cache[secili_satir]
        
        cevap = QMessageBox.question(self, "Silme Onayı", f"'{urun.ad}' ürününü silmek istediğinizden emin misiniz?\nBu işlem geri alınamaz.", QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                urun_mantik.urun_sil(urun.id)
                QMessageBox.information(self, "Başarılı", "Ürün başarıyla silindi veya pasif hale getirildi."); self.yenile()
            except Exception as e: QMessageBox.critical(self, "Hata", f"Ürün silinemedi:\n{e}")

    def secili_urun_durum_degistir(self):
        secili_satir = self.urun_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen durumunu değiştirmek istediğiniz ürünü seçin.")
            return
        
        urun_nesnesi = self.urun_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not urun_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili ürün verisi bulunamadı.")
            return

        yeni_durum = not urun_nesnesi.aktif
        durum_str = "pasif" if yeni_durum else "aktif"
        cevap = QMessageBox.question(self, "Durum Değiştirme Onayı", 
                                     f"'{urun_nesnesi.ad}' ürününü {durum_str} yapmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                urun_mantik.urun_aktif_pasif_yap(urun_nesnesi.id, yeni_durum)
                QMessageBox.information(self, "Başarılı", "Ürün durumu başarıyla güncellendi.")
                self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürün durumu değiştirilirken bir hata oluştu:\n{e}")

    def secili_urun_etiket_bas(self):
        secili_satir = self.urun_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen etiketini basmak istediğiniz ürünü seçin.")
            return
        
        urun_nesnesi = self.urun_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not urun_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili ürün verisi bulunamadı.")
            return

        try:
            etiket_data = urun_mantik.etiket_verisi_getir(urun_nesnesi.id)
            if etiket_data:
                yazdirma_mantik.etiket_bastir_simulasyon(etiket_data, parent=self)
            else:
                QMessageBox.warning(self, "Hata", "Etiket verisi alınamadı.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Etiket basılırken bir hata oluştu:\n{e}")

    def urunleri_disa_aktar(self):
        # Dosya kaydetme diyalogu aç
        default_filename = f"urun_listesi_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv"
        dosya_adi, _ = QFileDialog.getSaveFileName(self, "Ürünleri CSV Olarak Kaydet", default_filename, "CSV Dosyaları (*.csv);;Tüm Dosyalar (*)")
        
        if dosya_adi:
            try:
                if veri_aktarim_mantik.urunleri_csv_ye_aktar(dosya_adi, self.aktif_sube_id):
                    QMessageBox.information(self, "Başarılı", f"Ürünler '{dosya_adi}' dosyasına başarıyla aktarıldı.")
                else:
                    QMessageBox.warning(self, "Hata", "Ürünler CSV'ye aktarılırken bir sorun oluştu.")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürünleri dışa aktarırken beklenmedik bir hata oluştu:\n{e}")

    def urunleri_ice_aktar(self):
        # Dosya açma diyalogu aç
        dosya_adi, _ = QFileDialog.getOpenFileName(self, "CSV Dosyasından Ürünleri İçe Aktar", "", "CSV Dosyaları (*.csv);;Tüm Dosyalar (*)")
        
        if dosya_adi:
            try:
                eklenen, guncellenen, atlanan = veri_aktarim_mantik.urunleri_csv_den_ice_aktar(dosya_adi, self.aktif_sube_id)
                QMessageBox.information(self, "Başarılı", 
                                        f"İçe aktarım tamamlandı:\n"
                                        f"Eklenen: {eklenen}\n"
                                        f"Güncellenen: {guncellenen}\n"
                                        f"Atlanan: {atlanan}")
                self.yenile() # Tabloyu yenile
            except ValueError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürünleri içe aktarırken beklenmedik bir hata oluştu:\n{e}")

# ===== UrunEkrani SINIFI BİTİŞİ =====
