import streamlit as st
import math
import random

# 設定網頁標題與圖示
st.set_page_config(page_title="喪屍末日據點經營模擬器 V3", page_icon="🧟", layout="wide")

# 建築物基礎資料表 (花費、天數與效果)
BUILDING_DATA = {
    "伐木場": {"cost": 20, "days": 2, "desc": "產生材料 (Lv*5 派駐上限，每人產2材料)"},
    "農場": {"cost": 20, "days": 2, "desc": "產生食物 (Lv*5 派駐上限，每人產2食物)"},
    "探索區": {"cost": 15, "days": 1, "desc": "消耗資源箱換取物資 (Lv*3 派駐上限)"},
    "藥學廠": {"cost": 25, "days": 3, "desc": "食物轉換為藥物 (Lv*2 派駐上限)"},
    "幼兒園": {"cost": 30, "days": 3, "desc": "被動效果：每日有 (Lv*5)% 機率增加1人口"},
    "住宅區": {"cost": 30, "days": 3, "desc": "被動效果：每級增加 20 點人口容量上限"},
    "防禦設施": {"cost": 25, "days": 2, "desc": "被動效果：每級增加 10 點據點防禦值"}
}

def generate_destinations():
    base_templates = [
        {"name_prefix": "廢棄的農場", "slots": (4, 6), "boxes": (30, 50), "def_bonus": 2, "neutral": (2, 8)},
        {"name_prefix": "市區辦公大樓", "slots": (6, 10), "boxes": (40, 70), "def_bonus": 10, "neutral": (5, 15)},
        {"name_prefix": "郊區學校", "slots": (5, 8), "boxes": (20, 30), "def_bonus": 5, "neutral": (10, 20)},
        {"name_prefix": "軍事哨站", "slots": (3, 5), "boxes": (50, 90), "def_bonus": 20, "neutral": (0, 3)}
    ]
    destinations = []
    for _ in range(3):
        template = random.choice(base_templates)
        destinations.append({
            "name": f"{template['name_prefix']} (區域 {random.randint(10, 99)})",
            "travel_days": random.randint(3, 7),
            "max_slots": random.randint(*template['slots']),
            "boxes": random.randint(*template['boxes']),
            "defense_bonus": template['def_bonus'],
            "neutral_pop": random.randint(*template['neutral'])
        })
    return destinations

# 初始化遊戲狀態
if 'game_started' not in st.session_state:
    st.session_state.game_started = True
    st.session_state.day = 1
    
    # 基礎資源
    st.session_state.human = 15          
    st.session_state.food = 100          
    
    # 箱內開出的二級資源
    st.session_state.ammo = 50           
    st.session_state.meds = 20           
    st.session_state.gas = 20            
    st.session_state.materials = 150  # 初始材料調高，供玩家初期建設    
    
    # 當前據點資訊
    st.session_state.current_base = {
        "name": "市郊避難所 (初始)",
        "max_slots": 3,
        "boxes": 30,
        "defense_bonus": 5,
        "neutral_pop": 3,
        "zombie_threat": 0 # 周圍喪屍數量
    }
    
    # 建築槽位系統 (初始3個空位)
    st.session_state.slots = [{"type": None, "level": 0, "status": "empty", "days_left": 0} for _ in range(3)]
    
    st.session_state.destinations = generate_destinations()
    st.session_state.logs = ["【系統】遊戲開始！這是一個殘酷的世界，請盡快利用手上的材料建造維生設施。"]

st.title("🧟 喪屍末日據點經營模擬器 V3")

if st.sidebar.button("🔄 重設遊戲狀態"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown(f"## 📅 存活時間：第 **{st.session_state.day}** 天")
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 生存規則")
st.sidebar.write("- **食物消耗**：每人每日消耗 **1** 食物。超載人口會導致生病率大增！")
st.sidebar.write("- **建設系統**：建築需要耗費「材料」與「日數」，升級可提升派駐上限或被動加成。")
st.sidebar.write("- **喪屍威脅**：周圍喪屍每日會聚集，數量越多越容易發動襲擊。防禦值可抵擋喪屍。")

# 計算被動建築加成
active_slots = [s for s in st.session_state.slots if s["status"] == "active"]
residential_cap = sum(s["level"] * 20 for s in active_slots if s["type"] == "住宅區")
defense_bld_bonus = sum(s["level"] * 10 for s in active_slots if s["type"] == "防禦設施")
kindergarten_lv = sum(s["level"] for s in active_slots if s["type"] == "幼兒園")

max_population_cap = 20 + residential_cap # 據點基礎容量20 + 住宅區加成

# ----------------- 頂部看板 -----------------
st.markdown("### 📦 物資現況")
col_r1, col_r2, col_r3, col_r4, col_r5, col_r6 = st.columns(6)
pop_color = "normal" if st.session_state.human <= max_population_cap else "inverse"
col_r1.metric("👥 人力 / 容量", f"{st.session_state.human} / {max_population_cap}", delta="超載" if st.session_state.human > max_population_cap else "", delta_color=pop_color)
col_r2.metric("🍞 食物", st.session_state.food)
col_r3.metric("🪵 材料", st.session_state.materials)
col_r4.metric("💥 彈藥", st.session_state.ammo)
col_r5.metric("💊 藥物", st.session_state.meds)
col_r6.metric("⛽ 汽油", st.session_state.gas)

st.markdown("### 🏕️ 據點現況：**" + st.session_state.current_base["name"] + "**")
col_b1, col_b2, col_b3, col_b4 = st.columns(4)
col_b1.metric("🧟 周圍喪屍威脅", st.session_state.current_base["zombie_threat"])
col_b2.metric("🛡️ 建築防禦加成", st.session_state.current_base["defense_bonus"] + defense_bld_bonus)
col_b3.metric("📦 剩餘資源箱", st.session_state.current_base["boxes"])
col_b4.metric("🤝 中立人口", st.session_state.current_base["neutral_pop"])

st.markdown("---")

# ----------------- 主要操作區 -----------------
main_col1, main_col2 = st.columns([3, 2])

with main_col1:
    tab1, tab2, tab3 = st.tabs(["🛠️ 派駐與生產", "🏗️ 建設與升級", "🗺️ 世界地圖"])
    
    # --- Tab 1: 派駐與生產 ---
    with tab1:
        st.markdown("#### 人力派駐管理 (僅顯示已建成的生產建築)")
        max_human = st.session_state.human
        total_assigned = 0
        btn_disabled = False
        
        # 動態計算可用生產建築等級上限
        lumber_lv = sum(s["level"] for s in active_slots if s["type"] == "伐木場")
        farm_lv = sum(s["level"] for s in active_slots if s["type"] == "農場")
        med_lv = sum(s["level"] for s in active_slots if s["type"] == "藥學廠")
        explore_lv = sum(s["level"] for s in active_slots if s["type"] == "探索區")
        
        if lumber_lv == 0 and farm_lv == 0 and med_lv == 0 and explore_lv == 0:
            st.info("⚠️ 當前沒有可派駐的生產建築。請先到「建設與升級」標籤建造農場、伐木場或探索區！")
        
        lumber_workers = st.slider(f"🪓 伐木場 (上限 {lumber_lv*5} 人 | 每人產 2 材料)", 0, lumber_lv*5, 0) if lumber_lv > 0 else 0
        farm_workers = st.slider(f"🌾 農場 (上限 {farm_lv*5} 人 | 每人產 2 食物)", 0, farm_lv*5, 0) if farm_lv > 0 else 0
        med_workers = st.slider(f"🧪 藥學廠 (上限 {med_lv*2} 人 | 每人消耗 1 食物 ➡️ 產 1 藥物)", 0, med_lv*2, 0) if med_lv > 0 else 0
        explore_workers = st.slider(f"📦 探索區 (上限 {explore_lv*3} 人 | 每人消耗 1 箱 ➡️ 隨機物資)", 0, explore_lv*3, 0) if explore_lv > 0 else 0
        
        total_assigned = lumber_workers + farm_workers + med_workers + explore_workers
        unassigned = max_human - total_assigned
        total_defense = st.session_state.current_base["defense_bonus"] + defense_bld_bonus + unassigned
        
        if total_assigned > max_human:
            st.error(f"❌ 派駐人力 ({total_assigned}) 超過總人口 ({max_human})！")
            btn_disabled = True
        else:
            st.success(f"✅ 留守/防禦人力：{unassigned} 人 (當前總防禦力: {total_defense})")

        # 推進天數核心按鈕
        if st.button("▶️ 結束本日，進入明天", disabled=btn_disabled, type="primary", use_container_width=True):
            new_logs = []
            new_logs.append(f"--- 【第 {st.session_state.day} 天 結算報告】 ---")
            
            # 1. 處理建築與升級進度
            for i, slot in enumerate(st.session_state.slots):
                if slot["status"] in ["building", "upgrading"]:
                    slot["days_left"] -= 1
                    if slot["days_left"] <= 0:
                        slot["level"] += 1
                        slot["status"] = "active"
                        new_logs.append(f"🏗️ 建築完工！【{slot['type']}】已達到等級 {slot['level']}。")

            # 2. 幼兒園被動生產
            if kindergarten_lv > 0:
                if random.randint(1, 100) <= (kindergarten_lv * 5):
                    st.session_state.human += 1
                    new_logs.append("👶 幼兒園發揮作用，據點吸引了 1 名新生人力。")

            # 3. 生產結算
            if lumber_workers > 0:
                prod = lumber_workers * 2
                st.session_state.materials += prod
                new_logs.append(f"🪓 伐木場產出了 {prod} 材料。")
                
            if farm_workers > 0:
                prod = farm_workers * 2
                st.session_state.food += prod
                new_logs.append(f"🌾 農場採收了 {prod} 食物。")
                
            if med_workers > 0:
                if st.session_state.food >= med_workers:
                    st.session_state.food -= med_workers
                    st.session_state.meds += med_workers
                    new_logs.append(f"🧪 藥廠提煉了 {med_workers} 藥物。")
                else:
                    new_logs.append("⚠️ 食物不足，藥廠無法全速運轉！")
                    
            if explore_workers > 0:
                actual_boxes = min(explore_workers, st.session_state.current_base["boxes"])
                if actual_boxes > 0:
                    st.session_state.current_base["boxes"] -= actual_boxes
                    f, a, m, g, mat = 0, 0, 0, 0, 0
                    for _ in range(actual_boxes):
                        f += random.randint(0, 2); a += random.randint(0, 2)
                        m += random.randint(0, 1); g += random.randint(0, 1)
                        mat += random.randint(1, 4)
                    st.session_state.food += f; st.session_state.ammo += a
                    st.session_state.meds += m; st.session_state.gas += g; st.session_state.materials += mat
                    new_logs.append(f"📦 探索區開啟 {actual_boxes} 資源箱：食物+{f}, 彈藥+{a}, 藥物+{m}, 汽油+{g}, 材料+{mat}。")
                else:
                    new_logs.append("🚨 據點資源箱已枯竭，探索區無收穫。")

            # 4. 消耗結算
            if st.session_state.food >= st.session_state.human:
                st.session_state.food -= st.session_state.human
            else:
                starved = math.ceil((st.session_state.human - st.session_state.food) / 2)
                st.session_state.food = 0
                st.session_state.human = max(0, st.session_state.human - starved)
                new_logs.append(f"💀 飢荒爆發！沒有足夠食物，{starved} 人不幸餓死。")

            # 5. 生病判定 (超載懲罰)
            sick_rate = 0.02 if st.session_state.human <= max_population_cap else 0.15
            if sick_rate > 0.02: new_logs.append("⚠️ 警告：人口超過住宅容量，居住環境擁擠導致生病率大幅提升！")
            
            sick = sum(1 for _ in range(st.session_state.human) if random.random() < sick_rate)
            if sick > 0:
                if st.session_state.meds >= sick:
                    st.session_state.meds -= sick
                    new_logs.append(f"🤢 {sick} 人生病，已消耗藥物治癒。")
                else:
                    dead = sick - st.session_state.meds
                    st.session_state.meds = 0
                    st.session_state.human = max(0, st.session_state.human - dead)
                    new_logs.append(f"💔 藥物不足！{dead} 人因病去世。")

            # 6. 周圍喪屍與襲擊判定
            st.session_state.current_base["zombie_threat"] += random.randint(2, 6)
            threat = st.session_state.current_base["zombie_threat"]
            attack_chance = min(threat, 80) # 最高80%機率襲擊
            
            if random.randint(1, 100) <= attack_chance:
                new_logs.append(f"🚨 【屍潮來襲】聚集的喪屍發動了攻擊！(喪屍數量: {threat} vs 總防禦: {total_defense})")
                if total_defense >= threat:
                    new_logs.append("🛡️ 靠著堅固的防禦與留守人員，據點無傷擊退屍潮！喪屍被清剿。")
                    st.session_state.current_base["zombie_threat"] = 0
                else:
                    breach = threat - total_defense
                    if st.session_state.ammo >= breach:
                        st.session_state.ammo -= breach
                        new_logs.append(f"🔫 防禦被突破！消耗 {breach} 彈藥成功消滅突入的喪屍。")
                        st.session_state.current_base["zombie_threat"] = 0
                    else:
                        st.session_state.ammo = 0
                        dmg = breach - st.session_state.ammo
                        dead = max(1, dmg // 3)
                        st.session_state.human = max(0, st.session_state.human - dead)
                        new_logs.append(f"💥 彈藥耗盡！喪屍在據點內展開屠殺，{dead} 名倖存者喪生！")
                        st.session_state.current_base["zombie_threat"] = max(0, threat - total_defense - 10)

            st.session_state.day += 1
            st.session_state.logs = new_logs + st.session_state.logs
            st.rerun()

    # --- Tab 2: 建設與升級 ---
    with tab2:
        st.markdown(f"#### 🏗️ 據點建築槽位 ({len(st.session_state.slots)} 格)")
        
        for i, slot in enumerate(st.session_state.slots):
            with st.container():
                st.markdown(f"**欄位 {i+1}**")
                if slot["status"] == "empty":
                    b_type = st.selectbox("選擇建築", list(BUILDING_DATA.keys()), key=f"sel_{i}", label_visibility="collapsed")
                    req_cost = BUILDING_DATA[b_type]["cost"]
                    req_days = BUILDING_DATA[b_type]["days"]
                    st.caption(BUILDING_DATA[b_type]["desc"])
                    if st.button(f"🔨 開始建設 {b_type} (耗 {req_cost} 材料, {req_days} 天)", key=f"bld_{i}"):
                        if st.session_state.materials >= req_cost:
                            st.session_state.materials -= req_cost
                            st.session_state.slots[i] = {"type": b_type, "level": 0, "status": "building", "days_left": req_days}
                            st.session_state.logs.insert(0, f"🔨 消耗了 {req_cost} 材料，開始在欄位 {i+1} 建設【{b_type}】，預計 {req_days} 天後完工。")
                            st.rerun()
                        else:
                            st.error("材料不足！")
                
                elif slot["status"] in ["building", "upgrading"]:
                    st.info(f"🚧 【{slot['type']}】施工中... 剩餘 {slot['days_left']} 天")
                
                elif slot["status"] == "active":
                    req_cost = BUILDING_DATA[slot["type"]]["cost"] * (slot["level"] + 1)
                    req_days = BUILDING_DATA[slot["type"]]["days"]
                    st.success(f"🏢 **Lv.{slot['level']} {slot['type']}**")
                    if st.button(f"⬆️ 升級至 Lv.{slot['level']+1} (耗 {req_cost} 材料, {req_days} 天)", key=f"upg_{i}"):
                        if st.session_state.materials >= req_cost:
                            st.session_state.materials -= req_cost
                            st.session_state.slots[i]["status"] = "upgrading"
                            st.session_state.slots[i]["days_left"] = req_days
                            st.session_state.logs.insert(0, f"⬆️ 消耗了 {req_cost} 材料，開始升級【{slot['type']}】，預計 {req_days} 天後完工。")
                            st.rerun()
                        else:
                            st.error("材料不足！")
                st.divider()

    # --- Tab 3: 世界地圖 ---
    with tab3:
        st.markdown("#### 🗺️ 探索與遷移")
        st.write("放棄目前的據點建築，帶著所有物資前往新的地點。")
        
        total_cargo = st.session_state.food + st.session_state.ammo + st.session_state.meds + st.session_state.materials
        st.info(f"車隊當前物資總量：**{total_cargo}** 單位")
        
        selected_dest_name = st.selectbox("選擇目標據點", [d["name"] for d in st.session_state.destinations])
        dest = next(d for d in st.session_state.destinations if d["name"] == selected_dest_name)
        
        st.markdown(f"**目標資訊**：距離 {dest['travel_days']} 天 | 空位 {dest['max_slots']} | 資源箱 {dest['boxes']} | 基礎防禦 {dest['defense_bonus']} | 中立人口 {dest['neutral_pop']}")
        
        req_food = st.session_state.human * dest["travel_days"]
        req_gas = math.ceil(total_cargo / 100) * dest["travel_days"]
        
        col_c1, col_c2 = st.columns(2)
        col_c1.metric("🍞 遷移所需食物", req_food, f"現有: {st.session_state.food}")
        col_c2.metric("⛽ 遷移所需汽油", req_gas, f"現有: {st.session_state.gas}")
        
        can_migrate = st.session_state.food >= req_food and st.session_state.gas >= req_gas
        if not can_migrate: st.error("⚠️ 食物或汽油不足，無法進行遷移！")
        
        if st.button("🚚 開始遷移！", disabled=not can_migrate, type="primary"):
            st.session_state.food -= req_food
            st.session_state.gas -= req_gas
            st.session_state.day += dest["travel_days"]
            st.session_state.current_base = dest
            st.session_state.current_base["zombie_threat"] = 0
            
            # 重置為全新空地
            st.session_state.slots = [{"type": None, "level": 0, "status": "empty", "days_left": 0} for _ in range(dest["max_slots"])]
            st.session_state.destinations = generate_destinations()
            st.session_state.logs.insert(0, f"🚚 歷經 {dest['travel_days']} 天跋涉，抵達新據點：{dest['name']}。一切建設必須從頭開始！")
            st.rerun()

# ----------------- 右側日誌區 -----------------
with main_col2:
    st.markdown("### 📜 事件日誌")
    if st.session_state.human <= 0:
        st.error("🚨 據點全員覆沒！遊戲結束。")
        
    log_container = st.container(height=650)
    with log_container:
        for log in st.session_state.logs:
            if "❌" in log or "💀" in log or "⚠️" in log or "💥" in log or "🚨" in log or "💔" in log:
                st.markdown(f"<span style='color:#e74c3c;'>{log}</span>", unsafe_allow_html=True)
            elif "✅" in log or "🌾" in log or "🧪" in log or "📦" in log or "🤝" in log or "🚚" in log or "🏗️" in log or "🪓" in log:
                st.markdown(f"<span style='color:#2ecc71;'>{log}</span>", unsafe_allow_html=True)
            else:
                st.write(log)
