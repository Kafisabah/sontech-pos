# Dosya Adı: cekirdek/loglama/log_mantik.py
# Güncelleme Tarihi / Saati: 16.07.2025 / 07:30
# Yapılan İşlem: Kullanıcıdan gelen son sürüm ile güncellendi.

import datetime
from cekirdek.veritabani_yonetimi import OturumYerel, LogKaydi, Kullanici
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError

# === Log İşlem Tipleri Sabitleri ===
LOG_ACTION_SALE_COMPLETE = "SATIS_TAMAMLA"
LOG_ACTION_SALE_RETURN = "SATIS_IADE"
LOG_ACTION_PRODUCT_ADD = "URUN_EKLE"
LOG_ACTION_PRODUCT_UPDATE = "URUN_GUNCELLE"
LOG_ACTION_PRODUCT_STATUS_CHANGE = "URUN_DURUM_DEGISTIR"
LOG_ACTION_STOCK_ADJUSTMENT = "STOK_DUZELTME"
LOG_ACTION_STOCK_PURCHASE = "ALIS_KAYDI"
LOG_ACTION_CUSTOMER_ADD = "MUSTERI_EKLE"
LOG_ACTION_CUSTOMER_UPDATE = "MUSTERI_GUNCELLE"
LOG_ACTION_CUSTOMER_PAYMENT = "MUSTERI_ODEME_AL"
LOG_ACTION_CUSTOMER_STATUS_CHANGE = "MUSTERI_DURUM_DEGISTIR"
LOG_ACTION_USER_LOGIN = "KULLANICI_GIRIS"
LOG_ACTION_USER_LOGOUT = "KULLANICI_CIKIS"
LOG_ACTION_USER_ADD = "KULLANICI_EKLE"
LOG_ACTION_USER_UPDATE = "KULLANICI_GUNCELLE"
LOG_ACTION_USER_PASSWORD_CHANGE = "KULLANICI_SIFRE_DEGISTIR"
LOG_ACTION_USER_STATUS_CHANGE = "KULLANICI_DURUM_DEGISTIR"
LOG_ACTION_BRAND_ADD = "MARKA_EKLE"
LOG_ACTION_BRAND_UPDATE = "MARKA_GUNCELLE" 
LOG_ACTION_BRAND_STATUS_CHANGE = "MARKA_DURUM_DEGISTIR"
LOG_ACTION_CATEGORY_ADD = "KATEGORI_EKLE"
LOG_ACTION_CATEGORY_UPDATE = "KATEGORI_GUNCELLE"
LOG_ACTION_CATEGORY_STATUS_CHANGE = "KATEGORI_DURUM_DEGISTIR"
LOG_ACTION_PROMOTION_ADD = "PROMOSYON_EKLE"
LOG_ACTION_PROMOTION_UPDATE = "PROMOSYON_GUNCELLE"
LOG_ACTION_PROMOTION_STATUS_CHANGE = "PROMOSYON_DURUM_DEGISTIR"
LOG_ACTION_SUPPLIER_ADD = "TEDARIKCI_EKLE"
LOG_ACTION_SUPPLIER_UPDATE = "TEDARIKCI_GUNCELLE"
LOG_ACTION_SUPPLIER_STATUS_CHANGE = "TEDARIKCI_DURUM_DEGISTIR"
LOG_ACTION_SHIFT_START = "VARDIYA_BASLAT"
LOG_ACTION_SHIFT_END = "VARDIYA_BITIR"
LOG_ACTION_SETTINGS_UPDATE = "AYARLAR_GUNCELLE"
LOG_ACTION_PRODUCT_LABEL_PRINT = "URUN_ETIKET_BAS"


# ===== log_aktivite FONKSİYONU BAŞLANGICI =====
def log_aktivite(kullanici_id: int | None, islem_tipi: str, detaylar: str):
    """
    Uygulama içi aktiviteleri veritabanına kaydeder.
    Args:
        kullanici_id (int | None): İşlemi yapan kullanıcının ID'si. Eğer sistem tarafından yapılan bir işlemse None olabilir.
        islem_tipi (str): Yapılan işlemin tipi (örn: "SATIS_TAMAMLA", "URUN_EKLE").
        detaylar (str): İşlemle ilgili detaylı açıklama.
    """
    oturum = OturumYerel()
    try:
        yeni_log = LogKaydi(
            kullanici_id=kullanici_id,
            islem_tipi=islem_tipi,
            detaylar=detaylar,
            zaman_damgasi=datetime.datetime.utcnow()
        )
        oturum.add(yeni_log)
        oturum.commit()
    except SQLAlchemyError as e:
        oturum.rollback()
        print(f"HATA: Log kaydı veritabanına eklenirken bir sorun oluştu: {e}")
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Log kaydı sırasında beklenmedik bir hata oluştu: {e}")
    finally:
        oturum.close()
# ===== log_aktivite FONKSİYONU BİTİŞİ =====

# ===== log_kayitlarini_getir FONKSİYONU BAŞLANGICI =====
def log_kayitlarini_getir(limit: int = 100, islem_tipi: str = None, kullanici_id: int = None, baslangic_tarihi: datetime.date = None, bitis_tarihi: datetime.date = None) -> list[LogKaydi]:
    """
    Veritabanından log kayıtlarını çeker, filtrelere göre.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(LogKaydi).options(joinedload(LogKaydi.kullanici)).order_by(LogKaydi.zaman_damgasi.desc())

        if islem_tipi:
            sorgu = sorgu.filter(LogKaydi.islem_tipi == islem_tipi)
        if kullanici_id:
            sorgu = sorgu.filter(LogKaydi.kullanici_id == kullanici_id)
        if baslangic_tarihi:
            sorgu = sorgu.filter(LogKaydi.zaman_damgasi >= baslangic_tarihi)
        if bitis_tarihi:
            # Bitiş tarihini de dahil etmek için bir gün ekliyoruz
            bitis_tarihi_dahil = bitis_tarihi + datetime.timedelta(days=1)
            sorgu = sorgu.filter(LogKaydi.zaman_damgasi < bitis_tarihi_dahil)
        
        sorgu = sorgu.limit(limit)
        return sorgu.all()
    except Exception as e:
        print(f"HATA: Log kayıtları getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== log_kayitlarini_getir FONKSİYONU BİTİŞİ =====
