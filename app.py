from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json, os, random, uuid
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
    {"id": 1, "description": "Παίξε Crack The Code για 3 λεπτά", "target": 3, "reward_points": 50, "type": "playtime", "game": "Crack The Code"},
    {"id": 2, "description": "Σκόραρε 500 πόντους στο Code Kids", "target": 500, "reward_points": 80, "type": "score", "game": "Crack The Code Kids"},
    {"id": 3, "description": "Βρες 10 λέξεις στο Code Words", "target": 10, "reward_points": 100, "type": "words_found", "game": "Crack The Code Words"},
]

AD_SCALE_1_TARGET = 5
AD_SCALE_1_BONUS = 100
AD_SCALE_2_TARGET = 10
AD_SCALE_2_BONUS = 200
AD_POINTS_PER_WATCH = 10  # βασικό, διπλασιάζεται αν double active
AD_STARS_PER_WATCH = 2
FREE_SPINS_1_AD = 5

# Νέα WHEEL_PRIZES με βάρη (weighted)
WHEEL_PRIZES = [
    {"label": "+100 Νομίσματα", "type": "points", "value": 100, "weight": "uncommon"},
    {"label": "Μπόνους Γύρος", "type": "free_spin", "value": 1, "weight": "rare"},
    {"label": "10 Αστέρια", "type": "stars", "value": 10, "weight": "uncommon"},
    {"label": "Διπλοί Πόντοι", "type": "double", "value": 0, "weight": "epic"},
    {"label": "-10 Αστέρια", "type": "stars", "value": -10, "weight": "uncommon"},
    {"label": "Μηδέν", "type": "lose", "value": 0, "weight": "common"},
    {"label": "-10 Αστέρια", "type": "stars", "value": -10, "weight": "uncommon"},
    {"label": "Επίπεδο UP", "type": "level_up", "value": 0, "weight": "epic"},
    {"label": "+10 Νομίσματα", "type": "points", "value": 10, "weight": "common"},
    {"label": "-500 XP", "type": "xp", "value": -500, "weight": "uncommon"},
    {"label": "+500 Επαναφορά", "type": "xp", "value": 500, "weight": "rare"},
    {"label": "50 XP", "type": "xp", "value": 50, "weight": "common"},
]

# Βάρη: common=50%, uncommon=30%, rare=15%, epic=5%
WEIGHT_MAP = {"common": 50, "uncommon": 30, "rare": 15, "epic": 5}

MILESTONE_2000 = 2000
MILESTONE_3000 = 3000

DEFAULT_SHOP = {
    "hats": [
        {"id":"hat_01","name":"Μαγικό Καπέλο","icon":"🎩","price":50,"slot":"hat"},
        {"id":"hat_02","name":"Γυαλιά Ηλίου","icon":"😎","price":30,"slot":"glasses"},
        {"id":"hat_03","name":"Στέμμα","icon":"👑","price":100,"slot":"hat"},
    ],
    "outfits": [
        {"id":"outfit_01","name":"Κάπα Σούπερ Ήρωα","icon":"🦸","price":80,"slot":"outfit"},
        {"id":"outfit_02","name":"Πολύχρωμο Μπλουζάκι","icon":"👕","price":40,"slot":"outfit"},
        {"id":"outfit_03","name":"Πριγκιπικό Φόρεμα","icon":"👗","price":90,"slot":"outfit"},
    ],
    "skins": [
        {"id":"skin_01","name":"Χρυσό Λαμπραντόρ","icon":"🐕","price":200,"slot":"skin"},
        {"id":"skin_02","name":"Τιγρέ Γάτα","icon":"🐈","price":150,"slot":"skin"},
        {"id":"skin_03","name":"Κουνελάκι","icon":"🐰","price":120,"slot":"skin"},
    ],
    "backgrounds": [
        {"id":"bg_01","name":"Παραλία","icon":"🏖️","price":60,"slot":"background"},
        {"id":"bg_02","name":"Διάστημα","icon":"🌌","price":70,"slot":"background"},
        {"id":"bg_03","name":"Κάστρο","icon":"🏰","price":80,"slot":"background"},
    ]
}

AVATAR_ITEMS_POOL = [
    {"id":"avatar_01","name":"Ρόμπα Μάγου","icon":"🧙","price":0,"slot":"outfit"},
    {"id":"avatar_02","name":"Κάλυμμα Ματιού Πειρατή","icon":"🦜","price":0,"slot":"glasses"},
    {"id":"avatar_03","name":"Φτερά Αγγέλου","icon":"👼","price":0,"slot":"outfit"},
    {"id":"avatar_04","name":"Καπέλο Ντετέκτιβ","icon":"🕵️","price":0,"slot":"hat"},
    {"id":"avatar_05","name":"Στεφάνι Λουλουδιών","icon":"🌺","price":0,"slot":"hat"},
    {"id":"avatar_06","name":"Παπιγιόν","icon":"🎀","price":0,"slot":"outfit"},
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
            "missions":{},"last_mission_date":None,"ad_watch_count":0,"ad_scale_1_claimed":False,"ad_scale_2_claimed":False,
            "free_spins":0,"milestone_2000_reached":False,"milestone_3000_reached":False,
            "referral_code":str(uuid.uuid4())[:8],"referred_by":None,"referral_reward_claimed":False,
            "inventory":[],"equipped":{},"pet_skin":"🐱","pet_name":"Whiskers","background":None,"happiness":50,"food_items":0,
            "double_active":False
        }
    u = users[user_id]
    today = date.today().isoformat()
    if u.get("last_mission_date") != today:
        u["missions"] = {str(m["id"]):{"progress":0,"claimed":False} for m in DAILY_MISSIONS}
        u["ad_watch_count"] = 0; u["ad_scale_1_claimed"] = False; u["ad_scale_2_claimed"] = False
        u["last_mission_date"] = today
    u["level"] = max(1, (u.get("total_points",0)//POINTS_PER_LEVEL)+1)
    for field in ["missions","free_spins","milestone_2000_reached","milestone_3000_reached","ad_watch_count","stars","inventory","equipped","pet_skin","pet_name","background","happiness","food_items","xp","double_active"]:
        if field not in u:
            if field == "missions": u[field] = {}
            elif field in ("free_spins","stars","happiness","food_items","xp"): u[field] = 0
            elif field == "inventory": u[field] = []
            elif field == "equipped": u[field] = {}
            elif field in ("milestone_2000_reached","milestone_3000_reached","ad_scale_1_claimed","ad_scale_2_claimed","double_active"): u[field] = False
            elif field == "pet_skin": u[field] = "🐱"
            elif field == "pet_name": u[field] = "Whiskers"
            elif field == "background": u[field] = None
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
    all_items = []
    shop = read_json(SHOP_FILE)
    for cat in shop.values(): all_items.extend(cat)
    all_items.extend(AVATAR_ITEMS_POOL)
    for slot, item_id in user_data.get("equipped", {}).items():
        item = next((it for it in all_items if it["id"] == item_id), None)
        if item: equipped[slot] = item
    return equipped

def weighted_choice():
    total = sum(WEIGHT_MAP[p["weight"]] for p in WHEEL_PRIZES)
    r = random.uniform(0, total)
    upto = 0
    for i, p in enumerate(WHEEL_PRIZES):
        w = WEIGHT_MAP[p["weight"]]
        if upto + w >= r:
            return i
        upto += w
    return len(WHEEL_PRIZES)-1

@app.get("/board")
async def get_board(request: Request, userId: str):
    check_auth(request); u = get_user(userId)
    return {"total_points":u["total_points"],"stars":u.get("stars",0),"level":u["level"],"free_spins":u.get("free_spins",0),"next_level_points":u["level"]*POINTS_PER_LEVEL,"happiness":u.get("happiness",50),"double_active":u.get("double_active",False)}

@app.get("/missions")
async def get_missions(request: Request, userId: str):
    check_auth(request); u = get_user(userId)
    return {"missions":[{"id":m["id"],"description":m["description"],"target":m["target"],"progress":u.get("missions",{}).get(str(m["id"]),{}).get("progress",0),"reward_points":m["reward_points"],"claimed":u.get("missions",{}).get(str(m["id"]),{}).get("claimed",False)} for m in DAILY_MISSIONS]}

@app.post("/missions/update")
async def update_mission_progress(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); game = data.get("game",""); score = data.get("score",0); playtime = data.get("playtime",0); words = data.get("words",0)
    if not user_id: raise HTTPException(400, "Missing userId")
    u = get_user(user_id)
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        if mid not in u["missions"]: u["missions"][mid] = {"progress":0,"claimed":False}
        if m["type"]=="score" and m["game"]==game: u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress",0)+score)
        elif m["type"]=="playtime" and m["game"]==game: u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress",0)+playtime)
        elif m["type"]=="words_found" and m["game"]==game: u["missions"][mid]["progress"] = min(m["target"], u["missions"][mid].get("progress",0)+words)
    save_user(user_id, u); return {"status":"ok"}

@app.post("/missions/claim")
async def claim_mission(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); mission_id = str(data.get("missionId"))
    u = get_user(user_id)
    if mission_id not in u.get("missions",{}): raise HTTPException(404, "Mission not found")
    mission = u["missions"][mission_id]; mission_def = next((m for m in DAILY_MISSIONS if str(m["id"])==mission_id), None)
    if not mission_def or mission.get("progress",0)<mission_def["target"] or mission.get("claimed"): raise HTTPException(400, "Not completable")
    reward = mission_def["reward_points"]
    if u.get("double_active"): reward *= 2
    u["total_points"] = u.get("total_points",0)+reward
    u["level"] = max(1,(u["total_points"]//POINTS_PER_LEVEL)+1); mission["claimed"] = True
    save_user(user_id, u); return {"status":"ok","reward_points":reward}

@app.post("/ad-reward")
async def ad_reward(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId")
    if not user_id: raise HTTPException(400, "Missing userId")
    u = get_user(user_id)
    pts = AD_POINTS_PER_WATCH
    stars = AD_STARS_PER_WATCH
    if u.get("double_active"):
        pts *= 2
        stars *= 2
    u["free_spins"] = u.get("free_spins",0) + FREE_SPINS_1_AD
    u["total_points"] = u.get("total_points",0) + pts
    u["stars"] = u.get("stars",0) + stars
    u["level"] = max(1,(u["total_points"]//POINTS_PER_LEVEL)+1)
    save_user(user_id, u)
    return {"status":"ok","points_earned":pts,"stars_earned":stars,"free_spins":u["free_spins"]}

@app.post("/wheel/spin")
async def spin_wheel(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId")
    if not user_id: raise HTTPException(400, "Missing userId")
    u = get_user(user_id)
    if u.get("free_spins",0)<1: raise HTTPException(403, "Not enough free spins")
    u["free_spins"]-=1
    prize_index = weighted_choice()
    prize = WHEEL_PRIZES[prize_index].copy()
    multiplier = 2 if u.get("double_active") else 1
    if prize["type"]=="points":
        val = prize["value"]*multiplier
        u["total_points"] = u.get("total_points",0)+val
        prize["label"] = f"+{val} Νομίσματα"
    elif prize["type"]=="stars":
        val = prize["value"]*multiplier
        u["stars"] = max(0, u.get("stars",0)+val)
        prize["label"] = f"{val} Αστέρια"
    elif prize["type"]=="free_spin":
        u["free_spins"] = u.get("free_spins",0)+prize["value"]
    elif prize["type"]=="xp":
        val = prize["value"]*multiplier
        u["xp"] = u.get("xp",0)+val
        prize["label"] = f"{val} XP"
        if val<0: u["xp"] = max(0, u["xp"])
    elif prize["type"]=="double":
        u["double_active"] = True
        prize["label"] = "Διπλοί Πόντοι Ενεργοί!"
    elif prize["type"]=="level_up":
        u["level"] = u.get("level",1)+1
        u["xp"] = 0
        prize["label"] = "Επίπεδο UP!"
    elif prize["type"]=="cosmetic":
        available = [it for it in AVATAR_ITEMS_POOL if it["id"] not in u.get("inventory",[])]
        if available:
            item = random.choice(available); u.setdefault("inventory",[]).append(item["id"])
            prize["label"] = item["name"]; prize["item"] = item
        else: prize["type"] = "stars"; prize["value"] = 20; prize["label"] = "20 Αστέρια"; u["stars"] = u.get("stars",0)+20
    u["level"] = max(1, (u.get("total_points",0)//POINTS_PER_LEVEL)+1)
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
    u = get_user(user_id)
    if u.get("double_active"): points *= 2
    u["total_points"] = u.get("total_points",0)+points
    u["level"] = max(1,(u["total_points"]//POINTS_PER_LEVEL)+1)
    save_user(user_id, u); return {"status":"ok","added":points}

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
    equipped_items = get_equipped_items(u)
    return {"pet_emoji":u.get("pet_skin","🐱"),"pet_name":u.get("pet_name","Whiskers"),"happiness":u.get("happiness",50),"food_items":u.get("food_items",0),"inventory":u.get("inventory",[]),"equipped":u.get("equipped",{}),"equipped_items":equipped_items}

@app.get("/inventory")
async def get_inventory(request: Request, userId: str):
    check_auth(request); u = get_user(userId)
    shop = read_json(SHOP_FILE); all_items = [it for cat in shop.values() for it in cat] + AVATAR_ITEMS_POOL
    inv = [it for it in all_items if it["id"] in u.get("inventory",[])]
    return {"items":inv,"equipped":list(u.get("equipped",{}).values())}

@app.get("/shop")
async def get_shop(): return read_json(SHOP_FILE)

@app.post("/buy")
async def buy_item(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); item_id = data.get("itemId")
    if not user_id or not item_id: raise HTTPException(400, "Missing params")
    u = get_user(user_id)
    item = get_item_by_id(item_id)
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
    equipped_items = get_equipped_items(u)
    return {"status":"ok","equipped_items":equipped_items}

@app.post("/unequip")
async def unequip_item(request: Request):
    check_auth(request); data = await request.json(); user_id = data.get("userId"); item_id = data.get("itemId")
    if not user_id or not item_id: raise HTTPException(400, "Missing params")
    u = get_user(user_id)
    item = get_item_by_id(item_id)
    if not item: raise HTTPException(404, "Item not found")
    slot = item.get("slot","outfit")
    if slot=="skin": u["pet_skin"] = "🐱"
    elif slot=="background": u["background"] = None
    else: u.get("equipped",{}).pop(slot, None)
    save_user(user_id, u)
    equipped_items = get_equipped_items(u)
    return {"status":"ok","equipped_items":equipped_items}

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
    return {"status":"ok","message":"Yum! +5 πόντοι","happiness":u["happiness"]}
