import streamlit as st
import math
import random

# 設定網頁標題與圖示
st.set_page_config(page_title="喪屍末日據點經營模擬器 V5", page_icon="🧟", layout="wide")

# 建築物基礎資料表 (刪除幼兒園)
BUILDING_DATA = {
    "伐木場": {"cost": 20, "days": 2, "desc": "產生材料 (Lv*5 派駐上限，每人產 2 材料)"},
    "農場": {"cost": 20, "days": 2, "desc": "產生食物 (Lv*5 派駐上限，每人產 2 食物)"},
    "探索區": {"cost": 15, "days": 1, "desc": "消耗資源箱換取隨機物資 (Lv*3 派駐上限)"},
    "藥學廠": {"cost": 25, "days": 3, "desc": "食物轉換為藥物 (Lv*2 派駐上限)"},
    "雷達站": {"cost": 35, "days": 3, "desc": "主動招募：派駐有機率尋獲中立人口，是唯一增加人口的手段 (Lv*2 派駐上限)"},
    "住宅區": {"cost": 30, "days": 3, "desc": "被動效果：每級增加 20 點人口容量上限"},
    "防禦設施": {"cost": 25, "days": 2, "desc": "被動效果：每級增加 10 點據點防禦值"}
}

def get_adjacent_destinations(current_id):
    layer = current_id // 4
    local_idx = current_id % 4
    
    destinations = []
    for i in range(4):
        if i != local_idx:
            destinations.append(layer * 4 + i)
            
    if local_idx == 3:
        destinations.append((layer + 1) * 4 + 0)
        
    if local_idx == 0 and layer > 0:
        destinations.append((layer - 1) * 4 + 3)
        
    output = []
    base_names = ["物資轉運站", "廢棄市鎮區", "封鎖軍事線", "未知核心樞紐"]
    for d_id in destinations:
        d_layer = d_id // 4
        d_idx = d_id % 4
        
        random.seed(d_id + 2026) 
        max_slots = random.randint(4, 7) + d_layer * 2
        boxes = random.randint(30, 60) + d_layer * 15
        def_bonus = random.randint(2, 8) + d_layer * 5
        neutral = random.randint(1, 5) + d_layer
        random.seed() 
        
        name = f"區域 {d_id} - {base_names[d_idx]} (等級: {d_layer}等)"
        output.append({
            "id": d_id,
            "name": name,
            "layer": d_layer,
            "travel_days": random.randint(2, 4) + d_layer,
            "max_slots": max_slots,
            "boxes": boxes,
            "defense_bonus": def_bonus,
            "neutral_pop": neutral
        })
    return output

if 'game_started' not in st.session_state:
    st.session_state.game_started = True
    st.session_state.day = 1
    
    st.session_state.global_ammo = 50           
    st.session_state.global_meds = 20           
    st.session_state.global_gas = 40            
    st.session_state.global_materials = 150  
    st.session_state.global_food = 200
    
    st.session_state.owned_bases = {
        0: {
            "name": "區域 0 - 市郊避難所 (0等)",
            "layer": 0,
            "human": 15,
            "max_slots": 3,
            "boxes": 30,
            "defense_bonus": 5,
            "neutral_pop": 3,
            "zombie_threat": 5,
            "slots": [{"type": None, "level": 0, "status": "empty", "days_left": 0} for _ in range(3)]
        }
    }
    
    st.session_state.current_view_id = 0
    st.session_state.logs = ["【系統】遊戲開始！目前全人類龜縮在【區域 0】。雷達站是唯一獲取人口的管道！"]

st.title("🧟 喪屍末日據點經營模擬器 V5")

if st.sidebar.button("🔄 重設遊戲狀態"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

st.sidebar.markdown(f"## 📅 存活時間：第 **{st.session_state.day}** 天")
st.sidebar.markdown("---")

owned_options = {bid: f"{bdata['name']} [人口: {bdata['human']}]" for bid, bdata in st.session_state.owned_bases.items()}
selected_view_id = st.sidebar.selectbox("切換當前視角", list(owned_options.keys()), format_func=lambda x: owned_options[x])
st.session_state.current_view_id = selected_view_id

c_id = st.session_state.current_view_id
base = st.session_state.owned_bases[c_id]

active_slots = [s for s in base["slots"] if s["status"] == "active"]
residential_cap = sum(s["level"] * 20 for s in active_slots if s["type"] == "住宅區")
defense_bld_bonus = sum(s["level"] * 10 for s in active_slots if s["type"] == "防禦設施")
radar_lv = sum(s["level"] for s in active_slots if s["type"] == "雷達站")
max_population_cap = 20 + residential_cap

# 計算正在施工占用的總人力
builders_needed = sum(1 for s in base["slots"] if s["status"] in ["building", "upgrading"])
actual_builders = min(base["human"], builders_needed)
assignable_human = max(0, base["human"] - actual_builders)

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 生存與遷移規則")
st.sidebar.write("- **施工占用**：每個正在建造或升級的建築，會暫時佔用 **1 名人力**。")
st.sidebar.write("- **物資盲盒**：每個資源箱開啟後，必定隨機開出 **3 個單位** 的隨機資源。")
st.sidebar.write("- **防禦機制**：防線被突破時會優先消耗彈藥抵擋；若無彈藥，則會損失人口。")

st.markdown("### 📦 全局物資總庫存")
col_r1, col_r2, col_r3, col_r4, col_r5 = st.columns(5)
col_r1.metric("🍞 總食物", st.session_state.global_food)
col_r2.metric("🪵 總材料", st.session_state.global_materials)
col_r3.metric("💥 總彈藥", st.session_state.global_ammo)
col_r4.metric("💊 總藥物", st.session_state.global_meds)
col_r5.metric("⛽ 總汽油", st.session_state.global_gas)

st.markdown(f"### 🏕️ 當前選定據點現況：**{base['name']}**")
col_b1, col_b2, col_b3, col_b4, col_b5 = st.columns(5)
pop_color = "normal" if base["human"] <= max_population_cap else "inverse"
col_b1.metric("👥 據點人口 / 容量", f"{base['human']} / {max_population_cap}", delta="超載" if base["human"] > max_population_cap else "", delta_color=pop_color)
col_b2.metric("🧟 周圍喪屍威脅", base["zombie_threat"])
col_b3.metric("🛡️ 總防禦加成", base["defense_bonus"] + defense_bld_bonus)
col_b4.metric("📦 剩餘資源箱", base["boxes"])
col_b5.metric("🤝 可招募中立人口", base["neutral_pop"])

st.markdown("---")

main_col1, main_col2 = st.columns([3, 2])

with main_col1:
    tab1, tab2, tab3 = st.tabs(["🛠️ 派駐與生產", "🏗️ 建設與升級", "🗺️ 地圖跳板與遷移"])
    
    with tab1:
        st.markdown(f"#### 【{base['name']}】每日派駐管理")
        
        if builders_needed > 0:
            st.info(f"👷 當前據點有工程正在進行，已暫時指派 {actual_builders} 名人力投入施工 (無法參與生產與防禦)。")
            
        lumber_lv = sum(s["level"] for s in active_slots if s["type"] == "伐木場")
        farm_lv = sum(s["level"] for s in active_slots if s["type"] == "農場")
        med_lv = sum(s["level"] for s in active_slots if s["type"] == "藥學廠")
        explore_lv = sum(s["level"] for s in active_slots if s["type"] == "探索區")
        
        if base["human"] == 0:
            st.warning("⚠️ 這個據點目前沒有常駐人口！")
            btn_disabled = True
            lumber_workers, farm_workers, med_workers, explore_workers, radar_workers = 0, 0, 0, 0, 0
            unassigned = 0
            total_defense = base["defense_bonus"] + defense_bld_bonus
        else:
            btn_disabled = False
            lumber_workers = st.slider(f"🪓 伐木場 (上限 {lumber_lv*5} 人)", 0, lumber_lv*5, 0) if lumber_lv > 0 else 0
            farm_workers = st.slider(f"🌾 農場 (上限 {farm_lv*5} 人)", 0, farm_lv*5, 0) if farm_lv > 0 else 0
            med_workers = st.slider(f"🧪 藥學廠 (上限 {med_lv*2} 人)", 0, med_lv*2, 0) if med_lv > 0 else 0
            explore_workers = st.slider(f"📦 探索區 (上限 {explore_lv*3} 人)", 0, explore_lv*3, 0) if explore_lv > 0 else 0
            radar_workers = st.slider(f"📡 雷達站 (上限 {radar_lv*2} 人 | 每人 15% 機率尋獲人口)", 0, radar_lv*2, 0) if radar_lv > 0 else 0
            
            total_assigned = lumber_workers + farm_workers + med_workers + explore_workers + radar_workers
            unassigned = assignable_human - total_assigned
            total_defense = base["defense_bonus"] + defense_bld_bonus + unassigned
            
            if total_assigned > assignable_human:
                st.error(f"❌ 派駐人力超載！目前剩餘可用人力僅有 {assignable_human} 人。")
                btn_disabled = True
            else:
                st.success(f"✅ 閒置防禦人力：{unassigned} 人 (本據點防禦力: {total_defense})")

        st.markdown("---")
        
        if st.button("▶️ 全局時間前進至明天", disabled=btn_disabled, type="primary", use_container_width=True):
            new_logs = []
            new_logs.append(f"--- 【第 {st.session_state.day} 天 全局結算報告】 ---")
            
            for b_id, b_data in list(st.session_state.owned_bases.items()):
                b_active = [s for s in b_data["slots"] if s["status"] == "active"]
                b_def_bonus = b_data["defense_bonus"] + sum(s["level"] * 10 for s in b_active if s["type"] == "防禦設施")
                b_max_pop = 20 + sum(s["level"] * 20 for s in b_active if s["type"] == "住宅區")
                
                b_build_req = sum(1 for s in b_data["slots"] if s["status"] in ["building", "upgrading"])
                b_build_act = min(b_data["human"], b_build_req)
                
                if b_build_req > 0 and b_data["human"] < b_build_req:
                    new_logs.append(f"⚠️ [{b_data['name']}] 施工人力不足，部分工程暫停！")
                
                progressed = 0
                for slot in b_data["slots"]:
                    if slot["status"] in ["building", "upgrading"] and progressed < b_build_act:
                        slot["days_left"] -= 1
                        progressed += 1
                        if slot["days_left"] <= 0:
                            slot["level"] += 1
                            slot["status"] = "active"
                            new_logs.append(f"🏗️ [{b_data['name']}] 建築完工！【{slot['type']}】升至 Lv.{slot['level']}，已釋放 1 名占用人力。")
                
                if b_data["human"] <= 0:
                    b_data["zombie_threat"] += random.randint(1, 3)
                    continue
                
                if b_id == st.session_state.current_view_id:
                    if lumber_workers > 0:
                        st.session_state.global_materials += lumber_workers * 2
                        new_logs.append(f"🪓 [{b_data['name']}] 伐木場產出 {lumber_workers * 2} 材料。")
                    if farm_workers > 0:
                        st.session_state.global_food += farm_workers * 2
                        new_logs.append(f"🌾 [{b_data['name']}] 農場產出 {farm_workers * 2} 食物。")
                    if med_workers > 0:
                        if st.session_state.global_food >= med_workers:
                            st.session_state.global_food -= med_workers
                            st.session_state.global_meds += med_workers
                            new_logs.append(f"🧪 [{b_data['name']}] 藥廠提煉了 {med_workers} 藥物。")
                    if explore_workers > 0:
                        act_box = min(explore_workers, b_data["boxes"])
                        if act_box > 0:
                            b_data["boxes"] -= act_box
                            f, a, m, g, mat = 0, 0, 0, 0, 0
                            res_pool = ["f", "a", "m", "g", "mat"]
                            for _ in range(act_box):
                                for _ in range(3): # 每箱精準抽3個
                                    roll = random.choice(res_pool)
                                    if roll == "f": f += 1
                                    elif roll == "a": a += 1
                                    elif roll == "m": m += 1
                                    elif roll == "g": g += 1
                                    elif roll == "mat": mat += 1
                            
                            st.session_state.global_food += f
                            st.session_state.global_ammo += a
                            st.session_state.global_meds += m
                            st.session_state.global_gas += g
                            st.session_state.global_materials += mat
                            new_logs.append(f"📦 [{b_data['name']}] 探索區拆解 {act_box} 箱，共獲得 {act_box*3} 單位物資 (食+{f} 彈+{a} 藥+{m} 油+{g} 材+{mat})。")
                    if radar_workers > 0:
                        success_recruits = 0
                        for _ in range(radar_workers):
                            if random.random() < 0.15 and b_data["neutral_pop"] > 0:
                                success_recruits += 1
                                b_data["neutral_pop"] -= 1
                                b_data["human"] += 1
                        if success_recruits > 0:
                            new_logs.append(f"📡 [{b_data['name']}] 雷達站成功引導 {success_recruits} 名中立人口加入！")
                
                h_count = b_data["human"]
                if st.session_state.global_food >= h_count:
                    st.session_state.global_food -= h_count
                else:
                    starved = math.ceil((h_count - st.session_state.global_food) / 2)
                    st.session_state.global_food = 0
                    b_data["human"] = max(0, b_data["human"] - starved)
                    new_logs.append(f"💀 [{b_data['name']}] 糧倉空虛！爆發大飢荒，{starved} 人餓死。")

                s_rate = 0.02 if b_data["human"] <= b_max_pop else 0.15
                sick = sum(1 for _ in range(b_data["human"]) if random.random() < s_rate)
                if sick > 0:
                    if st.session_state.global_meds >= sick:
                        st.session_state.global_meds -= sick
                    else:
                        dead = sick - st.session_state.global_meds
                        st.session_state.global_meds = 0
                        b_data["human"] = max(0, b_data["human"] - dead)
                        new_logs.append(f"💔 [{b_data['name']}] 藥物見底！{dead} 人不幸病逝。")

                b_data["zombie_threat"] += random.randint(2, 6) + b_data["layer"] * 3
                if b_id == st.session_state.current_view_id:
                    b_idle = max(0, b_data["human"] - b_build_act - total_assigned)
                else:
                    b_idle = max(0, b_data["human"] - b_build_act)
                    
                b_defense = b_def_bonus + b_idle
                
                if random.randint(1, 100) <= min(b_data["zombie_threat"], 75):
                    z_power = b_data["zombie_threat"]
                    new_logs.append(f"⚠️ [{b_data['name']}] 遭到屍潮襲擊！(屍潮: {z_power} vs 防禦: {b_defense})")
                    if b_defense >= z_power:
                        b_data["zombie_threat"] = 0
                        new_logs.append(f"🛡️ [{b_data['name']}] 守軍依靠防禦工事全殲屍潮！")
                    else:
                        breach = z_power - b_defense
                        if st.session_state.global_ammo >= breach:
                            st.session_state.global_ammo -= breach
                            b_data["zombie_threat"] = 0
                            new_logs.append(f"🔫 [{b_data['name']}] 防線被破！消耗 {breach} 單位彈藥成功擊斃突入的喪屍。")
                        else:
                            dmg = breach - st.session_state.global_ammo
                            new_logs.append(f"💥 [{b_data['name']}] 防線被破！耗盡最後的 {st.session_state.global_ammo} 彈藥後，剩餘喪屍展開屠殺...")
                            st.session_state.global_ammo = 0
                            dead = max(1, dmg // 3)
                            b_data["human"] = max(0, b_data["human"] - dead)
                            b_data["zombie_threat"] = max(0, z_power - b_defense - 5)
                            new_logs.append(f"🩸 [{b_data['name']}] {dead} 名倖存者慘遭喪屍咬死！")

            st.session_state.day += 1
            st.session_state.logs = new_logs + st.session_state.logs
            st.rerun()

    with tab2:
        st.markdown(f"#### 🏗️ 【{base['name']}】建築配置槽 ({len(base['slots'])} 格)")
        
        for i, slot in enumerate(base["slots"]):
            with st.container():
                st.write(f"**槽位 {i+1}**")
                if slot["status"] == "empty":
                    b_type = st.selectbox("選擇建造項目", list(BUILDING_DATA.keys()), key=f"sel_{c_id}_{i}", label_visibility="collapsed")
                    cost = BUILDING_DATA[b_type]["cost"]
                    days = BUILDING_DATA[b_type]["days"]
                    st.caption(BUILDING_DATA[b_type]["desc"])
                    
                    can_build = True
                    if assignable_human < 1:
                        st.warning("⚠️ 沒有多餘的可用人力來進行施工！(請從生產線上調離人力)")
                        can_build = False
                    
                    if st.button(f"🔨 建造 {b_type} (需 {cost} 材料, {days} 天, 占 1 人力)", key=f"bld_{c_id}_{i}", disabled=not can_build):
                        if st.session_state.global_materials >= cost:
                            st.session_state.global_materials -= cost
                            base["slots"][i] = {"type": b_type, "level": 0, "status": "building", "days_left": days}
                            st.session_state.logs.insert(0, f"🔨 在 [{base['name']}] 消耗 {cost} 材料開始建造【{b_type}】。")
                            st.rerun()
                        else:
                            st.error("全球物資庫存的材料不足！")
                
                elif slot["status"] in ["building", "upgrading"]:
                    st.info(f"🚧 【{slot['type']}】施工中... 剩餘 {slot['days_left']} 天 (占用 1 人力)")
                
                elif slot["status"] == "active":
                    cost = BUILDING_DATA[slot["type"]]["cost"] * (slot["level"] + 1)
                    days = BUILDING_DATA[slot["type"]]["days"]
                    st.success(f"🏢 **Lv.{slot['level']} {slot['type']}**")
                    
                    can_upgrade = True
                    if assignable_human < 1:
                        st.warning("⚠️ 沒有多餘的可用人力來進行升級！")
                        can_upgrade = False
                        
                    if st.button(f"⬆️ 升級至 Lv.{slot['level']+1} (需 {cost} 材料, {days} 天, 占 1 人力)", key=f"upg_{c_id}_{i}", disabled=not can_upgrade):
                        if st.session_state.global_materials >= cost:
                            st.session_state.global_materials -= cost
                            slot["status"] = "upgrading"
                            slot["days_left"] = days
                            st.session_state.logs.insert(0, f"⬆️ 在 [{base['name']}] 消耗 {cost} 材料升級【{slot['type']}】。")
                            st.rerun()
                        else:
                            st.error("材料不足！")
            st.divider()

    with tab3:
        st.markdown("#### 🗺️ 遠征車隊調配系統")
        st.write(f"從當前選定的 **[{base['name']}]** 組建車隊，出發前往相鄰區塊。")
        
        adj_dests = get_adjacent_destinations(c_id)
        dest_names = [d["name"] for d in adj_dests]
        
        selected_dest_name = st.selectbox("選擇目的地區塊", dest_names)
        dest = next(d for d in adj_dests if d["name"] == selected_dest_name)
        
        st.markdown(f"**📊 目標情報摘要**：")
        st.write(f"- 估計行軍天數：`{dest['travel_days']} 天` | 建築空位槽：`{dest['max_slots']} 格`")
        st.write(f"- 預估剩餘資源箱：`{dest['boxes']} 箱` | 中立人口基數：`{dest['neutral_pop']} 人`")
        
        st.markdown("##### 📦 精確配置搬遷載重（自全局總量中提撥）")
        
        move_human = st.number_input("🚚 隨行車隊人口數量", min_value=0, max_value=base["human"], value=min(5, base["human"]))
        move_mats = st.number_input("🪵 搬運材料數量", min_value=0, max_value=st.session_state.global_materials, value=0)
        
        req_gas = math.ceil((move_human / 2) + (move_mats / 5))
        req_food = move_human * dest["travel_days"]
        
        st.markdown("##### ⛽ 搬遷物資消耗預估")
        col_c1, col_c2 = st.columns(2)
        col_c1.metric("⛽ 消耗汽油 (公式: 人/2 + 材/5)", req_gas, f"總庫存: {st.session_state.global_gas}")
        col_c2.metric("🍞 消耗食物 (公式: 人 * 天數)", req_food, f"總庫存: {st.session_state.global_food}")
        
        can_migrate = True
        if move_human <= 0:
            st.error("⚠️ 車隊必須至少包含 1 名人口帶路！")
            can_migrate = False
        elif st.session_state.global_gas < req_gas:
            st.error("⚠️ 汽油不足以供給此重量的車隊！")
            can_migrate = False
        elif st.session_state.global_food < req_food:
            st.error("⚠️ 食物不足以供給旅途消耗！")
            can_migrate = False
            
        if st.button("🚚 發動遠征／出發遷移！", disabled=not can_migrate, type="primary"):
            st.session_state.global_gas -= req_gas
            st.session_state.global_food -= req_food
            base["human"] -= move_human
            st.session_state.day += dest["travel_days"]
            
            target_id = dest["id"]
            if target_id not in st.session_state.owned_bases:
                st.session_state.owned_bases[target_id] = {
                    "name": dest["name"],
                    "layer": dest["layer"],
                    "human": move_human,
                    "max_slots": dest["max_slots"],
                    "boxes": dest["boxes"],
                    "defense_bonus": dest["defense_bonus"],
                    "neutral_pop": dest["neutral_pop"],
                    "zombie_threat": dest["layer"] * 10, 
                    "slots": [{"type": None, "level": 0, "status": "empty", "days_left": 0} for _ in range(dest["max_slots"])]
                }
                st.session_state.logs.insert(0, f"🚚 【開拓新領土】車隊歷時 {dest['travel_days']} 天，抵達未知的 {dest['name']}！在此建立新據點分支。")
            else:
                st.session_state.owned_bases[target_id]["human"] += move_human
                st.session_state.logs.insert(0, f"🚚 【物資增援】車隊歷時 {dest['travel_days']} 天，成功折返回既有據點 [{st.session_state.owned_bases[target_id]['name']}] 並注入人口！")
            
            st.session_state.current_view_id = target_id
            st.rerun()

with main_col2:
    st.markdown("### 📜 帝國日誌與隨機事件")
    
    total_living_human = sum(b["human"] for b in st.session_state.owned_bases.values())
    if total_living_human <= 0:
        st.error("🚨 所有據點的倖存者都已覆滅，人類的火種完全熄滅了... 遊戲結束。")
        
    log_container = st.container(height=650)
    with log_container:
        for log in st.session_state.logs:
            if "❌" in log or "💀" in log or "⚠️" in log or "💥" in log or "🚨" in log or "💔" in log or "🩸" in log:
                st.markdown(f"<span style='color:#e74c3c;'>{log}</span>", unsafe_allow_html=True)
            elif "✅" in log or "🌾" in log or "🧪" in log or "📦" in log or "🤝" in log or "🚚" in log or "🏗️" in log or "📡" in log or "🔫" in log:
                st.markdown(f"<span style='color:#2ecc71;'>{log}</span>", unsafe_allow_html=True)
            else:
                st.write(log)
