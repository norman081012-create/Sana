import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 系統初始化與配置
# ==========================================
st.set_page_config(page_title="Project Sana VFO v7.3 核心控制台", layout="wide")

# CSS 樣式優化 (黑客/監控台風格)
st.markdown("""
<style>
    .node-box { background-color: #262730; border: 1px solid #464b5d; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    .inner-os { color: #ff4b4b; font-style: italic; border-left: 3px solid #ff4b4b; padding-left: 10px; margin-bottom: 10px; }
    .mask-os { color: #00ffcc; border-left: 3px solid #00ffcc; padding-left: 10px; margin-bottom: 10px; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# 【請確認這是你的 API KEY】
API_KEY = "AIzaSyCuGgEHKMohZyrt365D9kZScDpU4iEryKE"
genai.configure(api_key=API_KEY)

# ==========================================
# 2. 狀態機 (Session State) 防呆初始化
# ==========================================
# 核心設定初始化
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.messages = []
    st.session_state.scores = {"L": 0, "T": 0, "SAI": 50, "BD": 100, "MF": 20}
    st.session_state.prev_module_a = "保持中立，觀察玩家語感，維持基礎社交距離。"
    st.session_state.current_goal = "撐完這場相親並保持基本禮貌"
    st.session_state.goal_library = ["維持專業形象", "避免被識破是AI", "引導至課程推銷", "尋求靈魂共鳴"]
    st.session_state.user_labels = "初次見面的陌生人"
    st.session_state.last_sana_output = "（尚未開始對話）"

# ⭐ 關鍵修復：確保 nodes_output 絕對存在，避免 AttributeError
if "nodes_output" not in st.session_state:
    st.session_state.nodes_output = {}

# ==========================================
# 3. LLM 節點調用工具
# ==========================================
def call_vfo_node(prompt, model_name, json_mode=True):
    """獨立呼叫 LLM 節點的通用函式"""
    model = genai.GenerativeModel(model_name)
    config = {"response_mime_type": "application/json"} if json_mode else None
    try:
        response = model.generate_content(prompt, generation_config=config)
        if json_mode:
            return json.loads(response.text.replace('```json', '').replace('```', '').strip())
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

# ==========================================
# 4. 多節點 Pipeline 邏輯 (VFO 核心引擎)
# ==========================================
def run_vfo_pipeline(user_speech, user_action, model_name):
    nodes = {}
    
    with st.status("🧠 VFO 認知神經元運算中...", expanded=True) as status:
        # Step 1: 讀取策略與內存提取
        st.write("Node 1: 內存庫存呼叫...")
        p1 = f"基於上輪策略：{st.session_state.prev_module_a} 與輸入：{user_speech}，從 Sana 背景模組中提取 3 個最相關的內存設定(L1-L6)。"
        nodes['memories'] = call_vfo_node(p1, model_name, False)
        
        # Step 2: 使用者標籤與總結
        st.write("Node 2: 標籤判定與當前總結...")
        p2 = f"內存：{nodes['memories']}，玩家輸入：{user_speech}。更新玩家標籤並總結互動關鍵。"
        nodes['user_context'] = call_vfo_node(p2, model_name)
        
        # Step 3: 動態評分調整 (自由評分)
        st.write("Node 3: 儀表板數值結算...")
        p3 = f"當前分數：{st.session_state.scores}。參考上輪模組 A：{st.session_state.prev_module_a} 與上輪 Sana 表現：{st.session_state.last_sana_output}。對新分數進行調整並說明理由。"
        nodes['scores_new'] = call_vfo_node(p3, model_name)
        
        # Step 4: 模組 C (內心真實)
        st.write("Node 4: 模組 C 內心反射生成...")
        p4 = f"基於新分數：{nodes['scores_new']} 與上下文。寫出 Sana 此刻最真實、未經過濾的內心 OS。"
        nodes['module_c'] = call_vfo_node(p4, model_name, False)
        
        # Step 5: 模組 D (營業面具) - 物理隔離！
        st.write("Node 5: 物理隔離啟動，鑄造模組 D 面具...")
        # 嚴格禁止餵入 nodes['module_c']
        p5 = f"你是社交高手。基於新分數：{nodes['scores_new']} 與標籤：{nodes['user_context']}。忽略內心真實想法，設計一套完美的外在反應與肢體語言。"
        nodes['module_d'] = call_vfo_node(p5, model_name, False)
        
        # Step 6 & 7: 最終決策與回覆
        st.write("Node 6-7: VFO 決策與語感轉化...")
        p6 = f"結合模組 C：{nodes['module_c']} 與模組 D：{nodes['module_d']}，決定最終回覆策略。生成包含 'sana_action' 與 'sana_speech' 的 JSON。確保符合說人話原則。"
        nodes['final_output'] = call_vfo_node(p6, model_name)
        
        # Step 8: 目標判定與庫存管理
        st.write("Node 8: 核心目標結算...")
        p8 = f"總結：{nodes['user_context']}。判斷當前目標 '{st.session_state.current_goal}' 是否需更換。目標庫：{st.session_state.goal_library}。請以 JSON 格式回傳 'goal_decision'。"
        nodes['goal_update'] = call_vfo_node(p8, model_name)
        
        # Step 9: 次輪預載 (Module A)
        st.write("Node 9: 下一輪策略預分析...")
        p9 = f"基於最新目標：{nodes['goal_update']} 與分數：{nodes['scores_new']}，制定下一輪的模組 A 戰略大方向。"
        nodes['next_a'] = call_vfo_node(p9, model_name, False)
        
        status.update(label="✅ VFO 運算完畢", state="complete", expanded=False)
    
    return nodes

# ==========================================
# 5. UI 介面實作
# ==========================================

# 側邊欄：模型與作弊器
with st.sidebar:
    st.title("⚙️ 核心後台")
    # 簡化模型選擇，避免 API list 錯誤卡死
    models = ["gemini-1.5-pro", "gemini-1.5-flash"]
    selected_model = st.selectbox("驅動大腦", models, index=1) # 預設用 flash 跑得比較快
    
    st.divider()
    st.subheader("🛠️ 作弊模式 (Cheat)")
    st.session_state.user_labels = st.text_input("修改對象標籤", st.session_state.user_labels)
    st.session_state.current_goal = st.text_input("覆寫目前目標", st.session_state.current_goal)
    
    st.divider()
    if st.button("🔴 重置系統 (Reset All)"):
        st.session_state.clear()
        st.rerun()

# 主介面
col_chat, col_monitor = st.columns([6, 4])

with col_chat:
    st.subheader("🏋️‍♀️ Sana 互動視窗")
    
    # 聊天紀錄區
    chat_box = st.container(height=550)
    for m in st.session_state.messages:
        with chat_box.chat_message(m["role"]):
            st.write(f"*{m['action']}* {m['speech']}")
    
    # 輸入窗
    with st.form("chat_input", clear_on_submit=True):
        u_act = st.text_input("動作 (姿態)", placeholder="(例如：拿著手搖飲走過來)")
        u_speech = st.text_input("對話內容", placeholder="說點什麼...")
        
        if st.form_submit_button("送出至 VFO") and u_speech:
            # 1. 執行 Pipeline
            results = run_vfo_pipeline(u_speech, u_act, selected_model)
            
            # 2. 更新 Session State 狀態
            st.session_state.nodes_output = results
            
            # 安全讀取分數與最終輸出
            if isinstance(results.get('scores_new'), dict):
                st.session_state.scores = results['scores_new'].get('scores', st.session_state.scores)
            
            st.session_state.prev_module_a = results.get('next_a', '無最新策略')
            
            final_res = results.get('final_output', {})
            if isinstance(final_res, dict):
                sana_act = final_res.get('sana_action', '(思考中)')
                sana_say = final_res.get('sana_speech', '...')
            else:
                sana_act = "(系統異常)"
                sana_say = str(final_res)
                
            st.session_state.last_sana_output = sana_say
            
            # 3. 紀錄對話歷史
            st.session_state.messages.append({"role": "user", "action": u_act, "speech": u_speech})
            st.session_state.messages.append({"role": "assistant", "action": sana_act, "speech": sana_say})
            
            st.rerun()

with col_monitor:
    st.subheader("📊 VFO 儀表板")
    
    # 數值顯示
    s = st.session_state.scores
    mc = st.columns(3)
    mc[0].metric("L (友善)", s.get("L", 0))
    mc[1].metric("T (信任)", s.get("T", 0))
    mc[2].metric("MF (疲憊)", s.get("MF", 20), delta_color="inverse")
    
    st.divider()
    st.write(f"**當前標籤：** `{st.session_state.user_labels}`")
    st.write(f"**當前目標：** `{st.session_state.current_goal}`")
    
    # ⭐ 關鍵修復：安全讀取節點歷史 (使用 .get)
    if st.session_state.get("nodes_output"):
        st.subheader("👁️ 黑盒子 (分步運算結果)")
        nb = st.session_state.nodes_output
        
        with st.expander("Node 1-3: 內存與分數決策"):
            st.write("**選定內存：**", nb.get('memories'))
            st.write("**標籤總結：**", nb.get('user_context'))
            st.write("**調分邏輯：**", nb.get('scores_new'))
            
        with st.expander("🎭 Node 4-5: 內外分離測試", expanded=True):
            st.markdown(f"<div class='inner-os'><b>模組 C (內心真實):</b><br>{nb.get('module_c')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='mask-os'><b>模組 D (營業面具):</b><br>{nb.get('module_d')}</div>", unsafe_allow_html=True)
            st.caption("🔒 隔離確認：Node 5 (面具) 生成時，未存取 Node 4 (內心) 的資料。")
            
        with st.expander("📅 Node 8-9: 次輪預載 (Module A)"):
            st.write("**目標異動：**", nb.get('goal_update'))
            st.info(nb.get('next_a'))
    else:
        st.info("系統待機中... 請在左側輸入對話以啟動 VFO 引擎。")
