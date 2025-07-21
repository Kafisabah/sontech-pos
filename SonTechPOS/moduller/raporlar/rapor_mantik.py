# Dosya Adı: moduller/raporlar/rapor_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 14:00
# Yapılan İşlem: Günlük satış özeti, en çok satanlar (adet/ciro), kâr/zarar ve SKT raporları eklendi.

from cekirdek.veritabani_yonetimi import OturumYerel, Satis, SatisKalemi, Urun, AlisKalemi, Alis, Marka
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import joinedload
from decimal import Decimal, InvalidOperation
import datetime

# ===== gunluk_satis_ozeti_getir FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def gunluk_satis_ozeti_getir(sube_id: int, baslangic_tarihi: datetime.date, bitis_tarihi: datetime.date) -> list[dict]:
    """
    Belirtilen tarih aralığı ve şube için günlük satış özetini çeker.
    Returns:
        list: Her gün için tarih, toplam işlem sayısı ve toplam ciro içeren sözlük listesi döndürür.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        # Bitiş tarihini de sorguya dahil etmek için bir gün ekliyoruz.
        bitis_tarihi_dahil = bitis_tarihi + datetime.timedelta(days=1)

        sonuclar = oturum.query(
            func.date(Satis.tarih).label('gun'),
            func.count(Satis.id).label('islem_sayisi'),
            func.sum(Satis.toplam_tutar).label('toplam_ciro')
        ).filter(
            Satis.sube_id == sube_id,
            Satis.durum == 'tamamlandi', # Sadece tamamlanmış satışları al
            Satis.tarih >= baslangic_tarihi,
            Satis.tarih < bitis_tarihi_dahil
        ).group_by('gun').order_by('gun').all()
        
        # Sonuçları sözlük olarak döndür
        rapor_verisi = []
        for row in sonuclar:
            rapor_verisi.append({
                'gun': row.gun,
                'islem_sayisi': row.islem_sayisi,
                'toplam_ciro': row.toplam_ciro
            })
        print(f"DEBUG: Günlük satış özeti başarıyla alındı. Toplam {len(rapor_verisi)} gün.")
        return rapor_verisi
    except Exception as e:
        print(f"HATA: Günlük satış özeti getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== gunluk_satis_ozeti_getir FONKSİYONU BİTİŞİ =====

# ===== en_cok_satan_urunler_adet_getir FONKSİYONU BAŞLANGICI (YENİ) =====
def en_cok_satan_urunler_adet_getir(sube_id: int, limit: int = 10, baslangic_tarihi: datetime.date = None, bitis_tarihi: datetime.date = None) -> list[dict]:
    """
    Belirtilen tarih aralığında en çok satan ürünleri (adet bazında) getirir.
    Args:
        sube_id (int): Şube ID'si.
        limit (int): Gösterilecek ürün sayısı limiti.
        baslangic_tarihi (datetime.date, optional): Filtre başlangıç tarihi. Defaults to None.
        bitis_tarihi (datetime.date, optional): Filtre bitiş tarihi. Defaults to None.
    Returns:
        list: Her ürün için ID, barkod, ad ve toplam satış adedi içeren sözlük listesi.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        bitis_tarihi_dahil = bitis_tarihi + datetime.timedelta(days=1) if bitis_tarihi else None

        sorgu = oturum.query(
            Urun.id.label('urun_id'),
            Urun.barkod.label('barkod'),
            Urun.ad.label('ad'),
            func.sum(SatisKalemi.miktar).label('toplam_satilan_adet')
        ).join(SatisKalemi).join(Satis).filter(
            Satis.sube_id == sube_id,
            Satis.durum == 'tamamlandi'
        )
        if baslangic_tarihi:
            sorgu = sorgu.filter(Satis.tarih >= baslangic_tarihi)
        if bitis_tarihi_dahil:
            sorgu = sorgu.filter(Satis.tarih < bitis_tarihi_dahil)
        
        sorgu = sorgu.group_by(Urun.id, Urun.barkod, Urun.ad).order_by(func.sum(SatisKalemi.miktar).desc()).limit(limit)
        
        rapor_verisi = []
        for row in sorgu.all():
            rapor_verisi.append({
                'urun_id': row.urun_id,
                'barkod': row.barkod,
                'ad': row.ad,
                'toplam_satilan_adet': row.toplam_satilan_adet
            })
        print(f"DEBUG: En çok satan ürünler (adet) raporu başarıyla alındı. Toplam {len(rapor_verisi)} ürün.")
        return rapor_verisi
    except Exception as e:
        print(f"HATA: En çok satan ürünler (adet) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== en_cok_satan_urunler_adet_getir FONKSİYONU BİTİŞİ =====

# ===== en_cok_satan_urunler_ciro_getir FONKSİYONU BAŞLANGICI (YENİ) =====
def en_cok_satan_urunler_ciro_getir(sube_id: int, limit: int = 10, baslangic_tarihi: datetime.date = None, bitis_tarihi: datetime.date = None) -> list[dict]:
    """
    Belirtilen tarih aralığında en çok ciro yapan ürünleri getirir.
    Args:
        sube_id (int): Şube ID'si.
        limit (int): Gösterilecek ürün sayısı limiti.
        baslangic_tarihi (datetime.date, optional): Filtre başlangıç tarihi. Defaults to None.
        bitis_tarihi (datetime.date, optional): Filtre bitiş tarihi. Defaults to None.
    Returns:
        list: Her ürün için ID, barkod, ad ve toplam ciro içeren sözlük listesi.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        bitis_tarihi_dahil = bitis_tarihi + datetime.timedelta(days=1) if bitis_tarihi else None

        sorgu = oturum.query(
            Urun.id.label('urun_id'),
            Urun.barkod.label('barkod'),
            Urun.ad.label('ad'),
            func.sum(SatisKalemi.toplam_fiyat).label('toplam_ciro') # toplam_fiyat sütununu kullan
        ).join(SatisKalemi).join(Satis).filter(
            Satis.sube_id == sube_id,
            Satis.durum == 'tamamlandi'
        )
        if baslangic_tarihi:
            sorgu = sorgu.filter(Satis.tarih >= baslangic_tarihi)
        if bitis_tarihi_dahil:
            sorgu = sorgu.filter(Satis.tarih < bitis_tarihi_dahil)
        
        sorgu = sorgu.group_by(Urun.id, Urun.barkod, Urun.ad).order_by(func.sum(SatisKalemi.toplam_fiyat).desc()).limit(limit)
        
        rapor_verisi = []
        for row in sorgu.all():
            rapor_verisi.append({
                'urun_id': row.urun_id,
                'barkod': row.barkod,
                'ad': row.ad,
                'toplam_ciro': row.toplam_ciro
            })
        print(f"DEBUG: En çok ciro yapan ürünler raporu başarıyla alındı. Toplam {len(rapor_verisi)} ürün.")
        return rapor_verisi
    except Exception as e:
        print(f"HATA: En çok ciro yapan ürünler getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== en_cok_satan_urunler_ciro_getir FONKSİYONU BİTİŞİ =====

# ===== kar_zarar_raporu_getir FONKSİYONU BAŞLANGICI (YENİ) =====
def kar_zarar_raporu_getir(sube_id: int, baslangic_tarihi: datetime.date = None, bitis_tarihi: datetime.date = None) -> list[dict]:
    """
    Belirtilen tarih aralığı ve şube için ürün bazlı tahmini kâr/zarar verilerini hesaplar.
    Maliyet, ürünün kayıtlı son alış fiyatına göre tahmin edilir.
    Args:
        sube_id (int): Şube ID'si.
        baslangic_tarihi (datetime.date, optional): Filtre başlangıç tarihi. Defaults to None.
        bitis_tarihi (datetime.date, optional): Filtre bitiş tarihi. Defaults to None.
    Returns:
        list: Her ürün için bilgileri içeren sözlük listesi.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    rapor_verisi = []
    try:
        bitis_tarihi_dahil = bitis_tarihi + datetime.timedelta(days=1) if bitis_tarihi else None

        # Satılan ürünleri ve toplam satış tutarlarını al
        satis_kalemleri_sorgu = oturum.query(
            SatisKalemi.urun_id.label('urun_id'),
            Urun.barkod.label('barkod'),
            Urun.ad.label('ad'),
            func.sum(SatisKalemi.miktar).label('toplam_satilan_adet'),
            func.sum(SatisKalemi.toplam_fiyat).label('toplam_ciro')
        ).join(Urun).join(Satis).filter(
            Satis.sube_id == sube_id,
            Satis.durum == 'tamamlandi'
        )
        if baslangic_tarihi:
            satis_kalemleri_sorgu = satis_kalemleri_sorgu.filter(Satis.tarih >= baslangic_tarihi)
        if bitis_tarihi_dahil:
            satis_kalemleri_sorgu = satis_kalemleri_sorgu.filter(Satis.tarih < bitis_tarihi_dahil)
        
        satis_kalemleri_sorgu = satis_kalemleri_sorgu.group_by(SatisKalemi.urun_id, Urun.barkod, Urun.ad).all()

        for row in satis_kalemleri_sorgu:
            urun_id = row.urun_id
            toplam_satilan_adet = row.toplam_satilan_adet
            toplam_ciro = row.toplam_ciro

            # Ürünün son alış fiyatını al
            # Bunu doğrudan Urun modelindeki alis_fiyati sütunundan alabiliriz,
            # veya AlisKalemi tablosundan en güncelini çekebiliriz.
            # Urun modelindeki alis_fiyati "son bilinen alış fiyatı" olduğu için onu kullanalım.
            urun_detay = oturum.query(Urun).filter(Urun.id == urun_id).first()
            son_alis_fiyati = urun_detay.alis_fiyati if urun_detay else Decimal('0.00')

            tahmini_maliyet = toplam_satilan_adet * son_alis_fiyati
            tahmini_kar = toplam_ciro - tahmini_maliyet

            rapor_verisi.append({
                'urun_id': urun_id,
                'barkod': row.barkod,
                'ad': row.ad,
                'toplam_satilan_adet': toplam_satilan_adet,
                'toplam_ciro': toplam_ciro,
                'tahmini_maliyet': tahmini_maliyet,
                'tahmini_kar': tahmini_kar
            })
        print(f"DEBUG: Kâr/Zarar raporu başarıyla oluşturuldu. Toplam {len(rapor_verisi)} ürün.")
        return rapor_verisi
    except Exception as e:
        print(f"HATA: Kâr/Zarar raporu getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== kar_zarar_raporu_getir FONKSİYONU BİTİŞİ =====

# ===== skt_raporu_getir FONKSİYONU BAŞLANGICI (YENİ) =====
def skt_raporu_getir(sube_id: int, days_threshold: int) -> list[dict]:
    """
    SKT'si bugün veya belirtilen gün sayısı içinde dolacak olan
    alış kalemlerini getirir.
    Args:
        sube_id (int): Şube ID'si (şimdilik kullanılmıyor ama gelecekte lazım olabilir)
        days_threshold (int): Kaç gün sonrasına kadar kontrol edileceği.
    Returns:
        list: İlgili bilgileri içeren sözlük listesi.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        today = datetime.date.today()
        end_date_threshold = today + datetime.timedelta(days=days_threshold)

        sorgu = oturum.query(
            AlisKalemi.id.label('alis_kalemi_id'), # Alış kalemi ID'si
            Alis.id.label('alis_id'), # Alış ID'si
            AlisKalemi.urun_id.label('urun_id'),
            Urun.ad.label('urun_adi'),
            Marka.ad.label('marka_adi'),
            AlisKalemi.miktar.label('miktar'),
            AlisKalemi.son_kullanma_tarihi.label('skt')
        ).join(Urun).outerjoin(Marka).join(Alis).filter(
            AlisKalemi.son_kullanma_tarihi != None, # SKT'si olanlar
            AlisKalemi.son_kullanma_tarihi <= end_date_threshold
        ).order_by(AlisKalemi.son_kullanma_tarihi.asc(), Urun.ad.asc())
        
        rapor_verisi = []
        for row in sorgu.all():
            expiry_date = row.skt.date() if isinstance(row.skt, datetime.datetime) else row.skt
            remaining_days = (expiry_date - today).days if expiry_date else None
            
            rapor_verisi.append({
                'alis_kalemi_id': row.alis_kalemi_id,
                'alis_id': row.alis_id,
                'urun_id': row.urun_id,
                'urun_adi': row.urun_adi,
                'marka_adi': row.marka_adi,
                'miktar': row.miktar,
                'skt': expiry_date,
                'kalan_gun': remaining_days
            })
        print(f"DEBUG: SKT raporu başarıyla oluşturuldu. Toplam {len(rapor_verisi)} kayıt.")
        return rapor_verisi
    except Exception as e:
        print(f"HATA: SKT raporu getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== skt_raporu_getir FONKSİYONU BİTİŞİ =====
