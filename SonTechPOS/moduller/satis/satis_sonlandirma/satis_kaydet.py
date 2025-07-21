# Dosya Adı: moduller/satis/satis_sonlandirma/satis_kaydet.py
# Güncelleme Tarihi / Saati: 12.07.2025 13:50
# Yapılan İşlem: Loglama entegrasyonu yapıldı.

from sqlalchemy.orm import Session
from decimal import Decimal
import datetime

# Veritabanı modellerimiz
from cekirdek.veritabani_yonetimi import Satis, SatisKalemi, Odeme, Stok, Musteri, MusteriKupon
from cekirdek.ayarlar import ayarlar # Ayarlardan puan katsayısını almak için
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_SALE_COMPLETE

# ===== veritabanina_satisi_kaydet FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def veritabanina_satisi_kaydet(
    oturum: Session,
    sepet: list[dict],
    odemeler: list[dict],
    toplamlar: dict,
    sube_id: int,
    kullanici_id: int,
    musteri_id: int | None = None,
    genel_indirim_tutari: Decimal = Decimal('0.00'),
    uygulanan_promosyon_id: int | None = None,
    uygulanan_kupon_id: int | None = None
) -> tuple[int | None, bool, str]:
    """
    Hazırlanan satış verilerini veritabanına tek bir işlemde (transaction) kaydeder.
    """
    try:
        print("DEBUG (satis_kaydet): Satış kaydı işlemi başlatılıyor...")
        
        toplam_tutar = toplamlar.get('toplam_tutar', Decimal('0.00'))
        
        # 1. Yeni bir Satis nesnesi oluştur
        yeni_satis = Satis(
            sube_id=sube_id,
            musteri_id=musteri_id,
            kullanici_id=kullanici_id,
            toplam_tutar=toplam_tutar,
            indirim_tutari=genel_indirim_tutari,
            promosyon_indirim_tutari=Decimal('0.00'),
            uygulanan_kupon_id=uygulanan_kupon_id,
            uygulanan_promosyon_id=uygulanan_promosyon_id,
            durum='tamamlandi'
        )
        oturum.add(yeni_satis)
        oturum.flush()

        # 2. Satış Kalemlerini oluştur ve Stokları Düşür
        for kalem in sepet:
            urun_id = kalem['urun'].id
            satilan_miktar = kalem['miktar']
            birim_fiyat = kalem['fiyat'].satis_fiyati
            kalem_toplam_fiyat = birim_fiyat * satilan_miktar
            kalem_indirim_tutari = Decimal('0.00') 

            satis_kalemi = SatisKalemi(
                satis=yeni_satis,
                urun_id=urun_id,
                miktar=satilan_miktar,
                birim_fiyat=birim_fiyat,
                toplam_fiyat=kalem_toplam_fiyat,
                indirim_tutari=kalem_indirim_tutari
            )
            oturum.add(satis_kalemi)

            stok_kaydi = oturum.query(Stok).filter_by(urun_id=urun_id, sube_id=sube_id).first()
            
            if not stok_kaydi:
                print(f"UYARI: Ürün (ID: {urun_id}) için stok kaydı bulunamadı. Eksi stokla yeni kayıt oluşturuluyor.")
                stok_kaydi = Stok(urun_id=urun_id, sube_id=sube_id, miktar=-satilan_miktar)
                oturum.add(stok_kaydi)
            else:
                stok_kaydi.miktar -= satilan_miktar

            print(f"DEBUG: Stok düşüldü. Ürün: {kalem['urun'].ad}, Kalan Stok: {stok_kaydi.miktar}")

        # 3. Ödemeleri oluştur ve Müşteri Bakiyesini Güncelle
        veresiye_tutari = Decimal('0.00')
        for odeme_bilgisi in odemeler:
            odeme = Odeme(
                satis=yeni_satis,
                yontem=odeme_bilgisi['yontem'],
                tutar=odeme_bilgisi['tutar'],
                durum='tamamlandi'
            )
            oturum.add(odeme)
            if odeme_bilgisi['yontem'] == 'Veresiye':
                veresiye_tutari += odeme_bilgisi['tutar']

        if veresiye_tutari > 0 and musteri_id:
            musteri_kaydi = oturum.query(Musteri).filter_by(id=musteri_id).first()
            if not musteri_kaydi:
                raise Exception(f"Veresiye işlemi için Müşteri (ID: {musteri_id}) bulunamadı!")
            musteri_kaydi.bakiye += veresiye_tutari
            print(f"DEBUG: Müşteri bakiyesi güncellendi. Müşteri: {musteri_kaydi.ad}, Yeni Bakiye: {musteri_kaydi.bakiye}")

        # 4. Müşteri Sadakat Puanı Güncelleme
        if musteri_id:
            try:
                puan_katsayisi_str = ayarlar.getir('genel', 'puan_katsayisi', '0.01')
                puan_katsayisi = Decimal(puan_katsayisi_str)
                
                net_satis_tutari = toplam_tutar - genel_indirim_tutari - yeni_satis.promosyon_indirim_tutari
                eklenecek_puan = int(net_satis_tutari * puan_katsayisi)

                if eklenecek_puan > 0:
                    musteri_kaydi = oturum.query(Musteri).filter_by(id=musteri_id).first()
                    if musteri_kaydi:
                        musteri_kaydi.sadakat_puani += eklenecek_puan
                        print(f"DEBUG: Müşteri '{musteri_kaydi.ad}' için {eklenecek_puan} sadakat puanı eklendi. Yeni puan: {musteri_kaydi.sadakat_puani}")
                    else:
                        print(f"UYARI: Müşteri (ID: {musteri_id}) bulunamadığı için sadakat puanı eklenemedi.")
            except Exception as e:
                print(f"UYARI: Sadakat puanı hesaplanırken/eklenirken hata oluştu: {e}")
        
        # 5. Uygulanan Kuponu Kullanıldı Olarak İşaretle
        if uygulanan_kupon_id:
            musteri_kupon_kaydi = oturum.query(MusteriKupon).filter_by(id=uygulanan_kupon_id).first()
            if musteri_kupon_kaydi:
                musteri_kupon_kaydi.durum = 'kullanildi'
                musteri_kupon_kaydi.kullanilan_satis_id = yeni_satis.id
                musteri_kupon_kaydi.kullanilan_tarih = datetime.datetime.utcnow()
                print(f"DEBUG: Müşteri kuponu (ID: {uygulanan_kupon_id}) kullanıldı olarak işaretlendi.")
            else:
                print(f"UYARI: Uygulanan kupon (ID: {uygulanan_kupon_id}) bulunamadı, durumu güncellenemedi.")

        oturum.commit()
        
        sale_id = yeni_satis.id
        mesaj = f"Satış (No: {sale_id}) başarıyla kaydedildi."
        print(f"BİLGİ: {mesaj}")
        log_aktivite(kullanici_id, LOG_ACTION_SALE_COMPLETE, f"Satış tamamlandı: ID={sale_id}, Tutar={toplam_tutar:.2f}, Müşteri={musteri_id or 'Yok'}")
        return sale_id, True, mesaj

    except Exception as e:
        oturum.rollback()
        hata_mesaji = f"Satış kaydedilemedi: {e}"
        print(f"HATA (satis_kaydet): {hata_mesaji}")
        # Loglama burada yapılmaz, çünkü bu fonksiyonun dışındaki try-except bloğu tarafından yakalanacak.
        return None, False, hata_mesaji
