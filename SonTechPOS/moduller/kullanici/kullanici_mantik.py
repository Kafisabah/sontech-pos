# Dosya Adı: moduller/kullanici/kullanici_mantik.py
# Güncelleme Tarihi / Saati: 17.07.2025 / 10:15
# Yapılan İşlem: PIN ile kullanıcı doğrulama fonksiyonu eklendi.

import bcrypt
from cekirdek.veritabani_yonetimi import OturumYerel, Kullanici
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_
from cekirdek.loglama.log_mantik import log_aktivite, LOG_ACTION_USER_ADD, LOG_ACTION_USER_UPDATE, LOG_ACTION_USER_PASSWORD_CHANGE, LOG_ACTION_USER_STATUS_CHANGE, LOG_ACTION_USER_LOGIN

def kullanici_dogrula_pin(girilen_pin: str) -> Kullanici | None:
    oturum = OturumYerel()
    try:
        tum_kullanicilar = oturum.query(Kullanici).filter(Kullanici.aktif == True, Kullanici.pin != None).all()
        for kullanici in tum_kullanicilar:
            if bcrypt.checkpw(girilen_pin.encode('utf-8'), kullanici.pin.encode('utf-8')):
                log_aktivite(kullanici.id, LOG_ACTION_USER_LOGIN, f"PIN ile giriş yapıldı: Kullanıcı Adı={kullanici.kullanici_adi}")
                return kullanici
        return None
    except Exception as e:
        print(f"HATA: PIN ile kullanıcı doğrulanırken bir hata oluştu: {e}")
        return None
    finally:
        oturum.close()

def kullanici_ekle(kullanici_adi: str, sifre: str, tam_ad: str = None, rol: str = 'kullanici') -> int | None:
    if not kullanici_adi or not sifre:
        raise ValueError("Kullanıcı adı ve şifre boş olamaz.")
    if rol not in ['admin', 'kullanici']:
        raise ValueError("Geçersiz kullanıcı rolü. 'admin' veya 'kullanici' olmalıdır.")
    oturum = OturumYerel()
    try:
        if oturum.query(Kullanici).filter(Kullanici.kullanici_adi == kullanici_adi).first():
            raise IntegrityError(f"Kullanıcı adı '{kullanici_adi}' zaten mevcut!", params=None, orig=None)
        sifre_hash = bcrypt.hashpw(sifre.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        yeni_kullanici = Kullanici(kullanici_adi=kullanici_adi, sifre_hash=sifre_hash, tam_ad=tam_ad, rol=rol, aktif=True)
        oturum.add(yeni_kullanici)
        oturum.commit()
        log_aktivite(None, LOG_ACTION_USER_ADD, f"Yeni kullanıcı eklendi: ID={yeni_kullanici.id}, Ad={yeni_kullanici.kullanici_adi}")
        return yeni_kullanici.id
    finally:
        oturum.close()

def kullanici_dogrula(kullanici_adi: str, sifre: str) -> Kullanici | None:
    oturum = OturumYerel()
    try:
        kullanici = oturum.query(Kullanici).filter(Kullanici.kullanici_adi == kullanici_adi, Kullanici.aktif == True).first()
        if kullanici and bcrypt.checkpw(sifre.encode('utf-8'), kullanici.sifre_hash.encode('utf-8')):
            log_aktivite(kullanici.id, LOG_ACTION_USER_LOGIN, f"Kullanıcı girişi: Ad={kullanici.kullanici_adi}")
            return kullanici
        return None
    finally:
        oturum.close()
