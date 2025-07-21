# Dosya Adı: moduller/alis/alis_ekrani.py
# Oluşturma Tarihi / Saati: 12.07.2025 13:00
# Yapılan İşlem: Alış yönetimi için arayüz ekranı oluşturuldu.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QDoubleSpinBox, QSpinBox,
                             QTextEdit, QDateEdit, QComboBox)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal
import datetime

from moduller.alis import alis_mantik
from moduller.tedarikci import tedarikci_mantik # Tedarikçi seçimi için
from moduller.urun import urun_mantik # Ürün seçimi için

# ===== AlisEkleDuzenleDialog SINIFI BAŞLANGICI =====
class AlisEkleDuzenleDialog(QDialog):
    def __init__(self, alis_verisi=None, parent=None):
        super().__init__(parent)
        self.alis_verisi = alis_verisi
        self.setWindowTitle("Alış Düzenle" if alis_verisi else "Yeni Alış Ekle")
        self.setMinimumWidth(600)
        self.kalemler = [] # Sepet gibi çalışacak
        self._arayuzu_olustur()
        if alis_verisi:
            self._formu_doldur()

    def _arayuzu_olustur(self):
        self.main_layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        # Alış Bilgileri
        self.tedarikci_id_input = QLineEdit()
        self.tedarikci_adi_label = QLabel("Tedarikçi Adı: Yok")
        self.tedarikci_sec_btn = QPushButton("Tedarikçi Seç")
        self.tedarikci_sec_btn.clicked.connect(self._tedarikci_sec_dialogu)
        tedarikci_layout = QHBoxLayout()
        tedarikci_layout.addWidget(self.tedarikci_id_input)
        tedarikci_layout.addWidget(self.tedarikci_sec_btn)

        self.fatura_no_input = QLineEdit()
        self.notlar_input = QTextEdit()
        self.notlar_input.setFixedHeight(40)
        self.alis_tarihi_input = QDateEdit(QDate.currentDate(), calendarPopup=True)

        form_layout.addRow("Tedarikçi ID:", tedarikci_layout)
        form_layout.addRow("", self.tedarikci_adi_label)
        form_layout.addRow("Fatura No:", self.fatura_no_input)
        form_layout.addRow("Alış Tarihi:", self.alis_tarihi_input)
        form_layout.addRow("Notlar:", self.notlar_input)

        self.main_layout.addLayout(form_layout)

        # Alış Kalemleri Tablosu
        self.kalemler_tablosu = QTableWidget()
        self.kalemler_tablosu.setColumnCount(5)
        self.kalemler_tablosu.setHorizontalHeaderLabels(["Ürün ID", "Ürün Adı", "Miktar", "Alış Fiyatı", "SKT"])
        self.kalemler_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.kalemler_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.kalemler_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.main_layout.addWidget(self.kalemler_tablosu)

        # Kalem Ekle/Sil Butonları
        kalem_buton_layout = QHBoxLayout()
        self.urun_id_kalem_input = QLineEdit()
        self.urun_id_kalem_input.setPlaceholderText("Ürün ID")
        self.urun_adi_kalem_label = QLabel("Ürün Adı: Yok")
        self.urun_sec_kalem_btn = QPushButton("Ürün Seç")
        self.urun_sec_kalem_btn.clicked.connect(self._urun_sec_kalem_dialogu)
        self.miktar_kalem_input = QSpinBox()
        self.miktar_kalem_input.setMinimum(1); self.miktar_kalem_input.setMaximum(99999)
        self.alis_fiyati_kalem_input = QDoubleSpinBox()
        self.alis_fiyati_kalem_input.setDecimals(2); self.alis_fiyati_kalem_input.setMaximum(999999.99); self.alis_fiyati_kalem_input.setSuffix(" ₺")
        self.skt_kalem_input = QDateEdit(calendarPopup=True)
        self.skt_kalem_input.setDateTime(self.skt_kalem_input.minimumDateTime()) # Tarihi temizle
        self.skt_kalem_input.setToolTip("Son Kullanma Tarihi (isteğe bağlı)")


        self.kalem_ekle_btn = QPushButton("Kalem Ekle")
        self.kalem_ekle_btn.clicked.connect(self._kalem_ekle)
        self.kalem_sil_btn = QPushButton("Seçili Kalemi Sil")
        self.kalem_sil_btn.clicked.connect(self._kalem_sil)

        kalem_buton_layout.addWidget(self.urun_id_kalem_input)
        kalem_buton_layout.addWidget(self.urun_sec_kalem_btn)
        kalem_buton_layout.addWidget(self.urun_adi_kalem_label)
        kalem_buton_layout.addWidget(QLabel("Miktar:"))
        kalem_buton_layout.addWidget(self.miktar_kalem_input)
        kalem_buton_layout.addWidget(QLabel("Alış Fiyatı:"))
        kalem_buton_layout.addWidget(self.alis_fiyati_kalem_input)
        kalem_buton_layout.addWidget(QLabel("SKT:"))
        kalem_buton_layout.addWidget(self.skt_kalem_input)
        kalem_buton_layout.addWidget(self.kalem_ekle_btn)
        kalem_buton_layout.addWidget(self.kalem_sil_btn)
        kalem_buton_layout.addStretch()
        self.main_layout.addLayout(kalem_buton_layout)

        # Ana Kaydet/İptal Butonları
        buton_layout = QHBoxLayout()
        self.kaydet_btn = QPushButton("Alışı Kaydet")
        self.kaydet_btn.clicked.connect(self.accept)
        self.iptal_btn = QPushButton("İptal")
        self.iptal_btn.clicked.connect(self.reject)
        buton_layout.addStretch()
        buton_layout.addWidget(self.kaydet_btn)
        buton_layout.addWidget(self.iptal_btn)
        self.main_layout.addLayout(buton_layout)

    def _tedarikci_sec_dialogu(self):
        # Basit bir tedarikçi seçme diyalogu
        tedarikci_id_str, ok = QMessageBox.information(self, "Tedarikçi Seç", "Lütfen tedarikçi ID'sini girin:", QMessageBox.Ok | QMessageBox.Cancel)
        if ok and tedarikci_id_str.isdigit():
            tedarikci_id = int(tedarikci_id_str)
            tedarikci = tedarikci_mantik.tedarikci_getir_by_id(tedarikci_id)
            if tedarikci:
                self.tedarikci_id_input.setText(str(tedarikci_id))
                self.tedarikci_adi_label.setText(f"Tedarikçi Adı: {tedarikci.ad}")
            else:
                QMessageBox.warning(self, "Tedarikçi Bulunamadı", "Belirtilen ID'ye sahip tedarikçi bulunamadı.")
                self.tedarikci_id_input.clear()
                self.tedarikci_adi_label.setText("Tedarikçi Adı: Yok")

    def _urun_sec_kalem_dialogu(self):
        # Basit bir ürün seçme diyalogu (şimdilik sadece ID'yi alıyoruz)
        urun_id_str, ok = QMessageBox.information(self, "Ürün Seç", "Lütfen ürün ID'sini girin:", QMessageBox.Ok | QMessageBox.Cancel)
        if ok and urun_id_str.isdigit():
            urun_id = int(urun_id_str)
            # Ürün mantığından ürünü çek
            urun = urun_mantik.urunleri_getir(1) # Şube ID'si sabit, geliştirilebilir
            secili_urun = next((u for u in urun if u.id == urun_id), None)
            if secili_urun:
                self.urun_id_kalem_input.setText(str(urun_id))
                self.urun_adi_kalem_label.setText(f"Ürün Adı: {secili_urun.ad}")
                # Eğer ürünün bir alış fiyatı varsa, onu varsayılan olarak getir
                if secili_urun.alis_fiyati:
                    self.alis_fiyati_kalem_input.setValue(float(secili_urun.alis_fiyati))
            else:
                QMessageBox.warning(self, "Ürün Bulunamadı", "Belirtilen ID'ye sahip ürün bulunamadı.")
                self.urun_id_kalem_input.clear()
                self.urun_adi_kalem_label.setText("Ürün Adı: Yok")
                self.alis_fiyati_kalem_input.setValue(0.00)

    def _kalem_ekle(self):
        urun_id_str = self.urun_id_kalem_input.text().strip()
        miktar = self.miktar_kalem_input.value()
        alis_fiyati = Decimal(str(self.alis_fiyati_kalem_input.value()))
        skt = self.skt_kalem_input.date().toPyDate() if self.skt_kalem_input.date().isValid() else None

        if not urun_id_str.isdigit():
            QMessageBox.warning(self, "Hata", "Lütfen geçerli bir Ürün ID'si girin.")
            return
        urun_id = int(urun_id_str)

        urun = urun_mantik.urunleri_getir(1) # Şube ID'si sabit, geliştirilebilir
        secili_urun = next((u for u in urun if u.id == urun_id), None)
        if not secili_urun:
            QMessageBox.warning(self, "Hata", "Belirtilen Ürün ID'sine sahip ürün bulunamadı.")
            return
        
        # Kalemleri listeye ekle
        yeni_kalem = {
            "urun_id": urun_id,
            "urun_adi": secili_urun.ad,
            "miktar": miktar,
            "alis_fiyati": alis_fiyati,
            "son_kullanma_tarihi": skt
        }
        self.kalemler.append(yeni_kalem)
        self._kalemler_tablosunu_doldur()
        self._kalem_formunu_temizle()

    def _kalem_sil(self):
        secili_satir = self.kalemler_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yok", "Lütfen silmek istediğiniz kalemi seçin.")
            return
        
        cevap = QMessageBox.question(self, "Kalem Sil", "Seçili kalemi silmek istediğinizden emin misiniz?", QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            del self.kalemler[secili_satir]
            self._kalemler_tablosunu_doldur()

    def _kalemler_tablosunu_doldur(self):
        self.kalemler_tablosu.setRowCount(len(self.kalemler))
        for i, kalem in enumerate(self.kalemler):
            self.kalemler_tablosu.setItem(i, 0, QTableWidgetItem(str(kalem['urun_id'])))
            self.kalemler_tablosu.setItem(i, 1, QTableWidgetItem(kalem['urun_adi']))
            self.kalemler_tablosu.setItem(i, 2, QTableWidgetItem(str(kalem['miktar'])))
            self.kalemler_tablosu.setItem(i, 3, QTableWidgetItem(f"{kalem['alis_fiyati']:.2f} ₺"))
            skt_str = kalem['son_kullanma_tarihi'].strftime('%Y-%m-%d') if kalem['son_kullanma_tarihi'] else "N/A"
            self.kalemler_tablosu.setItem(i, 4, QTableWidgetItem(skt_str))

    def _kalem_formunu_temizle(self):
        self.urun_id_kalem_input.clear()
        self.urun_adi_kalem_label.setText("Ürün Adı: Yok")
        self.miktar_kalem_input.setValue(1)
        self.alis_fiyati_kalem_input.setValue(0.00)
        self.skt_kalem_input.setDateTime(self.skt_kalem_input.minimumDateTime())

    def _formu_doldur(self):
        # Düzenleme modu için formu doldur
        self.tedarikci_id_input.setText(str(self.alis_verisi.tedarikci_id) if self.alis_verisi.tedarikci_id else "")
        if self.alis_verisi.tedarikci:
            self.tedarikci_adi_label.setText(f"Tedarikçi Adı: {self.alis_verisi.tedarikci.ad}")
        self.fatura_no_input.setText(self.alis_verisi.fatura_no or "")
        if self.alis_verisi.tarih:
            self.alis_tarihi_input.setDate(QDate(self.alis_verisi.tarih.year, self.alis_verisi.tarih.month, self.alis_verisi.tarih.day))
        self.notlar_input.setText(self.alis_verisi.notlar or "")

        # Kalemleri doldur
        self.kalemler = []
        for kalem_db in self.alis_verisi.kalemler:
            self.kalemler.append({
                "urun_id": kalem_db.urun_id,
                "urun_adi": kalem_db.urun.ad if kalem_db.urun else "Bilinmeyen Ürün",
                "miktar": kalem_db.miktar,
                "alis_fiyati": kalem_db.alis_fiyati,
                "son_kullanma_tarihi": kalem_db.son_kullanma_tarihi
            })
        self._kalemler_tablosunu_doldur()

    def bilgileri_al(self):
        alis_tarihi = self.alis_tarihi_input.date().toPyDate() if self.alis_tarihi_input.date().isValid() else None
        return {
            "alis_bilgileri": {
                "tedarikci_id": int(self.tedarikci_id_input.text()) if self.tedarikci_id_input.text().isdigit() else None,
                "fatura_no": self.fatura_no_input.text().strip() or None,
                "notlar": self.notlar_input.toPlainText().strip() or None,
                "tarih": alis_tarihi
            },
            "kalemler_listesi": self.kalemler
        }
# ===== AlisEkleDuzenleDialog SINIFI BİTİŞİ =====


# ===== AlisEkrani SINIFI BAŞLANGICI =====
class AlisEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Alış Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.yeni_alis_btn = QPushButton("Yeni Alış Ekle")
        self.yeni_alis_btn.clicked.connect(self.yeni_alis_ekle_dialogu)
        
        self.detay_goster_btn = QPushButton("Seçili Alışı Görüntüle")
        self.detay_goster_btn.clicked.connect(self.secili_alisi_goruntule_dialogu)

        self.yenile_btn = QPushButton("Yenile")
        self.yenile_btn.clicked.connect(self.yenile)

        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.yeni_alis_btn)
        ust_panel_layout.addWidget(self.detay_goster_btn)
        ust_panel_layout.addWidget(self.yenile_btn)
        self.ana_layout.addLayout(ust_panel_layout)

        self.alis_tablosu = QTableWidget()
        self.alis_tablosu.setColumnCount(4)
        self.alis_tablosu.setHorizontalHeaderLabels(["ID", "Tarih", "Tedarikçi", "Fatura No"])
        self.alis_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.alis_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.alis_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.alis_tablosu)

    def yenile(self):
        self._tabloyu_doldur()

    def _tabloyu_doldur(self):
        try:
            alislar = alis_mantik.alis_listele()
            self.alis_tablosu.setRowCount(len(alislar))
            for i, alis in enumerate(alislar):
                self.alis_tablosu.setItem(i, 0, QTableWidgetItem(str(alis.id)))
                self.alis_tablosu.setItem(i, 1, QTableWidgetItem(alis.tarih.strftime('%Y-%m-%d %H:%M')))
                self.alis_tablosu.setItem(i, 2, QTableWidgetItem(alis.tedarikci.ad if alis.tedarikci else "N/A"))
                self.alis_tablosu.setItem(i, 3, QTableWidgetItem(alis.fatura_no or "N/A"))
                self.alis_tablosu.item(i, 0).setData(Qt.UserRole, alis.id) # Alış ID'sini sakla
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Alışlar yüklenirken bir sorun oluştu:\n{e}")

    def yeni_alis_ekle_dialogu(self):
        dialog = AlisEkleDuzenleDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            alis_verileri = dialog.bilgileri_al()
            try:
                alis_mantik.alis_kaydet(
                    alis_bilgileri=alis_verileri['alis_bilgileri'],
                    kalemler_listesi=alis_verileri['kalemler_listesi']
                )
                QMessageBox.information(self, "Başarılı", "Alış başarıyla kaydedildi.")
                self.yenile()
            except ValueError as e:
                QMessageBox.warning(self, "Eksik/Geçersiz Bilgi", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Alış kaydedilirken bir hata oluştu:\n{e}")

    def secili_alisi_goruntule_dialogu(self):
        secili_satir = self.alis_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yok", "Lütfen görüntülemek istediğiniz alışı seçin.")
            return
        
        alis_id = self.alis_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        try:
            alis_detay = alis_mantik.alis_detay_getir(alis_id)
            if not alis_detay:
                QMessageBox.warning(self, "Hata", "Alış detayı bulunamadı.")
                return

            # Alış detaylarını göstermek için basit bir mesaj kutusu veya yeni bir diyalog kullanılabilir
            detay_mesaji = f"Alış ID: {alis_detay.id}\n" \
                           f"Tarih: {alis_detay.tarih.strftime('%Y-%m-%d %H:%M')}\n" \
                           f"Tedarikçi: {alis_detay.tedarikci.ad if alis_detay.tedarikci else 'N/A'}\n" \
                           f"Fatura No: {alis_detay.fatura_no or 'N/A'}\n" \
                           f"Notlar: {alis_detay.notlar or 'Yok'}\n\n" \
                           f"--- Kalemler ---\n"
            for kalem in alis_detay.kalemler:
                detay_mesaji += f"- Ürün: {kalem.urun.ad if kalem.urun else 'Bilinmeyen Ürün'}, Miktar: {kalem.miktar}, Alış Fiyatı: {kalem.alis_fiyati:.2f}₺, SKT: {kalem.son_kullanma_tarihi.strftime('%Y-%m-%d') if kalem.son_kullanma_tarihi else 'N/A'}\n"
            
            QMessageBox.information(self, "Alış Detayı", detay_mesaji)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Alış detayı görüntülenirken bir sorun oluştu:\n{e}")

# ===== AlisEkrani SINIFI BİTİŞİ =====
