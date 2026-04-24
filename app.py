# app.py
import streamlit as st
import sana_config as cfg
import sana_engine as engine

# ==========================================
# 1. 頁面與狀態初始化
# ==========================================
st.set_page_config(page_title="Sana VFO Terminal (Eng Prompt)", layout="wide", initial_sidebar_state="expanded")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "available_models" not in st.session_state:
    st.session_state.available_models = []

# ==========================================
# 2. 側邊欄：API 與模型鎖定
# ==========================================
with st.sidebar:
    st.title("⚙️ Sana VFO 系統控制")
    api_key = st.text_input("🔑 API 金鑰", value=cfg.DEFAULT_API_KEY, type="password")
    
    if api_key:
        if st.button("🔄 重新整理可用模型清單") or not st.session_state.available_models:
            with st.spinner("正在向 Google 請求可用模型..."):
                try:
                    st.session_state.available_models = engine.fetch_available_models(api_key)
                except Exception as e:
                    st.error(f"無法獲取清單: {e}")

        if st.session_state.available_models:
            default_idx = 0
            for i, m in enumerate(st.session_state.available_models):
                if "pro-preview" in m or "3.1-pro" in m:
                    default_idx = i
                    break
                elif "1.5-pro" in m:
                    default_idx = i
            
            selected_model = st.selectbox("🤖 選擇運算核心 (Model)", st.session_state.available_models, index=default_idx)
            st.info(f"當前模型：{selected_model}")
        else:
            st.error("未發現可用模型，請檢查金鑰。")
            
    st.markdown("---")
    st.markdown("### 📦 模組說明速查")
    category = st.selectbox("選擇模組分類", list(cfg.MODULES_FOR_UI.keys()))
    for mod_name, mod_desc in cfg.MODULES_FOR_UI[category].items():
        with st.expander(f"🔹 {mod_name}"):
            st.caption(mod_desc)

# ==========================================
# 3. 雙欄式主畫面：左側對話區 / 右側即時分析板
# ==========================================
col_chat, col_dash = st.columns([7, 3], gap="large")

with col_chat:
    st.title("Sana 核心認知終端")
    
    # 渲染歷史對話 (100% 乾淨)
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_input := st.chat_input("輸入對話，先生..."):
        if not api_key:
            st.error("先生，請先配置 API Key。")
            st.stop()
        
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner(f'Sana ({selected_model}) VFO v7.3 運算中...'):
                try:
                    # 修復記憶斷層：強迫 AI 看見自己上一輪完整的 VFO 英文推演
                    history_for_api = []
                    for m in st.session_state.messages[:-1]:
                        if m["role"] == "user":
                            history_for_api.append({"role": "user", "parts": [m["content"]]})
                        else:
                            full_memory = m.get("raw_text", m["content"])
                            history_for_api.append({"role": "model", "parts": [full_memory]})
                            
                    forced_input = cfg.get_forced_template(user_input)
                    
                    result = engine.process_sana_turn(
                        api_key=api_key,
                        selected_model=selected_model,
                        system_prompt=cfg.SYSTEM_PROMPT,
                        history_for_api=history_for_api,
                        forced_template_text=forced_input
                    )
                    
                    st.markdown(result["output"])
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "raw_text": result["raw_full_text"],     
                        "content": result["output"],
                        "parsed_dash": result["parsed_dash"]
                    })
                    st.rerun() 

                except Exception as e:
                    st.error(f"運算中斷：{str(e)}")

# ==========================================
# 4. 右側欄：Sana 實時狀態監測板
# ==========================================
with col_dash:
    st.subheader("📊 Sana VFO 監測板")
    st.markdown("*(擷取自最新一輪神經運算)*")
    st.divider()
    
    latest_msg = None
    for msg in reversed(st.session_state.messages):
        if msg["role"] == "assistant":
            latest_msg = msg
            break
            
    if latest_msg and latest_msg.get("parsed_dash"):
        d = latest_msg["parsed_dash"]
        
        # 面具疲勞度警告條
        mf_val = d.get('mf', '20').split('(')[0].strip()
        st.markdown(f"**🎭 Mask Fatigue (MF): {mf_val} / 100**")
        try:
            # 防呆：確保 mf_val 裡面沒有夾雜其他文字
            clean_mf = int(float(re.search(r'\d+', mf_val).group()))
            st.progress(min(clean_mf, 100))
        except:
            pass
        
        st.markdown("**🛡️ Module 9: Turing Test Detection**")
        if d.get("ai_scan", "0") != "0" and d.get("ai_scan") != "No Data":
            st.error(f"⚠️ 偵測到 AI 塑膠味！Intrusion Value: {d.get('ai_scan')}")
        else:
            st.success("Safe (未觸發覆寫)")
            
        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("L (Friendliness)", d.get("l_val", "0").split('(')[0].strip())
            st.metric("SAI (Dominance)", d.get("sai", "50").split('(')[0].strip())
        with col2:
            st.metric("T (Trust)", d.get("t_val", "0").split('(')[0].strip())
            st.metric("B-D (Boundary)", d.get("bd", "100").split('(')[0].strip())
            
        st.markdown("**🧠 Module B: Strategic Judgment**")
        st.info(d.get("mod_b", "No Data"))
        
        st.markdown("**🌋 Module C: True Inner Reflex**")
        st.warning(d.get("mod_c", "No Data"))
        
        st.markdown("**🎭 Module D: Professional Mask**")
        st.success(d.get("mod_d", "No Data"))
        
        st.markdown("**🎯 Module A: Next Round Prep**")
        st.write(d.get("mod_a", "No Data"))
        
        # 🔥 將 Raw Log 流放到最角落
        st.divider()
        st.caption("⚙️ 開發者底層監控")
        with st.expander("🔍 展開 VFO 原始推演 Log (Raw Data)", expanded=False):
            st.code(latest_msg.get("raw_text", "No Data"), language="markdown")
        
    else:
        st.caption("等待首輪對話產生 VFO 數據...")
