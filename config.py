import os
from pathlib import Path
from dotenv import load_dotenv

# Proje dizinindeki .env dosyasını yükle
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"
load_dotenv(dotenv_path=env_path)

# Binance Yapılandırması
BINANCE_API_KEY = os.getenv("BINANCE_API_KEY", "")
BINANCE_SECRET_KEY = os.getenv("BINANCE_SECRET_KEY", "")
BINANCE_DEMO = os.getenv("BINANCE_DEMO", "true").strip().lower() in ("true", "1", "yes")

# Gemini Yapılandırması (Kullanıcı tercihi doğrultusunda mevcut model varsayılandır)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite")

# Telegram & Strateji
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL", "cryptosignals0rg")
LEVERAGE = int(os.getenv("LEVERAGE", "5"))
MARGIN_MODE = os.getenv("MARGIN_MODE", "ISOLATED").strip().upper()
TRADE_AMOUNT_USDT = float(os.getenv("TRADE_AMOUNT_USDT", "10.0"))

# Otomasyon ve Dosya Yolları
SCAN_INTERVAL_SECONDS = int(os.getenv("SCAN_INTERVAL_SECONDS", "60"))
AUTO_LOOP = os.getenv("AUTO_LOOP", "false").strip().lower() in ("true", "1", "yes")
EXCEL_FILE = os.getenv("EXCEL_FILE", "islem_gecmisi.xlsx")
TRACKER_FILE = os.getenv("TRACKER_FILE", "islenen_sinyaller.json")
