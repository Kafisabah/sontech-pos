# Dosya Adı: moduller/musteri/musteri_ekrani.py
# Güncelleme Tarihi / Saati: 12.07.2025 16:00
# Yapılan İşlem: Müşteri ödeme alma, hesap ekstresi ve kupon görüntüleme butonları ve işlevleri eklendi.

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                             QTableWidgetItem, QHeaderView, QLabel, QDialog,
                             QFormLayout, QLineEdit, QMessageBox, QDoubleSpinBox, QCheckBox,
                             QTextEdit, QDateEdit, QComboBox) # QDateEdit, QComboBox eklendi
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from sqlalchemy.exc import IntegrityError
from decimal import Decimal
import datetime

from moduller.musteri import musteri_mantik
from moduller.kullanici import kullanici_mantik # Ödeme kaydı için kullanıcı ID'si gerekebilir
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_CUSTOMER_ADD, LOG_ACTION_CUSTOMER_UPDATE, LOG_ACTION_CUSTOMER_STATUS_CHANGE, LOG_ACTION_CUSTOMER_PAYMENT # Log sabitleri

# ===== MusteriDuzenlemeDialog SINIFI (GÜNCELLENDİ) =====
class MusteriDuzenlemeDialog(QDialog):
    def __init__(self, musteri_verisi=None, parent=None): # musteri_verisi eklendi
        super().__init__(parent)
        self.musteri_verisi = musteri_verisi # musteri_verisi eklendi
        self.setWindowTitle("Müşteri Düzenle" if musteri_verisi else "Yeni Müşteri Ekle") # Başlık güncellendi
        self.setMinimumWidth(400)
        self._arayuzu_olustur()
        if musteri_verisi: # Eğer düzenleme moduysa formu doldur
            self._formu_doldur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)
        self.ad_input = QLineEdit()
        self.telefon_input = QLineEdit()
        self.adres_input = QLineEdit()
        self.bakiye_input = QDoubleSpinBox()
        self.bakiye_input.setDecimals(2); self.bakiye_input.setMinimum(-999999.99); self.bakiye_input.setMaximum(999999.99); self.bakiye_input.setSuffix(" ₺")
        self.aktif_checkbox = QCheckBox("Aktif")
        self.aktif_checkbox.setChecked(True) # Varsayılan aktif

        self.layout.addRow("Ad Soyad:", self.ad_input)
        self.layout.addRow("Telefon:", self.telefon_input)
        self.layout.addRow("Adres:", self.adres_input)
        self.layout.addRow("Bakiye:", self.bakiye_input)
        self.layout.addRow("Aktif:", self.aktif_checkbox)

        self.kaydet_btn = QPushButton("Kaydet")
        self.iptal_btn = QPushButton("İptal")
        self.kaydet_btn.clicked.connect(self.accept)
        self.iptal_btn.clicked.connect(self.reject)
        buton_layout = QHBoxLayout()
        buton_layout.addStretch()
        buton_layout.addWidget(self.kaydet_btn)
        buton_layout.addWidget(self.iptal_btn)
        self.layout.addRow(buton_layout)

    def _formu_doldur(self): # Yeni metod
        """Mevcut müşteri verilerini forma yükler."""
        self.ad_input.setText(self.musteri_verisi.ad)
        self.telefon_input.setText(self.musteri_verisi.telefon or "")
        self.adres_input.setText(self.musteri_verisi.adres or "")
        self.bakiye_input.setValue(float(self.musteri_verisi.bakiye))
        self.aktif_checkbox.setChecked(self.musteri_verisi.aktif)


    def bilgileri_al(self):
        return {
            "ad": self.ad_input.text().strip(),
            "telefon": self.telefon_input.text().strip() or None,
            "adres": self.adres_input.text().strip() or None,
            "bakiye": Decimal(str(self.bakiye_input.value())),
            "aktif": self.aktif_checkbox.isChecked()
        }

# ===== MusteriOdemeDialog SINIFI BAŞLANGICI (YENİ) =====
class MusteriOdemeDialog(QDialog):
    def __init__(self, musteri_id: int, musteri_adi: str, mevcut_bakiye: Decimal, parent=None):
        super().__init__(parent)
        self.musteri_id = musteri_id
        self.musteri_adi = musteri_adi
        self.mevcut_bakiye = mevcut_bakiye
        self.setWindowTitle(f"{musteri_adi} - Ödeme Al")
        self.setMinimumWidth(350)
        self._arayuzu_olustur()

    def _arayuzu_olustur(self):
        self.layout = QFormLayout(self)
        self.layout.addRow("Müşteri:", QLabel(self.musteri_adi))
        self.layout.addRow("Mevcut Bakiye:", QLabel(f"{self.mevcut_bakiye:.2f} ₺"))

        self.odeme_tutari_input = QDoubleSpinBox()
        self.odeme_tutari_input.setDecimals(2)
        self.odeme_tutari_input.setMinimum(0.01)
        self.odeme_tutari_input.setMaximum(float(self.mevcut_bakiye) if self.mevcut_bakiye > 0 else 999999.99)
        self.odeme_tutari_input.setSuffix(" ₺")
        self.odeme_tutari_input.setValue(float(self.mevcut_bakiye) if self.mevcut_bakiye > 0 else 0.00)

        self.odeme_yontemi_combo = QComboBox()
        self.odeme_yontemi_combo.addItems(["Nakit", "Kredi Kartı"]) # Varsayılan ödeme yöntemleri
        
        self.notlar_input = QLineEdit()

        self.layout.addRow("Ödeme Tutarı:", self.odeme_tutari_input)
        self.layout.addRow("Ödeme Yöntemi:", self.odeme_yontemi_combo)
        self.layout.addRow("Notlar:", self.notlar_input)

        self.kaydet_btn = QPushButton("Ödemeyi Kaydet")
        self.iptal_btn = QPushButton("İptal")
        self.kaydet_btn.clicked.connect(self.accept)
        self.iptal_btn.clicked.connect(self.reject)

        buton_layout = QHBoxLayout()
        buton_layout.addStretch()
        buton_layout.addWidget(self.kaydet_btn)
        buton_layout.addWidget(self.iptal_btn)
        self.layout.addRow(buton_layout)

    def bilgileri_al(self):
        return {
            "musteri_id": self.musteri_id,
            "tutar": Decimal(str(self.odeme_tutari_input.value())),
            "odeme_yontemi": self.odeme_yontemi_combo.currentText(),
            "notlar": self.notlar_input.text().strip() or None
        }
# ===== MusteriOdemeDialog SINIFI BİTİŞİ =====

# ===== MusteriHesapEkstresiDialog SINIFI BAŞLANGICI (YENİ) =====
class MusteriHesapEkstresiDialog(QDialog):
    def __init__(self, musteri_id: int, musteri_adi: str, parent=None):
        super().__init__(parent)
        self.musteri_id = musteri_id
        self.musteri_adi = musteri_adi
        self.setWindowTitle(f"{musteri_adi} - Hesap Ekstresi")
        self.setMinimumWidth(800)
        self.setMinimumHeight(500)
        self._arayuzu_olustur()
        self.ekstreyi_goster()

    def _arayuzu_olustur(self):
        self.main_layout = QVBoxLayout(self)
        control_layout = QHBoxLayout()

        self.baslangic_tarih_label = QLabel("Başlangıç:")
        self.baslangic_tarih_input = QDateEdit(calendarPopup=True)
        self.baslangic_tarih_input.setDateTime(self.baslangic_tarih_input.minimumDateTime())
        
        self.bitis_tarih_label = QLabel("Bitiş:")
        self.bitis_tarih_input = QDateEdit(calendarPopup=True)
        self.bitis_tarih_input.setDateTime(self.bitis_tarih_input.minimumDateTime())

        self.raporu_getir_btn = QPushButton("Ekstreyi Getir")
        self.raporu_getir_btn.clicked.connect(self.ekstreyi_goster)

        control_layout.addWidget(self.baslangic_tarih_label)
        control_layout.addWidget(self.baslangic_tarih_input)
        control_layout.addWidget(self.bitis_tarih_label)
        control_layout.addWidget(self.bitis_tarih_input)
        control_layout.addStretch()
        control_layout.addWidget(self.raporu_getir_btn)
        self.main_layout.addLayout(control_layout)

        self.ekstre_tablosu = QTableWidget()
        self.ekstre_tablosu.setColumnCount(5)
        self.ekstre_tablosu.setHorizontalHeaderLabels(["Tarih", "İşlem Türü", "Açıklama", "Borç (₺)", "Alacak (₺)"])
        self.ekstre_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.ekstre_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.main_layout.addWidget(self.ekstre_tablosu)

        self.guncel_bakiye_label = QLabel("Güncel Bakiye: 0.00 ₺")
        self.guncel_bakiye_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.main_layout.addWidget(self.guncel_bakiye_label)

    def ekstreyi_goster(self):
        baslangic_tarihi = self.baslangic_tarih_input.date().toPyDate() if self.baslangic_tarih_input.date().isValid() else None
        bitis_tarihi = self.bitis_tarih_input.date().toPyDate() if self.bitis_tarih_input.date().isValid() else None

        try:
            ledger_entries = musteri_mantik.musteri_hesap_ekstresi_getir(self.musteri_id, baslangic_tarihi, bitis_tarihi)
            current_balance = musteri_mantik.musteri_bakiye_getir(self.musteri_id)

            self.ekstre_tablosu.setRowCount(len(ledger_entries))
            for satir_index, entry in enumerate(ledger_entries):
                tarih_str = entry['tarih'].strftime('%d.%m.%Y %H:%M:%S') if entry['tarih'] else 'N/A'
                self.ekstre_tablosu.setItem(satir_index, 0, QTableWidgetItem(tarih_str))
                self.ekstre_tablosu.setItem(satir_index, 1, QTableWidgetItem(entry['tip']))
                self.ekstre_tablosu.setItem(satir_index, 2, QTableWidgetItem(entry['aciklama']))
                
                borc_str = f"{entry['borc']:.2f} ₺" if entry['borc'] is not None else ""
                alacak_str = f"{entry['alacak']:.2f} ₺" if entry['alacak'] is not None else ""
                
                borc_item = QTableWidgetItem(borc_str)
                if entry['borc'] is not None and entry['borc'] > 0: borc_item.setForeground(Qt.red)
                self.ekstre_tablosu.setItem(satir_index, 3, borc_item)

                alacak_item = QTableWidgetItem(alacak_str)
                if entry['alacak'] is not None and entry['alacak'] > 0: alacak_item.setForeground(Qt.darkGreen)
                self.ekstre_tablosu.setItem(satir_index, 4, alacak_item)
            
            if current_balance is not None:
                bakiye_style = "color: red;" if current_balance > 0 else "color: green;" if current_balance < 0 else ""
                self.guncel_bakiye_label.setText(f"Güncel Bakiye: <span style='{bakiye_style}'>{current_balance:.2f} ₺</span>")
            else:
                self.guncel_bakiye_label.setText("Güncel Bakiye: N/A")

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Hesap ekstresi oluşturulurken bir sorun oluştu:\n{e}")
# ===== MusteriHesapEkstresiDialog SINIFI BİTİŞİ =====

# ===== MusteriKuponlariDialog SINIFI BAŞLANGICI (YENİ) =====
class MusteriKuponlariDialog(QDialog):
    def __init__(self, musteri_id: int, musteri_adi: str, parent=None):
        super().__init__(parent)
        self.musteri_id = musteri_id
        self.musteri_adi = musteri_adi
        self.setWindowTitle(f"{musteri_adi} - Kuponları")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self._arayuzu_olustur()
        self.kuponlari_goster()

    def _arayuzu_olustur(self):
        self.main_layout = QVBoxLayout(self)
        control_layout = QHBoxLayout()

        self.yenile_btn = QPushButton("Yenile")
        self.yenile_btn.clicked.connect(self.kuponlari_goster)

        control_layout.addStretch()
        control_layout.addWidget(self.yenile_btn)
        self.main_layout.addLayout(control_layout)

        self.kupon_tablosu = QTableWidget()
        self.kupon_tablosu.setColumnCount(5)
        self.kupon_tablosu.setHorizontalHeaderLabels(["ID", "Kupon Kodu", "Açıklama", "İndirim", "Son Geçerlilik"])
        self.kupon_tablosu.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.kupon_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        self.main_layout.addWidget(self.kupon_tablosu)

    def kuponlari_goster(self):
        try:
            kuponlar = musteri_mantik.musteri_kuponlarini_getir(self.musteri_id)
            self.kupon_tablosu.setRowCount(len(kuponlar))
            for satir_index, kupon in enumerate(kuponlar):
                self.kupon_tablosu.setItem(satir_index, 0, QTableWidgetItem(str(kupon.id)))
                self.kupon_tablosu.setItem(satir_index, 1, QTableWidgetItem(kupon.kupon.kupon_kodu if kupon.kupon else "N/A"))
                self.kupon_tablosu.setItem(satir_index, 2, QTableWidgetItem(kupon.kupon.aciklama if kupon.kupon else "N/A"))
                
                indirim_str = ""
                if kupon.kupon and kupon.kupon.indirim_tipi == 'yuzde':
                    indirim_str = f"%{kupon.kupon.indirim_degeri:.0f}"
                elif kupon.kupon and kupon.kupon.indirim_tipi == 'tutar':
                    indirim_str = f"{kupon.kupon.indirim_degeri:.2f} ₺"
                self.kupon_tablosu.setItem(satir_index, 3, QTableWidgetItem(indirim_str))
                
                skt_str = kupon.son_kullanma_tarihi.strftime('%Y-%m-%d') if kupon.son_kullanma_tarihi else "Süresiz"
                self.kupon_tablosu.setItem(satir_index, 4, QTableWidgetItem(skt_str))

        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Müşteri kuponları yüklenirken bir sorun oluştu:\n{e}")
# ===== MusteriKuponlariDialog SINIFI BİTİŞİ =====


# ===== MusteriEkrani SINIFI BAŞLANGICI (GÜNCELLENDİ) =====
class MusteriEkrani(QWidget):
    # Yeni Sinyal: Müşteri seçildiğinde müşteri verisini gönderir.
    musteri_secildi = pyqtSignal(dict)

    def __init__(self, secim_modu=False, parent=None):
        super().__init__(parent)
        self.secim_modu = secim_modu
        self._arayuzu_olustur()
        self.yenile()

    def _arayuzu_olustur(self):
        self.ana_layout = QVBoxLayout(self)
        ust_panel_layout = QHBoxLayout()
        baslik = QLabel("Müşteri Yönetimi")
        baslik.setStyleSheet("font-size: 24px; font-weight: bold;")
        
        self.yeni_musteri_btn = QPushButton("Yeni Müşteri Ekle")
        self.yeni_musteri_btn.clicked.connect(self.yeni_musteri_ekle_dialogu)

        self.duzenle_btn = QPushButton("Seçili Müşteriyi Düzenle")
        self.duzenle_btn.clicked.connect(self.secili_musteriyi_duzenle_dialogu)

        self.durum_degistir_btn = QPushButton("Durumu Değiştir")
        self.durum_degistir_btn.clicked.connect(self.secili_musteri_durum_degistir)

        self.odeme_al_btn = QPushButton("Ödeme Al") # Yeni buton
        self.odeme_al_btn.clicked.connect(self.musteri_odeme_al_dialogu) # Yeni işlev

        self.hesap_ekstresi_btn = QPushButton("Hesap Ekstresi") # Yeni buton
        self.hesap_ekstresi_btn.clicked.connect(self.musteri_hesap_ekstresi_goster) # Yeni işlev

        self.kuponlari_gor_btn = QPushButton("Kuponları Görüntüle") # Yeni buton
        self.kuponlari_gor_btn.clicked.connect(self.musteri_kuponlari_goster) # Yeni işlev


        ust_panel_layout.addWidget(baslik)
        ust_panel_layout.addStretch()
        ust_panel_layout.addWidget(self.yeni_musteri_btn)
        
        # Eğer seçim modunda değilse düzenleme ve durum değiştirme butonlarını ekle
        if not self.secim_modu:
            ust_panel_layout.addWidget(self.duzenle_btn)
            ust_panel_layout.addWidget(self.durum_degistir_btn)
            ust_panel_layout.addWidget(self.odeme_al_btn) # Butonu ekle
            ust_panel_layout.addWidget(self.hesap_ekstresi_btn) # Butonu ekle
            ust_panel_layout.addWidget(self.kuponlari_gor_btn) # Butonu ekle
        
        # Eğer seçim modundaysa, "Müşteri Seç" butonunu ekle
        if self.secim_modu:
            self.sec_btn = QPushButton("Müşteri Seç")
            self.sec_btn.setStyleSheet("background-color: #28a745; color: white;")
            self.sec_btn.clicked.connect(self._secimi_onayla)
            ust_panel_layout.addWidget(self.sec_btn)

        self.ana_layout.addLayout(ust_panel_layout)

        self.musteri_tablosu = QTableWidget()
        self.musteri_tablosu.setColumnCount(5)
        self.musteri_tablosu.setHorizontalHeaderLabels(["ID", "Ad Soyad", "Telefon", "Bakiye", "Aktif"])
        self.musteri_tablosu.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.musteri_tablosu.setSelectionBehavior(QTableWidget.SelectRows)
        self.musteri_tablosu.setEditTriggers(QTableWidget.NoEditTriggers)
        # Eğer seçim modundaysa, çift tıklama olayını bağla
        if self.secim_modu:
            self.musteri_tablosu.doubleClicked.connect(self._secimi_onayla)
            
        self.ana_layout.addWidget(self.musteri_tablosu)

    def yenile(self):
        try:
            musteriler = musteri_mantik.musterileri_getir(include_inactive=True)
            self.musteri_tablosu.setRowCount(len(musteriler))
            for satir_index, musteri in enumerate(musteriler):
                self.musteri_tablosu.setItem(satir_index, 0, QTableWidgetItem(str(musteri.id)))
                self.musteri_tablosu.setItem(satir_index, 1, QTableWidgetItem(musteri.ad))
                self.musteri_tablosu.setItem(satir_index, 2, QTableWidgetItem(musteri.telefon or "N/A"))
                self.musteri_tablosu.setItem(satir_index, 3, QTableWidgetItem(f"{musteri.bakiye:.2f} ₺"))
                aktif_durum_str = "Evet" if musteri.aktif else "Hayır"
                self.musteri_tablosu.setItem(satir_index, 4, QTableWidgetItem(aktif_durum_str))
                self.musteri_tablosu.item(satir_index, 0).setData(Qt.UserRole, musteri)
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Müşteriler yüklenirken bir sorun oluştu:\n{e}")

    def yeni_musteri_ekle_dialogu(self):
        dialog = MusteriDuzenlemeDialog(parent=self)
        if dialog.exec_() == QDialog.Accepted:
            musteri_bilgileri = dialog.bilgileri_al()
            if not musteri_bilgileri['ad']:
                QMessageBox.warning(self, "Eksik Bilgi", "Müşteri Adı alanı zorunludur.")
                return
            try:
                musteri_mantik.yeni_musteri_ekle(
                    ad=musteri_bilgileri['ad'],
                    telefon=musteri_bilgileri['telefon'],
                    adres=musteri_bilgileri['adres']
                )
                QMessageBox.information(self, "Başarılı", "Müşteri başarıyla eklendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Müşteri eklenirken bir hata oluştu:\n{e}")

    def secili_musteriyi_duzenle_dialogu(self):
        secili_satir = self._get_secili_musteri_nesnesi()
        if not secili_satir: return

        musteri_nesnesi = secili_satir
        dialog = MusteriDuzenlemeDialog(musteri_verisi=musteri_nesnesi, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            yeni_bilgiler = dialog.bilgileri_al()
            try:
                musteri_mantik.musteri_guncelle(
                    musteri_id=musteri_nesnesi.id,
                    yeni_ad=yeni_bilgiler['ad'],
                    yeni_telefon=yeni_bilgiler['telefon'],
                    yeni_adres=yeni_bilgiler['adres'],
                    yeni_bakiye=yeni_bilgiler['bakiye']
                )
                if musteri_nesnesi.aktif != yeni_bilgiler['aktif']:
                    musteri_mantik.musteri_durum_degistir(musteri_nesnesi.id, yeni_bilgiler['aktif'])

                QMessageBox.information(self, "Başarılı", "Müşteri başarıyla güncellendi.")
                self.yenile()
            except IntegrityError as e:
                QMessageBox.warning(self, "Hata", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Müşteri güncellenirken bir hata oluştu:\n{e}")

    def secili_musteri_durum_degistir(self):
        secili_satir = self._get_secili_musteri_nesnesi()
        if not secili_satir: return

        musteri_nesnesi = secili_satir
        yeni_durum = not musteri_nesnesi.aktif
        durum_str = "pasif" if yeni_durum else "aktif"
        cevap = QMessageBox.question(self, "Durum Değiştirme Onayı", 
                                     f"'{musteri_nesnesi.ad}' müşterisini {durum_str} yapmak istediğinizden emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if cevap == QMessageBox.Yes:
            try:
                musteri_mantik.musteri_durum_degistir(musteri_nesnesi.id, yeni_durum)
                QMessageBox.information(self, "Başarılı", "Müşteri durumu başarıyla güncellendi.")
                self.yenile()
            except Exception as e:
                QMessageBox.critical(self, "Hata", f"Müşteri durumu değiştirilirken bir hata oluştu:\n{e}")

    def musteri_odeme_al_dialogu(self): # Yeni metod
        secili_musteri = self._get_secili_musteri_nesnesi()
        if not secili_musteri: return

        try:
            mevcut_bakiye = musteri_mantik.musteri_bakiye_getir(secili_musteri.id)
            if mevcut_bakiye is None:
                QMessageBox.warning(self, "Hata", "Müşteri bakiyesi alınamadı.")
                return
            elif mevcut_bakiye <= Decimal('0.00'):
                QMessageBox.information(self, "Bilgi", "Bu müşterinin borcu bulunmuyor.")
                return

            dialog = MusteriOdemeDialog(secili_musteri.id, secili_musteri.ad, mevcut_bakiye, parent=self)
            if dialog.exec_() == QDialog.Accepted:
                odeme_bilgileri = dialog.bilgileri_al()
                # Ödeme kaydını yap (aktif kullanıcı ID'si gerekebilir, şimdilik sabit 1)
                musteri_mantik.musteri_odeme_kaydet(
                    musteri_id=odeme_bilgileri['musteri_id'],
                    tutar=odeme_bilgileri['tutar'],
                    odeme_yontemi=odeme_bilgileri['odeme_yontemi'],
                    notlar=odeme_bilgileri['notlar'],
                    vardiya_id=1 # Varsayılan vardiya ID'si 1, gerçekte aktif vardiya ID'si olmalı
                )
                QMessageBox.information(self, "Başarılı", "Ödeme başarıyla kaydedildi.")
                self.yenile() # Tabloyu ve bakiye bilgisini yenile
        except ValueError as e:
            QMessageBox.warning(self, "Hata", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Müşteri ödemesi alınırken bir sorun oluştu:\n{e}")

    def musteri_hesap_ekstresi_goster(self): # Yeni metod
        secili_musteri = self._get_secili_musteri_nesnesi()
        if not secili_musteri: return

        dialog = MusteriHesapEkstresiDialog(secili_musteri.id, secili_musteri.ad, parent=self)
        dialog.exec_()

    def musteri_kuponlari_goster(self): # Yeni metod
        secili_musteri = self._get_secili_musteri_nesnesi()
        if not secili_musteri: return

        dialog = MusteriKuponlariDialog(secili_musteri.id, secili_musteri.ad, parent=self)
        dialog.exec_()

    def _get_secili_musteri_nesnesi(self): # Yardımcı metod
        secili_satirlar = self.musteri_tablosu.selectedItems()
        if not secili_satirlar:
            QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen bir müşteri seçin.")
            return None
        
        secili_satir = secili_satirlar[0].row()
        musteri_nesnesi = self.musteri_tablosu.item(secili_satir, 0).data(Qt.UserRole)
        if not musteri_nesnesi:
            QMessageBox.warning(self, "Hata", "Seçili müşteri verisi bulunamadı.")
            return None
        return musteri_nesnesi

    def _secimi_onayla(self, item=None): # item parametresi eklendi (çift tıklama için)
        """Müşteri seçme modunda seçili müşterinin verisini sinyal ile gönderir."""
        if self.secim_modu:
            if item: # Eğer çift tıklama ile geldiyse item dolu olacak
                musteri_nesnesi = item.data(Qt.UserRole)
            else: # Buton ile geldiyse seçili satırdan al
                secili_satir = self.musteri_tablosu.currentRow()
                if secili_satir < 0:
                    QMessageBox.warning(self, "Seçim Yapılmadı", "Lütfen listeden bir müşteri seçin.")
                    return
                musteri_nesnesi = self.musteri_tablosu.item(secili_satir, 0).data(Qt.UserRole)

            if not musteri_nesnesi:
                QMessageBox.warning(self, "Hata", "Seçili müşteri verisi bulunamadı.")
                return
            
            musteri_verisi = {
                "id": musteri_nesnesi.id,
                "ad": musteri_nesnesi.ad,
                "telefon": musteri_nesnesi.telefon,
                "bakiye": musteri_nesnesi.bakiye
            }
            
            print(f"DEBUG: Müşteri seçildi: {musteri_verisi}")
            self.musteri_secildi.emit(musteri_verisi)
            
            if isinstance(self.parent(), QDialog):
                self.parent().accept()
# ===== MusteriEkrani SINIFI BİTİŞİ =====
