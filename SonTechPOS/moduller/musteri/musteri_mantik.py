# Dosya Adı: moduller/musteri/musteri_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 16:00
# Yapılan İşlem: Müşteri güncelleme, ödeme alma, hesap ekstresi ve kupon işlemleri eklendi.

from cekirdek.veritabani_yonetimi import OturumYerel, Musteri, MusteriOdeme, MusteriKupon, Kupon, Satis
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func, and_
from decimal import Decimal
import datetime
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_CUSTOMER_ADD, LOG_ACTION_CUSTOMER_UPDATE, LOG_ACTION_CUSTOMER_STATUS_CHANGE, LOG_ACTION_CUSTOMER_PAYMENT

# ===== musterileri_getir FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def musterileri_getir(include_inactive: bool = False, arama_terimi: str = None) -> list[Musteri]:
    """
    Tüm müşterileri veya arama terimine uyanları veritabanından çeker.
    Args:
        include_inactive (bool): Pasif müşterileri de dahil et.
        arama_terimi (str, optional): Ad veya telefona göre arama terimi. Defaults to None.
    Returns:
        list: Musteri nesnelerinden oluşan bir liste döndürür.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Musteri)
        if not include_inactive:
            sorgu = sorgu.filter(Musteri.aktif == True)
        
        if arama_terimi:
            arama_terimi = f"%{arama_terimi}%"
            sorgu = sorgu.filter(
                or_(
                    Musteri.ad.ilike(arama_terimi),
                    Musteri.telefon.ilike(arama_terimi)
                )
            )
        sorgu = sorgu.order_by(Musteri.ad.asc())
        return sorgu.all()
    except Exception as e:
        print(f"HATA: Müşteriler getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== musterileri_getir FONKSİYONU BİTİŞİ =====

# ===== yeni_musteri_ekle FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def yeni_musteri_ekle(ad: str, telefon: str = None, email: str = None, adres: str = None) -> int | None:
    """
    Yeni bir müşteriyi veritabanına ekler.
    Args:
        ad (str): Müşterinin adı.
        telefon (str, optional): Telefon numarası. Defaults to None.
        email (str, optional): E-posta adresi. Defaults to None.
        adres (str, optional): Adres bilgisi. Defaults to None.
    Returns:
        int | None: Başarılı olursa yeni müşteri ID'si, değilse None.
    Raises:
        ValueError: Gerekli alan boşsa.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not ad:
        raise ValueError("Müşteri adı boş olamaz.")

    oturum = OturumYerel()
    try:
        # Telefon veya e-posta benzersizlik kontrolü
        if telefon and oturum.query(Musteri).filter(Musteri.telefon == telefon).first():
            raise IntegrityError(f"Telefon numarası '{telefon}' zaten başka bir müşteriye kayıtlı!")
        if email and oturum.query(Musteri).filter(Musteri.email == email).first():
            raise IntegrityError(f"E-posta adresi '{email}' zaten başka bir müşteriye kayıtlı!")

        yeni_musteri = Musteri(
            ad=ad,
            telefon=telefon,
            email=email,
            adres=adres,
            bakiye=Decimal('0.00'),
            sadakat_puani=0,
            aktif=True
        )
        oturum.add(yeni_musteri)
        oturum.commit()
        print(f"DEBUG: '{yeni_musteri.ad}' müşterisi başarıyla eklendi (ID: {yeni_musteri.id}).")
        log_aktivite(None, LOG_ACTION_CUSTOMER_ADD, f"Yeni müşteri eklendi: ID: {yeni_musteri.id}, Ad: {yeni_musteri.ad}")
        return yeni_musteri.id
    except IntegrityError as e:
        oturum.rollback()
        raise e # Tekrar fırlat
    except Exception as e:
        oturum.rollback()
        raise Exception(f"Müşteri eklenirken bir sorun oluştu: {e}")
    finally:
        oturum.close()
# ===== yeni_musteri_ekle FONKSİYONU BİTİŞİ =====

# ===== musteri_guncelle FONKSİYONU BAŞLANGICI (YENİ) =====
def musteri_guncelle(musteri_id: int, yeni_ad: str, yeni_telefon: str = None, yeni_email: str = None, yeni_adres: str = None, yeni_bakiye: Decimal = None) -> bool:
    """
    Verilen ID'ye sahip müşterinin bilgilerini günceller.
    Args:
        musteri_id (int): Güncellenecek müşteri ID'si.
        yeni_ad (str): Yeni müşteri adı.
        ... (diğer parametreler) ...
    Returns:
        bool: Güncelleme başarılıysa True, değilse False.
    Raises:
        ValueError: Gerekli alan boşsa.
        IntegrityError: Benzersizlik kısıtlaması ihlal edilirse.
        Exception: Diğer veritabanı hatalarında.
    """
    if not yeni_ad:
        raise ValueError("Müşteri adı boş olamaz.")

    oturum = OturumYerel()
    try:
        musteri = oturum.query(Musteri).filter(Musteri.id == musteri_id).first()
        if not musteri:
            print(f"UYARI: Müşteri (ID: {musteri_id}) bulunamadı.")
            return False

        # Benzersizlik kontrolü (kendisi hariç)
        if yeni_telefon and oturum.query(Musteri).filter(Musteri.telefon == yeni_telefon, Musteri.id != musteri_id).first():
            raise IntegrityError(f"Telefon numarası '{yeni_telefon}' zaten başka bir müşteriye kayıtlı!")
        if yeni_email and oturum.query(Musteri).filter(Musteri.email == yeni_email, Musteri.id != musteri_id).first():
            raise IntegrityError(f"E-posta adresi '{yeni_email}' zaten başka bir müşteriye kayıtlı!")

        musteri.ad = yeni_ad
        musteri.telefon = yeni_telefon
        musteri.email = yeni_email
        musteri.adres = yeni_adres
        if yeni_bakiye is not None:
            musteri.bakiye = yeni_bakiye # Bakiye doğrudan ayarlanabilir (manuel düzeltmeler için)
        
        oturum.commit()
        print(f"DEBUG: Müşteri (ID: {musteri_id}) başarıyla güncellendi.")
        log_aktivite(None, LOG_ACTION_CUSTOMER_UPDATE, f"Müşteri güncellendi: ID: {musteri.id}, Ad: {musteri.ad}")
        return True
    except IntegrityError as e:
        oturum.rollback()
        raise e # Tekrar fırlat
    except Exception as e:
        oturum.rollback()
        raise Exception(f"Müşteri güncellenirken bir hata oluştu: {e}")
    finally:
        oturum.close()
# ===== musteri_guncelle FONKSİYONU BİTİŞİ =====

# ===== musteri_durum_degistir FONKSİYONU BAŞLANGICI (YENİ) =====
def musteri_durum_degistir(musteri_id: int, aktif: bool) -> bool:
    """
    Verilen ID'ye sahip müşterinin aktiflik durumunu değiştirir.
    Args:
        musteri_id (int): Durumu değiştirilecek müşteri ID'si.
        aktif (bool): Yeni aktiflik durumu (True: aktif, False: pasif).
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        musteri = oturum.query(Musteri).filter(Musteri.id == musteri_id).first()
        if not musteri:
            print(f"UYARI: Müşteri (ID: {musteri_id}) bulunamadı.")
            return False
        
        if musteri.aktif == aktif:
            print(f"BİLGİ: Müşteri (ID: {musteri_id}) zaten istenen durumda.")
            return True

        musteri.aktif = aktif
        oturum.commit()
        durum_str = "aktif" if aktif else "pasif"
        print(f"DEBUG: Müşteri (ID: {musteri_id}) başarıyla {durum_str} yapıldı.")
        log_aktivite(None, LOG_ACTION_CUSTOMER_STATUS_CHANGE, f"Müşteri durumu değiştirildi: ID: {musteri.id}, Yeni Durum: {durum_str}")
        return True
    except Exception as e:
        oturum.rollback()
        raise Exception(f"Müşteri durumu değiştirilirken bir hata oluştu: {e}")
    finally:
        oturum.close()
# ===== musteri_durum_degistir FONKSİYONU BİTİŞİ =====

# ===== musteri_odeme_kaydet FONKSİYONU BAŞLANGICI (YENİ) =====
def musteri_odeme_kaydet(musteri_id: int, tutar: Decimal, odeme_yontemi: str, notlar: str = None, vardiya_id: int = None) -> int | None:
    """
    Müşteriden alınan ödemeyi kaydeder ve bakiyesini günceller.
    Args:
        musteri_id (int): Ödeme yapan müşteri ID'si.
        tutar (Decimal): Ödeme miktarı.
        odeme_yontemi (str): Ödeme yöntemi (örn: 'Nakit', 'Kredi Kartı').
        notlar (str, optional): Ödeme notları. Defaults to None.
        vardiya_id (int, optional): Ödemenin alındığı vardiya ID'si. Defaults to None.
    Returns:
        int | None: Başarılı olursa yeni müşteri ödeme kaydının ID'si, değilse None.
    Raises:
        ValueError: Miktar negatifse veya müşteri bulunamazsa.
        Exception: Diğer veritabanı hatalarında.
    """
    if tutar <= Decimal('0.00'):
        raise ValueError("Ödeme miktarı pozitif olmalıdır.")

    oturum = OturumYerel()
    try:
        musteri = oturum.query(Musteri).filter(Musteri.id == musteri_id).first()
        if not musteri:
            raise ValueError(f"Müşteri (ID: {musteri_id}) bulunamadı.")

        yeni_odeme = MusteriOdeme(
            musteri_id=musteri_id,
            vardiya_id=vardiya_id,
            tutar=tutar,
            odeme_yontemi=odeme_yontemi,
            notlar=notlar,
            tarih=datetime.datetime.utcnow()
        )
        oturum.add(yeni_odeme)
        oturum.flush() # ID'yi almak için

        # Müşteri bakiyesini güncelle (alınan ödeme borcu azaltır)
        musteri.bakiye -= tutar
        print(f"DEBUG: Müşteri '{musteri.ad}' bakiyesi {tutar} düşüldü. Yeni bakiye: {musteri.bakiye}")
        
        oturum.commit()
        print(f"BİLGİ: Müşteri (ID: {musteri_id}) için {tutar:.2f} TL ödeme ({odeme_yontemi}) başarıyla kaydedildi (Ödeme ID: {yeni_odeme.id}).")
        log_aktivite(None, LOG_ACTION_CUSTOMER_PAYMENT, f"Müşteri ödemesi alındı: Müşteri ID: {musteri_id}, Tutar: {tutar:.2f}, Yöntem: {odeme_yontemi}")
        return yeni_odeme.id
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Müşteri ödemesi kaydedilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== musteri_odeme_kaydet FONKSİYONU BİTİŞİ =====

# ===== musteri_hesap_ekstresi_getir FONKSİYONU BAŞLANGICI (YENİ) =====
def musteri_hesap_ekstresi_getir(musteri_id: int, baslangic_tarihi: datetime.date = None, bitis_tarihi: datetime.date = None) -> list[dict]:
    """
    Müşterinin hesap hareketlerini (satışlar ve ödemeler) getirir.
    Args:
        musteri_id (int): Ekstresi görüntülenecek müşteri ID'si.
        baslangic_tarihi (datetime.date, optional): Filtre başlangıç tarihi. Defaults to None.
        bitis_tarihi (datetime.date, optional): Filtre bitiş tarihi. Defaults to None.
    Returns:
        list: Hesap hareketlerini içeren sözlük listesi.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    ledger = []
    try:
        bitis_tarihi_dahil = bitis_tarihi + datetime.timedelta(days=1) if bitis_tarihi else None

        # Satışları (Borç) al
        satis_sorgu = oturum.query(Satis.id.label('id'), Satis.tarih.label('tarih'), Satis.toplam_tutar.label('tutar'),
                                    func.lit('Satış').label('tip'), func.concat('Fiş No: ', Satis.id).label('aciklama')
        ).filter(
            Satis.musteri_id == musteri_id,
            Satis.durum == 'tamamlandi' # Sadece tamamlanmış satışlar
        )
        if baslangic_tarihi:
            satis_sorgu = satis_sorgu.filter(Satis.tarih >= baslangic_tarihi)
        if bitis_tarihi_dahil:
            satis_sorgu = satis_sorgu.filter(Satis.tarih < bitis_tarihi_dahil)
        
        for row in satis_sorgu.all():
            ledger.append({
                'id': row.id,
                'tarih': row.tarih,
                'tip': row.tip,
                'aciklama': row.aciklama,
                'borc': row.tutar,
                'alacak': None
            })

        # Müşteri Ödemelerini (Alacak) al
        odeme_sorgu = oturum.query(MusteriOdeme.id.label('id'), MusteriOdeme.tarih.label('tarih'), MusteriOdeme.tutar.label('tutar'),
                                    func.lit('Ödeme').label('tip'), func.concat(MusteriOdeme.odeme_yontemi, ' - ', func.coalesce(MusteriOdeme.notlar, '')).label('aciklama')
        ).filter(
            MusteriOdeme.musteri_id == musteri_id
        )
        if baslangic_tarihi:
            odeme_sorgu = odeme_sorgu.filter(MusteriOdeme.tarih >= baslangic_tarihi)
        if bitis_tarihi_dahil:
            odeme_sorgu = odeme_sorgu.filter(MusteriOdeme.tarih < bitis_tarihi_dahil)
        
        for row in odeme_sorgu.all():
            ledger.append({
                'id': row.id,
                'tarih': row.tarih,
                'tip': row.tip,
                'aciklama': row.aciklama,
                'borc': None,
                'alacak': row.tutar
            })

        # Tarihe göre sırala
        ledger.sort(key=lambda x: x['tarih'] if x['tarih'] else datetime.datetime.min)
        print(f"DEBUG: Müşteri (ID: {musteri_id}) için hesap ekstresi başarıyla alındı. Toplam {len(ledger)} hareket.")
        return ledger
    except Exception as e:
        print(f"HATA: Müşteri hesap ekstresi getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== musteri_hesap_ekstresi_getir FONKSİYONU BİTİŞİ =====

# ===== musteri_kuponlarini_getir FONKSİYONU BAŞLANGICI (YENİ) =====
def musteri_kuponlarini_getir(musteri_id: int) -> list[MusteriKupon]:
    """
    Müşterinin kullanılabilir aktif kuponlarını getirir.
    Args:
        musteri_id (int): Kuponları getirilecek müşteri ID'si.
    Returns:
        list: MusteriKupon nesnelerinden oluşan bir liste.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        today = datetime.datetime.utcnow().date() # Sadece tarih kısmını al
        kuponlar = oturum.query(MusteriKupon).options(joinedload(MusteriKupon.kupon)).filter(
            MusteriKupon.musteri_id == musteri_id,
            MusteriKupon.durum == 'kullanilabilir',
            MusteriKupon.kupon.has(Kupon.aktif == True), # İlişkili kuponun aktif olması
            or_(MusteriKupon.son_kullanma_tarihi == None, MusteriKupon.son_kullanma_tarihi >= today)
        ).order_by(MusteriKupon.son_kullanma_tarihi.asc()).all()
        print(f"DEBUG: Müşteri (ID: {musteri_id}) için {len(kuponlar)} adet kupon bulundu.")
        return kuponlar
    except Exception as e:
        print(f"HATA: Müşteri kuponları getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== musteri_kuponlarini_getir FONKSİYONU BİTİŞİ =====

# ===== musteri_bakiye_getir FONKSİYONU BAŞLANGICI (YENİ) =====
def musteri_bakiye_getir(musteri_id: int) -> Decimal | None:
    """
    Müşterinin mevcut bakiyesini getirir.
    Args:
        musteri_id (int): Bakiyesi getirilecek müşteri ID'si.
    Returns:
        Decimal | None: Müşterinin bakiyesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        musteri = oturum.query(Musteri).filter(Musteri.id == musteri_id).first()
        if musteri:
            return musteri.bakiye
        else:
            print(f"UYARI: Müşteri (ID: {musteri_id}) bulunamadığı için bakiye alınamadı.")
            return None
    except Exception as e:
        print(f"HATA: Müşteri (ID: {musteri_id}) bakiyesi getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== musteri_bakiye_getir FONKSİYONU BİTİŞİ =====

# ===== sadakat_puani_ekle FONKSİYONU BAŞLANGICI (YENİ) =====
def sadakat_puani_ekle(musteri_id: int, puan_miktari: int) -> bool:
    """
    Müşterinin sadakat puanını artırır.
    Args:
        musteri_id (int): Puan eklenecek müşteri ID'si.
        puan_miktari (int): Eklenecek puan miktarı.
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        ValueError: Puan miktarı negatifse veya müşteri bulunamazsa.
        Exception: Diğer veritabanı hatalarında.
    """
    if puan_miktari <= 0:
        raise ValueError("Eklenecek puan miktarı pozitif olmalıdır.")

    oturum = OturumYerel()
    try:
        musteri = oturum.query(Musteri).filter(Musteri.id == musteri_id).first()
        if not musteri:
            raise ValueError(f"Müşteri (ID: {musteri_id}) bulunamadı.")
        
        musteri.sadakat_puani += puan_miktari
        oturum.commit()
        print(f"DEBUG: Müşteri '{musteri.ad}' için {puan_miktari} sadakat puanı eklendi. Yeni puan: {musteri.sadakat_puani}")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Sadakat puanı eklenirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== sadakat_puani_ekle FONKSİYONU BİTİŞİ =====

# ===== kupon_kullanildi_olarak_isaretle FONKSİYONU BAŞLANGICI (YENİ) =====
def kupon_kullanildi_olarak_isaretle(musteri_kupon_id: int, satis_id: int) -> bool:
    """
    Müşteri kuponunu kullanıldı olarak işaretler.
    Args:
        musteri_kupon_id (int): Kullanılan müşteri kuponunun ID'si.
        satis_id (int): Kuponun kullanıldığı satışın ID'si.
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        ValueError: Kupon bulunamazsa.
        Exception: Diğer veritabanı hatalarında.
    """
    oturum = OturumYerel()
    try:
        musteri_kupon = oturum.query(MusteriKupon).filter(MusteriKupon.id == musteri_kupon_id, MusteriKupon.durum == 'kullanilabilir').first()
        if not musteri_kupon:
            raise ValueError(f"Müşteri kuponu (ID: {musteri_kupon_id}) bulunamadı veya zaten kullanılmış/geçersiz.")
        
        musteri_kupon.durum = 'kullanildi'
        musteri_kupon.kullanilan_satis_id = satis_id
        musteri_kupon.kullanilan_tarih = datetime.datetime.utcnow()
        oturum.commit()
        print(f"DEBUG: Müşteri kuponu (ID: {musteri_kupon_id}) başarıyla kullanıldı olarak işaretlendi.")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Kupon kullanıldı olarak işaretlenirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== kupon_kullanildi_olarak_isaretle FONKSİYONU BİTİŞİ =====

# ===== kupon_kullanilabilir_yap FONKSİYONU BAŞLANGICI (YENİ) =====
def kupon_kullanilabilir_yap(musteri_kupon_id: int) -> bool:
    """
    Kullanılmış bir müşteri kuponunu tekrar kullanılabilir yapar (iade durumunda).
    Args:
        musteri_kupon_id (int): Tekrar kullanılabilir yapılacak müşteri kuponunun ID'si.
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        ValueError: Kupon bulunamazsa.
        Exception: Diğer veritabanı hatalarında.
    """
    oturum = OturumYerel()
    try:
        musteri_kupon = oturum.query(MusteriKupon).filter(MusteriKupon.id == musteri_kupon_id, MusteriKupon.durum == 'kullanildi').first()
        if not musteri_kupon:
            print(f"UYARI: Müşteri kuponu (ID: {musteri_kupon_id}) bulunamadı veya zaten kullanılabilir durumda.")
            return False
        
        musteri_kupon.durum = 'kullanilabilir'
        musteri_kupon.kullanilan_satis_id = None
        musteri_kupon.kullanilan_tarih = None
        oturum.commit()
        print(f"DEBUG: Müşteri kuponu (ID: {musteri_kupon_id}) başarıyla tekrar kullanılabilir yapıldı.")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Kupon tekrar kullanılabilir yapılırken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== kupon_kullanilabilir_yap FONKSİYONU BİTİŞİ =====
