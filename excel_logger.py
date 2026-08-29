import os
import pandas as pd
from datetime import datetime
from config import EXCEL_FILE

def get_excel_path(dosya_yolu: str = None) -> str:
    return dosya_yolu or EXCEL_FILE

def _tipleri_duzenle(df: pd.DataFrame) -> pd.DataFrame:
    """Arrow uyumluluğu için karışık tip içerebilecek sütunları güvenli string formatına çevirir."""
    metin_sutunlari = [
        "Parite", "İşlem Yönü", "Kaldıraç", "Kâr/Zarar ($)", "Kâr/Zarar (%)",
        "Borsa Emir ID", "TP Emir ID", "SL Emir ID", "Kapanış Fiyatı", 
        "Kapanış Tarihi", "Durum", "Hedef TP", "Zarar Kes SL"
    ]
    for col in metin_sutunlari:
        if col in df.columns:
            df[col] = df[col].astype(str).replace({"nan": "-", "None": "-", "": "-"})
    return df

def islemi_excel_kaydet(parite: str, yon: str, giris_fiyati: float, tp: float, sl: float, 
                        borsa_id: str, miktar: float = 0.05, kaldirac: int = 5, 
                        tp_id: str = None, sl_id: str = None, dosya_yolu: str = None):
    """
    Yeni açılan pozisyonu, TP/SL emir ID'lerini ve kaldıraç bilgisini Excel'e kaydeder.
    """
    hedef_dosya = get_excel_path(dosya_yolu)
    
    yeni_kayit = {
        "Tarih": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Parite": str(parite),
        "İşlem Yönü": str(yon).upper(),
        "Kaldıraç": f"{kaldirac}x",
        "Miktar": float(miktar),
        "Giriş Fiyatı": float(giris_fiyati),
        "Anlık Fiyat": float(giris_fiyati),
        "Kâr/Zarar ($)": "$0.00",
        "Kâr/Zarar (%)": "%0.00",
        "Hedef TP": str(tp) if tp is not None else "-",
        "Zarar Kes SL": str(sl) if sl is not None else "-",
        "Borsa Emir ID": str(borsa_id),
        "TP Emir ID": str(tp_id) if tp_id and str(tp_id) != "None" else "-",
        "SL Emir ID": str(sl_id) if sl_id and str(sl_id) != "None" else "-",
        "Kapanış Fiyatı": "-",
        "Kapanış Tarihi": "-",
        "Durum": "Açık"
    }
    
    if os.path.exists(hedef_dosya):
        try:
            df_eski = pd.read_excel(hedef_dosya)
            df_yeni = pd.DataFrame([yeni_kayit])
            df_toplam = pd.concat([df_eski, df_yeni], ignore_index=True)
        except Exception:
            df_toplam = pd.DataFrame([yeni_kayit])
    else:
        df_toplam = pd.DataFrame([yeni_kayit])
        
    df_toplam = _tipleri_duzenle(df_toplam)
    df_toplam.to_excel(hedef_dosya, index=False)
    print(f"[EXCEL] Yeni işlem '{hedef_dosya}' dosyasına başarıyla işlendi.")

def paritede_acik_pozisyon_var_mi(parite: str, dosya_yolu: str = None) -> bool:
    """Verilen parite için Excel'de açık durumda bir pozisyon olup olmadığını denetler."""
    hedef_dosya = get_excel_path(dosya_yolu)
    if not os.path.exists(hedef_dosya):
        return False
    try:
        df = pd.read_excel(hedef_dosya)
        if df.empty or "Durum" not in df.columns or "Parite" not in df.columns:
            return False
        aciklar = df[(df["Durum"] == "Açık") & (df["Parite"] == parite)]
        return len(aciklar) > 0
    except Exception as e:
        print(f"[EXCEL_UYARI] Pozisyon kontrolü yapılamadı: {e}")
        return False

def excel_kar_zarar_guncelle(borsa_istemcisi, dosya_yolu: str = None):
    """
    Binance üzerinden açık pozisyonları sorgular (fetch_positions).
    Borsada kapanan pozisyonları 'Kapalı' olarak günceller ve net PnL hesaplar.
    Açık kalan pozisyonlar için eksik TP/SL emirlerini tamamlar ve canlı PnL günceller.
    """
    hedef_dosya = get_excel_path(dosya_yolu)
    if not os.path.exists(hedef_dosya):
        return
        
    try:
        df = pd.read_excel(hedef_dosya)
        df = _tipleri_duzenle(df)
    except Exception as e:
        print(f"[EXCEL_HATA] Dosya okunamadı: {e}")
        return
        
    if df.empty:
        return

    # 1. Binance üzerindeki tüm canlı açık pozisyonları al
    acik_borsa_pozisyonlari = {}
    if borsa_istemcisi is not None:
        try:
            positions = borsa_istemcisi.fetch_positions()
            for p in positions:
                contracts = float(p.get('contracts', 0) or 0)
                if contracts > 0:
                    sym = p.get('symbol', '').split(':')[0].strip().upper()
                    acik_borsa_pozisyonlari[sym] = p
        except Exception as e:
            print(f"[EXCEL_UYARI] Borsa açık pozisyonları sorgulanamadı: {e}")

    degisiklik_oldu = False
    
    for idx, row in df.iterrows():
        if str(row.get("Durum")) == "Açık":
            try:
                parite = str(row["Parite"]).strip().upper()
                yon = str(row["İşlem Yönü"]).upper()
                giris = float(row["Giriş Fiyatı"])
                miktar = float(row.get("Miktar", 0.05))
                tp_id = str(row.get("TP Emir ID", "-")).strip()
                sl_id = str(row.get("SL Emir ID", "-")).strip()
                hedef_tp = float(row["Hedef TP"]) if str(row.get("Hedef TP")) not in ["-", "nan", "None"] else None
                zarar_sl = float(row["Zarar Kes SL"]) if str(row.get("Zarar Kes SL")) not in ["-", "nan", "None"] else None

                # 2. Anlık fiyatı çek
                anlik_fiyat = None
                if borsa_istemcisi is not None:
                    try:
                        ticker = borsa_istemcisi.fetch_ticker(parite)
                        anlik_fiyat = float(ticker['last'])
                    except Exception:
                        pass

                if anlik_fiyat is not None:
                    df.at[idx, "Anlık Fiyat"] = anlik_fiyat

                # 3. Pozisyon Borsada Açık mı Kapandı mı?
                borsada_hala_acik = (parite in acik_borsa_pozisyonlari) if borsa_istemcisi is not None else True

                if not borsada_hala_acik and borsa_istemcisi is not None:
                    # Pozisyon borsada kapanmış (TP veya SL tetiklendi)
                    kapanis_nedeni = "Kapalı"
                    kapanis_fiyati = anlik_fiyat or giris

                    if hedef_tp and anlik_fiyat:
                        if yon == "LONG" and anlik_fiyat >= hedef_tp * 0.998:
                            kapanis_nedeni = "Kapalı - TP Tetiklendi"
                            kapanis_fiyati = hedef_tp
                        elif yon == "SHORT" and anlik_fiyat <= hedef_tp * 1.002:
                            kapanis_nedeni = "Kapalı - TP Tetiklendi"
                            kapanis_fiyati = hedef_tp

                    if zarar_sl and anlik_fiyat and kapanis_nedeni == "Kapalı":
                        if yon == "LONG" and anlik_fiyat <= zarar_sl * 1.002:
                            kapanis_nedeni = "Kapalı - SL Tetiklendi"
                            kapanis_fiyati = zarar_sl
                        elif yon == "SHORT" and anlik_fiyat >= zarar_sl * 0.998:
                            kapanis_nedeni = "Kapalı - SL Tetiklendi"
                            kapanis_fiyati = zarar_sl

                    if kapanis_nedeni == "Kapalı":
                        kapanis_nedeni = "Kapalı - Borsa Emri Doldu"

                    # Net Realize PnL Hesapla
                    if yon == "LONG":
                        pnl_yuzde = ((kapanis_fiyati - giris) / giris) * 100
                        pnl_dolar = (kapanis_fiyati - giris) * miktar
                    else:
                        pnl_yuzde = ((giris - kapanis_fiyati) / giris) * 100
                        pnl_dolar = (giris - kapanis_fiyati) * miktar

                    df.at[idx, "Durum"] = kapanis_nedeni
                    df.at[idx, "Anlık Fiyat"] = kapanis_fiyati
                    df.at[idx, "Kapanış Fiyatı"] = str(round(kapanis_fiyati, 4))
                    df.at[idx, "Kapanış Tarihi"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    df.at[idx, "Kâr/Zarar (%)"] = f"%{pnl_yuzde:.2f}"
                    df.at[idx, "Kâr/Zarar ($)"] = f"${pnl_dolar:.2f}"

                    print(f"[EXCEL] {parite} ({yon}) pozisyonu kapandı: {kapanis_nedeni} (PnL: ${pnl_dolar:.2f} / %{pnl_yuzde:.2f})")
                    degisiklik_oldu = True

                else:
                    # Pozisyon hala açık: Anlık PnL hesapla & Eksik TP/SL varsa kur
                    if anlik_fiyat is not None:
                        if yon == "LONG":
                            pnl_yuzde = ((anlik_fiyat - giris) / giris) * 100
                            pnl_dolar = (anlik_fiyat - giris) * miktar
                        else:
                            pnl_yuzde = ((giris - anlik_fiyat) / giris) * 100
                            pnl_dolar = (giris - anlik_fiyat) * miktar

                        df.at[idx, "Kâr/Zarar (%)"] = f"%{pnl_yuzde:.2f}"
                        df.at[idx, "Kâr/Zarar ($)"] = f"${pnl_dolar:.2f}"
                        degisiklik_oldu = True

                    # Eksik TP/SL varsa tamamla
                    if borsa_istemcisi is not None and (tp_id in ["-", "None", "", "nan"] or sl_id in ["-", "None", "", "nan"]):
                        try:
                            from binance import eksik_tp_sl_tamamla
                            onarim = eksik_tp_sl_tamamla(
                                client=borsa_istemcisi,
                                coin_pair=parite,
                                yon=yon,
                                miktar=miktar,
                                giris_fiyati=giris,
                                tp_hedef=hedef_tp,
                                sl_hedef=zarar_sl,
                                tp_id=tp_id,
                                sl_id=sl_id
                            )
                            if onarim.get("guncellendi"):
                                df.at[idx, "TP Emir ID"] = str(onarim.get("tp_id", tp_id))
                                df.at[idx, "SL Emir ID"] = str(onarim.get("sl_id", sl_id))
                                if onarim.get("tp_fiyat"):
                                    df.at[idx, "Hedef TP"] = str(onarim["tp_fiyat"])
                                if onarim.get("sl_fiyat"):
                                    df.at[idx, "Zarar Kes SL"] = str(onarim["sl_fiyat"])
                                degisiklik_oldu = True
                        except Exception as e:
                            print(f"[EXCEL_UYARI] {parite} için oto-onarım çağrılamadı: {e}")

            except Exception as e:
                print(f"[EXCEL_GUNCELLEME_HATA] {row.get('Parite')} güncellenemedi: {e}")

    if degisiklik_oldu:
        df = _tipleri_duzenle(df)
        df.to_excel(hedef_dosya, index=False)
        print("[EXCEL] PnL ve pozisyon kapanışları başarıyla güncellendi.")