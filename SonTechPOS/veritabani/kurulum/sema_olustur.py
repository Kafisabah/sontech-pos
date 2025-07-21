# Dosya Adı: veritabani/kurulum/sema_olustur.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 13:00
# Yapılan İşlem: 'pin' kolonu yoksa ALTER TABLE ile ekleyen ve PIN atayan mantık eklendi.

import sys
import os
import pymysql
import bcrypt
from sqlalchemy import text # Ham SQL sorguları için

# Proje kök dizinini Python'un modül arama yoluna ekler.
proje_kok_dizini = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if proje_kok_dizini not in sys.path:
    sys.path.insert(0, proje_kok_dizini)

from cekirdek.ayarlar import ayarlar
from cekirdek.veritabani_yonetimi import motor, Temel, OturumYerel, Sube, Kullanici, Marka, Kategori

# ===== veritabani_olustur_ve_sec FONKSİYONU BAŞLANGICI =====
def veritabani_olustur_ve_sec():
    try:
        baglanti = pymysql.connect(
            host=ayarlar.getir('veritabani', 'host'),
            user=ayarlar.getir('veritabani', 'kullanici'),
            password=ayarlar.getir('veritabani', 'sifre'),
            port=int(ayarlar.getir('veritabani', 'port', 3306)),
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor
        )
        print("MySQL sunucusuna başarıyla bağlanıldı.")
        veritabani_adi = ayarlar.getir('veritabani', 'veritabani_adi')
        with baglanti.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {veritabani_adi} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"'{veritabani_adi}' veritabanı başarıyla oluşturuldu veya zaten mevcut.")
        baglanti.close()
        return True
    except Exception as e:
        print(f"HATA: Veritabanı oluşturulurken beklenmedik bir sorun oluştu: {e}")
        return False
# ===== veritabani_olustur_ve_sec FONKSİYONU BİTİŞİ =====

# ===== tablo_olustur FONKSİYONU BAŞLANGICI =====
def tablo_olustur():
    try:
        print("Veritabanı tabloları oluşturuluyor...")
        Temel.metadata.create_all(bind=motor)
        print("Tablolar başarıyla oluşturuldu veya zaten mevcut.")
    except Exception as e:
        print(f"HATA: Tablolar oluşturulurken bir sorun oluştu: {e}")
# ===== tablo_olustur FONKSİYONU BİTİŞİ =====

# ===== pin_kolonunu_ekle FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def pin_kolonunu_ekle():
    """'kullanicilar' tablosunda 'pin' kolonu yoksa ekler."""
    try:
        # SQLAlchemy yerine ham pymysql kullanarak kontrol yapalım
        baglanti = pymysql.connect(
            host=ayarlar.getir('veritabani', 'host'),
            user=ayarlar.getir('veritabani', 'kullanici'),
            password=ayarlar.getir('veritabani', 'sifre'),
            port=int(ayarlar.getir('veritabani', 'port', 3306)),
            database=ayarlar.getir('veritabani', 'veritabani_adi'),
            charset="utf8mb4"
        )
        with baglanti.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM kullanicilar LIKE 'pin'")
            sonuc = cursor.fetchone()
            if sonuc:
                print("'pin' kolonu zaten mevcut.")
            else:
                print("'pin' kolonu bulunamadı, ekleniyor...")
                cursor.execute("ALTER TABLE kullanicilar ADD COLUMN pin VARCHAR(255) UNIQUE AFTER sifre_hash")
                baglanti.commit()
                print("'pin' kolonu başarıyla eklendi.")
    except Exception as e:
        print(f"HATA: 'pin' kolonu kontrol edilirken/eklenirken bir sorun oluştu: {e}")
    finally:
        if 'baglanti' in locals() and baglanti.open:
            baglanti.close()
# ===== pin_kolonunu_ekle FONKSİYONU BİTİŞİ =====

# ===== varsayilan_yonetici_kullanici_olustur FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def varsayilan_yonetici_kullanici_olustur():
    oturum = OturumYerel()
    try:
        varsayilan_kullanici_adi = "admin"
        kullanici = oturum.query(Kullanici).filter(Kullanici.kullanici_adi == varsayilan_kullanici_adi).first()
        
        pin_hash = bcrypt.hashpw("1234".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        if not kullanici:
            sifre_hash = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            yeni_kullanici = Kullanici(
                kullanici_adi=varsayilan_kullanici_adi,
                sifre_hash=sifre_hash,
                pin=pin_hash,
                tam_ad="Sistem Yöneticisi",
                rol="admin",
                aktif=True
            )
            oturum.add(yeni_kullanici)
            print(f"Varsayılan yönetici '{varsayilan_kullanici_adi}' oluşturuldu. Şifre: admin123, PIN: 1234")
        else:
            print(f"Varsayılan yönetici '{varsayilan_kullanici_adi}' zaten mevcut.")
            if not kullanici.pin or not bcrypt.checkpw("1234".encode('utf-8'), kullanici.pin.encode('utf-8')):
                kullanici.pin = pin_hash
                print(f"Mevcut '{varsayilan_kullanici_adi}' kullanıcısının PIN'i '1234' olarak ayarlandı/güncellendi.")
        
        oturum.commit()
    except Exception as e:
        print(f"HATA: Varsayılan yönetici oluşturulurken/güncellenirken bir sorun oluştu: {e}")
        oturum.rollback()
    finally:
        oturum.close()
# ===== varsayilan_yonetici_kullanici_olustur FONKSİYONU BİTİŞİ =====

def varsayilan_sube_olustur():
    oturum = OturumYerel()
    try:
        if not oturum.query(Sube).filter(Sube.ad == "Merkez Şube").first():
            oturum.add(Sube(ad="Merkez Şube", adres="Merkez"))
            oturum.commit()
    finally:
        oturum.close()

def varsayilan_marka_ve_kategori_olustur():
    oturum = OturumYerel()
    try:
        if not oturum.query(Marka).filter(Marka.ad == "Genel Marka").first():
            oturum.add(Marka(ad="Genel Marka", aktif=True))
        if not oturum.query(Kategori).filter(Kategori.ad == "Genel Kategori").first():
            oturum.add(Kategori(ad="Genel Kategori", aktif=True))
        oturum.commit()
    finally:
        oturum.close()

if __name__ == "__main__":
    if veritabani_olustur_ve_sec():
        tablo_olustur()
        pin_kolonunu_ekle()
        varsayilan_sube_olustur()
        varsayilan_yonetici_kullanici_olustur()
        varsayilan_marka_ve_kategori_olustur()
