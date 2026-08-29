import os
import pandas as pd
import streamlit as st
from config import (
    TELEGRAM_CHANNEL, 
    LEVERAGE, 
    MARGIN_MODE, 
    TRADE_AMOUNT_USDT, 
    EXCEL_FILE,
    BINANCE_DEMO
)
from telegram import bugunun_mesajlarini_cek
from gemini import sinyali_cozumle
from binance import emri_baslat, borsa
from tracker import sinyal_islendi_mi, sinyali_kaydet, hafizayi_temizle
from excel_logger import excel_kar_zarar_guncelle, paritede_acik_pozisyon_var_mi, _tipleri_duzenle

st.set_page_config(
    page_title="Tersine İşlem Botu | Kontrol Paneli",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Başlangıç Senkronizasyonu
if "init_sync" not in st.session_state:
    if os.path.exists(EXCEL_FILE):
        try:
            excel_kar_zarar_guncelle(borsa)
        except Exception:
            pass
    st.session_state["init_sync"] = True

# Başlık
st.title("⚡ Tersine İşlem Botu (Reverse Signal Engine)")
st.caption("Yapay Zeka Destekli Otonom Sinyal Tersleme, Otomatik TP/SL ve Vadeli İşlem Kontrol Paneli")

# Sidebar
st.sidebar.header("🎛️ İşlem & Risk Ayarları")
kanal_secimi = st.sidebar.text_input("Hedef Telegram Kanalı", value=TELEGRAM_CHANNEL)
kaldirac_secimi = st.sidebar.slider("Kaldıraç (x)", min_value=1, max_value=20, value=LEVERAGE)
marjin_secimi = st.sidebar.selectbox("Marjin Tipi", ["ISOLATED", "CROSSED"], index=0 if MARGIN_MODE == "ISOLATED" else 1)
usdt_tutari = st.sidebar.number_input("İşlem Başına Tutar (USDT)", min_value=5.0, max_value=500.0, value=float(TRADE_AMOUNT_USDT), step=5.0)

st.sidebar.divider()
calistir_butonu = st.sidebar.button("🚀 Sinyal Tara & İşlemi Başlat", width="stretch")

with st.sidebar.expander("🛠️ Gelişmiş Ayarlar"):
    if st.button("🗑️ Sinyal Hafızasını Sıfırla", width="stretch"):
        hafizayi_temizle()
        st.success("İşlenmiş sinyal hafızası temizlendi!")

# Metrikler
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Borsa Modu", value="Binance Demo" if BINANCE_DEMO else "Binance Canlı", delta="USD-M Futures")
with col2:
    st.metric(label="Strateji", value="Inverse (Tersine)", delta="LONG ⇄ SHORT")
with col3:
    st.metric(label="Kaldıraç & Mod", value=f"{kaldirac_secimi}x", delta=marjin_secimi)
with col4:
    st.metric(label="İşlem Büyüklüğü", value=f"~${usdt_tutari:.1f} USDT")

st.divider()

# --- TABLO VE RAPOR BÖLÜMÜ ---
st.subheader("📁 Pozisyon Geçmişi ve Canlı PnL Raporu")

col_baslik, col_guncelle = st.columns([5, 1])
with col_guncelle:
    guncelle_tiklandi = st.button("🔄 PnL & Durum Güncelle", width="stretch")

if guncelle_tiklandi:
    with st.spinner("Binance verileri çekiliyor ve TP/SL durumları kontrol ediliyor..."):
        try:
            excel_kar_zarar_guncelle(borsa)
            st.success("Tablo ve emir durumları başarıyla güncellendi!")
        except Exception as e:
            st.error(f"Güncelleme hatası: {e}")

if os.path.exists(EXCEL_FILE):
    try:
        df_gecmis = pd.read_excel(EXCEL_FILE)
        if not df_gecmis.empty:
            df_gecmis = _tipleri_duzenle(df_gecmis)
            
            # Durum Filtresi
            filtre = st.radio("Filtrele:", ["Tümü", "Sadece Açık Pozisyonlar", "Kapananlar"], horizontal=True)
            if filtre == "Sadece Açık Pozisyonlar":
                df_goster = df_gecmis[df_gecmis["Durum"] == "Açık"]
            elif filtre == "Kapananlar":
                df_goster = df_gecmis[df_gecmis["Durum"] != "Açık"]
            else:
                df_goster = df_gecmis
                
            st.dataframe(df_goster, width="stretch")
        else:
            st.info("Kayıtlı işlem bulunmuyor.")
    except Exception as e:
        st.error(f"Excel dosyası okunamadı: {e}")
else:
    st.info("Henüz kaydedilmiş bir işlem dosyası bulunmuyor. İlk işlem açıldığında otomatik oluşturulacaktır.")

st.divider()

# --- SİNYAL AKIŞI ---
st.subheader("📊 Canlı Sinyal Tarama ve Emir Yürütme")

if calistir_butonu:
    with st.spinner(f"@{kanal_secimi} taranıyor ve yapay zeka analiz yapıyor..."):
        mesajlar = bugunun_mesajlarini_cek(kanal_secimi)
        
        if not mesajlar:
            st.error("Kanalda okunabilecek mesaj bulunamadı.")
        else:
            gecerli_sinyal = None
            secilen_ham_mesaj = ""
            atlanan_mesajlar = 0
            
            for mesaj in reversed(mesajlar):
                if sinyal_islendi_mi(mesaj):
                    atlanan_mesajlar += 1
                    continue
                    
                analiz = sinyali_cozumle(mesaj)
                if analiz.get("is_signal"):
                    gecerli_sinyal = analiz
                    secilen_ham_mesaj = mesaj
                    break
            
            if gecerli_sinyal:
                coin_pair = gecerli_sinyal.get("coin_pair")
                
                if paritede_acik_pozisyon_var_mi(coin_pair):
                    st.warning(f"⚠️ {coin_pair} paritesinde hâlihazırda açık bir işlem var. Mükerrer emir engellendi.")
                    sinyali_kaydet(secilen_ham_mesaj, gecerli_sinyal)
                else:
                    st.success("🎯 Yeni ve İşlenebilir Sinyal Yakalandı!")
                    
                    c_sol, c_sag = st.columns(2)
                    with c_sol:
                        st.markdown("### 📥 Yakalanan Ham Mesaj")
                        st.info(secilen_ham_mesaj)
                        
                    with c_sag:
                        st.markdown("### 🧠 AI Tersine Strateji Çıktısı")
                        st.json(gecerli_sinyal)
                    
                    st.markdown("### ⚙️ Borsa Yürütme Logları")
                    with st.status("Emir ve TP/SL Binance Demo sunucusuna iletiliyor...", expanded=True) as status:
                        st.write(f"Parite: {coin_pair} | Bizim Yönümüz: {gecerli_sinyal['bizim_yonumuz']}")
                        st.write(f"Kaldıraç: {kaldirac_secimi}x | Marjin: {marjin_secimi}")
                        st.write(f"Inverse TP: {gecerli_sinyal.get('bizim_tp')} | Inverse SL: {gecerli_sinyal.get('bizim_sl')}")
                        
                        try:
                            # Sinyali önce hafızaya yaz
                            sinyali_kaydet(secilen_ham_mesaj, gecerli_sinyal)
                            
                            # Emri başlat
                            sonuc = emri_baslat(
                                coin_pair=coin_pair,
                                yon=gecerli_sinyal['bizim_yonumuz'],
                                bizim_tp=gecerli_sinyal.get('bizim_tp'),
                                bizim_sl=gecerli_sinyal.get('bizim_sl'),
                                usdt_miktari=usdt_tutari,
                                leverage=kaldirac_secimi,
                                margin_mode=marjin_secimi
                            )
                            
                            if sonuc.get("success"):
                                status.update(label="✅ Ana Pozisyon, TP ve SL Başarıyla Açıldı!", state="complete", expanded=False)
                                st.balloons()
                                st.rerun()
                            else:
                                status.update(label=f"❌ Hata: {sonuc.get('error')}", state="error", expanded=True)
                        except Exception as e:
                            st.error(f"Borsa Hatası: {e}")
            else:
                if atlanan_mesajlar > 0:
                    st.info(f"Son mesajlar daha önce zaten işlenmişti ({atlanan_mesajlar} adet mükerrer sinyal atlandı).")
                else:
                    st.warning("Bugünkü mesajlar arasında geçerli bir işlem sinyali bulunamadı.")
else:
    st.info("Sol menüdeki **'Sinyal Tara & İşlemi Başlat'** butonuna basarak sistemi canlı olarak tetikleyebilirsiniz.")