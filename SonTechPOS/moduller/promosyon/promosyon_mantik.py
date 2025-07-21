# Dosya Adı: moduller/promosyon/promosyon_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 16:15
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, standart print kullanıldı.
#                Hata yönetimi Python'ın yerleşik istisnalarına uyarlandı.
#                Loglama entegrasyonu sağlandı.

from cekirdek.veritabani_yonetimi import OturumYerel, Promosyon, Urun
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import or_
import datetime
from decimal import Decimal
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_PROMOTION_ADD, LOG_ACTION_PROMOTION_UPDATE, LOG_ACTION_PROMOTION_STATUS_CHANGE

# ===== Promosyon Ekleme =====
def promosyon_ekle(ad: str, aciklama: str, promosyon_tipi: str, urun_id: int,
                   gerekli_miktar: int = 0, indirim_tutari: Decimal = Decimal('0.00'),
                   gerekli_bogo_miktar: int = 0, bedava_miktar: int = 0, bedava_urun_id: int = None,
                   baslangic_tarihi: datetime.datetime = None, bitis_tarihi: datetime.datetime = None) -> int | None:
    """
    Veritabanına yeni bir promosyon ekler.
    Args:
        ad (str): Promosyonun adı.
        aciklama (str): Promosyonun açıklaması.
        promosyon_tipi (str): Promosyon türü ('miktar_indirim', 'bogo', 'x_al_y_bedava').
        urun_id (int): Promosyonun uygulandığı ürünün ID'si.
        ... (diğer parametreler) ...
    Returns:
        int | None: Başarılı olursa yeni promosyon ID'si, değilse None.
    Raises:
        ValueError: Gerekli alanlar boşsa veya parametreler geçersizse.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not all([ad, promosyon_tipi, urun_id]):
        raise ValueError("Promosyon adı, türü ve ürün ID'si boş olamaz.")

    oturum = OturumYerel()
    try:
        # Ürün varlığını kontrol et
        if not oturum.query(Urun).filter(Urun.id == urun_id).first():
            raise ValueError(f"Belirtilen ürün ID ({urun_id}) bulunamadı.")
        if bedava_urun_id and not oturum.query(Urun).filter(Urun.id == bedava_urun_id).first():
            raise ValueError(f"Belirtilen bedava ürün ID ({bedava_urun_id}) bulunamadı.")

        # Benzersizlik kontrolü
        if oturum.query(Promosyon).filter(Promosyon.ad == ad).first():
            raise IntegrityError(f"Promosyon adı '{ad}' zaten kayıtlı!")

        # Promosyon tipine göre değer atamaları
        _gerekli_miktar = 0
        _indirim_tutari = Decimal('0.00')
        _gerekli_bogo_miktar = 0
        _bedava_miktar = 0
        _bedava_urun_id = None

        if promosyon_tipi == 'miktar_indirim':
            if not gerekli_miktar or indirim_tutari is None:
                raise ValueError("'miktar_indirim' türü için gerekli miktar ve indirim tutarı belirtilmelidir.")
            if gerekli_miktar <= 0 or indirim_tutari <= Decimal('0.00'):
                raise ValueError("Gerekli miktar ve indirim tutarı 0'dan büyük olmalıdır.")
            _gerekli_miktar = int(gerekli_miktar) # Ensure int
            _indirim_tutari = Decimal(indirim_tutari) # Ensure Decimal
        elif promosyon_tipi in ['bogo', 'x_al_y_free']:
            if not gerekli_bogo_miktar or not bedava_miktar:
                raise ValueError(f"'{promosyon_tipi}' türü için alınması gereken miktar ve bedava verilecek miktar belirtilmelidir.")
            if gerekli_bogo_miktar <= 0 or bedava_miktar <= 0:
                raise ValueError("Alınması gereken miktar ve bedava verilecek miktar 0'dan büyük olmalıdır.")
            _gerekli_bogo_miktar = int(gerekli_bogo_miktar) # Ensure int
            _bedava_miktar = int(bedava_miktar) # Ensure int
            _bedava_urun_id = bedava_urun_id
        else:
            raise ValueError(f"Geçersiz promosyon türü: {promosyon_tipi}")

        yeni_promosyon = Promosyon(
            ad=ad,
            aciklama=aciklama,
            promosyon_tipi=promosyon_tipi,
            urun_id=urun_id,
            gerekli_miktar=_gerekli_miktar,
            indirim_tutari=_indirim_tutari,
            gerekli_bogo_miktar=_gerekli_bogo_miktar,
            bedava_miktar=_bedava_miktar,
            bedava_urun_id=_bedava_urun_id,
            baslangic_tarihi=baslangic_tarihi,
            bitis_tarihi=bitis_tarihi,
            aktif=True
        )
        oturum.add(yeni_promosyon)
        oturum.commit()
        print(f"DEBUG: Promosyon '{ad}' başarıyla eklendi (ID: {yeni_promosyon.id}).")
        log_aktivite(None, LOG_ACTION_PROMOTION_ADD, f"Yeni promosyon eklendi: ID: {yeni_promosyon.id}, Ad: {yeni_promosyon.ad}")
        return yeni_promosyon.id
    except IntegrityError as e:
        oturum.rollback()
        if "Duplicate entry" in str(e):
            raise IntegrityError(f"Promosyon adı '{ad}' zaten kayıtlı!") from e
        else:
            raise Exception(f"Promosyon eklenirken veritabanı hatası: {e}") from e
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Promosyon eklenirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Promosyon Güncelleme =====
def promosyon_guncelle(promosyon_id: int, ad: str, aciklama: str, promosyon_tipi: str, urun_id: int,
                       gerekli_miktar: int = 0, indirim_tutari: Decimal = Decimal('0.00'),
                       gerekli_bogo_miktar: int = 0, bedava_miktar: int = 0, bedava_urun_id: int = None,
                       baslangic_tarihi: datetime.datetime = None, bitis_tarihi: datetime.datetime = None) -> bool:
    """
    Verilen ID'ye sahip promosyonu günceller.
    Args:
        promosyon_id (int): Güncellenecek promosyon ID'si.
        ... (diğer parametreler) ...
    Returns:
        bool: Güncelleme başarılıysa True, değilse False.
    Raises:
        ValueError: Gerekli alanlar boşsa veya parametreler geçersizse.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not all([ad, promosyon_tipi, urun_id]):
        raise ValueError("Promosyon adı, türü ve ürün ID'si boş olamaz.")

    oturum = OturumYerel()
    try:
        promosyon = oturum.query(Promosyon).filter(Promosyon.id == promosyon_id).first()
        if not promosyon:
            print(f"UYARI: Promosyon (ID: {promosyon_id}) bulunamadı.")
            return False

        # Ürün varlığını kontrol et
        if not oturum.query(Urun).filter(Urun.id == urun_id).first():
            raise ValueError(f"Belirtilen ürün ID ({urun_id}) bulunamadı.")
        if bedava_urun_id and not oturum.query(Urun).filter(Urun.id == bedava_urun_id).first():
            raise ValueError(f"Belirtilen bedava ürün ID ({bedava_urun_id}) bulunamadı.")

        # Benzersizlik kontrolü (kendisi hariç)
        if oturum.query(Promosyon).filter(Promosyon.ad == ad, Promosyon.id != promosyon_id).first():
            raise IntegrityError(f"Promosyon adı '{ad}' zaten başka bir promosyona ait!")

        # Promosyon tipine göre değer atamaları
        _gerekli_miktar = 0
        _indirim_tutari = Decimal('0.00')
        _gerekli_bogo_miktar = 0
        _bedava_miktar = 0
        _bedava_urun_id = None

        if promosyon_tipi == 'miktar_indirim':
            if not gerekli_miktar or indirim_tutari is None:
                raise ValueError("'miktar_indirim' türü için gerekli miktar ve indirim tutarı belirtilmelidir.")
            if gerekli_miktar <= 0 or indirim_tutari <= Decimal('0.00'):
                raise ValueError("Gerekli miktar ve indirim tutarı 0'dan büyük olmalıdır.")
            _gerekli_miktar = int(gerekli_miktar) # Ensure int
            _indirim_tutari = Decimal(indirim_tutari) # Ensure Decimal
        elif promosyon_tipi in ['bogo', 'x_al_y_free']:
            if not gerekli_bogo_miktar or not bedava_miktar:
                raise ValueError(f"'{promosyon_tipi}' türü için alınması gereken miktar ve bedava verilecek miktar belirtilmelidir.")
            if gerekli_bogo_miktar <= 0 or bedava_miktar <= 0:
                raise ValueError("Alınması gereken miktar ve bedava verilecek miktar 0'dan büyük olmalıdır.")
            _gerekli_bogo_miktar = int(gerekli_bogo_miktar) # Ensure int
            _bedava_miktar = int(bedava_miktar) # Ensure int
            _bedava_urun_id = bedava_urun_id
        else:
            raise ValueError(f"Geçersiz promosyon türü: {promosyon_tipi}")

        promosyon.ad = ad
        promosyon.aciklama = aciklama
        promosyon.promosyon_tipi = promosyon_tipi
        promosyon.urun_id = urun_id
        promosyon.gerekli_miktar = _gerekli_miktar
        promosyon.indirim_tutari = _indirim_tutari
        promosyon.gerekli_bogo_miktar = _gerekli_bogo_miktar
        promosyon.bedava_miktar = _bedava_miktar
        promosyon.bedava_urun_id = _bedava_urun_id
        promosyon.baslangic_tarihi = baslangic_tarihi
        promosyon.bitis_tarihi = bitis_tarihi
        
        oturum.commit()
        print(f"DEBUG: Promosyon (ID: {promosyon_id}) başarıyla güncellendi.")
        log_aktivite(None, LOG_ACTION_PROMOTION_UPDATE, f"Promosyon güncellendi: ID: {promosyon.id}, Ad: {promosyon.ad}")
        return True
    except IntegrityError as e:
        oturum.rollback()
        raise e # Tekrar fırlat
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Promosyon güncellenirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Promosyon Durum Değiştirme (Aktif/Pasif) =====
def promosyon_durum_degistir(promosyon_id: int, aktif: bool) -> bool:
    """
    Verilen ID'ye sahip promosyonun aktiflik durumunu değiştirir.
    Args:
        promosyon_id (int): Durumu değiştirilecek promosyon ID'si.
        aktif (bool): Yeni aktiflik durumu (True: aktif, False: pasif).
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        promosyon = oturum.query(Promosyon).filter(Promosyon.id == promosyon_id).first()
        if not promosyon:
            print(f"UYARI: Promosyon (ID: {promosyon_id}) bulunamadı.")
            return False
        
        if promosyon.aktif == aktif:
            print(f"BİLGİ: Promosyon (ID: {promosyon_id}) zaten istenen durumda.")
            return True

        promosyon.aktif = aktif
        oturum.commit()
        durum_str = "aktif" if aktif else "pasif"
        print(f"DEBUG: Promosyon (ID: {promosyon_id}) başarıyla {durum_str} yapıldı.")
        log_aktivite(None, LOG_ACTION_PROMOTION_STATUS_CHANGE, f"Promosyon durumu değiştirildi: ID: {promosyon.id}, Yeni Durum: {durum_str}")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Promosyon durumu değiştirilirken beklenmedik bir hata oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Promosyon Listeleme =====
def promosyonlari_getir(include_inactive: bool = False, arama_terimi: str = None) -> list[Promosyon]:
    """
    Tüm promosyonları veya arama terimine uyanları veritabanından çeker.
    Args:
        include_inactive (bool): Pasif promosyonları da dahil et.
        arama_terimi (str, optional): Ada göre arama terimi. Defaults to None.
    Returns:
        list: Promosyon nesnelerinden oluşan bir liste döndürür.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Promosyon).outerjoin(Urun, Promosyon.urun_id == Urun.id)
        if not include_inactive:
            sorgu = sorgu.filter(Promosyon.aktif == True)
        
        if arama_terimi:
            arama_terimi = f"%{arama_terimi}%"
            sorgu = sorgu.filter(Promosyon.ad.ilike(arama_terimi))
        sorgu = sorgu.order_by(Promosyon.ad.asc())
        return sorgu.all()
    except Exception as e:
        print(f"HATA: Promosyonlar getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Promosyon ID ile Getirme =====
def promosyon_getir_by_id(promosyon_id: int) -> Promosyon | None:
    """
    Verilen ID'ye sahip promosyonu getirir.
    Args:
        promosyon_id (int): Promosyon ID'si.
    Returns:
        Promosyon | None: Promosyon nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        return oturum.query(Promosyon).filter(Promosyon.id == promosyon_id).first()
    except Exception as e:
        print(f"HATA: Promosyon (ID: {promosyon_id}) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== Aktif Promosyonları Ürüne Göre Getirme =====
def urune_gore_aktif_promosyonlari_getir(urun_id: int) -> list[Promosyon]:
    """
    Belirli bir ürün için şu anda aktif ve geçerli olan promosyonları getirir.
    Args:
        urun_id (int): Ürün ID'si.
    Returns:
        list: Geçerli promosyon nesnelerinden oluşan bir liste.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        today = datetime.datetime.utcnow().date() # Sadece tarih kısmını al
        promosyonlar = oturum.query(Promosyon).filter(
            Promosyon.urun_id == urun_id,
            Promosyon.aktif == True,
            or_(Promosyon.baslangic_tarihi == None, Promosyon.baslangic_tarihi <= today),
            or_(Promosyon.bitis_tarihi == None, Promosyon.bitis_tarihi >= today)
        ).all()
        return promosyonlar
    except Exception as e:
        print(f"HATA: Ürün (ID: {urun_id}) için aktif promosyonlar getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
