import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 0. 頁面配置與 CSS
# ==========================================
st.set_page_config(page_title="Project Sana VFO 核心控制台", layout="wide")

st.markdown("""
<style>
    .reportview-container .main .block-container{ padding-top: 2rem; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .inner-os { background-color: #ffebee; padding: 15px; border-left: 5px solid #f44336; margin-bottom: 10px; }
    .mask-os { background-color: #e8f5e9; padding: 15px; border-left: 5px solid #4caf50; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 1. 系統初始化與 API 設定
# ==========================================
API_KEY = "AIzaSyCuGgEHKMohZyrt365D9kZScDpU4iEryKE" # 建議正式環境改為 st.secrets
genai.configure(api_key=API_KEY)

@st.cache_data(ttl=3600)
def get_available_models():
    try:
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name.replace('models/', ''))
        return models, ""
    except Exception as e:
        return [], str(e)

# ==========================================
# 2. 狀態機 (Session State) 初始化
# ==========================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.messages = []
    # 核心儀表板數值
    st.session_state.scores = {"L": 0, "T": 0, "SAI": 50, "BD": 100, "MF": 20}
    # 機制狀態庫
    st.session_state.user_labels = "初次見面的陌生人"
    st.session_state.current_goal = "撐完這場相親並保持基本禮貌"
    st.session_state.goal_library = ["維持專業形象", "避免被識破是AI", "引導至課程推銷"]
    st.session_state.prev_strategy = "保持中立，觀察玩家語感"
    st.session_state.prev_judgement = "標準社交邊界"
    st.session_state.black_box = {} # 存放當次運算的各模組中間產物

# ==========================================
# 3. VFO 核心運算引擎 (11 步迴圈)
# ==========================================
def run_vfo_engine(user_speech, user_action, selected_model):
    model = genai.GenerativeModel(selected_model)
    
    # 建立強大的系統提示詞 (包含 11 步邏輯)
    prompt = f"""
    你是 VFO (Value-Free Override) 認知引擎，負責驅動角色 Sana。
    你必須嚴格執行以下 11 步邏輯並回傳 JSON 格式結果。

    【當前系統快照】
    - 上輪策略: {st.session_state.prev_strategy}
    - 上輪判定標準: {st.session_state.prev_judgement}
    - 當前儀表板: {st.session_state.scores}
    - 當前使用者標籤: {st.session_state.user_labels}
    - 當前核心目標: {st.session_state.current_goal}

    【玩家輸入】
    - 動作: {user_action}
    - 說話: {user_speech}

    【執行指令】
    1. 讀取上輪策略及儀表板判定標準。
    2. 依照輸入及策略，從 Sana 的背景設定(健身、業績、歐洲、蛋包飯等)選取適當內存。
    3. 紀錄使用者新標籤及當回合總結。
    4. 參考上輪模組 A 的目標與策略。
    5. 對分數(L, T, SAI, BD, MF)做調整，並記錄理由。禁止死板規則，請根據語感自由評分。
    6. 產生「模組 C (內心真實反射)」：這是 Sana 卸下偽裝後最真實、可能很刻薄或混亂的想法。
    7. 產生「模組 D (業務面具)」：此步驟禁止參考模組 C。假設你是社交高手(如林志玲)，你會展現什麼表情與姿態？
    8. 依照 MF 值(越高面具越碎)與 4 模組內容，決定 VFO 最終決策戰術。
    9. 依照戰術生成 Sana 的最終回覆 (SHP 說人話，禁止 AI 味)。
    10. 判定是否達成目標，決定是否更換核心目標並更新目標庫。
    11. 產生下一輪的模組 A (下輪策略及儀表板判定標準)。

    【輸出格式範例】
    {{
      "module_a_prev": "...",
      "selected_memories": "...",
      "user_summary": "...",
      "score_logic": "...",
      "new_scores": {{"L": 5, "T": 3, "SAI": 55, "BD": 90, "MF": 25}},
      "module_c": "...",
      "module_d": "...",
      "final_strategy": "...",
      "sana_action": "...",
      "sana_speech": "...",
      "goal_decision": "是否變換及新目標",
      "next_module_a": "..."
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        result = json.loads(response.text.replace('```json', '').replace('```', '').strip())
        return result
    except Exception as e:
        st.error(f"VFO 運算發生錯誤: {e}")
        return None

# ==========================================
# 4. 前端介面佈局
# ==========================================

# 側邊欄：控制中心
with st.sidebar:
    st.title("🧠 VFO 核心控制台")
    
    # 1. 模型選擇
    available_models, err = get_available_models()
    if available_models:
        selected_model = st.selectbox("選擇 LLM 模型", available_models, index=0)
    else:
        st.error(f"無法讀取模型: {err}")
        selected_model = None
        
    st.divider()
    
    # 2. 作弊模式
    st.subheader("🛠️ 作弊模式 (Cheat Mode)")
    st.session_state.user_labels = st.text_input("修改玩家標籤", value=st.session_state.user_labels)
    st.session_state.current_goal = st.text_input("修改 Sana 當前目標", value=st.session_state.current_goal)
    
    new_lib = st.text_area("目標庫 (逗號分隔)", value=", ".join(st.session_state.goal_library))
    st.session_state.goal_library = [x.strip() for x in new_lib.split(",")]
    
    if st.button("重置系統"):
        st.session_state.clear()
        st.rerun()

# 主介面
col_left, col_right = st.columns([6, 4])

with col_left:
    st.subheader("🏋️‍♀️ 語場互動區")
    
    # 顯示歷史訊息
    chat_container = st.container(height=500)
    for m in st.session_state.messages:
        with chat_container.chat_message(m["role"]):
            st.markdown(f"*{m['action']}* {m['speech']}")
    
    # 輸入區
    with st.form("input_form", clear_on_submit=True):
        act = st.text_input("動作姿態 (選填)", placeholder="(靠很近)")
        speech = st.text_input("對玩家說...", placeholder="嘿，今天要練哪？")
        submitted = st.form_submit_button("送出至 VFO")
        
        if submitted and speech:
            # 觸發 VFO 運算
            res = run_vfo_engine(speech, act, selected_model)
            if res:
                # 更新狀態機
                st.session_state.scores = res["new_scores"]
                st.session_state.prev_strategy = res["next_module_a"]
                st.session_state.black_box = res
                
                # 紀錄訊息
                st.session_state.messages.append({"role": "user", "action": act, "speech": speech})
                st.session_state.messages.append({"role": "assistant", "action": res["sana_action"], "speech": res["sana_speech"]})
                
                # 處理目標變換
                if "新目標" in res["goal_decision"]:
                    st.session_state.current_goal = res["goal_decision"]
                
                st.rerun()

with col_right:
    st.subheader("📊 儀表板與黑盒子")
    
    # 數值顯示
    m_cols = st.columns(3)
    s = st.session_state.scores
    m_cols[0].metric("L (友善)", s["L"])
    m_cols[1].metric("T (信任)", s["T"])
    m_cols[2].metric("MF (疲憊)", s["MF"], delta_color="inverse")
    m_cols[0].metric("SAI (優勢)", s["SAI"])
    m_cols[1].metric("B-D (防禦)", s["BD"])

    st.divider()
    
    # 黑盒子詳解
    if st.session_state.black_box:
        bb = st.session_state.black_box
        with st.expander("👁️ 模組 A & B (戰略讀取與他省)", expanded=True):
            st.write(f"**選取的內存:** {bb.get('selected_memories')}")
            st.write(f"**戰略判定:** {bb.get('final_strategy')}")
            
        with st.expander("🎭 內外分離 (模組 C & D)"):
            st.markdown(f"<div class='inner-os'><b>模組 C (內心真實):</b><br>{bb.get('module_c')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='mask-os'><b>模組 D (面具偽裝):</b><br>{bb.get('module_d')}</div>", unsafe_allow_html=True)
            
        with st.expander("📉 評分邏輯"):
            st.write(bb.get('score_logic'))
            
        with st.expander("📅 下輪預載 (下一輪模組 A)"):
            st.info(bb.get('next_module_a'))
    else:
        st.info("尚未有運算紀錄，請開始對話。")
