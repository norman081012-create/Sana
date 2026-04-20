import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 系統初始化與 API 設定
# ==========================================
st.set_page_config(page_title="Project Sana VFO 核心控制台", layout="wide", initial_sidebar_state="expanded")

# 【重要】請在此填入你剛剛申請到的 Gemini API Key (保留雙引號)
API_KEY = "AIzaSyCuGgEHKMohZyrt365D9kZScDpU4iEryKE"
genai.configure(api_key=API_KEY)

# 【修正1】降階為 flash 模型，解決 404 NotFound 權限問題
model = genai.GenerativeModel(
    'gemini-1.5-flash', 
    generation_config={"response_mime_type": "application/json"}
)

# ==========================================
# 2. 狀態機與記憶庫初始化 (Session State)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "am_state" not in st.session_state:
    st.session_state.am_state = "中立 (Neutral)" # 氣氛模組
if "chm_score" not in st.session_state:
    st.session_state.chm_score = "中溫 (Mid Heat)" # 場子熱度
if "bd_score" not in st.session_state:
    st.session_state.bd_score = 100 # 邊界安全值 (越低越危險)
if "sai_score" not in st.session_state:
    st.session_state.sai_score = 50 # 社交優勢 (Social Advantage)

# ==========================================
# 3. VFO 核心決策大腦 (巨型 Prompt 封裝)
# ==========================================
def generate_sana_response(user_speech, user_action):
    """
    Sana 的靈魂。將你設計的數十個模組邏輯，壓縮成系統指令，
    讓 LLM 扮演 VFO 進行統籌裁決。
    """
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
        "bd_change": 對邊界安全值的影響數值 (-20 到 +10),
        "sai_change": 對社交優勢的影響數值 (-10 到 +10)
    }}
    """
    
    # 【修正2】防死當裝甲：將容易出錯的 API 呼叫包起來
    try:
        response = model.generate_content(system_prompt)
        # 清理可能夾帶的 Markdown 標記
        raw_text = response.text.replace('```json', '').replace('```', '').strip()
        return json.loads(raw_text)
    except Exception as e:
        # 如果 API 崩潰，會把錯誤原因印在畫面上，而不是直接讓網頁卡死
        return {
            "vfo_log": f"⚠️ 系統連線錯誤: {str(e)}", 
            "sana_action": "(系統異常，原地當機)", 
            "sana_speech": "「...我的大腦伺服器好像連線失敗了。」", 
            "new_am_state": st.session_state.am_state,
            "new_chm_score": st.session_state.chm_score,
            "bd_change": 0, "sai_change": 0
        }

# ==========================================
# 4. 前端視覺化面板 (Streamlit)
# ==========================================
# 頂部標題
st.markdown("### 🧠 Project Sana : VFO 模組聯合測試台")
st.caption("核心架構：Value-Free Override (VFO) | 搭載模組：OMM, CNM, SCM, AM, CHM, STM, BRM, SPM... 等40項協議")
st.markdown("---")

col_chat, col_sys = st.columns([6, 4])

# --- 右欄：VFO 後台監控儀表板 ---
with col_sys:
    st.markdown("#### ⚙️ 模組狀態機即時監控")
    
    # 核心數值區
    metrics_cols = st.columns(2)
    metrics_cols[0].metric("AM (氣氛狀態)", st.session_state.am_state)
    metrics_cols[1].metric("CHM (話題熱度)", st.session_state.chm_score)
    metrics_cols[0].metric("B-D (邊界安全值)", st.session_state.bd_score, delta_color="inverse")
    metrics_cols[1].metric("SAI (社交優勢)", st.session_state.sai_score)
    
    st.divider()
    
    # VFO 決策日誌
    st.markdown("**📊 VFO 路由決策日誌 (JSM 隱身模組破除)**")
    log_container = st.container(height=350)
    with log_container:
        for msg in st.session_state.messages:
            if msg["role"] == "Sana":
                st.info(f"**VFO 判定:** {msg['vfo_log']}")

# --- 左欄：語場互動區 ---
with col_chat:
    # 對話歷史紀錄
    chat_container = st.container(height=500)
    with chat_container:
        for msg in st.session_state.messages:
            if msg["role"] == "User":
                st.markdown(f"🧑‍💻 **玩家:** *{msg['action']}* {msg['speech']}")
            else:
                st.markdown(f"🏋️‍♀️ **Sana:** *{msg['action']}* {msg['speech']}")
                
    st.markdown("---")
    
    # 雙軌輸入表單
    with st.form("interaction_form", clear_on_submit=True):
        input_cols = st.columns([3, 7])
        with input_cols[0]:
            user_action = st.text_input("動作/姿態 (選填)", placeholder="(例如：靠很近、面無表情)")
        with input_cols[1]:
            user_speech = st.text_input("對話輸入", placeholder="輸入你想說的話...")
            
        submitted = st.form_submit_button("送出至 VFO")
        
        if submitted and user_speech:
            # 1. 紀錄玩家輸入
            st.session_state.messages.append({
                "role": "User", "action": user_action, "speech": user_speech
            })
            
            # 2. 呼叫大腦運算
            with st.spinner("VFO 協調模組中... (OMM / AM / SCM)"):
                sana_reply = generate_sana_response(user_speech, user_action)
            
            # 3. 更新所有背景數值
            st.session_state.am_state = sana_reply.get("new_am_state", st.session_state.am_state)
            st.session_state.chm_score = sana_reply.get("new_chm_score", st.session_state.chm_score)
            
            new_bd = st.session_state.bd_score + sana_reply.get("bd_change", 0)
            st.session_state.bd_score = max(0, min(100, new_bd)) # 限制在 0-100
            
            new_sai = st.session_state.sai_score + sana_reply.get("sai_change", 0)
            st.session_state.sai_score = max(0, min(100, new_sai))
            
            # 4. 紀錄 Sana 輸出與決策日誌
            st.session_state.messages.append({
                "role": "Sana",
                "action": sana_reply.get("sana_action", ""),
                "speech": sana_reply.get("sana_speech", ""),
                "vfo_log": sana_reply.get("vfo_log", "無紀錄")
            })
            
            # 重新整理畫面
            st.rerun()
