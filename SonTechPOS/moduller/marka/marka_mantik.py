# Dosya Adı: moduller/marka/marka_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 16:05
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, standart print kullanıldı.
#                Hata yönetimi Python'ın yerleşik istisnalarına uyarlandı.
#                Loglama entegrasyonu sağlandı.

from cekirdek.veritabani_yonetimi import OturumYerel, Marka, Urun
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_BRAND_ADD, LOG_ACTION_BRAND_UPDATE, LOG_ACTION_BRAND_STATUS_CHANGE

# ===== Marka Ekleme =====
def marka_ekle(ad: str) -> int | None:
    """
    Veritabanına yeni bir marka ekler.
    Args:
        ad (str): Markanın adı.
    Returns:
        int | None: Başarılı olursa yeni marka ID'si, değilse None.
    Raises:
        ValueError: Gerekli alan boşsa.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not ad:
        raise ValueError("Marka adı boş olamaz.")

    oturum = OturumYerel()
    try:
        yeni_marka = Marka(ad=ad, aktif=True)
        oturum.add(yeni_marka)
        oturum.commit()
        print(f"DEBUG: Marka '{ad}' başarıyla eklendi (ID: {yeni_marka.id}).")
        log_aktivite(None, LOG_ACTION_BRAND_ADD, f"Yeni marka eklendi: ID: {yeni_marka.id}, Ad: {yeni_marka.ad}")
        return yeni_marka.id
    except IntegrityError as e:
        oturum.rollback()
        # MySQL hata kodlarını kontrol etmek yerine, hata mesajını kontrol edebiliriz
        if "Duplicate entry" in str(e):
            raise IntegrityError(f"Marka adı '{ad}' zaten kayıtlı!") from e
        else:
            raise Exception(f"Marka eklenirken veritabanı hatası: {e}") from e
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Marka eklenirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Marka Güncelleme =====
def marka_guncelle(marka_id: int, yeni_ad: str) -> bool:
    """
    Verilen ID'ye sahip markanın adını günceller.
    Args:
        marka_id (int): Güncellenecek marka ID'si.
        yeni_ad (str): Markanın yeni adı.
    Returns:
        bool: Güncelleme başarılıysa True, değilse False.
    Raises:
        ValueError: Gerekli alan boşsa.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not yeni_ad:
        raise ValueError("Marka adı boş olamaz.")

    oturum = OturumYerel()
    try:
        marka = oturum.query(Marka).filter(Marka.id == marka_id).first()
        if not marka:
            print(f"UYARI: Marka (ID: {marka_id}) bulunamadı.")
            return False

        # Benzersizlik kontrolü (kendisi hariç)
        if oturum.query(Marka).filter(Marka.ad == yeni_ad, Marka.id != marka_id).first():
            raise IntegrityError(f"Marka adı '{yeni_ad}' zaten başka bir markaya ait!")

        marka.ad = yeni_ad
        oturum.commit()
        print(f"DEBUG: Marka (ID: {marka_id}) başarıyla güncellendi.")
        log_aktivite(None, LOG_ACTION_BRAND_UPDATE, f"Marka güncellendi: ID: {marka.id}, Ad: {marka.ad}")
        return True
    except IntegrityError as e:
        oturum.rollback()
        raise e # Tekrar fırlat
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Marka güncellenirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Marka Durum Değiştirme (Aktif/Pasif) =====
def marka_durum_degistir(marka_id: int, aktif: bool) -> bool:
    """
    Verilen ID'ye sahip markanın aktiflik durumunu değiştirir.
    Args:
        marka_id (int): Durumu değiştirilecek marka ID'si.
        aktif (bool): Yeni aktiflik durumu (True: aktif, False: pasif).
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        marka = oturum.query(Marka).filter(Marka.id == marka_id).first()
        if not marka:
            print(f"UYARI: Marka (ID: {marka_id}) bulunamadı.")
            return False
        
        if marka.aktif == aktif:
            print(f"BİLGİ: Marka (ID: {marka_id}) zaten istenen durumda.")
            return True

        # Eğer pasif yapılıyorsa, bu markayı kullanan aktif ürün var mı kontrol et
        if not aktif:
            aktif_urun_sayisi = oturum.query(Urun).filter(Urun.marka_id == marka_id, Urun.aktif == True).count()
            if aktif_urun_sayisi > 0:
                raise Exception(f"Bu marka {aktif_urun_sayisi} adet aktif ürün tarafından kullanıldığı için pasif yapılamaz!")

        marka.aktif = aktif
        oturum.commit()
        durum_str = "aktif" if aktif else "pasif"
        print(f"DEBUG: Marka (ID: {marka_id}) başarıyla {durum_str} yapıldı.")
        log_aktivite(None, LOG_ACTION_BRAND_STATUS_CHANGE, f"Marka durumu değiştirildi: ID: {marka.id}, Yeni Durum: {durum_str}")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Marka durumu değiştirilirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Marka Listeleme =====
def markalari_getir(include_inactive: bool = False, arama_terimi: str = None) -> list[Marka]:
    """
    Tüm markaları veya arama terimine uyanları veritabanından çeker.
    Args:
        include_inactive (bool): Pasif markaları da dahil et.
        arama_terimi (str, optional): Ada göre arama terimi. Defaults to None.
    Returns:
        list: Marka nesnelerinden oluşan bir liste döndürür.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Marka)
        if not include_inactive:
            sorgu = sorgu.filter(Marka.aktif == True)
        
        if arama_terimi:
            arama_terimi = f"%{arama_terimi}%"
            sorgu = sorgu.filter(Marka.ad.ilike(arama_terimi))
        sorgu = sorgu.order_by(Marka.ad.asc())
        return sorgu.all()
    except Exception as e:
        print(f"HATA: Markalar getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Marka ID ile Getirme =====
def marka_getir_by_id(marka_id: int) -> Marka | None:
    """
    Verilen ID'ye sahip markayı getirir.
    Args:
        marka_id (int): Marka ID'si.
    Returns:
        Marka | None: Marka nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        return oturum.query(Marka).filter(Marka.id == marka_id).first()
    except Exception as e:
        print(f"HATA: Marka (ID: {marka_id}) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Marka Adı ile Getirme =====
def marka_getir_by_ad(ad: str, only_active: bool = True) -> Marka | None:
    """
    Verilen ada sahip markayı getirir.
    Args:
        ad (str): Marka adı.
        only_active (bool): Sadece aktif markaları ara.
    Returns:
        Marka | None: Marka nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Marka).filter(Marka.ad.ilike(ad))
        if only_active:
            sorgu = sorgu.filter(Marka.aktif == True)
        return sorgu.first()
    except Exception as e:
        print(f"HATA: Marka (ad: {ad}) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
