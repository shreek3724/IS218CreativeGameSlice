"""CSRF-protected forms for account actions."""

from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, Regexp


class SignupForm(FlaskForm):
    """Validate a new account before it reaches the database."""

    display_name = StringField(
        "Display name", validators=[DataRequired(), Length(max=40)]
    )
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(min=3, max=30),
            Regexp(
                r"^[A-Za-z0-9_]+$",
                message="Use letters, numbers, or underscores only.",
            ),
        ],
    )
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField(
        "Confirm password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match."),
        ],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    """Validate submitted sign-in credentials."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class LogoutForm(FlaskForm):
    """Provide a CSRF token for the sign-out request."""

    submit = SubmitField("Sign out")
