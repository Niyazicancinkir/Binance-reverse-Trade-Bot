# 🗺️ Binance Reverse Trade Bot - Geliştirme Yol Haritası (Roadmap)

Bu belge, projenin tamamlanan özelliklerini ve kripto vadeli işlem piyasasında **en yüksek F/P (Fiyat/Performans & Risk/Getiri Oranı)** sağlayan bir sonraki aşama geliştirme planlarını içerir.

---

## ✅ Faz 1: Temel Otonomi ve Risk Koruması (Tamamlandı)

- [x] **Yapay Zeka Destekli Tersine Strateji:** Gemini ile mesaj analizi, `LONG ⇄ SHORT`, `SL ⇄ TP` tersleme motoru.
- [x] **Otomatik Borsa TP/SL Emirleri:** Pozisyon açıldığı anda Binance üzerinde `reduceOnly: True` parametreli `TAKE_PROFIT_MARKET` ve `STOP_MARKET` tetikleyicileri.
- [x] **Anlık Fiyat Doğrulama (Anti-Trigger Guard):** Sinyal seviyelerini anlık fiyata göre denetleyen ve `-2021` borsa hatasını önleyen `tp_sl_fiyatlarini_dogrula()` motoru.
- [x] **Kaldıraç & Marjin Kontrolü:** `LEVERAGE` (5x) ve `MARGIN_MODE` (ISOLATED) parametreleri.
- [x] **Mükerrer Sinyal Koruması (Idempotency):** Sinyal hash hafızası (`tracker.py`) ile mükerrer işlemlerin engellenmesi.
- [x] **Oto-Onarım (Auto-Healing):** Açıkta kalmış, TP/SL emri bulunmayan eski pozisyonların taranıp eksik borsa emirlerinin otomatik kurulması.
- [x] **Döngüsel Tarama & Streamlit Dashboard:** CLI `--loop` arka plan taraması ve canlı PnL web kontrol paneli.
- [x] **Birim Test Paketi:** 19 adet birim ve entegrasyon testi (%100 başarı).

---

## 🚀 Faz 2: Kripto Dünyası İçin En İyi F/P Stratejisi (Yapılacaklar)

> ### 🏆 F/P Şampiyonu: Hibrit Kısmi Kâr Al (%50 TP) + Moonbag Trailing Stop
> Kripto vadeli işlem piyasalarında kazanma oranını en üst seviyeye çıkaran ve riski sıfıra indiren kurumsal fon stratejisi.

### 1. Kademeli Kâr Al (%50 Partial Take Profit - TP1)
* **Açıklama:** Fiyat birinci hedefe (fenomenin patladığı SL seviyesine veya +%3 kâra) ulaştığında pozisyonun **%50'si piyasa emriyle kapatılır**.
* **Avantajı:** Kâr anında realize edilir ve cebe konur.

### 2. Başabaşa Taşıma (Breakeven Stop Loss - Sıfır Risk)
* **Açıklama:** %50 kâr alındığı anda, kalan %50'lik parçanın Zarar Kes (SL) seviyesi **işleme giriş fiyatına** taşınır.
* **Avantajı:** İşlem artık **%0 Riskli (Free Trade / Risksiz İşlem)** haline gelir. Fiyat terse dönse bile zarar edilmez.

### 3. Moonbag İz Süren SL (Trailing Stop - %1.5 Callback Rate)
* **Açıklama:** Kalan %50 miktar ("Moonbag"), Binance üzerinde `TRAILING_STOP_MARKET` emriyle trendin gidebildiği en derin noktaya kadar sürülür.
* **Avantajı:** Fenomenlerin büyük çöküşlerinden veya likidasyon avlarından maksimum kâr toplanır.

### 4. Dinamik ATR / Volatilite Tabanlı Seviye Belirleme
* **Açıklama:** Sabit yüzdeler yerine coin'in son 24 saatlik oynaklığına (ATR) göre dinamik TP/SL aralıkları belirleme.

### 5. Çoklu Telegram Kanalı ve Özel Kara Liste (Blacklist)
* **Açıklama:** Birden fazla kanalı aynı anda dinleme, başarı oranı düşük/yüksek kanalları skorlama ve düşük likiditeli pariteleri kara listeye alma desteği.

---

## 📌 1 Günlük Test Notları & İzleme Rehberi

1. **Canlı İzleme:** `python main.py --loop --interval 60` veya `python -m streamlit run app.py` ile sistemi 24 saat çalıştırın.
2. **Kontrol Edilecek Metrikler:**
   - Açılan pozisyonların ortalama kapanma süresi.
   - TP ve SL gerçekleşme oranları (Win/Loss Ratio).
   - Fenomen sinyallerinin ilk hedeften sonraki hareket derinliği (Moonbag ihtiyacının gözlemlenmesi).
