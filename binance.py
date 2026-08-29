import ccxt
import os
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from config import (
    BINANCE_API_KEY, 
    BINANCE_SECRET_KEY, 
    BINANCE_DEMO, 
    LEVERAGE, 
    MARGIN_MODE, 
    TRADE_AMOUNT_USDT
)
from excel_logger import islemi_excel_kaydet

_borsa_instance = None

def get_binance_client():
    """Binance CCXT istemcisini yapılandırır ve döndürür."""
    global _borsa_instance
    if _borsa_instance is None:
        _borsa_instance = ccxt.binance({
            'apiKey': BINANCE_API_KEY or "demo_key",
            'secret': BINANCE_SECRET_KEY or "demo_secret",
            'enableRateLimit': True,
            'verify': False,
            'options': {
                'defaultType': 'future',
                'adjustForTimeDifference': True,
                'fetchMarkets': ['linear']
            }
        })
        _borsa_instance.session.verify = False
        if BINANCE_DEMO:
            _borsa_instance.enable_demo_trading(True)
        try:
            _borsa_instance.load_time_difference()
        except Exception:
            pass
    return _borsa_instance

# Geriye dönük uyumluluk için varsayılan borsa nesnesi
borsa = get_binance_client()

def kaldirac_ve_marjin_ayarla(client, symbol: str, leverage: int = None, margin_mode: str = None):
    """
    Belirtilen parite için kaldıraç ve marjin modunu (ISOLATED/CROSSED) ayarlar.
    """
    lev = leverage or LEVERAGE
    m_mode = (margin_mode or MARGIN_MODE).upper()
    
    # 1. Kaldıraç Ayarı
    try:
        client.set_leverage(lev, symbol)
        print(f"[BORSA] {symbol} için Kaldıraç {lev}x olarak ayarlandı.")
    except Exception as e:
        print(f"[BORSA_UYARI] Kaldıraç ayarlanamadı: {e}")

    # 2. Marjin Modu Ayarı (ISOLATED / CROSSED)
    try:
        client.set_margin_mode(m_mode, symbol)
        print(f"[BORSA] {symbol} için Marjin Modu {m_mode} olarak ayarlandı.")
    except Exception as e:
        err_msg = str(e).lower()
        if "no need to change" in err_msg or "cannot be changed" in err_msg:
            print(f"[BORSA_BILGI] Marjin modu zaten {m_mode}.")
        else:
            print(f"[BORSA_UYARI] Marjin modu ayarlanamadı: {e}")

def miktar_hesapla(client, coin_pair: str, giris_fiyati: float, usdt_miktari: float = None, leverage: int = None) -> float:
    """
    Minimum borsa limitlerini ve kaldıraçlı USDT tutarını dikkate alarak emir adedini hesaplar.
    """
    hedef_usdt = usdt_miktari or TRADE_AMOUNT_USDT
    lev = leverage or LEVERAGE
    
    try:
        markets = client.load_markets()
        market_info = markets.get(coin_pair, {})
        limits = market_info.get('limits', {})
        min_amount = float(limits.get('amount', {}).get('min', 0.001) or 0.001)
        min_cost = float(limits.get('cost', {}).get('min', 5.0) or 5.0)
    except Exception:
        min_amount = 0.001
        min_cost = 5.0

    # Minimum borsa maliyet güvenliği (en az 6 USDT hacim)
    min_notional_usdt = max(min_cost, 6.0)
    
    # Toplam işlem hacmi = Kullanılan Marjin ($) * Kaldıraç
    toplam_islem_hacmi = max(hedef_usdt * lev, min_notional_usdt)
    hesaplanan_adet = toplam_islem_hacmi / giris_fiyati
    
    nihai_miktar = max(min_amount, hesaplanan_adet)
    
    try:
        nihai_miktar = float(client.amount_to_precision(coin_pair, nihai_miktar))
    except Exception:
        nihai_miktar = round(nihai_miktar, 4 if nihai_miktar < 1 else 2)
        
    return nihai_miktar

def tp_sl_fiyatlarini_dogrula(yon: str, giris_fiyati: float, tp: float = None, sl: float = None, 
                              client = None, coin_pair: str = None) -> tuple[float, float]:
    """
    Binance Futures kurallarına göre TP ve SL seviyelerini anlık fiyata göre doğrular ve düzeltir.
    Böylece 'Order would immediately trigger' (-2021) hatası kesin olarak engellenir.
    """
    yon_upper = yon.upper()
    nihai_tp = float(tp) if tp and str(tp) not in ["-", "None", "", "nan"] and float(tp) > 0 else None
    nihai_sl = float(sl) if sl and str(sl) not in ["-", "None", "", "nan"] and float(sl) > 0 else None
    
    if yon_upper == "LONG":
        # LONG için: TP > giriş, SL < giriş olmalıdır
        if nihai_tp and nihai_sl and (nihai_tp <= giris_fiyati and nihai_sl >= giris_fiyati):
            print("[BORSA_DUZELTME] TP ve SL seviyeleri LONG yönüne göre ters algılanmıştı, düzeltildi.")
            nihai_tp, nihai_sl = nihai_sl, nihai_tp
            
        if not nihai_tp or nihai_tp <= giris_fiyati:
            nihai_tp = giris_fiyati * 1.03
            
        if not nihai_sl or nihai_sl >= giris_fiyati:
            nihai_sl = giris_fiyati * 0.98
            
    else:  # SHORT
        # SHORT için: TP < giriş, SL > giriş olmalıdır
        if nihai_tp and nihai_sl and (nihai_tp >= giris_fiyati and nihai_sl <= giris_fiyati):
            print("[BORSA_DUZELTME] TP ve SL seviyeleri SHORT yönüne göre ters algılanmıştı, düzeltildi.")
            nihai_tp, nihai_sl = nihai_sl, nihai_tp
            
        if not nihai_tp or nihai_tp >= giris_fiyati:
            nihai_tp = giris_fiyati * 0.97
            
        if not nihai_sl or nihai_sl <= giris_fiyati:
            nihai_sl = giris_fiyati * 1.02

    # Borsa fiyat hassasiyetine (tick size) göre yuvarlama
    if client and coin_pair:
        try:
            if nihai_tp:
                nihai_tp = float(client.price_to_precision(coin_pair, nihai_tp))
            if nihai_sl:
                nihai_sl = float(client.price_to_precision(coin_pair, nihai_sl))
        except Exception:
            nihai_tp = round(nihai_tp, 6) if nihai_tp else None
            nihai_sl = round(nihai_sl, 6) if nihai_sl else None
    else:
        nihai_tp = round(nihai_tp, 6) if nihai_tp else None
        nihai_sl = round(nihai_sl, 6) if nihai_sl else None
        
    return nihai_tp, nihai_sl

def eksik_tp_sl_tamamla(client, coin_pair: str, yon: str, miktar: float, 
                        giris_fiyati: float, tp_hedef: float = None, sl_hedef: float = None, 
                        tp_id: str = None, sl_id: str = None) -> dict:
    """
    Açık pozisyonun eksik olan TP veya SL emirlerini tespit eder, 
    güvenli seviyeleri hesaplar ve Binance üzerinde otomatik olarak kurar.
    """
    ters_yon = "buy" if yon.upper() == "SHORT" else "sell"
    sonuc = {
        "tp_id": tp_id,
        "sl_id": sl_id,
        "tp_fiyat": tp_hedef,
        "sl_fiyat": sl_hedef,
        "guncellendi": False
    }
    
    tp_eksik = not tp_id or str(tp_id).strip() in ["-", "None", "", "nan"]
    sl_eksik = not sl_id or str(sl_id).strip() in ["-", "None", "", "nan"]
    
    if not (tp_eksik or sl_eksik):
        return sonuc

    # Güncel piyasa fiyatını al
    try:
        ticker = client.fetch_ticker(coin_pair)
        anlik_fiyat = float(ticker['last'])
    except Exception:
        anlik_fiyat = giris_fiyati
        
    gecerli_tp, gecerli_sl = tp_sl_fiyatlarini_dogrula(
        yon=yon, 
        giris_fiyati=anlik_fiyat, 
        tp=tp_hedef, 
        sl=sl_hedef, 
        client=client, 
        coin_pair=coin_pair
    )

    # 1. Eksik TP Emrini Kur
    if tp_eksik and gecerli_tp:
        try:
            tp_params = {'stopPrice': float(gecerli_tp), 'reduceOnly': True}
            tp_emir = client.create_order(
                symbol=coin_pair,
                type='TAKE_PROFIT_MARKET',
                side=ters_yon,
                amount=miktar,
                params=tp_params
            )
            yeni_tp_id = str(tp_emir.get('id', 'N/A'))
            sonuc["tp_id"] = yeni_tp_id
            sonuc["tp_fiyat"] = gecerli_tp
            sonuc["guncellendi"] = True
            print(f"[OTO_KORUMA] {coin_pair} ({yon}) için eksik TP emri kuruldu: ${gecerli_tp} (ID: {yeni_tp_id})")
        except Exception as e:
            print(f"[OTO_KORUMA_UYARI] {coin_pair} için TP emri kurulamadı: {e}")

    # 2. Eksik SL Emrini Kur
    if sl_eksik and gecerli_sl:
        try:
            sl_params = {'stopPrice': float(gecerli_sl), 'reduceOnly': True}
            sl_emir = client.create_order(
                symbol=coin_pair,
                type='STOP_MARKET',
                side=ters_yon,
                amount=miktar,
                params=sl_params
            )
            yeni_sl_id = str(sl_emir.get('id', 'N/A'))
            sonuc["sl_id"] = yeni_sl_id
            sonuc["sl_fiyat"] = gecerli_sl
            sonuc["guncellendi"] = True
            print(f"[OTO_KORUMA] {coin_pair} ({yon}) için eksik SL emri kuruldu: ${gecerli_sl} (ID: {yeni_sl_id})")
        except Exception as e:
            print(f"[OTO_KORUMA_UYARI] {coin_pair} için SL emri kurulamadı: {e}")

    return sonuc

def emri_baslat(coin_pair: str, yon: str, bizim_tp: float = None, bizim_sl: float = None, 
                usdt_miktari: float = None, leverage: int = None, margin_mode: str = None, 
                client_override = None) -> dict:
    """
    Ana piyasa emrini açar ve ardından borsaya doğrulanmış otomatik TP ve SL koşullu emirlerini iletir.
    """
    client = client_override or get_binance_client()
    lev = leverage or LEVERAGE
    m_mode = margin_mode or MARGIN_MODE
    
    sonuc = {
        "success": False,
        "main_order_id": None,
        "tp_order_id": None,
        "sl_order_id": None,
        "entry_price": 0.0,
        "amount": 0.0,
        "error": None
    }
    
    try:
        ccxt_yon = "sell" if yon.upper() == "SHORT" else "buy"
        ters_yon = "buy" if yon.upper() == "SHORT" else "sell"
        
        # 1. Kaldıraç ve Marjin Yapılandırması
        kaldirac_ve_marjin_ayarla(client, coin_pair, lev, m_mode)
        
        # 2. Güncel Fiyat ve Miktar Belirleme
        ticker = client.fetch_ticker(coin_pair)
        giris_fiyati = float(ticker['last'])
        miktar = miktar_hesapla(client, coin_pair, giris_fiyati, usdt_miktari, lev)
        
        # 3. TP ve SL Seviyelerini Anlık Fiyata Göre Doğrula & Düzelt (Binance -2021 Hatasını Önler)
        gecerli_tp, gecerli_sl = tp_sl_fiyatlarini_dogrula(
            yon=yon, 
            giris_fiyati=giris_fiyati, 
            tp=bizim_tp, 
            sl=bizim_sl, 
            client=client, 
            coin_pair=coin_pair
        )
        
        print(f"[BORSA] Ana Emir iletiliyor: {coin_pair} | Yön: {yon} | Miktar: {miktar} (~${miktar * giris_fiyati:.2f}) | Kaldıraç: {lev}x")
        
        # 4. Ana Market Pozisyonunu Aç
        ana_emir = client.create_market_order(coin_pair, ccxt_yon, miktar)
        main_order_id = str(ana_emir.get('id', 'N/A'))
        
        sonuc["success"] = True
        sonuc["main_order_id"] = main_order_id
        sonuc["entry_price"] = giris_fiyati
        sonuc["amount"] = miktar
        
        print("\n" + "="*65)
        print(f">>> [ORDER_EXECUTED] Ana Pozisyon Açıldı! <<<")
        print(f">>> Borsa Yanıt ID : {main_order_id}")
        print(f">>> Parite         : {coin_pair}")
        print(f">>> Pozisyon Yönü  : {yon} ({miktar} birim)")
        print(f">>> Giriş Fiyatı   : ${giris_fiyati:.4f}")
        print(f">>> Kaldıraç / Mod : {lev}x ({m_mode})")
        
        # 5. Otomatik TP (Take Profit) Emri İlet
        tp_order_id = None
        if gecerli_tp and gecerli_tp > 0:
            try:
                tp_params = {
                    'stopPrice': float(gecerli_tp),
                    'reduceOnly': True
                }
                tp_emir = client.create_order(
                    symbol=coin_pair,
                    type='TAKE_PROFIT_MARKET',
                    side=ters_yon,
                    amount=miktar,
                    params=tp_params
                )
                tp_order_id = str(tp_emir.get('id', 'N/A'))
                sonuc["tp_order_id"] = tp_order_id
                print(f">>> [TP_ORDER] Otomatik Kâr Al Emri Kuruldu: ${gecerli_tp} (ID: {tp_order_id})")
            except Exception as e:
                print(f"[BORSA_UYARI] TP Emri kurulamadı: {e}")
        
        # 6. Otomatik SL (Stop Loss) Emri İlet
        sl_order_id = None
        if gecerli_sl and gecerli_sl > 0:
            try:
                sl_params = {
                    'stopPrice': float(gecerli_sl),
                    'reduceOnly': True
                }
                sl_emir = client.create_order(
                    symbol=coin_pair,
                    type='STOP_MARKET',
                    side=ters_yon,
                    amount=miktar,
                    params=sl_params
                )
                sl_order_id = str(sl_emir.get('id', 'N/A'))
                sonuc["sl_order_id"] = sl_order_id
                print(f">>> [SL_ORDER] Otomatik Zarar Kes Emri Kuruldu: ${gecerli_sl} (ID: {sl_order_id})")
            except Exception as e:
                print(f"[BORSA_UYARI] SL Emri kurulamadı: {e}")
                
        print("="*65 + "\n")
        
        # 7. Excel Dosyasına Kayıt
        islemi_excel_kaydet(
            parite=coin_pair,
            yon=yon,
            giris_fiyati=giris_fiyati,
            tp=gecerli_tp,
            sl=gecerli_sl,
            borsa_id=main_order_id,
            miktar=miktar,
            kaldirac=lev,
            tp_id=tp_order_id,
            sl_id=sl_order_id
        )
        
        return sonuc
        
    except Exception as e:
        print(f"[BORSA_HATA] {e}")
        sonuc["error"] = str(e)
        return sonuc