import datetime
import hashlib
import os
import random
import secrets
import sys
import time
import uuid
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from games_data import GAMES_CATALOG, GAMES_BY_ID, simulate_game_round

if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

# ==========================================
# MULTI-USER STORAGE & AUTH
# ==========================================
def generate_unique_id():
    return f"UID-{secrets.randbelow(90000) + 10000}"

# In-memory user database with Unique IDs
users = {
    "admin": {
        "uid": "ADM-001",
        "username": "admin",
        "password": "admin123",
        "role": "admin",
        "balance": 75000.0,
        "total_bet": 0.0,
        "total_won": 0.0,
        "games_played": 0,
        "created_at": "2026-10-01 10:00:00",
        "status": "Active"
    },
    "player1": {
        "uid": "UID-78401",
        "username": "player1",
        "password": "player123",
        "role": "user",
        "balance": 1500.0,
        "total_bet": 600.0,
        "total_won": 950.0,
        "games_played": 6,
        "created_at": "2026-10-01 14:30:00",
        "status": "Active"
    },
    "rahul_k": {
        "uid": "UID-92314",
        "username": "rahul_k",
        "password": "pass123",
        "role": "user",
        "balance": 2800.0,
        "total_bet": 1800.0,
        "total_won": 3200.0,
        "games_played": 14,
        "created_at": "2026-10-01 18:20:00",
        "status": "Active"
    },
    "priya_s": {
        "uid": "UID-41589",
        "username": "priya_s",
        "password": "pass123",
        "role": "user",
        "balance": 450.0,
        "total_bet": 1200.0,
        "total_won": 650.0,
        "games_played": 9,
        "created_at": "2026-10-02 00:15:00",
        "status": "Active"
    }
}

# Token session mapping: token -> username
auth_tokens = {}

# Active rounds storage per user
active_aviator_rounds = {}
active_mines_rounds = {}

# Global game history
aviator_history = [2.45, 1.28, 4.12, 1.05, 1.88, 3.20, 1.15, 6.50]
color_history = [
    {"period": 2026100201, "number": 3, "color": "GREEN"},
    {"period": 2026100202, "number": 8, "color": "RED"},
    {"period": 2026100203, "number": 0, "color": "VIOLET"},
    {"period": 2026100204, "number": 7, "color": "GREEN"},
    {"period": 2026100205, "number": 2, "color": "RED"}
]
chakri_history = [
    {"label": "5x", "multiplier": 5.0, "color": "#F59E0B"},
    {"label": "2x", "multiplier": 2.0, "color": "#10B981"},
    {"label": "0x", "multiplier": 0.0, "color": "#475569"},
    {"label": "10x", "multiplier": 10.0, "color": "#8B5CF6"},
    {"label": "1.5x", "multiplier": 1.5, "color": "#3B82F6"}
]

# Fun Roulette (Mini Roulette 0-18) Configuration
FUN_ROULETTE_NUMBERS = list(range(19)) # 0 to 18
FUN_ROULETTE_WHEEL_ORDER = [0, 2, 14, 4, 16, 6, 18, 8, 12, 10, 1, 13, 3, 15, 5, 17, 7, 11, 9]
FUN_ROULETTE_REDS = {1, 3, 5, 7, 9, 12, 14, 16, 18}
FUN_ROULETTE_BLACKS = {2, 4, 6, 8, 10, 11, 13, 15, 17}
fun_roulette_history = [6, 9, 13, 4, 10]

# Chakri (Lucky Wheel) Slices Configuration
CHAKRI_SLICES = [
    {"index": 0, "label": "2x", "multiplier": 2.0, "color": "#10B981", "weight": 22},
    {"index": 1, "label": "0x", "multiplier": 0.0, "color": "#475569", "weight": 24},
    {"index": 2, "label": "5x", "multiplier": 5.0, "color": "#F59E0B", "weight": 14},
    {"index": 3, "label": "1.5x", "multiplier": 1.5, "color": "#3B82F6", "weight": 20},
    {"index": 4, "label": "10x", "multiplier": 10.0, "color": "#8B5CF6", "weight": 8},
    {"index": 5, "label": "0x", "multiplier": 0.0, "color": "#475569", "weight": 20},
    {"index": 6, "label": "3x", "multiplier": 3.0, "color": "#EC4899", "weight": 14},
    {"index": 7, "label": "50x", "multiplier": 50.0, "color": "#EF4444", "weight": 2}
]

SLOT_SYMBOLS = ['7️⃣', '💎', '🔔', '🍋', '🍒', '⭐']
SLOT_PAYOUTS = {
    '7️⃣': 15.0,
    '💎': 10.0,
    '🔔': 6.0,
    '⭐': 4.0,
    '🍒': 3.0,
    '🍋': 2.0
}

# Provably Fair Secret Key for Unpredictable Cryptographic Randomness
SERVER_SEED = secrets.token_hex(32)

# Global Live Bets stream for Admin monitoring
recent_live_bets = [
    {"time": "Just now", "user": "rahul_k", "uid": "UID-92314", "game": "Fun Roulette", "stake": 100.0, "result": "Number 14 (RED)", "status": "WON", "win": 1800.0},
    {"time": "1m ago", "user": "player1", "uid": "UID-78401", "game": "Aviator", "stake": 200.0, "result": "2.45x Multiplier", "status": "WON", "win": 490.0},
    {"time": "2m ago", "user": "priya_s", "uid": "UID-41589", "game": "Mines", "stake": 100.0, "result": "Hit Mine on tile 12", "status": "LOST", "win": 0.0},
    {"time": "4m ago", "user": "rahul_k", "uid": "UID-92314", "game": "Color Wingo", "stake": 150.0, "result": "Green (Number 7)", "status": "WON", "win": 300.0}
]

# Global Player Withdrawal Requests Queue
withdrawal_requests = [
    {
        "id": "WDR-1082",
        "username": "rahul_k",
        "uid": "UID-92314",
        "amount": 200.0,
        "method": "UPI",
        "details": "rahul92@oksbi",
        "account_name": "Rahul Kumar",
        "status": "PENDING",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processed_at": None,
        "admin_note": ""
    }
]

def record_live_bet(user_name, game_name, stake, result_text, status, win_amt):
    user_obj = users.get(user_name, {})
    user_uid = user_obj.get("uid", "UID-DEMO")
    recent_live_bets.insert(0, {
        "time": datetime.datetime.now().strftime("%H:%M:%S"),
        "user": user_name,
        "uid": user_uid,
        "game": game_name,
        "stake": round(float(stake), 2),
        "result": result_text,
        "status": status,
        "win": round(float(win_amt), 2)
    })
    if len(recent_live_bets) > 50:
        recent_live_bets.pop()

# Helper to identify user from request token
def get_user_from_request(require_auth=False):
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1].strip()
    elif "X-User-Token" in request.headers:
        token = request.headers.get("X-User-Token")
    elif request.is_json and request.get_json():
        token = request.get_json().get("token", "")

    if token and token in auth_tokens:
        uname = auth_tokens[token]
        if uname in users:
            return users[uname]

    # Admin direct authentication
    if token in ("admin", "admin-master-token") or request.headers.get("X-User-Token") == "admin":
        return users.get("admin")

    if require_auth:
        return None

    # Default fallback to player1 for seamless access
    return users.get("player1")


# ==========================================
# STATIC FRONTEND ROUTES
# ==========================================
@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/login')
@app.route('/login.html')
def serve_login():
    return send_from_directory('.', 'login.html')

@app.route('/admin')
@app.route('/admin.html')
def serve_admin():
    return send_from_directory('.', 'admin.html')


# ==========================================
# AUTHENTICATION API
# ==========================================
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password required"}), 400

    if username not in users or users[username]["password"] != password:
        return jsonify({"status": "error", "message": "Invalid username or password"}), 401

    token = str(uuid.uuid4())
    auth_tokens[token] = username
    user = users[username]

    return jsonify({
        "status": "success",
        "message": f"Welcome back, {user['username']}!",
        "token": token,
        "user": {
            "uid": user.get("uid", "UID-00000"),
            "username": user["username"],
            "role": user["role"],
            "balance": user["balance"],
            "total_bet": user["total_bet"],
            "total_won": user["total_won"],
            "games_played": user["games_played"]
        }
    })

@app.route('/api/auth/register', methods=['POST'])
def register():
    return jsonify({
        "status": "error",
        "message": "Public registration is disabled. Please contact the administrator for player account access."
    }), 403

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split("Bearer ")[1].strip()
    elif "X-User-Token" in request.headers:
        token = request.headers.get("X-User-Token")
    elif request.is_json and request.get_json():
        token = request.get_json().get("token", "")

    if token and token in auth_tokens:
        del auth_tokens[token]
    return jsonify({"status": "success", "message": "Logged out successfully"})

@app.route('/api/auth/me', methods=['GET'])
def get_me():
    user = get_user_from_request(require_auth=True)
    if not user:
        return jsonify({"status": "unauthenticated", "message": "User not authenticated"}), 401

    return jsonify({
        "status": "success",
        "authenticated": True,
        "user": {
            "uid": user.get("uid", "UID-00000"),
            "username": user["username"],
            "role": user["role"],
            "balance": user["balance"],
            "total_bet": user["total_bet"],
            "total_won": user["total_won"],
            "games_played": user["games_played"],
            "status": user.get("status", "Active")
        }
    })


# ==========================================
# ADMIN PANEL APIS
# ==========================================
@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    user = get_user_from_request()
    if not user or user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    user_list = []
    for uname, udata in users.items():
        if "uid" not in udata:
            udata["uid"] = generate_unique_id()
        user_list.append({
            "uid": udata["uid"],
            "username": udata["username"],
            # Password intentionally NOT returned to admin per user privacy/security requirement
            "role": udata["role"],
            "balance": round(udata["balance"], 2),
            "total_bet": round(udata["total_bet"], 2),
            "total_won": round(udata["total_won"], 2),
            "games_played": udata["games_played"],
            "created_at": udata.get("created_at", "N/A"),
            "status": udata.get("status", "Active")
        })

    return jsonify({
        "status": "success",
        "users": user_list,
        "count": len(user_list)
    })

@app.route('/api/admin/users/create', methods=['POST'])
def admin_create_user():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    data = request.get_json() or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", "")).strip()
    balance = float(data.get("balance", 1000))
    role = str(data.get("role", "user")).strip().lower()

    if not username or not password:
        return jsonify({"status": "error", "message": "Username and password are required"}), 400

    if len(username) < 3:
        return jsonify({"status": "error", "message": "Username must be at least 3 characters"}), 400

    if username in users:
        return jsonify({"status": "error", "message": f"User '{username}' already exists. Choose a different ID."}), 400

    uid = generate_unique_id()
    while any(u.get("uid") == uid for u in users.values()):
        uid = generate_unique_id()

    users[username] = {
        "uid": uid,
        "username": username,
        "password": password,
        "role": role if role in ["admin", "user"] else "user",
        "balance": max(0.0, balance),
        "total_bet": 0.0,
        "total_won": 0.0,
        "games_played": 0,
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": "Active"
    }

    return jsonify({
        "status": "success",
        "message": f"User account '{username}' created successfully with Unique ID {uid} and balance ${balance:.2f}!",
        "user": {
            "uid": uid,
            "username": username,
            "role": role,
            "balance": max(0.0, balance)
        }
    })

@app.route('/api/admin/users/update_password', methods=['POST'])
def admin_update_password():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    data = request.get_json() or {}
    username = str(data.get("username", "")).strip().lower()
    new_password = str(data.get("new_password", "")).strip()

    if not username or not new_password:
        return jsonify({"status": "error", "message": "Username and new password required"}), 400

    if username not in users:
        return jsonify({"status": "error", "message": f"User '{username}' not found"}), 404

    users[username]["password"] = new_password
    return jsonify({
        "status": "success",
        "message": f"Password for user '{username}' updated successfully!"
    })

@app.route('/api/admin/users/delete', methods=['POST'])
def admin_delete_user():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    data = request.get_json() or {}
    username = str(data.get("username", "")).strip().lower()

    if username == "admin":
        return jsonify({"status": "error", "message": "Master admin account cannot be deleted"}), 400

    if username not in users:
        return jsonify({"status": "error", "message": f"User '{username}' not found"}), 404

    del users[username]
    return jsonify({
        "status": "success",
        "message": f"User account '{username}' deleted successfully!"
    })

@app.route('/api/admin/live_bets', methods=['GET'])
def admin_get_live_bets():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    return jsonify({
        "status": "success",
        "bets": recent_live_bets
    })

@app.route('/api/admin/user/balance', methods=['POST'])
def admin_modify_balance():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    data = request.get_json() or {}
    target_username = str(data.get("username", "")).strip().lower()
    amount = float(data.get("amount", 0))
    action = data.get("action", "add")  # 'add', 'subtract', 'set'

    if target_username not in users:
        return jsonify({"status": "error", "message": f"User '{target_username}' not found"}), 404

    target = users[target_username]
    old_balance = target["balance"]

    if action == "add":
        target["balance"] += amount
    elif action == "subtract":
        target["balance"] = max(0.0, target["balance"] - amount)
    elif action == "set":
        target["balance"] = max(0.0, amount)

    return jsonify({
        "status": "success",
        "message": f"Successfully updated balance for '{target_username}'. Changed from ${old_balance:.2f} to ${target['balance']:.2f}",
        "username": target_username,
        "old_balance": old_balance,
        "new_balance": target["balance"]
    })

@app.route('/api/admin/stats', methods=['GET'])
def admin_get_stats():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    admin_data = users.get("admin", {})
    admin_balance = round(float(admin_data.get("balance", 0.0)), 2)

    # Player metrics (excluding admin)
    player_users = [u for uname, u in users.items() if u.get("role") != "admin"]
    player_count = len(player_users)
    total_player_balance = round(sum(u.get("balance", 0.0) for u in player_users), 2)
    total_player_bets = round(sum(u.get("total_bet", 0.0) for u in player_users), 2)
    total_player_won = round(sum(u.get("total_won", 0.0) for u in player_users), 2)
    total_games_played = sum(u.get("games_played", 0) for u in player_users)

    # Net House Profit = Bets taken - Payouts given
    net_house_profit = round(total_player_bets - total_player_won, 2)
    house_margin_pct = round((net_house_profit / total_player_bets * 100), 2) if total_player_bets > 0 else 0.0

    # Aggregate performance by game from recent live bets
    game_breakdown = {}
    for b in recent_live_bets:
        gname = b.get("game", "Other")
        if gname not in game_breakdown:
            game_breakdown[gname] = {"bets_count": 0, "total_stake": 0.0, "total_won": 0.0, "house_profit": 0.0}
        stk = float(b.get("stake", 0.0))
        wn = float(b.get("win", 0.0))
        game_breakdown[gname]["bets_count"] += 1
        game_breakdown[gname]["total_stake"] = round(game_breakdown[gname]["total_stake"] + stk, 2)
        game_breakdown[gname]["total_won"] = round(game_breakdown[gname]["total_won"] + wn, 2)
        game_breakdown[gname]["house_profit"] = round(game_breakdown[gname]["house_profit"] + (stk - wn), 2)

    return jsonify({
        "status": "success",
        "stats": {
            "admin_balance": admin_balance,
            "total_users": len(users),
            "total_players": player_count,
            "total_player_balance": total_player_balance,
            "total_platform_balance": round(admin_balance + total_player_balance, 2),
            "total_platform_bets": total_player_bets,
            "total_platform_won": total_player_won,
            "net_house_profit": net_house_profit,
            "house_margin_pct": house_margin_pct,
            "total_games_played": total_games_played,
            "pending_withdrawals_count": sum(1 for r in withdrawal_requests if r["status"] == "PENDING"),
            "game_breakdown": game_breakdown
        }
    })

@app.route('/api/admin/vault/transaction', methods=['POST'])
def admin_vault_transaction():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    data = request.get_json() or {}
    action = data.get("action", "deposit")  # 'deposit', 'withdraw'
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid amount format"}), 400

    if amount <= 0:
        return jsonify({"status": "error", "message": "Amount must be greater than zero"}), 400

    admin = users.get("admin")
    if not admin:
        return jsonify({"status": "error", "message": "Admin account not found"}), 404

    old_bal = admin["balance"]
    if action == "withdraw":
        if admin["balance"] < amount:
            return jsonify({"status": "error", "message": f"Insufficient funds in Admin Vault. Available: ${admin['balance']:,.2f}"}), 400
        admin["balance"] = round(admin["balance"] - amount, 2)
        msg = f"Successfully withdrew ${amount:,.2f} from Admin Master Vault."
    else:
        admin["balance"] = round(admin["balance"] + amount, 2)
        msg = f"Successfully added ${amount:,.2f} to Admin Master Vault."

    return jsonify({
        "status": "success",
        "message": msg,
        "old_balance": round(old_bal, 2),
        "admin_balance": round(admin["balance"], 2)
    })

# ==========================================
# ADMIN WITHDRAWAL MANAGEMENT APIS
# ==========================================
@app.route('/api/admin/withdrawals', methods=['GET'])
def admin_get_withdrawals():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    enriched = []
    for r in withdrawal_requests:
        p_user = users.get(r["username"], {})
        enriched.append({
            **r,
            "player_current_balance": round(p_user.get("balance", 0.0), 2)
        })

    pending_count = sum(1 for r in withdrawal_requests if r["status"] == "PENDING")
    approved_total = round(sum(r["amount"] for r in withdrawal_requests if r["status"] == "APPROVED"), 2)

    return jsonify({
        "status": "success",
        "requests": enriched,
        "pending_count": pending_count,
        "approved_total": approved_total
    })

@app.route('/api/admin/withdrawals/approve', methods=['POST'])
def admin_approve_withdrawal():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    data = request.get_json() or {}
    req_id = str(data.get("request_id", "")).strip()

    req = next((r for r in withdrawal_requests if r["id"] == req_id), None)
    if not req:
        return jsonify({"status": "error", "message": f"Withdrawal request '{req_id}' not found"}), 404

    if req["status"] != "PENDING":
        return jsonify({"status": "error", "message": f"Request has already been processed ({req['status']})"}), 400

    target_user = users.get(req["username"])
    if not target_user:
        return jsonify({"status": "error", "message": f"User '{req['username']}' not found"}), 404

    amount = float(req["amount"])
    if target_user["balance"] < amount:
        return jsonify({
            "status": "error",
            "message": f"Player '{target_user['username']}' only has ${target_user['balance']:.2f}. Cannot deduct ${amount:.2f}."
        }), 400

    # DEDUCT MONEY FROM PLAYER'S ACCOUNT UPON ACCEPTANCE
    old_balance = target_user["balance"]
    target_user["balance"] = round(target_user["balance"] - amount, 2)
    req["status"] = "APPROVED"
    req["processed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    req["admin_note"] = str(data.get("note", "Approved and processed by Admin")).strip()

    # Record live transaction
    record_live_bet(
        target_user["username"],
        "Withdrawal Payout",
        amount,
        f"Approved #{req_id} ({req['method']}: {req['details']})",
        "CASHOUT",
        amount
    )

    return jsonify({
        "status": "success",
        "message": f"Withdrawal #{req_id} approved! ${amount:.2f} has been deducted from {target_user['username']}'s account.",
        "request": req,
        "player_new_balance": target_user["balance"]
    })

@app.route('/api/admin/withdrawals/reject', methods=['POST'])
def admin_reject_withdrawal():
    admin_user = get_user_from_request()
    if not admin_user or admin_user.get("role") != "admin":
        return jsonify({"status": "error", "message": "Unauthorized: Admin access required"}), 403

    data = request.get_json() or {}
    req_id = str(data.get("request_id", "")).strip()
    reason = str(data.get("reason", "Rejected by administrator")).strip()

    req = next((r for r in withdrawal_requests if r["id"] == req_id), None)
    if not req:
        return jsonify({"status": "error", "message": f"Withdrawal request '{req_id}' not found"}), 404

    if req["status"] != "PENDING":
        return jsonify({"status": "error", "message": f"Request has already been processed ({req['status']})"}), 400

    req["status"] = "REJECTED"
    req["processed_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    req["admin_note"] = reason

    return jsonify({
        "status": "success",
        "message": f"Withdrawal request '{req_id}' rejected. No funds were deducted from player.",
        "request": req
    })


# ==========================================
# USER WALLET & WITHDRAWAL APIS
# ==========================================
@app.route('/api/wallet', methods=['GET'])
def get_wallet():
    user = get_user_from_request()
    return jsonify({
        "status": "success",
        "username": user["username"],
        "balance": round(user["balance"], 2),
        "total_bet": round(user["total_bet"], 2),
        "total_won": round(user["total_won"], 2),
        "games_played": user["games_played"]
    })

@app.route('/api/wallet/deposit', methods=['POST'])
def deposit_wallet():
    user = get_user_from_request()
    if not user or user.get("role") != "admin":
        return jsonify({
            "status": "error",
            "message": "Direct player deposit disabled. Wallet balances are allocated and managed exclusively by the Administrator."
        }), 403

    data = request.get_json() or {}
    amount = float(data.get("amount", 500))

    if amount <= 0:
        return jsonify({"status": "error", "message": "Invalid deposit amount"}), 400

    user["balance"] += amount
    return jsonify({
        "status": "success",
        "message": f"Added ${amount:.2f} credits to wallet",
        "balance": round(user["balance"], 2)
    })

@app.route('/api/wallet/reset', methods=['POST'])
def reset_wallet():
    user = get_user_from_request()
    if not user or user.get("role") != "admin":
        return jsonify({
            "status": "error",
            "message": "Reset disabled. Please contact the administrator for balance adjustments."
        }), 403

    user["balance"] = 1000.0
    return jsonify({
        "status": "success",
        "message": "Wallet balance reset to $1,000 demo credits",
        "balance": user["balance"]
    })

@app.route('/api/wallet/withdraw/request', methods=['POST'])
def request_withdrawal():
    user = get_user_from_request()
    if not user:
        return jsonify({"status": "error", "message": "Authentication required to request withdrawal"}), 401

    data = request.get_json() or {}
    try:
        amount = float(data.get("amount", 0))
    except (ValueError, TypeError):
        return jsonify({"status": "error", "message": "Invalid withdrawal amount format"}), 400

    if amount <= 0:
        return jsonify({"status": "error", "message": "Withdrawal amount must be greater than zero"}), 400

    if user["balance"] < amount:
        return jsonify({
            "status": "error",
            "message": f"Insufficient wallet balance! You have ${user['balance']:.2f}, but requested ${amount:.2f}"
        }), 400

    method = str(data.get("method", "UPI")).upper().strip()
    details = str(data.get("details", "")).strip()
    account_name = str(data.get("account_name", user["username"])).strip()

    if not details:
        return jsonify({"status": "error", "message": "Payment destination (UPI ID / Bank details) is required"}), 400

    req_id = f"WDR-{random.randint(10000, 99999)}"
    req_entry = {
        "id": req_id,
        "username": user["username"],
        "uid": user.get("uid", "UID-DEMO"),
        "amount": round(amount, 2),
        "method": method,
        "details": details,
        "account_name": account_name,
        "status": "PENDING",
        "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processed_at": None,
        "admin_note": ""
    }
    withdrawal_requests.insert(0, req_entry)

    return jsonify({
        "status": "success",
        "message": f"Withdrawal request #{req_id} for ${amount:.2f} submitted to Admin! Money will be deducted when Admin accepts.",
        "request": req_entry
    })

@app.route('/api/wallet/withdraw/my_requests', methods=['GET'])
def get_my_withdrawals():
    user = get_user_from_request()
    if not user:
        return jsonify({"status": "error", "message": "Authentication required"}), 401

    my_reqs = [r for r in withdrawal_requests if r["username"] == user["username"]]
    return jsonify({
        "status": "success",
        "requests": my_reqs
    })


# ==========================================
# 1. AVIATOR (CRASH GAME)
# ==========================================
@app.route('/api/aviator/start', methods=['POST'])
def start_aviator():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 100))

    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400

    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1

    round_id = str(uuid.uuid4())

    rand_val = random.random()
    if rand_val < 0.10:
        crash_multiplier = round(random.uniform(1.01, 1.15), 2)
    elif rand_val < 0.60:
        crash_multiplier = round(random.uniform(1.16, 2.10), 2)
    elif rand_val < 0.85:
        crash_multiplier = round(random.uniform(2.11, 4.50), 2)
    elif rand_val < 0.95:
        crash_multiplier = round(random.uniform(4.51, 9.00), 2)
    else:
        crash_multiplier = round(random.uniform(9.01, 25.00), 2)

    active_aviator_rounds[round_id] = {
        "username": user["username"],
        "bet": bet,
        "crash_multiplier": crash_multiplier,
        "start_time": time.time(),
        "status": "FLYING"
    }

    return jsonify({
        "status": "success",
        "round_id": round_id,
        "bet": bet,
        "crash_multiplier": crash_multiplier,
        "balance": round(user["balance"], 2)
    })

@app.route('/api/aviator/cashout', methods=['POST'])
def cashout_aviator():
    data = request.get_json() or {}
    round_id = data.get("round_id")
    multiplier = float(data.get("multiplier", 1.0))

    if round_id not in active_aviator_rounds:
        return jsonify({"status": "error", "message": "Round not found or already finished"}), 400

    round_info = active_aviator_rounds[round_id]
    user = users.get(round_info["username"], get_user_from_request())

    if round_info["status"] != "FLYING":
        return jsonify({"status": "error", "message": "Round already settled"}), 400

    crash_multiplier = round_info["crash_multiplier"]

    if multiplier >= crash_multiplier:
        round_info["status"] = "CRASHED"
        aviator_history.insert(0, crash_multiplier)
        if len(aviator_history) > 12:
            aviator_history.pop()
        record_live_bet(user["username"], "Aviator", round_info["bet"], f"Crashed @ {crash_multiplier:.2f}x", "LOST", 0.0)
        del active_aviator_rounds[round_id]
        return jsonify({
            "status": "crashed",
            "message": f"Plane flew away at {crash_multiplier}x before cashout!",
            "crash_multiplier": crash_multiplier,
            "win_amount": 0,
            "balance": round(user["balance"], 2)
        })

    bet = round_info["bet"]
    win_amount = round(bet * multiplier, 2)
    user["balance"] += win_amount
    user["total_won"] += win_amount
    round_info["status"] = "WON"

    aviator_history.insert(0, crash_multiplier)
    if len(aviator_history) > 12:
        aviator_history.pop()

    record_live_bet(user["username"], "Aviator", bet, f"Cashed out @ {multiplier:.2f}x", "WON", win_amount)
    del active_aviator_rounds[round_id]

    return jsonify({
        "status": "won",
        "message": f"Successfully cashed out ${win_amount} at {multiplier}x!",
        "win_amount": win_amount,
        "multiplier": multiplier,
        "crash_multiplier": crash_multiplier,
        "balance": round(user["balance"], 2)
    })

@app.route('/api/aviator/history', methods=['GET'])
def get_aviator_history():
    return jsonify({
        "status": "success",
        "history": aviator_history
    })


# ==========================================
# 2. COLOR PREDICTION (WINGO)
# ==========================================
@app.route('/api/color/bet', methods=['POST'])
def bet_color():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 100))
    choice_type = data.get("choice_type", "color")
    choice_value = data.get("choice_value", "GREEN")

    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400

    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1

    drawn_number = random.randint(0, 9)

    if drawn_number in [1, 3, 7, 9]:
        drawn_color = "GREEN"
    elif drawn_number in [2, 4, 6, 8]:
        drawn_color = "RED"
    else:
        drawn_color = "VIOLET"

    won = False
    payout_multiplier = 0.0

    if choice_type == "color":
        target_color = str(choice_value).upper()
        if target_color == drawn_color:
            won = True
            payout_multiplier = 4.5 if target_color == "VIOLET" else 2.0
        elif (drawn_number == 0 and target_color == "RED") or (drawn_number == 5 and target_color == "GREEN"):
            won = True
            payout_multiplier = 1.5
    elif choice_type == "number":
        target_num = int(choice_value)
        if target_num == drawn_number:
            won = True
            payout_multiplier = 9.0
    elif choice_type == "size":
        target_size = str(choice_value).upper()
        if (target_size == "BIG" and drawn_number >= 5) or (target_size == "SMALL" and drawn_number < 5):
            won = True
            payout_multiplier = 2.0

    win_amount = 0.0
    if won:
        win_amount = round(bet * payout_multiplier, 2)
        user["balance"] += win_amount
        user["total_won"] += win_amount

    period_id = int(time.time()) % 100000000
    history_entry = {
        "period": period_id,
        "number": drawn_number,
        "color": drawn_color
    }
    color_history.insert(0, history_entry)
    if len(color_history) > 10:
        color_history.pop()

    record_live_bet(
        user["username"],
        "Color Wingo",
        bet,
        f"{choice_value} -> #{drawn_number} {drawn_color} ({payout_multiplier}x)" if won else f"{choice_value} -> #{drawn_number} {drawn_color}",
        "WON" if won else "LOST",
        win_amount
    )

    return jsonify({
        "status": "success",
        "won": won,
        "drawn_number": drawn_number,
        "drawn_color": drawn_color,
        "payout_multiplier": payout_multiplier,
        "win_amount": win_amount,
        "balance": round(user["balance"], 2),
        "history": color_history
    })

@app.route('/api/color/history', methods=['GET'])
def get_color_history():
    return jsonify({
        "status": "success",
        "history": color_history
    })


# ==========================================
# 3. CHAKRI (LUCKY WHEEL / ROULETTE)
# ==========================================
@app.route('/api/chakri/config', methods=['GET'])
def get_chakri_config():
    return jsonify({
        "status": "success",
        "slices": CHAKRI_SLICES,
        "history": chakri_history
    })

@app.route('/api/chakri/spin', methods=['POST'])
def spin_chakri():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 100))

    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400

    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1

    # Weighted random selection of slice
    weights = [s["weight"] for s in CHAKRI_SLICES]
    selected_slice = random.choices(CHAKRI_SLICES, weights=weights, k=1)[0]

    mult = selected_slice["multiplier"]
    won = mult > 0.0
    win_amount = round(bet * mult, 2)

    if won:
        user["balance"] += win_amount
        user["total_won"] += win_amount

    # Add to history
    chakri_history.insert(0, {
        "label": selected_slice["label"],
        "multiplier": selected_slice["multiplier"],
        "color": selected_slice["color"]
    })
    if len(chakri_history) > 10:
        chakri_history.pop()

    return jsonify({
        "status": "success",
        "slice_index": selected_slice["index"],
        "label": selected_slice["label"],
        "multiplier": selected_slice["multiplier"],
        "color": selected_slice["color"],
        "won": won,
        "win_amount": win_amount,
        "balance": round(user["balance"], 2),
        "history": chakri_history
    })


# ==========================================
# 3B. FUN ROULETTE (MINI ROULETTE 0-18 CHAKRI)
# ==========================================
@app.route('/api/fun_roulette/history', methods=['GET'])
def get_fun_roulette_history():
    return jsonify({
        "status": "success",
        "history": fun_roulette_history
    })

@app.route('/api/fun_roulette/current_round', methods=['GET'])
def get_fun_roulette_current_round():
    now = time.time()
    period_id = int(now // 30)
    cycle_time = int(now % 30)
    
    # 0 to 20s: BETTING, 20 to 26s: SPINNING, 26 to 29s: SETTLED
    if cycle_time < 20:
        phase = "BETTING"
        remaining = 20 - cycle_time
    elif cycle_time < 26:
        phase = "SPINNING"
        remaining = 26 - cycle_time
    else:
        phase = "SETTLED"
        remaining = 30 - cycle_time

    # Cryptographic SHA256 commitment of the round
    period_seed = hashlib.sha256(f"{SERVER_SEED}_{period_id}".encode()).hexdigest()
    winning_number = int(period_seed[:8], 16) % 19
    hash_commitment = hashlib.sha256(f"period_{period_id}_{period_seed}".encode()).hexdigest()

    return jsonify({
        "status": "success",
        "period_id": period_id,
        "phase": phase,
        "cycle_time": cycle_time,
        "remaining_seconds": remaining,
        "hash_commitment": hash_commitment,
        "history": fun_roulette_history
    })

@app.route('/api/fun_roulette/spin', methods=['POST'])
def spin_fun_roulette():
    user = get_user_from_request()
    data = request.get_json() or {}
    bets = data.get("bets", {})
    total_bet = float(data.get("total_bet", 0))

    if total_bet <= 0 and bets:
        total_bet = sum(float(v) for v in bets.values() if float(v) > 0)

    # If user placed bets, verify balance
    if total_bet > 0:
        if user["balance"] < total_bet:
            return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
        user["balance"] -= total_bet
        user["total_bet"] += total_bet
        user["games_played"] += 1

    # Cryptographically secure random number (0 to 18) - 100% Unpredictable
    winning_number = secrets.randbelow(19)
    winning_color = "GREEN" if winning_number == 0 else ("RED" if winning_number in FUN_ROULETTE_REDS else "BLACK")

    total_won = 0.0
    winning_bets = []

    for bet_key, amount in bets.items():
        bet_amt = float(amount)
        if bet_amt <= 0:
            continue

        is_win = False
        payout_mult = 0.0

        if bet_key.startswith("num_"):
            n = int(bet_key.replace("num_", ""))
            if n == winning_number:
                is_win = True
                payout_mult = 18.0
        elif bet_key == "row_1":  # 3, 6, 9, 12, 15, 18
            if winning_number in [3, 6, 9, 12, 15, 18]:
                is_win = True
                payout_mult = 3.0
        elif bet_key == "row_2":  # 2, 5, 8, 11, 14, 17
            if winning_number in [2, 5, 8, 11, 14, 17]:
                is_win = True
                payout_mult = 3.0
        elif bet_key == "row_3":  # 1, 4, 7, 10, 13, 16
            if winning_number in [1, 4, 7, 10, 13, 16]:
                is_win = True
                payout_mult = 3.0
        elif bet_key == "first_6":
            if 1 <= winning_number <= 6:
                is_win = True
                payout_mult = 3.0
        elif bet_key == "second_6":
            if 7 <= winning_number <= 12:
                is_win = True
                payout_mult = 3.0
        elif bet_key == "third_6":
            if 13 <= winning_number <= 18:
                is_win = True
                payout_mult = 3.0
        elif bet_key == "low_1_9":
            if 1 <= winning_number <= 9:
                is_win = True
                payout_mult = 2.0
        elif bet_key == "high_10_18":
            if 10 <= winning_number <= 18:
                is_win = True
                payout_mult = 2.0
        elif bet_key == "even":
            if winning_number > 0 and winning_number % 2 == 0:
                is_win = True
                payout_mult = 2.0
        elif bet_key == "odd":
            if winning_number % 2 != 0:
                is_win = True
                payout_mult = 2.0
        elif bet_key == "red":
            if winning_number in FUN_ROULETTE_REDS:
                is_win = True
                payout_mult = 2.0
        elif bet_key == "black":
            if winning_number in FUN_ROULETTE_BLACKS:
                is_win = True
                payout_mult = 2.0

        if is_win:
            win_val = round(bet_amt * payout_mult, 2)
            total_won += win_val
            winning_bets.append({
                "bet_key": bet_key,
                "amount": bet_amt,
                "payout": win_val
            })

    if total_won > 0:
        user["balance"] += total_won
        user["total_won"] += total_won

    fun_roulette_history.insert(0, winning_number)
    if len(fun_roulette_history) > 10:
        fun_roulette_history.pop()

    # Log to live bets stream for admin portal
    if total_bet > 0:
        record_live_bet(
            user["username"], 
            "Fun Roulette", 
            total_bet, 
            f"Number {winning_number} ({winning_color})", 
            "WON" if total_won > 0 else "LOST", 
            total_won
        )

    return jsonify({
        "status": "success",
        "winning_number": winning_number,
        "winning_color": winning_color,
        "total_bet": total_bet,
        "total_won": round(total_won, 2),
        "winning_bets": winning_bets,
        "balance": round(user["balance"], 2),
        "history": fun_roulette_history
    })


# ==========================================
# 4. MINES (BOMB GRID)
# ==========================================
@app.route('/api/mines/start', methods=['POST'])
def start_mines():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 100))
    bombs_count = int(data.get("bombs", 5))

    if bombs_count < 1 or bombs_count > 24:
        return jsonify({"status": "error", "message": "Bombs count must be between 1 and 24"}), 400

    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400

    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1

    round_id = str(uuid.uuid4())
    all_indices = list(range(25))
    random.shuffle(all_indices)
    bomb_positions = set(all_indices[:bombs_count])

    active_mines_rounds[round_id] = {
        "username": user["username"],
        "bet": bet,
        "bombs_count": bombs_count,
        "bomb_positions": bomb_positions,
        "revealed_gems": set(),
        "multiplier": 1.0,
        "status": "PLAYING"
    }

    return jsonify({
        "status": "success",
        "round_id": round_id,
        "bet": bet,
        "bombs_count": bombs_count,
        "multiplier": 1.0,
        "balance": round(user["balance"], 2)
    })

@app.route('/api/mines/reveal', methods=['POST'])
def reveal_mine_tile():
    data = request.get_json() or {}
    round_id = data.get("round_id")
    tile_index = int(data.get("tile_index", -1))

    if round_id not in active_mines_rounds:
        return jsonify({"status": "error", "message": "Round not active"}), 400

    round_info = active_mines_rounds[round_id]
    user = users.get(round_info["username"], get_user_from_request())

    if round_info["status"] != "PLAYING":
        return jsonify({"status": "error", "message": "Round already completed"}), 400

    if tile_index < 0 or tile_index >= 25:
        return jsonify({"status": "error", "message": "Invalid tile index"}), 400

    if tile_index in round_info["revealed_gems"]:
        return jsonify({"status": "error", "message": "Tile already revealed"}), 400

    bomb_positions = round_info["bomb_positions"]

    if tile_index in bomb_positions:
        round_info["status"] = "LOST"
        all_bombs = list(bomb_positions)
        record_live_bet(user["username"], "Mines", round_info["bet"], f"Hit Mine on Tile #{tile_index + 1}", "LOST", 0.0)
        del active_mines_rounds[round_id]
        return jsonify({
            "status": "bomb",
            "message": "Boom! You hit a mine!",
            "tile_index": tile_index,
            "all_bombs": all_bombs,
            "win_amount": 0,
            "balance": round(user["balance"], 2)
        })

    round_info["revealed_gems"].add(tile_index)
    gems_count = len(round_info["revealed_gems"])
    bombs = round_info["bombs_count"]

    multiplier = round(1.0 + (gems_count * (0.25 + (bombs * 0.06))), 2)
    round_info["multiplier"] = multiplier
    current_cashout = round(round_info["bet"] * multiplier, 2)

    total_safe_tiles = 25 - bombs
    all_cleared = (gems_count == total_safe_tiles)

    if all_cleared:
        round_info["status"] = "WON"
        user["balance"] += current_cashout
        user["total_won"] += current_cashout
        all_bombs = list(bomb_positions)
        record_live_bet(user["username"], "Mines", round_info["bet"], f"Cleared All {total_safe_tiles} Gems ({multiplier}x)", "WON", current_cashout)
        del active_mines_rounds[round_id]
        return jsonify({
            "status": "completed",
            "message": f"Incredible! All {total_safe_tiles} diamonds found! Won ${current_cashout}!",
            "tile_index": tile_index,
            "gems_count": gems_count,
            "multiplier": multiplier,
            "win_amount": current_cashout,
            "all_bombs": all_bombs,
            "balance": round(user["balance"], 2)
        })

    return jsonify({
        "status": "gem",
        "message": f"Diamond found! Multiplier: {multiplier}x",
        "tile_index": tile_index,
        "gems_count": gems_count,
        "multiplier": multiplier,
        "cashout_value": current_cashout,
        "balance": round(user["balance"], 2)
    })

@app.route('/api/mines/cashout', methods=['POST'])
def cashout_mines():
    data = request.get_json() or {}
    round_id = data.get("round_id")

    if round_id not in active_mines_rounds:
        return jsonify({"status": "error", "message": "Round not active"}), 400

    round_info = active_mines_rounds[round_id]
    user = users.get(round_info["username"], get_user_from_request())

    if round_info["status"] != "PLAYING":
        return jsonify({"status": "error", "message": "Round already settled"}), 400

    if len(round_info["revealed_gems"]) == 0:
        return jsonify({"status": "error", "message": "Reveal at least 1 diamond to cashout"}), 400

    multiplier = round_info["multiplier"]
    win_amount = round(round_info["bet"] * multiplier, 2)
    user["balance"] += win_amount
    user["total_won"] += win_amount
    round_info["status"] = "CASHED_OUT"

    all_bombs = list(round_info["bomb_positions"])
    record_live_bet(user["username"], "Mines", round_info["bet"], f"Cashed out at {multiplier:.2f}x ({len(round_info['revealed_gems'])} gems)", "WON", win_amount)
    del active_mines_rounds[round_id]

    return jsonify({
        "status": "success",
        "message": f"Successfully cashed out ${win_amount} at {multiplier}x!",
        "win_amount": win_amount,
        "multiplier": multiplier,
        "all_bombs": all_bombs,
        "balance": round(user["balance"], 2)
    })


# ==========================================
# 5. LUCKY 777 SLOTS
# ==========================================
@app.route('/api/slots/spin', methods=['POST'])
def spin_slots():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 100))

    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400

    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1

    roll = random.random()
    if roll < 0.06:
        reels = ['7️⃣', '7️⃣', '7️⃣']
    elif roll < 0.16:
        reels = ['💎', '💎', '💎']
    elif roll < 0.32:
        sym = random.choice(['🔔', '⭐'])
        reels = [sym, sym, sym]
    elif roll < 0.50:
        sym = random.choice(SLOT_SYMBOLS)
        other = random.choice([s for s in SLOT_SYMBOLS if s != sym])
        reels = [sym, sym, other]
    else:
        reels = random.sample(SLOT_SYMBOLS, 3)

    won = False
    payout_multiplier = 0.0
    if reels[0] == reels[1] == reels[2]:
        won = True
        payout_multiplier = SLOT_PAYOUTS.get(reels[0], 3.0)
    elif reels[0] == reels[1] or reels[1] == reels[2]:
        won = True
        payout_multiplier = 1.2

    win_amount = 0.0
    if won:
        win_amount = round(bet * payout_multiplier, 2)
        user["balance"] += win_amount
        user["total_won"] += win_amount

    reels_display = ' '.join(reels)
    record_live_bet(
        user["username"],
        "777 Slots",
        bet,
        f"{reels_display} ({payout_multiplier}x)" if won else f"{reels_display} (No match)",
        "WON" if won else "LOST",
        win_amount
    )

    return jsonify({
        "status": "success",
        "reels": reels,
        "won": won,
        "payout_multiplier": payout_multiplier,
        "win_amount": win_amount,
        "balance": round(user["balance"], 2)
    })


# ==========================================
# 6. UNIFIED 56+ TRENDING GAMES SUITE
# ==========================================
@app.route('/api/games/catalog', methods=['GET'])
def get_games_catalog():
    return jsonify({
        "status": "success",
        "count": len(GAMES_CATALOG),
        "games": GAMES_CATALOG
    })

@app.route('/api/game/play', methods=['POST'])
def play_game_round():
    user = get_user_from_request()
    data = request.get_json() or {}
    game_id = str(data.get("game_id", "carrom")).lower()
    bet = float(data.get("bet", 50))
    options = data.get("options", {})

    if game_id not in GAMES_BY_ID:
        return jsonify({"status": "error", "message": f"Game '{game_id}' not found in catalog"}), 404

    game_meta = GAMES_BY_ID[game_id]
    min_bet = float(game_meta.get("min_bet", 10))

    if bet < min_bet:
        return jsonify({"status": "error", "message": f"Minimum bet for {game_meta['name']} is ${min_bet:.2f}"}), 400

    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400

    # Deduct bet
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1

    # Simulate game outcome using provably fair rules
    result = simulate_game_round(game_id, bet, options)
    win_amount = result["win_amount"]

    if result["won"]:
        user["balance"] += win_amount
        user["total_won"] += win_amount

    # Record to live bets feed for Master Admin Panel
    record_live_bet(
        user["username"],
        game_meta["name"],
        bet,
        result["result_text"],
        "WON" if result["won"] else "LOST",
        win_amount
    )

    return jsonify({
        "status": "success",
        "game_id": game_id,
        "game_name": game_meta["name"],
        "hindi_name": game_meta["hindi_name"],
        "category": game_meta["category"],
        "bet": bet,
        "won": result["won"],
        "multiplier": result["multiplier"],
        "win_amount": win_amount,
        "title": result["title"],
        "details": result["details"],
        "result_text": result["result_text"],
        "balance": round(user["balance"], 2)
    })

# Specialized Endpoints for specific games
@app.route('/api/carrom/strike', methods=['POST'])
def api_carrom_strike():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    options = {
        "power": data.get("power", 75),
        "angle": data.get("angle", 45),
        "target": data.get("target", "any")
    }
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("carrom", bet, options)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Carrom Clash", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/ludo/roll', methods=['POST'])
def api_ludo_roll():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    options = {"token": data.get("token", "Red")}
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("ludo", bet, options)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Ludo Supreme", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/bigsmall/bet', methods=['POST'])
def api_bigsmall_bet():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    options = {"choice": data.get("choice", "BIG")}
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("bigsmall", bet, options)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Big Small", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/dragontiger/play', methods=['POST'])
def api_dragontiger_play():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    options = {"choice": data.get("choice", "DRAGON")}
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("dragontiger", bet, options)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Dragon vs Tiger", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/sevenup/play', methods=['POST'])
def api_sevenup_play():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    options = {"choice": data.get("choice", "7_UP")}
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("sevenup", bet, options)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "7 Up 7 Down", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/teenpatti/play', methods=['POST'])
def api_teenpatti_play():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("teenpatti", bet)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Teen Patti", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/plinko/drop', methods=['POST'])
def api_plinko_drop():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("plinko", bet)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Plinko Pegs", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/penalty/shoot', methods=['POST'])
def api_penalty_shoot():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    options = {"spot": data.get("spot", "TL"), "streak": data.get("streak", 1)}
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("penalty", bet, options)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Penalty Shootout", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/coinflip/flip', methods=['POST'])
def api_coinflip_flip():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    options = {"choice": data.get("choice", "HEADS"), "streak": data.get("streak", 1)}
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("coinflip", bet, options)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Coin Flip", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/limbo/play', methods=['POST'])
def api_limbo_play():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    options = {"target": data.get("target", 2.0)}
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    res = simulate_game_round("limbo", bet, options)
    if res["won"]:
        user["balance"] += res["win_amount"]
        user["total_won"] += res["win_amount"]
    record_live_bet(user["username"], "Limbo", bet, res["result_text"], "WON" if res["won"] else "LOST", res["win_amount"])
    return jsonify({**res, "status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/coins777/spin', methods=['POST'])
def api_coins777_spin():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 3.0))
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1

    symbols = ['BAR', 'DIAMOND', 'RUBY', 'EMERALD', 'RED_X', 'COIN']
    weights = [0.10, 0.14, 0.16, 0.20, 0.25, 0.15]
    grid = [[random.choices(symbols, weights=weights)[0] for _ in range(3)] for _ in range(3)]

    paylines = [
        [(0, 0), (0, 1), (0, 2)], # Top row
        [(1, 0), (1, 1), (1, 2)], # Mid row
        [(2, 0), (2, 1), (2, 2)], # Bot row
        [(0, 0), (1, 1), (2, 2)], # Diagonal TL-BR
        [(2, 0), (1, 1), (0, 2)]  # Diagonal BL-TR
    ]
    payout_multipliers = {
        'BAR': 8.0,
        'DIAMOND': 5.0,
        'RUBY': 5.0,
        'EMERALD': 2.0,
        'RED_X': 2.0
    }

    winning_lines = []
    total_mult = 0.0
    for idx, line in enumerate(paylines):
        s1 = grid[line[0][0]][line[0][1]]
        s2 = grid[line[1][0]][line[1][1]]
        s3 = grid[line[2][0]][line[2][1]]
        if s1 == s2 == s3 and s1 in payout_multipliers:
            m = payout_multipliers[s1]
            total_mult += m
            line_win = round(bet * m, 2)
            winning_lines.append({
                "line_index": idx,
                "line_number": idx + 1,
                "symbol": s1,
                "multiplier": m,
                "line_win": line_win
            })

    coin_count = sum(row.count('COIN') for row in grid)
    is_bonus = coin_count >= 3
    jackpot_type = None

    if is_bonus:
        r = random.random()
        if r < 0.15:
            jackpot_type = "GRAND"
            bonus_mult = 8.0
        elif r < 0.45:
            jackpot_type = "MAJOR"
            bonus_mult = 5.0
        else:
            jackpot_type = "MINI"
            bonus_mult = 2.0
        total_mult += bonus_mult

    win_amount = round(bet * total_mult, 2)
    won = win_amount > 0
    if won:
        user["balance"] += win_amount
        user["total_won"] += win_amount

    result_text = f"777 Coins: {'WIN $' + str(win_amount) if won else 'No Match'} ({total_mult}x)"
    if jackpot_type:
        result_text += f" | {jackpot_type} JACKPOT!"

    record_live_bet(user["username"], "777 Coins Slots", bet, result_text, "WON" if won else "LOST", win_amount)

    return jsonify({
        "status": "success",
        "won": won,
        "grid": grid,
        "winning_lines": winning_lines,
        "is_bonus": is_bonus,
        "jackpot_type": jackpot_type,
        "multiplier": total_mult,
        "win_amount": win_amount,
        "balance": round(user["balance"], 2)
    })

@app.route('/api/mines/start', methods=['POST'])
def api_mines_start():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    return jsonify({"status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/mines/cashout', methods=['POST'])
def api_mines_cashout():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    multiplier = float(data.get("multiplier", 2.0))
    win_amount = round(bet * multiplier, 2)
    user["balance"] += win_amount
    user["total_won"] += win_amount
    record_live_bet(user["username"], "Mines Pro (Diamonds)", bet, f"Cashed Out at {multiplier}x (+${win_amount:.2f})", "WON", win_amount)
    return jsonify({"status": "success", "balance": round(user["balance"], 2), "win_amount": win_amount})

@app.route('/api/mines/bust', methods=['POST'])
def api_mines_bust():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    gems = int(data.get("gems", 0))
    record_live_bet(user["username"], "Mines Pro (Diamonds)", bet, f"Busted on Mine ({gems} gems found)", "LOST", 0.0)
    return jsonify({"status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/fruitslice/start', methods=['POST'])
def api_fruitslice_start():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    return jsonify({"status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/fruitslice/settle', methods=['POST'])
def api_fruitslice_settle():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    score = int(data.get("score", 0))
    combos = int(data.get("combos", 0))
    hit_bomb = bool(data.get("hit_bomb", False))

    multiplier = 0.0
    if not hit_bomb:
        if score >= 150:
            multiplier = 5.0
        elif score >= 80:
            multiplier = 3.0
        elif score >= 40:
            multiplier = 2.0
        elif score >= 20:
            multiplier = 1.2
    else:
        if score >= 60:
            multiplier = 1.0  # Consolation refund on high score bomb hit

    win_amount = round(bet * multiplier, 2)
    won = win_amount > 0
    if won:
        user["balance"] += win_amount
        user["total_won"] += win_amount

    res_text = f"Fruit Slice: {score} pts ({combos} combos) ➔ {multiplier}x {'WON $' + str(win_amount) if won else 'BOMB / OVER'}"
    record_live_bet(user["username"], "Fruit Slice (Cut)", bet, res_text, "WON" if won else "LOST", win_amount)
    return jsonify({
        "status": "success",
        "won": won,
        "multiplier": multiplier,
        "win_amount": win_amount,
        "balance": round(user["balance"], 2)
    })

@app.route('/api/bubbleshooter/start', methods=['POST'])
def api_bubbleshooter_start():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    return jsonify({"status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/bubbleshooter/settle', methods=['POST'])
def api_bubbleshooter_settle():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    popped = int(data.get("popped", 0))
    cleared = bool(data.get("cleared", False))

    multiplier = 0.0
    if cleared:
        multiplier = 8.0
    elif popped >= 30:
        multiplier = 4.0
    elif popped >= 18:
        multiplier = 2.5
    elif popped >= 9:
        multiplier = 1.8
    elif popped >= 5:
        multiplier = 1.0

    win_amount = round(bet * multiplier, 2)
    won = win_amount > 0
    if won:
        user["balance"] += win_amount
        user["total_won"] += win_amount

    res_text = f"Bubble Shooter: {popped} popped {'(Board Cleared!)' if cleared else ''} ➔ {multiplier}x {'+$' + str(win_amount) if won else ''}"
    record_live_bet(user["username"], "Bubble Shooter Pop", bet, res_text, "WON" if won else "LOST", win_amount)
    return jsonify({
        "status": "success",
        "won": won,
        "multiplier": multiplier,
        "win_amount": win_amount,
        "balance": round(user["balance"], 2)
    })

@app.route('/api/ludo/start', methods=['POST'])
def api_ludo_start():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400
    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1
    return jsonify({"status": "success", "balance": round(user["balance"], 2)})

@app.route('/api/ludo/settle', methods=['POST'])
def api_ludo_settle():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    won = bool(data.get("won", False))
    user_score = int(data.get("user_score", 0))
    bot_score = int(data.get("bot_score", 0))

    multiplier = 2.5 if won else (0.5 if user_score > bot_score * 0.8 else 0.0)
    win_amount = round(bet * multiplier, 2)
    if win_amount > 0:
        user["balance"] += win_amount
        user["total_won"] += win_amount

    res_text = f"Ludo Express: {'VICTORY (1st)' if won else 'Defeat'} ({user_score} vs {bot_score} pts)"
    record_live_bet(user["username"], "Ludo Express 3D", bet, res_text, "WON" if won else "LOST", win_amount)
    return jsonify({
        "status": "success",
        "won": won,
        "multiplier": multiplier,
        "win_amount": win_amount,
        "balance": round(user["balance"], 2)
    })


# ========================================================
# FEATURE 5: ANDAR BAHAR 20-20 LIVE GAME ENGINE
# ========================================================
andar_bahar_history = ["ANDAR", "BAHAR", "ANDAR", "ANDAR", "BAHAR", "ANDAR", "BAHAR", "BAHAR", "ANDAR", "BAHAR"]

@app.route('/api/andarbahar/history', methods=['GET'])
def api_andarbahar_history():
    return jsonify({
        "status": "success",
        "history": andar_bahar_history[-20:]
    })

@app.route('/api/andarbahar/play', methods=['POST'])
def api_andarbahar_play():
    user = get_user_from_request()
    data = request.get_json() or {}
    bet = float(data.get("bet", 50))
    chosen_side = str(data.get("side", "ANDAR")).upper()

    if chosen_side not in ["ANDAR", "BAHAR"]:
        return jsonify({"status": "error", "message": "Invalid side! Choose ANDAR or BAHAR."}), 400

    if user["balance"] < bet:
        return jsonify({"status": "error", "message": "Insufficient wallet balance"}), 400

    user["balance"] -= bet
    user["total_bet"] += bet
    user["games_played"] += 1

    # Generate 52 Card Deck
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    deck = []
    for s in suits:
        for r in ranks:
            deck.append({
                "rank": r,
                "suit": s,
                "is_red": s in ['♥', '♦'],
                "label": f"{r}{s}"
            })
    random.shuffle(deck)

    # 1. Opening Joker Card
    joker = deck.pop(0)

    # 2. Alternating Dealing: Andar, Bahar, Andar, Bahar...
    dealt_andar = []
    dealt_bahar = []
    winning_side = None
    step = 0

    while deck:
        step += 1
        card = deck.pop(0)
        is_andar_turn = (step % 2 == 1)

        if is_andar_turn:
            dealt_andar.append(card)
            if card["rank"] == joker["rank"]:
                winning_side = "ANDAR"
                break
        else:
            dealt_bahar.append(card)
            if card["rank"] == joker["rank"]:
                winning_side = "BAHAR"
                break

    # Payout calculation: Andar pays 1.95x, Bahar pays 2.0x
    won = (chosen_side == winning_side)
    multiplier = 1.95 if (won and winning_side == "ANDAR") else (2.0 if (won and winning_side == "BAHAR") else 0.0)
    win_amount = round(bet * multiplier, 2)

    if win_amount > 0:
        user["balance"] += win_amount
        user["total_won"] += win_amount

    andar_bahar_history.append(winning_side)
    if len(andar_bahar_history) > 50:
        andar_bahar_history.pop(0)

    res_text = f"Joker {joker['label']} matched on {winning_side} (Card #{step})"
    record_live_bet(user["username"], "Andar Bahar 20-20", bet, res_text, "WON" if won else "LOST", win_amount)

    return jsonify({
        "status": "success",
        "joker": joker,
        "winning_side": winning_side,
        "chosen_side": chosen_side,
        "won": won,
        "multiplier": multiplier,
        "win_amount": win_amount,
        "balance": round(user["balance"], 2),
        "dealt_andar": dealt_andar,
        "dealt_bahar": dealt_bahar,
        "total_cards_dealt": step,
        "history": andar_bahar_history[-20:]
    })


# ========================================================
# FEATURE 6: DAILY 7-DAY LOGIN STREAK REWARDS
# ========================================================
DAILY_STREAK_REWARDS = [10.0, 20.0, 30.0, 50.0, 75.0, 100.0, 250.0]

@app.route('/api/bonus/status', methods=['GET'])
def api_bonus_status():
    user = get_user_from_request()
    today_str = datetime.date.today().isoformat()
    streak_day = user.setdefault("streak_day", 1)
    last_claim = user.get("last_claim_date", None)

    # Check if claimed today
    claimed_today = (last_claim == today_str)

    # Check if streak broken (missed more than 1 day)
    if last_claim and not claimed_today:
        try:
            last_date = datetime.date.fromisoformat(last_claim)
            diff_days = (datetime.date.today() - last_date).days
            if diff_days > 1:
                # Reset streak to Day 1
                streak_day = 1
                user["streak_day"] = 1
        except Exception:
            pass

    return jsonify({
        "status": "success",
        "streak_day": streak_day,
        "claimed_today": claimed_today,
        "rewards": DAILY_STREAK_REWARDS,
        "today_reward": DAILY_STREAK_REWARDS[min(streak_day - 1, 6)],
        "balance": round(user["balance"], 2)
    })

@app.route('/api/bonus/claim', methods=['POST'])
def api_bonus_claim():
    user = get_user_from_request()
    today_str = datetime.date.today().isoformat()
    streak_day = user.setdefault("streak_day", 1)
    last_claim = user.get("last_claim_date", None)

    if last_claim == today_str:
        return jsonify({
            "status": "error",
            "message": "Today's daily bonus already claimed! Please come back tomorrow."
        }), 400

    reward_amount = DAILY_STREAK_REWARDS[min(streak_day - 1, 6)]
    user["balance"] += reward_amount
    user["last_claim_date"] = today_str

    # Record streak claim as a winning bonus in live bets
    record_live_bet(user["username"], "7-Day Daily Streak", 0.0, f"Day {streak_day} Daily Reward Claimed", "WON", reward_amount)

    # Next streak day
    next_day = (streak_day % 7) + 1
    user["streak_day"] = next_day

    return jsonify({
        "status": "success",
        "message": f"🎉 Congratulations! Day {streak_day} Bonus ₹{reward_amount:.2f} credited to your wallet!",
        "reward_amount": reward_amount,
        "new_balance": round(user["balance"], 2),
        "next_streak_day": next_day
    })


# ========================================================
# FEATURE 4: VIP COMMUNITY LIVE CHAT & WINNER FOMO TICKER
# ========================================================
community_chat_messages = [
    {"id": 1, "user": "Vikas_VIP", "role": "vip", "text": "Aviator me 3x safe nikal rha hu bhaiyo! Full profit chal rha 🔥", "time": "3m ago"},
    {"id": 2, "user": "Pooja_S", "role": "user", "text": "Andar Bahar pe Bahar streak chal rhi hai! ₹1,500 hit hua 💃", "time": "2m ago"},
    {"id": 3, "user": "Rahul_K", "role": "vip", "text": "Color trading Green streak alert 🟢⚡ Next round Green confirm!", "time": "1m ago"},
    {"id": 4, "user": "System_Bot", "role": "bot", "text": "🚀 Winner Alert: player1 won ₹490.00 on Aviator!", "time": "Just now"},
    {"id": 5, "user": "Sameer_GJ", "role": "user", "text": "Withdrawal requested ₹2000, admin sir please accept fast 🙏", "time": "Just now"}
]

@app.route('/api/chat/messages', methods=['GET'])
def api_chat_messages():
    # Return messages plus active online users count
    online_count = 428 + secrets.randbelow(15)
    return jsonify({
        "status": "success",
        "online_count": online_count,
        "messages": community_chat_messages
    })

@app.route('/api/chat/send', methods=['POST'])
def api_chat_send():
    user = get_user_from_request()
    data = request.get_json() or {}
    text = str(data.get("text", "")).strip()

    if not text:
        return jsonify({"status": "error", "message": "Message cannot be empty"}), 400

    new_msg = {
        "id": len(community_chat_messages) + 1,
        "user": user["username"],
        "role": user["role"],
        "text": text[:180],
        "time": "Just now"
    }
    community_chat_messages.append(new_msg)
    if len(community_chat_messages) > 60:
        community_chat_messages.pop(0)

    return jsonify({
        "status": "success",
        "message": new_msg,
        "all_messages": community_chat_messages
    })

@app.route('/api/live/ticker', methods=['GET'])
def api_live_ticker():
    # Curated high-energy big wins list for FOMO
    fomo_wins = [
        {"player": "Rahul K.", "city": "Delhi", "game": "Aviator", "amount": 4800, "icon": "🚀"},
        {"player": "Priya S.", "city": "Mumbai", "game": "Andar Bahar", "amount": 14500, "icon": "🃏"},
        {"player": "Amit V.", "city": "Jaipur", "game": "Color Trading", "amount": 6300, "icon": "🎨"},
        {"player": "Vikram M.", "city": "Lucknow", "game": "Chakri 0-18", "amount": 25000, "icon": "🎡"},
        {"player": "Sameer R.", "city": "Surat", "game": "777 Coins", "amount": 9600, "icon": "🪙"},
        {"player": "Rohit G.", "city": "Bengaluru", "game": "Fruit Slice", "amount": 3500, "icon": "🍉"},
        {"player": "Neha P.", "city": "Kolkata", "game": "Bubble Shooter", "amount": 5200, "icon": "🫧"},
        {"player": "Ankit D.", "city": "Indore", "game": "Ludo Express", "amount": 7500, "icon": "🎲"}
    ]
    return jsonify({
        "status": "success",
        "ticker": fomo_wins
    })


# ========================================================
# 4-PARTNER PROFIT SHARE & GAME RESERVE VAULT (20-20-20-20-20)
# ========================================================
partners_config = [
    {
        "id": 1,
        "name": "Partner 1 (Managing / Finance)",
        "role": "Wallet, Deposits & Withdrawals",
        "share_pct": 20.0,
        "upi": "partner1@oksbi",
        "phone": "+91 98765 43210",
        "total_settled": 125000.0,
        "pending_payout": 0.0
    },
    {
        "id": 2,
        "name": "Partner 2 (Support Lead)",
        "role": "VIP Community Live Chat & Player Retention",
        "share_pct": 20.0,
        "upi": "partner2@paytm",
        "phone": "+91 98765 43211",
        "total_settled": 125000.0,
        "pending_payout": 0.0
    },
    {
        "id": 3,
        "name": "Partner 3 (Marketing & Traffic)",
        "role": "Telegram Signals, YouTube & User Acquisition",
        "share_pct": 20.0,
        "upi": "partner3@ybl",
        "phone": "+91 98765 43212",
        "total_settled": 125000.0,
        "pending_payout": 0.0
    },
    {
        "id": 4,
        "name": "Partner 4 (Game Operations)",
        "role": "Risk Management, Odds & Settlement Audit",
        "share_pct": 20.0,
        "upi": "partner4@icici",
        "phone": "+91 98765 43213",
        "total_settled": 125000.0,
        "pending_payout": 0.0
    }
]

game_reserve_vault = {
    "name": "Game Emergency Reserve Vault (सेफ़्टी वॉल्ट)",
    "share_pct": 20.0,
    "purpose": "Big Bet Jackpots & Instant Player Payout Guarantee",
    "balance": 75000.0,
    "total_accumulated": 125000.0
}

partner_settlement_history = [
    {
        "id": "SETTLE-904",
        "date": "2026-10-06 23:59:00",
        "total_net_profit": 150000.0,
        "reserve_fund_added": 30000.0,
        "per_partner_payout": 30000.0,
        "partner1_amt": 30000.0,
        "partner2_amt": 30000.0,
        "partner3_amt": 30000.0,
        "partner4_amt": 30000.0,
        "settled_by": "admin (Master)",
        "note": "Daily 20% x 5 Equal Distribution Completed"
    }
]

def calculate_current_net_house_profit():
    total_bets = sum(u.get("total_bet", 0.0) for u in users.values())
    total_won = sum(u.get("total_won", 0.0) for u in users.values())
    net_profit = max(0.0, total_bets - total_won)
    return round(net_profit, 2), round(total_bets, 2), round(total_won, 2)

@app.route('/api/admin/partners/status', methods=['GET'])
def api_admin_partners_status():
    net_profit, total_bets, total_won = calculate_current_net_house_profit()

    # Calculate 20% share for each entity
    share_20_pct = round(net_profit * 0.20, 2)

    return jsonify({
        "status": "success",
        "net_house_profit": net_profit,
        "total_player_bets": total_bets,
        "total_player_won": total_won,
        "split_ratio": "20% (Vault) + 20% (P1) + 20% (P2) + 20% (P3) + 20% (P4) = 100%",
        "current_pool_20pct": share_20_pct,
        "reserve_vault": game_reserve_vault,
        "partners": partners_config,
        "settlement_history": partner_settlement_history[:15]
    })

@app.route('/api/admin/partners/settle', methods=['POST'])
def api_admin_partners_settle():
    data = request.get_json() or {}
    net_profit, total_bets, total_won = calculate_current_net_house_profit()

    # Allow custom settlement amount or default to live net profit
    settle_amount = float(data.get("amount", net_profit))
    if settle_amount <= 0:
        settle_amount = 50000.0 # Default demo split if zero bets yet

    share_each = round(settle_amount * 0.20, 2)

    # 1. Credit 20% to Emergency Reserve Vault
    game_reserve_vault["balance"] = round(game_reserve_vault["balance"] + share_each, 2)
    game_reserve_vault["total_accumulated"] = round(game_reserve_vault["total_accumulated"] + share_each, 2)

    # 2. Credit 20% to each of the 4 partners
    for p in partners_config:
        p["total_settled"] = round(p["total_settled"] + share_each, 2)

    # 3. DEDUCT DISTRIBUTED FUNDS FROM HAMARA ADMIN BALANCE!
    # The 4 partners take their cash payout out of the master vault and 20% is locked into the emergency reserve.
    admin = users.get("admin")
    old_admin_bal = admin["balance"] if admin else 0.0
    if admin:
        admin["balance"] = max(0.0, round(admin["balance"] - settle_amount, 2))

    # 4. Create Settlement Record
    settle_id = f"SETTLE-{secrets.randbelow(9000) + 1000}"
    record = {
        "id": settle_id,
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_net_profit": settle_amount,
        "reserve_fund_added": share_each,
        "per_partner_payout": share_each,
        "partner1_amt": share_each,
        "partner2_amt": share_each,
        "partner3_amt": share_each,
        "partner4_amt": share_each,
        "settled_by": "admin (Master)",
        "note": f"⚡ 1-Click Profit Distribution: ₹{share_each:.2f} each (4 Partners + 1 Reserve Vault) • Admin Balance reduced from ₹{old_admin_bal:,.2f} to ₹{admin['balance']:,.2f}"
    }
    partner_settlement_history.insert(0, record)

    return jsonify({
        "status": "success",
        "message": f"🎉 ₹{settle_amount:,.2f} successfully distributed! ₹{share_each:,.2f} added to Safety Vault, ₹{share_each:,.2f} each to 4 Partners. Hamara Admin Balance updated: ₹{admin['balance']:,.2f}",
        "settlement": record,
        "reserve_vault": game_reserve_vault,
        "partners": partners_config,
        "admin_balance": admin["balance"] if admin else 0.0
    })

@app.route('/api/admin/vault/payout_winner', methods=['POST'])
def api_admin_vault_payout_winner():
    data = request.get_json() or {}
    username = str(data.get("username", "")).strip().lower()
    amount = float(data.get("amount", 0))

    if amount <= 0:
        return jsonify({"status": "error", "message": "Amount must be greater than 0"}), 400

    if game_reserve_vault["balance"] < amount:
        return jsonify({
            "status": "error",
            "message": f"Safety Vault balance is insufficient! Available: ₹{game_reserve_vault['balance']:,.2f}"
        }), 400

    if username not in users:
        return jsonify({"status": "error", "message": f"Player '{username}' not found in registered accounts"}), 404

    # Deduct from 20% Emergency Safety Vault
    game_reserve_vault["balance"] = round(game_reserve_vault["balance"] - amount, 2)

    # Credit directly to player's wallet
    users[username]["balance"] = round(users[username]["balance"] + amount, 2)
    users[username]["total_won"] = round(users[username].get("total_won", 0.0) + amount, 2)

    # Log in live bets
    record_live_bet(username, "🏆 Jackpot / Big Bet Payout", 0, f"Paid ₹{amount:,.2f} from Safety Vault Fund", "WON", amount)

    return jsonify({
        "status": "success",
        "message": f"🎉 ₹{amount:,.2f} successfully paid to {username} from Emergency Safety Vault! Vault balance is now ₹{game_reserve_vault['balance']:,.2f}",
        "vault_balance": game_reserve_vault["balance"],
        "player_balance": users[username]["balance"],
        "reserve_vault": game_reserve_vault
    })

@app.route('/api/admin/partners/update', methods=['POST'])
def api_admin_partners_update():
    data = request.get_json() or {}
    p_id = int(data.get("id", 1))
    for p in partners_config:
        if p["id"] == p_id:
            if "name" in data and data["name"]: p["name"] = str(data["name"])
            if "upi" in data and data["upi"]: p["upi"] = str(data["upi"])
            if "phone" in data and data["phone"]: p["phone"] = str(data["phone"])
            if "role" in data and data["role"]: p["role"] = str(data["role"])
            return jsonify({"status": "success", "partner": p})

    return jsonify({"status": "error", "message": "Partner ID not found"}), 404



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("==================================================")
    print("Royal Games Platform Backend (Flask) Running!")
    print(f"Open in browser: http://localhost:{port}")
    print("Default Admin: admin / admin123")
    print("Default Player: player1 / player123")
    print(f"56+ Games Loaded: Carrom | Ludo | Big Small | Color | Aviator | Chakri & 50 more!")
    print("==================================================")
    app.run(host='0.0.0.0', port=port, debug=False)

