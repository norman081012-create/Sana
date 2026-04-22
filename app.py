import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 系統初始化與配置
# ==========================================
st.set_page_config(page_title="Project Sana VFO v8.0 核心控制台", layout="wide")

st.markdown("""
<style>
    .node-box { background-color: #262730; border: 1px solid #464b5d; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
    .inner-os { color: #ff4b4b; font-style: italic; border-left: 3px solid #ff4b4b; padding-left: 10px; margin-bottom: 10px; }
    .mask-os { color: #00ffcc; border-left: 3px solid #00ffcc; padding-left: 10px; margin-bottom: 10px; }
    .stMetric { background-color: #1e1e1e; padding: 15px; border-radius: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

# 【API KEY】
API_KEY = "AIzaSyCuGgEHKMohZyrt365D9kZScDpU4iEryKE"
genai.configure(api_key=API_KEY)

# ==========================================
# 2. 狀態機 (Session State) 防呆初始化
# ==========================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.messages = []
    st.session_state.scores = {"L": 0, "T": 0, "SAI": 50, "BD": 100, "MF": 20}
    st.session_state.prev_module_a = "保持中立，觀察玩家語感，維持基礎社交距離。"
    st.session_state.current_goal = "撐完這場相親並保持基本禮貌"
    st.session_state.goal_library = ["維持專業形象", "避免被識破是AI", "引導至課程推銷"]
    st.session_state.user_labels = "初次見面的陌生人"
    st.session_state.last_sana_output = "（尚未開始對話）"
    st.session_state.core_modules = "" # ⭐ 新增：存放生成的 L1-L6 靈魂陣列

if "nodes_output" not in st.session_state:
    st.session_state.nodes_output = {}

# ==========================================
# 3. LLM 工具與【第 0 步：靈魂孵化器】
# ==========================================
def call_vfo_node(prompt, model_name, json_mode=True):
    model = genai.GenerativeModel(model_name)
    config = {"response_mime_type": "application/json"} if json_mode else None
    try:
        response = model.generate_content(prompt, generation_config=config)
        if json_mode:
            return json.loads(response.text.replace('```json', '').replace('```', '').strip())
        return response.text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

def generate_core_modules(seeds, model_name):
    """依照玩家輸入的種子，動態生成 L1-L6 模塊陣列"""
    prompt = f"""
    【系統指令：多核靈魂關鍵字矩陣生成器】
    請針對以下使用者輸入的「每一個」[種子關鍵字]，獨立生成以下陣列。
    絕對禁止輸出完整句子或詳細描述，所有欄位【僅限填入 1~3 個核心關鍵詞或簡短標籤】。

    [種子關鍵字清單]：{seeds}

    --- 陣列循環開始 ---
    【核心模塊 N：[替換為種子關鍵字]】
    [L1 底層矛盾]
    ├ 追求極致_標籤：{{關鍵詞}}
    └ 現實代價_標籤：{{關鍵詞}}
    [L2 情緒錨點]
    ├ 最深渴望_場景：{{名詞/短語}}
    └ 最深恐懼_下場：{{名詞/短語}}
    [L3 觀念防禦]
    ├ 敵意偏見_標籤：{{名詞/短語}}
    ├ 疲勞地雷_MF+：{{觸發動作_關鍵詞}}
    └ 安全回血_MF-：{{降壓情境_關鍵詞}}
    [L4 實戰內存]
    ├ 武器/話術_屬性：{{攻擊/防禦_關鍵詞}}
    ├ 生理壓力_反射：{{身體部位/痛覺_關鍵詞}}
    └ 逃避念頭_白日夢：{{跳躍思維_關鍵詞}}
    [L5 軌跡表象]
    ├ 日常休閒_嗜好：{{行為_名詞}}
    ├ 社會規劃_行程：{{待辦_關鍵詞}}
    ├ 印證偏見_記憶：{{歷史事件_標籤}}
    └ 掩飾發洩_口頭禪：{{慣用語_短句}}
    [L6 感官品味]
    ├ 外顯人設_氣場：{{形容詞_標籤}}
    ├ 慰藉依賴_飲食：{{具體食物/飲料_名詞}}
    ├ 私密精神_歌單：{{音樂/影視風格_標籤}}
    └ 焦慮微表情_動作：{{無意識動詞_短語}}
    --- 陣列循環結束 ---
    
    【VFO 跨模塊調和指令】
    在對話生成時，VFO 需自動檢索上述 N 個模塊的標籤陣列。允許跨種子調用。
    請直接輸出生成的結果，不要包含任何開場白。
    """
    return call_vfo_node(prompt, model_name, json_mode=False)

# ==========================================
# 4. 多節點 Pipeline (對接靈魂庫)
# ==========================================
def run_vfo_pipeline(user_speech, user_action, model_name):
    nodes = {}
    
    with st.status("🧠 VFO 認知神經元運算中...", expanded=True) as status:
        # Step 1: 從動態生成的核心模塊中提取內存
        st.write("Node 1: 內存庫存呼叫 (檢索靈魂矩陣)...")
        p1 = f"""
        【Sana 的核心模塊庫】：
        {st.session_state.core_modules}
        
        基於上輪策略：{st.session_state.prev_module_a} 與玩家輸入：{user_speech}。
        請從上方的【Sana 的核心模塊庫】中，精準提取 3 個最相關的內存設定 (如 L3疲勞地雷、L4生理壓力等)。
        """
        nodes['memories'] = call_vfo_node(p1, model_name, False)
        
        st.write("Node 2: 標籤判定與當前總結...")
        p2 = f"內存：{nodes['memories']}，玩家輸入：{user_speech}。更新玩家標籤並總結互動關鍵。"
        nodes['user_context'] = call_vfo_node(p2, model_name)
        
        st.write("Node 3: 儀表板數值結算...")
        p3 = f"當前分數：{st.session_state.scores}。參考上輪策略：{st.session_state.prev_module_a}。對新分數(L, T, SAI, BD, MF)進行合理增減並說明理由。"
        nodes['scores_new'] = call_vfo_node(p3, model_name)
        
        st.write("Node 4: 模組 C 內心反射生成...")
        p4 = f"基於新分數：{nodes['scores_new']} 與上下文。寫出 Sana 此刻最真實、未經過濾的內心 OS。"
        nodes['module_c'] = call_vfo_node(p4, model_name, False)
        
        st.write("Node 5: 鑄造模組 D 面具 (物理隔離)...")
        p5 = f"你是社交高手。基於新分數：{nodes['scores_new']} 與標籤：{nodes['user_context']}。忽略內心真實想法，設計一套完美的外在反應與肢體語言。"
        nodes['module_d'] = call_vfo_node(p5, model_name, False)
        
        st.write("Node 6-7: VFO 決策與語感轉化...")
        p6 = f"結合模組 C：{nodes['module_c']} 與模組 D：{nodes['module_d']}。生成包含 'sana_action' 與 'sana_speech' 的 JSON。確保對話簡短、帶口語碎屑、符合說人話原則。"
        nodes['final_output'] = call_vfo_node(p6, model_name)
        
        st.write("Node 8-9: 目標結算與次輪預載...")
        p8 = f"判斷目標 '{st.session_state.current_goal}' 是否更換，目標庫：{st.session_state.goal_library}。請回傳 'goal_decision' (JSON)。"
        nodes['goal_update'] = call_vfo_node(p8, model_name)
        
        p9 = f"基於最新目標：{nodes['goal_update']} 與分數：{nodes['scores_new']}，制定下一輪的模組 A 戰略。"
        nodes['next_a'] = call_vfo_node(p9, model_name, False)
        
        status.update(label="✅ VFO 運算完畢", state="complete", expanded=False)
    
    return nodes

# ==========================================
# 5. UI 介面實作
# ==========================================
with st.sidebar:
    st.title("⚙️ 核心後台")
    # 加上 -latest 避免 v1beta 404 錯誤
    models = ["gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]
    selected_model = st.selectbox("驅動大腦", models, index=0)
    
    st.divider()
    
    # ⭐ 新增：第 0 步 - 靈魂孵化器
    st.subheader("🧬 步驟 0: 靈魂種子孵化器")
    seed_input = st.text_input("輸入種子 (逗號分隔)", "健身, 去歐洲玩, 蛋包飯")
    if st.button("🌟 孵化 / 覆寫 靈魂矩陣"):
        with st.spinner("LLM 正在建構多核靈魂矩陣..."):
            st.session_state.core_modules = generate_core_modules(seed_input, selected_model)
        st.success("✅ 靈魂建構完成！(請見下方)")
    
    if st.session_state.core_modules:
        with st.expander("👁️ 檢視當前靈魂矩陣 (L1-L6)"):
            st.text(st.session_state.core_modules)
            
    st.divider()
    st.subheader("🛠️ 狀態覆寫 (Cheat)")
    st.session_state.user_labels = st.text_input("玩家標籤", st.session_state.user_labels)
    st.session_state.current_goal = st.text_input("當前目標", st.session_state.current_goal)
    
    if st.button("🔴 重置狀態機"):
        st.session_state.clear()
        st.rerun()

col_chat, col_monitor = st.columns([6, 4])

with col_chat:
    st.subheader("🏋️‍♀️ Sana 互動視窗")
    if not st.session_state.core_modules:
        st.warning("⚠️ 請先在左側欄執行「步驟 0: 靈魂種子孵化器」，賦予 Sana 記憶與人格矩陣！")
        
    chat_box = st.container(height=550)
    for m in st.session_state.messages:
        with chat_box.chat_message(m["role"]):
            st.write(f"*{m['action']}* {m['speech']}")
    
    with st.form("chat_input", clear_on_submit=True):
        u_act = st.text_input("動作 (姿態)", placeholder="(拿著手搖飲走過來)")
        u_speech = st.text_input("對話內容", placeholder="說點什麼...")
        
        if st.form_submit_button("送出至 VFO") and u_speech:
            if not st.session_state.core_modules:
                st.error("請先孵化靈魂矩陣！")
            else:
                results = run_vfo_pipeline(u_speech, u_act, selected_model)
                st.session_state.nodes_output = results
                
                if isinstance(results.get('scores_new'), dict):
                    st.session_state.scores = results['scores_new'].get('scores', st.session_state.scores)
                
                st.session_state.prev_module_a = results.get('next_a', '無最新策略')
                
                final_res = results.get('final_output', {})
                if isinstance(final_res, dict):
                    sana_act = final_res.get('sana_action', '(思考中)')
                    sana_say = final_res.get('sana_speech', '...')
                else:
                    sana_act = "(動作解析失敗)"
                    sana_say = str(final_res)
                    
                st.session_state.last_sana_output = sana_say
                
                st.session_state.messages.append({"role": "user", "action": u_act, "speech": u_speech})
                st.session_state.messages.append({"role": "assistant", "action": sana_act, "speech": sana_say})
                st.rerun()

with col_monitor:
    st.subheader("📊 VFO 儀表板")
    s = st.session_state.scores
    mc = st.columns(3)
    mc[0].metric("L (友善)", s.get("L", 0))
    mc[1].metric("T (信任)", s.get("T", 0))
    mc[2].metric("MF (疲憊)", s.get("MF", 20), delta_color="inverse")
    
    st.divider()
    st.write(f"**當前標籤：** `{st.session_state.user_labels}`")
    st.write(f"**當前目標：** `{st.session_state.current_goal}`")
    
    if st.session_state.get("nodes_output"):
        st.subheader("👁️ 黑盒子 (分步運算結果)")
        nb = st.session_state.nodes_output
        
        with st.expander("Node 1-3: 內存與分數決策"):
            st.write("**精準提取內存：**", nb.get('memories'))
            st.write("**標籤總結：**", nb.get('user_context'))
            st.write("**調分邏輯：**", nb.get('scores_new'))
            
        with st.expander("🎭 Node 4-5: 內外分離測試", expanded=True):
            st.markdown(f"<div class='inner-os'><b>模組 C (內心):</b><br>{nb.get('module_c')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='mask-os'><b>模組 D (面具):</b><br>{nb.get('module_d')}</div>", unsafe_allow_html=True)
            
        with st.expander("📅 Node 8-9: 次輪預載 (Module A)"):
            st.write("**目標異動：**", nb.get('goal_update'))
            st.info(nb.get('next_a'))
