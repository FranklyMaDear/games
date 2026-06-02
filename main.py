from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type", "X-API-Key"],
)

API_KEY = "m0n3t4g_s3cur3_k3y_2026"
POINTS_LOG_FILE = "points_log.json"
USERS_FILE = "users.json"

def read_json(filename):
    if not os.path.exists(filename):
        return [] if filename == POINTS_LOG_FILE else {}
    with open(filename, "r") as f:
        return json.load(f)

def write_json(filename, data):
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

@app.post("/log")
async def log_points(request: Request):
    client_key = request.headers.get("X-API-Key")
    if client_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")

    data = await request.json()
    user_id = data.get("userId", "unknown")
    game = data.get("game", "unknown")
    points_earned = data.get("points", 0)
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

    return {
        "status": "ok",
        "total_points": users[user_id],
        "total_logs": len(logs)
    }

@app.get("/points/{user_id}")
async def get_points(user_id: str, request: Request):
    client_key = request.headers.get("X-API-Key")
    if client_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    users = read_json(USERS_FILE)
    return {"userId": user_id, "total_points": users.get(user_id, 0)}
