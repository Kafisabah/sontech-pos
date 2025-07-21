# Dosya Adı: cekirdek/ayarlar.py
# Güncelleme Tarihi / Saati: 16.07.2025 / 06:48
# Yapılan Güncelleme: Kullanıcıdan gelen son sürüm ile güncellendi.

import configparser
import os

# ===== AyarYoneticisi SINIFI BAŞLANGICI =====
class AyarYoneticisi:
    """
    config.ini dosyasını okumak ve yönetmek için kullanılır.
    Singleton deseni ile uygulama boyunca tek bir örnek oluşturulur.
    """
    _ornek = None
    _config = None

    def __new__(cls):
        if cls._ornek is None:
            cls._ornek = super(AyarYoneticisi, cls).__new__(cls)
            cls._ornek._ayarlari_yukle()
        return cls._ornek

    def _ayarlari_yukle(self):
        """config.ini dosyasını bulur ve okur."""
        self._config = configparser.ConfigParser(comment_prefixes=';', inline_comment_prefixes=';', allow_no_value=True)
        # Bu dosyanın bulunduğu dizinden bir üst dizine çıkıp config.ini'yi bulur.
        config_yolu = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        self._config.read(config_yolu, encoding='utf-8')

    def getir(self, bolum, anahtar, varsayilan=None):
        """Belirtilen bölüm ve anahtardaki ayarı string olarak döndürür."""
        return self._config.get(bolum, anahtar, fallback=varsayilan)

    def getir_int(self, bolum, anahtar, varsayilan=None):
        """Belirtilen bölüm ve anahtardaki ayarı integer olarak döndürür."""
        return self._config.getint(bolum, anahtar, fallback=varsayilan)
    
    def getir_float(self, bolum, anahtar, varsayilan=None):
        """Belirtilen bölüm ve anahtardaki ayarı float olarak döndürür."""
        return self._config.getfloat(bolum, anahtar, fallback=varsayilan)

    def hizli_butonlari_getir(self):
        """
        config.ini dosyasından hızlı buton ayarlarını okur ve bir sözlük olarak döndürür.
        """
        if not self._config.has_section('hizli_butonlar'):
            return {}
        
        butonlar = {}
        for key, value in self._config.items('hizli_butonlar'):
            butonlar[key.upper()] = value # Tuş isimlerini büyük harfe çevir
        return butonlar

# ===== AyarYoneticisi SINIFI BİTİŞİ =====

# Singleton örneğini dışa aktararak her yerden aynı nesneye erişim sağlanır.
ayarlar = AyarYoneticisi()