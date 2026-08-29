# Binance Reverse Trade Bot ⚡

Telegram kanallarındaki işlem sinyallerini yapay zeka (Gemini) ile analiz eden, yönü tersine çevirerek (**LONG ⇄ SHORT, SL ⇄ TP**) Binance vadeli işlemler (Futures) demo/canlı hesabında otomatik pozisyon açabilen, **otomatik TP/SL** emirleri kuran ve mükerrer işlemleri önleyen Python botu.

## Özellikler

- **Telegram Sinyal Tarayıcı:** Herkese açık kanallardan web önizleme yöntemiyle en güncel sinyalleri çeker.
- **Gemini NLP Analizi & Ters Strateji:** Düzensiz mesaj formatlarını algılar; `LONG` sinyalini `SHORT`'a, `SHORT` sinyalini `LONG`'a çevirir. Orijinal SL seviyesini bizim TP'miz, orijinal TP seviyesini bizim SL'imiz yapar.
- **Otomatik TP & SL (Kâr Al & Zarar Kes):** Pozisyon açıldığı anda Binance üzerinde `reduceOnly: True` parametreli `TAKE_PROFIT_MARKET` ve `STOP_MARKET` tetikleyici emirleri açar.
- **Kaldıraç & Risk Yönetimi:** `.env` üzerinden veya Streamlit arayüzünden ayarlanabilir kaldıraç (örn. `5x`), marjin modu (`ISOLATED` / `CROSSED`) ve işlem büyüklüğü (`TRADE_AMOUNT_USDT`).
- **Mükerrer Sinyal Koruması (Idempotency):** Sinyal hash'i ve açık parite kontrolü sayesinde aynı sinyal için tekrar tekrar pozisyon açılmasını engeller.
- **Canlı PnL ve Pozisyon Kapatma Takibi:** Açık işlemlerin fiyat ve emir durumlarını borsa ile senkronize eder; TP/SL tetiklendiğinde durumu `"Kapalı"` olarak Excel'e (`islem_gecmisi.xlsx`) kaydeder.
- **Sürekli Döngü (Daemon) ve Streamlit Dashboard:** Hem arka planda periyodik tarama yapan CLI (`python main.py --loop`) hem de kullanıcı dostu Streamlit web paneli sunar.

---

## Kurulum

Python 3.10 veya üzeri önerilir.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Yapılandırma (`.env`)

Proje kök dizininde `.env.example` dosyasını `.env` olarak kopyalayın ve kendi API anahtarlarınızı girin:

```powershell
Copy-Item .env.example .env
```

`.env` dosya içeriği örneği:

```ini
# Binance API Bilgileri
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET_KEY=your_binance_secret_key
BINANCE_DEMO=true

# Gemini API
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.1-flash-lite

# Telegram ve Risk Ayarları
TELEGRAM_CHANNEL=cryptosignals0rg
LEVERAGE=5
MARGIN_MODE=ISOLATED
TRADE_AMOUNT_USDT=10.0

# Otomasyon
SCAN_INTERVAL_SECONDS=60
AUTO_LOOP=false
```

---

## Çalıştırma

### 1. Streamlit Web Kontrol Paneli:
```powershell
streamlit run app.py
```

### 2. Terminal Üzerinden Tek Seferlik Tarama:
```powershell
python main.py
```

### 3. Terminal Üzerinden Sürekli Otomatik Döngü (Background Worker):
```powershell
python main.py --loop --interval 60
```

---

## Testleri Çalıştırma

Bütün birim ve entegrasyon testlerini offline mock altyapısıyla koşturmak için:

```powershell
pytest tests/ -v
```

---

## Güvenlik Notları

- API anahtarlarınızı asla GitHub'a veya harici ortamlara göndermeyin (`.env` ve `islem_gecmisi.xlsx` dosyaları `.gitignore` ile korunmaktadır).
- Binance API anahtarınızda vadeli işlem (Futures) izninin açık, **para çekme (Withdrawal) izninin kapalı** olduğundan emin olun.
- Gerçek borsa moduna (`BINANCE_DEMO=false`) geçmeden önce stratejinizi ve risk parametrelerinizi demo modunda test edin.