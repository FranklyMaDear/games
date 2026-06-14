from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import random
import uuid
from datetime import datetime, date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gamified_hub")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Secrets ----------
API_KEY = os.environ.get("API_KEY", "m0n3t4g_s3cur3_k3y_2026")

USERS_FILE = "users.json"
POINTS_LOG_FILE = "points_log.json"
SHOP_FILE = "shop.json"

# ---------- ΣΤΑΘΕΡΕΣ ----------
POINTS_PER_LEVEL = 1000

# Daily Missions
DAILY_MISSIONS = [
    {"id": "d1", "day": 1, "description": "Play 1 match of Chess", "target": 1, "game": "Chess", "reward_type": "points", "reward_value": 20, "reward_label": "+20 Points", "link": "https://t.me/Franklygames_bot/chess"},
    {"id": "d2", "day": 2, "description": "Solve 1 Sudoku Puzzle", "target": 1, "game": "Sudoku", "reward_type": "stars", "reward_value": 10, "reward_label": "+10 Stars", "link": "https://t.me/Franklygames_bot/sudoku"},
    {"id": "d3", "day": 3, "description": "Play 1 match of Connect 4", "target": 1, "game": "Connect 4", "reward_type": "free_spin", "reward_value": 2, "reward_label": "+2 Free Spins", "link": "https://t.me/Franklygames_bot/connectfour"},
    {"id": "d4", "day": 4, "description": "Check your Daily Omen", "target": 1, "game": "Omen", "reward_type": "stars", "reward_value": 15, "reward_label": "+15 Stars", "link": "https://t.me/omenread_bot/omen"},
    {"id": "d5", "day": 5, "description": "Play 1 match of Balloons", "target": 1, "game": "Balloons", "reward_type": "points", "reward_value": 30, "reward_label": "+30 Points", "link": "https://t.me/Franklygames_bot/balloons"},
    {"id": "d6", "day": 6, "description": "Play Codewords once", "target": 1, "game": "Codewords", "reward_type": "free_spin", "reward_value": 3, "reward_label": "+3 Free Spins", "link": "https://t.me/crackthecodes_bot/codewords"},
    {"id": "d7", "day": 7, "description": "Visit LifeLine (Palmistry)", "target": 1, "game": "LifeLine", "reward_type": "stars", "reward_value": 20, "reward_label": "+20 Stars", "link": "https://t.me/lifeline2026_bot/games"},
    {"id": "d8", "day": 8, "description": "Play 2 matches of Connect 4", "target": 2, "game": "Connect 4", "reward_type": "points", "reward_value": 50, "reward_label": "+50 Points", "link": "https://t.me/Franklygames_bot/connectfour"},
    {"id": "d9", "day": 9, "description": "Win 2 matches of Chess", "target": 2, "game": "Chess", "reward_type": "free_spin", "reward_value": 5, "reward_label": "+5 Free Spins", "link": "https://t.me/Franklygames_bot/chess"},
    {"id": "d10", "day": 10, "description": "Complete 1 Chess, 1 Sudoku, 1 Connect 4", "target": 3, "game": "Multi", "reward_type": "points", "reward_value": 100, "reward_label": "+100 Points", "link": "https://t.me/Franklygames_bot/chess"},
]

# Weekly Missions
WEEKLY_MISSIONS = [
    {"id": "w1", "description": "Play 7 matches of Chess this week", "target": 7, "game": "Chess", "reward_type": "points", "reward_value": 150, "reward_label": "+150 Points"},
    {"id": "w2", "description": "Complete 5 grids of Sudoku this week", "target": 5, "game": "Sudoku", "reward_type": "stars", "reward_value": 100, "reward_label": "+100 Stars"},
    {"id": "w3", "description": "Win 8 matches of Connect 4 this week", "target": 8, "game": "Connect 4", "reward_type": "free_spin", "reward_value": 10, "reward_label": "+10 Free Spins"},
    {"id": "w4", "description": "Complete 3 Chess, 3 Sudoku, 3 Connect 4", "target": 9, "game": "Multi", "reward_type": "points", "reward_value": 300, "reward_label": "+300 Points"},
]

WHEEL_SEGMENTS = [
    {"type": "points", "value": 5, "mode": "double"},
    {"type": "points", "value": 10, "mode": "double"},
    {"type": "free_spin", "value": 1, "mode": "double"},
    {"type": "zonk", "value": 0, "mode": "none"},
    {"type": "stars", "value": 5, "mode": "mandatory_ad"},
    {"type": "stars", "value": 10, "mode": "mandatory_ad"},
    {"type": "free_spin", "value": 2, "mode": "double"},
    {"type": "zonk", "value": 0, "mode": "none"},
    {"type": "points", "value": 5, "mode": "double"},
    {"type": "points", "value": 10, "mode": "double"},
    {"type": "free_spin", "value": 1, "mode": "double"},
    {"type": "free_spin", "value": 2, "mode": "double"},
]

DEFAULT_SHOP = {
    "hats": [
        {"id": "hat_01", "name": "Magic Hat", "icon": "🎩", "price": 50, "slot": "hat"},
        {"id": "hat_02", "name": "Cool Sunglasses", "icon": "😎", "price": 30, "slot": "glasses"},
        {"id": "hat_03", "name": "Crown", "icon": "👑", "price": 100, "slot": "hat"},
    ],
    "outfits": [
        {"id": "outfit_01", "name": "Superhero Cape", "icon": "🦸", "price": 80, "slot": "outfit"},
        {"id": "outfit_02", "name": "Rainbow Shirt", "icon": "👕", "price": 40, "slot": "outfit"},
        {"id": "outfit_03", "name": "Princess Dress", "icon": "👗", "price": 90, "slot": "outfit"},
    ],
    "skins": [
        {"id": "skin_01", "name": "Golden Retriever", "icon": "🐕", "price": 200, "slot": "skin"},
        {"id": "skin_02", "name": "Tabby Cat", "icon": "🐈", "price": 150, "slot": "skin"},
        {"id": "skin_03", "name": "Bunny", "icon": "🐰", "price": 120, "slot": "skin"},
    ],
    "backgrounds": [
        {"id": "bg_01", "name": "Beach", "icon": "🏖️", "price": 60, "slot": "background"},
        {"id": "bg_02", "name": "Space", "icon": "🌌", "price": 70, "slot": "background"},
        {"id": "bg_03", "name": "Castle", "icon": "🏰", "price": 80, "slot": "background"},
    ],
}

AVATAR_ITEMS_POOL = [
    {"id": "avatar_01", "name": "Wizard Robe", "icon": "🧙", "price": 0, "slot": "outfit"},
    {"id": "avatar_02", "name": "Pirate Eye Patch", "icon": "🦜", "price": 0, "slot": "glasses"},
    {"id": "avatar_03", "name": "Angel Wings", "icon": "👼", "price": 0, "slot": "outfit"},
    {"id": "avatar_04", "name": "Detective Hat", "icon": "🕵️", "price": 0, "slot": "hat"},
    {"id": "avatar_05", "name": "Flower Crown", "icon": "🌺", "price": 0, "slot": "hat"},
    {"id": "avatar_06", "name": "Bow Tie", "icon": "🎀", "price": 0, "slot": "outfit"},
]


# ---------- JSON helpers ----------
def read_json(filename):
    if not os.path.exists(filename):
        if filename == SHOP_FILE:
            write_json(SHOP_FILE, DEFAULT_SHOP)
            return DEFAULT_SHOP
        return {} if filename == USERS_FILE else []
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except:
        return {} if filename == USERS_FILE else []


def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)


def get_user(user_id: str) -> dict:
    users = read_json(USERS_FILE)
    if user_id not in users:
        display_name = user_id
        if user_id.startswith("tg_"):
            display_name = "TG_" + user_id[3:11]
        else:
            display_name = user_id[:12]
        users[user_id] = {
            "total_points": 0,
            "stars": 0,
            "level": 1,
            "xp": 0,
            "display_name": display_name,
            "streak": 0,
            "last_login_date": None,
            "daily_missions": {},
            "weekly_missions": {},
            "last_daily_reset": None,
            "last_weekly_reset": None,
            "ad_watch_count": 0,
            "free_spins": 5,
            "inventory": [],
            "equipped": {},
            "pet_skin": "🐱",
            "pet_name": "Whiskers",
            "background": None,
            "happiness": 50,
            "food_items": 2,
            "double_active": False,
        }
    u = users[user_id]
    today = date.today().isoformat()
    week_start = (date.today() - timedelta(days=date.today().weekday())).isoformat()

    if u.get("last_daily_reset") != today:
        u["daily_missions"] = {m["id"]: {"progress": 0, "claimed": False} for m in DAILY_MISSIONS}
        u["last_daily_reset"] = today
    if u.get("last_weekly_reset") != week_start:
        u["weekly_missions"] = {m["id"]: {"progress": 0, "claimed": False} for m in WEEKLY_MISSIONS}
        u["last_weekly_reset"] = week_start

    u["level"] = max(1, (u.get("total_points", 0) // POINTS_PER_LEVEL) + 1)

    defaults = {
        "daily_missions": {}, "weekly_missions": {}, "free_spins": 5,
        "stars": 0, "happiness": 50, "food_items": 2, "xp": 0,
        "inventory": [], "equipped": {}, "double_active": False,
        "pet_skin": "🐱", "pet_name": "Whiskers", "background": None,
        "display_name": u.get("display_name", user_id[:12])
    }
    for field, default in defaults.items():
        if field not in u:
            u[field] = default

    users[user_id] = u
    write_json(USERS_FILE, users)
    return u


def save_user(user_id: str, data: dict):
    users = read_json(USERS_FILE)
    users[user_id] = data
    write_json(USERS_FILE, users)


def check_auth(request: Request):
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")


def get_item_by_id(item_id: str):
    shop = read_json(SHOP_FILE)
    for cat in shop.values():
        for item in cat:
            if item["id"] == item_id:
                return item
    for item in AVATAR_ITEMS_POOL:
        if item["id"] == item_id:
            return item
    return None


def get_equipped_items(user_data: dict) -> dict:
    equipped = {}
    all_items = []
    shop = read_json(SHOP_FILE)
    for cat in shop.values():
        all_items.extend(cat)
    all_items.extend(AVATAR_ITEMS_POOL)
    for slot, item_id in user_data.get("equipped", {}).items():
        item = next((it for it in all_items if it["id"] == item_id), None)
        if item:
            equipped[slot] = item
    return equipped


# =========================== ENDPOINTS ===========================

@app.get("/board")
async def get_board(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    return {
        "total_points": u["total_points"],
        "stars": u.get("stars", 0),
        "level": u["level"],
        "free_spins": u.get("free_spins", 0),
        "next_level_points": u["level"] * POINTS_PER_LEVEL,
        "happiness": u.get("happiness", 50),
        "double_active": u.get("double_active", False),
    }


@app.get("/missions")
async def get_missions(request: Request, userId: str, type: str = "daily"):
    check_auth(request)
    u = get_user(userId)
    missions_list = DAILY_MISSIONS if type == "daily" else WEEKLY_MISSIONS
    key = "daily_missions" if type == "daily" else "weekly_missions"
    result = []
    for m in missions_list:
        md = u.get(key, {}).get(m["id"], {"progress": 0, "claimed": False})
        completed = md.get("progress", 0) >= m["target"]
        result.append({
            "id": m["id"], "day": m.get("day", 0), "description": m["description"],
            "target": m["target"], "reward_type": m["reward_type"], "reward_value": m["reward_value"],
            "reward_label": m["reward_label"], "link": m.get("link", ""),
            "progress": md.get("progress", 0), "claimed": md.get("claimed", False), "completed": completed,
        })
    return {"missions": result}


@app.post("/missions/update")
async def update_mission_progress(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "")
    win = data.get("win", False)        # ΝΕΟ
    played = data.get("played", False)  # ΝΕΟ
    score = data.get("score", 0)
    
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    
    u = get_user(user_id)
    
    for mlist, key in [(DAILY_MISSIONS, "daily_missions"), (WEEKLY_MISSIONS, "weekly_missions")]:
        for m in mlist:
            mid = m["id"]
            if mid not in u[key]:
                u[key][mid] = {"progress": 0, "claimed": False}
            
            # Έλεγξε αν το mission αφορά αυτό το παιχνίδι
            if m["game"] == game or m["game"] == "Multi":
                # Αν θέλει νίκη (π.χ. "Win 8 matches")
                if "win" in m["description"].lower() and win:
                    u[key][mid]["progress"] = min(m["target"], u[key][mid].get("progress", 0) + 1)
                # Αν θέλει απλά να παίξει (π.χ. "Play 7 matches")
                elif "play" in m["description"].lower() and played:
                    u[key][mid]["progress"] = min(m["target"], u[key][mid].get("progress", 0) + 1)
                # Αν θέλει σκορ (π.χ. "Score 500 points")
                elif "score" in m["description"].lower() and score > 0:
                    u[key][mid]["progress"] = min(m["target"], u[key][mid].get("progress", 0) + score)
    
    save_user(user_id, u)
    return {"status": "ok"}


@app.post("/missions/claim")
async def claim_mission(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    mission_id = data.get("missionId")
    mtype = data.get("type", "daily")
    if not user_id or not mission_id:
        raise HTTPException(status_code=400, detail="Missing params")
    u = get_user(user_id)
    key = "daily_missions" if mtype == "daily" else "weekly_missions"
    missions_list = DAILY_MISSIONS if mtype == "daily" else WEEKLY_MISSIONS
    if mission_id not in u.get(key, {}):
        raise HTTPException(status_code=404, detail="Mission not found")
    md = u[key][mission_id]
    mdef = next((m for m in missions_list if m["id"] == mission_id), None)
    if not mdef or md.get("progress", 0) < mdef["target"] or md.get("claimed"):
        raise HTTPException(status_code=400, detail="Not completable")
    md["claimed"] = True
    save_user(user_id, u)
    return {"status": "ok"}


@app.post("/wheel/spin")
async def wheel_spin(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    u = get_user(user_id)
    if u.get("free_spins", 0) < 1:
        raise HTTPException(status_code=403, detail="Not enough free spins")
    u["free_spins"] -= 1
    prize_index = random.randint(0, len(WHEEL_SEGMENTS) - 1)
    prize = WHEEL_SEGMENTS[prize_index].copy()
    save_user(user_id, u)
    return {"status": "ok", "prizeIndex": prize_index, "prize": prize}


@app.get("/ad-status")
async def ad_status(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    return {"ad_watch_count": u.get("ad_watch_count", 0), "free_spins": u.get("free_spins", 0)}


@app.post("/add-points")
async def add_points(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    points = data.get("points", 0)
    if not user_id or not isinstance(points, (int, float)) or points <= 0:
        raise HTTPException(status_code=400, detail="Points must be a positive number")
    u = get_user(user_id)
    if u.get("double_active"):
        points *= 2
    u["total_points"] = u.get("total_points", 0) + points
    u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    save_user(user_id, u)
    return {"status": "ok", "added": points, "total_points": u["total_points"]}


@app.post("/add-stars")
async def add_stars(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    stars = data.get("stars", 0)
    if not user_id or not isinstance(stars, int) or stars <= 0:
        raise HTTPException(status_code=400, detail="Invalid stars value")
    u = get_user(user_id)
    u["stars"] = u.get("stars", 0) + stars
    save_user(user_id, u)
    return {"status": "ok", "stars": u["stars"]}


@app.post("/add-free-spins")
async def add_free_spins(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    spins = data.get("spins", 0)
    if not user_id or not isinstance(spins, int) or spins <= 0:
        raise HTTPException(status_code=400, detail="Invalid spins value")
    u = get_user(user_id)
    u["free_spins"] = u.get("free_spins", 0) + spins
    save_user(user_id, u)
    return {"status": "ok", "free_spins": u["free_spins"]}


@app.post("/log")
async def log_game(request: Request):
    return {"status": "ok"}


@app.get("/leaderboard")
async def get_leaderboard(request: Request, limit: int = 20):
    check_auth(request)
    users = read_json(USERS_FILE)
    lb = []
    for uid, data in users.items():
        lb.append({
            "userId": uid,
            "nickname": data.get("display_name", uid[:12]),
            "points": data.get("total_points", 0),
            "stars": data.get("stars", 0),
        })
    lb.sort(key=lambda x: (-x["points"], -x["stars"]))
    return {"leaderboard": lb[:limit]}


@app.post("/set-display-name")
async def set_display_name(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    display_name = data.get("display_name", "").strip()
    if not user_id or not display_name:
        raise HTTPException(status_code=400, detail="Missing userId or display_name")
    if len(display_name) > 30:
        raise HTTPException(status_code=400, detail="Display name too long (max 30 chars)")
    u = get_user(user_id)
    u["display_name"] = display_name
    save_user(user_id, u)
    return {"status": "ok", "display_name": display_name}


# ========== AVATAR ENDPOINTS ==========
@app.get("/avatar")
async def get_avatar(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    equipped_items = get_equipped_items(u)
    return {
        "pet_emoji": u.get("pet_skin", "🐱"),
        "pet_name": u.get("pet_name", "Whiskers"),
        "happiness": u.get("happiness", 50),
        "food_items": u.get("food_items", 0),
        "equipped_items": equipped_items,
    }


@app.get("/inventory")
async def get_inventory(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    shop = read_json(SHOP_FILE)
    all_items = [it for cat in shop.values() for it in cat] + AVATAR_ITEMS_POOL
    inv = [it for it in all_items if it["id"] in u.get("inventory", [])]
    return {"items": inv, "equipped": list(u.get("equipped", {}).values())}


@app.get("/shop")
async def get_shop():
    return read_json(SHOP_FILE)


@app.post("/buy")
async def buy_item(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    item_id = data.get("itemId")
    if not user_id or not item_id:
        raise HTTPException(status_code=400, detail="Missing params")
    u = get_user(user_id)
    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    if item_id in u.get("inventory", []):
        raise HTTPException(status_code=400, detail="Already owned")
    cost = item.get("price", 0)
    if u.get("stars", 0) < cost:
        raise HTTPException(status_code=400, detail="Not enough stars")
    u["stars"] = u.get("stars", 0) - cost
    u.setdefault("inventory", []).append(item_id)
    save_user(user_id, u)
    return {"status": "ok", "cost": cost}


@app.post("/equip")
async def equip_item(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    item_id = data.get("itemId")
    if not user_id or not item_id:
        raise HTTPException(status_code=400, detail="Missing params")
    u = get_user(user_id)
    if item_id not in u.get("inventory", []):
        raise HTTPException(status_code=400, detail="Not in inventory")
    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    slot = item.get("slot", "outfit")
    if slot == "skin":
        u["pet_skin"] = item.get("icon", "🐱")
    elif slot == "background":
        u["background"] = item_id
    else:
        u.setdefault("equipped", {})[slot] = item_id
    save_user(user_id, u)
    return {"status": "ok", "equipped_items": get_equipped_items(u)}


@app.post("/unequip")
async def unequip_item(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    item_id = data.get("itemId")
    if not user_id or not item_id:
        raise HTTPException(status_code=400, detail="Missing params")
    u = get_user(user_id)
    item = get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    slot = item.get("slot", "outfit")
    if slot == "skin":
        u["pet_skin"] = "🐱"
    elif slot == "background":
        u["background"] = None
    else:
        u.get("equipped", {}).pop(slot, None)
    save_user(user_id, u)
    return {"status": "ok", "equipped_items": get_equipped_items(u)}


@app.post("/feed")
async def feed_cat(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    u = get_user(user_id)
    if u.get("food_items", 0) < 1:
        raise HTTPException(status_code=400, detail="No food items! Spin the wheel to win food.")
    u["food_items"] = u.get("food_items", 0) - 1
    u["happiness"] = min(100, u.get("happiness", 50) + 10)
    u["total_points"] = u.get("total_points", 0) + 5
    save_user(user_id, u)
    return {"status": "ok", "message": "Yum! +5 points", "happiness": u["happiness"]}
