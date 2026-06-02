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

MAX_ENERGY = 300
ENERGY_COST_PER_GAME = 5
ENERGY_REGEN_PER_SECOND = 1 / 60          # 1 energy/min
ENERGY_REWARD_AD = 50
DAILY_BONUS_POINTS = 100
DAILY_BONUS_ENERGY = 30

STREAK_MULTIPLIERS = {7: 2, 30: 3, 90: 5, 180: 10}

RATE_LIMIT_GAME = 60
RATE_LIMIT_AD_REFILL = 300
RATE_LIMIT_DAILY = 86400
RATE_LIMIT_GIFT = 3600
RATE_LIMIT_WHEEL = 3600

POINTS_PER_LEVEL = 500

DAILY_MISSIONS = [
    {"id": 1, "description": "Play 1 game", "target": 1, "reward_points": 50},
    {"id": 2, "description": "Play 3 games", "target": 3, "reward_points": 150},
    {"id": 3, "description": "Claim daily bonus", "target": 1, "reward_points": 30},
]

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

# ---------- Energy ----------
def update_energy(user_data: dict) -> dict:
    now = datetime.utcnow()
    last_update_str = user_data.get("last_energy_update")
    if last_update_str:
        last_update = datetime.fromisoformat(last_update_str)
        delta = (now - last_update).total_seconds()
        regen = int(delta * ENERGY_REGEN_PER_SECOND)
        if regen > 0:
            user_data["current_energy"] = min(MAX_ENERGY, user_data["current_energy"] + regen)
    else:
        user_data["current_energy"] = MAX_ENERGY
    user_data["last_energy_update"] = now.isoformat()
    return user_data

def get_user(user_id: str) -> dict:
    users = read_json(USERS_FILE)
    if user_id not in users:
        users[user_id] = {
            "total_points": 0,
            "current_energy": MAX_ENERGY,
            "max_energy": MAX_ENERGY,
            "last_energy_update": None,
            "streak": 0,
            "last_login_date": None,
            "last_daily_claim": None,
            "last_gift_claim": None,
            "last_wheel_spin": None,
            "last_ad_refill": None,
            "last_game": None,
            "games_played_today": 0,
            "last_game_date": None,
            "missions": {},
            "referral_code": str(uuid.uuid4())[:8],
            "referred_by": None,
            "referral_reward_claimed": False
        }
    user_data = update_energy(users[user_id])
    today = date.today().isoformat()
    last_game_date = user_data.get("last_game_date")
    if last_game_date != today:
        user_data["games_played_today"] = 0
        user_data["last_game_date"] = today
        user_data["missions"] = {}
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

def check_rate_limit(user_data: dict, field: str, limit_seconds: int):
    last = user_data.get(field)
    if last:
        last_dt = datetime.fromisoformat(last)
        if datetime.utcnow() - last_dt < timedelta(seconds=limit_seconds):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

# ---------- Multiplier & Level ----------
def get_multiplier(streak: int) -> int:
    mult = 1
    for days, m in sorted(STREAK_MULTIPLIERS.items()):
        if streak >= days:
            mult = m
    return mult

def get_level(points: int) -> int:
    return points // POINTS_PER_LEVEL

def get_level_progress(points: int) -> float:
    level_points = points % POINTS_PER_LEVEL
    return level_points / POINTS_PER_LEVEL

def update_streak(user_data: dict) -> dict:
    today = date.today().isoformat()
    last_login = user_data.get("last_login_date")
    if last_login == today:
        return user_data
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if last_login == yesterday:
        user_data["streak"] = user_data.get("streak", 0) + 1
    else:
        user_data["streak"] = 1
    user_data["last_login_date"] = today
    return user_data

# ---------- Missions ----------
def init_daily_missions(user_data: dict):
    if not user_data.get("missions"):
        user_data["missions"] = {}
        for m in DAILY_MISSIONS:
            user_data["missions"][str(m["id"])] = {"progress": 0, "completed": False, "claimed": False}
    return user_data

def update_mission_progress(user_data: dict, action: str, count: int = 1):
    user_data = init_daily_missions(user_data)
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        if (m["id"] == 1 or m["id"] == 2) and action == "game":
            user_data["missions"][mid]["progress"] = min(m["target"], user_data["missions"][mid].get("progress", 0) + count)
        elif m["id"] == 3 and action == "daily_claim":
            user_data["missions"][mid]["progress"] = 1
        if user_data["missions"][mid]["progress"] >= m["target"]:
            user_data["missions"][mid]["completed"] = True
    return user_data

# =========================== ENDPOINTS ===========================

@app.post("/log")
async def log_game(request: Request):
    """Παίζει παιχνίδι – καταναλώνει ενέργεια, δίνει πόντους."""
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "unknown")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")

    user_data = get_user(user_id)
    check_rate_limit(user_data, "last_game", RATE_LIMIT_GAME)

    if user_data["current_energy"] < ENERGY_COST_PER_GAME:
        raise HTTPException(status_code=403, detail="Not enough energy")

    multiplier = get_multiplier(user_data.get("streak", 0))
    user_data["current_energy"] -= ENERGY_COST_PER_GAME
    user_data["last_energy_update"] = datetime.utcnow().isoformat()
    user_data["last_game"] = datetime.utcnow().isoformat()
    user_data["games_played_today"] = user_data.get("games_played_today", 0) + 1
    points_earned = 10 * multiplier
    user_data["total_points"] = user_data.get("total_points", 0) + points_earned

    user_data = update_mission_progress(user_data, "game")

    save_user(user_id, user_data)

    logs = read_json(POINTS_LOG_FILE)
    logs.append({
        "userId": user_id, "game": game, "points": points_earned,
        "timestamp": datetime.utcnow().isoformat()
    })
    write_json(POINTS_LOG_FILE, logs)

    return {
        "status": "ok",
        "points_earned": points_earned,
        "total_points": user_data["total_points"],
        "current_energy": user_data["current_energy"],
        "multiplier": multiplier,
        "level": get_level(user_data["total_points"])
    }

@app.post("/score")
async def submit_score(request: Request):
    """Υποβολή σκορ απευθείας από το παιχνίδι (χωρίς κατανάλωση ενέργειας)."""
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "unknown")
    score = data.get("score", 0)
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    if not isinstance(score, (int, float)) or score <= 0:
        raise HTTPException(status_code=400, detail="Invalid score")

    user_data = get_user(user_id)
    user_data["total_points"] = user_data.get("total_points", 0) + score
    save_user(user_id, user_data)

    logs = read_json(POINTS_LOG_FILE)
    logs.append({
        "userId": user_id, "game": game, "points": score,
        "timestamp": datetime.utcnow().isoformat(), "source": "game_submit"
    })
    write_json(POINTS_LOG_FILE, logs)

    return {
        "status": "ok",
        "score_added": score,
        "total_points": user_data["total_points"],
        "level": get_level(user_data["total_points"])
    }

@app.post("/add-points")
async def add_points(request: Request):
    """Δέχεται σκορ από παιχνίδια (postMessage) και προσθέτει πόντους χωρίς κατανάλωση ενέργειας."""
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "unknown")
    points = data.get("points", 0)

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    if not isinstance(points, (int, float)) or points <= 0:
        raise HTTPException(status_code=400, detail="Invalid points value")

    user_data = get_user(user_id)
    user_data["total_points"] = user_data.get("total_points", 0) + points
    save_user(user_id, user_data)

    logs = read_json(POINTS_LOG_FILE)
    logs.append({
        "userId": user_id,
        "game": game,
        "points": points,
        "timestamp": datetime.utcnow().isoformat(),
        "source": "game_score_postmessage"
    })
    write_json(POINTS_LOG_FILE, logs)

    return {
        "status": "ok",
        "added": points,
        "total": user_data["total_points"],
        "level": get_level(user_data["total_points"])
    }

@app.get("/energy")
async def get_energy(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    return {"current_energy": user_data["current_energy"], "max_energy": user_data["max_energy"]}

@app.post("/refill")
async def refill_energy(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    user_data = get_user(user_id)
    check_rate_limit(user_data, "last_ad_refill", RATE_LIMIT_AD_REFILL)
    user_data["current_energy"] = min(MAX_ENERGY, user_data["current_energy"] + ENERGY_REWARD_AD)
    user_data["last_energy_update"] = datetime.utcnow().isoformat()
    user_data["last_ad_refill"] = datetime.utcnow().isoformat()
    save_user(user_id, user_data)
    return {"status": "ok", "current_energy": user_data["current_energy"]}

@app.post("/daily_claim")
async def daily_claim(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    user_data = get_user(user_id)
    check_rate_limit(user_data, "last_daily_claim", RATE_LIMIT_DAILY)
    user_data = update_streak(user_data)
    user_data["last_daily_claim"] = datetime.utcnow().isoformat()
    multiplier = get_multiplier(user_data["streak"])
    bonus_points = DAILY_BONUS_POINTS * multiplier
    user_data["total_points"] = user_data.get("total_points", 0) + bonus_points
    user_data["current_energy"] = min(MAX_ENERGY, user_data["current_energy"] + DAILY_BONUS_ENERGY)
    user_data["last_energy_update"] = datetime.utcnow().isoformat()
    user_data = update_mission_progress(user_data, "daily_claim")
    save_user(user_id, user_data)
    return {
        "status": "ok",
        "bonus_points": bonus_points,
        "bonus_energy": DAILY_BONUS_ENERGY,
        "streak": user_data["streak"],
        "total_points": user_data["total_points"],
        "current_energy": user_data["current_energy"]
    }

@app.post("/gift")
async def random_gift(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    user_data = get_user(user_id)
    check_rate_limit(user_data, "last_gift_claim", RATE_LIMIT_GIFT)
    reward_type = random.choice(["points", "energy"])
    if reward_type == "points":
        amount = random.randint(50, 200)
        user_data["total_points"] = user_data.get("total_points", 0) + amount
    else:
        amount = random.randint(20, 60)
        user_data["current_energy"] = min(MAX_ENERGY, user_data["current_energy"] + amount)
    user_data["last_gift_claim"] = datetime.utcnow().isoformat()
    user_data["last_energy_update"] = datetime.utcnow().isoformat()
    save_user(user_id, user_data)
    return {"status": "ok", "reward_type": reward_type, "amount": amount,
            "total_points": user_data["total_points"], "current_energy": user_data["current_energy"]}

@app.post("/wheel")
async def lucky_wheel(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    user_data = get_user(user_id)
    check_rate_limit(user_data, "last_wheel_spin", RATE_LIMIT_WHEEL)
    prizes = [
        {"type": "points", "amount": 10},
        {"type": "points", "amount": 50},
        {"type": "energy", "amount": 20},
        {"type": "points", "amount": 5},
        {"type": "points", "amount": 100},
        {"type": "energy", "amount": 30},
        {"type": "points", "amount": 200},
        {"type": "energy", "amount": 15}
    ]
    prize = random.choice(prizes)
    if prize["type"] == "points":
        user_data["total_points"] = user_data.get("total_points", 0) + prize["amount"]
    else:
        user_data["current_energy"] = min(MAX_ENERGY, user_data["current_energy"] + prize["amount"])
    user_data["last_wheel_spin"] = datetime.utcnow().isoformat()
    user_data["last_energy_update"] = datetime.utcnow().isoformat()
    save_user(user_id, user_data)
    return {"status": "ok", "prize": prize, "total_points": user_data["total_points"],
            "current_energy": user_data["current_energy"]}

@app.get("/streak")
async def get_streak(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    return {"streak": user_data.get("streak", 0)}

@app.get("/board")
async def get_board(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    total_points = user_data.get("total_points", 0)
    level = get_level(total_points)
    progress = get_level_progress(total_points)
    return {
        "total_points": total_points,
        "level": level,
        "progress": progress,
        "next_level_points": (level + 1) * POINTS_PER_LEVEL
    }

@app.get("/shop")
async def shop(request: Request):
    check_auth(request)
    return {"items": [{"id":1,"name":"Double Points (1h)","cost":200},
                      {"id":2,"name":"Energy Refill","cost":150}]}

@app.get("/season")
async def season_info(request: Request):
    check_auth(request)
    now = datetime.utcnow()
    week_number = now.isocalendar()[1]
    days_until_monday = (7 - now.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    return {
        "season": week_number,
        "ends_in_days": days_until_monday,
        "rewards": ["🥇 Top 1: 5000 pts", "🥈 Top 2: 3000 pts", "🥉 Top 3: 1000 pts"]
    }

@app.get("/leaderboard")
async def leaderboard(request: Request, limit: int = 20):
    check_auth(request)
    users = read_json(USERS_FILE)
    sorted_users = sorted(users.items(), key=lambda x: x[1].get("total_points", 0), reverse=True)[:limit]
    leaderboard = []
    for uid, info in sorted_users:
        leaderboard.append({
            "userId": uid,
            "points": info.get("total_points", 0),
            "level": get_level(info.get("total_points", 0)),
            "streak": info.get("streak", 0)
        })
    return {"leaderboard": leaderboard}

@app.get("/missions")
async def get_missions(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    user_data = init_daily_missions(user_data)
    # Save to ensure missions exist
    save_user(userId, user_data)
    missions_status = []
    for m in DAILY_MISSIONS:
        mid = str(m["id"])
        status = user_data["missions"].get(mid, {"progress": 0, "completed": False, "claimed": False})
        missions_status.append({
            "id": m["id"],
            "description": m["description"],
            "target": m["target"],
            "progress": status["progress"],
            "completed": status["completed"],
            "claimed": status.get("claimed", False),
            "reward_points": m["reward_points"]
        })
    return {"missions": missions_status}

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
    if not mission.get("completed") or mission.get("claimed"):
        raise HTTPException(status_code=400, detail="Mission not completable or already claimed")
    mission_def = next((m for m in DAILY_MISSIONS if str(m["id"]) == mission_id), None)
    if mission_def:
        user_data["total_points"] = user_data.get("total_points", 0) + mission_def["reward_points"]
        mission["claimed"] = True
        save_user(user_id, user_data)
        return {"status": "ok", "reward_points": mission_def["reward_points"], "total_points": user_data["total_points"]}
    else:
        raise HTTPException(status_code=400, detail="Invalid mission")

@app.get("/referral")
async def get_referral(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    return {"referral_code": user_data.get("referral_code", ""),
            "referred_by": user_data.get("referred_by"),
            "referral_reward_claimed": user_data.get("referral_reward_claimed", False)}

@app.post("/referral/apply")
async def apply_referral(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    referral_code = data.get("referralCode")
    if not user_id or not referral_code:
        raise HTTPException(status_code=400, detail="Missing userId or referralCode")
    user_data = get_user(user_id)
    if user_data.get("referred_by"):
        raise HTTPException(status_code=400, detail="Referral already applied")
    users = read_json(USERS_FILE)
    referred_by = None
    for uid, info in users.items():
        if info.get("referral_code") == referral_code and uid != user_id:
            referred_by = uid
            break
    if not referred_by:
        raise HTTPException(status_code=404, detail="Invalid referral code")
    user_data["referred_by"] = referred_by
    user_data["total_points"] = user_data.get("total_points", 0) + 50
    save_user(user_id, user_data)
    inviter_data = get_user(referred_by)
    if not inviter_data.get("referral_reward_claimed", False):
        inviter_data["total_points"] = inviter_data.get("total_points", 0) + 100
        inviter_data["referral_reward_claimed"] = True
        save_user(referred_by, inviter_data)
    return {"status": "ok", "bonus_points": 50, "total_points": user_data["total_points"]}

@app.get("/points/{user_id}")
async def get_points(user_id: str, request: Request):
    client_key = request.headers.get("X-API-Key")
    if not client_key or client_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    users = read_json(USERS_FILE)
    return {"userId": user_id, "total_points": users.get(user_id, {}).get("total_points", 0)}

@app.get("/admin/winners")
async def admin_winners(key: str = Query(...)):
    if key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    users = read_json(USERS_FILE)
    winners = {uid: info.get("total_points", 0) for uid, info in users.items() if info.get("total_points", 0) >= 1000}
    sorted_winners = sorted(winners.items(), key=lambda x: x[1], reverse=True)
    return {"winners": [{"userId": uid, "points": pts} for uid, pts in sorted_winners], "total": len(sorted_winners)}
