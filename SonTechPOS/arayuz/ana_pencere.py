# Dosya Adı: arayuz/ana_pencere.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 08:45
# Yapılan İşlem: Tüm modül ekranları import edildi ve ana panele entegre edildi.

from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QMessageBox
from PyQt5.QtCore import Qt, QTimer

from arayuz.ana_panel_ekrani import AnaPanelEkrani
from moduller.satis.satis_ekrani import SatisEkrani
from moduller.urun.urun_ekrani import UrunEkrani
from moduller.stok.stok_ekrani import StokEkrani
from moduller.musteri.musteri_ekrani import MusteriEkrani
from moduller.raporlar.rapor_ekrani import RaporEkrani
from moduller.ayarlar.ayarlar_ekrani import AyarlarEkrani
from moduller.tedarikci.tedarikci_ekrani import TedarikciEkrani
from moduller.marka.marka_ekrani import MarkaEkrani
from moduller.kategori.kategori_ekrani import KategoriEkrani
from moduller.kullanici.kullanici_ekrani import KullaniciEkrani
from moduller.promosyon.promosyon_ekrani import PromosyonEkrani
from moduller.vardiya.vardiya_ekrani import VardiyaEkrani
from moduller.alis.alis_ekrani import AlisEkrani

class AnaPencere(QMainWindow):
    def __init__(self, kullanici=None):
        super().__init__()
        self.aktif_kullanici = kullanici
        self.setWindowTitle("SonTechPOS")
        self.setGeometry(100, 100, 1366, 768)

        self._esc_timer = QTimer()
        self._esc_timer.setSingleShot(True)
        self._esc_press_count = 0

        self._icerik_alani_olustur()
        self.setCentralWidget(self.icerik_alani)

    def _icerik_alani_olustur(self):
        self.icerik_alani = QStackedWidget()

        self.ana_panel = AnaPanelEkrani(self.aktif_kullanici)
        self.ana_panel.modul_ac_istegi.connect(self.modul_ac)
        self.icerik_alani.addWidget(self.ana_panel)

        self.modul_ekranlari = {
            "Satış": SatisEkrani(),
            "Ürünler": UrunEkrani(),
            "Stok": StokEkrani(),
            "Alışlar": AlisEkrani(),
            "Müşteriler": MusteriEkrani(),
            "Tedarikçiler": TedarikciEkrani(),
            "Promosyonlar": PromosyonEkrani(),
            "Vardiyalar": VardiyaEkrani(),
            "Raporlar": RaporEkrani(),
            "Kullanıcılar": KullaniciEkrani(),
            "Markalar": MarkaEkrani(),
            "Kategoriler": KategoriEkrani(),
            "Ayarlar": AyarlarEkrani(),
        }

        for ekran in self.modul_ekranlari.values():
            self.icerik_alani.addWidget(ekran)

    def modul_ac(self, modul_adi):
        if modul_adi == "Kapat":
            self.close()
            return

        if modul_adi in self.modul_ekranlari:
            hedef_widget = self.modul_ekranlari[modul_adi]
            self.icerik_alani.setCurrentWidget(hedef_widget)
        else:
            QMessageBox.information(self, "Modül Hazır Değil", f"'{modul_adi}' modülü henüz kullanıma hazır değil.")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            if self.icerik_alani.currentWidget() is not self.ana_panel:
                self.icerik_alani.setCurrentWidget(self.ana_panel)
                self._esc_press_count = 0
            else:
                self._esc_press_count += 1
                if self._esc_press_count == 2:
                    self.close()
                else:
                    self.statusBar().showMessage("Çıkmak için tekrar ESC tuşuna basın...", 2000)
                    self._esc_timer.start(500)
                    self._esc_timer.timeout.connect(lambda: setattr(self, '_esc_press_count', 0))
        else:
            self._esc_press_count = 0
            super().keyPressEvent(event)

    def closeEvent(self, event):
        cevap = QMessageBox.question(self, 'Programı Kapat', 
                                     "Programdan çıkmak istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if cevap == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()
