import os
from datetime import datetime, timezone
from flask import Flask, jsonify, render_template, request
from flask_login import LoginManager
from config import config
from backend.models import db, User, Achievement
from backend.routes.auth_routes import auth_bp
from backend.routes.assessment_routes import assessment_bp
from backend.routes.recommendation_routes import recommendation_bp

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

    # Register Route Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(recommendation_bp)

    # CORS support for React development server
    @app.after_request
    def set_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
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

    # Health Check API
    @app.route("/api/health", methods=["GET"])
    def health_check():
        """Health check endpoint to verify server status and active environment."""
        # Verify database connection
        db_status = "connected"
        try:
            db.session.execute(db.text("SELECT 1"))
        except Exception as e:
            db_status = f"unavailable: {str(e)}"

        return jsonify({
            "status": "healthy",
            "app": app.config.get("APP_NAME", "AquaWise"),
            "version": "1.0.0",
            "environment": config_name,
            "database": db_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 200

    # Root route
    @app.route("/", methods=["GET"])
    def index():
        return render_template("index.html")

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
