# Dosya Adı: moduller/tedarikci/tedarikci_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 15:55
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, standart print kullanıldı.
#                Hata yönetimi Python'ın yerleşik istisnalarına uyarlandı.

from cekirdek.veritabani_yonetimi import OturumYerel, Tedarikci, Alis
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_SUPPLIER_ADD, LOG_ACTION_SUPPLIER_UPDATE, LOG_ACTION_SUPPLIER_STATUS_CHANGE

# ===== Tedarikçi Ekleme =====
def tedarikci_ekle(ad: str, iletisim_yetkilisi: str = None, telefon: str = None, email: str = None, adres: str = None) -> int | None:
    """
    Veritabanına yeni bir tedarikçi ekler.
    Args:
        ad (str): Tedarikçinin adı.
        iletisim_yetkilisi (str, optional): İletişim yetkilisi. Defaults to None.
        telefon (str, optional): Telefon numarası. Defaults to None.
        email (str, optional): E-posta adresi. Defaults to None.
        adres (str, optional): Adres bilgisi. Defaults to None.
    Returns:
        int | None: Başarılı olursa yeni tedarikçi ID'si, değilse None.
    Raises:
        ValueError: Gerekli alanlar boşsa.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not ad:
        raise ValueError("Tedarikçi adı boş olamaz.")

    oturum = OturumYerel()
    try:
        yeni_tedarikci = Tedarikci(
            ad=ad,
            iletisim_yetkilisi=iletisim_yetkilisi,
            telefon=telefon,
            email=email,
            adres=adres,
            aktif=True
        )
        oturum.add(yeni_tedarikci)
        oturum.commit()
        print(f"DEBUG: Tedarikçi '{ad}' başarıyla eklendi (ID: {yeni_tedarikci.id}).")
        log_aktivite(None, LOG_ACTION_SUPPLIER_ADD, f"Yeni tedarikçi eklendi: ID: {yeni_tedarikci.id}, Ad: {yeni_tedarikci.ad}")
        return yeni_tedarikci.id
    except IntegrityError as e:
        oturum.rollback()
        # MySQL hata kodlarını kontrol etmek yerine, hata mesajını kontrol edebiliriz
        if "Duplicate entry" in str(e):
            if "for key 'ad'" in str(e):
                raise IntegrityError(f"Tedarikçi adı '{ad}' zaten kayıtlı!") from e
            elif "for key 'telefon'" in str(e):
                raise IntegrityError(f"Telefon numarası '{telefon}' zaten başka bir tedarikçiye kayıtlı!") from e
            elif "for key 'email'" in str(e):
                raise IntegrityError(f"E-posta adresi '{email}' zaten başka bir tedarikçiye kayıtlı!") from e
            else:
                raise IntegrityError(f"Tedarikçi eklenirken benzersizlik hatası: {e}") from e
        else:
            raise Exception(f"Tedarikçi eklenirken veritabanı hatası: {e}") from e
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Tedarikçi eklenirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Tedarikçi Güncelleme =====
def tedarikci_guncelle(tedarikci_id: int, ad: str, iletisim_yetkilisi: str = None, telefon: str = None, email: str = None, adres: str = None) -> bool:
    """
    Verilen ID'ye sahip tedarikçinin bilgilerini günceller.
    Args:
        tedarikci_id (int): Güncellenecek tedarikçi ID'si.
        ad (str): Yeni tedarikçi adı.
        ... (diğer parametreler) ...
    Returns:
        bool: Güncelleme başarılıysa True, değilse False.
    Raises:
        ValueError: Gerekli alan boşsa.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not ad:
        raise ValueError("Tedarikçi adı boş olamaz.")

    oturum = OturumYerel()
    try:
        tedarikci = oturum.query(Tedarikci).filter(Tedarikci.id == tedarikci_id).first()
        if not tedarikci:
            print(f"UYARI: Tedarikçi (ID: {tedarikci_id}) bulunamadı.")
            return False

        # Benzersizlik kontrolü (kendisi hariç)
        if oturum.query(Tedarikci).filter(Tedarikci.ad == ad, Tedarikci.id != tedarikci_id).first():
            raise IntegrityError(f"Tedarikçi adı '{ad}' zaten başka bir tedarikçiye ait!")
        if telefon and oturum.query(Tedarikci).filter(Tedarikci.telefon == telefon, Tedarikci.id != tedarikci_id).first():
            raise IntegrityError(f"Telefon numarası '{telefon}' zaten başka bir tedarikçiye kayıtlı!")
        if email and oturum.query(Tedarikci).filter(Tedarikci.email == email, Tedarikci.id != tedarikci_id).first():
            raise IntegrityError(f"E-posta adresi '{email}' zaten başka bir tedarikçiye kayıtlı!")

        tedarikci.ad = ad
        tedarikci.iletisim_yetkilisi = iletisim_yetkilisi
        tedarikci.telefon = telefon
        tedarikci.email = email
        tedarikci.adres = adres
        
        oturum.commit()
        print(f"DEBUG: Tedarikçi (ID: {tedarikci_id}) başarıyla güncellendi.")
        log_aktivite(None, LOG_ACTION_SUPPLIER_UPDATE, f"Tedarikçi güncellendi: ID: {tedarikci.id}, Ad: {tedarikci.ad}")
        return True
    except IntegrityError as e:
        oturum.rollback()
        raise e # Tekrar fırlat
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Tedarikçi güncellenirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Tedarikçi Durum Değiştirme (Aktif/Pasif) =====
def tedarikci_durum_degistir(tedarikci_id: int, aktif: bool) -> bool:
    """
    Verilen ID'ye sahip tedarikçinin aktiflik durumunu değiştirir.
    Args:
        tedarikci_id (int): Durumu değiştirilecek tedarikçi ID'si.
        aktif (bool): Yeni aktiflik durumu (True: aktif, False: pasif).
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        tedarikci = oturum.query(Tedarikci).filter(Tedarikci.id == tedarikci_id).first()
        if not tedarikci:
            print(f"UYARI: Tedarikçi (ID: {tedarikci_id}) bulunamadı.")
            return False
        
        if tedarikci.aktif == aktif:
            print(f"BİLGİ: Tedarikçi (ID: {tedarikci_id}) zaten istenen durumda.")
            return True

        # Eğer pasif yapılıyorsa, bu tedarikçiyi kullanan aktif alış kaydı var mı kontrol et
        if not aktif:
            aktif_alis_sayisi = oturum.query(Alis).filter(Alis.tedarikci_id == tedarikci_id).count()
            if aktif_alis_sayisi > 0:
                raise Exception(f"Bu tedarikçi {aktif_alis_sayisi} adet alış kaydında kullanıldığı için pasif yapılamaz!")

        tedarikci.aktif = aktif
        oturum.commit()
        durum_str = "aktif" if aktif else "pasif"
        print(f"DEBUG: Tedarikçi (ID: {tedarikci_id}) başarıyla {durum_str} yapıldı.")
        log_aktivite(None, LOG_ACTION_SUPPLIER_STATUS_CHANGE, f"Tedarikçi durumu değiştirildi: ID: {tedarikci.id}, Yeni Durum: {durum_str}")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Tedarikçi durumu değiştirilirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Tedarikçi Listeleme =====
def tedarikcileri_getir(include_inactive: bool = False, arama_terimi: str = None) -> list[Tedarikci]:
    """
    Tüm tedarikçileri veya arama terimine uyanları veritabanından çeker.
    Args:
        include_inactive (bool): Pasif tedarikçileri de dahil et.
        arama_terimi (str, optional): Ada veya telefona göre arama terimi. Defaults to None.
    Returns:
        list: Tedarikçi nesnelerinden oluşan bir liste döndürür.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Tedarikci)
        if not include_inactive:
            sorgu = sorgu.filter(Tedarikci.aktif == True)
        
        if arama_terimi:
            arama_terimi = f"%{arama_terimi}%"
            sorgu = sorgu.filter(
                or_(
                    Tedarikci.ad.ilike(arama_terimi),
                    Tedarikci.telefon.ilike(arama_terimi)
                )
            )
        sorgu = sorgu.order_by(Tedarikci.ad.asc())
        return sorgu.all()
    except Exception as e:
        print(f"HATA: Tedarikçiler getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Tedarikçi ID ile Getirme =====
def tedarikci_getir_by_id(tedarikci_id: int) -> Tedarikci | None:
    """
    Verilen ID'ye sahip tedarikçiyi getirir.
    Args:
        tedarikci_id (int): Tedarikçi ID'si.
    Returns:
        Tedarikci | None: Tedarikçi nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        return oturum.query(Tedarikci).filter(Tedarikci.id == tedarikci_id).first()
    except Exception as e:
        print(f"HATA: Tedarikçi (ID: {tedarikci_id}) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Tedarikçi Telefon Numarası ile Getirme =====
def tedarikci_getir_by_telefon(telefon: str, only_active: bool = True) -> Tedarikci | None:
    """
    Verilen telefon numarasına sahip tedarikçiyi getirir.
    Args:
        telefon (str): Telefon numarası.
        only_active (bool): Sadece aktif tedarikçileri ara.
    Returns:
        Tedarikci | None: Tedarikçi nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Tedarikci).filter(Tedarikci.telefon == telefon)
        if only_active:
            sorgu = sorgu.filter(Tedarikci.aktif == True)
        return sorgu.first()
    except Exception as e:
        print(f"HATA: Tedarikçi (telefon: {telefon}) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
