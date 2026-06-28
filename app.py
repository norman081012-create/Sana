import streamlit as st
import math
import random

# 設定網頁標題與圖示
st.set_page_config(page_title="喪屍末日據點經營模擬器 V2", page_icon="🧟", layout="wide")

# 動態生成新據點的函數
def generate_destinations():
    base_templates = [
        {"name_prefix": "廢棄的農場", "slots": (15, 20), "boxes": (30, 50), "def_bonus": (2, 5), "neutral": (2, 8)},
        {"name_prefix": "市區辦公大樓", "slots": (25, 35), "boxes": (40, 70), "def_bonus": (10, 15), "neutral": (5, 15)},
        {"name_prefix": "郊區幼兒園", "slots": (10, 15), "boxes": (20, 30), "def_bonus": (5, 10), "neutral": (10, 20)},
        {"name_prefix": "軍事哨站", "slots": (10, 15), "boxes": (50, 90), "def_bonus": (25, 40), "neutral": (0, 3)}
    ]
    destinations = []
    for _ in range(3):
        template = random.choice(base_templates)
        destinations.append({
            "name": f"{template['name_prefix']} (區域 {random.randint(10, 99)})",
            "travel_days": random.randint(3, 7),
            "max_slots": random.randint(*template['slots']),
            "boxes": random.randint(*template['boxes']),
            "defense_bonus": random.randint(*template['def_bonus']),
            "neutral_pop": random.randint(*template['neutral'])
        })
    return destinations

# 初始化遊戲狀態
if 'game_started' not in st.session_state:
    st.session_state.game_started = True
    st.session_state.day = 1
    
    # 基礎資源
    st.session_state.human = 35          
    st.session_state.food = 200          # 初始食物調高，因為按日消耗
    
    # 箱內開出的二級資源
    st.session_state.ammo = 50           
    st.session_state.meds = 20           
    st.session_state.gas = 20            
    st.session_state.materials = 50      
    
    # 當前據點資訊
    st.session_state.current_base = {
        "name": "市郊避難所 (初始)",
        "max_slots": 15,
        "boxes": 30,
        "defense_bonus": 5,
        "neutral_pop": 3
    }
    
    # 建築物數量
    st.session_state.buildings = {
        "幼兒園": 1,
        "農場": 1,
        "藥學廠": 1,
        "彈藥工廠": 1,
        "拆箱區": 1
    }
    
    # 可遷移據點
    st.session_state.destinations = generate_destinations()
    
    # 歷史紀錄日誌
    st.session_state.logs = ["【系統】遊戲開始！這是一個殘酷的世界，以「日」為單位努力活下去吧。"]

# 遊戲標題
st.title("🧟 喪屍末日據點經營模擬器 V2")

# 重設遊戲按鈕
if st.sidebar.button("🔄 重設遊戲狀態"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# 側邊欄規則
st.sidebar.markdown(f"## 📅 存活時間：第 **{st.session_state.day}** 天")
st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 生存規則 (日更版)")
st.sidebar.write("- **食物消耗**：每人每日消耗 **1** 食物。")
st.sidebar.write("- **疾病判定**：每人每日有 **2%** 機率生病，需1藥物。")
st.sidebar.write("- **防禦值**：據點基礎防禦 + (留守人力 × 1)。")
st.sidebar.write("- **遷移機制**：旅行需扣除食物與汽油，搬運的物資越多，消耗的汽油越大！")

# ----------------- 頂部看板 -----------------
# 1. 物資現況
st.markdown("### 📦 物資現況")
col_r1, col_r2, col_r3, col_r4, col_r5, col_r6 = st.columns(6)
col_r1.metric("👥 人力 (總口數)", st.session_state.human)
col_r2.metric("🍞 食物", st.session_state.food)
col_r3.metric("💥 彈藥", st.session_state.ammo)
col_r4.metric("💊 藥物", st.session_state.meds)
col_r5.metric("⛽ 汽油", st.session_state.gas)
col_r6.metric("🪵 材料", st.session_state.materials)

# 2. 據點現況
st.markdown("### 🏕️ 據點現況：**" + st.session_state.current_base["name"] + "**")
col_b1, col_b2, col_b3, col_b4 = st.columns(4)

used_slots = sum(st.session_state.buildings.values())
free_slots = st.session_state.current_base["max_slots"] - used_slots

col_b1.metric("🛡️ 據點基礎防禦", st.session_state.current_base["defense_bonus"])
col_b2.metric("📦 剩餘資源箱", st.session_state.current_base["boxes"])
col_b3.metric("🤝 中立人口", st.session_state.current_base["neutral_pop"])
col_b4.metric("🏗️ 剩餘建築欄位", f"{free_slots} / {st.session_state.current_base['max_slots']}")

st.markdown("---")

# ----------------- 主要操作區 -----------------
main_col1, main_col2 = st.columns([3, 2])

with main_col1:
    tab1, tab2 = st.tabs(["🛠️ 據點營運", "🗺️ 世界地圖 (遷移)"])
    
    # --- Tab 1: 據點營運 ---
    with tab1:
        st.markdown("#### 人力派駐管理 (每日產出)")
        max_human = st.session_state.human
        
        # 1. 幼兒園
        kg_count = st.session_state.buildings["幼兒園"]
        st.info(f"🏫 幼兒園 ({kg_count}間)：每日有 `{max_human}%` 的機率吸引或產出 1 名新生人力。")
        
        # 2. 農場
        farm_workers = st.slider("🌾 派駐農場 (每人產出 2 食物/日)", 0, max_human, min(10, max_human), key="farm")
        
        # 3. 彈藥工廠
        max_after_farm = max(0, max_human - farm_workers)
        ammo_workers = st.slider("🏭 派駐彈藥工廠 (每人消耗 1 材料 ➡️ 產出 2 彈藥)", 0, max_human, min(3, max_after_farm), key="ammo_fac")
        
        # 4. 藥學廠
        max_after_ammo = max(0, max_after_farm - ammo_workers)
        med_workers = st.slider("🧪 派駐藥學廠 (每人消耗 1 食物 ➡️ 產出 1 藥物)", 0, max_human, min(2, max_after_ammo), key="med_fac")
        
        # 5. 拆箱區
        max_after_med = max(0, max_after_ammo - med_workers)
        box_workers = st.slider("📦 派駐拆箱區 (每人消耗 1 資源箱 ➡️ 隨機二級物資)", 0, max_human, min(3, max_after_med), key="box_fac")
        
        total_assigned = farm_workers + ammo_workers + med_workers + box_workers
        unassigned = max_human - total_assigned
        
        # 動態防禦力計算
        total_defense = st.session_state.current_base["defense_bonus"] + unassigned
        
        if total_assigned > max_human:
            st.error(f"❌ 派駐人力超載！")
            btn_disabled = True
        else:
            st.success(f"✅ 留守/防禦人力：{unassigned} 人 (當前總防禦力: {total_defense})")
            btn_disabled = False

        # 中立人口招募按鈕
        if st.session_state.current_base["neutral_pop"] > 0:
            if st.button("🤝 招募 1 名中立人口 (消耗 10 食物)"):
                if st.session_state.food >= 10:
                    st.session_state.food -= 10
                    st.session_state.human += 1
                    st.session_state.current_base["neutral_pop"] -= 1
                    st.session_state.logs.insert(0, "🤝 你花費了 10 食物，成功招募了一名中立倖存者加入據點！")
                    st.rerun()
                else:
                    st.error("食物不足，無法招募！")

        if st.button("▶️ 結束本日，進入明天", disabled=btn_disabled, type="primary", use_container_width=True):
            new_logs = []
            new_logs.append(f"--- 【第 {st.session_state.day} 天 結算報告】 ---")
            
            # 生產
            if random.randint(1, 100) <= max_human * kg_count:
                st.session_state.human += 1
                new_logs.append("👶 幼兒園發揮作用，據點加入了 1 名新人口。")
                
            food_prod = farm_workers * 2
            st.session_state.food += food_prod
            if food_prod > 0: new_logs.append(f"🌾 農場採收了 {food_prod} 食物。")
            
            ammo_mats = ammo_workers * 1
            if st.session_state.materials >= ammo_mats:
                st.session_state.materials -= ammo_mats
                st.session_state.ammo += ammo_workers * 2
                if ammo_workers > 0: new_logs.append(f"🏭 工廠製造了 {ammo_workers * 2} 彈藥。")
            
            med_food = med_workers * 1
            if st.session_state.food >= med_food:
                st.session_state.food -= med_food
                st.session_state.meds += med_workers * 1
                if med_workers > 0: new_logs.append(f"🧪 藥廠提煉了 {med_workers * 1} 藥物。")
                
            # 拆箱
            actual_boxes = min(box_workers, st.session_state.current_base["boxes"])
            if actual_boxes > 0:
                st.session_state.current_base["boxes"] -= actual_boxes
                f, a, m, g, mat = 0, 0, 0, 0, 0
                for _ in range(actual_boxes):
                    f += random.randint(0, 2)
                    a += random.randint(0, 2)
                    m += random.randint(0, 1)
                    g += random.randint(0, 1)
                    mat += random.randint(1, 3)
                st.session_state.food += f
                st.session_state.ammo += a
                st.session_state.meds += m
                st.session_state.gas += g
                st.session_state.materials += mat
                new_logs.append(f"📦 拆開 {actual_boxes} 個資源箱：獲得 食物+{f}, 彈藥+{a}, 藥物+{m}, 汽油+{g}, 材料+{mat}。")
            elif box_workers > 0:
                new_logs.append("🚨 據點資源箱已空！")

            # 消耗 (食物)
            food_needed = st.session_state.human * 1
            if st.session_state.food >= food_needed:
                st.session_state.food -= food_needed
            else:
                starved = math.ceil((food_needed - st.session_state.food) / 2)
                st.session_state.food = 0
                st.session_state.human = max(0, st.session_state.human - starved)
                new_logs.append(f"💀 飢荒！{starved} 人餓死。")

            # 消耗 (生病)
            sick = sum(1 for _ in range(st.session_state.human) if random.random() < 0.02)
            if sick > 0:
                if st.session_state.meds >= sick:
                    st.session_state.meds -= sick
                    new_logs.append(f"🤢 {sick} 人生病，已用藥物治癒。")
                else:
                    dead = sick - st.session_state.meds
                    st.session_state.meds = 0
                    st.session_state.human = max(0, st.session_state.human - dead)
                    new_logs.append(f"💔 藥物不足！{dead} 人因病去世。")
                    
            # 喪屍襲擊 (機率10%)
            if random.random() < 0.10:
                z_str = random.randint(5, 20) + (st.session_state.day // 2)
                new_logs.append(f"⚠️ 喪屍來襲！強度: {z_str} (據點防禦: {total_defense})")
                if total_defense >= z_str:
                    new_logs.append("🛡️ 靠著堅固的防禦與留守人員，無傷擊退屍潮！")
                else:
                    breach = z_str - total_defense
                    if st.session_state.ammo >= breach:
                        st.session_state.ammo -= breach
                        new_logs.append(f"🔫 防禦被破，消耗 {breach} 彈藥消滅突入的喪屍。")
                    else:
                        st.session_state.ammo = 0
                        dmg = breach - st.session_state.ammo
                        dead = max(1, dmg // 3)
                        st.session_state.human = max(0, st.session_state.human - dead)
                        new_logs.append(f"💥 彈藥耗盡！喪屍屠殺了 {dead} 名倖存者！")

            st.session_state.day += 1
            st.session_state.logs = new_logs + st.session_state.logs
            st.rerun()

    # --- Tab 2: 世界地圖與遷移 ---
    with tab2:
        st.markdown("#### 🗺️ 探索與遷移")
        st.write("當前據點資源枯竭時，你可以帶領所有人遷移到新據點。")
        
        # 計算總物資重量 (決定汽油消耗)
        total_cargo = st.session_state.food + st.session_state.ammo + st.session_state.meds + st.session_state.materials
        st.info(f"車隊當前物資總量：**{total_cargo}** 單位")
        
        selected_dest_name = st.selectbox("選擇目標據點", [d["name"] for d in st.session_state.destinations])
        dest = next(d for d in st.session_state.destinations if d["name"] == selected_dest_name)
        
        st.markdown(f"**目標資訊**：距離 {dest['travel_days']} 天 | 建築欄 {dest['max_slots']} | 資源箱 {dest['boxes']} | 基礎防禦 {dest['defense_bonus']} | 中立人口 {dest['neutral_pop']}")
        
        # 計算消耗
        req_food = st.session_state.human * dest["travel_days"]
        req_gas = math.ceil(total_cargo / 100) * dest["travel_days"]
        
        col_c1, col_c2 = st.columns(2)
        col_c1.metric("🍞 遷移所需食物 (依人口與天數)", req_food, f"現有: {st.session_state.food}")
        col_c2.metric("⛽ 遷移所需汽油 (依物資與天數)", req_gas, f"現有: {st.session_state.gas}")
        
        can_migrate = st.session_state.food >= req_food and st.session_state.gas >= req_gas
        
        if not can_migrate:
            st.error("⚠️ 食物或汽油不足，無法進行遷移！")
        
        if st.button("🚚 開始遷移！", disabled=not can_migrate, type="primary"):
            st.session_state.food -= req_food
            st.session_state.gas -= req_gas
            st.session_state.day += dest["travel_days"]
            
            # 更新據點
            st.session_state.current_base = dest
            
            # 刷新地圖目的地
            st.session_state.destinations = generate_destinations()
            
            st.session_state.logs.insert(0, f"🚚 【大遷徙】車隊歷經 {dest['travel_days']} 天的跋涉，消耗了 {req_food} 食物與 {req_gas} 汽油，成功抵達新據點：{dest['name']}！")
            st.rerun()

# ----------------- 右側日誌區 -----------------
with main_col2:
    st.markdown("### 📜 據點事件與歷史日誌")
    
    if st.session_state.human <= 0:
        st.error("🚨 據點全員覆沒！請重設遊戲。")
        
    log_container = st.container(height=600)
    with log_container:
        for log in st.session_state.logs:
            if "❌" in log or "💀" in log or "⚠️" in log or "💥" in log or "🚨" in log:
                st.markdown(f"<span style='color:#e74c3c;'>{log}</span>", unsafe_allow_html=True)
            elif "✅" in log or "🌾" in log or "🧪" in log or "📦" in log or "🤝" in log or "🚚" in log:
                st.markdown(f"<span style='color:#2ecc71;'>{log}</span>", unsafe_allow_html=True)
            else:
                st.write(log)
