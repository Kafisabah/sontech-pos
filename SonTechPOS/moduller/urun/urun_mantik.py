# Dosya Adı: moduller/urun/urun_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 14:50
# Yapılan İşlem: 'LOG_ACTION_PRODUCT_LABEL_PRINT' sabiti import edildi.

from cekirdek.veritabani_yonetimi import OturumYerel, Urun, Marka, Kategori, Stok, Fiyat, SatisKalemi, AlisKalemi, Tedarikci, Alis
from sqlalchemy.orm import joinedload
from sqlalchemy import or_, func
from decimal import Decimal
import datetime
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_PRODUCT_ADD, LOG_ACTION_PRODUCT_UPDATE, LOG_ACTION_PRODUCT_STATUS_CHANGE, LOG_ACTION_PRODUCT_LABEL_PRINT # Yeni sabit eklendi

# ===== urunleri_getir FONKSİYONU (Aynı kalıyor) =====
def urunleri_getir(sube_id: int):
    oturum = OturumYerel()
    try:
        # Ürünleri marka ve kategori bilgileriyle birlikte yükle
        urunler = oturum.query(Urun).options(
            joinedload(Urun.marka),
            joinedload(Urun.kategori)
        ).all()
        
        # Her ürün için ilgili şubeye ait stok ve fiyat bilgilerini ekle
        for urun in urunler:
            urun.sube_stok = oturum.query(Stok).filter(Stok.urun_id == urun.id, Stok.sube_id == sube_id).first()
            urun.sube_fiyat = oturum.query(Fiyat).filter(Fiyat.urun_id == urun.id, Fiyat.sube_id == sube_id).first()
        return urunler
    except Exception as e:
        print(f"HATA: Ürünler getirilirken bir sorun oluştu: {e}")
        raise e
    finally: oturum.close()

# ===== marka_getir_veya_olustur FONKSİYONU (Aynı kalıyor) =====
def marka_getir_veya_olustur(oturum, marka_adi: str):
    if not marka_adi: return None
    marka = oturum.query(Marka).filter(Marka.ad == marka_adi).first()
    if not marka:
        marka = Marka(ad=marka_adi)
        oturum.add(marka)
        oturum.flush() # ID'yi almak için
        print(f"DEBUG: Yeni marka oluşturuldu: {marka_adi} (ID: {marka.id})")
    return marka

# ===== kategori_getir_veya_olustur FONKSİYONU (Aynı kalıyor) =====
def kategori_getir_veya_olustur(oturum, kategori_adi: str):
    if not kategori_adi: return None
    kategori = oturum.query(Kategori).filter(Kategori.ad == kategori_adi).first()
    if not kategori:
        kategori = Kategori(ad=kategori_adi)
        oturum.add(kategori)
        oturum.flush() # ID'yi almak için
        print(f"DEBUG: Yeni kategori oluşturuldu: {kategori_adi} (ID: {kategori.id})")
    return kategori

# ===== yeni_urun_ekle FONKSİYONU (Aynı kalıyor) =====
def yeni_urun_ekle(urun_bilgileri: dict, sube_id: int):
    oturum = OturumYerel()
    try:
        marka = marka_getir_veya_olustur(oturum, urun_bilgileri['marka_adi'])
        kategori = kategori_getir_veya_olustur(oturum, urun_bilgileri['kategori_adi'])
        
        # Yeni ürün nesnesini oluştururken tüm yeni alanları dahil et
        yeni_urun = Urun(
            barkod=urun_bilgileri['barkod'],
            ad=urun_bilgileri['ad'],
            birim='Adet', # Varsayılan birim
            aktif=True,
            marka=marka,
            kategori=kategori,
            alis_fiyati=urun_bilgileri.get('alis_fiyati', Decimal('0.00')),
            satis_fiyati=urun_bilgileri.get('satis_fiyati', Decimal('0.00')),
            kdv_orani=urun_bilgileri.get('kdv_orani', Decimal('10.00')),
            min_stok_seviyesi=urun_bilgileri.get('min_stok_seviyesi', 0)
        )
        oturum.add(yeni_urun)
        oturum.flush() # Ürün ID'sini almak için

        # Şubeye özel stok ve fiyat kaydı oluştur
        yeni_fiyat = Fiyat(
            urun_id=yeni_urun.id,
            sube_id=sube_id,
            alis_fiyati=urun_bilgileri.get('alis_fiyati', Decimal('0.00')),
            satis_fiyati=urun_bilgileri.get('satis_fiyati', Decimal('0.00')),
            kdv_orani=urun_bilgileri.get('kdv_orani', Decimal('10.00'))
        )
        oturum.add(yeni_fiyat)
        
        yeni_stok = Stok(
            urun_id=yeni_urun.id,
            sube_id=sube_id,
            miktar=urun_bilgileri.get('miktar', 0),
            min_stok_seviyesi=urun_bilgileri.get('min_stok_seviyesi', 0) # Şube bazlı min stok
        )
        oturum.add(yeni_stok)
        
        oturum.commit()
        print(f"DEBUG: Yeni ürün '{yeni_urun.ad}' başarıyla eklendi.")
        log_aktivite(None, LOG_ACTION_PRODUCT_ADD, f"Yeni ürün eklendi: ID: {yeni_urun.id}, Ad: {yeni_urun.ad}")
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Yeni ürün eklenirken bir hata oluştu: {e}")
        raise
    finally: oturum.close()

# ===== urun_guncelle FONKSİYONU (Aynı kalıyor) =====
def urun_guncelle(urun_id: int, urun_bilgileri: dict, sube_id: int):
    """Mevcut bir ürünü, stok ve fiyat bilgileriyle birlikte günceller."""
    oturum = OturumYerel()
    try:
        urun = oturum.query(Urun).filter(Urun.id == urun_id).first()
        if not urun: raise Exception(f"Güncellenecek ürün (ID: {urun_id}) bulunamadı.")
        
        print(f"DEBUG: Ürün güncelleniyor: {urun.ad}")
        
        # Önceki satış fiyatını kaydet (eğer değişiyorsa)
        if urun.satis_fiyati != urun_bilgileri['satis_fiyati']:
            urun.onceki_satis_fiyati = urun.satis_fiyati
            print(f"DEBUG: '{urun.ad}' için önceki satış fiyatı {urun.onceki_satis_fiyati} olarak kaydedildi.")

        urun.barkod = urun_bilgileri['barkod']
        urun.ad = urun_bilgileri['ad']
        urun.marka = marka_getir_veya_olustur(oturum, urun_bilgileri['marka_adi'])
        urun.kategori = kategori_getir_veya_olustur(oturum, urun_bilgileri['kategori_adi'])
        urun.alis_fiyati = urun_bilgileri.get('alis_fiyati', urun.alis_fiyati)
        urun.satis_fiyati = urun_bilgileri.get('satis_fiyati', urun.satis_fiyati)
        urun.kdv_orani = urun_bilgileri.get('kdv_orani', urun.kdv_orani)
        urun.min_stok_seviyesi = urun_bilgileri.get('min_stok_seviyesi', urun.min_stok_seviyesi)
        
        # Şubeye özel fiyatı güncelle (varsa)
        fiyat = oturum.query(Fiyat).filter_by(urun_id=urun_id, sube_id=sube_id).first()
        if fiyat:
            fiyat.alis_fiyati = urun_bilgileri.get('alis_fiyati', fiyat.alis_fiyati)
            fiyat.satis_fiyati = urun_bilgileri.get('satis_fiyati', fiyat.satis_fiyati)
            fiyat.kdv_orani = urun_bilgileri.get('kdv_orani', fiyat.kdv_orani)
            print(f"DEBUG: Şube {sube_id} için fiyat güncellendi.")
        else:
            # Eğer şubeye özel fiyat yoksa oluştur
            yeni_fiyat = Fiyat(
                urun_id=urun.id,
                sube_id=sube_id,
                alis_fiyati=urun_bilgileri.get('alis_fiyati', Decimal('0.00')),
                satis_fiyati=urun_bilgileri.get('satis_fiyati', Decimal('0.00')),
                kdv_orani=urun_bilgileri.get('kdv_orani', Decimal('10.00'))
            )
            oturum.add(yeni_fiyat)
            print(f"UYARI: Ürün (ID: {urun_id}) için şubeye özel fiyat kaydı bulunamadı, yeni oluşturuldu.")


        # Şubeye özel stoğu güncelle (varsa)
        stok = oturum.query(Stok).filter_by(urun_id=urun_id, sube_id=sube_id).first()
        if stok:
            stok.miktar = urun_bilgileri.get('miktar', stok.miktar)
            stok.min_stok_seviyesi = urun_bilgileri.get('min_stok_seviyesi', stok.min_stok_seviyesi) # Şube bazlı min stok
            print(f"DEBUG: Şube {sube_id} için stok güncellendi.")
        else:
            # Eğer şubeye özel stok yoksa oluştur
            yeni_stok = Stok(
                urun_id=urun.id,
                sube_id=sube_id,
                miktar=urun_bilgileri.get('miktar', 0),
                min_stok_seviyesi=urun_bilgileri.get('min_stok_seviyesi', 0)
            )
            oturum.add(yeni_stok)
            print(f"UYARI: Ürün (ID: {urun_id}) için şubeye özel stok kaydı bulunamadı, yeni oluşturuldu.")
        
        oturum.commit()
        print(f"BİLGİ: '{urun.ad}' ürünü başarıyla güncellendi.")
        log_aktivite(None, LOG_ACTION_PRODUCT_UPDATE, f"Ürün güncellendi: ID: {urun.id}, Ad: {urun.ad}")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Ürün güncellenirken bir sorun oluştu: {e}")
        raise
    finally:
        oturum.close()

# ===== urun_sil FONKSİYONU (Aynı kalıyor) =====
def urun_sil(urun_id: int):
    """Bir ürünü, ilişkili stok ve fiyat kayıtlarıyla birlikte siler."""
    oturum = OturumYerel()
    try:
        # 1. Ürünün hiç satışta kullanılıp kullanılmadığını kontrol et
        satis_sayisi = oturum.query(SatisKalemi).filter(SatisKalemi.urun_id == urun_id).count()
        if satis_sayisi > 0:
            # Ürünü silmek yerine pasif hale getir
            urun = oturum.query(Urun).filter(Urun.id == urun_id).first()
            if urun:
                urun.aktif = False
                oturum.commit()
                print(f"UYARI: Bu ürün satış işlemlerinde kullanıldığı için silinemedi, pasif hale getirildi: '{urun.ad}'")
                log_aktivite(None, LOG_ACTION_PRODUCT_STATUS_CHANGE, f"Ürün pasif hale getirildi (satışta kullanıldığı için silinemedi): ID: {urun.id}, Ad: {urun.ad}")
                return True # İşlem başarılı sayılabilir, çünkü ürün pasif hale getirildi
            else:
                raise Exception(f"Ürün (ID: {urun_id}) bulunamadı, silme/pasifleştirme yapılamadı.")
        
        # 2. Ürünü bul ve sil (eğer satışta kullanılmadıysa)
        urun = oturum.query(Urun).filter(Urun.id == urun_id).first()
        if not urun:
            raise Exception(f"Ürün (ID: {urun_id}) bulunamadı.")
            
        print(f"DEBUG: Ürün siliniyor: {urun.ad}")
        oturum.delete(urun) # Cascade ayarı sayesinde ilişkili kayıtlar da silinecek
        oturum.commit()
        print(f"BİLGİ: '{urun.ad}' ürünü başarıyla silindi.")
        log_aktivite(None, LOG_ACTION_PRODUCT_UPDATE, f"Ürün silindi: ID: {urun.id}, Ad: {urun.ad}")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Ürün silinirken bir sorun oluştu: {e}")
        raise
    finally:
        oturum.close()

# ===== YENİ FONKSİYONLAR BAŞLANGICI =====

def urun_aktif_pasif_yap(urun_id: int, aktif_durum: bool) -> bool:
    """
    Belirtilen ürünün aktiflik durumunu değiştirir.
    Args:
        urun_id (int): Durumu değiştirilecek ürünün ID'si.
        aktif_durum (bool): Ürünün yeni aktiflik durumu (True: aktif, False: pasif).
    Returns:
        bool: İşlem başarılıysa True, değilse False.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        urun = oturum.query(Urun).filter(Urun.id == urun_id).first()
        if not urun:
            print(f"UYARI: Ürün (ID: {urun_id}) bulunamadı, aktif/pasif yapılamadı.")
            return False
        
        if urun.aktif == aktif_durum:
            print(f"BİLGİ: Ürün (ID: {urun_id}) zaten istenen aktiflik durumunda.")
            return True

        urun.aktif = aktif_durum
        oturum.commit()
        durum_str = "aktif" if aktif_durum else "pasif"
        print(f"DEBUG: Ürün '{urun.ad}' (ID: {urun_id}) başarıyla {durum_str} yapıldı.")
        log_aktivite(None, LOG_ACTION_PRODUCT_STATUS_CHANGE, f"Ürün durumu değiştirildi: ID: {urun.id}, Yeni Durum: {durum_str}")
        return True
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Ürün durumu değiştirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

def son_alis_fiyati_getir(urun_id: int) -> Decimal | None:
    """
    Bir ürün için kaydedilmiş son geçerli (NULL olmayan) alış fiyatını getirir.
    Args:
        urun_id (int): Alış fiyatı getirilecek ürünün ID'si.
    Returns:
        Decimal | None: Son alış fiyatı veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        # AlisKalemi ve Alis tablolarını birleştirerek en son alış fiyatını bul
        son_fiyat_kaydi = oturum.query(AlisKalemi).options(joinedload(AlisKalemi.alis)).filter(
            AlisKalemi.urun_id == urun_id,
            AlisKalemi.alis_fiyati != None # NULL olmayan fiyatları al
        ).order_by(Alis.tarih.desc(), AlisKalemi.id.desc()).first() # En son alış tarihine ve sonra ID'ye göre sırala

        if son_fiyat_kaydi:
            print(f"DEBUG: Ürün (ID: {urun_id}) için son alış fiyatı: {son_fiyat_kaydi.alis_fiyati}")
            return son_fiyat_kaydi.alis_fiyati
        else:
            print(f"BİLGİ: Ürün (ID: {urun_id}) için kayıtlı son alış fiyatı bulunamadı.")
            return None
    except Exception as e:
        print(f"HATA: Ürün (ID: {urun_id}) için son alış fiyatı alınırken hata: {e}")
        return None
    finally:
        oturum.close()

def stok_raporu_getir(sube_id: int, kritik_seviye_altinda_olanlar: bool = False, pasif_urunleri_dahil_et: bool = False) -> list[dict]:
    """
    Stok raporu için ürün verilerini getirir (marka adı, kategori adı, min stok dahil).
    Args:
        sube_id (int): Hangi şubenin stokları raporlanacak.
        kritik_seviye_altinda_olanlar (bool): True ise sadece stoğu min_stok_seviyesi altında olanları getirir.
        pasif_urunleri_dahil_et (bool): Pasif ürünleri de rapora dahil et.
    Returns:
        list: Her ürün için bilgileri içeren sözlük listesi.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Urun, Stok, Marka, Kategori).outerjoin(Stok, and_(Stok.urun_id == Urun.id, Stok.sube_id == sube_id)).outerjoin(Marka).outerjoin(Kategori)
        
        filtreler = []
        if not pasif_urunleri_dahil_et:
            filtreler.append(Urun.aktif == True)

        if kritik_seviye_altinda_olanlar:
            # Stok kaydı yoksa veya stok min seviyenin altındaysa
            filtreler.append(or_(Stok.miktar == None, Stok.miktar <= Urun.min_stok_seviyesi))
        
        if filtreler:
            sorgu = sorgu.filter(and_(*filtreler))

        sorgu = sorgu.order_by(Urun.ad.asc())
        sonuclar = sorgu.all()

        rapor_verisi = []
        for urun, stok, marka, kategori in sonuclar:
            rapor_verisi.append({
                'id': urun.id,
                'barkod': urun.barkod,
                'ad': urun.ad,
                'marka_adi': marka.ad if marka else "N/A",
                'kategori_adi': kategori.ad if kategori else "N/A",
                'mevcut_stok': stok.miktar if stok else Decimal('0.00'),
                'min_stok_seviyesi': urun.min_stok_seviyesi,
                'aktif': urun.aktif
            })
        print(f"DEBUG: Stok raporu başarıyla oluşturuldu. Toplam {len(rapor_verisi)} ürün.")
        return rapor_verisi
    except Exception as e:
        print(f"HATA: Stok raporu getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

def siparis_onerisi_getir(sube_id: int) -> list[dict]:
    """
    Minimum stok seviyesinin altına düşmüş aktif ürünler için sipariş öneri verilerini toplar.
    Veriler: barkod, ad, mevcut stok, min stok, son alış fiyatı, son tedarikçi, tahmini tükenme süresi (gün).
    Args:
        sube_id (int): Hangi şubenin stokları için öneri yapılacak.
    Returns:
        list: Her ürün için bilgileri içeren sözlük listesi.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        # Kritik seviyenin altında olan ürünleri çek
        kritik_urunler = oturum.query(Urun, Stok).outerjoin(Stok, and_(Stok.urun_id == Urun.id, Stok.sube_id == sube_id)).filter(
            Urun.aktif == True,
            or_(Stok.miktar == None, Stok.miktar <= Urun.min_stok_seviyesi)
        ).order_by(Urun.ad.asc()).all()

        oneriler = []
        for urun, stok in kritik_urunler:
            mevcut_stok = stok.miktar if stok else Decimal('0.00')
            min_stok = urun.min_stok_seviyesi

            son_alis_fiyati = son_alis_fiyati_getir(urun.id) # Kendi fonksiyonumuzu kullan
            
            son_tedarikci_adi = "N/A"
            tahmini_tukenme_suresi = "N/A"

            # Son alış işlemini bul ve tedarikçi bilgisini al
            son_alis_kaydi = oturum.query(AlisKalemi).options(joinedload(AlisKalemi.alis).joinedload(Alis.tedarikci)).filter(
                AlisKalemi.urun_id == urun.id
            ).order_by(Alis.tarih.desc(), AlisKalemi.id.desc()).first()

            if son_alis_kaydi and son_alis_kaydi.alis and son_alis_kaydi.alis.tedarikci:
                son_tedarikci_adi = son_alis_kaydi.alis.tedarikci.ad
            
            # Tahmini tükenme süresi hesaplama (basit bir yaklaşım, daha karmaşık olabilir)
            # Son X gündeki ortalama satış miktarı / mevcut stok
            # Bu rapor için şimdilik bu alanı N/A bırakabiliriz veya manuel bir değer atayabiliriz.

            oneriler.append({
                'id': urun.id,
                'barkod': urun.barkod,
                'ad': urun.ad,
                'mevcut_stok': mevcut_stok,
                'min_stok_seviyesi': min_stok,
                'son_alis_fiyati': son_alis_fiyati,
                'son_tedarikci': son_tedarikci_adi,
                'tahmini_tukenme_suresi': tahmini_tukenme_suresi
            })
        print(f"DEBUG: Sipariş önerileri başarıyla oluşturuldu. Toplam {len(oneriler)} ürün.")
        return oneriler
    except Exception as e:
        print(f"HATA: Sipariş önerileri getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

def etiket_verisi_getir(urun_id: int) -> dict | None:
    """
    Etiket basımı için belirli bir ürünün gerekli tüm detaylarını getirir.
    Args:
        urun_id (int): Etiket verisi getirilecek ürünün ID'si.
    Returns:
        dict | None: Ürün detaylarını içeren sözlük veya None.
    Raises:
        Exception: Veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        urun = oturum.query(Urun).filter(Urun.id == urun_id).first()
        if not urun:
            print(f"UYARI: Ürün (ID: {urun_id}) etiket verisi için bulunamadı.")
            return None
        
        etiket_data = {
            'id': urun.id,
            'barkod': urun.barkod,
            'ad': urun.ad,
            'satis_fiyati': urun.satis_fiyati,
            'kdv_orani': urun.kdv_orani,
            'onceki_satis_fiyati': urun.onceki_satis_fiyati,
            'son_guncelleme_tarihi': urun.son_guncelleme_tarihi
        }
        print(f"DEBUG: Ürün (ID: {urun_id}) için etiket verisi başarıyla alındı.")
        log_aktivite(None, LOG_ACTION_PRODUCT_LABEL_PRINT, f"Ürün etiketi basıldı: ID: {urun.id}, Ad: {urun.ad}")
        return etiket_data
    except Exception as e:
        print(f"HATA: Ürün (ID: {urun_id}) etiket verisi alınırken hata: {e}")
        raise e
    finally:
        oturum.close()

# ===== YENİ FONKSİYONLAR BİTİŞİ =====
