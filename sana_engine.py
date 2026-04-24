# sana_engine.py
import re
import google.generativeai as genai

def fetch_available_models(api_key):
    genai.configure(api_key=api_key)
    models = []
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            clean_name = m.name.replace("models/", "")
            models.append(clean_name)
    return models

def extract_sana_dashboard(internal_text):
    if not internal_text:
        return {}
        
    plain_text = internal_text.replace('**', '').replace('* ', '')
    
    def extract(pattern):
        match = re.search(pattern, plain_text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "No Data"

    # 針對全英文的 VFO v7.3 進行萃取
    data = {
        # 核心數值 (從 [External Stimulus Value Settlement] 中抓取)
        "l_val": extract(r"L=(.*?)(?=\n|\s*/|\s*T=)"),
        "t_val": extract(r"T=(.*?)(?=\n|\s*/|\s*SAI=)"),
        "sai": extract(r"SAI=(.*?)(?=\n|\s*/|\s*B-D=)"),
        "bd": extract(r"B-D=(.*?)(?=\n|\s*/|\s*MF=)"),
        "mf": extract(r"MF=(.*?)(?=\n|\s*/|\s*ATM=)"),
        
        # 模組 9 入侵掃描
        "ai_scan": extract(r"Intrusion Value.*?(\d+)"),
        
        # 核心邏輯判斷
        "mod_b": extract(r"Module B[^\n:]*[:：]\s*(.*?)(?=\n.*\[Step Two\]|\n\n)"),
        "mod_c": extract(r"Module C[^\n:]*[:：]\s*(.*?)(?=\n.*Module D)"),
        "mod_d": extract(r"Module D[^\n:]*[:：]\s*(.*?)(?=\n.*\[VFO Harmonized)"),
        
        # 次輪準備
        "mod_a": extract(r"Module A[^\n:]*[:：]\s*(.*?)(?=\n|-|$)")
    }
    return data

def process_sana_turn(api_key, selected_model, system_prompt, history_for_api, forced_template_text):
    genai.configure(api_key=api_key)
    model_inst = genai.GenerativeModel(model_name=selected_model, system_instruction=system_prompt)
    
    chat = model_inst.start_chat(history=history_for_api)
    response = chat.send_message(forced_template_text)
    full_text = response.text
    
    # 清理 markdown 區塊符號
    clean_text = re.sub(r"^```[a-z]*\n", "", full_text)
    clean_text = re.sub(r"\n```$", "", clean_text)
    
    internal_text = ""
    output_text = ""
    
    # Sana 的格式是使用 ---------------------- 分隔內部推演與最終對話
    parts = clean_text.split("----------------------")
    if len(parts) >= 2:
        internal_text = parts[0].strip()
        
        # 確保不會印出多餘的 [Final Reply] 標題
        raw_out = parts[-1].strip()
        output_text = re.sub(r"\[Final Reply\]", "", raw_out, flags=re.IGNORECASE).strip()
    else:
        # 終極防呆
        internal_text = clean_text
        match = re.search(r'\[Final Reply\](.*?)(\[Stage 0|\Z)', clean_text, re.DOTALL | re.IGNORECASE)
        if match:
            output_text = match.group(1).strip()
        else:
            output_text = clean_text

    parsed_dash = extract_sana_dashboard(internal_text)

    return {
        "internal": internal_text,
        "output": output_text,
        "raw_full_text": full_text,
        "parsed_dash": parsed_dash
    }
