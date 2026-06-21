import streamlit as st
import random

# ==========================================
# 1. 初始化遊戲狀態 (Game State)
# ==========================================
if 'init' not in st.session_state:
    st.session_state.init = True
    st.session_state.day = 1
    
    # 基地資源
    st.session_state.food = 100
    st.session_state.materials = 50
    st.session_state.defense = 20
    
    # 人口群體 (數據化隊員)
    st.session_state.pop_workers = 15
    st.session_state.pop_guards = 5
    
    # NPC 陣營數據
    st.session_state.factions = {
        "新軍政府": {"好感度": 50, "武力": 80, "特產": "武器"},
        "狂信徒幫": {"好感度": 20, "武力": 40, "特產": "食物"}
    }
    
    # 事件日誌
    st.session_state.logs = ["系統啟動：長官，歡迎來到末日指揮中心。"]

# ==========================================
# 2. 核心遊戲邏輯：結算回合 (Game Loop)
# ==========================================
def end_day(scavenge_food, scavenge_mat, build_defense):
    logs_today = [f"--- 第 {st.session_state.day} 天結算 ---"]
    
    # 1. 結算生產與採集
    food_gained = scavenge_food * random.randint(1, 3)
    mat_gained = scavenge_mat * random.randint(1, 2)
    def_gained = build_defense * 1  # 每個工程人員增加 1 點防禦
    
    st.session_state.food += food_gained
    st.session_state.materials += mat_gained
    st.session_state.defense += def_gained
    logs_today.append(f"搜刮與建設結果：獲得 {food_gained} 食物, {mat_gained} 建材, 提升 {def_gained} 點防禦。")
    
    # 2. 結算消耗 (每人每天消耗 1 單位食物)
    total_pop = st.session_state.pop_workers + st.session_state.pop_guards
    st.session_state.food -= total_pop
    
    if st.session_state.food < 0:
        st.session_state.food = 0
        logs_today.append("⚠️ 警告：食物耗盡！基地發生飢荒，部分人員餓死或逃跑！")
        st.session_state.pop_workers -= random.randint(1, 3) # 隨機扣除人口
    else:
        logs_today.append(f"消耗：全體人員消耗了 {total_pop} 單位食物。")
    
    # 3. 隨機事件：喪屍襲擊
    if random.random() > 0.6:  # 40% 機率遇襲
        zombie_str = random.randint(10, 30)
        logs_today.append(f"🚨 警報：測量到強度 {zombie_str} 的喪屍群襲擊基地！")
        
        # 戰鬥計算：防禦力 + 守衛數量 vs 喪屍強度
        total_defense = st.session_state.defense + (st.session_state.pop_guards * 2)
        if total_defense >= zombie_str:
            logs_today.append("✅ 戰鬥結果：守衛成功擊退喪屍，基地無恙。")
        else:
            damage = zombie_str - total_defense
            st.session_state.defense -= damage
            st.session_state.pop_workers -= random.randint(0, 2)
            logs_today.append(f"❌ 戰鬥結果：防線被突破！防禦力下降，並有平民傷亡。")
            if st.session_state.defense < 0: st.session_state.defense = 0
            
    # 推進天數並更新日誌 (最新的在最上面)
    st.session_state.day += 1
    st.session_state.logs = logs_today + st.session_state.logs

# ==========================================
# 3. 戰情室介面設計 (UI Layout)
# ==========================================
st.set_page_config(page_title="末日指揮中心", layout="wide")
st.title(f"☢️ 基地指揮中心 - 第 {st.session_state.day} 天")

# 頂部資源儀表板
st.markdown("### 📊 基地狀態")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📦 食物", st.session_state.food)
col2.metric("🧱 建材", st.session_state.materials)
col3.metric("🛡️ 防禦力", st.session_state.defense)
col4.metric("👷 勞工 (人口)", st.session_state.pop_workers)
col5.metric("🔫 守衛 (武裝)", st.session_state.pop_guards)

st.divider()

# 主畫面分為三大區塊：行動指令、外部陣營、事件日誌
tab1, tab2, tab3 = st.tabs(["📋 今日行動分配", "🌍 外部陣營情報", "📜 事件日誌"])

with tab1:
    st.subheader("分配今日勞動人口")
    st.write(f"目前可用勞工總數：**{st.session_state.pop_workers}** 人")
    
    # 確保滑桿總數不會超過可用勞工
    scavenge_food = st.slider("派去搜刮【食物】的人數", 0, st.session_state.pop_workers, 0)
    remaining_workers = st.session_state.pop_workers - scavenge_food
    
    scavenge_mat = st.slider("派去搜刮【建材】的人數", 0, remaining_workers, 0)
    build_defense = remaining_workers - scavenge_mat
    
    st.info(f"剩下的 {build_defense} 人將留在基地【修築防禦工事】。")
    
    if st.button("▶️ 執行指令並結算這一天", type="primary"):
        end_day(scavenge_food, scavenge_mat, build_defense)
        st.rerun() # 重新整理畫面顯示最新數值

with tab2:
    st.subheader("已知人類勢力")
    for faction, data in st.session_state.factions.items():
        with st.expander(f"🚩 {faction}"):
            st.write(f"外交好感度：{data['好感度']}")
            st.progress(data['好感度'] / 100)
            st.write(f"預估武力值：{data['武力']}")
            st.button(f"與 {faction} 進行貿易 (開發中...)", key=faction)

with tab3:
    st.subheader("基地日誌")
    # 顯示前 15 筆日誌
    for log in st.session_state.logs[:15]:
        st.text(log)
