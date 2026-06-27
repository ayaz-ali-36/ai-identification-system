# services/face_service.py
# ─────────────────────────────────────────
# Handles all face detection and embedding
# extraction. Every route that processes a
# photo calls functions from this file.
# Centralizing this logic means DeepFace is
# only configured in one place.
# ─────────────────────────────────────────

from deepface import DeepFace
import json
import numpy as np
from config import Config


class FaceExtractionError(Exception):
    """Custom error for face extraction failures.
    Lets routes catch this specifically and return
    a clear message to the user instead of a generic
    500 server error."""
    pass


def extract_embedding(image_path):
    """
    Extracts a face embedding from a photo.

    Returns: dict with embedding (list of 128 floats)
    Raises: FaceExtractionError if no face or
            multiple faces are detected.
    """
    try:
        results = DeepFace.represent(
            img_path=image_path,
            model_name=Config.FACE_MODEL,
            detector_backend=Config.FACE_DETECTOR,
            enforce_detection=True   # raises error if no face found
        )
    except ValueError as e:
        # DeepFace raises ValueError when no face is detected
        raise FaceExtractionError(
            "No face detected in the photo. "
            "Please upload a clear photo showing the face."
        )

    # DeepFace returns a list — one entry per face found
    if len(results) == 0:
        raise FaceExtractionError(
            "No face detected in the photo."
        )

    if len(results) > 1:
        # Multiple faces — pick the largest one
        # (closest to camera = most likely the subject)
        results.sort(
            key=lambda r: r['facial_area']['w'] * r['facial_area']['h'],
            reverse=True
        )
        # We use the largest face but warn the caller
        chosen = results[0]
        return {
            "embedding": chosen["embedding"],
            "warning": f"{len(results)} faces detected. Used the largest face.",
            "face_confidence": chosen.get("face_confidence", None)
        }

    # Exactly one face — the clean case
    chosen = results[0]
    return {
        "embedding": chosen["embedding"],
        "warning": None,
        "face_confidence": chosen.get("face_confidence", None)
    }


def embedding_to_json(embedding):
    """Converts embedding list to JSON string for SQLite storage."""
    return json.dumps(embedding)


def json_to_embedding(embedding_json):
    """Converts JSON string back to numpy array for comparison."""
    return np.array(json.loads(embedding_json))


def compare_embeddings(embedding1, embedding2):
    """
    Compares two embeddings using cosine similarity.
    Returns a score from 0 to 100.
    """
    from sklearn.metrics.pairwise import cosine_similarity

    arr1 = np.array(embedding1).reshape(1, -1)
    arr2 = np.array(embedding2).reshape(1, -1)

    raw_score = cosine_similarity(arr1, arr2)[0][0]

    # Normalize from [-1, 1] range to [0, 100] range
    # This is the normalization fix from your senior's feedback
    normalized_score = ((raw_score + 1) / 2) * 100

    return round(normalized_score, 2)