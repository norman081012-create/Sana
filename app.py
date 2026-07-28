"""
喪屍末日卡牌生存原型 (Card Survival 機制驗證版)
------------------------------------------------
玩法:
1. 左側是你的「卡牌庫存」(資源卡 + 倖存者卡)
2. 勾選兩張卡嘗試合成 -> 若配方存在則消耗輸入、產出新卡
3. 也可以把資源卡「投入」防禦/巡邏等行動卡來準備夜晚
4. 按「結束白天」推進到夜晚結算,殭屍潮會依你的防禦值造成傷害

這是機制demo,美術/拖拉手感之後在Godot做,這裡先驗證數值與合成規則。
"""

import streamlit as st
import uuid
from dataclasses import dataclass, field

st.set_page_config(page_title="喪屍卡牌生存 Demo", page_icon="🧟", layout="wide")

# ---------------------------------------------------------------------------
# 資料定義
# ---------------------------------------------------------------------------

@dataclass
class CardDef:
    id: str
    name: str
    emoji: str
    kind: str  # "resource" | "action" | "survivor"
    desc: str = ""


CARD_DEFS = {
    # 基礎資源
    "scrap":   CardDef("scrap", "廢鐵", "🔩", "resource", "隨處可撿,建造與武器的基礎材料"),
    "wood":    CardDef("wood", "木材", "🪵", "resource", "拆家具或砍樹取得"),
    "cloth":   CardDef("cloth", "布料", "🧵", "resource", "做繃帶或燃燒瓶引信"),
    "fuel":    CardDef("fuel", "汽油", "⛽", "resource", "車輛與燃燒瓶原料,稀有"),
    "herb":    CardDef("herb", "藥草", "🌿", "resource", "野外採集,製藥用"),
    "can":     CardDef("can", "罐頭食物", "🥫", "resource", "存糧,回合結算時消耗"),
    "water":   CardDef("water", "淨水", "💧", "resource", "存糧,回合結算時消耗"),
    # 合成產物
    "melee":   CardDef("melee", "簡易武器", "🔨", "resource", "廢鐵+木材,提升巡邏效率"),
    "bandage": CardDef("bandage", "繃帶", "🩹", "resource", "布料+藥草,治療受傷倖存者"),
    "molotov": CardDef("molotov", "燃燒瓶", "🧨", "resource", "汽油+布料,強力防禦道具"),
    "medkit":  CardDef("medkit", "醫療包", "💉", "resource", "繃帶+藥草進階合成"),
    # 倖存者(特殊資源,可投入行動卡)
    "survivor":CardDef("survivor", "倖存者", "🧑", "survivor", "你的隊員,可指派去巡邏/防禦"),
    # 行動卡
    "patrol":  CardDef("patrol", "巡邏", "🔦", "action", "投入倖存者+簡易武器,白天有機率帶回資源"),
    "defend":  CardDef("defend", "防禦工事", "🛡️", "action", "投入廢鐵/木材/燃燒瓶,提升夜晚防禦值"),
}

# 合成配方: frozenset(輸入卡id, 可重複用list表示) -> 輸出
# 這裡用簡單 tuple(sorted) 當 key,數量都預設為1
RECIPES = {
    tuple(sorted(["scrap", "wood"])): ("melee", "廢鐵+木材 → 簡易武器"),
    tuple(sorted(["cloth", "herb"])): ("bandage", "布料+藥草 → 繃帶"),
    tuple(sorted(["fuel", "cloth"])): ("molotov", "汽油+布料 → 燃燒瓶"),
    tuple(sorted(["bandage", "herb"])): ("medkit", "繃帶+藥草 → 醫療包"),
}

STARTER_INVENTORY = ["scrap", "scrap", "wood", "wood", "cloth", "herb",
                      "can", "can", "can", "water", "water", "survivor", "survivor"]


# ---------------------------------------------------------------------------
# 狀態初始化
# ---------------------------------------------------------------------------

def new_card(def_id: str):
    return {"uid": str(uuid.uuid4())[:8], "def_id": def_id}


def init_state():
    if "inventory" not in st.session_state:
        st.session_state.inventory = [new_card(d) for d in STARTER_INVENTORY]
    if "day" not in st.session_state:
        st.session_state.day = 1
    if "log" not in st.session_state:
        st.session_state.log = ["🌅 第 1 天開始。你在廢棄超市附近醒來。"]
    if "defense_pool" not in st.session_state:
        st.session_state.defense_pool = 0  # 已投入防禦的資源換算成的防禦值
    if "assigned_to_defend" not in st.session_state:
        st.session_state.assigned_to_defend = []  # uid list
    if "assigned_to_patrol" not in st.session_state:
        st.session_state.assigned_to_patrol = []
    if "survivors_alive" not in st.session_state:
        st.session_state.survivors_alive = 2
    if "game_over" not in st.session_state:
        st.session_state.game_over = False


init_state()


def log(msg):
    st.session_state.log.insert(0, msg)


def inv_defs():
    """回傳庫存卡片(附上定義)"""
    return [(c, CARD_DEFS[c["def_id"]]) for c in st.session_state.inventory]


def remove_by_uid(uid):
    st.session_state.inventory = [c for c in st.session_state.inventory if c["uid"] != uid]


def add_card(def_id):
    st.session_state.inventory.append(new_card(def_id))


# ---------------------------------------------------------------------------
# 版面
# ---------------------------------------------------------------------------

st.title("🧟 喪屍末日卡牌生存 — 機制 Demo")
st.caption("Streamlit 原型,驗證「拖拉合成 + 資源投入行動」的數值手感,之後移植到 Godot。")

if st.session_state.game_over:
    st.error("💀 據點失守。所有倖存者陣亡。")
    if st.button("重新開始"):
        for k in ["inventory", "day", "log", "defense_pool", "assigned_to_defend",
                  "assigned_to_patrol", "survivors_alive", "game_over"]:
            del st.session_state[k]
        st.rerun()
    st.stop()

top_l, top_r = st.columns([3, 1])
with top_l:
    st.subheader(f"☀️ 第 {st.session_state.day} 天 — 白天階段")
with top_r:
    st.metric("倖存者", st.session_state.survivors_alive)

col_inv, col_action, col_log = st.columns([2, 2, 1.3])

# --- 左欄: 庫存 + 合成 -------------------------------------------------
with col_inv:
    st.markdown("### 🎒 卡牌庫存")
    cards = inv_defs()
    if not cards:
        st.info("庫存空了。")
    else:
        options = {f"{d.emoji} {d.name} ({c['uid']})": c["uid"] for c, d in cards}
        picked_labels = st.multiselect(
            "勾選 2 張卡嘗試合成",
            options=list(options.keys()),
            max_selections=2,
        )
        picked_uids = [options[l] for l in picked_labels]

        if len(picked_uids) == 2:
            def_ids = sorted(
                next(c for c in st.session_state.inventory if c["uid"] == u)["def_id"]
                for u in picked_uids
            )
            key = tuple(def_ids)
            if key in RECIPES:
                out_id, desc = RECIPES[key]
                st.success(f"✅ 可合成: {desc}")
                if st.button("執行合成 🔨", type="primary"):
                    for u in picked_uids:
                        remove_by_uid(u)
                    add_card(out_id)
                    log(f"🔨 合成成功: {desc}")
                    st.rerun()
            else:
                st.warning("這兩張卡沒有已知配方。")

        st.divider()
        st.markdown("**目前持有:**")
        # 依 def_id 分組顯示數量,體驗更接近卡牌堆疊
        from collections import Counter
        counter = Counter(c["def_id"] for c in st.session_state.inventory)
        grid_cols = st.columns(4)
        for i, (def_id, qty) in enumerate(counter.items()):
            d = CARD_DEFS[def_id]
            with grid_cols[i % 4]:
                st.markdown(f"**{d.emoji} {d.name}**  \nx{qty}")

# --- 中欄: 行動卡(投入資源) --------------------------------------------
with col_action:
    st.markdown("### ⚔️ 行動卡")

    st.markdown("**🛡️ 防禦工事**")
    st.caption("投入 廢鐵/木材/燃燒瓶,提升今晚防禦值。燃燒瓶效果最好。")
    defend_options = {
        f"{CARD_DEFS[c['def_id']].emoji} {CARD_DEFS[c['def_id']].name} ({c['uid']})": c
        for c in st.session_state.inventory
        if c["def_id"] in ("scrap", "wood", "molotov")
    }
    chosen_defend = st.multiselect("選擇要投入防禦的卡", list(defend_options.keys()), key="defend_pick")
    if st.button("投入防禦 🛡️"):
        gain = 0
        for label in chosen_defend:
            c = defend_options[label]
            gain += {"scrap": 2, "wood": 1, "molotov": 5}[c["def_id"]]
            remove_by_uid(c["uid"])
        st.session_state.defense_pool += gain
        if gain:
            log(f"🛡️ 投入防禦工事,防禦值 +{gain} (目前 {st.session_state.defense_pool})")
        st.rerun()

    st.info(f"目前防禦值: **{st.session_state.defense_pool}**")

    st.divider()
    st.markdown("**🔦 巡邏派遣**")
    st.caption("派倖存者出去巡邏,有機率帶回資源,但可能受傷或死亡。")
    can_patrol = st.session_state.survivors_alive > 0
    has_melee = any(c["def_id"] == "melee" for c in st.session_state.inventory)
    if st.button("派遣巡邏 🔦", disabled=not can_patrol):
        import random
        risk = 0.25 if has_melee else 0.45
        if has_melee:
            # 消耗一把簡易武器
            uid = next(c["uid"] for c in st.session_state.inventory if c["def_id"] == "melee")
            remove_by_uid(uid)
        roll = random.random()
        if roll < risk:
            st.session_state.survivors_alive -= 1
            log("💀 巡邏隊遭遇喪屍群,一名倖存者失蹤...")
        else:
            loot = random.choice(["scrap", "wood", "cloth", "fuel", "herb", "can", "water"])
            add_card(loot)
            log(f"🔦 巡邏平安歸來,帶回 {CARD_DEFS[loot].emoji}{CARD_DEFS[loot].name}")
        st.rerun()

# --- 右欄: 日誌 ---------------------------------------------------------
with col_log:
    st.markdown("### 📜 事件日誌")
    for entry in st.session_state.log[:12]:
        st.write(entry)

st.divider()

# --- 結束白天 / 夜晚結算 -------------------------------------------------
bottom = st.columns([1, 1, 2])
with bottom[0]:
    if st.button("🌙 結束白天,進入夜晚結算", type="primary", use_container_width=True):
        import random

        # 1. 消耗糧食
        food = [c for c in st.session_state.inventory if c["def_id"] == "can"]
        water = [c for c in st.session_state.inventory if c["def_id"] == "water"]
        if food:
            remove_by_uid(food[0]["uid"])
        else:
            st.session_state.survivors_alive = max(0, st.session_state.survivors_alive - 1)
            log("🍽️ 沒有食物了!一名倖存者因飢餓虛弱倒下。")
        if water:
            remove_by_uid(water[0]["uid"])
        else:
            st.session_state.survivors_alive = max(0, st.session_state.survivors_alive - 1)
            log("💧 沒有淨水了!一名倖存者因脫水倒下。")

        # 2. 殭屍潮強度隨天數上升
        wave_strength = 3 + st.session_state.day * 2 + random.randint(-2, 3)
        defense = st.session_state.defense_pool
        st.session_state.defense_pool = 0  # 防禦值只沿用一晚

        if defense >= wave_strength:
            log(f"🌙 第{st.session_state.day}晚: 殭屍潮強度{wave_strength} vs 防禦{defense} → 完美防守!")
        else:
            dmg_ratio = (wave_strength - defense) / max(wave_strength, 1)
            losses = 1 if dmg_ratio > 0.3 else 0
            if random.random() < dmg_ratio:
                losses += 1
            st.session_state.survivors_alive = max(0, st.session_state.survivors_alive - losses)
            log(f"🌙 第{st.session_state.day}晚: 殭屍潮強度{wave_strength} vs 防禦{defense} → 據點受損,損失 {losses} 名倖存者")

        st.session_state.day += 1

        if st.session_state.survivors_alive <= 0:
            st.session_state.game_over = True
        else:
            log(f"🌅 第 {st.session_state.day} 天開始。")
        st.rerun()

with bottom[1]:
    st.caption("提示: 先合成燃燒瓶再投入防禦,比單純堆廢鐵有效率很多。")

with bottom[2]:
    st.caption("這版本用 multiselect 模擬「拖拉合成」,Godot版會換成實際拖拉手勢,規則邏輯完全相同。")
