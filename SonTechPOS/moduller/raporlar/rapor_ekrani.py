# Dosya Adı: moduller/raporlar/rapor_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 14:40
# Yapılan İşlem: Hatalı 'LOG_ACTION_SETTINGS_UPDATE' import ifadesi kaldırıldı.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QMessageBox,
                             QDateEdit, QCalendarWidget, QComboBox, QSpinBox)
from PyQt5.QtCore import Qt, QDate
from decimal import Decimal

from moduller.raporlar import rapor_mantik
from moduller.urun import urun_mantik # SKT ve Sipariş Önerisi raporları için

# ===== RaporEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class RaporEkrani(QWidget):
    """Raporlama modülünün ana arayüz widget'ı."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aktif_sube_id = 1 # Varsayılan şube ID'si
        self._arayuzu_olustur()
        self.rapor_tipi_combo.setCurrentIndex(0) # Başlangıçta Günlük Satış Özeti'ni seç
        self._rapor_tipi_degisti(0) # İlk raporu yükle

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)

        # Üst Panel: Başlık ve Filtreler
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Raporlar")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.rapor_tipi_combo = QComboBox()
        self.rapor_tipi_combo.addItems([
            "Günlük Satış Özeti",
            "En Çok Satan Ürünler (Adet)",
            "En Çok Satan Ürünler (Ciro)",
            "Kâr/Zarar Raporu",
            "SKT Raporu",
            "Sipariş Önerileri"
        ])
        self.rapor_tipi_combo.currentIndexChanged.connect(self._rapor_tipi_degisti)

        self.baslangic_tarih_label = QLabel("Başlangıç:")
        self.baslangic_tarih_input = QDateEdit(QDate.currentDate(), calendarPopup=True)
        self.baslangic_tarih_input.setDateTime(self.baslangic_tarih_input.minimumDateTime()) # Tarihi temizle
        
        self.bitis_tarih_label = QLabel("Bitiş:")
        self.bitis_tarih_input = QDateEdit(QDate.currentDate(), calendarPopup=True)
        self.bitis_tarih_input.setDateTime(self.bitis_tarih_input.minimumDateTime()) # Tarihi temizle

        self.limit_label = QLabel("Limit:")
        self.limit_input = QSpinBox()
        self.limit_input.setMinimum(1); self.limit_input.setMaximum(100); self.limit_input.setValue(10)

        self.skt_esik_label = QLabel("SKT Eşik (Gün):")
        self.skt_esik_input = QSpinBox()
        self.skt_esik_input.setMinimum(0); self.skt_esik_input.setMaximum(365); self.skt_esik_input.setValue(30)

        self.raporu_getir_btn = QPushButton("Raporu Getir")
        self.raporu_getir_btn.clicked.connect(self.raporu_goster)

        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.rapor_tipi_combo)
        ust_panel_layout.addWidget(self.baslangic_tarih_label)
        ust_panel_layout.addWidget(self.baslangic_tarih_input)
        ust_panel_layout.addWidget(self.bitis_tarih_label)
        ust_panel_layout.addWidget(self.bitis_tarih_input)
        ust_panel_layout.addWidget(self.limit_label)
        ust_panel_layout.addWidget(self.limit_input)
        ust_panel_layout.addWidget(self.skt_esik_label)
        ust_panel_layout.addWidget(self.skt_esik_input)
        ust_panel_layout.addWidget(self.raporu_getir_btn)
        self.ana_layout.addLayout(ust_panel_layout)

        # Rapor Tablosu
        self.rapor_tablosu = QTableWidget()
        self.ana_layout.addWidget(self.rapor_tablosu)

    def _rapor_tipi_degisti(self, index):
        # Tarih filtrelerini ve limit/eşik alanlarını rapor tipine göre gizle/göster
        rapor_tipi = self.rapor_tipi_combo.currentText()
        
        tarih_filtreleri_goster = (rapor_tipi in ["Günlük Satış Özeti", "En Çok Satan Ürünler (Adet)", "En Çok Satan Ürünler (Ciro)", "Kâr/Zarar Raporu"])
        limit_goster = (rapor_tipi in ["En Çok Satan Ürünler (Adet)", "En Çok Satan Ürünler (Ciro)"])
        skt_esik_goster = (rapor_tipi == "SKT Raporu")

        self.baslangic_tarih_label.setVisible(tarih_filtreleri_goster)
        self.baslangic_tarih_input.setVisible(tarih_filtreleri_goster)
        self.bitis_tarih_label.setVisible(tarih_filtreleri_goster)
        self.bitis_tarih_input.setVisible(tarih_filtreleri_goster)
        
        self.limit_label.setVisible(limit_goster)
        self.limit_input.setVisible(limit_goster)

        self.skt_esik_label.setVisible(skt_esik_goster)
        self.skt_esik_input.setVisible(skt_esik_goster)

        self.raporu_goster() # Rapor tipi değişince otomatik olarak raporu yenile

    def raporu_goster(self):
        self.rapor_tablosu.clear()
        self.rapor_tablosu.setRowCount(0)
        rapor_tipi = self.rapor_tipi_combo.currentText()
        baslangic_tarihi = self.baslangic_tarih_input.date().toPyDate() if self.baslangic_tarih_input.date().isValid() else None
        bitis_tarihi = self.bitis_tarih_input.date().toPyDate() if self.bitis_tarih_input.date().isValid() else None
        limit = self.limit_input.value()
        skt_esik = self.skt_esik_input.value()

        try:
            if rapor_tipi == "Günlük Satış Özeti":
                sonuclar = rapor_mantik.gunluk_satis_ozeti_getir(self.aktif_sube_id, baslangic_tarihi, bitis_tarihi)
                self._tabloyu_doldur_gunluk_satis(sonuclar)
            elif rapor_tipi == "En Çok Satan Ürünler (Adet)":
                sonuclar = rapor_mantik.en_cok_satan_urunler_adet_getir(self.aktif_sube_id, limit, baslangic_tarihi, bitis_tarihi)
                self._tabloyu_doldur_en_cok_satan_adet(sonuclar)
            elif rapor_tipi == "En Çok Satan Ürünler (Ciro)":
                sonuclar = rapor_mantik.en_cok_satan_urunler_ciro_getir(self.aktif_sube_id, limit, baslangic_tarihi, bitis_tarihi)
                self._tabloyu_doldur_en_cok_satan_ciro(sonuclar)
            elif rapor_tipi == "Kâr/Zarar Raporu":
                sonuclar = rapor_mantik.kar_zarar_raporu_getir(self.aktif_sube_id, baslangic_tarihi, bitis_tarihi)
                self._tabloyu_doldur_kar_zarar(sonuclar)
            elif rapor_tipi == "SKT Raporu":
                sonuclar = rapor_mantik.skt_raporu_getir(self.aktif_sube_id, skt_esik)
                self._tabloyu_doldur_skt(sonuclar)
            elif rapor_tipi == "Sipariş Önerileri":
                sonuclar = urun_mantik.siparis_onerisi_getir(self.aktif_sube_id)
                self._tabloyu_doldur_siparis_oneri(sonuclar)

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Rapor oluşturulurken bir sorun oluştu:\n{e}")

    def _tabloyu_doldur_gunluk_satis(self, sonuclar):
        self.rapor_tablosu.setColumnCount(3)
        self.rapor_tablosu.setHorizontalHeaderLabels(["Tarih", "Toplam İşlem", "Toplam Ciro"])
        self.rapor_tablosu.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.rapor_tablosu.setRowCount(len(sonuclar))
        for satir_index, sonuc in enumerate(sonuclar):
            tarih_str = sonuc['gun'].strftime('%d.%m.%Y')
            toplam_ciro_str = f"{sonuc['toplam_ciro']:.2f} ₺"
            self.rapor_tablosu.setItem(satir_index, 0, QTableWidgetItem(tarih_str))
            self.rapor_tablosu.setItem(satir_index, 1, QTableWidgetItem(str(sonuc['islem_sayisi'])))
            self.rapor_tablosu.setItem(satir_index, 2, QTableWidgetItem(toplam_ciro_str))

    def _tabloyu_doldur_en_cok_satan_adet(self, sonuclar):
        self.rapor_tablosu.setColumnCount(4)
        self.rapor_tablosu.setHorizontalHeaderLabels(["ID", "Barkod", "Ürün Adı", "Toplam Satış Adedi"])
        self.rapor_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rapor_tablosu.setRowCount(len(sonuclar))
        for satir_index, sonuc in enumerate(sonuclar):
            self.rapor_tablosu.setItem(satir_index, 0, QTableWidgetItem(str(sonuc['urun_id'])))
            self.rapor_tablosu.setItem(satir_index, 1, QTableWidgetItem(sonuc['barkod']))
            self.rapor_tablosu.setItem(satir_index, 2, QTableWidgetItem(sonuc['ad']))
            self.rapor_tablosu.setItem(satir_index, 3, QTableWidgetItem(str(sonuc['toplam_satilan_adet'])))

    def _tabloyu_doldur_en_cok_satan_ciro(self, sonuclar):
        self.rapor_tablosu.setColumnCount(4)
        self.rapor_tablosu.setHorizontalHeaderLabels(["ID", "Barkod", "Ürün Adı", "Toplam Ciro"])
        self.rapor_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rapor_tablosu.setRowCount(len(sonuclar))
        for satir_index, sonuc in enumerate(sonuclar):
            self.rapor_tablosu.setItem(satir_index, 0, QTableWidgetItem(str(sonuc['urun_id'])))
            self.rapor_tablosu.setItem(satir_index, 1, QTableWidgetItem(sonuc['barkod']))
            self.rapor_tablosu.setItem(satir_index, 2, QTableWidgetItem(sonuc['ad']))
            self.rapor_tablosu.setItem(satir_index, 3, QTableWidgetItem(f"{sonuc['toplam_ciro']:.2f} ₺"))

    def _tabloyu_doldur_kar_zarar(self, sonuclar):
        self.rapor_tablosu.setColumnCount(6)
        self.rapor_tablosu.setHorizontalHeaderLabels(["ID", "Barkod", "Ürün Adı", "Toplam Ciro", "Tahmini Maliyet", "Tahmini Kâr"])
        self.rapor_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rapor_tablosu.setRowCount(len(sonuclar))
        for satir_index, sonuc in enumerate(sonuclar):
            self.rapor_tablosu.setItem(satir_index, 0, QTableWidgetItem(str(sonuc['urun_id'])))
            self.rapor_tablosu.setItem(satir_index, 1, QTableWidgetItem(sonuc['barkod']))
            self.rapor_tablosu.setItem(satir_index, 2, QTableWidgetItem(sonuc['ad']))
            self.rapor_tablosu.setItem(satir_index, 3, QTableWidgetItem(f"{sonuc['toplam_ciro']:.2f} ₺"))
            self.rapor_tablosu.setItem(satir_index, 4, QTableWidgetItem(f"{sonuc['tahmini_maliyet']:.2f} ₺"))
            kar_str = f"{sonuc['tahmini_kar']:.2f} ₺"
            if sonuc['tahmini_kar'] < 0:
                kar_item = QTableWidgetItem(kar_str)
                kar_item.setForeground(Qt.red)
                self.rapor_tablosu.setItem(satir_index, 5, kar_item)
            else:
                self.rapor_tablosu.setItem(satir_index, 5, QTableWidgetItem(kar_str))

    def _tabloyu_doldur_skt(self, sonuclar):
        self.rapor_tablosu.setColumnCount(7)
        self.rapor_tablosu.setHorizontalHeaderLabels(["Alış ID", "Ürün ID", "Ürün Adı", "Marka", "Miktar", "SKT", "Kalan Gün"])
        self.rapor_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rapor_tablosu.setRowCount(len(sonuclar))
        for satir_index, sonuc in enumerate(sonuclar):
            self.rapor_tablosu.setItem(satir_index, 0, QTableWidgetItem(str(sonuc['alis_id'])))
            self.rapor_tablosu.setItem(satir_index, 1, QTableWidgetItem(str(sonuc['urun_id'])))
            self.rapor_tablosu.setItem(satir_index, 2, QTableWidgetItem(sonuc['urun_adi']))
            self.rapor_tablosu.setItem(satir_index, 3, QTableWidgetItem(sonuc['marka_adi'] or "N/A"))
            self.rapor_tablosu.setItem(satir_index, 4, QTableWidgetItem(str(sonuc['miktar'])))
            skt_str = sonuc['skt'].strftime('%Y-%m-%d') if sonuc['skt'] else "N/A"
            self.rapor_tablosu.setItem(satir_index, 5, QTableWidgetItem(skt_str))
            
            kalan_gun_str = str(sonuc['kalan_gun'])
            if sonuc['kalan_gun'] is not None:
                if sonuc['kalan_gun'] < 0:
                    kalan_gun_item = QTableWidgetItem(f"Geçmiş ({abs(sonuc['kalan_gun'])} gün)")
                    kalan_gun_item.setForeground(Qt.red)
                    self.rapor_tablosu.setItem(satir_index, 6, kalan_gun_item)
                elif sonuc['kalan_gun'] <= self.skt_esik_input.value(): # Eşik değeri ile karşılaştır
                    kalan_gun_item = QTableWidgetItem(kalan_gun_str)
                    kalan_gun_item.setForeground(Qt.darkYellow)
                    self.rapor_tablosu.setItem(satir_index, 6, kalan_gun_item)
                else:
                    self.rapor_tablosu.setItem(satir_index, 6, QTableWidgetItem(kalan_gun_str))
            else:
                self.rapor_tablosu.setItem(satir_index, 6, QTableWidgetItem("N/A"))


    def _tabloyu_doldur_siparis_oneri(self, sonuclar):
        self.rapor_tablosu.setColumnCount(7)
        self.rapor_tablosu.setHorizontalHeaderLabels(["ID", "Barkod", "Ürün Adı", "Mevcut Stok", "Min. Stok", "Son Alış F.", "Son Tedarikçi"])
        self.rapor_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.rapor_tablosu.setRowCount(len(sonuclar))
        for satir_index, sonuc in enumerate(sonuclar):
            self.rapor_tablosu.setItem(satir_index, 0, QTableWidgetItem(str(sonuc['id'])))
            self.rapor_tablosu.setItem(satir_index, 1, QTableWidgetItem(sonuc['barkod']))
            self.rapor_tablosu.setItem(satir_index, 2, QTableWidgetItem(sonuc['ad']))
            self.rapor_tablosu.setItem(satir_index, 3, QTableWidgetItem(str(sonuc['mevcut_stok'])))
            self.rapor_tablosu.setItem(satir_index, 4, QTableWidgetItem(str(sonuc['min_stok_seviyesi'])))
            self.rapor_tablosu.setItem(satir_index, 5, QTableWidgetItem(f"{sonuc['son_alis_fiyati']:.2f} ₺" if sonuc['son_alis_fiyati'] else "0.00 ₺"))
            self.rapor_tablosu.setItem(satir_index, 6, QTableWidgetItem(sonuc['son_tedarikci'] or "N/A"))

# ===== RaporEkrani SINIFI BİTİŞİ =====
