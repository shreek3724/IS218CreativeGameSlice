"""Flask application factory."""

import os
from pathlib import Path

from flask import Flask, render_template

from app.db import init_app_database


def create_app(test_config=None):
    """Create the configured application and initialize its database."""
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "development-only-change-me"),
        DATABASE_PATH=os.environ.get(
            "DATABASE_PATH", Path(app.instance_path) / "art_conservator.db"
        ),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    init_app_database(app)

    @app.get("/")
    def home():
        return render_template("home.html")

    return app
