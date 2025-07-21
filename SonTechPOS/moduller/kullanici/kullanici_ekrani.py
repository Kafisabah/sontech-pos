# Dosya Adı: moduller/kullanici/kullanici_ekrani.py
# Oluşturma Tarihi / Saati: 12.07.2025 11:15
# Yapılan İşlem: Kullanıcı yönetimi için arayüz ekranı oluşturuldu.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QCheckBox, QComboBox)
from PyQt5.QtCore import Qt
from sqlalchemy.exc import IntegrityError

from moduller.kullanici import kullanici_mantik

# ===== KullaniciDuzenlemeDialog SINIFI BAŞLANGICI =====
class KullaniciDuzenlemeDialog(QDialog):
    def __init__(self, kullanici_verisi=None, parent=None):
        super().__init__(parent)
        self.kullanici_verisi = kullanici_verisi
        self.setWindowTitle("Kullanıcı Düzenle" if kullanici_verisi else "Yeni Kullanıcı Ekle")
        self.setMinimumWidth(400)
        self._arayuzu_olustur()
        if kullanici_verisi:
            self._formu_doldur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)
        self.kullanici_adi_input = QLineEdit()
        self.sifre_input = QLineEdit()
        self.sifre_input.setEchoMode(QLineEdit.Password) # Şifreyi gizle
        self.tam_ad_input = QLineEdit()
        self.rol_combo = QComboBox()
        self.rol_combo.addItems(["kullanici", "admin"])
        self.aktif_checkbox = QCheckBox("Aktif")
        self.aktif_checkbox.setChecked(True) # Varsayılan olarak aktif

        self.layout.addRow("Kullanıcı Adı:", self.kullanici_adi_input)
        self.layout.addRow("Şifre:", self.sifre_input)
        self.layout.addRow("Tam Ad:", self.tam_ad_input)
        self.layout.addRow("Rol:", self.rol_combo)
        self.layout.addRow("Durum:", self.aktif_checkbox)

        # Düzenleme modundaysa şifre alanı isteğe bağlı olsun
        if self.kullanici_verisi:
            self.sifre_input.setPlaceholderText("Değiştirmek istemiyorsanız boş bırakın")
            # Kullanıcı adını düzenleme modunda değiştirilemez yap (isteğe bağlı, benzersizlik için)
            # self.kullanici_adi_input.setReadOnly(True)

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
        """Mevcut kullanıcı verilerini forma yükler."""
        self.kullanici_adi_input.setText(self.kullanici_verisi.kullanici_adi)
        self.tam_ad_input.setText(self.kullanici_verisi.tam_ad or "")
        self.rol_combo.setCurrentText(self.kullanici_verisi.rol)
        self.aktif_checkbox.setChecked(self.kullanici_verisi.aktif)

    def bilgileri_al(self):
        return {
            "kullanici_adi": self.kullanici_adi_input.text().strip(),
            "sifre": self.sifre_input.text().strip() or None, # Şifre boşsa None döndür
            "tam_ad": self.tam_ad_input.text().strip() or None,
            "rol": self.rol_combo.currentText(),
            "aktif": self.aktif_checkbox.isChecked()
        }
# ===== KullaniciDuzenlemeDialog SINIFI BİTİŞİ =====


# ===== KullaniciEkrani SINIFI BAŞLANGICI =====
class KullaniciEkrani(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Kullanıcı Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.arama_input = QLineEdit()
        self.arama_input.setPlaceholderText("Kullanıcı Adı veya Tam Ad Ara...")
        self.arama_input.textChanged.connect(self.arama_yap)

        self.yeni_kullanici_btn = QPushButton("Yeni Kullanıcı Ekle")
        self.yeni_kullanici_btn.clicked.connect(self.yeni_kullanici_ekle_dialogu)
        
        self.duzenle_btn = QPushButton("Seçili Kullanıcıyı Düzenle")
        self.duzenle_btn.clicked.connect(self.secili_kullaniciyi_duzenle_dialogu)

        self.durum_degistir_btn = QPushButton("Durumu Değiştir")
        self.durum_degistir_btn.clicked.connect(self.secili_kullanici_durum_degistir)

        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.arama_input)
        ust_panel_layout.addWidget(self.yeni_kullanici_btn)
        ust_panel_layout.addWidget(self.duzenle_btn)
        ust_panel_layout.addWidget(self.durum_degistir_btn)
        self.ana_layout.addLayout(ust_panel_layout)

        self.kullanici_tablosu = QTableWidget()
        self.kullanici_tablosu.setColumnCount(5)
        self.kullanici_tablosu.setHorizontalHeaderLabels(["ID", "Kullanıcı Adı", "Tam Ad", "Rol", "Aktif"])
        self.kullanici_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.kullanici_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.kullanici_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.ana_layout.addWidget(self.kullanici_tablosu)

    def yenile(self):
        self._tabloyu_doldur()

    def arama_yap(self, text):
        self._tabloyu_doldur(arama_terimi=text)

    def _tabloyu_doldur(self, arama_terimi: str = None):
        try:
            kullanicilar = kullanici_mantik.kullanicilari_getir(include_inactive=True, arama_terimi=arama_terimi)
            self.kullanici_tablosu.setRowCount(len(kullanicilar))
            for i, kullanici in enumerate(kullanicilar):
                self.kullanici_tablosu.setItem(i, 0, QTableWidgetItem(str(kullanici.id)))
                self.kullanici_tablosu.setItem(i, 1, QTableWidgetItem(kullanici.kullanici_adi))
                self.kullanici_tablosu.setItem(i, 2, QTableWidgetItem(kullanici.tam_ad or "N/A"))
                self.kullanici_tablosu.setItem(i, 3, QTableWidgetItem(kullanici.rol))
                aktif_durum_str = "Evet" if kullanici.aktif else "Hayır"
                self.kullanici_tablosu.setItem(i, 4, QTableWidgetItem(aktif_durum_str))
                # Tüm kullanıcı nesnesini UserRole'a kaydet
                self.kullanici_tablosu.item(i, 0).setData(Qt.UserRole, kullanici)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Kullanıcılar yüklenirken bir sorun oluştu:\n{e}")

    def yeni_kullanici_ekle_dialogu(self):
        dialog = KullaniciDuzenlemeDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            kullanici_bilgileri = dialog.bilgileri_al()
            try:
                kullanici_mantik.kullanici_ekle(
                    kullanici_adi=kullanici_bilgileri['kullanici_adi'],
                    sifre=kullanici_bilgileri['sifre'],
                    tam_ad=kullanici_bilgileri['tam_ad'],
                    rol=kullanici_bilgileri['rol']
                )
                QMessageBox.information(self, "Başarılı", "Kullanıcı başarıyla eklendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except ValueError as e:
                QMessageBox.warning(self, "Eksik Bilgi", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kullanıcı eklenirken bir hata oluştu:\n{e}")

    def secili_kullaniciyi_duzenle_dialogu(self):
        secili_satir = self.kullanici_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen düzenlemek istediğiniz kullanıcıyı seçin.")
            return
        
        # UserRole'dan kullanıcı nesnesini al
        kullanici_nesnesi = self.kullanici_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not kullanici_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili kullanıcı verisi bulunamadı.")
            return

        dialog = KullaniciDuzenlemeDialog(kullanici_verisi=kullanici_nesnesi, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            yeni_bilgiler = dialog.bilgileri_al()
            try:
                # Kullanıcı detaylarını güncelle
                kullanici_mantik.kullanici_detay_guncelle(
                    kullanici_id=kullanici_nesnesi.id,
                    yeni_kullanici_adi=yeni_bilgiler['kullanici_adi'],
                    yeni_tam_ad=yeni_bilgiler['tam_ad'],
                    yeni_rol=yeni_bilgiler['rol']
                )
                # Şifre değiştirildiyse güncelle
                if yeni_bilgiler['sifre']:
                    kullanici_mantik.kullanici_sifre_guncelle(kullanici_nesnesi.id, yeni_bilgiler['sifre'])
                
                # Aktiflik durumunu da güncelle
                if kullanici_nesnesi.aktif != yeni_bilgiler['aktif']:
                    kullanici_mantik.kullanici_durum_degistir(kullanici_nesnesi.id, yeni_bilgiler['aktif'])

                QMessageBox.information(self, "Başarılı", "Kullanıcı başarıyla güncellendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except ValueError as e:
                QMessageBox.warning(self, "Eksik Bilgi", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kullanıcı güncellenirken bir hata oluştu:\n{e}")

    def secili_kullanici_durum_degistir(self):
        secili_satir = self.kullanici_tablosu.currentRow()
        if secili_satir < 0:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen durumunu değiştirmek istediğiniz kullanıcıyı seçin.")
            return
        
        kullanici_nesnesi = self.kullanici_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not kullanici_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili kullanıcı verisi bulunamadı.")
            return

        yeni_durum = not kullanici_nesnesi.aktif
        durum_str = "pasif" if yeni_durum else "aktif"
        cevap = QMessageBox.question(self, "Durum Değiştirme Onayı", 
                                     f"'{kullanici_nesnesi.kullanici_adi}' kullanıcısını {durum_str} yapmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                kullanici_mantik.kullanici_durum_degistir(kullanici_nesnesi.id, yeni_durum)
                QMessageBox.information(self, "Başarılı", "Kullanıcı durumu başarıyla güncellendi.")
                self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Kullanıcı durumu değiştirilirken bir hata oluştu:\n{e}")

# ===== KullaniciEkrani SINIFI BİTİŞİ =====
