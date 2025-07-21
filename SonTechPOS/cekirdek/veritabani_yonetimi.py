# Dosya Adı: cekirdek/veritabani_yonetimi.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 10:15
# Yapılan İşlem: Kullanici modeline PIN ile giriş için 'pin' alanı eklendi.

from sqlalchemy import create_engine, Column, Integer, String, Boolean, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
import datetime

from cekirdek.ayarlar import ayarlar

# ===== VERITABANI BAĞLANTI BİLGİLERİ =====
kullanici_db = ayarlar.getir('veritabani', 'kullanici', 'root')
sifre = ayarlar.getir('veritabani', 'sifre', '')
host = ayarlar.getir('veritabani', 'host', 'localhost')
port = int(ayarlar.getir('veritabani', 'port', 3306))
veritabani_adi = ayarlar.getir('veritabani', 'veritabani_adi', 'sontech_pos_db')
VERITABANI_URL = f"mysql+pymysql://{kullanici_db}:{sifre}@{host}:{port}/{veritabani_adi}?charset=utf8mb4"
motor = create_engine(VERITABANI_URL)
OturumYerel = sessionmaker(autocommit=False, autoflush=False, bind=motor)
Temel = declarative_base()

# ===== VERITABANI MODELLERİ (TABLOLAR) =====

class Kullanici(Temel):
    __tablename__ = 'kullanicilar'
    id = Column(Integer, primary_key=True, index=True)
    kullanici_adi = Column(String(50), unique=True, nullable=False)
    sifre_hash = Column(String(255), nullable=False)
    pin = Column(String(255), unique=True, nullable=True, index=True) # YENİ ALAN
    tam_ad = Column(String(255), nullable=True)
    rol = Column(String(50), default='kullanici')
    aktif = Column(Boolean, default=True)
    satislar = relationship("Satis", back_populates="kullanici")
    vardiyalar = relationship("Vardiya", back_populates="kullanici")
    loglar = relationship("LogKaydi", back_populates="kullanici")

class Marka(Temel):
    __tablename__ = 'markalar'
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), unique=True, nullable=False)
    aktif = Column(Boolean, default=True)
    urunler = relationship("Urun", back_populates="marka")

class Kategori(Temel):
    __tablename__ = 'kategoriler'
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), unique=True, nullable=False)
    aciklama = Column(Text, nullable=True)
    skt_zorunlu = Column(Boolean, default=False)
    aktif = Column(Boolean, default=True)
    urunler = relationship("Urun", back_populates="kategori")

class Promosyon(Temel):
    __tablename__ = 'promosyonlar'
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(255), unique=True, nullable=False)
    aciklama = Column(Text, nullable=True)
    promosyon_tipi = Column(String(50), nullable=False)
    urun_id = Column(Integer, ForeignKey('urunler.id'), nullable=False)
    urun = relationship("Urun", foreign_keys=[urun_id], back_populates="promosyonlar")
    gerekli_miktar = Column(Integer, default=0)
    indirim_tutari = Column(Numeric(10, 2), default=0.00)
    gerekli_bogo_miktar = Column(Integer, default=0)
    bedava_miktar = Column(Integer, default=0)
    bedava_urun_id = Column(Integer, ForeignKey('urunler.id'), nullable=True)
    bedava_urun = relationship("Urun", foreign_keys=[bedava_urun_id], back_populates="bedava_promosyonlar")
    baslangic_tarihi = Column(DateTime, nullable=True)
    bitis_tarihi = Column(DateTime, nullable=True)
    aktif = Column(Boolean, default=True)
    uygulanan_satislar = relationship("Satis", foreign_keys="Satis.uygulanan_promosyon_id", back_populates="uygulanan_promosyon")

class Urun(Temel):
    __tablename__ = 'urunler'
    id = Column(Integer, primary_key=True, index=True)
    barkod = Column(String(100), unique=True, nullable=False, index=True)
    ad = Column(String(255), nullable=False)
    birim = Column(String(20), nullable=False, default='Adet')
    aktif = Column(Boolean, default=True)
    marka_id = Column(Integer, ForeignKey('markalar.id'))
    marka = relationship("Marka", back_populates="urunler")
    kategori_id = Column(Integer, ForeignKey('kategoriler.id'))
    kategori = relationship("Kategori", back_populates="urunler")
    alis_fiyati = Column(Numeric(10, 2), default=0.00)
    satis_fiyati = Column(Numeric(10, 2), default=0.00)
    kdv_orani = Column(Numeric(5, 2), default=10.00)
    min_stok_seviyesi = Column(Numeric(10, 2), default=0.00)
    onceki_satis_fiyati = Column(Numeric(10, 2), nullable=True)
    son_guncelleme_tarihi = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    stoklar = relationship("Stok", back_populates="urun", cascade="all, delete-orphan")
    fiyatlar = relationship("Fiyat", back_populates="urun", cascade="all, delete-orphan")
    satis_kalemleri = relationship("SatisKalemi", back_populates="urun")
    alis_kalemleri = relationship("AlisKalemi", back_populates="urun")
    promosyonlar = relationship("Promosyon", foreign_keys="Promosyon.urun_id", back_populates="urun")
    bedava_promosyonlar = relationship("Promosyon", foreign_keys="Promosyon.bedava_urun_id", back_populates="bedava_urun")

class Sube(Temel):
    __tablename__ = 'subeler'
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(100), unique=True, nullable=False)
    adres = Column(String(255))
    aktif = Column(Boolean, default=True)
    stoklar = relationship("Stok", back_populates="sube")
    fiyatlar = relationship("Fiyat", back_populates="sube")
    satislar = relationship("Satis", back_populates="sube")

class Stok(Temel):
    __tablename__ = 'stoklar'
    id = Column(Integer, primary_key=True, index=True)
    miktar = Column(Numeric(10, 2), default=0.00)
    min_stok_seviyesi = Column(Numeric(10, 2), default=0.00)
    urun_id = Column(Integer, ForeignKey('urunler.id'), nullable=False)
    urun = relationship("Urun", back_populates="stoklar")
    sube_id = Column(Integer, ForeignKey('subeler.id'), nullable=False)
    sube = relationship("Sube", back_populates="stoklar")
    son_guncelleme = Column(DateTime, default=datetime.datetime.utcnow)

class Fiyat(Temel):
    __tablename__ = 'fiyatlar'
    id = Column(Integer, primary_key=True, index=True)
    alis_fiyati = Column(Numeric(10, 2), default=0.00)
    satis_fiyati = Column(Numeric(10, 2), default=0.00)
    kdv_orani = Column(Numeric(5, 2), default=10.00)
    urun_id = Column(Integer, ForeignKey('urunler.id'), nullable=False)
    urun = relationship("Urun", back_populates="fiyatlar")
    sube_id = Column(Integer, ForeignKey('subeler.id'), nullable=False)
    sube = relationship("Sube", back_populates="fiyatlar")

class Musteri(Temel):
    __tablename__ = 'musteriler'
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(255), nullable=False)
    telefon = Column(String(20), unique=True, nullable=True)
    adres = Column(String(255), nullable=True)
    aktif = Column(Boolean, default=True)
    bakiye = Column(Numeric(10, 2), default=0.00)
    sadakat_puani = Column(Integer, default=0)
    satislar = relationship("Satis", back_populates="musteri")
    musteri_odemeleri = relationship("MusteriOdeme", back_populates="musteri")
    musteri_kuponlari = relationship("MusteriKupon", back_populates="musteri")

class Satis(Temel):
    __tablename__ = 'satislar'
    id = Column(Integer, primary_key=True, index=True)
    toplam_tutar = Column(Numeric(10, 2), nullable=False)
    indirim_tutari = Column(Numeric(10, 2), default=0.00)
    promosyon_indirim_tutari = Column(Numeric(10, 2), default=0.00)
    uygulanan_kupon_id = Column(Integer, ForeignKey('musteri_kuponlari.id'), nullable=True)
    uygulanan_promosyon_id = Column(Integer, ForeignKey('promosyonlar.id'), nullable=True)
    durum = Column(String(50), default='tamamlandi')
    tarih = Column(DateTime, default=datetime.datetime.utcnow)
    sube_id = Column(Integer, ForeignKey('subeler.id'))
    sube = relationship("Sube", back_populates="satislar")
    musteri_id = Column(Integer, ForeignKey('musteriler.id'), nullable=True)
    musteri = relationship("Musteri", back_populates="satislar")
    kullanici_id = Column(Integer, ForeignKey('kullanicilar.id'), nullable=True)
    kullanici = relationship("Kullanici", back_populates="satislar")
    vardiya_id = Column(Integer, ForeignKey('vardiyalar.id'), nullable=True)
    vardiya = relationship("Vardiya", back_populates="satislar")
    kalemler = relationship("SatisKalemi", back_populates="satis", cascade="all, delete-orphan")
    odemeler = relationship("Odeme", back_populates="satis", cascade="all, delete-orphan")
    iade_kayitlari = relationship("Iade", back_populates="orijinal_satis")
    uygulanan_promosyon = relationship("Promosyon", foreign_keys="Satis.uygulanan_promosyon_id", back_populates="uygulanan_satislar")

class SatisKalemi(Temel):
    __tablename__ = 'satis_kalemleri'
    id = Column(Integer, primary_key=True, index=True)
    miktar = Column(Numeric(10, 2), nullable=False)
    birim_fiyat = Column(Numeric(10, 2), nullable=False)
    toplam_fiyat = Column(Numeric(10, 2), nullable=False)
    satis_id = Column(Integer, ForeignKey('satislar.id'))
    satis = relationship("Satis", back_populates="kalemler")
    urun_id = Column(Integer, ForeignKey('urunler.id'))
    urun = relationship("Urun", back_populates="satis_kalemleri")
    indirim_tutari = Column(Numeric(10, 2), default=0.00)

class Odeme(Temel):
    __tablename__ = 'odemeler'
    id = Column(Integer, primary_key=True, index=True)
    satis_id = Column(Integer, ForeignKey('satislar.id'))
    yontem = Column(String(50), nullable=False)
    tutar = Column(Numeric(10, 2), nullable=False)
    durum = Column(String(50), default='tamamlandi')
    satis = relationship("Satis", back_populates="odemeler")

class Tedarikci(Temel):
    __tablename__ = 'tedarikciler'
    id = Column(Integer, primary_key=True, index=True)
    ad = Column(String(255), unique=True, nullable=False)
    iletisim_yetkilisi = Column(String(255), nullable=True)
    telefon = Column(String(20), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    adres = Column(String(255), nullable=True)
    aktif = Column(Boolean, default=True)
    alislar = relationship("Alis", back_populates="tedarikci")

class Vardiya(Temel):
    __tablename__ = 'vardiyalar'
    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey('kullanicilar.id'), nullable=False)
    kullanici = relationship("Kullanici", back_populates="vardiyalar")
    baslangic_zamani = Column(DateTime, default=datetime.datetime.utcnow)
    bitis_zamani = Column(DateTime, nullable=True)
    baslangic_kasa_nakiti = Column(Numeric(10, 2), default=0.00)
    bitis_kasa_nakiti = Column(Numeric(10, 2), nullable=True)
    toplam_satis_cirosu = Column(Numeric(10, 2), nullable=True)
    nakit_satislar = Column(Numeric(10, 2), nullable=True)
    kart_satislar = Column(Numeric(10, 2), nullable=True)
    veresiye_satislar = Column(Numeric(10, 2), nullable=True)
    alinan_nakit_odemeler = Column(Numeric(10, 2), nullable=True)
    alinan_kart_odemeler = Column(Numeric(10, 2), nullable=True)
    hesaplanan_fark = Column(Numeric(10, 2), nullable=True)
    notlar = Column(Text, nullable=True)
    aktif = Column(Boolean, default=True)
    satislar = relationship("Satis", back_populates="vardiya")
    musteri_odemeleri = relationship("MusteriOdeme", back_populates="vardiya")

class Kupon(Temel):
    __tablename__ = 'kuponlar'
    id = Column(Integer, primary_key=True, index=True)
    kupon_kodu = Column(String(50), unique=True, nullable=False)
    aciklama = Column(Text, nullable=True)
    indirim_tipi = Column(String(20), nullable=False)
    indirim_degeri = Column(Numeric(10, 2), nullable=False)
    min_satis_tutari = Column(Numeric(10, 2), default=0.00)
    aktif = Column(Boolean, default=True)
    musteri_kuponlari = relationship("MusteriKupon", back_populates="kupon")

class MusteriKupon(Temel):
    __tablename__ = 'musteri_kuponlari'
    id = Column(Integer, primary_key=True, index=True)
    musteri_id = Column(Integer, ForeignKey('musteriler.id'), nullable=False)
    musteri = relationship("Musteri", back_populates="musteri_kuponlari")
    kupon_id = Column(Integer, ForeignKey('kuponlar.id'), nullable=False)
    kupon = relationship("Kupon", back_populates="musteri_kuponlari")
    son_kullanma_tarihi = Column(DateTime, nullable=True)
    durum = Column(String(20), default='kullanilabilir')
    kullanilan_satis_id = Column(Integer, ForeignKey('satislar.id'), nullable=True)
    kullanilan_satis = relationship("Satis", foreign_keys=[kullanilan_satis_id], post_update=True) 

class MusteriOdeme(Temel):
    __tablename__ = 'musteri_odemeleri'
    id = Column(Integer, primary_key=True, index=True)
    musteri_id = Column(Integer, ForeignKey('musteriler.id'), nullable=False)
    musteri = relationship("Musteri", back_populates="musteri_odemeleri")
    vardiya_id = Column(Integer, ForeignKey('vardiyalar.id'), nullable=True)
    vardiya = relationship("Vardiya", back_populates="musteri_odemeleri")
    tutar = Column(Numeric(10, 2), nullable=False)
    odeme_yontemi = Column(String(50), nullable=False)
    tarih = Column(DateTime, default=datetime.datetime.utcnow)
    notlar = Column(Text, nullable=True)

class Alis(Temel):
    __tablename__ = 'alislar'
    id = Column(Integer, primary_key=True, index=True)
    tedarikci_id = Column(Integer, ForeignKey('tedarikciler.id'), nullable=True)
    tedarikci = relationship("Tedarikci", back_populates="alislar")
    fatura_no = Column(String(100), nullable=True)
    tarih = Column(DateTime, default=datetime.datetime.utcnow)
    notlar = Column(Text, nullable=True)
    kalemler = relationship("AlisKalemi", back_populates="alis", cascade="all, delete-orphan")

class AlisKalemi(Temel):
    __tablename__ = 'alis_kalemleri'
    id = Column(Integer, primary_key=True, index=True)
    alis_id = Column(Integer, ForeignKey('alislar.id'), nullable=False)
    alis = relationship("Alis", back_populates="kalemler")
    urun_id = Column(Integer, ForeignKey('urunler.id'), nullable=False)
    urun = relationship("Urun", back_populates="alis_kalemleri")
    miktar = Column(Numeric(10, 2), nullable=False)
    alis_fiyati = Column(Numeric(10, 2), nullable=False)
    son_kullanma_tarihi = Column(DateTime, nullable=True)

class Iade(Temel):
    __tablename__ = 'iadeler'
    id = Column(Integer, primary_key=True, index=True)
    orijinal_satis_id = Column(Integer, ForeignKey('satislar.id'), nullable=False)
    orijinal_satis = relationship("Satis", back_populates="iade_kayitlari")
    iade_tutari = Column(Numeric(10, 2), nullable=False)
    iade_tarihi = Column(DateTime, default=datetime.datetime.utcnow)
    sebep = Column(Text, nullable=True)
    notlar = Column(Text, nullable=True)
    kullanici_id = Column(Integer, ForeignKey('kullanicilar.id'), nullable=True)
    kullanici = relationship("Kullanici")

class LogKaydi(Temel):
    __tablename__ = 'log_kayitlari'
    id = Column(Integer, primary_key=True, index=True)
    kullanici_id = Column(Integer, ForeignKey('kullanicilar.id'), nullable=True)
    kullanici = relationship("Kullanici", back_populates="loglar")
    islem_tipi = Column(String(100), nullable=False)
    detaylar = Column(Text, nullable=True)
    zaman_damgasi = Column(DateTime, default=datetime.datetime.utcnow)
