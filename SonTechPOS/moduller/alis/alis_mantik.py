# Dosya Adı: moduller/alis/alis_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 13:50
# Yapılan İşlem: Loglama entegrasyonu yapıldı.

from cekirdek.veritabani_yonetimi import OturumYerel, Alis, AlisKalemi, Stok, Urun, Tedarikci
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from decimal import Decimal
import datetime
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_STOCK_PURCHASE

# ===== alis_kaydet FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def alis_kaydet(alis_bilgileri: dict, kalemler_listesi: list[dict]) -> int | None:
    if not kalemler_listesi:
        raise ValueError("Alış kaydı için en az bir ürün girilmelidir.")

    oturum = OturumYerel()
    try:
        tedarikci_id = alis_bilgileri.get('tedarikci_id')
        if tedarikci_id:
            tedarikci = oturum.query(Tedarikci).filter(Tedarikci.id == tedarikci_id).first()
            if not tedarikci:
                raise ValueError(f"Belirtilen tedarikçi ID ({tedarikci_id}) bulunamadı.")

        yeni_alis = Alis(
            tedarikci_id=tedarikci_id,
            fatura_no=alis_bilgileri.get('fatura_no'),
            notlar=alis_bilgileri.get('notlar'),
            tarih=datetime.datetime.utcnow()
        )
        oturum.add(yeni_alis)
        oturum.flush()

        for kalem in kalemler_listesi:
            urun_id = kalem.get('urun_id')
            miktar = kalem.get('miktar')
            alis_fiyati = kalem.get('alis_fiyati')
            son_kullanma_tarihi = kalem.get('son_kullanma_tarihi')

            if not all([urun_id, miktar, alis_fiyati is not None]):
                raise ValueError("Alış kalemi için ürün ID, miktar ve alış fiyatı zorunludur.")
            if miktar <= 0 or alis_fiyati < Decimal('0.00'):
                raise ValueError("Miktar pozitif, alış fiyatı negatif olamaz.")

            urun = oturum.query(Urun).filter(Urun.id == urun_id).first()
            if not urun:
                raise ValueError(f"Alış kalemi için ürün ID ({urun_id}) bulunamadı.")

            alis_kalemi = AlisKalemi(
                alis=yeni_alis,
                urun_id=urun_id,
                miktar=miktar,
                alis_fiyati=alis_fiyati,
                son_kullanma_tarihi=son_kullanma_tarihi
            )
            oturum.add(alis_kalemi)

            stok_kaydi = oturum.query(Stok).filter_by(urun_id=urun_id, sube_id=1).first()
            if stok_kaydi:
                stok_kaydi.miktar += miktar
                print(f"DEBUG: Ürün '{urun.ad}' stoğu {miktar} artırıldı. Yeni stok: {stok_kaydi.miktar}")
            else:
                yeni_stok = Stok(
                    urun_id=urun_id,
                    sube_id=1,
                    miktar=miktar,
                    min_stok_seviyesi=urun.min_stok_seviyesi
                )
                oturum.add(yeni_stok)
                print(f"UYARI: Ürün '{urun.ad}' için stok kaydı bulunamadı, yeni oluşturuldu. Miktar: {miktar}")

            urun.alis_fiyati = alis_fiyati
            print(f"DEBUG: Ürün '{urun.ad}' için genel alış fiyatı {alis_fiyati} olarak güncellendi.")

        oturum.commit()
        print(f"BİLGİ: Alış işlemi (ID: {yeni_alis.id}) başarıyla kaydedildi ve stoklar güncellendi.")
        log_aktivite(None, LOG_ACTION_STOCK_PURCHASE, f"Alış kaydedildi: ID={yeni_alis.id}, Tedarikçi={tedarikci_id or 'Yok'}, Ürün Sayısı={len(kalemler_listesi)}")
        return yeni_alis.id

    except Exception as e:
        oturum.rollback()
        print(f"HATA: Alış kaydedilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== alis_listele FONKSİYONU BAŞLANGICI (Aynı kalıyor) =====
def alis_listele(tedarikci_id: int = None, baslangic_tarihi: datetime.date = None, bitis_tarihi: datetime.date = None) -> list[Alis]:
    oturum = OturumYerel()
    try:
        sorgu = oturum.query(Alis).options(joinedload(Alis.tedarikci)).order_by(Alis.tarih.desc())

        if tedarikci_id:
            sorgu = sorgu.filter(Alis.tedarikci_id == tedarikci_id)
        if baslangic_tarihi:
            sorgu = sorgu.filter(Alis.tarih >= baslangic_tarihi)
        if bitis_tarihi:
            sorgu = sorgu.filter(Alis.tarih <= bitis_tarihi + datetime.timedelta(days=1))

        return sorgu.all()
    except Exception as e:
        print(f"HATA: Alışlar listelenirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()

# ===== alis_detay_getir FONKSİYONU BAŞLANGICI (Aynı kalıyor) =====
def alis_detay_getir(alis_id: int) -> Alis | None:
    oturum = OturumYerel()
    try:
        alis = oturum.query(Alis).options(
            joinedload(Alis.tedarikci),
            joinedload(Alis.kalemler).joinedload(AlisKalemi.urun)
        ).filter(Alis.id == alis_id).first()
        return alis
    except Exception as e:
        print(f"HATA: Alış detayı (ID: {alis_id}) getirilirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
