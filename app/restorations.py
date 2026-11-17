"""Server-verified restoration submission and persistence."""

import hashlib
import json
import sqlite3
from dataclasses import dataclass

from flask import Blueprint, jsonify, request, url_for
from flask_login import current_user, login_required

from app.db import get_db
from app.rules import AGED_VARNISH, OVERPAINT, SURFACE_DIRT, PaintingGrid

restorations_bp = Blueprint("restorations", __name__)
VALID_LAYERS = {SURFACE_DIRT, OVERPAINT, AGED_VARNISH}
RATIO_KEYS = ("water_ratio", "oil_ratio", "acid_ratio")


@dataclass(frozen=True)
class VerifiedRestoration:
    """Server-calculated state ready for one persistence transaction."""

    integrity: float
    clue_accuracy: float
    final_score: float
    layers_restored_count: int


def _invalid(message):
    return ValueError(message)


def _read_move(move):
    if not isinstance(move, dict):
        raise _invalid("Each move must be an object.")
    x, y, layer = move.get("x"), move.get("y"), move.get("layer")
    mixture, tool = move.get("solvent_mixture"), move.get("tool")
    if any(
        not isinstance(value, int) or isinstance(value, bool)
        for value in (x, y, layer)
    ):
        raise _invalid("Move coordinates and layer must be integers.")
    if not 0 <= x < 4 or not 0 <= y < 4 or layer not in VALID_LAYERS:
        raise _invalid("Move coordinates or layer are invalid.")
    if not isinstance(mixture, dict) or not isinstance(tool, str):
        raise _invalid("Move mixture and tool are required.")
    if any(
        not isinstance(mixture.get(key), int) or isinstance(mixture.get(key), bool)
        for key in RATIO_KEYS
    ):
        raise _invalid("Solvent ratios must be integers.")
    return layer, (y, x), {key: mixture[key] for key in RATIO_KEYS}, tool


def replay_moves(moves):
    """Replay client moves through the authoritative domain model."""
    if not isinstance(moves, list) or not moves:
        raise _invalid("At least one move is required.")
    grid = PaintingGrid()
    for move in moves:
        layer, coordinate, mixture, tool = _read_move(move)
        grid.apply_move(layer, coordinate, mixture, tool)
    completed = sum(grid.layer_complete(layer) for layer in VALID_LAYERS)
    return VerifiedRestoration(
        integrity=grid.integrity,
        clue_accuracy=grid.clue_accuracy,
        final_score=grid.final_score,
        layers_restored_count=completed,
    )


def _fingerprint(payload):
    canonical_payload = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_payload.encode()).hexdigest()


def _read_submission(payload):
    if not isinstance(payload, dict):
        raise _invalid("A JSON object is required.")
    artwork_id = payload.get("artwork_id")
    mode = payload.get("mode")
    elapsed = payload.get("time_seconds")
    image_data = payload.get("restored_image_data")
    if not isinstance(artwork_id, str) or not artwork_id:
        raise _invalid("Artwork is required.")
    if mode != "casual":
        raise _invalid("Only casual mode is available.")
    if not isinstance(elapsed, int) or isinstance(elapsed, bool) or elapsed < 0:
        raise _invalid("Elapsed time must be a non-negative integer.")
    if not isinstance(image_data, str) or not image_data.startswith(
        "data:image/png;base64,"
    ):
        raise _invalid("A PNG canvas export is required.")
    if len(image_data) > 3_000_000:
        raise _invalid("Canvas export is too large.")
    moves = payload.get("moves")
    return artwork_id, mode, elapsed, image_data, moves


@restorations_bp.post("/api/restorations")
@login_required
def save_restoration():
    """Replay and atomically save a user-owned restoration result."""
    try:
        payload = request.get_json(silent=True)
        artwork_id, mode, elapsed, image_data, moves = _read_submission(payload)
        fingerprint = _fingerprint(payload)
        verified = replay_moves(moves)
    except ValueError as error:
        return jsonify(error=str(error)), 400
    if verified.layers_restored_count != len(VALID_LAYERS):
        return (
            jsonify(
                error="Complete all three layers before saving.",
                layers_restored_count=verified.layers_restored_count,
            ),
            422,
        )

    database = get_db()
    try:
        database.execute("BEGIN IMMEDIATE")
        existing = database.execute(
            "SELECT match_id FROM restoration_matches "
            "WHERE user_id = ? AND submission_fingerprint = ?",
            (current_user.user_id, fingerprint),
        ).fetchone()
        if existing:
            database.commit()
            return jsonify(
                match_id=existing["match_id"],
                result_url=url_for("results", match_id=existing["match_id"]),
                duplicate=True,
            )
        cursor = database.execute(
            """
            INSERT INTO restoration_matches (
                user_id, artwork_id, mode, final_integrity_score, clue_accuracy,
                final_score, layers_restored_count, time_seconds,
                restored_image_data, submission_fingerprint
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                current_user.user_id,
                artwork_id,
                mode,
                verified.integrity,
                verified.clue_accuracy,
                verified.final_score,
                verified.layers_restored_count,
                elapsed,
                image_data,
                fingerprint,
            ),
        )
        database.commit()
    except sqlite3.IntegrityError:
        database.rollback()
        existing = database.execute(
            "SELECT match_id FROM restoration_matches "
            "WHERE user_id = ? AND submission_fingerprint = ?",
            (current_user.user_id, fingerprint),
        ).fetchone()
        if existing:
            return jsonify(
                match_id=existing["match_id"],
                result_url=url_for("results", match_id=existing["match_id"]),
                duplicate=True,
            )
        raise
    return (
        jsonify(
            match_id=cursor.lastrowid,
            result_url=url_for("results", match_id=cursor.lastrowid),
            duplicate=False,
        ),
        201,
    )
