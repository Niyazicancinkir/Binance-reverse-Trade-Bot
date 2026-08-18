# Binance Reverse Trade Bot

Telegram kanallarındaki işlem sinyallerini analiz eden, yönü tersine çevirerek Binance demo futures hesabında işlem başlatabilen Python botu.

## Özellikler

- Telegram kanalından son sinyalleri okur.
- Gemini ile mesajın işlem sinyali olup olmadığını analiz eder.
- LONG sinyalini SHORT'a, SHORT sinyalini LONG'a çevirir.
- Binance demo futures üzerinde market emri gönderebilir.
- İşlem kayıtlarını `islem_gecmisi.xlsx` dosyasına yazar ve PnL bilgisini günceller.
- Streamlit kontrol paneli sunar.

## Kurulum

Python 3.10 veya üzeri önerilir.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install ccxt google-generativeai pandas openpyxl requests beautifulsoup4 streamlit
```

## API anahtarları

`.env.example` dosyasını referans alarak gerekli ortam değişkenlerini PowerShell oturumunda tanımlayın:

```powershell
$env:BINANCE_API_KEY = "binance_api_key"
$env:BINANCE_SECRET_KEY = "binance_secret_key"
$env:GEMINI_API_KEY = "gemini_api_key"
```

Kod anahtarları otomatik olarak dosyadan okumaz; `.env` dosyasını repoya eklemeyin. Ortam değişkenlerini kalıcı yapmak için işletim sisteminin kullanıcı ortam değişkenlerini kullanın.

## Çalıştırma

Streamlit kontrol paneli:

```powershell
streamlit run app.py
```

Terminal üzerinden çalıştırma:

```powershell
python main.py
```

Binance istemcisi demo trading modunda yapılandırılmıştır. Gerçek hesapta işlem açmadan önce kodu ve risk ayarlarını mutlaka test edin.

## Güvenlik

- API anahtarlarını, secret key'leri veya başka kimlik bilgilerini kaynak koduna yazmayın.
- Binance API anahtarlarında mümkünse yalnızca gerekli işlem izinlerini açın ve para çekme iznini kapalı tutun.
- Daha önce paylaşılmış anahtarları iptal edip yenileriyle değiştirin.
- İşlem geçmişi ve `.env` dosyaları `.gitignore` ile repodan hariç tutulur.