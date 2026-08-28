import streamlit as st
import pandas as pd
import os
from telegram import bugunun_mesajlarini_cek
from gemini import sinyali_cozumle
from binance import emri_baslat, borsa
from excel_logger import excel_kar_zarar_guncelle

# Sayfa Yapılandırması (Aydınlık & Minimal Konsept)
st.set_page_config(
    page_title="Tersine İşlem Botu | Kontrol Paneli",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Özel CSS ile Aydınlık ve Minimal Tasarım Dokunuşları
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ccccc; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- PROGRAM INIT (Açılışta Otomatik Çalışan Kısım) ---
# Program ilk ayağa kalktığında (cache veya session state kullanarak) Excel PnL güncellemesini bir kez tetikler
if "init_guncelleme" not in st.session_state:
    if os.path.exists("islem_gecmisi.xlsx"):
        try:
            excel_kar_zarar_guncelle(borsa)
        except Exception:
            pass
    st.session_state["init_guncelleme"] = True

# Başlık Bölümü
st.title("⚡ Tersine İşlem Botu (Honeypot & Inverse Engine)")
st.caption("Yapay Zeka Destekli Otonom Sinyal Tersleme ve Borsa Yürütücü Paneli")

# Sidebar (Kontrol Paneli)
st.sidebar.header("🎛️ Kontrol Merkezi")
kanal_secimi = st.sidebar.text_input("Hedef Telegram Kanalı", value="cryptosignals0rg")
islem_miktari = st.sidebar.slider("İşlem Miktarı (Birim)", 0.01, 0.10, 0.05)

calistir_butonu = st.sidebar.button("🚀 Botu Manuel Tetikle")

# Ana Ekran Metrikleri
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Sistem Durumu", value="Aktif / Hazır", delta="Stabil")
with col2:
    st.metric(label="Mod Stratejisi", value="Inverse (Tersine)", delta="LONG -> SHORT")
with col3:
    st.metric(label="Borsa Ağı", value="Binance Demo", delta="USD-M Futures")

st.divider()

# --- EXCEL RAPORU VE GÜNCELLEME BÖLÜMÜ ---
st.subheader("📁 Geçmiş İşlem Arşivi ve Canlı PnL Raporu")

col_tablo_baslik, col_buton = st.columns([4, 1])
with col_buton:
    # Kullanıcının manuel olarak PnL ve fiyatları güncelleyebileceği buton
    guncelle_tiklandi = st.button("🔄 PnL Güncelle", use_container_width=True)

if guncelle_tiklandi:
    with st.spinner("Binance verileri çekiliyor ve PnL hesaplanıyor..."):
        try:
            excel_kar_zarar_guncelle(borsa)
            st.success("Tablo başarıyla güncellendi!")
        except Exception as e:
            st.error(f"Güncelleme sırasında hata oluştu: {e}")

# Excel Tablosunu Ekrana Basma
if os.path.exists("islem_gecmisi.xlsx"):
    df_gecmis = pd.read_excel("islem_gecmisi.xlsx")
    st.dataframe(df_gecmis, use_container_width=True)
else:
    st.info("Henüz kaydedilmiş bir işlem bulunmuyor. Bot sinyal yakaladığında buraya eklenecektir.")

st.divider()

# İşlem Akış Ekranı
st.subheader("📊 Canlı İşlem ve Sinyal Akışı")

if calistir_butonu:
    with st.spinner(f"@{kanal_secimi} taranıyor ve yapay zeka analiz yapıyor..."):
        mesajlar = bugunun_mesajlarini_cek(kanal_secimi)
        
        if not mesajlar:
            st.error("Kanalda okunabilecek mesaj bulunamadı.")
        else:
            gecerli_sinyal = None
            secilen_ham_mesaj = ""
            
            for mesaj in reversed(mesajlar):
                analiz = sinyali_cozumle(mesaj)
                if analiz.get("is_signal"):
                    gecerli_sinyal = analiz
                    secilen_ham_mesaj = mesaj
                    break
            
            if gecerli_sinyal:
                st.success("🎯 Hedef Sinyal Başarıyla Yakalandı!")
                
                c_sol, c_sag = st.columns(2)
                with c_sol:
                    st.markdown("### 📥 Yakalanan Ham Mesaj")
                    st.info(secilen_ham_mesaj)
                    
                with c_sag:
                    st.markdown("### 🧠 AI & Strateji Çıktısı")
                    st.json(gecerli_sinyal)
                
                st.markdown("### ⚙️ Borsa Yürütme Logları")
                with st.status("Emir Binance Demo sunucusuna iletiliyor...", expanded=True) as status:
                    st.write("Zaman senkronizasyonu kontrol ediliyor...")
                    st.write(f"Parite: {gecerli_sinyal['coin_pair']} | Yön: {gecerli_sinyal['bizim_yonumuz']}")
                    
                    try:
                        emri_baslat(
                            gecerli_sinyal['coin_pair'], 
                            gecerli_sinyal['bizim_yonumuz'],
                            gecerli_sinyal.get('bizim_tp'),
                            gecerli_sinyal.get('bizim_sl')
                        )
                        status.update(label="✅ İşlem Başarıyla Tamamlandı ve Excel'e Kaydedildi!", state="complete", expanded=False)
                        st.balloons()
                        # Tablo güncel görnsün diye sayfayı yenilemek için küçük bir tetikleyici
                        st.rerun()
                    except Exception as e:
                        st.error(f"Borsa Hatası: {e}")
            else:
                st.warning("Bugünkü mesajlar arasında geçerli bir işlem sinyali bulunamadı.")
else:
    st.info("Sol taraftaki **'Botu Manuel Tetikle'** butonuna basarak sistemi canlı olarak çalıştırabilirsin.")