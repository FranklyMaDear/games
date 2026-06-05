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

DAILY_MISSIONS = [
    {"id": 1, "description": "Play Crack The Code for 3 minutes", "target": 3, "reward_points": 50, "type": "playtime", "game": "Crack The Code"},
    {"id": 2, "description": "Score 500 pts in Code Kids", "target": 500, "reward_points": 80, "type": "score", "game": "Crack The Code Kids"},
    {"id": 3, "description": "Find 10 words in Code Words", "target": 10, "reward_points": 100, "type": "words_found", "game": "Crack The Code Words"},
]

# Ad rewards
FREE_SPINS_1_AD = 5
AD_POINTS = 10
AD_STARS = 2

# 12 slices - Wood theme, some require ads
WHEEL_PRIZES = [
    {"label": "+10 Points", "type": "points", "value": 10},
    {"label": "+10 Stars", "type": "stars", "value": 10},
    {"label": "+1 Free Spin", "type": "free_spin", "value": 1},
    {"label": "+2 Free Spins", "type": "free_spin", "value": 2},
    {"label": "+20 Points (Ads)", "type": "points_ads", "value": 20},
    {"label": "+10 Points (Ads)", "type": "points_ads", "value": 10},
    {"label": "+10 Stars (Ads)", "type": "stars_ads", "value": 10},
    {"label": "+1 Free Spin (Ads)", "type": "free_spin_ads", "value": 1},
    {"label": "+2 Free Spins (Ads)", "type": "free_spin_ads", "value": 2},
    {"label": "+10 Points", "type": "points", "value": 10},
    {"label": "+10 Stars", "type": "stars", "value": 10},
    {"label": "+20 Points (Ads)", "type": "points_ads", "value": 20},
]

MILESTONE_2000 = 2000
MILESTONE_3000 = 3000

# ---------- SHOP & AVATAR ITEMS ----------
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
    ]
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
        users[user_id] = {
            "total_points": 0,
            "stars": 0,
            "level": 1,
            "xp": 0,
            "streak": 0,
            "last_login_date": None,
            "missions": {},
            "last_mission_date": None,
            "ad_watch_count": 0,
            "ad_scale_1_claimed": False,
            "ad_scale_2_claimed": False,
            "free_spins": 0,
            "milestone_2000_reached": False,
            "milestone_3000_reached": False,
            "referral_code": str(uuid.uuid4())[:8],
            "referred_by": None,
            "referral_reward_claimed": False,
            "inventory": [],
            "equipped": {},
            "pet_skin": "🐱",
            "pet_name": "Whiskers",
            "background": None,
            "happiness": 50,
            "food_items": 0,
            "double_active": False,
        }
    u = users[user_id]
    today = date.today().isoformat()

    # Daily reset
    if u.get("last_mission_date") != today:
        u["missions"] = {str(m["id"]): {"progress": 0, "claimed": False} for m in DAILY_MISSIONS}
        u["ad_watch_count"] = 0
        u["ad_scale_1_claimed"] = False
        u["ad_scale_2_claimed"] = False
        u["last_mission_date"] = today

    u["level"] = max(1, (u.get("total_points", 0) // POINTS_PER_LEVEL) + 1)

    # Ensure all fields exist
    defaults = {
        "missions": {},
        "free_spins": 0,
        "stars": 0,
        "happiness": 50,
        "food_items": 0,
        "xp": 0,
        "inventory": [],
        "equipped": {},
        "milestone_2000_reached": False,
        "milestone_3000_reached": False,
        "ad_scale_1_claimed": False,
        "ad_scale_2_claimed": False,
        "double_active": False,
        "pet_skin": "🐱",
        "pet_name": "Whiskers",
        "background": None,
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
async def get_missions(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    missions_status = []
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        md = u.get("missions", {}).get(mid, {"progress": 0, "claimed": False})
        missions_status.append({
            "id": m["id"],
            "description": m["description"],
            "target": m["target"],
            "progress": md.get("progress", 0),
            "reward_points": m["reward_points"],
            "claimed": md.get("claimed", False),
        })
    return {"missions": missions_status}


@app.post("/missions/update")
async def update_mission_progress(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "")
    score = data.get("score", 0)
    playtime = data.get("playtime", 0)
    words = data.get("words", 0)

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")

    u = get_user(user_id)
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        if mid not in u["missions"]:
            u["missions"][mid] = {"progress": 0, "claimed": False}
        if m["type"] == "score" and m["game"] == game:
            u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress", 0) + score)
        elif m["type"] == "playtime" and m["game"] == game:
            u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress", 0) + playtime)
        elif m["type"] == "words_found" and m["game"] == game:
            u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress", 0) + words)

    save_user(user_id, u)
    return {"status": "ok"}


@app.post("/missions/claim")
async def claim_mission(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    mission_id = str(data.get("missionId"))

    u = get_user(user_id)
    if mission_id not in u.get("missions", {}):
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = u["missions"][mission_id]
    mission_def = next((m for m in DAILY_MISSIONS if str(m["id"]) == mission_id), None)
    if not mission_def or mission.get("progress", 0) < mission_def["target"] or mission.get("claimed"):
        raise HTTPException(status_code=400, detail="Mission not completable or already claimed")

    reward = mission_def["reward_points"]
    if u.get("double_active"):
        reward *= 2

    u["total_points"] = u.get("total_points", 0) + reward
    u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    mission["claimed"] = True

    if u["total_points"] >= MILESTONE_2000 and not u.get("milestone_2000_reached"):
        u["milestone_2000_reached"] = True
    if u["total_points"] >= MILESTONE_3000 and not u.get("milestone_3000_reached"):
        u["milestone_3000_reached"] = True

    save_user(user_id, u)
    return {"status": "ok", "reward_points": reward, "total_points": u["total_points"], "level": u["level"]}


@app.post("/ad-reward")
async def ad_reward(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")

    u = get_user(user_id)
    pts = AD_POINTS
    stars = AD_STARS
    if u.get("double_active"):
        pts *= 2
        stars *= 2

    u["free_spins"] = u.get("free_spins", 0) + FREE_SPINS_1_AD
    u["total_points"] = u.get("total_points", 0) + pts
    u["stars"] = u.get("stars", 0) + stars
    u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)

    save_user(user_id, u)
    return {
        "status": "ok",
        "points_earned": pts,
        "stars_earned": stars,
        "free_spins": u["free_spins"],
    }


@app.post("/wheel/spin")
async def spin_wheel(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")

    u = get_user(user_id)
    if u.get("free_spins", 0) < 1:
        raise HTTPException(status_code=403, detail="Not enough free spins")

    u["free_spins"] -= 1

    prize_index = random.randint(0, len(WHEEL_PRIZES) - 1)
    prize = WHEEL_PRIZES[prize_index].copy()

    # Only instant types are credited here; _ads types are handled client-side
    if prize["type"] == "points":
        u["total_points"] = u.get("total_points", 0) + prize["value"]
    elif prize["type"] == "stars":
        u["stars"] = u.get("stars", 0) + prize["value"]
    elif prize["type"] == "free_spin":
        u["free_spins"] = u.get("free_spins", 0) + prize["value"]
    elif prize["type"] == "cosmetic":
        available = [it for it in AVATAR_ITEMS_POOL if it["id"] not in u.get("inventory", [])]
        if available:
            item = random.choice(available)
            u.setdefault("inventory", []).append(item["id"])
            prize["label"] = item["name"]
            prize["item"] = item
        else:
            prize["type"] = "stars"
            prize["value"] = 20
            prize["label"] = "20 Stars"
            u["stars"] = u.get("stars", 0) + 20

    u["level"] = max(1, (u.get("total_points", 0) // POINTS_PER_LEVEL) + 1)

    if u["total_points"] >= MILESTONE_2000 and not u.get("milestone_2000_reached"):
        u["milestone_2000_reached"] = True
    if u["total_points"] >= MILESTONE_3000 and not u.get("milestone_3000_reached"):
        u["milestone_3000_reached"] = True

    save_user(user_id, u)
    return {"status": "ok", "prize": prize, "prizeIndex": prize_index}


@app.get("/ad-status")
async def ad_status(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    return {
        "ad_watch_count": u.get("ad_watch_count", 0),
        "free_spins": u.get("free_spins", 0),
    }


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

    if u["total_points"] >= MILESTONE_2000 and not u.get("milestone_2000_reached"):
        u["milestone_2000_reached"] = True
    if u["total_points"] >= MILESTONE_3000 and not u.get("milestone_3000_reached"):
        u["milestone_3000_reached"] = True

    save_user(user_id, u)

    logs = read_json(POINTS_LOG_FILE)
    logs.append({
        "userId": user_id,
        "game": data.get("game", "unknown"),
        "points": points,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "game_score",
    })
    write_json(POINTS_LOG_FILE, logs)

    return {"status": "ok", "added": points, "total_points": u["total_points"], "level": u["level"]}


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
    lb = [{"userId": uid, "points": data.get("total_points", 0)} for uid, data in users.items()]
    lb.sort(key=lambda x: x["points"], reverse=True)
    return {"leaderboard": lb[:limit]}


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
