import streamlit as st
import random
import math

# ==========================================
# 1. 初始化與核心系統 (Game State & Core Logic)
# ==========================================
def init_game():
    st.session_state.phase = "Day 0"
    st.session_state.day = 0
    
    # 玩家核心數據
    st.session_state.player = {
        "stats": {"偵查": 4, "戰鬥": 4, "生產": 4, "魅力": 4, "特殊技能": 0},
        "job": None,
        "level": 1,
        "exp": 0,
        "unspent_points": 0,
        "ap": 16,
        "max_ap": 16
    }
    st.session_state.inventory = {"食物": 10, "建材": 0, "藥物": 0, "器具": 0, "槍械": 0, "特殊": 0}
    st.session_state.followers = []
    st.session_state.npcs = []
    st.session_state.logs = ["系統啟動：長官，歡迎來到末日指揮中心。"]

def gain_exp(amount):
    """處理經驗值獲取與升級邏輯"""
    st.session_state.player["exp"] += amount
    st.session_state.logs.insert(0, f"🌟 獲得 {amount} 點經驗值。")
    if st.session_state.player["exp"] >= 100:
        st.session_state.player["level"] += 1
        st.session_state.player["exp"] -= 100
        st.session_state.player["unspent_points"] += 1
        st.session_state.player["max_ap"] += 1 
        st.toast("🆙 升級了！獲得 1 點可分配屬性點！")
        st.session_state.logs.insert(0, f"🆙 升級至 Lv.{st.session_state.player['level']}！")

def generate_location(job_type):
    """根據職業生成出生點與資源乘數"""
    locations = {
        "警察": {"name": "警察局", "def_bonus": 8, "zombies": "未知", "mods": {"食物": 1.0, "建材": 1.0, "藥物": 1.0, "器具": 1.0, "槍械": 1.5, "特殊": 1.2}},
        "高管": {"name": "辦公大樓", "def_bonus": 5, "zombies": "未知", "mods": {"食物": 1.2, "建材": 1.0, "藥物": 1.0, "器具": 1.1, "槍械": 0.9, "特殊": 1.0}},
        "農夫": {"name": "農莊", "def_bonus": 3, "zombies": "未知", "mods": {"食物": 1.5, "建材": 1.2, "藥物": 0.8, "器具": 1.0, "槍械": 0.5, "特殊": 1.0}}
    }
    loc = locations[job_type]
    loc["nodes"] = [{"id": i+1, "richness": random.randint(3, 10), "searched": False} for i in range(5)]
    return loc

def generate_npcs(count):
    """生成初始中立人口"""
    npcs = []
    names = ["阿傑", "老王", "小美", "陳大叔", "李姐", "建國", "志明", "春嬌"]
    items = ["食物", "藥物", "器具"]
    for i in range(count):
        npc = {
            "id": i,
            "name": f"倖存者 {random.choice(names)}_{i}",
            "stats": {"偵查": random.randint(1, 5), "戰鬥": random.randint(1, 5), "生產": random.randint(1, 5), "魅力": random.randint(1, 5)},
            "desired_item": random.choice(items),
            "friendship": 0,
            "probed": False,
            "recruited": False
        }
        npcs.append(npc)
    return npcs

def calculate_loot(rolls, location_mods, player_stats, job):
    """處理擲骰與物資判定"""
    base_weights = {"食物": 30, "建材": 25, "藥物": 15, "器具": 15, "槍械": 10, "特殊": 5}
    adjusted_weights = {k: v * location_mods.get(k, 1.0) for k, v in base_weights.items()}
    special_stat = player_stats["特殊技能"]
    
    if job == "警察":
        adjusted_weights["槍械"] *= (1 + (special_stat * 0.1))
    elif job == "農夫":
        adjusted_weights["食物"] *= (1 + (special_stat * 0.1))
        adjusted_weights["建材"] *= (1 + (special_stat * 0.05))
    elif job == "高管":
        adjusted_weights["特殊"] *= (1 + (special_stat * 0.15))

    loot_results = {"食物": 0, "建材": 0, "藥物": 0, "器具": 0, "槍械": 0, "特殊": 0}
    items = list(adjusted_weights.keys()) + ["空"]
    weights = list(adjusted_weights.values()) + [sum(adjusted_weights.values()) * 0.05]

    for _ in range(rolls):
        found = random.choices(items, weights=weights, k=1)[0]
        if found != "空":
            loot_results[found] += 1
    return loot_results

if 'phase' not in st.session_state:
    init_game()

# ==========================================
# 左側邊欄：角色狀態面板
# ==========================================
if st.session_state.phase != "Day 0":
    with st.sidebar:
        st.header(f"👤 長官 ({st.session_state.player['job']})")
        st.subheader(f"Lv. {st.session_state.player['level']}")
        st.progress(st.session_state.player["exp"] / 100, text=f"EXP: {st.session_state.player['exp']} / 100")
        st.metric("⚡ 行動點數 (AP)", f"{st.session_state.player['ap']} / {st.session_state.player['max_ap']}")
        
        st.divider()
        st.markdown("### 📊 五維能力")
        for stat, val in st.session_state.player["stats"].items():
            col_s1, col_s2 = st.columns([3, 1])
            col_s1.write(f"**{stat}**: {val}")
            if st.session_state.player["unspent_points"] > 0:
                if col_s2.button("➕", key=f"add_{stat}"):
                    st.session_state.player["stats"][stat] += 1
                    st.session_state.player["unspent_points"] -= 1
                    st.session_state.player["max_ap"] += 1
                    st.session_state.player["ap"] += 1
                    st.rerun()
                    
        if st.session_state.player["unspent_points"] > 0:
            st.info(f"✨ 尚有 {st.session_state.player['unspent_points']} 點屬性可分配")

# ==========================================
# 第 0 天：創角
# ==========================================
if st.session_state.phase == "Day 0":
    st.title("☢️ 末日指揮中心 - 第 0 天：危機爆發")
    st.subheader("🛠️ 分配初始能力值 (共 16 點)")
    
    if 'temp_stats' not in st.session_state:
        st.session_state.temp_stats = {"偵查": 4, "戰鬥": 4, "生產": 4, "魅力": 4, "特殊技能": 0}
        
    c1, c2, c3, c4, c5 = st.columns(5)
    st.session_state.temp_stats["偵查"] = c1.number_input("偵查", 1, 10, st.session_state.temp_stats["偵查"])
    st.session_state.temp_stats["戰鬥"] = c2.number_input("戰鬥", 1, 10, st.session_state.temp_stats["戰鬥"])
    st.session_state.temp_stats["生產"] = c3.number_input("生產", 1, 10, st.session_state.temp_stats["生產"])
    st.session_state.temp_stats["魅力"] = c4.number_input("魅力", 1, 10, st.session_state.temp_stats["魅力"])
    st.session_state.temp_stats["特殊技能"] = c5.number_input("特殊技能", 0, 10, st.session_state.temp_stats["特殊技能"])
    
    total_points = sum(st.session_state.temp_stats.values())
    
    if total_points > 16:
        st.error(f"⚠️ 點數超標！已使用：{total_points}/16 點。")
    elif total_points < 16:
        st.warning(f"⚠️ 還有未分配的點數！已使用：{total_points}/16 點。")
    else:
        st.success(f"✅ 點數分配完成 (16/16)。請選擇下方職業開始遊戲。")
        st.divider()
        col1, col2, col3 = st.columns(3)
        
        def confirm_start(job):
            st.session_state.player["stats"] = st.session_state.temp_stats.copy()
            st.session_state.player["job"] = job
            st.session_state.player["max_ap"] = total_points
            st.session_state.player["ap"] = total_points
            st.session_state.location = generate_location(job)
            st.session_state.npcs = generate_npcs(20) # 生成 20 名中立人口
            st.session_state.phase = "Day 1"
            st.session_state.day = 1
            st.rerun()

        with col1:
            st.subheader("🚓 警察局")
            if st.button("成為警察"): confirm_start("警察")
        with col2:
            st.subheader("💼 辦公大樓")
            if st.button("成為高管"): confirm_start("高管")
        with col3:
            st.subheader("🌾 農莊")
            if st.button("成為農夫"): confirm_start("農夫")

# ==========================================
# 第 1 天及以後：核心遊玩系統
# ==========================================
elif st.session_state.phase == "Day 1":
    st.title(f"☢️ 基地指揮中心 - 第 {st.session_state.day} 天")
    st.markdown(f"### 📍 當前位置：{st.session_state.location['name']} (防禦加成：{st.session_state.location['def_bonus']}/10)")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🍞 食物", st.session_state.inventory["食物"])
    c2.metric("🧱 建材", st.session_state.inventory["建材"])
    c3.metric("💊 藥物", st.session_state.inventory["藥物"])
    c4.metric("🛠️ 器具", st.session_state.inventory["器具"])
    c5.metric("🔫 槍械", st.session_state.inventory["槍械"])
    c6.metric("🌟 特殊", st.session_state.inventory["特殊"])
    
    st.divider()
    # 恢復為四個頁籤
    tab1, tab2, tab3, tab4 = st.tabs(["🗺️ 廢墟探索", "🤝 中立人口", "📋 黨羽管理", "📜 系統日誌"])
    
    # --- 頁籤 1: 廢墟探索 ---
    with tab1:
        st.subheader("區域資源點")
        recon_stat = st.session_state.player["stats"]["偵查"]
        ap_cost = max(1, math.floor(20 / recon_stat))
        
        for i, node in enumerate(st.session_state.location["nodes"]):
            col_a, col_b = st.columns([3, 1])
            if not node["searched"]:
                col_a.write(f"📦 資源點 #{node['id']} - 預估豐富度：{node['richness']} (需耗費 **{ap_cost} AP**)")
                if col_b.button(f"🔍 消耗 {ap_cost} AP 搜索", key=f"search_{i}"):
                    if st.session_state.player["ap"] >= ap_cost:
                        st.session_state.player["ap"] -= ap_cost
                        loot = calculate_loot(node["richness"], st.session_state.location["mods"], st.session_state.player["stats"], st.session_state.player["job"])
                        
                        loot_msg = [f"{item} x{qty}" for item, qty in loot.items() if qty > 0]
                        for item, qty in loot.items():
                            if qty > 0: st.session_state.inventory[item] += qty
                        
                        log_text = f"在資源點 #{node['id']} 找到了：" + "、".join(loot_msg) if loot_msg else f"在資源點 #{node['id']} 什麼都沒找到..."
                        st.session_state.logs.insert(0, log_text)
                        st.session_state.location["nodes"][i]["searched"] = True
                        gain_exp(15)
                        st.rerun()
                    else:
                        st.error("⚠️ 行動點數 (AP) 不足！")
            else:
                col_a.write(f"🪹 資源點 #{node['id']} - 已被搜刮一空。")
                col_b.button("已搜索", disabled=True, key=f"searched_{i}")

    # --- 頁籤 2: 中立人口互動 ---
    with tab2:
        st.subheader(f"本地中立倖存者 (共 {len([n for n in st.session_state.npcs if not n['recruited']])} 人)")
        
        # 互動的 AP 消耗設計 (可根據平衡度調整)
        probe_ap = 1 
        chat_ap = 1
        
        for i, npc in enumerate(st.session_state.npcs):
            if npc["recruited"]: continue
                
            with st.expander(f"👤 {npc['name']} (友善度: {npc['friendship']})"):
                if not npc["probed"]:
                    st.write("數值與需求：未知")
                    if st.button(f"👁️ 探虛實 (消耗 {probe_ap} AP)", key=f"probe_{i}"):
                        if st.session_state.player["ap"] >= probe_ap:
                            st.session_state.player["ap"] -= probe_ap
                            st.session_state.npcs[i]["probed"] = True
                            gain_exp(5) # 探聽情報也能獲得微量經驗
                            st.rerun()
                        else:
                            st.error("⚠️ 行動點數 (AP) 不足！")
                else:
                    st.write(f"**五維能力**：偵查 {npc['stats']['偵查']} | 戰鬥 {npc['stats']['戰鬥']} | 生產 {npc['stats']['生產']} | 魅力 {npc['stats']['魅力']}")
                    st.write(f"**期望物資**：{npc['desired_item']}")
                    
                    col_x, col_y = st.columns(2)
                    with col_x:
                        if st.button(f"💬 閒聊與送禮 (消耗 {chat_ap} AP)", key=f"gift_{i}"):
                            if st.session_state.player["ap"] >= chat_ap:
                                st.session_state.player["ap"] -= chat_ap
                                # 若有期望物資則扣除並大幅加好感
                                if st.session_state.inventory.get(npc['desired_item'], 0) > 0:
                                    st.session_state.inventory[npc['desired_item']] -= 1
                                    # 魅力值影響送禮與聊天的額外加成
                                    bonus = math.floor(st.session_state.player["stats"]["魅力"] / 2)
                                    st.session_state.npcs[i]["friendship"] += (20 + bonus)
                                    st.toast(f"送禮成功！{npc['name']} 非常開心！")
                                else:
                                    bonus = math.floor(st.session_state.player["stats"]["魅力"] / 3)
                                    st.session_state.npcs[i]["friendship"] += (5 + bonus)
                                    st.toast("透過閒聊，友善度微幅提升。")
                                gain_exp(5)
                                st.rerun()
                            else:
                                st.error("⚠️ 行動點數 (AP) 不足！")
                    
                    with col_y:
                        if npc["friendship"] >= 20:
                            if st.button("🤝 招募進入團隊", key=f"recruit_{i}", type="primary"):
                                st.session_state.npcs[i]["recruited"] = True
                                st.session_state.followers.append(npc)
                                st.session_state.logs.insert(0, f"🎉 成功招募 {npc['name']} 加入陣營！")
                                gain_exp(30) # 招募成功獲得大量經驗
                                st.rerun()
                        else:
                            st.button("🤝 招募 (友善度不足 20)", key=f"recruit_disabled_{i}", disabled=True)

    # --- 頁籤 3: 黨羽管理 ---
    with tab3:
        st.subheader("你的黨羽名單")
        if not st.session_state.followers:
            st.info("目前還沒有人追隨你。去「中立人口」頁籤招募一些夥伴吧！")
        else:
            for f in st.session_state.followers:
                st.write(f"**{f['name']}**")
                st.caption(f"能力：偵查 {f['stats']['偵查']} | 戰鬥 {f['stats']['戰鬥']} | 生產 {f['stats']['生產']} | 魅力 {f['stats']['魅力']}")
                # 這裡保留任務指派的下拉選單，為後續的回合結算做準備
                st.selectbox(
                    "指派明日任務", 
                    ["無", "協助搜索資源", "修築防禦工事", "據點守衛"], 
                    key=f"task_{f['id']}"
                )
                st.divider()

    # --- 頁籤 4: 系統日誌 ---
    with tab4:
        for log in st.session_state.logs[:15]:
            st.text(log)
