from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import random
from datetime import datetime, timedelta, date
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("gamified_backend")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],
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
            "last_game": None
        }
    user_data = update_energy(users[user_id])
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

# ---------- Multiplier ----------
def get_multiplier(streak: int) -> int:
    mult = 1
    for days, m in sorted(STREAK_MULTIPLIERS.items()):
        if streak >= days:
            mult = m
    return mult

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
    points_earned = 10 * multiplier
    user_data["total_points"] = user_data.get("total_points", 0) + points_earned

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
        "multiplier": multiplier
    }

@app.get("/energy")
async def get_energy(request: Request, userId: str):
    check_auth(request)
    user_data = get_user(userId)
    return {"current_energy": user_data["current_energy"], "max_energy": user_data["max_energy"]}

@app.post("/refill")
async def refill_energy(request: Request):
    """Αναπλήρωση ενέργειας μέσω rewarded ad."""
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
        {"type": "points", "amount": random.randint(10, 50)},
        {"type": "points", "amount": random.randint(100, 500)},
        {"type": "energy", "amount": random.randint(30, 100)}
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
    """Board progress: 20 steps, κάθε 100 πόντοι = 1 βήμα."""
    check_auth(request)
    user_data = get_user(userId)
    total_points = user_data.get("total_points", 0)
    steps_completed = total_points // 100
    total_steps = 20
    return {
        "total_points": total_points,
        "steps_completed": min(steps_completed, total_steps),
        "total_steps": total_steps
    }

@app.get("/shop")
async def shop(request: Request):
    check_auth(request)
    return {"items": [{"id":1,"name":"Double Points (1h)","cost":200},
                      {"id":2,"name":"Energy Refill","cost":150}]}

@app.get("/season")
async def season(request: Request):
    check_auth(request)
    return {"season":1,"ends_in_days":12,"rewards":["skin1","badge"]}

@app.get("/rewards")
async def rewards_list(request: Request):
    check_auth(request)
    return {"rewards":[{"name":"Daily Login Bonus","desc":"Claim every 24h"},
                       {"name":"Weekly Top 10","desc":"Extra points for top players"}]}

@app.get("/admin/winners")
async def admin_winners(key: str = Query(...)):
    if key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    users = read_json(USERS_FILE)
    winners = {uid: info.get("total_points", 0) for uid, info in users.items()
               if info.get("total_points", 0) >= 1000}
    sorted_winners = sorted(winners.items(), key=lambda x: x[1], reverse=True)
    return {"winners": [{"userId": uid, "points": pts} for uid, pts in sorted_winners],
            "total": len(sorted_winners)}
