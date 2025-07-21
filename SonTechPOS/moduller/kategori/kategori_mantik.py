# Dosya Adı: moduller/kategori/kategori_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 16:20
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, standart print kullanıldı.
#                Hata yönetimi Python'ın yerleşik istisnalarına uyarlandı.
#                Loglama entegrasyonu sağlandı.

from cekirdek.veritabani_yonetimi import OturumYerel, Kategori, Urun
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_CATEGORY_ADD, LOG_ACTION_CATEGORY_UPDATE, LOG_ACTION_CATEGORY_STATUS_CHANGE

# ===== Kategori Ekleme =====
def kategori_ekle(ad: str, aciklama: str = None) -> int | None:
    """
    Veritabanına yeni bir kategori ekler.
    Args:
        ad (str): Kategorinin adı.
        aciklama (str, optional): Kategorinin açıklaması. Defaults to None.
    Returns:
        int | None: Başarılı olursa yeni kategori ID'si, değilse None.
    Raises:
        ValueError: Gerekli alan boşsa.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not ad:
        raise ValueError("Kategori adı boş olamaz.")

    oturum = OturumYerel()
    try:
        yeni_kategori = Kategori(ad=ad, aciklama=aciklama, aktif=True)
        oturum.add(yeni_kategori)
        oturum.commit()
        print(f"DEBUG: Kategori '{ad}' başarıyla eklendi (ID: {yeni_kategori.id}).")
        log_aktivite(None, LOG_ACTION_CATEGORY_ADD, f"Yeni kategori eklendi: ID: {yeni_kategori.id}, Ad: {yeni_kategori.ad}")
        return yeni_kategori.id
    except IntegrityError as e:
        oturum.rollback()
        if "Duplicate entry" in str(e):
            raise IntegrityError(f"Kategori adı '{ad}' zaten kayıtlı!") from e
        else:
            raise Exception(f"Kategori eklenirken veritabanı hatası: {e}") from e
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Kategori eklenirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Kategori Güncelleme =====
def kategori_guncelle(kategori_id: int, yeni_ad: str, yeni_aciklama: str = None) -> bool:
    """
    Verilen ID'ye sahip kategorinin bilgilerini günceller.
    Args:
        kategori_id (int): Güncellenecek kategori ID'si.
        yeni_ad (str): Kategorinin yeni adı.
        yeni_aciklama (str, optional): Kategorinin yeni açıklaması. Defaults to None.
    Returns:
        bool: Güncelleme başarılıysa True, değilse False.
    Raises:
        ValueError: Gerekli alan boşsa.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not yeni_ad:
        raise ValueError("Kategori adı boş olamaz.")

    oturum = OturumYerel()
    try:
        kategori = oturum.query(Kategori).filter(Kategori.id == kategori_id).first()
        if not kategori:
            print(f"UYARI: Kategori (ID: {kategori_id}) bulunamadı.")
            return False

        # Benzersizlik kontrolü (kendisi hariç)
        if oturum.query(Kategori).filter(Kategori.ad == yeni_ad, Kategori.id != kategori_id).first():
            raise IntegrityError(f"Kategori adı '{yeni_ad}' zaten başka bir kategoriye ait!")

        kategori.ad = yeni_ad
        kategori.aciklama = yeni_aciklama
        
        oturum.commit()
        print(f"DEBUG: Kategori (ID: {kategori_id}) başarıyla güncellendi.")
        log_aktivite(None, LOG_ACTION_CATEGORY_UPDATE, f"Kategori güncellendi: ID: {kategori.id}, Yeni Ad: {kategori.ad}")
        return True
    except IntegrityError as e:
        oturum.rollback()
        raise e # Tekrar fırlat
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Kategori güncellenirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Kategori Durum Değiştirme (Aktif/Pasif) =====
def kategori_durum_degistir(kategori_id: int, aktif: bool) -> bool:
    """
    Verilen ID'ye sahip kategorinin aktiflik durumunu değiştirir.
    Args:
        kategori_id (int): Durumu değiştirilecek kategori ID'si.
        aktif (bool): Yeni aktiflik durumu (True: aktif, False: pasif).
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        kategori = oturum.query(Kategori).filter(Kategori.id == kategori_id).first()
        if not kategori:
            print(f"UYARI: Kategori (ID: {kategori_id}) bulunamadı.")
            return False
        
        if kategori.aktif == aktif:
            print(f"BİLGİ: Kategori (ID: {kategori_id}) zaten istenen durumda.")
            return True

        # Eğer pasif yapılıyorsa, bu kategoriyi kullanan aktif ürün var mı kontrol et
        if not aktif:
            aktif_urun_sayisi = oturum.query(Urun).filter(Urun.kategori_id == kategori_id, Urun.aktif == True).count()
            if aktif_urun_sayisi > 0:
                raise Exception(f"Bu kategori {aktif_urun_sayisi} adet aktif ürün tarafından kullanıldığı için pasif yapılamaz!")

        kategori.aktif = aktif
        oturum.commit()
        durum_str = "aktif" if aktif else "pasif"
        print(f"DEBUG: Kategori (ID: {kategori_id}) başarıyla {durum_str} yapıldı.")
        log_aktivite(None, LOG_ACTION_CATEGORY_STATUS_CHANGE, f"Kategori durumu değiştirildi: ID: {kategori.id}, Yeni Durum: {durum_str}")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Kategori durumu değiştirilirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Kategori Listeleme =====
def kategorileri_getir(include_inactive: bool = False, arama_terimi: str = None) -> list[Kategori]:
    """
    Tüm kategorileri veya arama terimine uyanları veritabanından çeker.
    Args:
        include_inactive (bool): Pasif kategorileri de dahil et.
        arama_terimi (str, optional): Ada göre arama terimi. Defaults to None.
    Returns:
        list: Kategori nesnelerinden oluşan bir liste döndürür.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Kategori)
        if not include_inactive:
            sorgu = sorgu.filter(Kategori.aktif == True)
        
        if arama_terimi:
            arama_terimi = f"%{arama_terimi}%"
            sorgu = sorgu.filter(or_(Kategori.ad.ilike(arama_terimi), Kategori.aciklama.ilike(arama_terimi))) # Açıklamada da arama yap
        sorgu = sorgu.order_by(Kategori.ad.asc())
        return sorgu.all()
    except Exception as e:
        print(f"HATA: Kategoriler getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Kategori ID ile Getirme =====
def kategori_getir_by_id(kategori_id: int) -> Kategori | None:
    """
    Verilen ID'ye sahip kategoriyi getirir.
    Args:
        kategori_id (int): Kategori ID'si.
    Returns:
        Kategori | None: Kategori nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        return oturum.query(Kategori).filter(Kategori.id == kategori_id).first()
    except Exception as e:
        print(f"HATA: Kategori (ID: {kategori_id}) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Kategori Adı ile Getirme =====
def kategori_getir_by_ad(ad: str, only_active: bool = True) -> Kategori | None:
    """
    Verilen ada sahip kategoriyi getirir.
    Args:
        ad (str): Kategori adı.
        only_active (bool): Sadece aktif kategorileri ara.
    Returns:
        Kategori | None: Kategori nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Kategori).filter(Kategori.ad.ilike(ad))
        if only_active:
            sorgu = sorgu.filter(Kategori.aktif == True)
        return sorgu.first()
    except Exception as e:
        print(f"HATA: Kategori (ad: {ad}) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
