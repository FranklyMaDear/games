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

# ---------- ΝΕΟ ΣΥΣΤΗΜΑ (ΔΩΡΕΑΝ ΠΑΙΧΝΙΔΙ, MISSIONS, ADS) ----------
# Το παιχνίδι είναι πλέον ΔΩΡΕΑΝ – δεν αφαιρείται ενέργεια
# Οι πόντοι κερδίζονται μόνο από missions και ad watches

# Ρυθμίσεις για ads (σκάλες)
AD_WATCH_REWARD_POINTS = 20        # Πόντοι ανά διαφήμιση
AD_SCALE_1_TARGET = 5              # 5 διαφημίσεις
AD_SCALE_1_BONUS = 100             # Bonus πόντοι
AD_SCALE_2_TARGET = 10             # 10 διαφημίσεις
AD_SCALE_2_BONUS = 200             # Bonus πόντοι

# Ορόσημα πόντων
MILESTONE_2000 = 2000
MILESTONE_3000 = 3000
TALLY_URL = "https://tally.so/r/44jy95?transparentBackground=1"

# Daily missions (από τα παιχνίδια)
DAILY_MISSIONS = [
    {"id": 1, "description": "Play Crack The Code for 3 minutes", "target": 3, "reward_points": 50, "type": "playtime", "game": "Crack The Code"},
    {"id": 2, "description": "Score 500 pts in Code Kids", "target": 500, "reward_points": 80, "type": "score", "game": "Crack The Code Kids"},
    {"id": 3, "description": "Find 10 words in Code Words", "target": 10, "reward_points": 100, "type": "words_found", "game": "Crack The Code Words"},
]

POINTS_PER_LEVEL = 500

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
            "total_xp": 0,
            "level": 1,
            "streak": 0,
            "last_login_date": None,
            "last_daily_claim": None,
            "missions": {},
            "last_mission_date": None,
            "ad_watch_count": 0,           # συνολικές διαφημίσεις σήμερα
            "ad_scale_1_claimed": False,
            "ad_scale_2_claimed": False,
            "last_ad_watch": None,
            "milestone_2000_reached": False,
            "milestone_3000_reached": False,
            "referral_code": str(uuid.uuid4())[:8],
            "referred_by": None,
            "referral_reward_claimed": False
        }
    user_data = users[user_id]
    today = date.today().isoformat()
    
    # Καθημερινή επαναφορά
    last_date = user_data.get("last_mission_date")
    if last_date != today:
        user_data["missions"] = {str(m["id"]): {"progress": 0, "claimed": False} for m in DAILY_MISSIONS}
        user_data["ad_watch_count"] = 0
        user_data["ad_scale_1_claimed"] = False
        user_data["ad_scale_2_claimed"] = False
        user_data["last_mission_date"] = today
    
    if "missions" not in user_data:
        user_data["missions"] = {}
    if "total_points" not in user_data:
        user_data["total_points"] = 0
    if "level" not in user_data:
        user_data["level"] = 1
    
    # Ενημέρωση level βάσει πόντων
    user_data["level"] = (user_data["total_points"] // POINTS_PER_LEVEL) + 1
    
    users[user_id] = user_data
    write_json(USERS_FILE, users)
    return user_data

def save_user(user_id: str, user_data: dict):
    users = read_json(USERS_FILE)
    users[user_id] = user_data
    write_json(USERS_FILE, users)

# ---------- Auth ----------
def check_auth(request: Request):
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

# =========================== ENDPOINTS ===========================

@app.get("/points/{user_id}")
async def get_points(user_id: str, request: Request):
    check_auth(request)
    user_data = get_user(user_id)
    return {
        "userId": user_id,
        "total_points": user_data["total_points"],
        "level": user_data["level"],
        "milestone_2000_reached": user_data.get("milestone_2000_reached", False),
        "milestone_3000_reached": user_data.get("milestone_3000_reached", False)
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
    """Τα παιχνίδια στέλνουν score/playtime για να ενημερωθούν οι αποστολές."""
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "")
    score = data.get("score", 0)
    playtime = data.get("playtime", 0)
    words = data.get("words", 0)

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
    user_data["level"] = (user_data["total_points"] // POINTS_PER_LEVEL) + 1
    mission["claimed"] = True
    
    # Έλεγχος οροσήμων
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
    """Ο χρήστης είδε μία διαφήμιση. Αυξάνει τον μετρητή και δίνει πόντους/κλίμακες."""
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    
    user_data = get_user(user_id)
    user_data["ad_watch_count"] = user_data.get("ad_watch_count", 0) + 1
    user_data["last_ad_watch"] = datetime.utcnow().isoformat()
    
    points_earned = AD_WATCH_REWARD_POINTS
    bonus = 0
    
    # Έλεγχος σκαλών
    if user_data["ad_watch_count"] >= AD_SCALE_1_TARGET and not user_data.get("ad_scale_1_claimed"):
        bonus += AD_SCALE_1_BONUS
        user_data["ad_scale_1_claimed"] = True
    if user_data["ad_watch_count"] >= AD_SCALE_2_TARGET and not user_data.get("ad_scale_2_claimed"):
        bonus += AD_SCALE_2_BONUS
        user_data["ad_scale_2_claimed"] = True
    
    total_earned = points_earned + bonus
    user_data["total_points"] = user_data.get("total_points", 0) + total_earned
    user_data["level"] = (user_data["total_points"] // POINTS_PER_LEVEL) + 1
    
    # Έλεγχος οροσήμων
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
        "points_per_ad": AD_WATCH_REWARD_POINTS
    }

@app.get("/board")
async def get_board(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    return {
        "total_points": user_data["total_points"],
        "level": user_data["level"],
        "next_level_points": user_data["level"] * POINTS_PER_LEVEL,
        "milestone_2000_reached": user_data.get("milestone_2000_reached", False),
        "milestone_3000_reached": user_data.get("milestone_3000_reached", False),
        "tally_url": TALLY_URL
    }

# ---------- Endpoints κληρονομιάς (διατηρούνται για συμβατότητα) ----------

@app.get("/energy")
async def get_energy(request: Request, userId: str):
    # Δεν χρησιμοποιείται πλέον, επιστρέφει dummy
    return {"current_energy": 999, "max_energy": 999}

@app.post("/log")
async def log_game(request: Request):
    # Δεν αφαιρεί ενέργεια πλέον, απλά καταγράφει
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "unknown")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    
    user_data = get_user(user_id)
    logs = read_json(POINTS_LOG_FILE)
    logs.append({
        "userId": user_id, "game": game, "points": 0,
        "timestamp": datetime.utcnow().isoformat(), "source": "free_play"
    })
    write_json(POINTS_LOG_FILE, logs)
    
    return {"status": "ok", "message": "Game launched (free play)"}
