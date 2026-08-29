import requests
from bs4 import BeautifulSoup
from config import TELEGRAM_CHANNEL

def bugunun_mesajlarini_cek(kanal_adi: str = None) -> list:
    """
    Belirtilen Telegram kanalının web önizlemesinden en güncel mesajları çeker.
    """
    hedef_kanal = kanal_adi or TELEGRAM_CHANNEL
    # @ işaretini temizle
    hedef_kanal = hedef_kanal.lstrip("@").strip()
    
    url = f"https://t.me/s/{hedef_kanal}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[TELEGRAM_HATA] Sayfaya ulaşılamadı. HTTP Kod: {response.status_code}")
            return []
            
        soup = BeautifulSoup(response.text, 'html.parser')
        mesaj_kutulari = soup.find_all('div', class_='tgme_widget_message')
        
        tum_metinler = []
        for kutu in mesaj_kutulari:
            metin_divi = kutu.find('div', class_='tgme_widget_message_text')
            if metin_divi:
                temiz_metin = metin_divi.get_text(separator=" ", strip=True)
                if temiz_metin:
                    tum_metinler.append(temiz_metin)
                
        if not tum_metinler:
            print(f"[TELEGRAM_BILGI] @{hedef_kanal} kanalından metin mesajı çekilemedi.")
            return []
            
        en_taze_mesajlar = tum_metinler[-5:]
        print(f"[TELEGRAM] @{hedef_kanal} kanalından en güncel {len(en_taze_mesajlar)} mesaj başarıyla alındı.")
        return en_taze_mesajlar
        
    except Exception as e:
        print(f"[TELEGRAM_HATA] Scraper çalışırken hata oluştu: {e}")
        return []