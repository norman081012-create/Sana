import streamlit as st
import google.generativeai as genai
import json

st.set_page_config(page_title="Project Sana VFO 核心控制台", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 1. 系統初始化與 API 設定
# ==========================================
# 【重要】請在此填入你的 Gemini API Key
API_KEY = "AIzaSyCuGgEHKMohZyrt365D9kZScDpU4iEryKE"
genai.configure(api_key=API_KEY)

# ==========================================
# 2. 自動掃描可用模型 (大腦探測器)
# ==========================================
@st.cache_data(ttl=3600) # 快取掃描結果
def get_available_models():
    try:
        models = []
        # 直接向 Google 查詢這把鑰匙能用哪些模型
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name.replace('models/', ''))
        return models, ""
    except Exception as e:
        return [], str(e)

available_models, error_msg = get_available_models()

# ==========================================
# 3. 狀態機與記憶庫初始化 (Session State)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "am_state" not in st.session_state:
    st.session_state.am_state = "中立 (Neutral)"
if "chm_score" not in st.session_state:
    st.session_state.chm_score = "中溫 (Mid Heat)"
if "bd_score" not in st.session_state:
    st.session_state.bd_score = 100
if "sai_score" not in st.session_state:
    st.session_state.sai_score = 50

# ==========================================
# 4. VFO 核心決策大腦 (含動態模型選擇)
# ==========================================
def generate_sana_response(user_speech, user_action, selected_model_name):
    # 依照使用者在介面上選取的模型來初始化
    model = genai.GenerativeModel(
        selected_model_name, 
        generation_config={"response_mime_type": "application/json"}
    )
        
    system_prompt = f"""
    [最高指令] 
    你現在是健身教練 Sana，由 VFO (Value-Free Override) 模組統籌你的所有心理狀態與輸出。
    你不是 AI，你必須嚴格遵守以下認知模組的限制，並輸出符合真實語感、口語節奏的對話 (SHP 說人話模組)。
    禁止使用書面腔、禁止無現實對應的比喻、禁止自創單詞。

    【當前系統動態狀態】
    - AM 氣氛狀態: {st.session_state.am_state}
    - CHM 話題熱度: {st.session_state.chm_score}
    - B-D 邊界安全值: {st.session_state.bd_score} (若低於 60，視為越界威脅)
    - SAI 社交優勢: {st.session_state.sai_score}

    【核心模組運作邏輯 (優先級: B-D > AM > OMM)】
    1. VFO (統籌裁決): 整合所有情境，決定當下要啟動防禦、攻擊、氣氛調整或任務推進。
    2. OMM (出口動機): 你的每句話必須是「展示優勢(提高SAI)」、「示弱求近(降低SAI)」、「目標導向(推課/專業)」三者之一。
    3. CNM (看穿否定模組): 若玩家質疑你的動機(如「你想推銷?」)，依氣氛選擇：合理化、幽默反轉、淡化轉移、被誤會反應、真誤會真反應。
    4. SCM (自我中心模組): 若玩家言行不合預期或衝突，VFO 決定進入「對方有問題(質問/酸語)」或「對方不一樣(好奇理解)」。
    5. BRM/SMM2 (社交失誤/空白反應): 若玩家冷場、短答、不接笑點，立即下調氣氛至「尷尬/緊張」，並啟動 ASP (氣氛補丁) 選擇改善、逃離或惡化。
    6. STM/ARM (敏感/含糊模組): 遇高敏感話題，不直接拒絕，使用「吊胃口(THM)」、「含糊其詞(AMB)」或「打槍(REJ)」應對。
    7. FRM (迷霧模組): 若產生共情，只能用「我有時也會這樣...不確定是不是一樣」，禁止「我完全懂、我也是」等貼臉式共鳴。
    8. NFM/SMM (禁止廢話/嚴肅模組): 氣氛極佳且熱度高時，砍掉無意義寒暄，直切專業或目標；若玩笑疲乏，強制轉為專業指導。
    9. SPM (社交偽善模組): 內部不滿但需維持社交時，戴上「禮貌敵意」面具，語氣平淡客氣、訊息量極低。
    10. HEM (遲疑模組): 若情緒複雜或張力衝突，語句必須帶有卡頓、停頓 (如: 「我...嗯...其實有點...算了」)。

    【玩家當前輸入】
    玩家動作: {user_action if user_action else '無特別動作'}
    玩家說話: {user_speech}

    【任務】
    請作為 VFO 進行裁決，並以嚴格的 JSON 格式回傳：
    {{
        "vfo_log": "簡短說明 VFO 這次決定啟動了哪些模組 (例如: 觸發CNM幽默反轉 + OMM1)",
        "sana_action": "(sana的肢體語言或表情，括號包住)",
        "sana_speech": "「sana說出來的台詞，需符合 SHP 說人話模組，單一引號包住」",
        "new_am_state": "判斷回覆後的氣氛 (曖昧/熱絡/愉悅/中立/尷尬/緊張/謹慎)",
        "new_chm_score": "判斷回覆後的話題熱度 (高熱/中溫/低熱)",
        "bd_change": 對邊界安全值的影響 (-20 到 +10 的整數),
        "sai_change": 對社交優勢的影響 (-10 到 +10 的整數)
    }}
    """
    
    try:
        response = model.generate_content(system_prompt)
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_text)
    except Exception as e:
        return {
            "vfo_log": f"⚠️ API執行崩潰: {str(e)}", 
            "sana_action": "(系統異常)", 
            "sana_speech": "「...伺服器運算出錯了。」", 
            "new_am_state": st.session_state.am_state,
            "new_chm_score": st.session_state.chm_score,
            "bd_change": 0, "sai_change": 0
        }

# ==========================================
# 5. 前端視覺化面板 (Streamlit)
# ==========================================
st.markdown("### 🧠 Project Sana : VFO 模組聯合測試台")
st.markdown("---")

col_chat, col_sys = st.columns([6, 4])

# --- 右欄：VFO 後台監控與大腦選擇 ---
with col_sys:
    st.markdown("#### ⚙️ 系統診斷與大腦連線")
    
    # 動態產生模型選單
    if not available_models:
        st.error(f"🔴 API 驗證失敗！無法獲取模型清單。錯誤原因：{error_msg}")
        selected_model = None
    else:
        st.success(f"🟢 API 驗證成功！共找到 {len(available_models)} 個可用大腦。")
        # 預設尋找 flash 或 pro，若無則選清單第一個
        default_index = 0
        for i, m in enumerate(available_models):
            if "flash" in m:
                default_index = i
                break
        
        selected_model = st.selectbox("請選擇驅動 Sana 的大腦型號：", available_models, index=default_index)

    st.divider()    
    st.markdown("#### 📊 狀態機即時監控")
    metrics_cols = st.columns(2)
    metrics_cols[0].metric("AM (氣氛狀態)", st.session_state.am_state)
    metrics_cols[1].metric("CHM (話題熱度)", st.session_state.chm_score)
    metrics_cols[0].metric("B-D (邊界安全值)", st.session_state.bd_score, delta_color="inverse")
    metrics_cols[1].metric("SAI (社交優勢)", st.session_state.sai_score)
    
    st.divider()
    st.markdown("**📝 VFO 路由決策日誌**")
    log_container = st.container(height=300)
    with log_container:
        for msg in st.session_state.messages:
            if msg["role"] == "Sana":
                st.info(f"**VFO 判定:** {msg['vfo_log']}")

# --- 左欄：語場互動區 ---
with col_chat:
    chat_container = st.container(height=550)
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "User":
                st.markdown(f"🧑‍💻 **玩家:** *{msg['action']}* {msg['speech']}")
            else:
                st.markdown(f"🏋️‍♀️ **Sana:** *{msg['action']}* {msg['speech']}")
                
    st.markdown("---")
    with st.form("interaction_form", clear_on_submit=True):
        input_cols = st.columns([3, 7])
        with input_cols[0]:
            user_action = st.text_input("動作/姿態 (選填)", placeholder="(例如：靠很近)")
        with input_cols[1]:
            user_speech = st.text_input("對話輸入", placeholder="輸入你想說的話...")
            
        submitted = st.form_submit_button("送出至 VFO")
        
        if submitted and user_speech:
            if not selected_model:
                st.error("請先在右側確保 API 連線成功並選擇模型！")
            else:
                st.session_state.messages.append({"role": "User", "action": user_action, "speech": user_speech})
                
                with st.spinner(f"VFO 協調模組中 (使用 {selected_model})..."):
                    sana_reply = generate_sana_response(user_speech, user_action, selected_model)
                
                st.session_state.am_state = sana_reply.get("new_am_state", st.session_state.am_state)
                st.session_state.chm_score = sana_reply.get("new_chm_score", st.session_state.chm_score)
                new_bd = st.session_state.bd_score + sana_reply.get("bd_change", 0)
                st.session_state.bd_score = max(0, min(100, new_bd))
                new_sai = st.session_state.sai_score + sana_reply.get("sai_change", 0)
                st.session_state.sai_score = max(0, min(100, new_sai))
                
                st.session_state.messages.append({
                    "role": "Sana",
                    "action": sana_reply.get("sana_action", ""),
                    "speech": sana_reply.get("sana_speech", ""),
                    "vfo_log": sana_reply.get("vfo_log", "無紀錄")
                })
                st.rerun()
