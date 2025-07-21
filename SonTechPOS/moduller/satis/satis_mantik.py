# Dosya Adı: moduller/satis/satis_mantik.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 15:30
# Yapılan İşlem: Hızlı satış ekranı için ürünleri getirecek yeni bir fonksiyon eklendi.

from cekirdek.veritabani_yonetimi import OturumYerel, Urun, Stok, Fiyat, Satis, SatisKalemi, Musteri, Odeme, Iade, MusteriKupon
from sqlalchemy.orm import joinedload
from sqlalchemy import or_
from decimal import Decimal
import datetime
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_SALE_RETURN
from moduller.satis.satis_sonlandirma import satis_kaydet

# ===== urun_ara FONKSİYONU =====
def urun_ara(arama_terimi: str, sube_id: int):
    if not arama_terimi or len(arama_terimi) < 2: return []
    oturum = OturumYerel()
    try:
        urunler = oturum.query(Urun).filter(Urun.aktif == True, or_(Urun.barkod.ilike(f"%{arama_terimi}%"), Urun.ad.ilike(f"%{arama_terimi}%"))).limit(10).all()
        sonuclar = []
        for urun in urunler:
            fiyat = oturum.query(Fiyat).filter(Fiyat.urun_id == urun.id, Fiyat.sube_id == sube_id).first()
            if fiyat:
                stok = oturum.query(Stok).filter(Stok.urun_id == urun.id, Stok.sube_id == sube_id).first()
                sonuclar.append({"urun": urun, "stok": stok, "fiyat": fiyat})
        return sonuclar
    finally: oturum.close()

# ===== YENİ FONKSİYON: hizli_satis_urunlerini_getir =====
def hizli_satis_urunlerini_getir(sube_id: int, limit: int = 20):
    """
    Hızlı satış ekranında gösterilecek ürünleri getirir.
    Not: İleride ürünler tablosuna 'hizli_satis_mi' gibi bir alan eklenerek
    sadece o ürünlerin getirilmesi sağlanabilir. Şimdilik son eklenen aktif ürünleri getiriyoruz.
    """
    oturum = OturumYerel()
    try:
        urunler = oturum.query(Urun).filter(Urun.aktif == True).order_by(Urun.id.desc()).limit(limit).all()
        sonuclar = []
        for urun in urunler:
            fiyat = oturum.query(Fiyat).filter(Fiyat.urun_id == urun.id, Fiyat.sube_id == sube_id).first()
            if fiyat:
                sonuclar.append({'urun': urun, 'fiyat': fiyat})
        return sonuclar
    except Exception as e:
        print(f"HATA: Hızlı satış ürünleri getirilirken hata: {e}")
        return []
    finally:
        oturum.close()
# ===== YENİ FONKSİYON BİTİŞİ =====

# ===== satis_yap ve satis_iade_yap FONKSİYONLARI (Değişiklik yok) =====
def satis_yap(sepet: list, odemeler: list, toplamlar: dict, sube_id: int, kullanici_id: int, musteri_id: int = None,
              genel_indirim_tutari: Decimal = Decimal('0.00'), uygulanan_promosyon_id: int = None, uygulanan_kupon_id: int = None):
    oturum = OturumYerel()
    try:
        satis_id, basarili, mesaj = satis_kaydet.veritabanina_satisi_kaydet(
            oturum=oturum, sepet=sepet, odemeler=odemeler, toplamlar=toplamlar,
            sube_id=sube_id, kullanici_id=kullanici_id, musteri_id=musteri_id,
            genel_indirim_tutari=genel_indirim_tutari,
            uygulanan_promosyon_id=uygulanan_promosyon_id,
            uygulanan_kupon_id=uygulanan_kupon_id
        )
        if not basarili:
            raise Exception(mesaj)
        return satis_id
    except Exception as e:
        raise e
    finally:
        pass

def satis_iade_yap(satis_id: int, sebep: str = None, notlar: str = None, iade_yapan_kullanici_id: int = None) -> int | None:
    oturum = OturumYerel()
    try:
        satis = oturum.query(Satis).options(
            joinedload(Satis.kalemler).joinedload(SatisKalemi.urun),
            joinedload(Satis.odemeler),
            joinedload(Satis.musteri),
            joinedload(Satis.uygulanan_kupon)
        ).filter(Satis.id == satis_id).first()

        if not satis: raise ValueError(f"Satış (ID: {satis_id}) bulunamadı.")
        if satis.durum == 'iade_edildi': raise ValueError(f"Satış (ID: {satis_id}) zaten iade edilmiş.")
        if satis.durum != 'tamamlandi': raise ValueError(f"Sadece 'tamamlandı' durumundaki satışlar iade edilebilir (Mevcut Durum: {satis.durum}).")

        yeni_iade = Iade(
            orijinal_satis_id=satis.id, iade_tutari=satis.toplam_tutar, sebep=sebep,
            notlar=notlar, kullanici_id=iade_yapan_kullanici_id
        )
        oturum.add(yeni_iade)
        oturum.flush()

        for kalem in satis.kalemler:
            stok_kaydi = oturum.query(Stok).filter(Stok.urun_id == kalem.urun_id, Stok.sube_id == satis.sube_id).first()
            if stok_kaydi:
                stok_kaydi.miktar += kalem.miktar
        
        veresiye_odeme = next((o for o in satis.odemeler if o.yontem == 'Veresiye'), None)
        if veresiye_odeme and satis.musteri:
            satis.musteri.bakiye -= veresiye_odeme.tutar

        if satis.uygulanan_kupon_id:
            musteri_kupon = oturum.query(MusteriKupon).filter(MusteriKupon.id == satis.uygulanan_kupon_id).first()
            if musteri_kupon:
                musteri_kupon.durum = 'kullanilabilir'
                musteri_kupon.kullanilan_satis_id = None
        
        satis.durum = 'iade_edildi'
        for odeme in satis.odemeler:
            odeme.durum = 'iade_edildi'
        
        oturum.commit()
        log_aktivite(iade_yapan_kullanici_id, LOG_ACTION_SALE_RETURN, f"Satış iade edildi: Satış ID={satis_id}, İade ID={yeni_iade.id}, Sebep={sebep or 'Yok'}")
        return yeni_iade.id
    except Exception as e:
        oturum.rollback()
        raise e
    finally:
        oturum.close()
