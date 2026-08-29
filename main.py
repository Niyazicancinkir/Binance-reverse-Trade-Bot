import argparse
import sys
import time
from config import (
    TELEGRAM_CHANNEL, 
    SCAN_INTERVAL_SECONDS, 
    AUTO_LOOP,
    LEVERAGE,
    MARGIN_MODE,
    TRADE_AMOUNT_USDT
)
from telegram import bugunun_mesajlarini_cek
from gemini import sinyali_cozumle
from binance import emri_baslat, borsa
from tracker import sinyal_islendi_mi, sinyali_kaydet
from excel_logger import excel_kar_zarar_guncelle, paritede_acik_pozisyon_var_mi

KRITIK_KELIMELER = ["signal", "buy", "sell", "long", "short", "entry", "tp", "sl", "target", "leverage"]

def tek_tarama_yap(hedef_kanal: str = None) -> int:
    """
    Kanalı bir kez tarar, açık pozisyon PnL'lerini günceller ve yeni sinyalleri işler.
    İşleme alınan yeni sinyal adedini döndürür.
    """
    kanal = hedef_kanal or TELEGRAM_CHANNEL
    print(f"\n[TARANIYOR] Kanal: @{kanal} | {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. Mevcut açık pozisyonların kâr/zararını ve TP/SL durumunu güncelle
    try:
        excel_kar_zarar_guncelle(borsa)
    except Exception as e:
        print(f"[UYARI] PnL güncelleme hatası: {e}")
        
    # 2. Mesajları çek
    mesajlar = bugunun_mesajlarini_cek(kanal)
    if not mesajlar:
        print("[BILGI] Kanalda yeni mesaj bulunamadı.")
        return 0
        
    yeni_islem_sayisi = 0
    
    # En yeni mesajdan eskiye doğru incele
    for mesaj in reversed(mesajlar):
        # 3. İdempotency Kontrolü: Bu mesaj daha önce işlendi mi?
        if sinyal_islendi_mi(mesaj):
            print(f"[PAS GEÇİLDİ - HAFIZA] Bu mesaj daha önce işleme alınmış.")
            continue
            
        mesaj_kucuk = mesaj.lower()
        # 4. Kota Koruma: Finansal kelime içermiyorsa Gemini'a gönderme
        if not any(kelime in mesaj_kucuk for kelime in KRITIK_KELIMELER):
            print(f"[PAS GEÇİLDİ - FİLTRE] Finansal anahtar kelime yok.")
            continue
            
        print(f"[ANALİZ EDİLİYOR (AI)]: {mesaj[:70]}...")
        analiz = sinyali_cozumle(mesaj)
        
        if analiz.get("is_signal"):
            coin_pair = analiz.get("coin_pair")
            
            # 5. Aynı paritede hâlihazırda açık pozisyon var mı?
            if paritede_acik_pozisyon_var_mi(coin_pair):
                print(f"[UYARI] {coin_pair} için zaten açık bir pozisyon mevcut. Mükerrer işlem engellendi.")
                sinyali_kaydet(mesaj, analiz)
                continue
                
            print(f"\n🎯 [BAŞARILI] Yeni Ters Sinyal Yakalandı!")
            print(f"  -> Orijinal Sinyal : {analiz.get('fenomen_yonu')} {coin_pair}")
            print(f"  -> Bizim Yönümüz   : {analiz.get('bizim_yonumuz')} (TERSE ÇEVRİLDİ)")
            print(f"  -> Hesaplanan TP   : {analiz.get('bizim_tp')}")
            print(f"  -> Hesaplanan SL   : {analiz.get('bizim_sl')}\n")
            
            # 6. Sinyali önce hafızaya kaydet
            sinyali_kaydet(mesaj, analiz)
            
            # 7. Binance üzerinde emri ve TP/SL'i başlat
            emri_baslat(
                coin_pair=coin_pair,
                yon=analiz['bizim_yonumuz'],
                bizim_tp=analiz.get('bizim_tp'),
                bizim_sl=analiz.get('bizim_sl'),
                usdt_miktari=TRADE_AMOUNT_USDT,
                leverage=LEVERAGE,
                margin_mode=MARGIN_MODE
            )
            yeni_islem_sayisi += 1
            break  # Tek taramada en taze 1 sinyali işleyip bitir
        else:
            print(f"[PAS GEÇİLDİ] AI bu mesajı işlem sinyali olarak onaylamadı.")
            
    return yeni_islem_sayisi

def main():
    parser = argparse.ArgumentParser(description="Binance Tersine İşlem Botu")
    parser.add_argument("--loop", action="store_true", help="Botu sürekli döngü modunda çalıştırır.")
    parser.add_argument("--channel", type=str, default=None, help="Hedef Telegram kanal adı.")
    parser.add_argument("--interval", type=int, default=None, help="Tarama aralığı (saniye).")
    args = parser.parse_args()
    
    surekli_dongu = args.loop or AUTO_LOOP
    aralik = args.interval or SCAN_INTERVAL_SECONDS
    hedef_kanal = args.channel or TELEGRAM_CHANNEL
    
    print("\n" + "="*60)
    print(" ⚡ BINANCE REVERSE TRADE BOT (OTONOM MERKEZ)")
    print(f"  -> Hedef Kanal      : @{hedef_kanal}")
    print(f"  -> Kaldıraç / Marjin: {LEVERAGE}x ({MARGIN_MODE})")
    print(f"  -> İşlem Büyüklüğü  : ~${TRADE_AMOUNT_USDT} USDT")
    print(f"  -> Çalışma Modu     : {'Sürekli Döngü (' + str(aralik) + ' sn)' if surekli_dongu else 'Tek Seferlik Tarama'}")
    print("="*60)
    
    if not surekli_dongu:
        tek_tarama_yap(hedef_kanal)
        print("\n[TAMAMLANDI] Tek seferlik tarama bitti.")
        return
        
    print("\n[OTOMASYON BAŞLADI] Durdurmak için Ctrl+C tuşlayabilirsiniz...\n")
    try:
        while True:
            tek_tarama_yap(hedef_kanal)
            print(f"[BEKLENİYOR] Bir sonraki tarama {aralik} saniye sonra...")
            time.sleep(aralik)
    except KeyboardInterrupt:
        print("\n[DURDURULDU] Bot kullanıcı tarafından kapatıldı.")
        sys.exit(0)

if __name__ == "__main__":
    main()
