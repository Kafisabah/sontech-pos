# Dosya Adı: moduller/promosyon/promosyon_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 17:25
# Yapılan İşlem: Promosyon tipi 'x_al_y_bedava' yerine 'x_al_y_free' olarak düzeltildi.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QCheckBox, QComboBox,
                             QSpinBox, QDoubleSpinBox, QTextEdit, QDateEdit, QInputDialog)
from PyQt5.QtCore import Qt, QDate
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
import datetime

from moduller.promosyon import promosyon_mantik
from moduller.urun import urun_mantik # Ürün aramak için

# ===== PromosyonDuzenlemeDialog SINIFI BAŞLANGICI (Aynı kalıyor) =====
class PromosyonDuzenlemeDialog(QDialog):
    def __init__(self, promosyon_verisi=None, parent=None):
        super().__init__(parent)
        self.promosyon_verisi = promosyon_verisi
        self.setWindowTitle("Promosyon Düzenle" if promosyon_verisi else "Yeni Promosyon Ekle")
        self.setMinimumWidth(500)
        self._arayuzu_olustur()
        if promosyon_verisi:
            self._formu_doldur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)

        self.ad_input = QLineEdit()
        self.aciklama_input = QTextEdit()
        self.aciklama_input.setFixedHeight(50)

        self.promosyon_tipi_combo = QComboBox()
        # Düzeltme: 'x_al_y_bedava' yerine 'x_al_y_free' kullanıldı
        self.promosyon_tipi_combo.addItems(["miktar_indirim", "bogo", "x_al_y_free"])
        self.promosyon_tipi_combo.currentIndexChanged.connect(self._promosyon_tipi_degisti)

        self.urun_id_input = QLineEdit()
        self.urun_adi_label = QLabel("Ürün Adı: Yok")
        self.urun_sec_btn = QPushButton("Ürün Seç")
        self.urun_sec_btn.clicked.connect(self._urun_sec_dialogu)

        # Miktar indirimi alanları
        self.gerekli_miktar_input = QSpinBox()
        self.gerekli_miktar_input.setMaximum(99999)
        self.indirim_tutari_input = QDoubleSpinBox()
        self.indirim_tutari_input.setDecimals(2)
        self.indirim_tutari_input.setMaximum(999999.99)
        self.indirim_tutari_input.setSuffix(" ₺")

        # BOGO/X al Y bedava alanları
        self.gerekli_bogo_miktar_input = QSpinBox()
        self.gerekli_bogo_miktar_input.setMaximum(99999)
        self.bedava_miktar_input = QSpinBox()
        self.bedava_miktar_input.setMaximum(99999)
        self.bedava_urun_id_input = QLineEdit()
        self.bedava_urun_adi_label = QLabel("Bedava Ürün Adı: Yok")
        self.bedava_urun_sec_btn = QPushButton("Bedava Ürün Seç")
        self.bedava_urun_sec_btn.clicked.connect(self._bedava_urun_sec_dialogu)

        self.baslangic_tarih_input = QDateEdit(calendarPopup=True)
        self.baslangic_tarih_input.setDateTime(self.baslangic_tarih_input.minimumDateTime()) # Tarihi temizle
        self.bitis_tarih_input = QDateEdit(calendarPopup=True)
        self.bitis_tarih_input.setDateTime(self.bitis_tarih_input.minimumDateTime()) # Tarihi temizle

        self.aktif_checkbox = QCheckBox("Aktif")
        self.aktif_checkbox.setChecked(True)

        self.layout.addRow("Ad:", self.ad_input)
        self.layout.addRow("Açıklama:", self.aciklama_input)
        self.layout.addRow("Promosyon Tipi:", self.promosyon_tipi_combo)
        
        urun_layout = QHBoxLayout()
        urun_layout.addWidget(self.urun_id_input)
        urun_layout.addWidget(self.urun_sec_btn)
        self.layout.addRow("Uygulanacak Ürün ID:", urun_layout)
        self.layout.addRow("", self.urun_adi_label)

        self.layout.addRow("Gerekli Miktar (Adet İndirimi):", self.gerekli_miktar_input)
        self.layout.addRow("İndirim Tutarı (Adet İndirimi):", self.indirim_tutari_input)

        self.layout.addRow("Gerekli Miktar (BOGO/X al Y bedava):", self.gerekli_bogo_miktar_input)
        self.layout.addRow("Bedava Verilecek Miktar:", self.bedava_miktar_input)
        bedava_urun_layout = QHBoxLayout()
        bedava_urun_layout.addWidget(self.bedava_urun_id_input)
        bedava_urun_layout.addWidget(self.bedava_urun_sec_btn)
        self.layout.addRow("Bedava Verilecek Ürün ID:", bedava_urun_layout)
        self.layout.addRow("", self.bedava_urun_adi_label)

        self.layout.addRow("Başlangıç Tarihi:", self.baslangic_tarih_input)
        self.layout.addRow("Bitiş Tarihi:", self.bitis_tarih_input)
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

        self._promosyon_tipi_degisti(self.promosyon_tipi_combo.currentIndex()) # Başlangıçta görünürlüğü ayarla

    def _promosyon_tipi_degisti(self, index):
        tip = self.promosyon_tipi_combo.currentText()
        is_miktar_indirim = (tip == "miktar_indirim")
        is_bogo_xy = (tip in ["bogo", "x_al_y_free"]) # Düzeltme: 'x_al_y_bedava' yerine 'x_al_y_free' kullanıldı

        # Satırları ve widget'ları gizle/göster
        self.gerekli_miktar_input.setVisible(is_miktar_indirim)
        self.indirim_tutari_input.setVisible(is_miktar_indirim)
        self.gerekli_bogo_miktar_input.setVisible(is_bogo_xy)
        self.bedava_miktar_input.setVisible(is_bogo_xy)
        self.bedava_urun_id_input.setVisible(is_bogo_xy)
        self.bedava_urun_adi_label.setVisible(is_bogo_xy)
        self.bedava_urun_sec_btn.setVisible(is_bogo_xy)

        # Form layout'taki satırları da gizle/göster
        for row_index in range(self.layout.rowCount()):
            label_item = self.layout.itemAt(row_index, QFormLayout.LabelRole)
            field_item = self.layout.itemAt(row_index, QFormLayout.FieldRole)
            
            if label_item and label_item.widget():
                label_text = label_item.widget().text()
                if "Gerekli Miktar (Adet İndirimi)" in label_text or "İndirim Tutarı (Adet İndirimi)" in label_text:
                    label_item.widget().setVisible(is_miktar_indirim)
                    if field_item and field_item.widget():
                        field_item.widget().setVisible(is_miktar_indirim)
                elif "Gerekli Miktar (BOGO/X al Y bedava)" in label_text or "Bedava Verilecek Miktar" in label_text or "Bedava Verilecek Ürün ID" in label_text:
                    label_item.widget().setVisible(is_bogo_xy)
                    if field_item and field_item.layout(): # QHBoxLayout için
                        for i in range(field_item.layout().count()):
                            widget = field_item.layout().itemAt(i).widget()
                            if widget: widget.setVisible(is_bogo_xy)
                    elif field_item and field_item.widget(): # QLabel için
                         field_item.widget().setVisible(is_bogo_xy)
                elif label_text == "": # Boş label'lar (ürün/bedava ürün adı için)
                    if field_item and field_item.widget():
                        if "Ürün Adı:" in field_item.widget().text():
                            field_item.widget().setVisible(True) # Bu her zaman görünür
                        elif "Bedava Ürün Adı:" in field_item.widget().text():
                            field_item.widget().setVisible(is_bogo_xy)

    def _urun_sec_dialogu(self):
        # QInputDialog.getText kullanarak metin girişi al
        urun_id_str, ok = QInputDialog.getText(self, "Ürün Seç", "Lütfen ürün ID'sini girin:")
        if ok and urun_id_str.isdigit():
            urun_id = int(urun_id_str)
            try:
                # Sube ID'si sabit 1 olarak varsayılıyor, geliştirilebilir
                urun = urun_mantik.urunleri_getir(1) 
                secili_urun = next((u for u in urun if u.id == urun_id), None)
                if secili_urun:
                    self.urun_id_input.setText(str(urun_id))
                    self.urun_adi_label.setText(f"Ürün Adı: {secili_urun.ad}")
                else:
                    QMessageBox.warning(self, "Ürün Bulunamadı", "Belirtilen ID'ye sahip ürün bulunamadı.")
                    self.urun_id_input.clear()
                    self.urun_adi_label.setText("Ürün Adı: Yok")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürün bilgisi alınırken bir sorun oluştu:\n{e}")


    def _bedava_urun_sec_dialogu(self):
        # QInputDialog.getText kullanarak metin girişi al
        urun_id_str, ok = QInputDialog.getText(self, "Bedava Ürün Seç", "Lütfen bedava verilecek ürünün ID'sini girin:")
        if ok and urun_id_str.isdigit():
            urun_id = int(urun_id_str)
            try:
                # Sube ID'si sabit 1 olarak varsayılıyor, geliştirilebilir
                urun = urun_mantik.urunleri_getir(1) 
                secili_urun = next((u for u in urun if u.id == urun_id), None)
                if secili_urun:
                    self.bedava_urun_id_input.setText(str(urun_id))
                    self.bedava_urun_adi_label.setText(f"Bedava Ürün Adı: {secili_urun.ad}")
                else:
                    QMessageBox.warning(self, "Ürün Bulunamadı", "Belirtilen ID'ye sahip ürün bulunamadı.")
                    self.bedava_urun_id_input.clear()
                    self.bedava_urun_adi_label.setText("Bedava Ürün Adı: Yok")
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Ürün bilgisi alınırken bir sorun oluştu:\n{e}")

    def _formu_doldur(self):
        """Mevcut promosyon verilerini forma yükler."""
        self.ad_input.setText(self.promosyon_verisi.ad)
        self.aciklama_input.setText(self.promosyon_verisi.aciklama or "")
        self.promosyon_tipi_combo.setCurrentText(self.promosyon_verisi.promosyon_tipi)
        
        self.urun_id_input.setText(str(self.promosyon_verisi.urun_id))
        # Ürün adını yükle
        try:
            urun = urun_mantik.urunleri_getir(1) # Şube ID'si sabit, geliştirilebilir
            secili_urun = next((u for u in urun if u.id == self.promosyon_verisi.urun_id), None)
            if secili_urun:
                self.urun_adi_label.setText(f"Ürün Adı: {secili_urun.ad}")
        except Exception as e:
            print(f"UYARI: Ürün adını yüklerken hata: {e}")

        self.gerekli_miktar_input.setValue(int(self.promosyon_verisi.gerekli_miktar))
        self.indirim_tutari_input.setValue(float(self.promosyon_verisi.indirim_tutari))

        self.gerekli_bogo_miktar_input.setValue(int(self.promosyon_verisi.gerekli_bogo_miktar))
        self.bedava_miktar_input.setValue(int(self.promosyon_verisi.bedava_miktar))
        self.bedava_urun_id_input.setText(str(self.promosyon_verisi.bedava_urun_id) if self.promosyon_verisi.bedava_urun_id else "")
        # Bedava ürün adını yükle
        if self.promosyon_verisi.bedava_urun_id:
            try:
                secili_bedava_urun = next((u for u in urun if u.id == self.promosyon_verisi.bedava_urun_id), None)
                if secili_bedava_urun:
                    self.bedava_urun_adi_label.setText(f"Bedava Ürün Adı: {secili_bedava_urun.ad}")
            except Exception as e:
                print(f"UYARI: Bedava ürün adını yüklerken hata: {e}")
        
        if self.promosyon_verisi.baslangic_tarihi:
            self.baslangic_tarih_input.setDate(QDate(self.promosyon_verisi.baslangic_tarihi.year,
                                                    self.promosyon_verisi.baslangic_tarihi.month,
                                                    self.promosyon_verisi.baslangic_tarihi.day))
        if self.promosyon_verisi.bitis_tarihi:
            self.bitis_tarih_input.setDate(QDate(self.promosyon_verisi.bitis_tarihi.year,
                                                 self.promosyon_verisi.bitis_tarihi.month,
                                                 self.promosyon_verisi.bitis_tarihi.day))
        self.aktif_checkbox.setChecked(self.promosyon_verisi.aktif)
        self._promosyon_tipi_degisti(self.promosyon_tipi_combo.currentIndex()) # Formu doldurduktan sonra görünürlüğü ayarla

    def bilgileri_al(self):
        baslangic_tarihi = self.baslangic_tarih_input.date().toPyDate() if self.baslangic_tarih_input.date().isValid() else None
        bitis_tarihi = self.bitis_tarih_input.date().toPyDate() if self.bitis_tarih_input.date().isValid() else None

        return {
            "ad": self.ad_input.text().strip(),
            "aciklama": self.aciklama_input.toPlainText().strip() or None,
            "promosyon_tipi": self.promosyon_tipi_combo.currentText(),
            "urun_id": int(self.urun_id_input.text()) if self.urun_id_input.text().isdigit() else None,
            "gerekli_miktar": self.gerekli_miktar_input.value(),
            "indirim_tutari": Decimal(str(self.indirim_tutari_input.value())),
            "gerekli_bogo_miktar": self.gerekli_bogo_miktar_input.value(),
            "bedava_miktar": self.bedava_miktar_input.value(),
            "bedava_urun_id": int(self.bedava_urun_id_input.text()) if self.bedava_urun_id_input.text().isdigit() else None,
            "baslangic_tarihi": baslangic_tarihi,
            "bitis_tarihi": bitis_tarihi,
            "aktif": self.aktif_checkbox.isChecked()
        }
# ===== PromosyonDuzenlemeDialog SINIFI BİTİŞİ =====


# ===== PromosyonEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class PromosyonEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Promosyon Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.arama_input = QLineEdit()
        self.arama_input.setPlaceholderText("Promosyon Adı Ara...")
        self.arama_input.textChanged.connect(self.arama_yap)

        self.yeni_promosyon_btn = QPushButton("Yeni Promosyon Ekle")
        self.yeni_promosyon_btn.clicked.connect(self.yeni_promosyon_ekle_dialogu)
        
        self.duzenle_btn = QPushButton("Seçili Promosyonu Düzenle")
        self.duzenle_btn.clicked.connect(self.secili_promosyonu_duzenle_dialogu)

        self.durum_degistir_btn = QPushButton("Durumu Değiştir")
        self.durum_degistir_btn.clicked.connect(self.secili_promosyon_durum_degistir)

        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.arama_input)
        ust_panel_layout.addWidget(self.yeni_promosyon_btn)
        ust_panel_layout.addWidget(self.duzenle_btn)
        ust_panel_layout.addWidget(self.durum_degistir_btn)
        self.ana_layout.addLayout(ust_panel_layout)

        self.promosyon_tablosu = QTableWidget()
        self.promosyon_tablosu.setColumnCount(8) # Sütun sayısı güncellendi
        self.promosyon_tablosu.setHorizontalHeaderLabels(["ID", "Ad", "Tip", "Ürün", "İndirim/Bedava", "Başlangıç", "Bitiş", "Aktif"])
        self.promosyon_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.promosyon_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.promosyon_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.promosyon_tablosu)

    def yenile(self):
        self._tabloyu_doldur()

    def arama_yap(self, text):
        self._tabloyu_doldur(arama_terimi=text)

    def _tabloyu_doldur(self, arama_terimi: str = None):
        try:
            promosyonlar = promosyon_mantik.promosyonlari_getir(include_inactive=True, arama_terimi=arama_terimi)
            self.promosyon_tablosu.setRowCount(len(promosyonlar))
            for i, promo in enumerate(promosyonlar):
                self.promosyon_tablosu.setItem(i, 0, QTableWidgetItem(str(promo.id)))
                self.promosyon_tablosu.setItem(i, 1, QTableWidgetItem(promo.ad))
                self.promosyon_tablosu.setItem(i, 2, QTableWidgetItem(promo.promosyon_tipi))
                self.promosyon_tablosu.setItem(i, 3, QTableWidgetItem(promo.urun.ad if promo.urun else "N/A"))
                
                indirim_str = ""
                if promo.promosyon_tipi == 'miktar_indirim':
                    indirim_str = f"{promo.gerekli_miktar} adet için {promo.indirim_tutari:.2f}₺ indirim"
                elif promo.promosyon_tipi == 'bogo':
                    indirim_str = f"{promo.gerekli_bogo_miktar} al {promo.bedava_miktar} bedava ({promo.bedava_urun.ad if promo.bedava_urun else 'N/A'})"
                elif promo.promosyon_tipi == 'x_al_y_bedava': # Burası 'x_al_y_free' olmalı
                    indirim_str = f"{promo.gerekli_bogo_miktar} al {promo.bedava_miktar} bedava ({promo.bedava_urun.ad if promo.bedava_urun else 'N/A'})"

                self.promosyon_tablosu.setItem(i, 4, QTableWidgetItem(indirim_str))
                self.promosyon_tablosu.setItem(i, 5, QTableWidgetItem(promo.baslangic_tarihi.strftime('%Y-%m-%d') if promo.baslangic_tarihi else "N/A"))
                self.promosyon_tablosu.setItem(i, 6, QTableWidgetItem(promo.bitis_tarihi.strftime('%Y-%m-%d') if promo.bitis_tarihi else "N/A"))
                aktif_durum_str = "Evet" if promo.aktif else "Hayır"
                self.promosyon_tablosu.setItem(i, 7, QTableWidgetItem(aktif_durum_str))
                # Tüm promosyon nesnesini UserRole'a kaydet
                self.promosyon_tablosu.item(i, 0).setData(Qt.UserRole, promo)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Promosyonlar yüklenirken bir sorun oluştu:\n{e}")

    def yeni_promosyon_ekle_dialogu(self):
        dialog = PromosyonDuzenlemeDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            promosyon_bilgileri = dialog.bilgileri_al()
            try:
                promosyon_mantik.promosyon_ekle(
                    ad=promosyon_bilgileri['ad'],
                    aciklama=promosyon_bilgileri['aciklama'],
                    promosyon_tipi=promosyon_bilgileri['promosyon_tipi'],
                    urun_id=promosyon_bilgileri['urun_id'],
                    gerekli_miktar=promosyon_bilgileri['gerekli_miktar'],
                    indirim_tutari=promosyon_bilgileri['indirim_tutari'],
                    gerekli_bogo_miktar=promosyon_bilgileri['gerekli_bogo_miktar'],
                    bedava_miktar=promosyon_bilgileri['bedava_miktar'],
                    bedava_urun_id=promosyon_bilgileri['bedava_urun_id'],
                    baslangic_tarihi=promosyon_bilgileri['baslangic_tarihi'],
                    bitis_tarihi=promosyon_bilgileri['bitis_tarihi']
                )
                QMessageBox.information(self, "Başarılı", "Promosyon başarıyla eklendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except ValueError as e:
                QMessageBox.warning(self, "Eksik/Geçersiz Bilgi", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Promosyon eklenirken bir hata oluştu:\n{e}")

    def secili_promosyonu_duzenle_dialogu(self):
        secili_satir = self.promosyon_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz promosyonu seçin.")
            return
        
        promo_nesnesi = self.promosyon_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not promo_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili promosyon verisi bulunamadı.")
            return

        dialog = PromosyonDuzenlemeDialog(promosyon_verisi=promo_nesnesi, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            yeni_bilgiler = dialog.bilgileri_al()
            try:
                promosyon_mantik.promosyon_guncelle(
                    promosyon_id=promo_nesnesi.id,
                    ad=yeni_bilgiler['ad'],
                    aciklama=yeni_bilgiler['aciklama'],
                    promosyon_tipi=yeni_bilgiler['promosyon_tipi'],
                    urun_id=yeni_bilgiler['urun_id'],
                    gerekli_miktar=yeni_bilgiler['gerekli_miktar'],
                    indirim_tutari=yeni_bilgiler['indirim_tutari'],
                    gerekli_bogo_miktar=yeni_bilgiler['gerekli_bogo_miktar'],
                    bedava_miktar=yeni_bilgiler['bedava_miktar'],
                    bedava_urun_id=yeni_bilgiler['bedava_urun_id'],
                    baslangic_tarihi=yeni_bilgiler['baslangic_tarihi'],
                    bitis_tarihi=yeni_bilgiler['bitis_tarihi']
                )
                # Aktiflik durumunu da güncelle
                if promo_nesnesi.aktif != yeni_bilgiler['aktif']:
                    promosyon_mantik.promosyon_durum_degistir(promo_nesnesi.id, yeni_bilgiler['aktif'])

                QMessageBox.information(self, "Başarılı", "Promosyon başarıyla güncellendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except ValueError as e:
                QMessageBox.warning(self, "Eksik/Geçersiz Bilgi", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Promosyon güncellenirken bir hata oluştu:\n{e}")

    def secili_promosyon_durum_degistir(self):
        secili_satir = self.promosyon_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen durumunu değiştirmek istediğiniz promosyonu seçin.")
            return
        
        promo_nesnesi = self.promosyon_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not promo_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili promosyon verisi bulunamadı.")
            return

        yeni_durum = not promo_nesnesi.aktif
        durum_str = "pasif" if yeni_durum else "aktif"
        cevap = QMessageBox.question(self, "Durum Değiştirme Onayı", 
                                     f"'{promo_nesnesi.ad}' promosyonunu {durum_str} yapmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                promosyon_mantik.promosyon_durum_degistir(promo_nesnesi.id, yeni_durum)
                QMessageBox.information(self, "Başarılı", "Promosyon durumu başarıyla güncellendi.")
                self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Promosyon durumu değiştirilirken bir hata oluştu:\n{e}")

# ===== PromosyonEkrani SINIFI BİTİŞİ =====
