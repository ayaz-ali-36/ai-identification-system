# routes/auth.py
# ─────────────────────────────────────────
# Authentication routes.
# POST /api/register → create account
# POST /api/login    → get JWT token
# GET  /api/profile  → get current user
# ─────────────────────────────────────────

import jwt
import bcrypt
from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from database import get_db
from config import Config
from middleware.auth_middleware import token_required

auth_bp = Blueprint('auth', __name__)


# ── Register ──────────────────────────────
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate required fields
    required = ['full_name', 'email', 'password', 'role']
    for field in required:
        if not data.get(field):
            return jsonify({
                "success": False,
                "message": f"{field} is required"
            }), 400

    # Validate role
    allowed_roles = ['family', 'hospital', 'admin']
    if data['role'] not in allowed_roles:
        return jsonify({
            "success": False,
            "message": "Invalid role. Use: family, hospital, admin"
        }), 400

    db = get_db()

    # Check email already exists
    existing = db.execute(
        "SELECT id FROM users WHERE email = ?",
        (data['email'],)
    ).fetchone()

    if existing:
        db.close()
        return jsonify({
            "success": False,
            "message": "Email already registered"
        }), 409

    # Hash the password — never store plain text
    password_hash = bcrypt.hashpw(
        data['password'].encode('utf-8'),
        bcrypt.gensalt()
    ).decode('utf-8')

    # Save to database
    cursor = db.execute(
        '''INSERT INTO users (full_name, email, password_hash, role)
           VALUES (?, ?, ?, ?)''',
        (data['full_name'], data['email'], password_hash, data['role'])
    )
    db.commit()
    user_id = cursor.lastrowid

    # Log the action
    db.execute(
        "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
        (user_id, "REGISTER", f"New {data['role']} account created")
    )
    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Account created successfully",
        "user_id": user_id
    }), 201


# ── Login ─────────────────────────────────
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return jsonify({
            "success": False,
            "message": "Email and password required"
        }), 400

    db = get_db()

    # Find user by email
    user = db.execute(
        "SELECT * FROM users WHERE email = ?",
        (data['email'],)
    ).fetchone()

    if not user:
        db.close()
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    # Verify password
    password_match = bcrypt.checkpw(
        data['password'].encode('utf-8'),
        user['password_hash'].encode('utf-8')
    )

    if not password_match:
        db.close()
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    # Generate JWT token
    payload = {
        "user_id": user['id'],
        "email":   user['email'],
        "role":    user['role'],
        "name":    user['full_name'],
        "exp":     datetime.now(timezone.utc) + Config.JWT_EXPIRY
    }

    token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")

    # Log the action
    db.execute(
        "INSERT INTO audit_logs (user_id, action, details) VALUES (?, ?, ?)",
        (user['id'], "LOGIN", "User logged in")
    )
    db.commit()
    db.close()

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id":    user['id'],
            "name":  user['full_name'],
            "email": user['email'],
            "role":  user['role']
        }
    }), 200


# ── Profile ───────────────────────────────
@auth_bp.route('/profile', methods=['GET'])
@token_required
def profile():
    user_data = request.current_user
    db = get_db()

    user = db.execute(
        "SELECT id, full_name, email, role, created_at FROM users WHERE id = ?",
        (user_data['user_id'],)
    ).fetchone()

    db.close()

    if not user:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    return jsonify({
        "success": True,
        "user": {
            "id":         user['id'],
            "name":       user['full_name'],
            "email":      user['email'],
            "role":       user['role'],
            "created_at": user['created_at']
        }
    }), 200