import ccxt
import os
import time
from excel_logger import islemi_excel_kaydet

API_KEY ="BINANCE_API_KEY"
SECRET_KEY ="BINANCE_SECRET_KEY"

borsa = ccxt.binance({
    'apiKey': API_KEY,
    'secret': SECRET_KEY,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
        'adjustForTimeDifference': True
    }
})
borsa.enable_demo_trading(True)
borsa.load_time_difference()

def emri_baslat(coin_pair, yon, bizim_tp, bizim_sl):
    try:
        ccxt_yon = "sell" if yon == "SHORT" else "buy"
        
        ticker = borsa.fetch_ticker(coin_pair)
        giris_fiyati = ticker['last']
        
        markets = borsa.load_markets()
        market_info = markets.get(coin_pair, {})
        min_amount = market_info.get('limits', {}).get('amount', {}).get('min', 1.0)
        
        min_hacim_adedi = 6.0 / giris_fiyati
        
        miktar = max(min_amount, min_hacim_adedi)
        
        miktar = round(miktar, 2) if miktar > 1 else round(miktar, 4)
        
        print(f"[BORSA] Emir iletiliyor: {coin_pair} | Yön: {yon} | Miktar: {miktar} (~${miktar * giris_fiyati:.2f})")
        
        emir = borsa.create_market_order(coin_pair, ccxt_yon, miktar)
        
        print("\n" + "="*60)
        print(f">>> [ORDER_EXECUTED] Ana Pozisyon Açıldı! <<<")
        print(f">>> Borsa Yanıt ID : {emir['id']}")
        print(f">>> Parite         : {coin_pair}")
        print(f">>> Pozisyon Yönü  : {yon} ({miktar} birim)")
        print(f">>> Giriş Fiyatı   : ${giris_fiyati}")
        if bizim_tp:
            print(f">>> Inverse TP     : ${bizim_tp}")
        if bizim_sl:
            print(f">>> Inverse SL     : ${bizim_sl}")
        print("="*60 + "\n")
        
        islemi_excel_kaydet(coin_pair, yon, giris_fiyati, bizim_tp, bizim_sl, emir['id'], miktar)
        
    except Exception as e:
        print(f"[BORSA_HATA] {e}")