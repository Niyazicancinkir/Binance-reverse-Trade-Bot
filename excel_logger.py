import pandas as pd
import os
from datetime import datetime

DOSYA_ADI = "islem_gecmisi.xlsx"

def islemi_excel_kaydet(parite, yon, giris_fiyati, tp, sl, borsa_id, miktar=0.05):
    """
    Yeni açılan pozisyonu ve miktarını Excel dosyasına ekler.
    """
    yeni_kayit = {
        "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Parite": parite,
        "İşlem Yönü": yon,
        "Miktar": miktar,
        "Giriş Fiyatı": giris_fiyati,
        "Anlık Fiyat": giris_fiyati,
        "Kâr/Zarar ($)": "$0.00",
        "Kâr/Zarar (%)": "%0.00",
        "Hedef TP": tp,
        "Zarar Kes SL": sl,
        "Borsa Emir ID": borsa_id,
        "Durum": "Açık"
    }
    
    if os.path.exists(DOSYA_ADI):
        df_eski = pd.read_excel(DOSYA_ADI)
        df_yeni = pd.DataFrame([yeni_kayit])
        df_toplam = pd.concat([df_eski, df_yeni], ignore_index=True)
    else:
        df_toplam = pd.DataFrame([yeni_kayit])
        
    df_toplam.to_excel(DOSYA_ADI, index=False)
    print(f"[EXCEL] Yeni işlem '{DOSYA_ADI}' dosyasına başarıyla işlendi.")

def excel_kar_zarar_guncelle(borsa_istemcisi):
    """
    Binance'ten anlık fiyatı çeker; pozisyon miktarını baz alarak 
    hem yüzde (%) hem de Dolar ($) cinsinden net kâr/zarar tutarını günceller.
    """
    if not os.path.exists(DOSYA_ADI):
        return
        
    df = pd.read_excel(DOSYA_ADI)
    
    for idx, row in df.iterrows():
        if row["Durum"] == "Açık":
            try:
                parite = row["Parite"]
                yon = row["İşlem Yönü"]
                giris = float(row["Giriş Fiyatı"])
                islem_miktari = float(row.get("Miktar", 0.05)) # Kaydedilen miktarı al
                
                # Binance'ten güncel fiyatı al
                ticker = borsa_istemcisi.fetch_ticker(parite)
                anlik_fiyat = ticker['last']
                df.at[idx, "Anlık Fiyat"] = anlik_fiyat
                
                # 1. Yüzde PnL Hesaplama
                if yon == "LONG":
                    pnl_yuzde = ((anlik_fiyat - giris) / giris) * 100
                    fark = anlik_fiyat - giris
                else:  # SHORT pozisyon
                    pnl_yuzde = ((giris - anlik_fiyat) / giris) * 100
                    fark = giris - anlik_fiyat
                    
                # 2. Dolar ($) PnL Hesaplama (Fark * O pozisyona ait miktar)
                pnl_dolar = fark * islem_miktari
                
                df.at[idx, "Kâr/Zarar (%)"] = f"%{pnl_yuzde:.2f}"
                df.at[idx, "Kâr/Zarar ($)"] = f"${pnl_dolar:.2f}"
                
            except Exception as e:
                print(f"[EXCEL_GUNCELLEME_HATA] {row['Parite']} için fiyat alınamadı: {e}")
                
    df.to_excel(DOSYA_ADI, index=False)
    print("[EXCEL] PnL değerleri güncellendi.")