from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import random
import uuid
from datetime import datetime, timedelta, date
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
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "SuperSecretAdminKey2026")

USERS_FILE = "users.json"
POINTS_LOG_FILE = "points_log.json"

# ---------- ΣΤΑΘΕΡΕΣ ----------
POINTS_PER_LEVEL = 1000

# Missions
DAILY_MISSIONS = [
    {"id": 1, "description": "Play Crack The Code for 3 minutes", "target": 3, "reward_points": 50, "type": "playtime", "game": "Crack The Code"},
    {"id": 2, "description": "Score 500 pts in Code Kids", "target": 500, "reward_points": 80, "type": "score", "game": "Crack The Code Kids"},
    {"id": 3, "description": "Find 10 words in Code Words", "target": 10, "reward_points": 100, "type": "words_found", "game": "Crack The Code Words"},
]

# Σκάλες διαφημίσεων
AD_SCALE_1_TARGET = 5
AD_SCALE_1_BONUS = 100
AD_SCALE_2_TARGET = 10
AD_SCALE_2_BONUS = 200
AD_POINTS_PER_WATCH = 20

# Free spins από διαφημίσεις (μόνο 1 Ad -> 5 spins)
FREE_SPINS_1_AD = 5

# Τροχός με 12 βραβεία (εμφανή / κρυφά, θετικά / αρνητικά)
WHEEL_PRIZES = [
    {"label": "+5 pts",      "points": 5},      # εμφανές
    {"label": "💀 Joker",    "points": 0},      # κρυφό
    {"label": "+10 pts",     "points": 10},     # εμφανές
    {"label": "-1 pt",       "points": -1},     # κρυφό
    {"label": "+20 pts",     "points": 20},     # εμφανές
    {"label": "-2 pts",      "points": -2},     # κρυφό
    {"label": "+5 pts",      "points": 5},      # εμφανές
    {"label": "💀 Joker",    "points": 0},      # κρυφό
    {"label": "+10 pts",     "points": 10},     # εμφανές
    {"label": "-1 pt",       "points": -1},     # κρυφό
    {"label": "+20 pts",     "points": 20},     # εμφανές
    {"label": "-2 pts",      "points": -2}      # κρυφό
]

# Milestones
MILESTONE_2000 = 2000
MILESTONE_3000 = 3000
TALLY_URL = "https://tally.so/r/44jy95?transparentBackground=1"

# ---------- JSON helpers ----------
def read_json(filename):
    if not os.path.exists(filename):
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
            "level": 1,
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
            "referral_reward_claimed": False
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
    
    for field in ["missions", "free_spins", "milestone_2000_reached", "milestone_3000_reached", "ad_watch_count"]:
        if field not in user_data:
            if field == "missions":
                user_data[field] = {}
            elif field == "free_spins":
                user_data[field] = 0
            elif field in ("milestone_2000_reached", "milestone_3000_reached", "ad_scale_1_claimed", "ad_scale_2_claimed"):
                user_data[field] = False
            elif field == "ad_watch_count":
                user_data[field] = 0
    
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
    user_data = get_user(userId)
    return {
        "total_points": user_data["total_points"],
        "level": user_data["level"],
        "free_spins": user_data.get("free_spins", 0),
        "next_level_points": user_data["level"] * POINTS_PER_LEVEL,
        "milestone_2000_reached": user_data.get("milestone_2000_reached", False),
        "milestone_3000_reached": user_data.get("milestone_3000_reached", False),
        "tally_url": TALLY_URL
    }

@app.get("/missions")
async def get_missions(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    missions_status = []
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        mission_data = user_data.get("missions", {}).get(mid, {"progress": 0, "claimed": False})
        missions_status.append({
            "id": m["id"],
            "description": m["description"],
            "target": m["target"],
            "progress": mission_data.get("progress", 0),
            "reward_points": m["reward_points"],
            "claimed": mission_data.get("claimed", False)
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

    user_data = get_user(user_id)
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        if mid not in user_data["missions"]:
            user_data["missions"][mid] = {"progress": 0, "claimed": False}
        if m["type"] == "score" and m["game"] == game:
            user_data["missions"][mid]["progress"] = min(m["target"], user_data["missions"][mid].get("progress", 0) + score)
        elif m["type"] == "playtime" and m["game"] == game:
            user_data["missions"][mid]["progress"] = min(m["target"], user_data["missions"][mid].get("progress", 0) + playtime)
        elif m["type"] == "words_found" and m["game"] == game:
            user_data["missions"][mid]["progress"] = min(m["target"], user_data["missions"][mid].get("progress", 0) + words)
    
    save_user(user_id, user_data)
    return {"status": "ok"}

@app.post("/missions/claim")
async def claim_mission(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    mission_id = str(data.get("missionId"))

    user_data = get_user(user_id)
    if mission_id not in user_data.get("missions", {}):
        raise HTTPException(status_code=404, detail="Mission not found")
    
    mission = user_data["missions"][mission_id]
    mission_def = next((m for m in DAILY_MISSIONS if str(m["id"]) == mission_id), None)
    if not mission_def or mission.get("progress", 0) < mission_def["target"] or mission.get("claimed"):
        raise HTTPException(status_code=400, detail="Mission not completable or already claimed")

    user_data["total_points"] = user_data.get("total_points", 0) + mission_def["reward_points"]
    user_data["level"] = max(1, (user_data["total_points"] // POINTS_PER_LEVEL) + 1)
    mission["claimed"] = True
    
    if user_data["total_points"] >= MILESTONE_2000 and not user_data.get("milestone_2000_reached"):
        user_data["milestone_2000_reached"] = True
    if user_data["total_points"] >= MILESTONE_3000 and not user_data.get("milestone_3000_reached"):
        user_data["milestone_3000_reached"] = True
    
    save_user(user_id, user_data)
    return {
        "status": "ok",
        "reward_points": mission_def["reward_points"],
        "total_points": user_data["total_points"],
        "level": user_data["level"],
        "milestone_2000_reached": user_data["milestone_2000_reached"],
        "milestone_3000_reached": user_data["milestone_3000_reached"]
    }

@app.post("/ad-watch")
async def ad_watch(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    
    user_data = get_user(user_id)
    user_data["ad_watch_count"] = user_data.get("ad_watch_count", 0) + 1
    
    points_earned = AD_POINTS_PER_WATCH
    bonus = 0
    
    if user_data["ad_watch_count"] >= AD_SCALE_1_TARGET and not user_data.get("ad_scale_1_claimed"):
        bonus += AD_SCALE_1_BONUS
        user_data["ad_scale_1_claimed"] = True
    if user_data["ad_watch_count"] >= AD_SCALE_2_TARGET and not user_data.get("ad_scale_2_claimed"):
        bonus += AD_SCALE_2_BONUS
        user_data["ad_scale_2_claimed"] = True
    
    total_earned = points_earned + bonus
    user_data["total_points"] = user_data.get("total_points", 0) + total_earned
    user_data["level"] = max(1, (user_data["total_points"] // POINTS_PER_LEVEL) + 1)
    
    if user_data["total_points"] >= MILESTONE_2000 and not user_data.get("milestone_2000_reached"):
        user_data["milestone_2000_reached"] = True
    if user_data["total_points"] >= MILESTONE_3000 and not user_data.get("milestone_3000_reached"):
        user_data["milestone_3000_reached"] = True
    
    save_user(user_id, user_data)
    
    return {
        "status": "ok",
        "points_earned": total_earned,
        "total_points": user_data["total_points"],
        "ad_watch_count": user_data["ad_watch_count"],
        "level": user_data["level"],
        "bonus": bonus,
        "milestone_2000_reached": user_data["milestone_2000_reached"],
        "milestone_3000_reached": user_data["milestone_3000_reached"]
    }

@app.post("/ad-free-spins-1")
async def ad_free_spins_1(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    
    user_data = get_user(user_id)
    user_data["free_spins"] = user_data.get("free_spins", 0) + FREE_SPINS_1_AD
    save_user(user_id, user_data)
    return {"status": "ok", "free_spins": user_data["free_spins"]}

@app.post("/wheel/spin")
async def spin_wheel(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    
    user_data = get_user(user_id)
    if user_data.get("free_spins", 0) < 1:
        raise HTTPException(status_code=403, detail="Not enough free spins")
    
    user_data["free_spins"] -= 1
    
    # Επιλογή τυχαίου βραβείου και του index του
    prize_index = random.randint(0, len(WHEEL_PRIZES)-1)
    prize = WHEEL_PRIZES[prize_index]
    
    # Εφαρμογή πόντων
    pts = prize.get("points", 0)
    if pts > 0:
        user_data["total_points"] = user_data.get("total_points", 0) + pts
    elif pts < 0:
        # αφαίρεση χωρίς να πάει κάτω από 0
        user_data["total_points"] = max(0, user_data.get("total_points", 0) + pts)
    
    # Εφαρμογή free spins (αν υπάρχουν)
    spins = prize.get("free_spins", 0)
    if spins > 0:
        user_data["free_spins"] = user_data.get("free_spins", 0) + spins
    elif spins < 0:
        user_data["free_spins"] = max(0, user_data.get("free_spins", 0) + spins)
    
    # Ανανέωση level
    user_data["level"] = max(1, (user_data["total_points"] // POINTS_PER_LEVEL) + 1)
    
    # Milestones
    if user_data["total_points"] >= MILESTONE_2000 and not user_data.get("milestone_2000_reached"):
        user_data["milestone_2000_reached"] = True
    if user_data["total_points"] >= MILESTONE_3000 and not user_data.get("milestone_3000_reached"):
        user_data["milestone_3000_reached"] = True
    
    save_user(user_id, user_data)
    
    return {
        "status": "ok",
        "prize": prize,
        "prizeIndex": prize_index,
        "total_points": user_data["total_points"],
        "free_spins": user_data["free_spins"],
        "level": user_data["level"],
        "milestone_2000_reached": user_data["milestone_2000_reached"],
        "milestone_3000_reached": user_data["milestone_3000_reached"]
    }

@app.get("/ad-status")
async def ad_status(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    return {
        "ad_watch_count": user_data.get("ad_watch_count", 0),
        "ad_scale_1_target": AD_SCALE_1_TARGET,
        "ad_scale_1_claimed": user_data.get("ad_scale_1_claimed", False),
        "ad_scale_1_bonus": AD_SCALE_1_BONUS,
        "ad_scale_2_target": AD_SCALE_2_TARGET,
        "ad_scale_2_claimed": user_data.get("ad_scale_2_claimed", False),
        "ad_scale_2_bonus": AD_SCALE_2_BONUS,
        "points_per_ad": AD_POINTS_PER_WATCH,
        "free_spins": user_data.get("free_spins", 0)
    }

@app.get("/points/{user_id}")
async def get_points(user_id: str, request: Request):
    check_auth(request)
    user_data = get_user(user_id)
    return {
        "userId": user_id,
        "total_points": user_data["total_points"],
        "level": user_data["level"]
    }

@app.post("/add-points")
async def add_points(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "unknown")
    points = data.get("points", 0)

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    if not isinstance(points, (int, float)) or points <= 0:
        raise HTTPException(status_code=400, detail="Points must be a positive number")
    
    user_data = get_user(user_id)
    user_data["total_points"] = user_data.get("total_points", 0) + points
    user_data["level"] = max(1, (user_data["total_points"] // POINTS_PER_LEVEL) + 1)
    
    if user_data["total_points"] >= MILESTONE_2000 and not user_data.get("milestone_2000_reached"):
        user_data["milestone_2000_reached"] = True
    if user_data["total_points"] >= MILESTONE_3000 and not user_data.get("milestone_3000_reached"):
        user_data["milestone_3000_reached"] = True
    
    save_user(user_id, user_data)
    
    logs = read_json(POINTS_LOG_FILE)
    logs.append({
        "userId": user_id, "game": game, "points": points,
        "timestamp": datetime.utcnow().isoformat(), "source": "game_score"
    })
    write_json(POINTS_LOG_FILE, logs)
    
    return {
        "status": "ok",
        "added": points,
        "total_points": user_data["total_points"],
        "level": user_data["level"]
    }

@app.post("/log")
async def log_game(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "unknown")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    
    logs = read_json(POINTS_LOG_FILE)
    logs.append({
        "userId": user_id, "game": game, "points": 0,
        "timestamp": datetime.utcnow().isoformat(), "source": "free_play"
    })
    write_json(POINTS_LOG_FILE, logs)
    return {"status": "ok", "message": "Game launched (free play)"}

@app.get("/leaderboard")
async def get_leaderboard(request: Request, limit: int = 20):
    check_auth(request)
    users = read_json(USERS_FILE)
    lb = []
    for uid, data in users.items():
        lb.append({"userId": uid, "points": data.get("total_points", 0)})
    lb.sort(key=lambda x: x["points"], reverse=True)
    return {"leaderboard": lb[:limit]}
