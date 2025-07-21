# Dosya Adı: moduller/yazdirma/yazdirma_mantik.py
# Oluşturma Tarihi / Saati: 12.07.2025 15:50
# Yapılan İşlem: Etiket yazdırma işlevleri oluşturuldu (simülasyon).

from PyQt5.QtWidgets import QMessageBox
from decimal import Decimal
import datetime

# ===== raf_etiketi_formatla FONKSİYONU BAŞLANGICI =====
def raf_etiketi_formatla(etiket_data: dict) -> str:
    """
    Verilen ürün verilerini raf etiketi formatında bir metin olarak döndürür.
    Args:
        etiket_data (dict): Ürün etiket bilgileri (id, barkod, ad, satis_fiyati, kdv_orani, onceki_satis_fiyati, son_guncelleme_tarihi).
    Returns:
        str: Formatlanmış etiket metni.
    """
    urun_adi = etiket_data.get('ad', 'Bilinmeyen Ürün')
    barkod = etiket_data.get('barkod', 'N/A')
    satis_fiyati = etiket_data.get('satis_fiyati', Decimal('0.00'))
    kdv_orani = etiket_data.get('kdv_orani', Decimal('0.00'))
    onceki_satis_fiyati = etiket_data.get('onceki_satis_fiyati')
    son_guncelleme_tarihi = etiket_data.get('son_guncelleme_tarihi')

    etiket_metni = f"--- RAF ETİKETİ ---\n"
    etiket_metni += f"Ürün: {urun_adi}\n"
    etiket_metni += f"Barkod: {barkod}\n"
    etiket_metni += f"--------------------\n"
    etiket_metni += f"Fiyat: {satis_fiyati:.2f} TL\n"
    etiket_metni += f"KDV: %{kdv_orani:.2f}\n"
    if onceki_satis_fiyati is not None and onceki_satis_fiyati != satis_fiyati:
        etiket_metni += f"Eski Fiyat: {onceki_satis_fiyati:.2f} TL\n"
    etiket_metni += f"--------------------\n"
    etiket_metni += f"Güncelleme: {son_guncelleme_tarihi.strftime('%d.%m.%Y %H:%M') if son_guncelleme_tarihi else 'N/A'}\n"
    etiket_metni += f"--------------------\n"
    print(f"DEBUG: Raf etiketi formatlandı: {urun_adi}")
    return etiket_metni

# ===== raf_etiketi_formatla FONKSİYONU BİTİŞİ =====

# ===== etiket_bastir_simulasyon FONKSİYONU BAŞLANGICI (YENİ) =====
def etiket_bastir_simulasyon(etiket_data: dict, parent=None):
    """
    Raf etiketini bir mesaj kutusunda göstererek yazdırma işlemini simüle eder.
    Args:
        etiket_data (dict): Yazdırılacak etiket verisi.
        parent (QWidget, optional): Mesaj kutusunun ebeveyn widget'ı. Defaults to None.
    """
    if not etiket_data:
        QMessageBox.warning(parent, "Hata", "Etiket verisi boş.")
        return

    try:
        etiket_metni = raf_etiketi_formatla(etiket_data)
        QMessageBox.information(parent, "Etiket Basımı Simülasyonu", etiket_metni)
        print(f"BİLGİ: Etiket basımı simüle edildi: Ürün ID {etiket_data.get('id')}")
    except Exception as e:
        QMessageBox.critical(parent, "Hata", f"Etiket basılırken bir sorun oluştu:\n{e}")
        print(f"HATA: Etiket basım simülasyonu sırasında hata: {e}")
# ===== etiket_bastir_simulasyon FONKSİYONU BİTİŞİ =====
