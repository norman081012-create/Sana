import streamlit as st
import math
import random

# 設定網頁標題與圖示
st.set_page_config(page_title="喪屍末日據點經營模擬器", page_icon="🧟", layout="wide")

# 初始化遊戲狀態
if 'game_started' not in st.session_state:
    st.session_state.game_started = True
    st.session_state.month = 1
    
    # 基礎資源
    st.session_state.human = 35          # 人力 (初始35人以利測試幼兒園無條件進位機制)
    st.session_state.food = 150          # 食物
    st.session_state.supply_box = 20     # 據點資源箱數量 (有限資源)
    
    # 箱內開出的二級資源
    st.session_state.ammo = 30           # 彈藥
    st.session_state.meds = 20           # 藥物
    st.session_state.gas = 10            # 汽油
    st.session_state.materials = 40      # 材料
    
    # 建築物數量 (初始配置)
    st.session_state.buildings = {
        "幼兒園": 1,
        "農場": 1,
        "藥學廠": 1,
        "彈藥工廠": 1,
        "拆箱區": 1
    }
    
    # 歷史紀錄日誌
    st.session_state.logs = ["【系統】遊戲開始！建立你的末日據點，帶領倖存者活下去。"]

# 遊戲標題
st.title("🧟 喪屍末日據點經營模擬器")
st.caption("基於核心資源轉換循環與據點特性的策略原型")

# 重設遊戲按鈕
if st.sidebar.button("🔄 重設遊戲狀態"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 顯示當前月份與核心警示
st.sidebar.markdown(f"## 📅 當前時間：第 **{st.session_state.month}** 個月")
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 生存規則提醒")
st.sidebar.write("1. **每個人力** 每月固定消耗 **2單位食物**。")
st.sidebar.write("2. **每個人力** 每月有 20% 機率生病，需消耗 **1單位藥物**，若藥物不足人口會減少。")
st.sidebar.write("3. **資源箱** 是有限的，抽完就必須尋找新據點。")
st.sidebar.write("4. 每月都有可能遭遇**喪屍襲擊**或**人類派系互動**！")

# 頂部資源看板
st.markdown("### 📦 據點物資現況")
col1, col2, col3, col4, col5, col6, col7 = st.columns(7)
col1.metric("👥 人力 (總口數)", st.session_state.human)
col2.metric("🍞 食物", st.session_state.food)
col3.metric("📦 剩餘資源箱", st.session_state.supply_box)
col4.metric("💥 彈藥", st.session_state.ammo)
col5.metric("💊 藥物", st.session_state.meds)
col6.metric("⛽ 汽油", st.session_state.gas)
col7.metric("🪵 材料", st.session_state.materials)

st.markdown("---")

# 遊戲主要區塊：左邊配置人力/建築，右邊顯示事件日誌
main_col1, main_col2 = st.columns([3, 2])

with main_col1:
    st.markdown("### 🛠️ 據點建築與人力派駐管理")
    st.write("請分配你的人力到各個建築物進行生產（未分配的人力將留守進行基本防禦）。")
    
    # 人力分配控制項
    max_human = st.session_state.human
    
    st.markdown(f"**可用總人力：{max_human} 人**")
    
    # 1. 幼兒園 (被動生產)
    st.markdown("#### 🏫 幼兒園 (人口繁衍中心)")
    kg_count = st.session_state.buildings["幼兒園"]
    kg_prod = math.ceil(max_human / 30) * kg_count
    st.info(f"當前數量：{kg_count} 間 | 特性：每個月自動產出 `總人口 / 30 (無條件進位)` 的人力。本月預期新增：**{kg_prod}** 人力。")
    
    # 2. 農場
    st.markdown("#### 🌾 農場")
    farm_workers = st.slider("派駐農場人力 (每人產出 5 食物)", 0, max_human, min(10, max_human), key="farm")
    
    # 3. 彈藥工廠
    st.markdown("#### 🏭 彈藥工廠")
    max_after_farm = max(0, max_human - farm_workers)
    ammo_workers = st.slider("派駐彈藥工廠人力 (每人消耗 2 材料 ➡️ 產出 4 彈藥)", 0, max_human, min(5, max_after_farm), key="ammo_fac")
    
    # 4. 藥學廠
    st.markdown("#### 🧪 藥學廠")
    max_after_ammo = max(0, max_after_farm - ammo_workers)
    med_workers = st.slider("派駐藥學廠人力 (每人消耗 2 食物 ➡️ 產出 3 藥物)", 0, max_human, min(5, max_after_ammo), key="med_fac")
    
    # 5. 拆箱區
    st.markdown("#### 📦 資源箱拆箱區")
    max_after_med = max(0, max_after_ammo - med_workers)
    box_workers = st.slider("派駐拆箱人力 (每人消耗 1 資源箱 ➡️ 隨機獲得基礎二級物資)", 0, max_human, min(5, max_after_med), key="box_fac")
    
    total_assigned = farm_workers + ammo_workers + med_workers + box_workers
    unassigned = max_human - total_assigned
    
    if total_assigned > max_human:
        st.error(f"❌ 警告：派駐總人力 ({total_assigned}人) 超過當前據點可用總人口 ({max_human}人)！請調整滑桿。")
        btn_disabled = True
    else:
        st.success(f"✅ 已分配人力：{total_assigned} 人 | 留守/防禦人力：{unassigned} 人")
        btn_disabled = False

    st.markdown("---")
    
    # 前進下一回合/月份的按鈕與核心邏輯
    if st.button("▶️ 結算本月，前進至下個月", disabled=btn_disabled, type="primary"):
        new_logs = []
        new_logs.append(f"--- 【第 {st.session_state.month} 個月 結算報告】 ---")
        
        # 1. 人口自然增長 (幼兒園)
        st.session_state.human += kg_prod
        new_logs.append(f"👶 幼兒園發揮作用，本月新增了 {kg_prod} 名新生人力。")
        
        # 2. 生產階段
        # 農場產出
        food_produced = farm_workers * 5
        st.session_state.food += food_produced
        if farm_workers > 0:
            new_logs.append(f"🌾 農場投入 {farm_workers} 人，成功採收了 {food_produced} 單位食物。")
            
        # 彈藥工廠轉換
        ammo_materials_needed = ammo_workers * 2
        if st.session_state.materials >= ammo_materials_needed:
            st.session_state.materials -= ammo_materials_needed
            ammo_produced = ammo_workers * 4
            st.session_state.ammo += ammo_produced
            if ammo_workers > 0:
                new_logs.append(f"🏭 彈藥工廠消耗 {ammo_materials_needed} 材料，製作了 {ammo_produced} 單位彈藥。")
        else:
            # 材料不足，按比例生產
            actual_workers = st.session_state.materials // 2
            st.session_state.materials -= (actual_workers * 2)
            ammo_produced = actual_workers * 4
            st.session_state.ammo += ammo_produced
            if ammo_workers > 0:
                new_logs.append(f"⚠️ 材料不足！彈藥工廠僅能供 {actual_workers} 人運作，消耗全部材料產出 {ammo_produced} 單位彈藥。")
                
        # 藥學廠轉換
        med_food_needed = med_workers * 2
        if st.session_state.food >= med_food_needed:
            st.session_state.food -= med_food_needed
            med_produced = med_workers * 3
            st.session_state.meds += med_produced
            if med_workers > 0:
                new_logs.append(f"🧪 藥學廠消耗 {med_food_needed} 食物，提煉了 {med_produced} 單位藥物。")
        else:
            actual_med_workers = st.session_state.food // 2
            st.session_state.food -= (actual_med_workers * 2)
            med_produced = actual_med_workers * 3
            st.session_state.meds += med_produced
            if med_workers > 0:
                new_logs.append(f"⚠️ 食物不足！藥學廠僅能供 {actual_med_workers} 人運作，提煉了 {med_produced} 單位藥物。")
                
        # 拆箱區
        actual_boxes_to_open = min(box_workers, st.session_state.supply_box)
        if actual_boxes_to_open > 0:
            st.session_state.supply_box -= actual_boxes_to_open
            # 隨機抽取資源
            get_food = 0
            get_ammo = 0
            get_meds = 0
            get_gas = 0
            get_mats = 0
            for _ in range(actual_boxes_to_open):
                get_food += random.randint(1, 3)
                get_ammo += random.randint(1, 3)
                get_meds += random.randint(0, 2)
                get_gas += random.randint(0, 1)
                get_mats += random.randint(1, 4)
            
            st.session_state.food += get_food
            st.session_state.ammo += get_ammo
            st.session_state.meds += get_meds
            st.session_state.gas += get_gas
            st.session_state.materials += get_mats
            
            new_logs.append(f"📦 拆箱工人開啟了 {actual_boxes_to_open} 個資源箱！獲得：食物+{get_food}、彈藥+{get_ammo}、藥物+{get_meds}、汽油+{get_gas}、材料+{get_mats}。")
        elif box_workers > 0 and st.session_state.supply_box == 0:
            new_logs.append("🚨 警告：據點內的資源箱已經完全枯竭！拆箱工人毫無收穫。需要尋找新據點！")

        # 3. 消耗階段 (生存壓力)
        # 食物消耗
        food_consumed = st.session_state.human * 2
        if st.session_state.food >= food_consumed:
            st.session_state.food -= food_consumed
            new_logs.append(f"🍽️ 全體倖存者消耗了 {food_consumed} 單位食物。")
        else:
            deficit = food_consumed - st.session_state.food
            starved_humans = math.ceil(deficit / 4) # 每缺4食物就餓死1人
            st.session_state.food = 0
            st.session_state.human = max(0, st.session_state.human - starved_humans)
            new_logs.append(f"💀 食物嚴重短缺！發生飢荒，有 {starved_humans} 名倖存者不幸餓死。")

        # 藥物生病消耗
        sick_count = 0
        for _ in range(st.session_state.human):
            if random.random() < 0.20: # 20% 生病機率
                sick_count += 1
                
        if sick_count > 0:
            if st.session_state.meds >= sick_count:
                st.session_state.meds -= sick_count
                new_logs.append(f"🤢 本月有 {sick_count} 人生病，消耗了 {sick_count} 單位藥物後全員痊癒。")
            else:
                untreated = sick_count - st.session_state.meds
                st.session_state.meds = 0
                dead_by_disease = math.ceil(untreated / 2) # 沒藥醫的人有一半機率死亡
                st.session_state.human = max(0, st.session_state.human - dead_by_disease)
                new_logs.append(f"💔 醫療資源不足！{sick_count} 人生病但藥物不夠，導致 {dead_by_disease} 人因病去世。")

        # 4. 外部隨機事件 (喪屍派系與人類派系)
        event_roll = random.random()
        if event_roll < 0.35:
            # 喪屍襲擊事件
            zombie_strength = random.randint(5, 15) + (st.session_state.month * 2)
            new_logs.append(f"⚠️ 【危機】大量喪屍襲擊據點！(屍潮強度: {zombie_strength})")
            
            # 防禦計算：彈藥能抵消屍潮，留守人力也能提供防禦協助
            ammo_defense = st.session_state.ammo
            if ammo_defense >= zombie_strength:
                st.session_state.ammo -= zombie_strength
                new_logs.append(f"🛡️ 守軍火力充足！消耗 {zombie_strength} 單位彈藥成功擊退屍潮，無人傷亡。")
            else:
                # 彈藥不夠，需要肉搏，留守人力幫忙減傷
                st.session_state.ammo = 0
                breach_damage = zombie_strength - ammo_defense
                # 留守人力每2人可以抵消1點肉搏傷害
                absorbed = unassigned // 2
                final_damage = max(1, breach_damage - absorbed)
                
                st.session_state.human = max(0, st.session_state.human - final_damage)
                new_logs.append(f"💥 火力不足！屍潮突破防線，雖有 {unassigned} 人留守反擊，仍有 {final_damage} 名倖存者在肉搏戰中犧牲。")
                
        elif event_roll < 0.60:
            # 人類派系互動
            human_factions = ["黑市商人", "鋼鐵兄弟會", "廢土掠奪者"]
            faction = random.choice(human_factions)
            
            if faction == "黑市商人":
                # 有利的貿易事件
                if st.session_state.gas >= 2:
                    st.session_state.gas -= 2
                    st.session_state.materials += 10
                    new_logs.append("🤝【外交】「黑市商人」拜訪據點。你用 2 單位汽油向他們交換了 10 單位建築材料。")
                else:
                    new_logs.append("🤝【外交】「黑市商人」拜訪據點，但你沒有足夠的汽油與他們進行物資交易。")
            elif faction == "鋼鐵兄弟會":
                # 互助事件
                st.session_state.ammo += 10
                new_logs.append("🎖️【外交】友善的人類派系「鋼鐵兄弟會」路過，讚賞你們的求生精神，贈予了 10 單位彈藥。")
            elif faction == "廢土掠奪者":
                # 掠奪者敵對事件
                new_logs.append("☠️【遭遇】「廢土掠奪者」前來勒索物資！")
                if st.session_state.ammo >= 8:
                    st.session_state.ammo -= 8
                    new_logs.append("🔫 據點守軍開槍示警並消耗 8 單位彈藥，成功嚇退了掠奪者。")
                else:
                    st.session_state.food = max(0, st.session_state.food - 30)
                    new_logs.append("😭 你們沒有足夠的彈藥反擊，據點被掠奪者強行搶走了 30 單位食物。")
        else:
            new_logs.append("🕊️ 本月無外部派系滋擾，據點度過了一個相對平靜的時間。")

        # 遊戲結束判定
        if st.session_state.human <= 0:
            new_logs.append("💀💀💀 【遊戲結束】 據點所有倖存者均已死亡，人類的火種熄滅了... 💀💀💀")
            st.session_state.game_started = False
            
        # 更新狀態
        st.session_state.month += 1
        st.session_state.logs = new_logs + st.session_state.logs
        st.rerun()

with main_col2:
    st.markdown("### 📜 據點事件與歷史日誌")
    
    # 顯示遊戲結束大橫幅
    if st.session_state.human <= 0:
        st.error("🚨 據點全員覆沒！請點擊左側「重設遊戲狀態」重新開始。")
        
    # 用容器顯示日誌
    log_container = st.container(height=500)
    with log_container:
        for log in st.session_state.logs:
            if "❌" in log or "💀" in log or "⚠️" in log or "💥" in log or "☠️" in log:
                st.markdown(f"<span style='color:#e74c3c;'>{log}</span>", unsafe_allow_html=True)
            elif "✅" in log or "🌾" in log or "🧪" in log or "📦" in log or "🤝" in log or "🎖️" in log:
                st.markdown(f"<span style='color:#2ecc71;'>{log}</span>", unsafe_allow_html=True)
            else:
                st.write(log)
