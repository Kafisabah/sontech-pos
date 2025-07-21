# Dosya Adı: moduller/stok/stok_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 12:45
# Yapılan İşlem: Stok listeleme sorgusu Urun modelindeki min_stok_seviyesi'ni dahil edecek şekilde güncellendi.

from cekirdek.veritabani_yonetimi import OturumYerel, Stok, Urun, Sube
from sqlalchemy.orm import joinedload
from decimal import Decimal

# ===== stoklari_getir FONKSİYONU BAŞLANGICI =====
def stoklari_getir(sube_id: int):
    """
    Belirtilen şubeye ait tüm stok kayıtlarını, ürün ve şube bilgileriyle birlikte çeker.
    Args:
        sube_id (int): Stokları listelenecek şubenin ID'si.
    Returns:
        list: Stok nesnelerinden oluşan bir liste döndürür.
    """
    if sube_id is None:
        print("Uyarı: Stokları getirmek için şube ID'si gereklidir.")
        return []
        
    oturum = OturumYerel()
    try:
        # Stok, Ürün ve Şube tablolarını birleştirerek sorgu yap
        # Urun.min_stok_seviyesi'ni de yükle
        stoklar = oturum.query(Stok).options(
            joinedload(Stok.urun).joinedload(Urun.marka), # Ürünün markasını da yükle
            joinedload(Stok.urun).joinedload(Urun.kategori), # Ürünün kategorisini de yükle
            joinedload(Stok.sube)
        ).filter(Stok.sube_id == sube_id).all()
        return stoklar
    except Exception as e:
        print(f"HATA: Stokları getirirken bir sorun oluştu: {e}")
        raise e
    finally:
        oturum.close()
# ===== stoklari_getir FONKSİYONU BİTİŞİ =====

# ===== stok_duzelt FONKSİYONU BAŞLANGICI =====
def stok_duzelt(stok_id: int, yeni_miktar: Decimal):
    """
    Belirli bir stok kaydının miktarını günceller.
    Args:
        stok_id (int): Güncellenecek stok kaydının ID'si.
        yeni_miktar (Decimal): Ürünün yeni stok miktarı.
    """
    oturum = OturumYerel()
    try:
        stok_kaydi = oturum.query(Stok).filter(Stok.id == stok_id).first()
        if stok_kaydi:
            stok_kaydi.miktar = yeni_miktar
            oturum.commit()
            print(f"DEBUG: Stok ID {stok_id} için miktar {yeni_miktar} olarak güncellendi.")
        else:
            print(f"HATA: Stok ID {stok_id} bulunamadı.")
            raise ValueError(f"Stok ID {stok_id} bulunamadı.")
    except Exception as e:
        oturum.rollback()
        print(f"HATA: Stok güncellenirken bir sorun oluştu: {e}")
        raise
    finally:
        oturum.close()
# ===== stok_duzelt FONKSİYONU BİTİŞİ =====
