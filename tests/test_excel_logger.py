import os
import pytest
import pandas as pd
from unittest.mock import MagicMock
from excel_logger import (
    islemi_excel_kaydet, 
    paritede_acik_pozisyon_var_mi, 
    excel_kar_zarar_guncelle
)

@pytest.fixture
def temp_excel(tmp_path):
    test_path = str(tmp_path / "test_islem_gecmisi.xlsx")
    yield test_path
    if os.path.exists(test_path):
        os.remove(test_path)

def test_islemi_excel_kaydet_ve_acik_pozisyon(temp_excel):
    assert not paritede_acik_pozisyon_var_mi("ETH/USDT", dosya_yolu=temp_excel)
    
    islemi_excel_kaydet(
        parite="ETH/USDT",
        yon="SHORT",
        giris_fiyati=3000.0,
        tp=2800.0,
        sl=3200.0,
        borsa_id="order_123",
        miktar=0.1,
        kaldirac=5,
        tp_id="tp_456",
        sl_id="sl_789",
        dosya_yolu=temp_excel
    )
    
    assert paritede_acik_pozisyon_var_mi("ETH/USDT", dosya_yolu=temp_excel)
    assert not paritede_acik_pozisyon_var_mi("BTC/USDT", dosya_yolu=temp_excel)
    
    df = pd.read_excel(temp_excel)
    assert len(df) == 1
    assert df.iloc[0]["Parite"] == "ETH/USDT"
    assert df.iloc[0]["Durum"] == "Açık"
    assert df.iloc[0]["TP Emir ID"] == "tp_456"

def test_excel_pnl_ve_tp_kapanis(temp_excel):
    islemi_excel_kaydet(
        parite="SOL/USDT",
        yon="LONG",
        giris_fiyati=100.0,
        tp=120.0,
        sl=90.0,
        borsa_id="main_sol",
        miktar=1.0,
        kaldirac=5,
        tp_id="tp_sol_1",
        sl_id="sl_sol_1",
        dosya_yolu=temp_excel
    )
    
    # Mock borsa istemcisi: Pozisyon borsada kapanmış (contracts: 0) ve anlık fiyat 120 (TP seviyesi)
    mock_borsa = MagicMock()
    mock_borsa.fetch_positions.return_value = []
    mock_borsa.fetch_ticker.return_value = {"last": 120.0}
    mock_borsa.fetch_order.side_effect = lambda order_id, symbol: {
        "id": order_id,
        "status": "filled" if order_id == "tp_sol_1" else "open",
        "average": 120.0
    }
    
    excel_kar_zarar_guncelle(mock_borsa, dosya_yolu=temp_excel)
    
    df = pd.read_excel(temp_excel)
    assert df.iloc[0]["Durum"] == "Kapalı - TP Tetiklendi"
    assert float(df.iloc[0]["Anlık Fiyat"]) == 120.0
    assert df.iloc[0]["Kâr/Zarar ($)"] == "$20.00"
    assert not paritede_acik_pozisyon_var_mi("SOL/USDT", dosya_yolu=temp_excel)

def test_excel_oto_onarim_eksik_tp_sl(temp_excel):
    # TP ve SL ID'si eksik olan bir pozisyon ekle
    islemi_excel_kaydet(
        parite="AVAX/USDT",
        yon="LONG",
        giris_fiyati=20.0,
        tp=None,
        sl=None,
        borsa_id="main_avax",
        miktar=1.0,
        kaldirac=5,
        tp_id=None,
        sl_id=None,
        dosya_yolu=temp_excel
    )

    mock_borsa = MagicMock()
    mock_borsa.fetch_positions.return_value = [{'symbol': 'AVAX/USDT:USDT', 'contracts': 1.0}]
    mock_borsa.fetch_ticker.return_value = {"last": 20.0}
    mock_borsa.price_to_precision.side_effect = lambda sym, p: f"{p:.4f}"
    mock_borsa.create_order.side_effect = lambda symbol, type, side, amount, params: {
        "id": f"yeni_{type}_999",
        "status": "open"
    }

    excel_kar_zarar_guncelle(mock_borsa, dosya_yolu=temp_excel)

    df = pd.read_excel(temp_excel)
    assert df.iloc[0]["TP Emir ID"] != "-"
    assert df.iloc[0]["SL Emir ID"] != "-"
    assert "TAKE_PROFIT_MARKET" in df.iloc[0]["TP Emir ID"]
    assert "STOP_MARKET" in df.iloc[0]["SL Emir ID"]
