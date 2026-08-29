import json
import re
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL

_model_instance = None

def get_ai_model():
    """Gemini AI model nesnesini gerektiğinde başlatır."""
    global _model_instance
    if _model_instance is None:
        if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key":
            raise ValueError("GEMINI_API_KEY tanımlanmamış. Lütfen .env dosyasını doldurun.")
        genai.configure(api_key=GEMINI_API_KEY)
        _model_instance = genai.GenerativeModel(
            GEMINI_MODEL,
            generation_config={"response_mime_type": "application/json"}
        )
    return _model_instance

def pariteyi_standartlastir(coin_pair: str) -> str:
    """Pariteyi standart CCXT formatına (örn: BTC/USDT) dönüştürür."""
    if not coin_pair:
        return "BTC/USDT"
    temiz = coin_pair.strip().upper()
    if "/" not in temiz:
        for quote in ["USDT", "BUSD", "USDC", "FDUSD"]:
            if temiz.endswith(quote):
                base = temiz[:-len(quote)]
                return f"{base}/{quote}"
    return temiz

def sinyali_cozumle(mesaj_metni: str, model_override=None) -> dict:
    """
    Telegram mesajını Gemini LLM ile analiz eder.
    Sinyali tersine çevirir (LONG -> SHORT, SL -> TP vb.).
    """
    prompt = f"""
    Aşağıdaki kripto para sinyal mesajını analiz et.
    Eğer mesaj bir işlem sinyali değilse veya anlamsızsa "is_signal": false döndür.
    Sinyal ise şu formatta saf JSON döndür:
    {{
        "is_signal": true,
        "coin_pair": "BNB/USDT",
        "fenomen_yonu": "LONG",
        "entry": 592.186,
        "sl": 572.249,
        "tp": 633.518
    }}
    
    Mesaj: "{mesaj_metni}"
    """
    
    try:
        model = model_override or get_ai_model()
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        
        # Olası markdown json bloklarını temizle
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?", "", raw_text)
            raw_text = re.sub(r"```$", "", raw_text).strip()
            
        veri = json.loads(raw_text)
        
        if veri.get("is_signal"):
            fenomen_yonu = str(veri.get("fenomen_yonu", "LONG")).strip().upper()
            veri["fenomen_yonu"] = "LONG" if "LONG" in fenomen_yonu or "BUY" in fenomen_yonu else "SHORT"
            veri["bizim_yonumuz"] = "SHORT" if veri["fenomen_yonu"] == "LONG" else "LONG"
            veri["coin_pair"] = pariteyi_standartlastir(veri.get("coin_pair", ""))
            
            eski_tp = float(veri.get("tp", 0) or 0)
            eski_sl = float(veri.get("sl", 0) or 0)
            entry = float(veri.get("entry", 0) or 0)
            
            # Tersine Strateji: Orijinal SL bizim TP'miz, orijinal TP bizim SL'imiz olur
            bizim_tp = eski_sl if eski_sl > 0 else None
            bizim_sl = eski_tp if eski_tp > 0 else None
            
            # Mantıksal yön tutarlılık kontrolü:
            if entry > 0 and bizim_tp and bizim_sl:
                if veri["bizim_yonumuz"] == "LONG" and (bizim_tp < entry and bizim_sl > entry):
                    bizim_tp, bizim_sl = bizim_sl, bizim_tp
                elif veri["bizim_yonumuz"] == "SHORT" and (bizim_tp > entry and bizim_sl < entry):
                    bizim_tp, bizim_sl = bizim_sl, bizim_tp
                    
            veri["bizim_tp"] = bizim_tp
            veri["bizim_sl"] = bizim_sl
            
        return veri
    except Exception as e:
        print(f"[AI_HATA] {e}")
        return {"is_signal": False, "hata": str(e)}