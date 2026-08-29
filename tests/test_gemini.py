import json
import pytest
from unittest.mock import MagicMock
from gemini import sinyali_cozumle, pariteyi_standartlastir

def test_pariteyi_standartlastir():
    assert pariteyi_standartlastir("BTCUSDT") == "BTC/USDT"
    assert pariteyi_standartlastir("ethusdt") == "ETH/USDT"
    assert pariteyi_standartlastir("SOL/USDT") == "SOL/USDT"
    assert pariteyi_standartlastir("SOLUSDC") == "SOL/USDC"

def test_sinyali_cozumle_long_to_short():
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_signal": True,
        "coin_pair": "BTCUSDT",
        "fenomen_yonu": "LONG",
        "entry": 60000.0,
        "sl": 58000.0,
        "tp": 65000.0
    })
    mock_model.generate_content.return_value = mock_response

    mesaj = "BTC LONG NOW! TP: 65000 SL: 58000"
    sonuc = sinyali_cozumle(mesaj, model_override=mock_model)

    assert sonuc["is_signal"] is True
    assert sonuc["coin_pair"] == "BTC/USDT"
    assert sonuc["fenomen_yonu"] == "LONG"
    # Ters Yön
    assert sonuc["bizim_yonumuz"] == "SHORT"
    # Orijinal SL bizim TP'miz olmalı
    assert sonuc["bizim_tp"] == 58000.0
    # Orijinal TP bizim SL'imiz olmalı
    assert sonuc["bizim_sl"] == 65000.0

def test_sinyali_cozumle_short_to_long():
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_signal": True,
        "coin_pair": "ETH/USDT",
        "fenomen_yonu": "SHORT",
        "entry": 3000.0,
        "sl": 3200.0,
        "tp": 2700.0
    })
    mock_model.generate_content.return_value = mock_response

    mesaj = "ETH SHORT NOW! TP: 2700 SL: 3200"
    sonuc = sinyali_cozumle(mesaj, model_override=mock_model)

    assert sonuc["is_signal"] is True
    assert sonuc["fenomen_yonu"] == "SHORT"
    assert sonuc["bizim_yonumuz"] == "LONG"
    assert sonuc["bizim_tp"] == 3200.0
    assert sonuc["bizim_sl"] == 2700.0

def test_sinyali_cozumle_non_signal():
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "is_signal": False
    })
    mock_model.generate_content.return_value = mock_response

    mesaj = "Herkese günaydın arkadaşlar, bugün piyasa yatay."
    sonuc = sinyali_cozumle(mesaj, model_override=mock_model)

    assert sonuc["is_signal"] is False
