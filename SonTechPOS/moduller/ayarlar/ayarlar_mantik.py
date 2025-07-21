# Dosya Adı: moduller/ayarlar/ayarlar_mantik.py
# Güncelleme Tarihi / Saati: 12.07.2025 15:40
# Yapılan İşlem: Ayarlar okunurken float değerler için ayarlar.getir_float() kullanıldı.

import configparser
import os
from cekirdek.ayarlar import ayarlar
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_SETTINGS_UPDATE

# ===== ayarlari_getir FONKSİYONU BAŞLANGICI (GÜNCELLENDİ) =====
def ayarlari_getir():
    """
    Tüm ayarları config.ini dosyasından okur ve bir sözlük olarak döndürür.
    """
    print("DEBUG: ayarlar_mantik.ayarlari_getir() çağrıldı.")
    try:
        ayarlar_sozlugu = {
            'magaza_adi': ayarlar.getir('genel', 'magaza_adi', 'SonTech Market'),
            # 'default_kdv_rate' ve 'puan_katsayisi' için getir_float() kullanıldı
            'varsayilan_kdv': ayarlar.getir_float('genel', 'default_kdv_rate', 10.0),
            'puan_katsayisi': ayarlar.getir_float('genel', 'puan_katsayisi', 0.01)
        }
        print(f"DEBUG: Okunan ayarlar: {ayarlar_sozlugu}")
        return ayarlar_sozlugu
    except Exception as e:
        print(f"HATA: Ayarlar getirilirken sorun oluştu: {e}")
        return {}
# ===== ayarlari_getir FONKSİYONU BİTİŞİ =====

# ===== ayarlari_kaydet FONKSİYONU BAŞLANGICI (Aynı kalıyor) =====
def ayarlari_kaydet(yeni_ayarlar: dict, kullanici_id: int | None = None):
    """
    Verilen yeni ayarları config.ini dosyasına kaydeder ve loglar.
    Args:
        yeni_ayarlar (dict): Kaydedilecek yeni ayarları içeren sözlük.
        kullanici_id (int | None): Ayarları kaydeden kullanıcının ID'si.
    Returns:
        bool: Kaydetme başarılıysa True, değilse False.
    """
    print(f"DEBUG: ayarlar_mantik.ayarlari_kaydet() çağrıldı. Kaydedilecek veriler: {yeni_ayarlar}")
    try:
        # config.ini dosyasını güncelleme mantığı
        # comment_prefixes ve allow_no_value ile başlatarak yorumları doğru ayrıştır
        config = configparser.ConfigParser(comment_prefixes=';', allow_no_value=True)
        config_yolu = os.path.join(os.path.dirname(__file__), '..', '..', 'config.ini')
        config.read(config_yolu, encoding='utf-8')

        # Genel bölümü oluştur veya güncelle
        if 'genel' not in config:
            config['genel'] = {}
        
        # Sadece ilgili ayarları güncelle
        if 'magaza_adi' in yeni_ayarlar:
            config['genel']['magaza_adi'] = yeni_ayarlar['magaza_adi']
        if 'varsayilan_kdv' in yeni_ayarlar:
            config['genel']['default_kdv_rate'] = str(yeni_ayarlar['varsayilan_kdv']) # String olarak kaydet
        if 'puan_katsayisi' in yeni_ayarlar:
            config['genel']['puan_katsayisi'] = str(yeni_ayarlar['puan_katsayisi']) # String olarak kaydet

        with open(config_yolu, 'w', encoding='utf-8') as configfile:
            config.write(configfile)
        
        log_detaylari = f"Uygulama ayarları güncellendi: {yeni_ayarlar}"
        log_aktivite(kullanici_id, LOG_ACTION_SETTINGS_UPDATE, log_detaylari)

        print("BİLGİ: Ayarlar başarıyla kaydedildi.")
        return True
    except Exception as e:
        print(f"HATA: Ayarlar kaydedilirken bir sorun oluştu: {e}")
        return False
# ===== ayarlari_kaydet FONKSİYONU BİTİŞİ =====
