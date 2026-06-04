from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import random
import uuid
from datetime import datetime, date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gamified_hub")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

API_KEY = os.environ.get("API_KEY", "m0n3t4g_s3cur3_k3y_2026")
USERS_FILE = "users.json"
POINTS_LOG_FILE = "points_log.json"
SHOP_FILE = "shop.json"

POINTS_PER_LEVEL = 1000

DAILY_MISSIONS = [
    {"id": 1, "description": "Play Crack The Code for 3 minutes", "target": 3, "reward_points": 50, "type": "playtime", "game": "Crack The Code"},
    {"id": 2, "description": "Score 500 pts in Code Kids", "target": 500, "reward_points": 80, "type": "score", "game": "Crack The Code Kids"},
    {"id": 3, "description": "Find 10 words in Code Words", "target": 10, "reward_points": 100, "type": "words_found", "game": "Crack The Code Words"},
]

AD_SCALE_1_TARGET = 5
AD_SCALE_1_BONUS = 100
AD_SCALE_2_TARGET = 10
AD_SCALE_2_BONUS = 200
AD_POINTS_PER_WATCH = 20
FREE_SPINS_1_AD = 5

WHEEL_PRIZES = [
    {"label": "+5 Points", "type": "points", "value": 5},
    {"label": "+10 Stars", "type": "stars", "value": 10},
    {"label": "+20 Points", "type": "points", "value": 20},
    {"label": "+30 Stars", "type": "stars", "value": 30},
    {"label": "+10 Points", "type": "points", "value": 10},
    {"label": "+50 Stars", "type": "stars", "value": 50},
    {"label": "+50 Points", "type": "points", "value": 50},
    {"label": "+100 Stars", "type": "stars", "value": 100},
    {"label": "Free Spin", "type": "free_spin", "value": 1},
    {"label": "Avatar Item", "type": "avatar_item", "value": 0},
    {"label": "Try Again", "type": "lose", "value": 0},
    {"label": "Try Again", "type": "lose", "value": 0},
]

MILESTONE_2000 = 2000
MILESTONE_3000 = 3000
TALLY_URL = "https://tally.so/r/44jy95?transparentBackground=1"

DEFAULT_SHOP = {
    "hats": [
        {"id": "hat_01", "name": "Magic Hat", "icon": "🎩", "price": 50, "slot": "hat"},
        {"id": "hat_02", "name": "Cool Sunglasses", "icon": "😎", "price": 30, "slot": "hat"},
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
    ]
}

AVATAR_ITEMS_POOL = [
    {"id": "avatar_01", "name": "Wizard Robe", "icon": "🧙", "price": 0, "slot": "outfit"},
    {"id": "avatar_02", "name": "Pirate Eye Patch", "icon": "🦜", "price": 0, "slot": "hat"},
    {"id": "avatar_03", "name": "Angel Wings", "icon": "👼", "price": 0, "slot": "outfit"},
    {"id": "avatar_04", "name": "Detective Hat", "icon": "🕵️", "price": 0, "slot": "hat"},
]

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
        users[user_id] = {
            "total_points": 0, "stars": 0, "level": 1,
            "streak": 0, "last_login_date": None,
            "missions": {}, "last_mission_date": None,
            "ad_watch_count": 0, "ad_scale_1_claimed": False, "ad_scale_2_claimed": False,
            "free_spins": 0,
            "milestone_2000_reached": False, "milestone_3000_reached": False,
            "referral_code": str(uuid.uuid4())[:8], "referred_by": None, "referral_reward_claimed": False,
            "inventory": [], "equipped": {}, "pet_skin": "🐶", "pet_name": "My Buddy", "background": None
        }
    user_data = users[user_id]
    today = date.today().isoformat()
    if user_data.get("last_mission_date") != today:
        user_data["missions"] = {str(m["id"]): {"progress": 0, "claimed": False} for m in DAILY_MISSIONS}
        user_data["ad_watch_count"] = 0
        user_data["ad_scale_1_claimed"] = False
        user_data["ad_scale_2_claimed"] = False
        user_data["last_mission_date"] = today
    user_data["level"] = max(1, (user_data.get("total_points", 0) // POINTS_PER_LEVEL) + 1)
    for field in ["missions", "free_spins", "milestone_2000_reached", "milestone_3000_reached", "ad_watch_count", "stars", "inventory", "equipped", "pet_skin", "pet_name", "background"]:
        if field not in user_data:
            if field == "missions": user_data[field] = {}
            elif field == "free_spins": user_data[field] = 0
            elif field == "stars": user_data[field] = 0
            elif field == "inventory": user_data[field] = []
            elif field == "equipped": user_data[field] = {}
            elif field in ("milestone_2000_reached", "milestone_3000_reached", "ad_scale_1_claimed", "ad_scale_2_claimed"): user_data[field] = False
            elif field == "pet_skin": user_data[field] = "🐶"
            elif field == "pet_name": user_data[field] = "My Buddy"
            elif field == "background": user_data[field] = None
    users[user_id] = user_data
    write_json(USERS_FILE, users)
    return user_data

def save_user(user_id: str, user_data: dict):
    users = read_json(USERS_FILE)
    users[user_id] = user_data
    write_json(USERS_FILE, users)

def check_auth(request: Request):
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# =========================== ENDPOINTS ===========================

@app.get("/board")
async def get_board(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    return {"total_points": u["total_points"], "stars": u.get("stars", 0), "level": u["level"], "free_spins": u.get("free_spins", 0), "next_level_points": u["level"] * POINTS_PER_LEVEL, "milestone_2000_reached": u.get("milestone_2000_reached", False), "milestone_3000_reached": u.get("milestone_3000_reached", False), "tally_url": TALLY_URL}

@app.get("/missions")
async def get_missions(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    ms = []
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        md = u.get("missions", {}).get(mid, {"progress": 0, "claimed": False})
        ms.append({"id": m["id"], "description": m["description"], "target": m["target"], "progress": md.get("progress", 0), "reward_points": m["reward_points"], "claimed": md.get("claimed", False)})
    return {"missions": ms}

@app.post("/missions/update")
async def update_mission_progress(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId"); game = data.get("game", ""); score = data.get("score", 0); playtime = data.get("playtime", 0); words = data.get("words", 0)
    if not user_id: raise HTTPException(status_code=400, detail="Missing userId")
    u = get_user(user_id)
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        if mid not in u["missions"]: u["missions"][mid] = {"progress": 0, "claimed": False}
        if m["type"] == "score" and m["game"] == game: u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress", 0) + score)
        elif m["type"] == "playtime" and m["game"] == game: u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress", 0) + playtime)
        elif m["type"] == "words_found" and m["game"] == game: u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress", 0) + words)
    save_user(user_id, u)
    return {"status": "ok"}

@app.post("/missions/claim")
async def claim_mission(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId"); mission_id = str(data.get("missionId"))
    u = get_user(user_id)
    if mission_id not in u.get("missions", {}): raise HTTPException(status_code=404, detail="Mission not found")
    mission = u["missions"][mission_id]
    mission_def = next((m for m in DAILY_MISSIONS if str(m["id"]) == mission_id), None)
    if not mission_def or mission.get("progress", 0) < mission_def["target"] or mission.get("claimed"): raise HTTPException(status_code=400, detail="Mission not completable or already claimed")
    u["total_points"] = u.get("total_points", 0) + mission_def["reward_points"]
    u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    mission["claimed"] = True
    if u["total_points"] >= MILESTONE_2000 and not u.get("milestone_2000_reached"): u["milestone_2000_reached"] = True
    if u["total_points"] >= MILESTONE_3000 and not u.get("milestone_3000_reached"): u["milestone_3000_reached"] = True
    save_user(user_id, u)
    return {"status": "ok", "reward_points": mission_def["reward_points"], "total_points": u["total_points"], "level": u["level"]}

@app.post("/ad-watch")
async def ad_watch(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id: raise HTTPException(status_code=400, detail="Missing userId")
    u = get_user(user_id)
    u["ad_watch_count"] = u.get("ad_watch_count", 0) + 1
    points_earned = AD_POINTS_PER_WATCH; bonus = 0
    if u["ad_watch_count"] >= AD_SCALE_1_TARGET and not u.get("ad_scale_1_claimed"): bonus += AD_SCALE_1_BONUS; u["ad_scale_1_claimed"] = True
    if u["ad_watch_count"] >= AD_SCALE_2_TARGET and not u.get("ad_scale_2_claimed"): bonus += AD_SCALE_2_BONUS; u["ad_scale_2_claimed"] = True
    total_earned = points_earned + bonus
    u["total_points"] = u.get("total_points", 0) + total_earned
    u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    if u["total_points"] >= MILESTONE_2000 and not u.get("milestone_2000_reached"): u["milestone_2000_reached"] = True
    if u["total_points"] >= MILESTONE_3000 and not u.get("milestone_3000_reached"): u["milestone_3000_reached"] = True
    save_user(user_id, u)
    return {"status": "ok", "points_earned": total_earned, "total_points": u["total_points"], "ad_watch_count": u["ad_watch_count"], "level": u["level"], "bonus": bonus}

@app.post("/ad-free-spins-1")
async def ad_free_spins_1(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id: raise HTTPException(status_code=400, detail="Missing userId")
    u = get_user(user_id)
    u["free_spins"] = u.get("free_spins", 0) + FREE_SPINS_1_AD
    save_user(user_id, u)
    return {"status": "ok", "free_spins": u["free_spins"]}

@app.post("/wheel/spin")
async def spin_wheel(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id: raise HTTPException(status_code=400, detail="Missing userId")
    u = get_user(user_id)
    if u.get("free_spins", 0) < 1: raise HTTPException(status_code=403, detail="Not enough free spins")
    u["free_spins"] -= 1
    prize_index = random.randint(0, len(WHEEL_PRIZES)-1)
    prize = WHEEL_PRIZES[prize_index].copy()
    if prize["type"] == "points":
        u["total_points"] = u.get("total_points", 0) + prize["value"]
    elif prize["type"] == "stars":
        u["stars"] = u.get("stars", 0) + prize["value"]
    elif prize["type"] == "free_spin":
        u["free_spins"] = u.get("free_spins", 0) + prize["value"]
    elif prize["type"] == "avatar_item":
        pool = AVATAR_ITEMS_POOL
        available = [it for it in pool if it["id"] not in u.get("inventory", [])]
        if available:
            item = random.choice(available)
            u.setdefault("inventory", []).append(item["id"])
            prize["label"] = item["name"]
            prize["item"] = item
        else:
            prize["type"] = "stars"
            prize["value"] = 20
            prize["label"] = "+20 Stars"
            u["stars"] = u.get("stars", 0) + 20
    u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    if u["total_points"] >= MILESTONE_2000 and not u.get("milestone_2000_reached"): u["milestone_2000_reached"] = True
    if u["total_points"] >= MILESTONE_3000 and not u.get("milestone_3000_reached"): u["milestone_3000_reached"] = True
    save_user(user_id, u)
    return {"status": "ok", "prize": prize, "prizeIndex": prize_index, "total_points": u["total_points"], "stars": u.get("stars", 0), "free_spins": u["free_spins"], "level": u["level"]}

@app.post("/double-reward")
async def double_reward(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId"); rtype = data.get("type"); value = data.get("value", 0)
    if not user_id: raise HTTPException(status_code=400, detail="Missing userId")
    u = get_user(user_id)
    if rtype == "points":
        u["total_points"] = u.get("total_points", 0) + value
        u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    elif rtype == "stars":
        u["stars"] = u.get("stars", 0) + value
    save_user(user_id, u)
    return {"status": "ok", "added": value, "type": rtype}

@app.get("/ad-status")
async def ad_status(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    return {"ad_watch_count": u.get("ad_watch_count", 0), "ad_scale_1_target": AD_SCALE_1_TARGET, "ad_scale_1_claimed": u.get("ad_scale_1_claimed", False), "ad_scale_1_bonus": AD_SCALE_1_BONUS, "ad_scale_2_target": AD_SCALE_2_TARGET, "ad_scale_2_claimed": u.get("ad_scale_2_claimed", False), "ad_scale_2_bonus": AD_SCALE_2_BONUS, "points_per_ad": AD_POINTS_PER_WATCH, "free_spins": u.get("free_spins", 0)}

@app.get("/points/{user_id}")
async def get_points(user_id: str, request: Request):
    check_auth(request)
    u = get_user(user_id)
    return {"userId": user_id, "total_points": u["total_points"], "stars": u.get("stars", 0), "level": u["level"]}

@app.post("/add-points")
async def add_points(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId"); game = data.get("game", "unknown"); points = data.get("points", 0)
    if not user_id: raise HTTPException(status_code=400, detail="Missing userId")
    if not isinstance(points, (int, float)) or points <= 0: raise HTTPException(status_code=400, detail="Points must be positive")
    u = get_user(user_id)
    u["total_points"] = u.get("total_points", 0) + points
    u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    if u["total_points"] >= MILESTONE_2000 and not u.get("milestone_2000_reached"): u["milestone_2000_reached"] = True
    if u["total_points"] >= MILESTONE_3000 and not u.get("milestone_3000_reached"): u["milestone_3000_reached"] = True
    save_user(user_id, u)
    logs = read_json(POINTS_LOG_FILE)
    logs.append({"userId": user_id, "game": game, "points": points, "timestamp": datetime.utcnow().isoformat(), "source": "game_score"})
    write_json(POINTS_LOG_FILE, logs)
    return {"status": "ok", "added": points, "total_points": u["total_points"], "level": u["level"]}

@app.post("/log")
async def log_game(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId"); game = data.get("game", "unknown")
    if not user_id: raise HTTPException(status_code=400, detail="Missing userId")
    logs = read_json(POINTS_LOG_FILE)
    logs.append({"userId": user_id, "game": game, "points": 0, "timestamp": datetime.utcnow().isoformat(), "source": "free_play"})
    write_json(POINTS_LOG_FILE, logs)
    return {"status": "ok", "message": "Game launched (free play)"}

@app.get("/leaderboard")
async def get_leaderboard(request: Request, limit: int = 20):
    check_auth(request)
    users = read_json(USERS_FILE)
    lb = [{"userId": uid, "points": data.get("total_points", 0), "stars": data.get("stars", 0)} for uid, data in users.items()]
    lb.sort(key=lambda x: x["points"], reverse=True)
    return {"leaderboard": lb[:limit]}

# ========== AVATAR ENDPOINTS ==========
@app.get("/avatar")
async def get_avatar(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    return {"pet_emoji": u.get("pet_skin", "🐶"), "pet_name": u.get("pet_name", "My Buddy"), "background": u.get("background"), "inventory": u.get("inventory", []), "equipped": u.get("equipped", {})}

@app.get("/inventory")
async def get_inventory(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    shop = read_json(SHOP_FILE)
    all_items = []
    for cat in shop.values():
        all_items.extend(cat)
    all_items.extend(AVATAR_ITEMS_POOL)
    inv = []
    for item_id in u.get("inventory", []):
        item = next((it for it in all_items if it["id"] == item_id), None)
        if item: inv.append(item)
    return {"items": inv, "equipped": list(u.get("equipped", {}).values())}

@app.get("/shop")
async def get_shop():
    return read_json(SHOP_FILE)

@app.post("/buy")
async def buy_item(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId"); item_id = data.get("itemId")
    if not user_id or not item_id: raise HTTPException(status_code=400, detail="Missing params")
    u = get_user(user_id)
    shop = read_json(SHOP_FILE)
    all_items = []
    for cat in shop.values():
        all_items.extend(cat)
    all_items.extend(AVATAR_ITEMS_POOL)
    item = next((it for it in all_items if it["id"] == item_id), None)
    if not item: raise HTTPException(status_code=404, detail="Item not found")
    if item_id in u.get("inventory", []): raise HTTPException(status_code=400, detail="Already owned")
    cost = item.get("price", 0)
    if u.get("stars", 0) < cost: raise HTTPException(status_code=400, detail="Not enough stars")
    u["stars"] = u.get("stars", 0) - cost
    u.setdefault("inventory", []).append(item_id)
    save_user(user_id, u)
    return {"status": "ok", "cost": cost, "stars": u["stars"]}

@app.post("/equip")
async def equip_item(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId"); item_id = data.get("itemId")
    if not user_id or not item_id: raise HTTPException(status_code=400, detail="Missing params")
    u = get_user(user_id)
    if item_id not in u.get("inventory", []): raise HTTPException(status_code=400, detail="Item not in inventory")
    shop = read_json(SHOP_FILE)
    all_items = []
    for cat in shop.values():
        all_items.extend(cat)
    all_items.extend(AVATAR_ITEMS_POOL)
    item = next((it for it in all_items if it["id"] == item_id), None)
    if not item: raise HTTPException(status_code=404, detail="Item not found")
    slot = item.get("slot", "outfit")
    if slot == "skin":
        u["pet_skin"] = item.get("icon", "🐶")
    elif slot == "background":
        u["background"] = item_id
    else:
        u.setdefault("equipped", {})[slot] = item_id
    save_user(user_id, u)
    return {"status": "ok"}

@app.post("/unequip")
async def unequip_item(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId"); item_id = data.get("itemId")
    if not user_id or not item_id: raise HTTPException(status_code=400, detail="Missing params")
    u = get_user(user_id)
    shop = read_json(SHOP_FILE)
    all_items = []
    for cat in shop.values():
        all_items.extend(cat)
    all_items.extend(AVATAR_ITEMS_POOL)
    item = next((it for it in all_items if it["id"] == item_id), None)
    if not item: raise HTTPException(status_code=404, detail="Item not found")
    slot = item.get("slot", "outfit")
    if slot == "skin":
        u["pet_skin"] = "🐶"
    elif slot == "background":
        u["background"] = None
    else:
        u.get("equipped", {}).pop(slot, None)
    save_user(user_id, u)
    return {"status": "ok"}
