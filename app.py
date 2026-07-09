import streamlit as st
import random

# --- 1. 狀態初始化 (State Management) ---
def init_game():
    if 'phase' not in st.session_state:
        st.session_state.phase = 'DRAW' # 階段：DRAW, MAIN, THREAT, CAMP
    if 'hand' not in st.session_state:
        st.session_state.hand = []
    if 'grid' not in st.session_state:
        # 使用 (x, y) 座標模擬網格，儲存 Tile 狀態
        st.session_state.grid = {
            (0, 0): {'terrain': '生存營地', 'building': '無', 'zombies': 0}
        }
    if 'resources' not in st.session_state:
        st.session_state.resources = {'food': 0, 'materials': 0}
    if 'turn' not in st.session_state:
        st.session_state.turn = 1

init_game()

st.title("Card & Zombie - Streamlit Prototype")
st.sidebar.header(f"回合: {st.session_state.turn}")
st.sidebar.write("### 營地物資")
st.sidebar.write(f"🥫 食物: {st.session_state.resources['food']}")
st.sidebar.write(f"🪵 建材: {st.session_state.resources['materials']}")

# --- 2. 核心邏輯函數 ---
def draw_cards():
    # 模擬抽取 5 張卡 (各類型)
    st.session_state.hand = [
        {'type': 'Terrain', 'name': '平原'},
        {'type': 'Terrain', 'name': '河流'},
        {'type': 'Building', 'name': '公寓'},
        {'type': 'Action', 'name': '搜索公寓'},
        {'type': 'Zombie', 'name': '遊蕩屍群'}
    ]
    st.session_state.phase = 'MAIN'

def end_turn_check():
    # 檢查手上是否有殭屍卡
    has_zombie = any(card['type'] == 'Zombie' for card in st.session_state.hand)
    if has_zombie:
        st.session_state.phase = 'THREAT'
    else:
        st.session_state.phase = 'CAMP'

def next_turn():
    st.session_state.turn += 1
    st.session_state.phase = 'DRAW'
    # 這裡可以加入手牌上限棄牌邏輯

# --- 3. 介面與階段渲染 ---

# [地圖顯示區]
st.write("### 🗺️ 當前探索地圖")
map_data = []
for coords, tile in st.session_state.grid.items():
    map_data.append({
        "座標": f"({coords[0]}, {coords[1]})",
        "地形": tile['terrain'],
        "建築": tile['building'],
        "殭屍數量": tile['zombies']
    })
st.table(map_data)

st.divider()

# [階段控制器]
if st.session_state.phase == 'DRAW':
    st.write("### 抽牌階段")
    if st.button("抽取 5 張卡牌"):
        draw_cards()
        st.rerun()

elif st.session_state.phase == 'MAIN':
    st.write("### 行動階段 (打出地形、建築、行動卡)")
    
    # 顯示手牌
    card_names = [f"[{c['type']}] {c['name']}" for c in st.session_state.hand]
    selected_card = st.selectbox("選擇要打出的卡牌:", ["-- 選擇卡牌 --"] + card_names)
    
    # 簡易目標選擇 (選擇要放置的座標)
    target_x = st.number_input("目標 X 座標", value=1)
    target_y = st.number_input("目標 Y 座標", value=0)
    
    if st.button("打出卡牌"):
        if selected_card != "-- 選擇卡牌 --":
            # 這裡實作卡牌效果的 if/else (對應 Godot 中的 Validation Checker)
            card_index = card_names.index(selected_card)
            card = st.session_state.hand[card_index]
            coords = (target_x, target_y)
            
            if card['type'] == 'Terrain':
                if coords not in st.session_state.grid:
                    st.session_state.grid[coords] = {'terrain': card['name'], 'building': '無', 'zombies': 0}
                    st.session_state.hand.pop(card_index)
                else:
                    st.error("該座標已有地形！")
                    
            elif card['type'] == 'Building':
                if coords in st.session_state.grid and st.session_state.grid[coords]['terrain'] == '平原':
                    st.session_state.grid[coords]['building'] = card['name']
                    st.session_state.hand.pop(card_index)
                else:
                    st.error("建築必須放置在平原上！")
            
            elif card['type'] == 'Zombie':
                st.warning("請在『結束回合』時處理殭屍卡，或實作主動放置邏輯。")
                
            st.rerun()

    if st.button("結束探索 (進入結算)"):
        end_turn_check()
        st.rerun()

elif st.session_state.phase == 'THREAT':
    st.error("⚠️ 危機階段：你必須將手上的殭屍卡放置於已有的建築上才能返回營地！")
    
    # 找出地圖上所有建築的座標
    building_coords = [coords for coords, tile in st.session_state.grid.items() if tile['building'] != '無']
    
    if not building_coords:
        st.info("地圖上沒有建築，殭屍向荒野散去...(系統沒收殭屍卡)")
        if st.button("前往營地"):
            st.session_state.hand = [c for c in st.session_state.hand if c['type'] != 'Zombie']
            st.session_state.phase = 'CAMP'
            st.rerun()
    else:
        target_building = st.selectbox("選擇殭屍入侵的座標:", building_coords)
        if st.button("放置殭屍"):
            st.session_state.grid[target_building]['zombies'] += 1 # 使用明確的 1-5 級別整數控制災情
            # 移除手牌中的殭屍卡
            zombie_indices = [i for i, c in enumerate(st.session_state.hand) if c['type'] == 'Zombie']
            if zombie_indices:
                st.session_state.hand.pop(zombie_indices[0])
            
            end_turn_check() # 再次檢查是否還有殭屍
            st.rerun()

elif st.session_state.phase == 'CAMP':
    st.success("⛺ 歡迎回到生存營地")
    st.write("在這裡你可以消耗剛剛探索獲得的資源來升級或招募。")
    
    # 營地選項範例
    col1, col2 = st.columns(2)
    with col1:
        if st.button("消耗 1 食物：恢復體力"):
            if st.session_state.resources['food'] >= 1:
                st.session_state.resources['food'] -= 1
                st.toast("體力恢復！")
            else:
                st.error("食物不足！")
    
    with col2:
        if st.button("消耗 1 建材：加固營地"):
            if st.session_state.resources['materials'] >= 1:
                st.session_state.resources['materials'] -= 1
                st.toast("營地防禦上升！")
            else:
                st.error("建材不足！")
                
    st.divider()
    if st.button("結束營地運營，開始新回合"):
        next_turn()
        st.rerun()
