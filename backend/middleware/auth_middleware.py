# middleware/auth_middleware.py
# ─────────────────────────────────────────
# JWT verification middleware.
# Any route that needs login protection
# uses the token_required decorator.
# ─────────────────────────────────────────

import jwt
from functools import wraps
from flask import request, jsonify
from config import Config

def token_required(f):
    """
    Decorator that protects routes.
    Usage: add @token_required above any route.
    Automatically extracts user from JWT token.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Token comes in Authorization header
        # Format: "Bearer eyJhbGci..."
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

        if not token:
            return jsonify({
                "success": False,
                "message": "Access denied. Token required."
            }), 401

        try:
            # Decode and verify the token
            payload = jwt.decode(
                token,
                Config.SECRET_KEY,
                algorithms=["HS256"]
            )
            # Attach user info to request
            request.current_user = payload

        except jwt.ExpiredSignatureError:
            return jsonify({
                "success": False,
                "message": "Token expired. Please login again."
            }), 401

        except jwt.InvalidTokenError:
            return jsonify({
                "success": False,
                "message": "Invalid token."
            }), 401

        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """
    Restricts route to admin role only.
    Always use AFTER @token_required.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if request.current_user.get("role") != "admin":
            return jsonify({
                "success": False,
                "message": "Admin access required."
            }), 403
        return f(*args, **kwargs)
    return decorated