# database.py
# ─────────────────────────────────────────
# Handles all database connection and
# schema creation. Every table your system
# needs is defined here in one place.
# ─────────────────────────────────────────

import sqlite3
from config import Config

def get_db():
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # ── Users table ───────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name     TEXT    NOT NULL,
            email         TEXT    NOT NULL UNIQUE,
            password_hash TEXT    NOT NULL,
            role          TEXT    NOT NULL DEFAULT 'family',
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Missing persons table ─────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS missing_persons (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name           TEXT    NOT NULL,
            age                 INTEGER,
            gender              TEXT,
            height_cm           REAL,
            weight_kg           REAL,
            last_seen_location  TEXT,
            date_missing        TEXT,
            description         TEXT,
            image_path          TEXT,
            status              TEXT    DEFAULT 'active',
            reporter_name       TEXT    NOT NULL,
            reporter_phone      TEXT,
            reporter_email      TEXT,
            reporter_relation   TEXT,
            user_id             INTEGER DEFAULT NULL,
            created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # ── Unidentified persons table ────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unidentified_persons (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            submitted_by    INTEGER NOT NULL,
            estimated_age   INTEGER,
            gender          TEXT,
            height_cm       REAL,
            weight_kg       REAL,
            found_location  TEXT,
            description     TEXT,
            image_path      TEXT,
            status          TEXT    DEFAULT 'active',
            created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (submitted_by) REFERENCES users(id)
        )
    ''')

    # ── Face embeddings table ─────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS face_embeddings (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            person_type  TEXT    NOT NULL,
            person_id    INTEGER NOT NULL,
            embedding    TEXT    NOT NULL,
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ── Matches table ─────────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS matches (
            id                     INTEGER PRIMARY KEY AUTOINCREMENT,
            missing_person_id      INTEGER NOT NULL,
            unidentified_person_id INTEGER NOT NULL,
            face_score             REAL    DEFAULT 0,
            age_score              REAL    DEFAULT 0,
            gender_score           REAL    DEFAULT 0,
            location_score         REAL    DEFAULT 0,
            text_score             REAL    DEFAULT 0,
            final_score            REAL    DEFAULT 0,
            match_status           TEXT    DEFAULT 'pending',
            created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (missing_person_id)      REFERENCES missing_persons(id),
            FOREIGN KEY (unidentified_person_id) REFERENCES unidentified_persons(id)
        )
    ''')

    # ── Audit logs table ──────────────────
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_logs (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            action     TEXT    NOT NULL,
            details    TEXT,
            timestamp  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("✅ Database initialized — all tables ready")