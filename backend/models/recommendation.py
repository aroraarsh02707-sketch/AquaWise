"""
Recommendation Model.
Stores personalized water conservation recommendations generated for an assessment.
"""
from datetime import datetime, timezone
from backend.models import db

def utc_now():
    return datetime.now(timezone.utc)

class Recommendation(db.Model):
    __tablename__ = "recommendations"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), default="medium", nullable=False)   # "low", "medium", "high"
    source = db.Column(db.String(20), default="rule_based", nullable=False) # "rule_based", "ai", "hybrid"
    potential_saving = db.Column(db.Float, default=0.0)                    # estimated L/day saved
    evidence = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "category": self.category,
            "title": self.title,
            "description": self.description,
            "priority": self.priority,
            "source": self.source,
            "potential_saving": round(self.potential_saving, 1) if self.potential_saving is not None else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "evidence": self.evidence,
        }

    def __repr__(self):
        return f"<Recommendation id={self.id} category='{self.category}' priority='{self.priority}'>"
