"""
Authentication REST API Routes.

Provides session-based authentication endpoints for the AquaWise React frontend:
- POST /api/auth/register : Register a new user (household or farmer)
- POST /api/auth/login    : Authenticate and establish user session
- POST /api/auth/logout   : End current user session
- GET  /api/auth/me       : Retrieve current authenticated user profile
"""

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from backend.models import db, User, Streak
from backend.utils.validators import validate_registration, validate_login

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user account.
    Validates input, checks for unique email, hashes password, creates user and streak.
    Logs the user in upon successful creation.
    """
    data = request.get_json(silent=True) or {}
    errors = validate_registration(data)
    if errors:
        first_err = next(iter(errors.values()))
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": first_err,
                "details": errors
            }
        }), 400

    email = data["email"].strip().lower()
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({
            "success": False,
            "error": {
                "code": "CONFLICT",
                "message": "An account with this email address already exists."
            }
        }), 409

    try:
        user = User(
            name=data["name"].strip(),
            email=email,
            user_type=data.get("user_type", "household").strip().lower()
        )
        user.set_password(data["password"])
        db.session.add(user)
        db.session.flush()  # Allocate user.id before creating Streak

        # Initialize user streak record
        streak = Streak(user_id=user.id)
        db.session.add(streak)

        db.session.commit()

        # Log the user into the session automatically
        login_user(user)

        return jsonify({
            "success": True,
            "data": {
                "user": user.to_dict(),
                "message": "Registration successful."
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": {
                "code": "REGISTRATION_FAILED",
                "message": "An error occurred while creating the account. Please try again."
            }
        }), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate a user and establish a session.
    """
    data = request.get_json(silent=True) or {}
    errors = validate_login(data)
    if errors:
        first_err = next(iter(errors.values()))
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": first_err,
                "details": errors
            }
        }), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({
            "success": False,
            "error": {
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password."
            }
        }), 401

    if not user.is_active:
        return jsonify({
            "success": False,
            "error": {
                "code": "ACCOUNT_DISABLED",
                "message": "This account has been deactivated."
            }
        }), 403

    remember = bool(data.get("remember", False))
    login_user(user, remember=remember)

    return jsonify({
        "success": True,
        "data": {
            "user": user.to_dict(),
            "message": "Login successful."
        }
    }), 200


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Terminate the current user session.
    """
    logout_user()
    return jsonify({
        "success": True,
        "data": {
            "message": "Logged out successfully."
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
@login_required
def get_current_user():
    """
    Retrieve profile information for the currently authenticated user.
    """
    return jsonify({
        "success": True,
        "data": {
            "user": current_user.to_dict()
        }
    }), 200
