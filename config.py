import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env if present
env_path = os.path.join(basedir, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)


class BaseConfig:
    """Base configuration with shared defaults."""
    APP_NAME = "AquaWise"
    SECRET_KEY = os.environ.get("SECRET_KEY", "aquawise-dev-fallback-secret-key")
    
    # SQLite database path resolution (ensures robust absolute path on all operating systems)
    raw_db_url = os.environ.get("DATABASE_URL")
    if raw_db_url and raw_db_url.startswith("sqlite:///"):
        path_part = raw_db_url[10:]
        # If relative (no drive letter like C: and no leading slash), make absolute
        if not (len(path_part) > 1 and path_part[1] == ":") and not path_part.startswith("/"):
            abs_db_path = os.path.abspath(os.path.join(basedir, path_part)).replace("\\", "/")
            SQLALCHEMY_DATABASE_URI = f"sqlite:///{abs_db_path}"
        else:
            SQLALCHEMY_DATABASE_URI = raw_db_url.replace("\\", "/")
    elif raw_db_url:
        SQLALCHEMY_DATABASE_URI = raw_db_url
    else:
        default_db_path = os.path.join(basedir, "database", "aquawise.db").replace("\\", "/")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{default_db_path}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # AI Service Configuration
    AI_API_KEY = os.environ.get("AI_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
    AI_MODEL = os.environ.get("AI_MODEL", "gemini-2.5-flash")
    
    # Server defaults
    PORT = int(os.environ.get("PORT", 5000))


class DevelopmentConfig(BaseConfig):
    """Configuration for local development."""
    DEBUG = True
    TESTING = False


class TestingConfig(BaseConfig):
    """Configuration for automated test suite."""
    TESTING = True
    DEBUG = True
    # In-memory database for fast, isolated tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(BaseConfig):
    """Configuration for production deployment."""
    DEBUG = False
    TESTING = False


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
