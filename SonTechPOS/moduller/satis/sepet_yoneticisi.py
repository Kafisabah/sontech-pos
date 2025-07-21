# Dosya Adı: moduller/satis/sepet_yoneticisi.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 11:45
# Yapılan İşlem: Sepetteki ürünlere indirim uygulama mantığı eklendi.

from decimal import Decimal, ROUND_HALF_UP
from moduller.urun import urun_mantik

# ===== SepetYoneticisi SINIFI BAŞLANGICI =====
class SepetYoneticisi:
    def __init__(self):
        self.sepet = []
        print("DEBUG: SepetYoneticisi oluşturuldu, sepet boşaltıldı.")

    def sepeti_temizle(self):
        self.sepet = []
        print("DEBUG: Sepet temizlendi.")

    def sepete_ekle(self, urun_verisi: dict):
        urun = urun_verisi.get('urun')
        if not urun:
            return False, "Geçersiz ürün verisi."

        try:
            guncel_urun_bilgisi = urun_mantik.urunleri_getir(1) 
            guncel_urun = next((u for u in guncel_urun_bilgisi if u.id == urun.id), None)
            guncel_stok_miktari = guncel_urun.sube_stok.miktar if guncel_urun and hasattr(guncel_urun, 'sube_stok') and guncel_urun.sube_stok else 0
        except Exception as e:
            print(f"HATA: sepete_ekle - Stok alınırken hata: {e}")
            guncel_stok_miktari = 0

        for kalem in self.sepet:
            if kalem['urun'].id == urun.id:
                yeni_miktar = kalem['miktar'] + 1
                mesaj = "Miktar artırıldı."
                if guncel_stok_miktari < yeni_miktar:
                    mesaj += f"\nUYARI: Stok yetersiz (Mevcut: {guncel_stok_miktari:.2f})."
                kalem['miktar'] = yeni_miktar
                return True, mesaj

        mesaj = "Sepete eklendi."
        if guncel_stok_miktari < 1:
            mesaj += f"\nUYARI: Stok yetersiz (Mevcut: {guncel_stok_miktari:.2f})."
        
        yeni_kalem = {
            "urun": urun,
            "miktar": 1,
            "fiyat": urun_verisi.get('fiyat'),
            "indirim_tutari": Decimal('0.00'),
            "indirim_aciklamasi": ""
        }
        self.sepet.append(yeni_kalem)
        return True, mesaj

    def sepet_urun_sil(self, index: int):
        if 0 <= index < len(self.sepet):
            silinen_urun_adi = self.sepet[index]['urun'].ad
            del self.sepet[index]
            return True, f"'{silinen_urun_adi}' sepetten silindi."
        return False, "Ürün sepette bulunamadı."

    def sepet_urun_miktar_guncelle(self, index: int, yeni_miktar: int):
        if not (0 <= index < len(self.sepet)):
            return False, "Geçersiz ürün seçimi."
        if yeni_miktar <= 0:
            return False, "Miktar 0'dan büyük olmalıdır."

        kalem = self.sepet[index]
        kalem['miktar'] = yeni_miktar
        kalem['indirim_tutari'] = Decimal('0.00')
        kalem['indirim_aciklamasi'] = ""
        return True, "Miktar güncellendi."

    def kalem_indirim_uygula(self, index: int, indirim_tipi: str, indirim_degeri: Decimal):
        if not (0 <= index < len(self.sepet)):
            return False, "Geçersiz ürün seçimi."
        
        kalem = self.sepet[index]
        birim_fiyat = kalem['fiyat'].satis_fiyati
        miktar = kalem['miktar']
        kalem_toplami = birim_fiyat * miktar

        hesaplanan_indirim = Decimal('0.00')
        aciklama = ""

        if indirim_tipi == 'tutar':
            if indirim_degeri >= kalem_toplami:
                return False, "İndirim tutarı, ürün toplamından büyük veya eşit olamaz."
            hesaplanan_indirim = indirim_degeri
            aciklama = f"{indirim_degeri:.2f} ₺ İndirim"
        elif indirim_tipi == 'yuzde':
            if not (0 < indirim_degeri < 100):
                return False, "Yüzde değeri 0 ile 100 arasında olmalıdır."
            hesaplanan_indirim = (kalem_toplami * indirim_degeri / Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            aciklama = f"%{indirim_degeri:.0f} İndirim"
        
        kalem['indirim_tutari'] = hesaplanan_indirim
        kalem['indirim_aciklamasi'] = aciklama
        return True, f"İndirim uygulandı: {aciklama}"

    def sepeti_hesapla(self):
        ara_toplam = sum(kalem['fiyat'].satis_fiyati * kalem['miktar'] for kalem in self.sepet)
        toplam_indirim = sum(kalem['indirim_tutari'] for kalem in self.sepet)
        genel_toplam = ara_toplam - toplam_indirim
        return {
            'ara_toplam': ara_toplam,
            'toplam_indirim': toplam_indirim,
            'genel_toplam': genel_toplam
        }
