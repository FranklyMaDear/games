from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import random
from datetime import date, timedelta
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

API_KEY = os.environ.get("API_KEY", "m0n3t4g_s3cur3_k3y_2026")
USERS_FILE = "users.json"
POINTS_PER_LEVEL = 500

# ---------- DAILY MISSIONS ----------
DAILY_MISSIONS = [
    {"id": "daily_chess", "description": "Play 3 matches of Chess", "target": 3, "game": "Chess", "reward_type": "points", "reward_value": 20, "reward_label": "+20 Points", "link": "https://t.me/Franklygames_bot/chess"},
    {"id": "daily_sudoku", "description": "Play 3 grids of Sudoku", "target": 3, "game": "Sudoku", "reward_type": "stars", "reward_value": 10, "reward_label": "+10 Stars", "link": "https://t.me/Franklygames_bot/sudoku"},
    {"id": "daily_connect4", "description": "Play 3 matches of Connect 4", "target": 3, "game": "Connect 4", "reward_type": "free_spin", "reward_value": 2, "reward_label": "+2 Free Spins", "link": "https://t.me/Franklygames_bot/connectfour"},
    {"id": "daily_animalwhack", "description": "Play 3 rounds of Animal Whack", "target": 3, "game": "Animal Whack", "reward_type": "points", "reward_value": 30, "reward_label": "+30 Points", "link": "https://t.me/Franklygames_bot/animals"},
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

def get_user(user_id: str) -> dict:
    users = read_json(USERS_FILE)
    if user_id not in users:
        users[user_id] = {
            "total_points": 0,
            "stars": 0,
            "level": 1,
            "display_name": user_id[:12],
            "free_spins": 5,
            "daily_missions": {},
            "last_daily_reset": None,
        }
    u = users[user_id]
    today = date.today().isoformat()
    if u.get("last_daily_reset") != today:
        u["daily_missions"] = {m["id"]: {"progress": 0, "claimed": False} for m in DAILY_MISSIONS}
        u["last_daily_reset"] = today
    u["level"] = max(1, (u.get("total_points", 0) // POINTS_PER_LEVEL) + 1)
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

# ---------- ENDPOINTS ----------
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
    }

@app.get("/missions")
async def get_missions(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    result = []
    for m in DAILY_MISSIONS:
        md = u.get("daily_missions", {}).get(m["id"], {"progress": 0, "claimed": False})
        result.append({
            "id": m["id"],
            "description": m["description"],
            "target": m["target"],
            "reward_type": m["reward_type"],
            "reward_value": m["reward_value"],
            "reward_label": m["reward_label"],
            "link": m["link"],
            "progress": md.get("progress", 0),
            "claimed": md.get("claimed", False),
            "completed": md.get("progress", 0) >= m["target"],
        })
    return {"missions": result}

@app.post("/missions/update")
async def update_mission_progress(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "")
    played = data.get("played", False)
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")
    u = get_user(user_id)
    for m in DAILY_MISSIONS:
        mid = m["id"]
        if mid not in u["daily_missions"]:
            u["daily_missions"][mid] = {"progress": 0, "claimed": False}
        if m["game"] == game and played:
            u["daily_missions"][mid]["progress"] = min(m["target"], u["daily_missions"][mid].get("progress", 0) + 1)
    save_user(user_id, u)
    return {"status": "ok"}

# NEW: Κεντρικό Endpoint για αυτόνομη κλήση από οποιοδήποτε παιχνίδι
@app.post("/api/game-complete")
async def api_game_complete(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    game_name = data.get("game")  # Πρέπει να ταιριάζει με το "game" στο DAILY_MISSIONS (π.χ. "Connect 4")
    
    if not user_id or not game_name:
        raise HTTPException(status_code=400, detail="Missing userId or game name")
        
    u = get_user(user_id)
    updated = False
    current_progress = 0
    target_value = 0
    
    for m in DAILY_MISSIONS:
        mid = m["id"]
        if mid not in u["daily_missions"]:
            u["daily_missions"][mid] = {"progress": 0, "claimed": False}
            
        if m["game"] == game_name:
            u["daily_missions"][mid]["progress"] = min(m["target"], u["daily_missions"][mid].get("progress", 0) + 1)
            current_progress = u["daily_missions"][mid]["progress"]
            target_value = m["target"]
            updated = True
            
    if not updated:
        raise HTTPException(status_code=404, detail=f"Game '{game_name}' not found in daily missions")
        
    save_user(user_id, u)
    logger.info(f"User {user_id} registered progress for {game_name}. Progress: {current_progress}/{target_value}")
    
    return {
        "status": "ok",
        "game": game_name,
        "progress": current_progress,
        "target": target_value
    }

@app.post("/missions/claim")
async def claim_mission(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    mission_id = data.get("missionId")
    if not user_id or not mission_id:
        raise HTTPException(status_code=400, detail="Missing params")
    u = get_user(user_id)
    md = u["daily_missions"].get(mission_id)
    if not md:
        raise HTTPException(status_code=404, detail="Mission not found")
    mdef = next((m for m in DAILY_MISSIONS if m["id"] == mission_id), None)
    if not mdef or md.get("progress", 0) < mdef["target"] or md.get("claimed"):
        raise HTTPException(status_code=400, detail="Not completable")
    md["claimed"] = True
    if mdef["reward_type"] == "points":
        u["total_points"] = u.get("total_points", 0) + mdef["reward_value"]
        u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    elif mdef["reward_type"] == "stars":
        u["stars"] = u.get("stars", 0) + mdef["reward_value"]
    elif mdef["reward_type"] == "free_spin":
        u["free_spins"] = u.get("free_spins", 0) + mdef["reward_value"]
    save_user(user_id, u)
    return {"status": "ok", "reward": mdef["reward_value"]}

@app.get("/game-stats")
async def get_game_stats(request: Request, userId: str):
    check_auth(request)
    u = get_user(userId)
    daily = u.get("daily_missions", {})
    return {
        "chess_played_today": daily.get("daily_chess", {}).get("progress", 0),
        "sudoku_played_today": daily.get("daily_sudoku", {}).get("progress", 0),
        "connect4_played_today": daily.get("daily_connect4", {}).get("progress", 0),
        "animalwhack_played_today": daily.get("daily_animalwhack", {}).get("progress", 0),
    }

@app.post("/add-points")
async def add_points(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    points = data.get("points", 0)
    u = get_user(user_id)
    u["total_points"] = u.get("total_points", 0) + points
    u["level"] = max(1, (u["total_points"] // POINTS_PER_LEVEL) + 1)
    save_user(user_id, u)
    return {"status": "ok", "added": points}

@app.post("/add-stars")
async def add_stars(request: Request):
    check_auth(request)
    data = await request.json()
    user_id = data.get("userId")
    stars = data.get("stars", 0)
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
    u = get_user(user_id)
    u["free_spins"] = u.get("free_spins", 0) + spins
    save_user(user_id, u)
    return {"status": "ok", "free_spins": u["free_spins"]}

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
    u = get_user(user_id)
    u["display_name"] = display_name
    save_user(user_id, u)
    return {"status": "ok", "display_name": display_name}
