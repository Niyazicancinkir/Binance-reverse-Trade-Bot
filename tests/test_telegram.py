import pytest
from unittest.mock import MagicMock, patch
from telegram import bugunun_mesajlarini_cek

MOCK_TELEGRAM_HTML = """
<!DOCTYPE html>
<html>
<body>
    <div class="tgme_widget_message">
        <div class="tgme_widget_message_text">BTC/USDT LONG Entry: 60000 TP: 65000 SL: 58000</div>
    </div>
    <div class="tgme_widget_message">
        <div class="tgme_widget_message_text">ETH/USDT SHORT Entry: 3000 TP: 2800 SL: 3200</div>
    </div>
</body>
</html>
"""

@patch("telegram.requests.get")
def test_bugunun_mesajlarini_cek_success(mock_requests_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.text = MOCK_TELEGRAM_HTML
    mock_requests_get.return_value = mock_resp

    mesajlar = bugunun_mesajlarini_cek("testkanal")
    assert len(mesajlar) == 2
    assert "BTC/USDT LONG" in mesajlar[0]
    assert "ETH/USDT SHORT" in mesajlar[1]

@patch("telegram.requests.get")
def test_bugunun_mesajlarini_cek_http_error(mock_requests_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_requests_get.return_value = mock_resp

    mesajlar = bugunun_mesajlarini_cek("gecersiz_kanal")
    assert mesajlar == []
