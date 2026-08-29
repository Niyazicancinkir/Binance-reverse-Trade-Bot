import hashlib
import json
import os
from datetime import datetime
from config import TRACKER_FILE

def mesaj_hash_hesapla(mesaj_metni: str) -> str:
    """Mesaj metnini normalize edip SHA-256 hash'ini üretir."""
    temiz_metin = " ".join(mesaj_metni.strip().split())
    return hashlib.sha256(temiz_metin.encode("utf-8")).hexdigest()

def _hafizayi_oku(dosya_yolu: str = None) -> dict:
    hedef = dosya_yolu or TRACKER_FILE
    if not os.path.exists(hedef):
        return {"islenenler": {}}
    try:
        with open(hedef, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[TRACKER_UYARI] Hafıza dosyası okunamadı, sıfırlanıyor: {e}")
        return {"islenenler": {}}

def _hafizayi_yaz(veri: dict, dosya_yolu: str = None) -> None:
    hedef = dosya_yolu or TRACKER_FILE
    try:
        with open(hedef, "w", encoding="utf-8") as f:
            json.dump(veri, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[TRACKER_HATA] Hafıza dosyasına yazılamadı: {e}")

def sinyal_islendi_mi(mesaj_metni: str, dosya_yolu: str = None) -> bool:
    """Verilen mesajın daha önce işleme alınıp alınmadığını kontrol eder."""
    m_hash = mesaj_hash_hesapla(mesaj_metni)
    hafiza = _hafizayi_oku(dosya_yolu)
    return m_hash in hafiza.get("islenenler", {})

def sinyali_kaydet(mesaj_metni: str, sinyal_detayi: dict = None, dosya_yolu: str = None) -> None:
    """İşlenen sinyali mükerrer işlem açılmasını önlemek için hafızaya kaydeder."""
    m_hash = mesaj_hash_hesapla(mesaj_metni)
    hafiza = _hafizayi_oku(dosya_yolu)
    
    sinyal_detayi = sinyal_detayi or {}
    hafiza.setdefault("islenenler", {})[m_hash] = {
        "tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "coin_pair": sinyal_detayi.get("coin_pair", ""),
        "fenomen_yonu": sinyal_detayi.get("fenomen_yonu", ""),
        "bizim_yonumuz": sinyal_detayi.get("bizim_yonumuz", ""),
        "mesaj_ozet": mesaj_metni[:100]
    }
    _hafizayi_yaz(hafiza, dosya_yolu)
    print(f"[TRACKER] Sinyal hafızaya kaydedildi (Hash: {m_hash[:8]}...)")

def hafizayi_temizle(dosya_yolu: str = None) -> None:
    """Hafıza dosyasını sıfırlar (Testler veya sıfırlama amaçlı)."""
    _hafizayi_yaz({"islenenler": {}}, dosya_yolu)
