"""Flask application factory."""

import os
from pathlib import Path

from flask import Flask, abort, render_template
from flask_login import LoginManager, current_user, login_required
from flask_wtf.csrf import CSRFProtect

from app.auth import auth_bp, load_user
from app.db import get_db, init_app_database
from app.forms import LogoutForm
from app.restorations import restorations_bp

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.user_loader(load_user)


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
    csrf.init_app(app)
    login_manager.init_app(app)
    app.register_blueprint(auth_bp)
    app.register_blueprint(restorations_bp)

    @app.context_processor
    def inject_logout_form():
        return {"logout_form": LogoutForm()}

    @app.get("/")
    def home():
        return render_template("home.html")

    @app.get("/play")
    @login_required
    def play():
        return render_template("play.html")

    @app.get("/results/<int:match_id>")
    @login_required
    def results(match_id):
        match = get_db().execute(
            "SELECT match_id, artwork_id, final_integrity_score, clue_accuracy, "
            "final_score, layers_restored_count, restored_image_data "
            "FROM restoration_matches "
            "WHERE match_id = ? AND user_id = ?",
            (match_id, current_user.user_id),
        ).fetchone()
        if not match:
            abort(404)
        return render_template("results.html", match=match)

    return app
