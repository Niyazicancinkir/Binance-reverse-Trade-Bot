import os
import pytest
from tracker import (
    mesaj_hash_hesapla, 
    sinyal_islendi_mi, 
    sinyali_kaydet, 
    hafizayi_temizle
)

@pytest.fixture
def temp_tracker(tmp_path):
    test_file = str(tmp_path / "test_tracker.json")
    yield test_file
    if os.path.exists(test_file):
        os.remove(test_file)

def test_mesaj_hash_hesapla():
    msg1 = "BTC/USDT LONG Entry: 50000"
    msg2 = "  BTC/USDT   LONG   Entry: 50000  "
    msg3 = "ETH/USDT SHORT Entry: 3000"
    
    # Boşluklardan arındırılmış aynı mesajlar aynı hash'i üretmeli
    assert mesaj_hash_hesapla(msg1) == mesaj_hash_hesapla(msg2)
    # Farklı mesajlar farklı hash üretmeli
    assert mesaj_hash_hesapla(msg1) != mesaj_hash_hesapla(msg3)

def test_sinyal_islendi_mi_and_kaydet(temp_tracker):
    msg = "SOL/USDT LONG Target: 150 Stop: 120"
    
    assert not sinyal_islendi_mi(msg, dosya_yolu=temp_tracker)
    
    sinyali_kaydet(msg, {"coin_pair": "SOL/USDT", "fenomen_yonu": "LONG", "bizim_yonumuz": "SHORT"}, dosya_yolu=temp_tracker)
    
    assert sinyal_islendi_mi(msg, dosya_yolu=temp_tracker)
    
    # Farklı mesaj işlenmedi olarak kalmalı
    assert not sinyal_islendi_mi("Farklı bir mesaj", dosya_yolu=temp_tracker)

def test_hafizayi_temizle(temp_tracker):
    msg = "BNB/USDT BUY TP: 600"
    sinyali_kaydet(msg, dosya_yolu=temp_tracker)
    assert sinyal_islendi_mi(msg, dosya_yolu=temp_tracker)
    
    hafizayi_temizle(dosya_yolu=temp_tracker)
    assert not sinyal_islendi_mi(msg, dosya_yolu=temp_tracker)
