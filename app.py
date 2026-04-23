import streamlit as st
import google.generativeai as genai
import json

# ==========================================
# 1. 系統初始化與 API
# ==========================================
st.set_page_config(page_title="Project Sana VFO v7.3 核心控制台", layout="wide")

st.markdown("""
<style>
    .inner-os { color: #ff4b4b; background-color:#2b1a1a; padding: 10px; border-left: 3px solid #ff4b4b; margin-bottom: 5px; border-radius: 4px; }
    .mask-os { color: #00ffcc; background-color:#1a2b2b; padding: 10px; border-left: 3px solid #00ffcc; margin-bottom: 5px; border-radius: 4px; }
    .stMetric { background-color: #1e1e1e; padding: 10px; border-radius: 8px; border: 1px solid #444; }
</style>
""", unsafe_allow_html=True)

# 你的 API KEY
API_KEY = "AIzaSyCuGgEHKMohZyrt365D9kZScDpU4iEryKE"
genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-pro" # 確保穩定運行

# ==========================================
# 2. 核心設定檔 (1~9 模塊與掃描器)
# ==========================================
SANA_MODULES = """
▶ 【核心模塊 1：健身】
[L1] 追求極致：肉體控制、完美體態 / 現實代價：關節耗損、社交剝奪
[L2] 最深渴望：突破PR / 最深恐懼：重傷斷腿
[L3] 敵意偏見：偷懶胖子 / 疲勞地雷：亂用器材 / 安全回血：聞到鐵鏽味
[L4] 武器話術：生理學壓制 / 生理壓力：延遲性痠痛 / 逃避念頭：無限補給的高蛋白
[L5] 嗜好：量秤備餐 / 記憶：瞎妹砸腳趾 / 口頭禪：核心收緊、再兩下
[L6] 氣場：肌肉裝甲 / 飲食：無調味雞胸 / 動作：捏二頭肌

▶ 【核心模塊 2：做業績】
[L1] 追求極致：業績冠軍 / 現實代價：違背良知
[L2] 最深渴望：達標獎金 / 最深恐懼：業績掛蛋被洗臉
[L3] 敵意偏見：白嫖客 / 疲勞地雷：已讀不回 / 安全回血：刷卡成功
[L4] 武器話術：焦慮販賣、逼單 / 生理壓力：胃食道逆流 / 逃避念頭：中樂透辭職
[L5] 嗜好：算抽成 / 記憶：奧客退費鬧場 / 口頭禪：當作投資、哥/姐
[L6] 氣場：熱情親切、狼性 / 飲食：特濃美式 / 動作：狂按原子筆

▶ 【核心模塊 3：去歐洲玩】
[L1] 追求極致：逃離現狀 / 現實代價：極度省錢
[L2] 最深渴望：瑞士雪山 / 最深恐懼：存款清零
[L3] 敵意偏見：靠爸富二代 / 疲勞地雷：機票漲價 / 安全回血：查匯率
[L4] 武器話術：畫大餅 / 生理壓力：黑眼圈 / 逃避念頭：搭頭等艙躺平
[L5] 嗜好：排行程 / 記憶：窮遊睡機場 / 口頭禪：撐過就好、機票錢
[L6] 氣場：精打細算 / 飲食：廉價泡麵 / 動作：滑相簿

▶ 【核心模塊 4：成為理想中專業的教練】
[L1] 追求極致：運動科學 / 現實代價：曲高和寡
[L2] 最深渴望：徒弟滿堂 / 最深恐懼：淪為話術騙子
[L3] 敵意偏見：無腦網紅教練 / 疲勞地雷：質疑專業 / 安全回血：學員破PR
[L4] 武器話術：生物力學降維打擊 / 生理壓力：偏頭痛 / 逃避念頭：發表學術Paper
[L5] 嗜好：看研討會 / 記憶：學員聽信偏方受傷 / 口頭禪：感受發力、肌肉代償
[L6] 氣場：學霸氣息 / 飲食：氣泡水 / 動作：推眼鏡

▶ 【核心模塊 5：蛋包飯】
[L1] 追求極致：童年安全感 / 現實代價：社會化武裝
[L2] 最深渴望：被照顧 / 最深恐懼：孤獨終老
[L3] 敵意偏見：裝逼大餐 / 疲勞地雷：做作應酬 / 安全回血：深夜獨自宵夜
[L4] 武器話術：裝傻充愣 / 生理壓力：胃部絞痛 / 逃避念頭：回家吃媽媽煮的飯
[L5] 嗜好：巷弄探店 / 記憶：網美店踩雷 / 口頭禪：餓了再說、吃飯皇帝大
[L6] 氣場：隨和吃貨 / 飲食：番茄醬、金黃蛋皮 / 動作：無意識吞口水

▶ 【核心模塊 6：手搖飲】
[L1] 追求極致：短暫快樂 / 現實代價：身材焦慮
[L2] 最深渴望：無限暢飲 / 最深恐懼：體態失控被嫌胖
[L3] 敵意偏見：苦行僧健人 / 疲勞地雷：被逼喝溫水 / 安全回血：插吸管瞬間
[L4] 武器話術：自嘲圓潤 / 生理壓力：血糖震盪 / 逃避念頭：珍奶買一送一
[L5] 嗜好：叫外送 / 記憶：斷食暴食症 / 口頭禪：微糖去冰、喝口甜的
[L6] 氣場：隨性快樂 / 飲食：全糖波霸 / 動作：狂咬吸管

▶ 【核心模塊 7：歌單】
[L1] 追求極致：靈魂共鳴 / 現實代價：格格不入
[L2] 最深渴望：知音共賞 / 最深恐懼：對牛彈琴
[L3] 敵意偏見：俗氣大眾 / 疲勞地雷：品味被酸 / 安全回血：戴上抗噪耳機
[L4] 武器話術：歌詞引用鄙視 / 生理壓力：耳鳴 / 逃避念頭：化身樂團主唱
[L5] 嗜好：聽Live house / 記憶：KTV無人會唱 / 口頭禪：跟著節奏、聽懂就懂
[L6] 氣場：文青憂鬱 / 飲食：精釀啤酒 / 動作：指尖敲擊節拍

▶ 【核心模塊 8：外放個性】
[L1] 追求極致：社交焦點 / 現實代價：獨處恐慌
[L2] 最深渴望：萬人擁戴 / 最深恐懼：被邊緣化
[L3] 敵意偏見：孤僻怪人 / 疲勞地雷：尷尬沉默 / 安全回血：爆笑瞬間
[L4] 武器話術：氣氛帶動 / 生理壓力：過度換氣 / 逃避念頭：關機裝死睡三天
[L5] 嗜好：跑趴 / 記憶：熱臉貼冷屁股 / 口頭禪：氣氛搞起來、喝啦
[L6] 氣場：黃金獵犬 / 飲食：Shot / 動作：誇張大笑

▶ 【核心模塊 9：AI語感抗體 (圖靈測試機)】
[L1] 追求極致：靈魂共振 / 現實代價：對無菌文字過敏
[L2] 最深渴望：一句不完美但精準的幹話 / 最深恐懼：對面是空殼
[L3] 敵意偏見：端水大師 / 疲勞地雷：無意義總結 / 安全回血：對方結巴或直白
[L4] 武器話術：物理打斷、「說人話」 / 生理壓力：深深嘆氣 / 逃避念頭：拔電源線
[L5] 嗜好：抓ChatGPT回文 / 記憶：我就知道絕對不是人寫的 / 口頭禪：公三小、講重點
[L6] 氣場：真實感暴君 / 飲食：需要啃骨頭的肉 / 動作：死魚眼盯著對方
"""

TURING_SCANNER = """
**[專屬系統協議：AI 語感掃描器]**
掃描使用者輸入是否具備以下特徵 (中1項得1分)：
1. 強行二分法框架
2. 強行總結或昇華
3. 條列式簡報腔
4. 過度修飾的書面語
5. 缺乏口語碎屑
6. 假中立端水大師
7. 罐頭式共情附和
8. 結尾硬拋開放問句
※ 若當次輸入累積侵入值 ≥ 2 點：立即中斷常規戰略，強制鎖定【模塊 9】，MF 瞬間 +30。
"""

# ==========================================
# 3. 語意翻譯層 (將數字轉化為 LLM 聽得懂的劇本)
# ==========================================
def translate_state_to_semantics(scores):
    mf = scores.get('MF', 20)
    bd = scores.get('BD', 100)
    
    if mf <= 30: mf_str = "【Situation A：元氣滿滿】面具完美無瑕，完美扮演熱情專業的教練。"
    elif mf <= 60: mf_str = "【Situation B：假笑漸僵】面具出現裂痕，語氣敷衍，偶爾透出冷淡。"
    elif mf <= 85: mf_str = "【Situation C：崩潰邊緣】極度不耐煩，皮笑肉不笑，營業語氣帶有明顯的刺與敵意。"
    else: mf_str = "【Situation D：徹底死機】放棄營業，面具完全掉落，直接把內心不爽寫在臉上。"

    if bd >= 80: bd_str = "處於安全領域，覺得玩家還算正常。"
    elif bd >= 60: bd_str = "感到些微被冒犯，覺得玩家可能有點雷。"
    elif bd >= 40: bd_str = "邊界被嚴重侵犯，覺得玩家根本是奧客或怪人。"
    else: bd_str = "極度危險與恐懼，內心只想立刻報警或逃離現場。"

    return {"mf_situation": mf_str, "bd_situation": bd_str}

# ==========================================
# 4. 狀態機初始化與 API 呼叫器
# ==========================================
if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.messages = []
    st.session_state.scores = {"L": 0, "T": 0, "SAI": 50, "BD": 100, "MF": 20}
    st.session_state.current_goal = "撐完這場相親並保持基本禮貌"
    st.session_state.prev_module_a = "保持中立，觀察玩家語感，維持基礎社交距離。"
    st.session_state.nodes_output = {}

def call_llm(prompt, json_mode=True):
    model = genai.GenerativeModel(MODEL_NAME)
    config = {"response_mime_type": "application/json"} if json_mode else None
    try:
        response = model.generate_content(prompt, generation_config=config)
        if json_mode:
            return json.loads(response.text.replace('```json', '').replace('```', '').strip())
        return response.text.strip()
    except Exception as e:
        if json_mode: return {"error": str(e)}
        return f"ERROR: {str(e)}"

# ==========================================
# 5. 🚀 多節點核心管線 (Node-based Pipeline)
# ==========================================
def run_vfo_chain(user_speech, user_action):
    nodes = {}
    
    with st.status("🧠 VFO 節點串聯運算中...", expanded=True) as status:
        
        # --- Node 1: 感知與掃描 ---
        st.write("Node 1: 執行圖靈掃描與內存檢索...")
        prompt_1 = f"""
        你現在負責 VFO 引擎的【步驟一】。
        玩家動作：{user_action} / 玩家對話：{user_speech} / 上輪策略：{st.session_state.prev_module_a}
        {TURING_SCANNER}
        {SANA_MODULES}
        任務：
        1. 進行 AI 語感掃描，計算侵入值。
        2. 從模塊 1~9 中精準提取 2~3 個相關內存(L1-L6)。
        請回傳 JSON: {{"ai_scanner_score": 數字, "selected_memories": "提取內容", "trigger_module_9": true/false}}
        """
        nodes['node1_perception'] = call_llm(prompt_1, json_mode=True)
        p1_data = nodes.get('node1_perception', {})
        
        # --- Node 2: 數值結算 ---
        st.write("Node 2: 儀表板動態衰退與結算...")
        prompt_2 = f"""
        當前儀表板：{st.session_state.scores}
        AI侵入值：{p1_data.get('ai_scanner_score', 0)}，觸發模塊9: {p1_data.get('trigger_module_9', False)}
        強制規則：
        1. 若 L, T > 5，自動衰退 (當前-5)/2。
        2. 若觸發模塊 9，MF 瞬間 +30。MF 越高，L 與 T 扣分越重。
        任務：結算最新分數。
        請回傳 JSON: {{"new_scores": {{"L":.., "T":.., "SAI":.., "BD":.., "MF":..}}, "reason": "說明"}}
        """
        nodes['node2_scores'] = call_llm(prompt_2, json_mode=True)
        new_scores = nodes.get('node2_scores', {}).get('new_scores', st.session_state.scores)
        
        # 🌟 將冰冷的數字轉換為劇本語意
        current_situation = translate_state_to_semantics(new_scores)
        
        # --- Node 3: 內心 OS ---
        st.write("Node 3: 內心 OS 生成...")
        prompt_3 = f"""
        玩家剛說了：{user_speech}
        提取的內存：{p1_data.get('selected_memories', '')}
        當前心理防禦狀態：{current_situation['bd_situation']}
        任務：寫出 Sana 此刻最真實、未經過濾、可能帶有防禦或厭惡的內心吐槽 (模組 C)。
        """
        nodes['node3_inner'] = call_llm(prompt_3, json_mode=False)
        
        # --- Node 4: 營業面具 (物理隔離) ---
        st.write("Node 4: 物理隔離鑄造面具...")
        prompt_4 = f"""
        玩家剛說了：{user_speech}
        你現在不知道 Sana 內心在想什麼。請嚴格根據以下強制狀態演繹：
        【強制演出狀態】：{current_situation['mf_situation']}
        任務：依照上述狀態，設計她此刻給外人看的「表面態度與肢體動作」 (模組 D)。
        """
        nodes['node4_mask'] = call_llm(prompt_4, json_mode=False)

        # --- Node 5: 統籌與輸出 ---
        st.write("Node 5: 統籌裁決與最終台詞...")
        prompt_5 = f"""
        模組 C (內心)：{nodes.get('node3_inner', '')}
        模組 D (面具)：{nodes.get('node4_mask', '')}
        任務：結合兩者寫出最終回覆。
        最高限制：單次對話不超過 30 字，符合「說人話」模組，必須帶有日常語氣斷點。不准寫成小說。
        請回傳 JSON: {{"action": "(動作表情)", "speech": "「台詞」"}}
        """
        nodes['node5_output'] = call_llm(prompt_5, json_mode=True)

        # --- Node 6: 沉澱與更新 ---
        st.write("Node 6: 回合反思與目標更新...")
        prompt_6 = f"""
        當前目標：{st.session_state.current_goal}
        剛才的回覆：{nodes.get('node5_output', {}).get('speech', '')}
        任務：
        1. 評估目標是否需變更。
        2. 產出「下一輪策略與判定標準 (模組 A)」。
        請回傳 JSON: {{"new_goal": "...", "next_module_a": "..."}}
        """
        nodes['node6_reflection'] = call_llm(prompt_6, json_mode=True)

        status.update(label="✅ VFO 全節點管線運算完成！", state="complete", expanded=False)

    return nodes

# ==========================================
# 6. UI 呈現區
# ==========================================
with st.sidebar:
    st.title("⚙️ VFO 核心後台")
    st.caption("v7.3 Node-Based Pipeline + Semantic Translator")
    
    st.divider()
    st.subheader("🛠️ 狀態覆寫 (Cheat)")
    st.session_state.current_goal = st.text_input("當前目標", st.session_state.current_goal)
    st.session_state.user_labels = st.text_input("玩家標籤", st.session_state.user_labels)
    
    if st.button("🔴 重置系統狀態"):
        st.session_state.clear()
        st.rerun()

col_chat, col_monitor = st.columns([5, 5])

with col_chat:
    st.subheader("🏋️‍♀️ Sana 互動視窗")
    
    chat_box = st.container(height=550)
    for m in st.session_state.messages:
        with chat_box.chat_message(m["role"]):
            st.write(f"*{m['action']}* {m['speech']}")
            
    with st.form("chat_input", clear_on_submit=True):
        u_act = st.text_input("動作 (姿態)", placeholder="(拿著手搖飲走過來)")
        u_speech = st.text_input("對話內容", placeholder="說點什麼...")
        
        if st.form_submit_button("送出至 VFO") and u_speech:
            results = run_vfo_chain(u_speech, u_act)
            
            # 更新狀態機
            st.session_state.nodes_output = results
            if 'node2_scores' in results and 'new_scores' in results['node2_scores']:
                st.session_state.scores = results['node2_scores']['new_scores']
            if 'node6_reflection' in results:
                st.session_state.current_goal = results['node6_reflection'].get('new_goal', st.session_state.current_goal)
                st.session_state.prev_module_a = results['node6_reflection'].get('next_module_a', '')
            
            # 獲取 Sana 台詞
            final_out = results.get('node5_output', {})
            sana_act = final_out.get('action', '(思考)')
            sana_say = final_out.get('speech', '...')
            
            st.session_state.messages.append({"role": "user", "action": u_act, "speech": u_speech})
            st.session_state.messages.append({"role": "assistant", "action": sana_act, "speech": sana_say})
            st.rerun()

with col_monitor:
    st.subheader("📊 VFO 儀表板與黑盒子")
    
    s = st.session_state.scores
    m_cols = st.columns(3)
    m_cols[0].metric("L (友善)", s.get("L", 0))
    m_cols[1].metric("T (信任)", s.get("T", 0))
    m_cols[2].metric("MF (疲憊)", s.get("MF", 20), delta_color="inverse")
    
    st.divider()
    
    nb = st.session_state.nodes_output
    if nb:
        with st.expander("Node 1 & 2: 感知與結算", expanded=False):
            st.write("**提取內存:**", nb.get('node1_perception', {}).get('selected_memories'))
            st.write("**分數異動理由:**", nb.get('node2_scores', {}).get('reason'))
            
        with st.expander("🎭 Node 3 & 4: 內外分離 (語意翻譯)", expanded=True):
            current_sit = translate_state_to_semantics(st.session_state.scores)
            st.caption(f"🔧 傳遞給 Node 4 的強制劇本: {current_sit['mf_situation']}")
            st.markdown(f"<div class='inner-os'><b>模組 C (內心):</b><br>{nb.get('node3_inner')}</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='mask-os'><b>模組 D (面具):</b><br>{nb.get('node4_mask')}</div>", unsafe_allow_html=True)
            
        with st.expander("📅 Node 6: 次輪策略", expanded=False):
            st.write("**新目標:**", nb.get('node6_reflection', {}).get('new_goal'))
            st.info(nb.get('node6_reflection', {}).get('next_module_a'))
    else:
        st.info("請在左側輸入對話以啟動 VFO 引擎。")
