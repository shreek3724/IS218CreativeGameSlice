"""Authentication routes and revocable database sessions."""

import secrets
import sqlite3
from dataclasses import dataclass

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import UserMixin, current_user, login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db
from app.forms import LoginForm, LogoutForm, SignupForm

auth_bp = Blueprint("auth", __name__)


@dataclass
class User(UserMixin):
    """Authenticated account tied to one revocable database session."""

    user_id: int
    username: str
    display_name: str
    session_token: str

    def get_id(self):
        return self.session_token


def load_user(session_token):
    """Load only an active session token for Flask-Login."""
    row = get_db().execute(
        """
        SELECT u.user_id, u.username, u.display_name, s.session_token
        FROM user_accounts AS u JOIN login_sessions AS s ON s.user_id = u.user_id
        WHERE s.session_token = ? AND s.is_active = 1
        """,
        (session_token,),
    ).fetchone()
    return User(**dict(row)) if row else None


def create_session(user_id):
    """Persist and return a new server-generated active session token."""
    token = secrets.token_urlsafe(32)
    database = get_db()
    database.execute(
        "INSERT INTO login_sessions (user_id, session_token) VALUES (?, ?)",
        (user_id, token),
    )
    database.commit()
    return token


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    """Create a local account with clear validation feedback."""
    form = SignupForm()
    if form.validate_on_submit():
        try:
            get_db().execute(
                """
                INSERT INTO user_accounts (username, display_name, password_hash)
                VALUES (?, ?, ?)
                """,
                (
                    form.username.data.lower(),
                    form.display_name.data.strip(),
                    generate_password_hash(form.password.data),
                ),
            )
            get_db().commit()
        except sqlite3.IntegrityError:
            get_db().rollback()
            form.username.errors.append(
                "That username is already taken. Choose another."
            )
        else:
            flash("Account created. Please sign in.", "success")
            return redirect(url_for("auth.login"))
    return render_template("signup.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate credentials and create a revocable session."""
    form = LoginForm()
    if form.validate_on_submit():
        row = get_db().execute(
            "SELECT user_id, username, display_name, password_hash FROM user_accounts "
            "WHERE username = ?",
            (form.username.data.lower(),),
        ).fetchone()
        if not row or not check_password_hash(row["password_hash"], form.password.data):
            form.password.errors.append("Username or password is incorrect.")
        else:
            token = create_session(row["user_id"])
            login_user(
                User(
                    user_id=row["user_id"],
                    username=row["username"],
                    display_name=row["display_name"],
                    session_token=token,
                )
            )
            return redirect(url_for("play"))
    return render_template("login.html", form=form)


@auth_bp.post("/logout")
@login_required
def logout():
    """Revoke the current database session through a CSRF-protected form."""
    form = LogoutForm()
    if form.validate_on_submit():
        get_db().execute(
            "UPDATE login_sessions SET is_active = 0 WHERE session_token = ?",
            (current_user.get_id(),),
        )
        get_db().commit()
        logout_user()
        flash("You have signed out.", "success")
    return redirect(url_for("home"))
