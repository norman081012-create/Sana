import streamlit as st
import random

# ==========================================
# 1. 初始化遊戲狀態與資料結構
# ==========================================
def init_game():
    st.session_state.phase = "Day 0"  # 遊戲階段：Day 0 (創角) -> Day 1 (遊玩)
    st.session_state.day = 0
    
    # 玩家五維與資源
    st.session_state.player = {"偵查": 0, "戰鬥": 0, "生產": 0, "魅力": 0, "特殊技能": []}
    st.session_state.inventory = {"食物": 10, "建材": 0, "藥物": 0, "器具": 0, "槍械": 0, "特殊": 0}
    
    # 黨羽名單
    st.session_state.followers = []

def generate_location(job_type):
    """根據職業生成出生點與資源池"""
    locations = {
        "警察": {"name": "警察局", "def_bonus": 8, "zombies": "未知", "mods": {"食物": 1.0, "槍械": 1.5}},
        "高管": {"name": "辦公大樓", "def_bonus": 5, "zombies": "未知", "mods": {"食物": 1.2, "器具": 1.1, "槍械": 0.9}},
        "農夫": {"name": "農莊", "def_bonus": 3, "zombies": "未知", "mods": {"食物": 1.5, "建材": 1.2, "槍械": 0.5}}
    }
    loc = locations[job_type]
    # 生成搜索點 (豐富度 1~10)
    loc["nodes"] = [{"id": i+1, "richness": random.randint(3, 10)} for i in range(5)]
    return loc

def generate_npcs(count):
    """生成初始中立人口"""
    npcs = []
    names = ["阿傑", "老王", "小美", "陳大叔", "李姐"]
    items = ["食物", "藥物", "器具"]
    for i in range(count):
        npc = {
            "id": i,
            "name": f"倖存者 {random.choice(names)}_{i}",
            "stats": {"偵查": random.randint(1, 5), "戰鬥": random.randint(1, 5), "生產": random.randint(1, 5), "魅力": random.randint(1, 5)},
            "desired_item": random.choice(items),
            "friendship": 0,
            "probed": False,  # 是否已被探虛實
            "recruited": False
        }
        npcs.append(npc)
    return npcs

if 'phase' not in st.session_state:
    init_game()

# ==========================================
# 2. 第 0 天：創角系統
# ==========================================
if st.session_state.phase == "Day 0":
    st.title("☢️ 末日指揮中心 - 第 0 天：危機爆發")
    st.markdown("病毒剛剛爆發，秩序正在瓦解。你目前在哪裡？")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🚓 警察 (警察局)")
        st.write("戰鬥 +1 \n\n 特殊技能: 槍械精通 (攻擊+1, 彈藥搜尋機率+10%)")
        if st.button("選擇警察"):
            st.session_state.player["戰鬥"] += 1
            st.session_state.player["特殊技能"].append("槍械精通")
            st.session_state.location = generate_location("警察")
            st.session_state.npcs = generate_npcs(20)
            st.session_state.phase = "Day 1"
            st.session_state.day = 1
            st.rerun()
            
    with col2:
        st.subheader("💼 高管 (辦公大樓)")
        st.write("魅力 +1 \n\n 特殊技能: 商業談判 (貿易價值+10%)")
        if st.button("選擇高管"):
            st.session_state.player["魅力"] += 1
            st.session_state.player["特殊技能"].append("商業談判")
            st.session_state.location = generate_location("高管")
            st.session_state.npcs = generate_npcs(20)
            st.session_state.phase = "Day 1"
            st.session_state.day = 1
            st.rerun()
            
    with col3:
        st.subheader("🌾 農夫 (農莊)")
        st.write("生產 +1 \n\n 特殊技能: 生存專家 (資源搜尋+10%, 近戰攻擊+2)")
        if st.button("選擇農夫"):
            st.session_state.player["生產"] += 1
            st.session_state.player["特殊技能"].append("生存專家")
            st.session_state.location = generate_location("農夫")
            st.session_state.npcs = generate_npcs(20)
            st.session_state.phase = "Day 1"
            st.session_state.day = 1
            st.rerun()

# ==========================================
# 3. 第 1 天及以後：核心遊玩系統
# ==========================================
elif st.session_state.phase == "Day 1":
    st.title(f"☢️ 末日指揮中心 - 第 {st.session_state.day} 天")
    
    st.markdown(f"### 📍 當前位置：{st.session_state.location['name']} (防禦加成：{st.session_state.location['def_bonus']}/10)")
    
    # 資源儀表板
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🍞 食物", st.session_state.inventory["食物"])
    c2.metric("🧱 建材", st.session_state.inventory["建材"])
    c3.metric("💊 藥物", st.session_state.inventory["藥物"])
    c4.metric("👥 你的黨羽", len(st.session_state.followers))
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["🗺️ 地點探索", "🤝 中立人口與招募", "📋 黨羽管理"])
    
    with tab1:
        st.subheader("可探索資源點")
        st.write(f"遊蕩殭屍數量：**{st.session_state.location['zombies']}** (需指派偵查)")
        for node in st.session_state.location["nodes"]:
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"資源點 #{node['id']} - 預估豐富度：{node['richness']}")
            col_b.button("探索 (開發中)", key=f"explore_{node['id']}")
            
    with tab2:
        st.subheader(f"中立人口列表 (共 {len([n for n in st.session_state.npcs if not n['recruited']])} 人)")
        
        for i, npc in enumerate(st.session_state.npcs):
            if npc["recruited"]:
                continue # 已招募的就不顯示在這裡
                
            with st.expander(f"👤 {npc['name']} (友善度: {npc['friendship']})"):
                if not npc["probed"]:
                    st.write("數值與需求：未知")
                    if st.button("👁️ 探虛實 (使用魅力)", key=f"probe_{i}"):
                        # 這裡可以加入魅力檢定機制，目前直接成功
                        st.session_state.npcs[i]["probed"] = True
                        st.rerun()
                else:
                    st.write(f"**五維能力**：偵查 {npc['stats']['偵查']} | 戰鬥 {npc['stats']['戰鬥']} | 生產 {npc['stats']['生產']} | 魅力 {npc['stats']['魅力']}")
                    st.write(f"**期望物資**：{npc['desired_item']}")
                    
                    col_x, col_y = st.columns(2)
                    with col_x:
                        if st.button("🎁 送禮交朋友", key=f"gift_{i}"):
                            # 簡化邏輯：如果有對應物資則扣除並增加大量好感，否則增加少量
                            if st.session_state.inventory.get(npc['desired_item'], 0) > 0:
                                st.session_state.inventory[npc['desired_item']] -= 1
                                st.session_state.npcs[i]["friendship"] += 20
                                st.toast(f"送禮成功！{npc['name']} 友善度大幅提升！")
                            else:
                                st.session_state.npcs[i]["friendship"] += 5
                                st.toast("單純用魅力交談，友善度微幅提升。")
                            st.rerun()
                    
                    with col_y:
                        if npc["friendship"] >= 20:
                            if st.button("🤝 招募", key=f"recruit_{i}", type="primary"):
                                st.session_state.npcs[i]["recruited"] = True
                                st.session_state.followers.append(npc)
                                st.toast(f"成功招募 {npc['name']}！")
                                st.rerun()
                        else:
                            st.button("🤝 招募 (友善度不足)", key=f"recruit_disabled_{i}", disabled=True)

    with tab3:
        st.subheader("你的黨羽")
        if not st.session_state.followers:
            st.write("目前還沒有人追隨你。")
        else:
            for f in st.session_state.followers:
                st.write(f"- **{f['name']}** (偵查:{f['stats']['偵查']} 戰鬥:{f['stats']['戰鬥']} 生產:{f['stats']['生產']})")
                st.selectbox("指派任務", ["無", "偵查殭屍數量", "搜索資源點", "修築防禦"], key=f"task_{f['id']}")
