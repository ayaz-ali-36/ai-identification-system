# config.py
# ─────────────────────────────────────────
# Central configuration for the entire app.
# All settings live here — never scattered
# across files.
# ─────────────────────────────────────────

import os
from datetime import timedelta

class Config:
    # ── Security ──────────────────────────
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_EXPIRY  = timedelta(hours=24)

    # ── Database ──────────────────────────
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), "database.db")

    # ── File uploads ──────────────────────
    UPLOAD_FOLDER         = os.path.join(os.path.dirname(__file__), "uploads")
    MISSING_FOLDER        = os.path.join(UPLOAD_FOLDER, "missing")
    UNIDENTIFIED_FOLDER   = os.path.join(UPLOAD_FOLDER, "unidentified")
    ALLOWED_EXTENSIONS    = {"png", "jpg", "jpeg", "webp"}
    MAX_CONTENT_LENGTH    = 16 * 1024 * 1024  # 16MB max upload

    # ── AI Model ──────────────────────────
    FACE_MODEL            = "Facenet"
    FACE_DETECTOR         = "opencv"

    # ── Multimodal weights ────────────────
    WEIGHT_FACE           = 0.70
    WEIGHT_AGE            = 0.10
    WEIGHT_GENDER         = 0.05
    WEIGHT_LOCATION       = 0.05
    WEIGHT_TEXT           = 0.10

    # ── Match threshold ───────────────────
    MATCH_THRESHOLD       = 60.0  # minimum score to create a match