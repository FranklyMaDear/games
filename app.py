from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import time
from datetime import datetime, timedelta
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("games_backend")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Σε παραγωγή μπορείς να περιορίσεις στο domain σου
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],
)

# API Key from environment (Hugging Face Secrets)
API_KEY = os.environ.get("API_KEY", "m0n3t4g_s3cur3_k3y_2026")  # fallback για τοπική ανάπτυξη

# Secret key for admin endpoint (ξεχωριστό από το API key για το frontend)
ADMIN_SECRET = os.environ.get("ADMIN_SECRET", "SuperSecretAdminKey2026")

# Files
POINTS_LOG_FILE = "points_log.json"
USERS_FILE = "users.json"

# Rate limiting: επιτρέπουμε max 1 απονομή πόντων ανά λεπτό ανά χρήστη
RATE_LIMIT_SECONDS = 60   # 1 λεπτό

# Συνάρτηση ασφαλούς ανάγνωσης/εγγραφής JSON
def read_json(filename):
    if not os.path.exists(filename):
        return [] if filename == POINTS_LOG_FILE else {}
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except Exception:
        return [] if filename == POINTS_LOG_FILE else {}

def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

# ------------------------------------------------------------
# Rate limiting & validation
# ------------------------------------------------------------
def check_rate_limit(user_id: str):
    """Επιστρέφει True αν ο χρήστης μπορεί να λάβει πόντους, αλλιώς False."""
    logs = read_json(POINTS_LOG_FILE)
    # Βρες την τελευταία καταχώρηση για αυτόν τον χρήστη
    last_time = None
    for entry in reversed(logs):
        if entry.get("userId") == user_id:
            last_time = entry.get("timestamp")
            break
    if last_time:
        try:
            last_dt = datetime.fromisoformat(last_time)
            if datetime.utcnow() - last_dt < timedelta(seconds=RATE_LIMIT_SECONDS):
                return False
        except Exception:
            pass
    return True

# ------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------
@app.post("/log")
async def log_points(request: Request):
    # 1. API Key validation
    client_key = request.headers.get("X-API-Key")
    if not client_key or client_key != API_KEY:
        logger.warning(f"Invalid API key attempt: {client_key}")
        raise HTTPException(status_code=403, detail="Invalid API Key")

    # 2. Parse body
    data = await request.json()
    user_id = data.get("userId")
    game = data.get("game", "unknown")
    points_earned = data.get("points", 0)

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing userId")

    # 3. Validate points (επιτρεπτές μόνο οι 10 μονάδες ανά κλήση)
    if points_earned != 10:
        logger.warning(f"User {user_id} attempted to add {points_earned} points (only 10 allowed).")
        raise HTTPException(status_code=400, detail="Invalid points amount")

    # 4. Rate limit check
    if not check_rate_limit(user_id):
        logger.warning(f"Rate limit exceeded for user {user_id}")
        raise HTTPException(status_code=429, detail="Too many requests. Please wait before earning more points.")

    # 5. Ενημέρωση logs & users
    timestamp = datetime.utcnow().isoformat()
    logs = read_json(POINTS_LOG_FILE)
    logs.append({
        "userId": user_id,
        "game": game,
        "points": points_earned,
        "timestamp": timestamp
    })
    write_json(POINTS_LOG_FILE, logs)

    users = read_json(USERS_FILE)
    if user_id not in users:
        users[user_id] = 0
    users[user_id] += points_earned
    write_json(USERS_FILE, users)

    logger.info(f"Points added: {user_id} +{points_earned} (total: {users[user_id]})")
    return {
        "status": "ok",
        "total_points": users[user_id],
        "total_logs": len(logs)
    }

@app.get("/points/{user_id}")
async def get_points(user_id: str, request: Request):
    client_key = request.headers.get("X-API-Key")
    if not client_key or client_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    users = read_json(USERS_FILE)
    return {"userId": user_id, "total_points": users.get(user_id, 0)}

@app.get("/admin/winners")
async def admin_winners(key: str = Query(...)):
    """Επιστρέφει όλους τους χρήστες με 1000+ πόντους (προστατευμένο με admin secret)."""
    if key != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    users = read_json(USERS_FILE)
    winners = {uid: pts for uid, pts in users.items() if pts >= 1000}
    # Ταξινόμηση κατά πόντους (φθίνουσα)
    sorted_winners = sorted(winners.items(), key=lambda x: x[1], reverse=True)
    return {
        "winners": [{"userId": uid, "points": pts} for uid, pts in sorted_winners],
        "total_winners": len(sorted_winners)
    }
