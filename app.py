import os
import hmac
import secrets
from datetime import datetime, timezone
from urllib.parse import urlsplit
from flask import Flask, jsonify, request, session
from flask_login import LoginManager, current_user, logout_user
from sqlalchemy import inspect
from config import config
from backend.models import db, User, Achievement
from backend.routes.auth_routes import auth_bp
from backend.routes.assessment_routes import assessment_bp
from backend.routes.recommendation_routes import recommendation_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.assistant_routes import assistant_bp
from backend.routes.profile_routes import profile_bp

login_manager = LoginManager()

def seed_achievements():
    """Seed the default achievement milestones into the database."""
    default_achievements = [
        {
            "name": "First Assessment",
            "description": "Completed your first water assessment.",
            "icon": "droplet",
            "requirement_type": "assessments_count",
            "requirement_value": 1.0,
        },
        {
            "name": "Water Saver",
            "description": "Achieved a Water Saver Score of 75 or higher.",
            "icon": "leaf",
            "requirement_type": "score_above",
            "requirement_value": 75.0,
        },
        {
            "name": "Smart Water User",
            "description": "Achieved a Water Saver Score of 85 or higher.",
            "icon": "shield",
            "requirement_type": "score_above",
            "requirement_value": 85.0,
        },
        {
            "name": "Consistent Saver",
            "description": "Maintained a 7-day conservation streak.",
            "icon": "flame",
            "requirement_type": "streak_days",
            "requirement_value": 7.0,
        },
        {
            "name": "Conservation Champion",
            "description": "Completed 5 water assessments.",
            "icon": "trophy",
            "requirement_type": "assessments_count",
            "requirement_value": 5.0,
        },
    ]

    for item in default_achievements:
        existing = Achievement.query.filter_by(name=item["name"]).first()
        if not existing:
            achievement = Achievement(
                name=item["name"],
                description=item["description"],
                icon=item["icon"],
                requirement_type=item["requirement_type"],
                requirement_value=item["requirement_value"],
            )
            db.session.add(achievement)

    db.session.commit()


def create_app(config_name=None):
    """
    Application factory for AquaWise.
    Initializes configuration, SQLAlchemy database, and core endpoints.
    """
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    base_dir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(base_dir, "frontend", "templates")
    static_dir = os.path.join(base_dir, "frontend", "static")
    database_dir = os.path.join(base_dir, "database")

    # Ensure database directory exists
    os.makedirs(database_dir, exist_ok=True)

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir
    )

    # Load configuration
    selected_config = config.get(config_name, config["default"])
    app.config.from_object(selected_config)

    # Environment configuration is read at app creation so factory callers and
    # production process managers can configure the same application reliably.
    if config_name == "production":
        app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
    elif os.environ.get("SECRET_KEY"):
        app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
    configured_origins = os.environ.get("CORS_ALLOWED_ORIGINS")
    if configured_origins and configured_origins.strip():
        app.config["CORS_ALLOWED_ORIGINS"] = [
            origin.strip().rstrip("/")
            for origin in configured_origins.split(",")
            if origin.strip()
        ]
    same_site_setting = os.environ.get("SESSION_COOKIE_SAMESITE")
    if same_site_setting:
        app.config["SESSION_COOKIE_SAMESITE"] = same_site_setting.strip().capitalize()
        app.config["REMEMBER_COOKIE_SAMESITE"] = same_site_setting.strip().capitalize()

    if config_name == "production":
        secret_key = app.config.get("SECRET_KEY")
        if (
            not isinstance(secret_key, str)
            or len(secret_key) < 32
            or len(set(secret_key)) < 16
            or "change-this" in secret_key.lower()
            or "development-only" in secret_key.lower()
            or "test-only" in secret_key.lower()
        ):
            raise RuntimeError("Production requires SECRET_KEY with at least 32 characters.")
        if not app.config.get("CORS_ALLOWED_ORIGINS"):
            raise RuntimeError("Production requires CORS_ALLOWED_ORIGINS with at least one frontend origin.")
        for origin in app.config["CORS_ALLOWED_ORIGINS"]:
            parsed_origin = urlsplit(origin)
            if (
                parsed_origin.scheme != "https"
                or not parsed_origin.netloc
                or parsed_origin.path
                or parsed_origin.query
                or parsed_origin.fragment
            ):
                raise RuntimeError("Production CORS_ALLOWED_ORIGINS entries must be HTTPS origins without paths.")
        if same_site_setting is None:
            raise RuntimeError("Production requires SESSION_COOKIE_SAMESITE (Lax for same-site, None for cross-site).")
        if app.config["SESSION_COOKIE_SAMESITE"] not in {"Lax", "Strict", "None"}:
            raise RuntimeError("SESSION_COOKIE_SAMESITE must be Lax, Strict, or None.")
        if app.config["SESSION_COOKIE_SAMESITE"] == "None" and not app.config["SESSION_COOKIE_SECURE"]:
            raise RuntimeError("SameSite=None cookies require SESSION_COOKIE_SECURE=True.")

    # Keep Flask-Login's persistent remember cookie aligned with the session cookie.
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_SECURE"] = app.config["SESSION_COOKIE_SECURE"]

    # Initialize SQLAlchemy database with application
    db.init_app(app)

    # Initialize Flask-Login for session-based user authentication
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized_callback():
        return jsonify({
            "success": False,
            "error": {
                "code": "UNAUTHORIZED",
                "message": "Authentication required. Please log in."
            }
        }), 401

    @app.before_request
    def restrict_api_to_household_accounts():
        """End legacy non-household sessions without altering their records."""
        if (
            request.path.startswith("/api/")
            and current_user.is_authenticated
            and current_user.user_type != "household"
        ):
            logout_user()
            return jsonify({
                "success": False,
                "error": {
                    "code": "ACCOUNT_TYPE_UNAVAILABLE",
                    "message": "This legacy account type is no longer supported. Its records have been preserved."
                }
            }), 403

    @app.before_request
    def enforce_api_csrf_token():
        """Require a session-bound token for every state-changing API request."""
        if not request.path.startswith("/api/") or request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
            return None

        expected_token = session.get("csrf_token")
        supplied_token = request.headers.get("X-CSRF-Token", "")
        if not expected_token or not supplied_token or not hmac.compare_digest(expected_token, supplied_token):
            return jsonify({
                "success": False,
                "error": {
                    "code": "CSRF_TOKEN_INVALID",
                    "message": "A valid CSRF token is required. Refresh the page and try again."
                }
            }), 400
        return None

    # Register Route Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(recommendation_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assistant_bp)
    app.register_blueprint(profile_bp)

    # CORS support for React development server
    @app.after_request
    def set_cors_headers(response):
        response.headers.add("Vary", "Origin")
        origin = request.headers.get("Origin")
        allowed_origins = app.config.get("CORS_ALLOWED_ORIGINS", [])
        if origin and origin.rstrip("/") in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin.rstrip("/")
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-CSRF-Token"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        return response

    @app.route("/api/auth/csrf", methods=["GET"])
    def get_csrf_token():
        """Create or return the token used to protect session-authenticated API calls."""
        token = session.get("csrf_token")
        if not token:
            token = secrets.token_urlsafe(32)
            session["csrf_token"] = token
        response = jsonify({"success": True, "data": {"csrf_token": token}})
        response.headers["Cache-Control"] = "no-store"
        return response

    # Register custom CLI commands
    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables and seed initial achievements."""
        db.create_all()
        seed_achievements()
        print("AquaWise database initialized and achievements seeded successfully.")

    @app.cli.command("seed-achievements")
    def seed_achievements_command():
        """Seed default achievements."""
        seed_achievements()
        print("Default achievements seeded successfully.")

    @app.cli.command("migrate-household-assessment-v2")
    def migrate_household_assessment_v2():
        """Add nullable V2 assessment metadata columns without changing old rows."""
        additions = {
            "assessments": {"calculation_details": "JSON"},
            "household_usage_details": {"extended_answers": "JSON"},
            "recommendations": {"evidence": "JSON"},
        }
        inspector = inspect(db.engine)
        with db.engine.begin() as connection:
            for table, columns in additions.items():
                if not inspector.has_table(table):
                    raise RuntimeError(f"Required table {table} is missing; initialize the database first.")
                present = {column["name"] for column in inspector.get_columns(table)}
                for column, column_type in columns.items():
                    if column not in present:
                        connection.execute(db.text(f"ALTER TABLE {table} ADD COLUMN {column} {column_type} NULL"))
        print("Household assessment V2 schema is ready. Existing records were preserved.")

    # Health Check API
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint to verify server status and active environment."""
        # Render uses this response to determine whether the service is ready.
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception:
            db.session.rollback()
            return jsonify({
                "status": "unhealthy",
                "app": app.config.get("APP_NAME", "AquaWise"),
                "version": "1.0.0",
                "environment": config_name,
                "database": "unavailable",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }), 503

        return jsonify({
            "status": "healthy",
            "app": app.config.get("APP_NAME", "AquaWise"),
            "version": "1.0.0",
            "environment": config_name,
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    # Root route: Flask serves the API; the Vite frontend owns its own index page.
    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "app": app.config.get("APP_NAME", "AquaWise"),
            "message": "AquaWise API service.",
            "health": "/api/health",
        })

    # Standard JSON error handlers for API routes
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "The requested resource could not be found."
            }
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred."
            }
        }), 500

    return app


# Create application instance for WSGI runners
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = app.config.get("DEBUG", True)
    app.run(host="127.0.0.1", port=port, debug=debug)
