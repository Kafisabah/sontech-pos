# Dosya Adı: moduller/veri_aktarim/veri_aktarim_mantik.py
# Oluşturma Tarihi / Saati: 12.07.2025 15:50
# Yapılan İşlem: Ürünleri CSV'ye aktarma ve CSV'den içe aktarma işlevleri oluşturuldu.

import csv
import os
from decimal import Decimal
import datetime
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from cekirdek.veritabani_yonetimi import OturumYerel, Urun, Marka, Kategori, Stok, Fiyat
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_PRODUCT_ADD, LOG_ACTION_PRODUCT_UPDATE

# CSV başlıkları (beklenen sıra)
CSV_HEADERS = [
    "barkod", "ad", "marka_adi", "kategori_adi", "alis_fiyati",
    "satis_fiyati", "kdv_orani", "mevcut_stok", "min_stok_seviyesi", "aktif"
]

# ===== urunleri_csv_ye_aktar FONKSİYONU BAŞLANGICI =====
def urunleri_csv_ye_aktar(dosya_adi: str, sube_id: int) -> bool:
    """
    Tüm ürünleri ve ilgili şube stok/fiyat bilgilerini bir CSV dosyasına aktarır.
    Args:
        dosya_adi (str): Kaydedilecek CSV dosyasının adı/yolu.
        sube_id (int): Hangi şubenin stok/fiyat bilgileri aktarılacak.
    Returns:
        bool: Aktarım başarılıysa True, değilse False.
    Raises:
        Exception: Dosya yazma veya veritabanı hatasında.
    """
    oturum = OturumYerel()
    try:
        # Tüm ürünleri, markaları ve kategorileri çek
        urunler = oturum.query(Urun).all()
        
        with open(dosya_adi, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(CSV_HEADERS) # Başlıkları yaz

            for urun in urunler:
                # İlgili şubenin stok ve fiyat bilgilerini al
                stok = oturum.query(Stok).filter_by(urun_id=urun.id, sube_id=sube_id).first()
                fiyat = oturum.query(Fiyat).filter_by(urun_id=urun.id, sube_id=sube_id).first()

                row = [
                    urun.barkod,
                    urun.ad,
                    urun.marka.ad if urun.marka else "",
                    urun.kategori.ad if urun.kategori else "",
                    fiyat.alis_fiyati if fiyat and fiyat.alis_fiyati is not None else "",
                    fiyat.satis_fiyati if fiyat and fiyat.satis_fiyati is not None else "",
                    fiyat.kdv_orani if fiyat and fiyat.kdv_orani is not None else "",
                    stok.miktar if stok and stok.miktar is not None else "",
                    urun.min_stok_seviyesi if urun.min_stok_seviyesi is not None else "",
                    "Evet" if urun.aktif else "Hayır"
                ]
                writer.writerow(row)
        
        print(f"BİLGİ: Ürünler başarıyla '{dosya_adi}' dosyasına aktarıldı.")
        log_aktivite(None, "URUN_DISA_AKTAR", f"Ürün listesi CSV'ye aktarıldı: {dosya_adi}")
        return True
    except SQLAlchemyError as e:
        print(f"HATA: Veritabanından ürünler okunurken bir sorun oluştu: {e}")
        return False
    except IOError as e:
        print(f"HATA: CSV dosyasına yazılırken bir sorun oluştu: {e}")
        return False
    except Exception as e:
        print(f"HATA: Ürünleri CSV'ye aktarırken beklenmedik bir hata oluştu: {e}")
        return False
    finally:
        oturum.close()
# ===== urunleri_csv_ye_aktar FONKSİYONU BİTİŞİ =====

# ===== urunleri_csv_den_ice_aktar FONKSİYONU BAŞLANGICI =====
def urunleri_csv_den_ice_aktar(dosya_adi: str, sube_id: int) -> tuple[int, int, int]:
    """
    Bir CSV dosyasından ürünleri okur ve veritabanına ekler/günceller.
    Args:
        dosya_adi (str): İçe aktarılacak CSV dosyasının adı/yolu.
        sube_id (int): Hangi şubeye stok/fiyat bilgileri eklenecek/güncellenecek.
    Returns:
        tuple[int, int, int]: (eklenen_sayisi, guncellenen_sayisi, atlanan_sayisi)
    Raises:
        ValueError: Dosya bulunamazsa veya format hatası varsa.
        Exception: Diğer veritabanı veya işlem hatalarında.
    """
    if not os.path.exists(dosya_adi):
        raise ValueError(f"HATA: '{dosya_adi}' dosyası bulunamadı!")

    eklenen_sayisi = 0
    guncellenen_sayisi = 0
    atlanan_sayisi = 0
    
    oturum = OturumYerel() # Her ürün için yeni oturum açmak yerine tek oturum kullan

    try:
        with open(dosya_adi, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=';')
            headers = next(reader) # Başlık satırını oku

            # Başlıkların doğru sırada olduğundan emin ol
            if [h.lower() for h in headers] != CSV_HEADERS:
                raise ValueError(f"CSV başlıkları beklenenden farklı. Beklenen: {CSV_HEADERS}, Bulunan: {headers}")

            for satir_no, row in enumerate(reader, start=2): # 2. satırdan başla (başlık sonrası)
                if not row: continue # Boş satırları atla

                try:
                    # Gelen verileri temizle ve doğru tiplere dönüştür
                    barkod = row[0].strip()
                    ad = row[1].strip()
                    marka_adi = row[2].strip() or None
                    kategori_adi = row[3].strip() or None
                    alis_fiyati = Decimal(row[4].replace(',', '.') or '0.00')
                    satis_fiyati = Decimal(row[5].replace(',', '.') or '0.00')
                    kdv_orani = Decimal(row[6].replace(',', '.') or '0.00')
                    mevcut_stok = int(row[7] or '0')
                    min_stok_seviyesi = int(row[8] or '0')
                    aktif_str = row[9].strip().lower()
                    aktif = (aktif_str == "evet" or aktif_str == "true" or aktif_str == "1")

                    if not barkod or not ad:
                        print(f"UYARI: Satır {satir_no}: Barkod veya Ürün Adı boş olduğu için atlandı.")
                        atlanan_sayisi += 1
                        continue

                    # Marka ve Kategori oluştur/getir
                    marka = oturum.query(Marka).filter(Marka.ad == marka_adi).first() if marka_adi else None
                    if marka_adi and not marka:
                        marka = Marka(ad=marka_adi, aktif=True)
                        oturum.add(marka)
                        oturum.flush() # ID'sini almak için
                        print(f"DEBUG: Yeni marka oluşturuldu (İçe Aktarım): {marka_adi}")

                    kategori = oturum.query(Kategori).filter(Kategori.ad == kategori_adi).first() if kategori_adi else None
                    if kategori_adi and not kategori:
                        kategori = Kategori(ad=kategori_adi, aktif=True)
                        oturum.add(kategori)
                        oturum.flush() # ID'sini almak için
                        print(f"DEBUG: Yeni kategori oluşturuldu (İçe Aktarım): {kategori_adi}")

                    # Ürünü bul veya yeni oluştur
                    urun = oturum.query(Urun).filter(Urun.barkod == barkod).first()
                    if urun:
                        # Ürünü güncelle
                        urun.ad = ad
                        urun.marka = marka
                        urun.kategori = kategori
                        urun.alis_fiyati = alis_fiyati
                        urun.satis_fiyati = satis_fiyati
                        urun.kdv_orani = kdv_orani
                        urun.min_stok_seviyesi = min_stok_seviyesi
                        urun.aktif = aktif
                        guncellenen_sayisi += 1
                        log_aktivite(None, LOG_ACTION_PRODUCT_UPDATE, f"Ürün içe aktarımla güncellendi: ID: {urun.id}, Ad: {urun.ad}")
                        print(f"DEBUG: Satır {satir_no}: Ürün '{ad}' güncellendi.")
                    else:
                        # Yeni ürün ekle
                        urun = Urun(
                            barkod=barkod,
                            ad=ad,
                            marka=marka,
                            kategori=kategori,
                            alis_fiyati=alis_fiyati,
                            satis_fiyati=satis_fiyati,
                            kdv_orani=kdv_orani,
                            min_stok_seviyesi=min_stok_seviyesi,
                            aktif=aktif,
                            birim='Adet' # Varsayılan birim
                        )
                        oturum.add(urun)
                        oturum.flush() # ID'sini almak için
                        eklenen_sayisi += 1
                        log_aktivite(None, LOG_ACTION_PRODUCT_ADD, f"Ürün içe aktarımla eklendi: ID: {urun.id}, Ad: {urun.ad}")
                        print(f"DEBUG: Satır {satir_no}: Ürün '{ad}' eklendi.")

                    # Şubeye özel stok ve fiyatı güncelle/ekle
                    stok_kaydi = oturum.query(Stok).filter_by(urun_id=urun.id, sube_id=sube_id).first()
                    if stok_kaydi:
                        stok_kaydi.miktar = mevcut_stok
                        stok_kaydi.min_stok_seviyesi = min_stok_seviyesi # Stok kaydındaki min stok da güncellensin
                    else:
                        yeni_stok = Stok(urun_id=urun.id, sube_id=sube_id, miktar=mevcut_stok, min_stok_seviyesi=min_stok_seviyesi)
                        oturum.add(yeni_stok)
                        print(f"DEBUG: Satır {satir_no}: Ürün '{ad}' için yeni şube stoğu oluşturuldu.")

                    fiyat_kaydi = oturum.query(Fiyat).filter_by(urun_id=urun.id, sube_id=sube_id).first()
                    if fiyat_kaydi:
                        fiyat_kaydi.alis_fiyati = alis_fiyati
                        fiyat_kaydi.satis_fiyati = satis_fiyati
                        fiyat_kaydi.kdv_orani = kdv_orani
                    else:
                        yeni_fiyat = Fiyat(urun_id=urun.id, sube_id=sube_id, alis_fiyati=alis_fiyati, satis_fiyati=satis_fiyati, kdv_orani=kdv_orani)
                        oturum.add(yeni_fiyat)
                        print(f"DEBUG: Satır {satir_no}: Ürün '{ad}' için yeni şube fiyatı oluşturuldu.")

                    oturum.commit() # Her satırda commit yapmak yavaş olabilir, ancak hata durumunda daha az veri kaybı sağlar.
                                    # Büyük dosyalarda toplu commit tercih edilebilir.
                except ValueError as ve:
                    oturum.rollback()
                    print(f"UYARI: Satır {satir_no} veri dönüştürme hatası: {ve}. Atlandı.")
                    atlanan_sayisi += 1
                except IntegrityError as ie:
                    oturum.rollback()
                    print(f"UYARI: Satır {satir_no} benzersizlik hatası: {ie}. Atlandı.")
                    atlanan_sayisi += 1
                except SQLAlchemyError as sae:
                    oturum.rollback()
                    print(f"HATA: Satır {satir_no} veritabanı hatası: {sae}. Atlandı.")
                    atlanan_sayisi += 1
                except Exception as e:
                    oturum.rollback()
                    print(f"HATA: Satır {satir_no} beklenmedik hata: {e}. Atlandı.")
                    atlanan_sayisi += 1
        
        print(f"BİLGİ: İçe aktarım tamamlandı. Eklenen: {eklenen_sayisi}, Güncellenen: {guncellenen_sayisi}, Atlanan: {atlanan_sayisi}")
        log_aktivite(None, "URUN_ICE_AKTAR", f"Ürünler CSV'den içe aktarıldı. Eklendi: {eklenen_sayisi}, Güncellendi: {guncellenen_sayisi}, Atlandı: {atlanan_sayisi}")
        return eklenen_sayisi, guncellenen_sayisi, atlanan_sayisi

    except FileNotFoundError:
        print(f"HATA: '{dosya_adi}' dosyası bulunamadı.")
        return 0, 0, 0
    except ValueError as ve:
        print(f"HATA: CSV okuma hatası: {ve}")
        return 0, 0, 0
    except Exception as e:
        print(f"HATA: Ürünleri CSV'den içe aktarırken beklenmedik bir hata oluştu: {e}")
        return 0, 0, 0
    finally:
        oturum.close() # İşlem sonunda oturumu kapat
# ===== urunleri_csv_den_ice_aktar FONKSİYONU BİTİŞİ =====
