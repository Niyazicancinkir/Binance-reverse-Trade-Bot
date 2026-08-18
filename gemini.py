import google.generativeai as genai
import json
import os

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

ai_model = genai.GenerativeModel('gemini-3.1-flash-lite',
generation_config={"response_mime_type": "application/json"}
)

def sinyali_cozumle(mesaj_metni):
    prompt = f"""
    Aşağıdaki kripto para sinyal mesajını analiz et.
    Eğer mesaj bir işlem sinyali değilse "is_signal": false döndür.
    Sinyal ise şu formatta JSON döndür:
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
        response = ai_model.generate_content(prompt)
        veri = json.loads(response.text)
        
        if veri.get("is_signal"):
            fenomen_yonu = veri["fenomen_yonu"].upper()
            
            veri["bizim_yonumuz"] = "SHORT" if fenomen_yonu == "LONG" else "LONG"
            
            eski_tp = veri.get("tp", 0)
            eski_sl = veri.get("sl", 0)
            
            if eski_tp > 0:
                veri["bizim_tp"] = eski_sl if eski_sl > 0 else None
            else:
                veri["bizim_tp"] = None
                
            if eski_sl > 0:
                veri["bizim_sl"] = eski_tp
            else:
                veri["bizim_sl"] = None
                
        return veri
    except Exception as e:
        print(f"[AI_HATA] {e}")
        return {"is_signal": False}