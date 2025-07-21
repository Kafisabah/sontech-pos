# Dosya Adı: moduller/vardiya/vardiya_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 18:10
# Yapılan İşlem: rich kütüphanesi bağımlılıkları kaldırıldı, standart print kullanıldı.
#                Hata yönetimi Python'ın yerleşik istisnalarına uyarlandı.
#                Loglama entegrasyonu sağlandı.

from cekirdek.veritabani_yonetimi import OturumYerel, Vardiya, Kullanici, Satis, Odeme, MusteriOdeme
from sqlalchemy.orm import joinedload
from sqlalchemy import func, and_
import datetime
from decimal import Decimal
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_SHIFT_START, LOG_ACTION_SHIFT_END

# ===== vardiya_baslat FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def vardiya_baslat(kullanici_id: int, baslangic_kasa_nakiti: Decimal = Decimal('0.00')) -> int | None:
    """
    Belirtilen kullanıcı için yeni bir vardiya başlatır.
    Kullanıcının zaten aktif bir vardiyası varsa hata verir.
    Args:
        kullanici_id (int): Vardiyayı başlatan kullanıcı ID'si.
        baslangic_kasa_nakiti (Decimal, optional): Vardiya başı kasa nakiti. Defaults to Decimal('0.00').
    Returns:
        int | None: Başarıyla başlatılırsa yeni vardiya ID'si, yoksa None.
    Raises:
        ValueError: Kullanıcının zaten aktif bir vardiyası varsa.
        Exception: Diğer veritabanı hatalarında.
    """
    oturum = OturumYerel()
    try:
        # Kullanıcının aktif vardiyası var mı kontrol et
        aktif_vardiya = oturum.query(Vardiya).filter(
            Vardiya.kullanici_id == kullanici_id,
            Vardiya.aktif == True,
            Vardiya.bitis_zamani == None
        ).first()
        if aktif_vardiya:
            raise ValueError(f"Bu kullanıcının (ID: {kullanici_id}) zaten aktif bir vardiyası (ID: {aktif_vardiya.id}) var.")

        yeni_vardiya = Vardiya(
            kullanici_id=kullanici_id,
            baslangic_zamani=datetime.datetime.utcnow(),
            baslangic_kasa_nakiti=baslangic_kasa_nakiti,
            aktif=True
        )
        oturum.add(yeni_vardiya)
        oturum.commit()
        print(f"DEBUG: Kullanıcı ID {kullanici_id} için yeni vardiya (ID: {yeni_vardiya.id}) başarıyla başlatıldı.")
        log_aktivite(kullanici_id, LOG_ACTION_SHIFT_START, f"Vardiya başlatıldı: ID: {yeni_vardiya.id}, Başlangıç Kasa: {baslangic_kasa_nakiti:.2f} TL")
        return yeni_vardiya.id
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Vardiya başlatma hatası: {e}")
        raise e
    finally:
        oturum.close()

# ===== Aktif Vardiyayı Getirme =====
def aktif_vardiya_getir(kullanici_id: int) -> Vardiya | None:
    """
    Belirtilen kullanıcının şu anda aktif olan vardiyasını getirir.
    Args:
        kullanici_id (int): Kullanıcı ID'si.
    Returns:
        Vardiya | None: Aktif vardiya nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        vardiya = oturum.query(Vardiya).options(joinedload(Vardiya.kullanici)).filter(
            Vardiya.kullanici_id == kullanici_id,
            Vardiya.aktif == True,
            Vardiya.bitis_zamani == None
        ).first()
        return vardiya
    except Exception as e:
        print(f"HATA: Aktif vardiya getirme hatası (Kullanıcı ID: {kullanici_id}): {e}")
        raise e
    finally:
        oturum.close()

# ===== Vardiya Bitirme =====
def vardiya_bitir(vardiya_id: int, bitis_kasa_nakiti: Decimal = None, notlar: str = None, kullanici_id: int = None) -> bool:
    """
    Belirtilen vardiyayı bitirir ve hesaplanan özet bilgileri kaydeder.
    Args:
        vardiya_id (int): Bitirilecek vardiya ID'si.
        bitis_kasa_nakiti (Decimal, optional): Vardiya sonu sayılan kasa nakiti.
        notlar (str, optional): Vardiya notları.
        kullanici_id (int, optional): Vardiyayı bitiren kullanıcının ID'si (loglama için).
    Returns:
        bool: Başarılı olursa True, değilse False.
    Raises:
        ValueError: Vardiya bulunamazsa veya zaten bitirilmişse.
        Exception: Diğer veritabanı hatalarında.
    """
    oturum = OturumYerel()
    try:
        vardiya = oturum.query(Vardiya).filter(
            Vardiya.id == vardiya_id,
            Vardiya.aktif == True,
            Vardiya.bitis_zamani == None
        ).first()

        if not vardiya:
            raise ValueError(f"Aktif vardiya (ID: {vardiya_id}) bulunamadı veya zaten bitirilmiş.")

        # Vardiya özetini hesapla
        ozet = vardiya_ozeti_hesapla(vardiya_id)
        musteri_odeme_ozeti = vardiya_musteri_odeme_ozeti_hesapla(vardiya_id)

        vardiya.bitis_zamani = datetime.datetime.utcnow()
        vardiya.bitis_kasa_nakiti = bitis_kasa_nakiti
        vardiya.toplam_satis_cirosu = ozet['total_sales']
        vardiya.nakit_satislar = ozet['cash_sales']
        vardiya.kart_satislar = ozet['card_sales']
        vardiya.veresiye_satislar = ozet['veresiye_sales']
        vardiya.alinan_nakit_odemeler = musteri_odeme_ozeti['cash_payments_received']
        vardiya.alinan_kart_odemeler = musteri_odeme_ozeti['card_payments_received']
        
        # Kasa farkı hesaplama (basit örnek)
        beklenen_nakit = vardiya.baslangic_kasa_nakiti + vardiya.nakit_satislar + vardiya.alinan_nakit_odemeler
        if bitis_kasa_nakiti is not None:
            vardiya.hesaplanan_fark = bitis_kasa_nakiti - beklenen_nakit
        else:
            vardiya.hesaplanan_fark = Decimal('0.00')

        vardiya.notlar = notlar
        vardiya.aktif = False # Vardiyayı pasif yap

        oturum.commit()
        print(f"DEBUG: Vardiya (ID: {vardiya_id}) başarıyla bitirildi. Fark: {vardiya.hesaplanan_fark:.2f}₺")
        log_aktivite(kullanici_id, LOG_ACTION_SHIFT_END, f"Vardiya bitirildi: ID: {vardiya.id}, Kasa Farkı: {vardiya.hesaplanan_fark:.2f} TL")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Vardiya bitirme hatası (ID: {vardiya_id}): {e}")
        raise e
    finally:
        oturum.close()

# ===== Vardiya ID ile Getirme =====
def vardiya_getir_by_id(vardiya_id: int) -> Vardiya | None:
    """
    Verilen ID'ye sahip vardiyanın tüm detaylarını getirir (kullanıcı adı dahil).
    Args:
        vardiya_id (int): Vardiya ID'si.
    Returns:
        Vardiya | None: Vardiya nesnesi veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        return oturum.query(Vardiya).options(joinedload(Vardiya.kullanici)).filter(Vardiya.id == vardiya_id).first()
    except Exception as e:
        print(f"HATA: Vardiya detayı getirme hatası (ID: {vardiya_id}): {e}")
        raise e
    finally:
        oturum.close()

# ===== Vardiya Özeti Hesaplama Fonksiyonları (Z Raporu için) =====
def vardiya_ozeti_hesapla(vardiya_id: int) -> dict:
    """
    Belirli bir vardiyadaki satışların özetini (ödeme türüne göre) hesaplar.
    Args:
        vardiya_id (int): Vardiya ID'si.
    Returns:
        dict: Satış özetini içeren sözlük.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    summary = {
        'total_sales': Decimal('0.00'),
        'cash_sales': Decimal('0.00'),
        'card_sales': Decimal('0.00'),
        'veresiye_sales': Decimal('0.00'),
        'total_discount': Decimal('0.00'),
        'total_promotion_discount': Decimal('0.00')
    }
    try:
        # Toplam satış, indirimler
        sales_data = oturum.query(
            func.sum(Satis.toplam_tutar).label('total_sales_amount'),
            func.sum(Satis.indirim_tutari).label('total_discount_amount'),
            func.sum(Satis.promosyon_indirim_tutari).label('total_promo_discount')
        ).filter(
            Satis.vardiya_id == vardiya_id,
            Satis.durum == 'tamamlandi'
        ).first()

        if sales_data:
            summary['total_sales'] = sales_data.total_sales_amount or Decimal('0.00')
            summary['total_discount'] = sales_data.total_discount_amount or Decimal('0.00')
            summary['total_promotion_discount'] = sales_data.total_promo_discount or Decimal('0.00')

        # Ödeme yöntemlerine göre satışlar
        payments_data = oturum.query(
            Odeme.yontem,
            func.sum(Odeme.tutar).label('total_paid')
        ).join(Satis).filter(
            Satis.vardiya_id == vardiya_id,
            Satis.durum == 'tamamlandi',
            Odeme.durum == 'tamamlandi' # Sadece tamamlanmış ödemeleri al
        ).group_by(Odeme.yontem).all()

        for payment in payments_data:
            method = payment.yontem
            total_paid = payment.total_paid or Decimal('0.00')
            if method == 'Nakit':
                summary['cash_sales'] = total_paid
            elif method == 'Kredi Kartı':
                summary['card_sales'] = total_paid
            elif method == 'Veresiye':
                summary['veresiye_sales'] = total_paid

        print(f"DEBUG: Vardiya {vardiya_id} için satış özeti: {summary}")
        return summary
    except Exception as e:
        print(f"HATA: Vardiya satış özeti alma hatası (Vardiya ID: {vardiya_id}): {e}")
        raise e
    finally:
        oturum.close()

def vardiya_musteri_odeme_ozeti_hesapla(vardiya_id: int) -> dict:
    """
    Belirli bir vardiyada alınan müşteri ödemelerinin özetini (ödeme türüne göre) hesaplar.
    Args:
        vardiya_id (int): Vardiya ID'si.
    Returns:
        dict: Müşteri ödeme özetini içeren sözlük.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    summary = {
        'cash_payments_received': Decimal('0.00'),
        'card_payments_received': Decimal('0.00')
    }
    try:
        payments_data = oturum.query(
            MusteriOdeme.odeme_yontemi,
            func.sum(MusteriOdeme.tutar).label('total_received')
        ).filter(
            MusteriOdeme.vardiya_id == vardiya_id
        ).group_by(MusteriOdeme.odeme_yontemi).all()

        for payment in payments_data:
            method = payment.odeme_yontemi
            total_received = payment.total_received or Decimal('0.00')
            if method == 'Nakit':
                summary['cash_payments_received'] = total_received
            elif method == 'Kredi Kartı':
                summary['card_payments_received'] = total_received
        
        print(f"DEBUG: Vardiya {vardiya_id} için müşteri ödeme özeti: {summary}")
        return summary
    except Exception as e:
        print(f"UYARI: Vardiya müşteri ödeme özeti alınamadı (Vardiya ID: {vardiya_id}). Hata: {e}")
        # Hata durumunda boş özet döndür, çünkü bu opsiyonel bir bilgi olabilir
        return summary
    finally:
        oturum.close()
