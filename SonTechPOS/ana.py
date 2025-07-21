# Dosya Adı: ana.py
# Güncelleme Tarihi / Saati: 16.07.2025 / 11:15
# Yapılan İşlem: Program akışı, yeni giriş ve dashboard ekranlarını kullanacak şekilde güncellendi.

import sys
import os

# Projenin kök dizinini Python'un modül arama yoluna ekler.
proje_kok_dizini = os.path.dirname(os.path.abspath(__file__))
if proje_kok_dizini not in sys.path:
    sys.path.insert(0, proje_kok_dizini)

from PyQt5.QtWidgets import QApplication
from arayuz.ana_pencere import AnaPencere 
from arayuz.giris_ekrani import GirisEkrani 

# ===== ana_fonksiyon BAŞLANGICI =====
def ana_fonksiyon():
    """
    Uygulamayı başlatan ana fonksiyon.
    Önce giriş ekranını gösterir, başarılı giriş sonrası ana pencereyi açar.
    """
    app = QApplication(sys.argv)
    
    # Uygulama genelinde kullanılacak stil ayarları
    app.setStyle("Fusion") 

    # 1. Giriş Ekranını Göster
    giris_penceresi = GirisEkrani()
    
    # exec_() metodu dialoğu modal olarak çalıştırır ve kapanmasını bekler.
    if giris_penceresi.exec_() == GirisEkrani.Accepted:
        # 2. Giriş Başarılıysa Ana Pencereyi Oluştur ve Göster
        aktif_kullanici = giris_penceresi.kullanici_verisi
        pencere = AnaPencere(kullanici=aktif_kullanici)
        pencere.showMaximized() # Pencereyi tam ekran başlat
        
        # Uygulama olay döngüsünü başlat
        sys.exit(app.exec_())
    else:
        # 3. Giriş Başarısız veya İptal Edildiyse Uygulamadan Çık
        sys.exit(0)

# ===== ana_fonksiyon BİTİŞİ =====

if __name__ == "__main__":
    ana_fonksiyon()
