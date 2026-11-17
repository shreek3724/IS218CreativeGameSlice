"""SQLite lifecycle and schema for Art Conservator."""

import sqlite3

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS user_accounts (
    user_id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    total_paintings_restored INTEGER NOT NULL DEFAULT 0,
    unlocked_artworks TEXT NOT NULL DEFAULT '[]',
    unlocked_tools TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS login_sessions (
    session_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_token TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_accounts (user_id)
);
CREATE TABLE IF NOT EXISTS restoration_matches (
    match_id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    artwork_id TEXT NOT NULL,
    mode TEXT NOT NULL CHECK (mode IN ('casual', 'timed')),
    final_integrity_score REAL NOT NULL,
    clue_accuracy REAL NOT NULL,
    final_score REAL NOT NULL,
    layers_restored_count INTEGER NOT NULL,
    time_seconds INTEGER NOT NULL,
    restored_image_data TEXT NOT NULL,
    submission_fingerprint TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user_accounts (user_id)
);
"""


def get_db():
    """Return one SQLite connection per Flask request."""
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    """Close the request-scoped connection."""
    database = g.pop("db", None)
    if database:
        database.close()


def init_app_database(app):
    """Register database lifecycle hooks and create the schema."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        get_db().executescript(SCHEMA)
        columns = {
            row["name"]
            for row in get_db().execute("PRAGMA table_info(restoration_matches)")
        }
        if "submission_fingerprint" not in columns:
            get_db().execute(
                "ALTER TABLE restoration_matches "
                "ADD COLUMN submission_fingerprint TEXT"
            )
        get_db().execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS "
            "restoration_matches_user_fingerprint ON restoration_matches "
            "(user_id, submission_fingerprint)"
        )
        get_db().commit()
