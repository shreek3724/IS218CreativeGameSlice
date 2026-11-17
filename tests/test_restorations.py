"""Focused server-verification tests for restoration submissions."""

import re
from pathlib import Path

import pytest

from app import create_app
from app.db import get_db
from app.rules import (
    AGED_VARNISH,
    BORDER_CELLS,
    LOW_RISK_CELLS,
    OVERPAINT,
    SURFACE_DIRT,
)


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE_PATH": Path(tmp_path) / "test.db",
        }
    )


def login_client(app, client, username):
    with app.app_context():
        database = get_db()
        cursor = database.execute(
            "INSERT INTO user_accounts (username, display_name, password_hash) "
            "VALUES (?, ?, ?)",
            (username, username, "unused"),
        )
        token = f"{username}-token"
        database.execute(
            "INSERT INTO login_sessions (user_id, session_token) VALUES (?, ?)",
            (cursor.lastrowid, token),
        )
        database.commit()
    with client.session_transaction() as session:
        session["_user_id"] = token
        session["_fresh"] = True


def csrf_token(client):
    response = client.get("/play")
    token = re.search(r'name="csrf-token" content="([^"]+)"', response.text)
    return token.group(1)


def valid_moves():
    moves = []
    for layer, zone, mixture, tool in (
        (
            SURFACE_DIRT,
            LOW_RISK_CELLS,
            {"water_ratio": 70, "oil_ratio": 30, "acid_ratio": 0},
            "swab",
        ),
        (
            OVERPAINT,
            LOW_RISK_CELLS,
            {"water_ratio": 20, "oil_ratio": 70, "acid_ratio": 10},
            "brush",
        ),
        (
            AGED_VARNISH,
            BORDER_CELLS,
            {"water_ratio": 10, "oil_ratio": 20, "acid_ratio": 70},
            "heat_lamp",
        ),
    ):
        moves.extend(
            {
                "x": column,
                "y": row,
                "layer": layer,
                "solvent_mixture": mixture,
                "tool": tool,
            }
            for row, column in sorted(zone)
        )
    return moves


def payload():
    return {
        "artwork_id": "golden-valley",
        "mode": "casual",
        "time_seconds": 60,
        "moves": valid_moves(),
        "restored_image_data": "data:image/png;base64,verified-test-image",
    }


def test_csrf_protects_restoration_save(app):
    client = app.test_client()
    login_client(app, client, "first")
    assert client.post("/api/restorations", json=payload()).status_code == 400


def test_incomplete_restoration_is_not_saved(app):
    client = app.test_client()
    login_client(app, client, "partial")
    response = client.post(
        "/api/restorations",
        json={**payload(), "moves": valid_moves()[:1]},
        headers={"X-CSRFToken": csrf_token(client)},
    )
    assert response.status_code == 422
    assert response.json["layers_restored_count"] == 0


def test_save_replays_moves_idempotently_and_enforces_ownership(app):
    owner = app.test_client()
    login_client(app, owner, "owner")
    headers = {"X-CSRFToken": csrf_token(owner)}
    first = owner.post("/api/restorations", json=payload(), headers=headers)
    assert first.status_code == 201
    match_id = first.json["match_id"]
    duplicate = owner.post("/api/restorations", json=payload(), headers=headers)
    assert duplicate.status_code == 200
    assert duplicate.json["match_id"] == match_id
    results = owner.get(first.json["result_url"])
    assert b"100%" in results.data
    assert b"3 / 3 layers restored" in results.data

    other = app.test_client()
    login_client(app, other, "other")
    assert other.get(first.json["result_url"]).status_code == 404
