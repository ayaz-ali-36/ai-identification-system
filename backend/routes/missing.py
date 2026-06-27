# routes/missing.py
# ─────────────────────────────────────────
# Missing person reporting routes.
# PUBLIC — no login required.
# Anyone can report: family, authority, stranger.
# ─────────────────────────────────────────

import os
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from database import get_db
from config import Config
from services.face_service import (
    extract_embedding,
    embedding_to_json,
    FaceExtractionError
)

missing_bp = Blueprint('missing', __name__)


def allowed_file(filename):
    """Checks file extension is safe to accept."""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ── Report Missing Person ─────────────────
@missing_bp.route('/missing-persons', methods=['POST'])
def report_missing():
    """
    Public route. No login required.
    Expects multipart/form-data with:
      - photo (file)
      - full_name, age, gender, height_cm, weight_kg
      - last_seen_location, date_missing, description
      - reporter_name, reporter_phone, reporter_email,
        reporter_relation
    """
    # ── Validate photo was sent ───────────
    if 'photo' not in request.files:
        return jsonify({
            "success": False,
            "message": "Photo is required"
        }), 400

    photo = request.files['photo']

    if photo.filename == '':
        return jsonify({
            "success": False,
            "message": "No photo selected"
        }), 400

    if not allowed_file(photo.filename):
        return jsonify({
            "success": False,
            "message": "Invalid file type. Use jpg, jpeg, png, or webp."
        }), 400

    # ── Validate required text fields ─────
    required_fields = ['full_name', 'reporter_name']
    for field in required_fields:
        if not request.form.get(field):
            return jsonify({
                "success": False,
                "message": f"{field} is required"
            }), 400

    # ── Save photo to disk ────────────────
    filename = secure_filename(photo.filename)
    # Prefix with timestamp to avoid duplicate filenames
    import time
    unique_filename = f"{int(time.time())}_{filename}"
    save_path = os.path.join(Config.MISSING_FOLDER, unique_filename)

    os.makedirs(Config.MISSING_FOLDER, exist_ok=True)
    photo.save(save_path)

    # ── Extract face embedding ────────────
    try:
        result = extract_embedding(save_path)
    except FaceExtractionError as e:
        # Clean up the saved photo since we cannot use it
        os.remove(save_path)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 422  # 422 = valid request but cannot process

    embedding_json = embedding_to_json(result["embedding"])

    # ── Save to database ───────────────────
    db = get_db()

    cursor = db.execute('''
        INSERT INTO missing_persons (
            full_name, age, gender, height_cm, weight_kg,
            last_seen_location, date_missing, description,
            image_path, reporter_name, reporter_phone,
            reporter_email, reporter_relation
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        request.form.get('full_name'),
        request.form.get('age'),
        request.form.get('gender'),
        request.form.get('height_cm'),
        request.form.get('weight_kg'),
        request.form.get('last_seen_location'),
        request.form.get('date_missing'),
        request.form.get('description'),
        unique_filename,
        request.form.get('reporter_name'),
        request.form.get('reporter_phone'),
        request.form.get('reporter_email'),
        request.form.get('reporter_relation')
    ))
    db.commit()
    case_id = cursor.lastrowid

    # ── Save embedding linked to this case ─
    db.execute('''
        INSERT INTO face_embeddings (person_type, person_id, embedding)
        VALUES (?, ?, ?)
    ''', ('missing', case_id, embedding_json))
    db.commit()

    # ── Log the action ─────────────────────
    db.execute('''
        INSERT INTO audit_logs (action, details)
        VALUES (?, ?)
    ''', ('REPORT_MISSING', f"Case {case_id} reported by {request.form.get('reporter_name')}"))
    db.commit()
    db.close()

    # ── Build response ─────────────────────
    response = {
        "success": True,
        "message": "Missing person reported successfully",
        "case_id": case_id,
        "track_url": f"/case/{case_id}"
    }

    if result.get("warning"):
        response["warning"] = result["warning"]

    return jsonify(response), 201


# ── Get Single Case (public — for tracking) ─
@missing_bp.route('/missing-persons/<int:case_id>', methods=['GET'])
def get_missing_person(case_id):
    db = get_db()

    person = db.execute(
        "SELECT * FROM missing_persons WHERE id = ?",
        (case_id,)
    ).fetchone()

    db.close()

    if not person:
        return jsonify({
            "success": False,
            "message": "Case not found"
        }), 404

    return jsonify({
        "success": True,
        "case": dict(person)
    }), 200


# ── List All Missing Persons ──────────────
@missing_bp.route('/missing-persons', methods=['GET'])
def list_missing_persons():
    db = get_db()

    persons = db.execute(
        "SELECT id, full_name, age, gender, last_seen_location, status, created_at FROM missing_persons ORDER BY created_at DESC"
    ).fetchall()

    db.close()

    return jsonify({
        "success": True,
        "count": len(persons),
        "cases": [dict(p) for p in persons]
    }), 200