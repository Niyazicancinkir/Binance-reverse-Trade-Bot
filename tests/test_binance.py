import pytest
from unittest.mock import MagicMock, patch
from binance import kaldirac_ve_marjin_ayarla, miktar_hesapla, emri_baslat, tp_sl_fiyatlarini_dogrula

@pytest.fixture
def mock_ccxt_client():
    client = MagicMock()
    client.load_markets.return_value = {
        "BTC/USDT": {
            "limits": {
                "amount": {"min": 0.001},
                "cost": {"min": 5.0}
            },
            "precision": {"amount": 3}
        }
    }
    client.fetch_ticker.return_value = {"last": 60000.0}
    client.amount_to_precision.side_effect = lambda sym, amt: f"{amt:.3f}"
    client.price_to_precision.side_effect = lambda sym, price: f"{price:.2f}"
    client.create_market_order.return_value = {"id": "11223344", "status": "closed"}
    client.create_order.side_effect = lambda symbol, type, side, amount, params: {
        "id": f"{type}_{side}_5566",
        "status": "open"
    }
    return client

def test_kaldirac_ve_marjin_ayarla(mock_ccxt_client):
    kaldirac_ve_marjin_ayarla(mock_ccxt_client, "BTC/USDT", leverage=10, margin_mode="ISOLATED")
    mock_ccxt_client.set_leverage.assert_called_once_with(10, "BTC/USDT")
    mock_ccxt_client.set_margin_mode.assert_called_once_with("ISOLATED", "BTC/USDT")

def test_miktar_hesapla(mock_ccxt_client):
    miktar = miktar_hesapla(mock_ccxt_client, "BTC/USDT", giris_fiyati=50000.0, usdt_miktari=10.0, leverage=5)
    assert miktar >= 0.001

def test_tp_sl_dogrulama_long_swap_and_fallback():
    # Long pozisyon için TP > Giriş ve SL < Giriş olmalı
    # Durum 1: TP ve SL ters girilmişse (TP=90, SL=110, Giriş=100) -> Swap edilmeli
    tp, sl = tp_sl_fiyatlarini_dogrula(yon="LONG", giris_fiyati=100.0, tp=90.0, sl=110.0)
    assert tp == 110.0
    assert sl == 90.0

    # Durum 2: TP geçersiz girilmişse (+%3 fallback)
    tp, sl = tp_sl_fiyatlarini_dogrula(yon="LONG", giris_fiyati=100.0, tp=80.0, sl=95.0)
    assert tp == 103.0
    assert sl == 95.0

def test_tp_sl_dogrulama_short_swap_and_fallback():
    # Short pozisyon için TP < Giriş ve SL > Giriş olmalı
    # Durum 1: TP ve SL ters girilmişse (TP=110, SL=90, Giriş=100) -> Swap edilmeli
    tp, sl = tp_sl_fiyatlarini_dogrula(yon="SHORT", giris_fiyati=100.0, tp=110.0, sl=90.0)
    assert tp == 90.0
    assert sl == 110.0

    # Durum 2: TP geçersiz girilmişse (-%3 fallback)
    tp, sl = tp_sl_fiyatlarini_dogrula(yon="SHORT", giris_fiyati=100.0, tp=120.0, sl=105.0)
    assert tp == 97.0
    assert sl == 105.0

@patch("binance.islemi_excel_kaydet")
def test_emri_baslat_with_tp_sl(mock_excel_save, mock_ccxt_client):
    sonuc = emri_baslat(
        coin_pair="BTC/USDT",
        yon="SHORT",
        bizim_tp=55000.0,
        bizim_sl=65000.0,
        usdt_miktari=20.0,
        leverage=5,
        margin_mode="ISOLATED",
        client_override=mock_ccxt_client
    )

    assert sonuc["success"] is True
    assert sonuc["main_order_id"] == "11223344"
    assert sonuc["tp_order_id"] is not None
    assert sonuc["sl_order_id"] is not None
    
    mock_ccxt_client.create_market_order.assert_called_once()
    assert mock_ccxt_client.create_order.call_count == 2
    mock_excel_save.assert_called_once()
