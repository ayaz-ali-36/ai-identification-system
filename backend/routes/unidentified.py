# routes/unidentified.py
# ─────────────────────────────────────────
# Unidentified person reporting routes.
# PROTECTED — hospital login required.
# Hospital staff report unknown patients/bodies.
# ─────────────────────────────────────────

import os
import time
from werkzeug.utils import secure_filename
from flask import Blueprint, request, jsonify
from database import get_db
from config import Config
from middleware.auth_middleware import token_required
from services.face_service import (
    extract_embedding,
    embedding_to_json,
    FaceExtractionError
)

unidentified_bp = Blueprint('unidentified', __name__)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# ── Report Unidentified Person ────────────
@unidentified_bp.route('/unidentified-persons', methods=['POST'])
@token_required
def report_unidentified():
    """
    Protected route. Hospital login required.
    Expects multipart/form-data with:
      - photo (file)
      - estimated_age, gender, height_cm, weight_kg
      - found_location, description
    Reporter is the logged-in hospital user.
    """
    # ── Validate photo ────────────────────
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

    # ── Save photo ────────────────────────
    filename = secure_filename(photo.filename)
    unique_filename = f"{int(time.time())}_{filename}"
    save_path = os.path.join(Config.UNIDENTIFIED_FOLDER, unique_filename)

    os.makedirs(Config.UNIDENTIFIED_FOLDER, exist_ok=True)
    photo.save(save_path)

    # ── Extract face embedding ────────────
    try:
        result = extract_embedding(save_path)
    except FaceExtractionError as e:
        os.remove(save_path)
        return jsonify({
            "success": False,
            "message": str(e)
        }), 422

    embedding_json = embedding_to_json(result["embedding"])

    # ── Save to database ──────────────────
    db = get_db()
    submitted_by = request.current_user['user_id']

    cursor = db.execute('''
        INSERT INTO unidentified_persons (
            submitted_by, estimated_age, gender,
            height_cm, weight_kg,
            found_location, description, image_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        submitted_by,
        request.form.get('estimated_age'),
        request.form.get('gender'),
        request.form.get('height_cm'),
        request.form.get('weight_kg'),
        request.form.get('found_location'),
        request.form.get('description'),
        unique_filename
    ))
    db.commit()
    case_id = cursor.lastrowid

    # ── Save embedding ────────────────────
    db.execute('''
        INSERT INTO face_embeddings (person_type, person_id, embedding)
        VALUES (?, ?, ?)
    ''', ('unidentified', case_id, embedding_json))
    db.commit()

    # ── Log the action ────────────────────
    db.execute('''
        INSERT INTO audit_logs (user_id, action, details)
        VALUES (?, ?, ?)
    ''', (submitted_by, 'REPORT_UNIDENTIFIED',
          f"Unidentified case {case_id} submitted"))
    db.commit()
    db.close()

    response = {
        "success": True,
        "message": "Unidentified person reported successfully",
        "case_id": case_id
    }

    if result.get("warning"):
        response["warning"] = result["warning"]

    return jsonify(response), 201


# ── Get Single Unidentified Case ──────────
@unidentified_bp.route('/unidentified-persons/<int:case_id>', methods=['GET'])
@token_required
def get_unidentified_person(case_id):
    db = get_db()

    person = db.execute(
        "SELECT * FROM unidentified_persons WHERE id = ?",
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


# ── List All Unidentified Cases ───────────
@unidentified_bp.route('/unidentified-persons', methods=['GET'])
@token_required
def list_unidentified_persons():
    db = get_db()

    persons = db.execute('''
        SELECT id, estimated_age, gender,
               found_location, status, created_at
        FROM unidentified_persons
        ORDER BY created_at DESC
    ''').fetchall()

    db.close()

    return jsonify({
        "success": True,
        "count": len(persons),
        "cases": [dict(p) for p in persons]
    }), 200