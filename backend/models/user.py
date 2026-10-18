"""
User Model.
Represents application users with secure authentication. The user_type column
is retained so existing legacy records remain readable without schema changes.
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.models import db

def utc_now():
    """Helper to return current UTC timestamp."""
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    user_type = db.Column(db.String(20), nullable=False, default="household")
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships (Cascading deletions ensure clean user data management)
    assessments = db.relationship(
        "Assessment",
        backref="user",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="desc(Assessment.created_at)"
    )
    ai_conversations = db.relationship(
        "AIConversation",
        backref="user",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="desc(AIConversation.updated_at)"
    )
    user_achievements = db.relationship(
        "UserAchievement",
        backref="user",
        cascade="all, delete-orphan",
        lazy=True
    )
    streak = db.relationship(
        "Streak",
        backref="user",
        uselist=False,
        cascade="all, delete-orphan",
        lazy=True
    )

    def set_password(self, password: str):
        """Hashes the password securely using Werkzeug."""
        if not password or len(password) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verifies a plain-text password against the stored hash."""
        if not self.password_hash or not password:
            return False
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Returns safe user information omitting sensitive password data."""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "user_type": self.user_type,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<User id={self.id} email='{self.email}' type='{self.user_type}'>"
