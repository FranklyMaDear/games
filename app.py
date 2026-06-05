from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json, os, random, uuid
from datetime import datetime, date, timedelta
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
    {"id": "d1", "day": 1, "description": "Play 1 match of Connect 4", "target": 1, "game": "Connect 4", "reward_type": "points", "reward_value": 10, "reward_label": "+10 Points"},
    {"id": "d2", "day": 2, "description": "Complete 1 grid of Sudoku", "target": 1, "game": "Sudoku", "reward_type": "stars", "reward_value": 10, "reward_label": "+10 Stars"},
    {"id": "d3", "day": 3, "description": "Play 1 match of Chess", "target": 1, "game": "Chess", "reward_type": "points", "reward_value": 20, "reward_label": "+20 Points"},
    {"id": "d4", "day": 4, "description": "Win 2 matches of Connect 4", "target": 2, "game": "Connect 4", "reward_type": "stars", "reward_value": 20, "reward_label": "+20 Stars"},
    {"id": "d5", "day": 5, "description": "Complete 2 grids of Sudoku", "target": 2, "game": "Sudoku", "reward_type": "free_spin", "reward_value": 2, "reward_label": "+2 Free Spins"},
    {"id": "d6", "day": 6, "description": "Play 2 matches of Chess", "target": 2, "game": "Chess", "reward_type": "points", "reward_value": 50, "reward_label": "+50 Points"},
    {"id": "d7", "day": 7, "description": "Complete 3 grids of Sudoku", "target": 3, "game": "Sudoku", "reward_type": "stars", "reward_value": 50, "reward_label": "+50 Stars"},
    {"id": "d8", "day": 8, "description": "Win 3 matches of Connect 4", "target": 3, "game": "Connect 4", "reward_type": "free_spin", "reward_value": 3, "reward_label": "+3 Free Spins"},
    {"id": "d9", "day": 9, "description": "Win 2 matches of Chess", "target": 2, "game": "Chess", "reward_type": "points", "reward_value": 100, "reward_label": "+100 Points"},
    {"id": "d10", "day": 10, "description": "Complete 1 Chess, 1 Sudoku, 1 Connect 4", "target": 3, "game": "Multi", "reward_type": "free_spin", "reward_value": 5, "reward_label": "+5 Free Spins"},
]

WEEKLY_MISSIONS = [
    {"id": "w1", "description": "Play 7 matches of Chess", "target": 7, "game": "Chess", "reward_type": "points", "reward_value": 150, "reward_label": "+150 Points"},
    {"id": "w2", "description": "Complete 5 grids of Sudoku", "target": 5, "game": "Sudoku", "reward_type": "stars", "reward_value": 150, "reward_label": "+150 Stars"},
    {"id": "w3", "description": "Win 8 matches of Connect 4", "target": 8, "game": "Connect 4", "reward_type": "free_spin", "reward_value": 10, "reward_label": "+10 Free Spins"},
    {"id": "w4", "description": "3 Chess, 3 Sudoku, 3 Connect 4", "target": 9, "game": "Multi", "reward_type": "points", "reward_value": 300, "reward_label": "+300 Points +5 Free Spins"},
]

WHEEL_PRIZES = [
    {"label": "+10 Points", "type": "points", "value": 10},
    {"label": "+10 Points", "type": "points", "value": 10},
    {"label": "+1 Free Spin", "type": "free_spin", "value": 1},
    {"label": "ZONK", "type": "zonk", "value": 0},
    {"label": "+20 Points", "type": "points", "value": 20},
    {"label": "+20 Points", "type": "points", "value": 20},
    {"label": "+2 Free Spins", "type": "free_spin", "value": 2},
    {"label": "ZONK", "type": "zonk", "value": 0},
    {"label": "+50 Points", "type": "points", "value": 50},
    {"label": "+50 Points", "type": "points", "value": 50},
    {"label": "+3 Free Spins", "type": "free_spin", "value": 3},
    {"label": "+5 Free Spins", "type": "free_spin", "value": 5},
]

DEFAULT_SHOP = {
    "hats": [
        {"id":"hat_01","name":"Magic Hat","icon":"🎩","price":50,"slot":"hat"},
        {"id":"hat_02","name":"Cool Sunglasses","icon":"😎","price":30,"slot":"glasses"},
        {"id":"hat_03","name":"Crown","icon":"👑","price":100,"slot":"hat"},
    ],
    "outfits": [
        {"id":"outfit_01","name":"Superhero Cape","icon":"🦸","price":80,"slot":"outfit"},
        {"id":"outfit_02","name":"Rainbow Shirt","icon":"👕","price":40,"slot":"outfit"},
        {"id":"outfit_03","name":"Princess Dress","icon":"👗","price":90,"slot":"outfit"},
    ],
    "skins": [
        {"id":"skin_01","name":"Golden Retriever","icon":"🐕","price":200,"slot":"skin"},
        {"id":"skin_02","name":"Tabby Cat","icon":"🐈","price":150,"slot":"skin"},
        {"id":"skin_03","name":"Bunny","icon":"🐰","price":120,"slot":"skin"},
    ],
    "backgrounds": [
        {"id":"bg_01","name":"Beach","icon":"🏖️","price":60,"slot":"background"},
        {"id":"bg_02","name":"Space","icon":"🌌","price":70,"slot":"background"},
        {"id":"bg_03","name":"Castle","icon":"🏰","price":80,"slot":"background"},
    ]
}

AVATAR_ITEMS_POOL = [
    {"id":"avatar_01","name":"Wizard Robe","icon":"🧙","price":0,"slot":"outfit"},
    {"id":"avatar_02","name":"Pirate Eye Patch","icon":"🦜","price":0,"slot":"glasses"},
    {"id":"avatar_03","name":"Angel Wings","icon":"👼","price":0,"slot":"outfit"},
    {"id":"avatar_04","name":"Detective Hat","icon":"🕵️","price":0,"slot":"hat"},
    {"id":"avatar_05","name":"Flower Crown","icon":"🌺","price":0,"slot":"hat"},
    {"id":"avatar_06","name":"Bow Tie","icon":"🎀","price":0,"slot":"outfit"},
]

def read_json(filename):
    if not os.path.exists(filename):
        if filename == SHOP_FILE: write_json(SHOP_FILE, DEFAULT_SHOP); return DEFAULT_SHOP
        return {} if filename == USERS_FILE else []
    try: return json.load(open(filename,"r"))
    except: return {} if filename == USERS_FILE else []

def write_json(filename, data):
    with open(filename,"w") as f: json.dump(data, f, indent=2)

def get_user(user_id: str) -> dict:
    users = read_json(USERS_FILE)
    if user_id not in users:
        users[user_id] = {
            "total_points":0,"stars":0,"level":1,"xp":0,"streak":0,"last_login_date":None,
            "daily_missions":{},"weekly_missions":{},"last_daily_reset":None,"last_weekly_reset":None,
            "ad_watch_count":0,"free_spins":0,
            "inventory":[],"equipped":{},"pet_skin":"🐱","pet_name":"Whiskers","background":None,"happiness":50,"food_items":0,"double_active":False
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

    u["level"] = max(1, (u.get("total_points",0)//POINTS_PER_LEVEL)+1)
    for field, default in [("daily_missions",{}),("weekly_missions",{}),("free_spins",0),("stars",0),("happiness",50),("food_items",0),("inventory",[]),("equipped",{}),("double_active",False),("pet_skin","🐱"),("pet_name","Whiskers"),("background",None)]:
        if field not in u: u[field] = default
    users[user_id] = u; write_json(USERS_FILE, users)
    return u

def save_user(user_id, data):
    users = read_json(USERS_FILE); users[user_id] = data; write_json(USERS_FILE, users)

def check_auth(request: Request):
    if request.headers.get("X-API-Key") != API_KEY: raise HTTPException(403, "Invalid API Key")

def get_item_by_id(item_id):
    shop = read_json(SHOP_FILE)
    for cat in shop.values():
        for item in cat:
            if item["id"] == item_id: return item
    for item in AVATAR_ITEMS_POOL:
        if item["id"] == item_id: return item
    return None

def get_equipped_items(user_data):
    equipped = {}
    all_items = [it for cat in read_json(SHOP_FILE).values() for it in cat] + AVATAR_ITEMS_POOL
    for slot, item_id in user_data.get("equipped", {}).items():
        item = next((it for it in all_items if it["id"] == item_id), None)
        if item: equipped[slot] = item
    return equipped

@app.get("/board")
async def get_board(request: Request, userId: str):
    check_auth(request); u = get_user(userId)
    return {"total_points":u["total_points"],"stars":u.get("stars",0),"level":u["level"],"free_spins":u.get("free_spins",0),"next_level_points":u["level"]*POINTS_PER_LEVEL,"happiness":u.get("happiness",50)}

@app.get("/missions")
async def get_missions(request: Request, userId: str, type: str = "daily"):
    check_auth(request); u = get_user(userId)
    missions_list = DAILY_MISSIONS if type == "daily" else WEEKLY_MISSIONS
    key = "daily_missions" if type == "daily" else "weekly_missions"
    result = []
    for m in missions_list:
        md = u.get(key, {}).get(m["id"], {"progress": 0, "claimed": False})
        result.append({
            "id": m["id"], "day": m.get("day", 0), "description": m["description"],
            "target": m["target"], "reward_type": m["reward_type"], "reward_value": m["reward_value"],
            "reward_label": m["reward_label"], "progress": md.get("progress", 0), "claimed": md.get("claimed", False)
        })
    return {"missions": result}

@app.post("/missions/update")
async def update_mission_progress(request: Request):
    check_auth(request); data = await request.json()
    user_id = data.get("userId"); game = data.get("game",""); score = data.get("score",0); playtime = data.get("playtime",0)
    if not user_id: raise HTTPException(400, "Missing userId")
    u = get_user(user_id)

    for mlist, key in [(DAILY_MISSIONS, "daily_missions"), (WEEKLY_MISSIONS, "weekly_missions")]:
        for m in mlist:
            mid = m["id"]
            if mid not in u[key]: u[key][mid] = {"progress": 0, "claimed": False}
            if m["game"] == game or m["game"] == "Multi":
                if m["game"] == "Multi":
                    if playtime > 0: u[key][mid]["progress"] = min(m["target"], u[key][mid].get("progress", 0) + 1)
                else:
                    if playtime > 0 or score > 0: u[key][mid]["progress"] = min(m["target"], u[key][mid].get("progress", 0) + 1)

    save_user(user_id, u)
    return {"status": "ok"}

@app.post("/missions/claim")
async def claim_mission(request: Request):
    check_auth(request); data = await request.json()
    user_id = data.get("userId"); mission_id = data.get("missionId"); mtype = data.get("type", "daily")
    if not user_id or not mission_id: raise HTTPException(400, "Missing params")
    u = get_user(user_id)
    key = "daily_missions" if mtype == "daily" else "weekly_missions"
    if mission_id not in u.get(key, {}): raise HTTPException(404, "Mission not found")
    md = u[key][mission_id]
    missions_list = DAILY_MISSIONS if mtype == "daily" else WEEKLY_MISSIONS
    mdef = next((m for m in missions_list if m["id"] == mission_id), None)
    if not mdef or md.get("progress", 0) < mdef["target"] or md.get("claimed"): raise HTTPException(400, "Not completable")
    md["claimed"] = True
    save_user(user_id, u)
    return {"status": "ok"}

@app.post("/wheel/spin")
async def spin_wheel(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId")
    if not user_id: raise HTTPException(400, "Missing userId")
    u = get_user(user_id)
    if u.get("free_spins",0)<1: raise HTTPException(403, "Not enough free spins")
    u["free_spins"]-=1
    prize_index = random.randint(0, len(WHEEL_PRIZES)-1)
    prize = WHEEL_PRIZES[prize_index].copy()
    save_user(user_id, u)
    return {"status":"ok","prize":prize,"prizeIndex":prize_index}

@app.get("/ad-status")
async def ad_status(request: Request, userId: str):
    check_auth(request); u = get_user(userId)
    return {"ad_watch_count":u.get("ad_watch_count",0),"free_spins":u.get("free_spins",0)}

@app.post("/add-points")
async def add_points(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); points = data.get("points",0)
    if not user_id or not isinstance(points,(int,float)) or points<=0: raise HTTPException(400, "Invalid")
    u = get_user(user_id); u["total_points"] = u.get("total_points",0)+points
    u["level"] = max(1,(u["total_points"]//POINTS_PER_LEVEL)+1)
    save_user(user_id, u); return {"status":"ok","added":points}

@app.post("/add-stars")
async def add_stars(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); stars = data.get("stars",0)
    if not user_id or not isinstance(stars,int) or stars<=0: raise HTTPException(400, "Invalid")
    u = get_user(user_id); u["stars"] = u.get("stars",0) + stars
    save_user(user_id, u); return {"status":"ok","stars":u["stars"]}

@app.post("/add-free-spins")
async def add_free_spins(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); spins = data.get("spins",0)
    if not user_id or not isinstance(spins,int) or spins<=0: raise HTTPException(400, "Invalid")
    u = get_user(user_id); u["free_spins"] = u.get("free_spins",0) + spins
    save_user(user_id, u); return {"status":"ok","free_spins":u["free_spins"]}

@app.post("/log")
async def log_game(request: Request): return {"status":"ok"}

@app.get("/leaderboard")
async def get_leaderboard(request: Request, limit: int = 20):
    check_auth(request); users = read_json(USERS_FILE)
    lb = [{"userId":uid,"points":data.get("total_points",0)} for uid,data in users.items()]
    lb.sort(key=lambda x: x["points"], reverse=True); return {"leaderboard":lb[:limit]}

@app.get("/avatar")
async def get_avatar(request: Request, userId: str):
    check_auth(request); u = get_user(userId)
    return {"pet_emoji":u.get("pet_skin","🐱"),"pet_name":u.get("pet_name","Whiskers"),"happiness":u.get("happiness",50),"food_items":u.get("food_items",0),"equipped_items":get_equipped_items(u)}

@app.get("/inventory")
async def get_inventory(request: Request, userId: str):
    check_auth(request); u = get_user(userId)
    all_items = [it for cat in read_json(SHOP_FILE).values() for it in cat] + AVATAR_ITEMS_POOL
    inv = [it for it in all_items if it["id"] in u.get("inventory",[])]
    return {"items":inv,"equipped":list(u.get("equipped",{}).values())}

@app.get("/shop")
async def get_shop(): return read_json(SHOP_FILE)

@app.post("/buy")
async def buy_item(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); item_id = data.get("itemId")
    if not user_id or not item_id: raise HTTPException(400, "Missing params")
    u = get_user(user_id); item = get_item_by_id(item_id)
    if not item: raise HTTPException(404, "Item not found")
    if item_id in u.get("inventory",[]): raise HTTPException(400, "Already owned")
    cost = item.get("price",0)
    if u.get("stars",0)<cost: raise HTTPException(400, "Not enough stars")
    u["stars"] = u.get("stars",0)-cost; u.setdefault("inventory",[]).append(item_id)
    save_user(user_id, u); return {"status":"ok","cost":cost}

@app.post("/equip")
async def equip_item(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); item_id = data.get("itemId")
    if not user_id or not item_id: raise HTTPException(400, "Missing params")
    u = get_user(user_id)
    if item_id not in u.get("inventory",[]): raise HTTPException(400, "Not in inventory")
    item = get_item_by_id(item_id)
    if not item: raise HTTPException(404, "Item not found")
    slot = item.get("slot","outfit")
    if slot=="skin": u["pet_skin"] = item.get("icon","🐱")
    elif slot=="background": u["background"] = item_id
    else: u.setdefault("equipped",{})[slot] = item_id
    save_user(user_id, u)
    return {"status":"ok","equipped_items":get_equipped_items(u)}

@app.post("/unequip")
async def unequip_item(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); item_id = data.get("itemId")
    if not user_id or not item_id: raise HTTPException(400, "Missing params")
    u = get_user(user_id); item = get_item_by_id(item_id)
    if not item: raise HTTPException(404, "Item not found")
    slot = item.get("slot","outfit")
    if slot=="skin": u["pet_skin"] = "🐱"
    elif slot=="background": u["background"] = None
    else: u.get("equipped",{}).pop(slot, None)
    save_user(user_id, u)
    return {"status":"ok","equipped_items":get_equipped_items(u)}

@app.post("/feed")
async def feed_cat(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId")
    if not user_id: raise HTTPException(400, "Missing userId")
    u = get_user(user_id)
    if u.get("food_items",0) < 1: raise HTTPException(400, "No food items!")
    u["food_items"] = u.get("food_items",0) - 1
    u["happiness"] = min(100, u.get("happiness",50) + 10)
    u["total_points"] = u.get("total_points",0) + 5
    save_user(user_id, u)
    return {"status":"ok","message":"Yum! +5 points","happiness":u["happiness"]}
