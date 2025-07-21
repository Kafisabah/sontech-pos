# Dosya Adı: moduller/satis/satis_ekrani.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 15:30
# Yapılan İşlem: Arayüz, gönderilen görsellere uygun olarak tamamen yeniden tasarlandı.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QLineEdit,
                             QMessageBox, QListWidget, QListWidgetItem, QDialog, QInputDialog, QFrame, QGridLayout, QToolButton)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QIcon
from decimal import Decimal

from moduller.satis import satis_mantik
from moduller.satis.odeme_ekrani import OdemeEkraniDialog
from moduller.musteri.musteri_ekrani import MusteriEkrani
from moduller.satis.sepet_yoneticisi import SepetYoneticisi
from arayuz.widgetlar.indirim_dialogu import IndirimDialogu

class SatisEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.aktif_sube_id = 1
        self.aktif_kullanici_id = 1
        self.sepet_yoneticisi = SepetYoneticisi()
        self.aktif_musteri = None
        self._arayuzu_olustur()
        self._hizli_satis_butonlarini_yukle()

    def _arayuzu_olustur(self):
        self.ana_layout = QHBoxLayout(self)
        self.ana_layout.setSpacing(10)
        self.ana_layout.setContentsMargins(5, 5, 5, 5)

        sol_panel = self._sol_panel_olustur()
        orta_panel = self._orta_panel_olustur()
        sag_panel = self._sag_panel_olustur()

        self.ana_layout.addWidget(sol_panel, 1)
        self.ana_layout.addWidget(orta_panel, 4)
        self.ana_layout.addWidget(sag_panel, 2)

    def _sol_panel_olustur(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)
        layout.setSpacing(5)
        layout.setAlignment(Qt.AlignTop)

        butonlar = [
            ("Fiş Notu", "📝"), ("İptal", "↩️"), ("Düzelt", "✏️"),
            ("Adisyon", "📄"), ("Perakende", "🛒"), ("Beklet", "⏸️"),
            ("Bekleyen", "🕒"), ("Satış Seç", "🔍"), ("Çekmece", "🗄️")
        ]
        for metin, ikon in butonlar:
            buton = QToolButton()
            buton.setText(f"{ikon}\n{metin}")
            buton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
            buton.setFixedSize(90, 70)
            layout.addWidget(buton)
        
        return panel

    def _orta_panel_olustur(self):
        panel = QFrame()
        layout = QVBoxLayout(panel)
        
        self.barkod_input = QLineEdit()
        self.barkod_input.setPlaceholderText("Barkod Okutun veya Ürün Adı Yazın...")
        self.barkod_input.setStyleSheet("font-size: 18px; padding: 10px; border: 1px solid #ccc; border-radius: 5px;")
        self.barkod_input.returnPressed.connect(self._barkod_ile_ekle)
        layout.addWidget(self.barkod_input)
        
        self.sepet_tablosu = QTableWidget()
        self.sepet_tablosu.setColumnCount(5)
        self.sepet_tablosu.setHorizontalHeaderLabels(["Ürün Adı", "Miktar", "Birim Fiyat", "İndirim", "Toplam"])
        self.sepet_tablosu.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.sepet_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.sepet_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.sepet_tablosu)
        
        alt_panel = QHBoxLayout()
        self.toplam_tutar_label = QLabel("0.00")
        self.toplam_tutar_label.setStyleSheet("font-size: 36px; font-weight: bold; color: #2c3e50;")
        
        self.odeme_al_btn = QPushButton("Ödeme Al")
        self.odeme_al_btn.setFixedHeight(60)
        self.odeme_al_btn.setStyleSheet("background-color: #27ae60; color: white; font-size: 20px; font-weight: bold; border-radius: 5px;")
        self.odeme_al_btn.clicked.connect(self.odeme_al)

        alt_panel.addWidget(self.toplam_tutar_label, 1, Qt.AlignVCenter | Qt.AlignRight)
        alt_panel.addWidget(self.odeme_al_btn, 0, Qt.AlignRight)
        layout.addLayout(alt_panel)

        return panel

    def _sag_panel_olustur(self):
        panel = QFrame()
        self.hizli_satis_layout = QGridLayout(panel)
        self.hizli_satis_layout.setSpacing(5)
        return panel

    def _hizli_satis_butonlarini_yukle(self):
        try:
            urunler = satis_mantik.hizli_satis_urunlerini_getir(self.aktif_sube_id)
            pozisyonlar = [(i, j) for i in range(5) for j in range(4)]
            for i, urun_veri in enumerate(urunler):
                if i >= len(pozisyonlar): break
                
                buton = QToolButton()
                buton.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
                buton.setText(f"{urun_veri['urun'].ad}\n{urun_veri['fiyat'].satis_fiyati:.2f} ₺")
                buton.setFixedSize(120, 80)
                buton.clicked.connect(lambda checked, u=urun_veri: self._urun_verisini_isle_ve_ekle(u))
                self.hizli_satis_layout.addWidget(buton, *pozisyonlar[i])
        except Exception as e:
            print(f"HATA: Hızlı satış butonları yüklenemedi: {e}")

    def _sepeti_guncelle(self):
        self.sepet_tablosu.setRowCount(0)
        sepet = self.sepet_yoneticisi.sepet
        self.sepet_tablosu.setRowCount(len(sepet))
        
        toplamlar = self.sepet_yoneticisi.sepeti_hesapla()
        
        for i, kalem in enumerate(sepet):
            kalem_toplam = (kalem['fiyat'].satis_fiyati * kalem['miktar']) - kalem['indirim_tutari']
            self.sepet_tablosu.setItem(i, 0, QTableWidgetItem(kalem['urun'].ad))
            self.sepet_tablosu.setItem(i, 1, QTableWidgetItem(str(kalem['miktar'])))
            self.sepet_tablosu.setItem(i, 2, QTableWidgetItem(f"{kalem['fiyat'].satis_fiyati:.2f} ₺"))
            self.sepet_tablosu.setItem(i, 3, QTableWidgetItem(kalem['indirim_aciklamasi']))
            self.sepet_tablosu.setItem(i, 4, QTableWidgetItem(f"{kalem_toplam:.2f} ₺"))
            self.sepet_tablosu.item(i, 0).setData(Qt.UserRole, i)
        
        self.toplam_tutar_label.setText(f"{toplamlar['genel_toplam']:.2f}")

    def _barkod_ile_ekle(self):
        barkod = self.barkod_input.text().strip()
        if not barkod: return
        try:
            sonuclar = satis_mantik.urun_ara(barkod, self.aktif_sube_id)
            if sonuclar and sonuclar[0]['urun'].barkod == barkod:
                self._urun_verisini_isle_ve_ekle(sonuclar[0])
            else:
                QMessageBox.warning(self, "Bulunamadı", "Bu barkoda sahip bir ürün bulunamadı.")
        finally:
            self.barkod_input.clear()

    def _urun_verisini_isle_ve_ekle(self, urun_verisi):
        basarili, mesaj = self.sepet_yoneticisi.sepete_ekle(urun_verisi)
        if basarili:
            self._sepeti_guncelle()
            if "UYARI" in mesaj:
                QMessageBox.warning(self, "Stok Uyarısı", mesaj)
        else:
            QMessageBox.critical(self, "Hata", mesaj)

    def odeme_al(self):
        if not self.sepet_yoneticisi.sepet:
            QMessageBox.warning(self, "Boş Sepet", "Satış yapmak için sepete ürün eklemelisiniz.")
            return
        toplamlar = self.sepet_yoneticisi.sepeti_hesapla()
        toplam_tutar = toplamlar.get('genel_toplam')
        musteri_adi = self.aktif_musteri['ad'] if self.aktif_musteri else None
        
        dialog = OdemeEkraniDialog(toplam_tutar, musteri_adi, self)
        if dialog.exec_() == QDialog.Accepted:
            odemeler = dialog.bilgileri_al()
            if not odemeler: return
            try:
                musteri_id = self.aktif_musteri['id'] if self.aktif_musteri else None
                satis_id = satis_mantik.satis_yap(self.sepet_yoneticisi.sepet, odemeler, toplamlar, self.aktif_sube_id, self.aktif_kullanici_id, musteri_id)
                QMessageBox.information(self, "Başarılı", f"Satış (No: {satis_id}) başarıyla tamamlandı.")
                self.sepeti_temizle()
            except Exception as e:
                QMessageBox.critical(self, "Satış Hatası", f"Satış tamamlanamadı:\n{e}")

    def sepeti_temizle(self):
        self.sepet_yoneticisi.sepeti_temizle()
        self.aktif_musteri = None
        self._sepeti_guncelle()
