"""
Gamification Models.
Includes Achievement definitions, User earned achievements, and User Streaks.
"""
from datetime import datetime, timezone
from backend.models import db

def utc_now():
    return datetime.now(timezone.utc)

class Achievement(db.Model):
    __tablename__ = "achievements"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=False)
    icon = db.Column(db.String(50), default="trophy", nullable=False)
    requirement_type = db.Column(db.String(50), nullable=False)  # e.g., "assessments_count", "streak_days", "score_above"
    requirement_value = db.Column(db.Float, default=1.0, nullable=False)

    user_achievements = db.relationship(
        "UserAchievement",
        backref="achievement",
        cascade="all, delete-orphan",
        lazy=True
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "requirement_type": self.requirement_type,
            "requirement_value": self.requirement_value,
        }

    def __repr__(self):
        return f"<Achievement id={self.id} name='{self.name}'>"


class UserAchievement(db.Model):
    __tablename__ = "user_achievements"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    achievement_id = db.Column(
        db.Integer,
        db.ForeignKey("achievements.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    earned_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "achievement_id": self.achievement_id,
            "name": self.achievement.name if self.achievement else None,
            "description": self.achievement.description if self.achievement else None,
            "icon": self.achievement.icon if self.achievement else None,
            "earned_at": self.earned_at.isoformat() if self.earned_at else None,
        }


class Streak(db.Model):
    __tablename__ = "streaks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_streak = db.Column(db.Integer, default=0, nullable=False)
    last_activity_date = db.Column(db.Date, nullable=True)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "last_activity_date": self.last_activity_date.isoformat() if self.last_activity_date else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<Streak user_id={self.user_id} current={self.current_streak} longest={self.longest_streak}>"
