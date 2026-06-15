# app.py
# ─────────────────────────────────────────
# Main Flask application entry point.
# Registers all routes and initializes
# the database on startup.
# ─────────────────────────────────────────

from flask import Flask
from flask_cors import CORS
from config import Config
from database import init_db

# ── Import all route blueprints ───────────
from routes.auth         import auth_bp
from routes.missing      import missing_bp
from routes.unidentified import unidentified_bp
from routes.matching     import matching_bp
from routes.admin        import admin_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Enable CORS for Next.js frontend ──
    CORS(app, resources={
        r"/api/*": {
            "origins": ["http://localhost:3000"],
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # ── Register all blueprints ───────────
    app.register_blueprint(auth_bp,         url_prefix="/api")
    app.register_blueprint(missing_bp,      url_prefix="/api")
    app.register_blueprint(unidentified_bp, url_prefix="/api")
    app.register_blueprint(matching_bp,     url_prefix="/api")
    app.register_blueprint(admin_bp,        url_prefix="/api")

    # ── Initialize database ───────────────
    with app.app_context():
        init_db()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )