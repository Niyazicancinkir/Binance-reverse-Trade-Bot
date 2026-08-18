import time
from telegram import bugunun_mesajlarini_cek
from gemini import sinyali_cozumle
from binance import emri_baslat

HEDEF_KANAL = "cryptosignals0rg"

def main():
    print(f"\n[SİSTEM MERKEZİ] Otonom Bot Başlatıldı (Kota Korumalı Tarayıcı).")
    print(f"[TARANIYOR] Kanal: @{HEDEF_KANAL}\n")
    
    mesajlar = bugunun_mesajlarini_cek(HEDEF_KANAL)
    
    if not mesajlar:
        print("[BILGI] Kanalda hiç mesaj bulunamadı.")
        return
        
    gecerli_sinyal = None
    kritik_kelimeler = ["signal", "buy", "sell", "long", "short", "entry", "tp", "sl"]
    
    for mesaj in reversed(mesajlar):  
        mesaj_kucuk = mesaj.lower()
        
        # Finansal anahtar kelime içermeyen mesajları Gemini'a göndermeden eliyoruz (Kota Koruma)
        if not any(kelime in mesaj_kucuk for kelime in kritik_kelimeler):
            print(f"[PAS GEÇİLDİ - FİLTRE] Finansal anahtar kelime yok.")
            continue
            
        print(f"[ANALİZ EDİLİYOR (AI)]: {mesaj[:80]}...")
        analiz = sinyali_cozumle(mesaj)
        
        if analiz.get("is_signal"):
            gecerli_sinyal = analiz
            print(f"[BAŞARILI] Güncel bir sinyal yakalandı!\n")
            break
        else:
            print(f"[PAS GEÇİLDİ] AI bu mesajı sinyal onaylamadı.\n")
            
    if gecerli_sinyal:
        print(f"[SİSTEM ONAYI] Strateji Devrede!")
        print(f"  -> Fenomen Yönü : {gecerli_sinyal['fenomen_yonu']}")
        print(f"  -> Bizim Yönümüz: {gecerli_sinyal['bizim_yonumuz']} (Tersine Çevrildi)")
        print(f"  -> Hedef Parite : {gecerli_sinyal['coin_pair']}")
        print(f"  -> Hesaplanan TP: {gecerli_sinyal.get('bizim_tp')}")
        print(f"  -> Hesaplanan SL: {gecerli_sinyal.get('bizim_sl')}\n")
        
        emri_baslat(
            gecerli_sinyal['coin_pair'], 
            gecerli_sinyal['bizim_yonumuz'],
            gecerli_sinyal.get('bizim_tp'),
            gecerli_sinyal.get('bizim_sl')
        )
    else:
        print("[BİLGİ] İşleme uygun geçerli bir sinyal bulunamadı.")

if __name__ == "__main__":
    main()