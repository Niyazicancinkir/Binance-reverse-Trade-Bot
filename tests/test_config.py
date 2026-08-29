import os
import pytest
import config

def test_config_defaults():
    assert isinstance(config.BINANCE_DEMO, bool)
    assert isinstance(config.LEVERAGE, int)
    assert isinstance(config.TRADE_AMOUNT_USDT, float)
    assert isinstance(config.SCAN_INTERVAL_SECONDS, int)
    assert isinstance(config.AUTO_LOOP, bool)
    assert config.MARGIN_MODE in ["ISOLATED", "CROSSED"]
    assert config.GEMINI_MODEL == "gemini-3.1-flash-lite"

def test_config_paths():
    assert config.EXCEL_FILE.endswith(".xlsx")
    assert config.TRACKER_FILE.endswith(".json")
