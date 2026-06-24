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
        "unspent_points": 0,  # 升級獲得的未分配點數
        "ap": 16,
        "max_ap": 16
    }
    st.session_state.inventory = {"食物": 10, "建材": 0, "藥物": 0, "器具": 0, "槍械": 0, "特殊": 0}
    st.session_state.followers = []
    st.session_state.logs = ["系統啟動：長官，歡迎來到末日指揮中心。"]

def gain_exp(amount):
    """處理經驗值獲取與升級邏輯"""
    st.session_state.player["exp"] += amount
    st.session_state.logs.insert(0, f"🌟 獲得 {amount} 點經驗值。")
    # 簡單升級公式：每 100 EXP 升一級
    if st.session_state.player["exp"] >= 100:
        st.session_state.player["level"] += 1
        st.session_state.player["exp"] -= 100
        st.session_state.player["unspent_points"] += 1
        # AP 上限隨著屬性點增加而提升
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

def calculate_loot(rolls, location_mods, player_stats, job):
    """處理擲骰與物資判定"""
    # 1. 基礎資源出現權重
    base_weights = {"食物": 30, "建材": 25, "藥物": 15, "器具": 15, "槍械": 10, "特殊": 5}
    
    # 2. 套用地點加成
    adjusted_weights = {k: v * location_mods.get(k, 1.0) for k, v in base_weights.items()}
    
    # 3. 套用職業與特殊技能加成 (Synergy)
    special_stat = player_stats["特殊技能"]
    if job == "警察":
        # 特殊技能1點 + 警察 = 槍械出現率額外 +10% (權重 * 1.1)
        adjusted_weights["槍械"] *= (1 + (special_stat * 0.1))
    elif job == "農夫":
        # 特殊技能 + 農夫 = 食物/建材 提升
        adjusted_weights["食物"] *= (1 + (special_stat * 0.1))
        adjusted_weights["建材"] *= (1 + (special_stat * 0.05))
    elif job == "高管":
        # 特殊技能 + 高管 = 容易找到特殊物品(高價值)
        adjusted_weights["特殊"] *= (1 + (special_stat * 0.15))

    # 4. 根據豐富度 (rolls) 進行 N 次判定
    loot_results = {"食物": 0, "建材": 0, "藥物": 0, "器具": 0, "槍械": 0, "特殊": 0}
    items = list(adjusted_weights.keys())
    weights = list(adjusted_weights.values())
    
    # 5% 機率什麼都沒找到 (可選機制)
    items.append("空")
    weights.append(sum(weights) * 0.05) 

    for _ in range(rolls):
        found = random.choices(items, weights=weights, k=1)[0]
        if found != "空":
            loot_results[found] += 1
            
    return loot_results

if 'phase' not in st.session_state:
    init_game()

# ==========================================
# 左側邊欄：角色狀態面板 (Day 1 以後顯示)
# ==========================================
if st.session_state.phase != "Day 0":
    with st.sidebar:
        st.header(f"👤 長官 ({st.session_state.player['job']})")
        st.subheader(f"Lv. {st.session_state.player['level']}")
        
        # 經驗值條
        st.progress(st.session_state.player["exp"] / 100, text=f"EXP: {st.session_state.player['exp']} / 100")
        
        # 行動點數 (AP)
        st.metric("⚡ 行動點數 (AP)", f"{st.session_state.player['ap']} / {st.session_state.player['max_ap']}")
        
        st.divider()
        st.markdown("### 📊 五維能力")
        
        # 屬性顯示與升級加點邏輯
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
# 第 0 天：創角與點數分配
# ==========================================
if st.session_state.phase == "Day 0":
    st.title("☢️ 末日指揮中心 - 第 0 天：危機爆發")
    st.markdown("病毒剛剛爆發，秩序正在瓦解。請先確認你的能力，並選擇你的據點。")
    
    st.subheader("🛠️ 分配初始能力值 (共 16 點)")
    
    # 創角暫存狀態
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
            st.session_state.phase = "Day 1"
            st.session_state.day = 1
            st.rerun()

        with col1:
            st.subheader("🚓 警察局")
            st.write("戰鬥主場。特殊技能聯動：提高槍械與彈藥尋獲率。")
            if st.button("成為警察"): confirm_start("警察")
                
        with col2:
            st.subheader("💼 辦公大樓")
            st.write("資源平均。特殊技能聯動：更容易找到高價值特殊物品。")
            if st.button("成為高管"): confirm_start("高管")
                
        with col3:
            st.subheader("🌾 農莊")
            st.write("後勤基地。特殊技能聯動：大幅提升食物與建材尋獲率。")
            if st.button("成為農夫"): confirm_start("農夫")

# ==========================================
# 第 1 天及以後：核心遊玩系統
# ==========================================
elif st.session_state.phase == "Day 1":
    st.title(f"☢️ 基地指揮中心 - 第 {st.session_state.day} 天")
    st.markdown(f"### 📍 當前位置：{st.session_state.location['name']} (防禦加成：{st.session_state.location['def_bonus']}/10)")
    
    # 頂部庫存
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("🍞 食物", st.session_state.inventory["食物"])
    c2.metric("🧱 建材", st.session_state.inventory["建材"])
    c3.metric("💊 藥物", st.session_state.inventory["藥物"])
    c4.metric("🛠️ 器具", st.session_state.inventory["器具"])
    c5.metric("🔫 槍械", st.session_state.inventory["槍械"])
    c6.metric("🌟 特殊", st.session_state.inventory["特殊"])
    
    st.divider()
    tab1, tab2 = st.tabs(["🗺️ 廢墟探索", "📜 系統日誌"])
    
    with tab1:
        st.subheader("區域資源點")
        st.write("行動力消耗公式：`20 / 偵查` (無條件捨去，最低為 1)")
        
        recon_stat = st.session_state.player["stats"]["偵查"]
        ap_cost = max(1, math.floor(20 / recon_stat))
        
        for i, node in enumerate(st.session_state.location["nodes"]):
            col_a, col_b = st.columns([3, 1])
            if not node["searched"]:
                col_a.write(f"📦 資源點 #{node['id']} - 預估豐富度：{node['richness']} (需耗費 **{ap_cost} AP**)")
                
                if col_b.button(f"🔍 消耗 {ap_cost} AP 搜索", key=f"search_{i}"):
                    if st.session_state.player["ap"] >= ap_cost:
                        # 扣除 AP
                        st.session_state.player["ap"] -= ap_cost
                        
                        # 進行擲骰結算
                        loot = calculate_loot(node["richness"], st.session_state.location["mods"], st.session_state.player["stats"], st.session_state.player["job"])
                        
                        # 加入庫存與紀錄
                        loot_msg = []
                        for item, qty in loot.items():
                            if qty > 0:
                                st.session_state.inventory[item] += qty
                                loot_msg.append(f"{item} x{qty}")
                        
                        if loot_msg:
                            log_text = f"在資源點 #{node['id']} 找到了：" + "、".join(loot_msg)
                        else:
                            log_text = f"在資源點 #{node['id']} 搜索了半天，什麼都沒找到..."
                            
                        st.session_state.logs.insert(0, log_text)
                        
                        # 標記為已搜索並給予經驗值
                        st.session_state.location["nodes"][i]["searched"] = True
                        gain_exp(15) # 每次搜索給 15 EXP
                        
                        st.rerun()
                    else:
                        st.error("⚠️ 行動點數 (AP) 不足！")
            else:
                col_a.write(f"🪹 資源點 #{node['id']} - 已被搜刮一空。")
                col_b.button("已搜索", disabled=True, key=f"searched_{i}")

    with tab2:
        for log in st.session_state.logs[:10]:
            st.text(log)
