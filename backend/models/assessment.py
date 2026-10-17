"""
Assessment Model.
Represents a water consumption assessment completed by a user.
"""
from datetime import datetime, timezone
from backend.models import db

def utc_now():
    return datetime.now(timezone.utc)

class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    assessment_type = db.Column(db.String(20), nullable=False)  # "household" or "farmer"
    assessment_date = db.Column(db.DateTime, default=utc_now, nullable=False, index=True)
    daily_consumption = db.Column(db.Float, nullable=False)       # litres / day
    weekly_consumption = db.Column(db.Float, nullable=False)      # litres / week
    monthly_consumption = db.Column(db.Float, nullable=False)     # litres / month
    water_saver_score = db.Column(db.Integer, nullable=False)     # 0 to 100
    calculation_details = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now, nullable=False)

    # Specific Usage Details (1-to-0/1)
    household_details = db.relationship(
        "HouseholdUsageDetails",
        backref="assessment",
        uselist=False,
        cascade="all, delete-orphan"
    )
    farmer_details = db.relationship(
        "FarmerUsageDetails",
        backref="assessment",
        uselist=False,
        cascade="all, delete-orphan"
    )

    # Activity Breakdown (1-to-Many)
    breakdowns = db.relationship(
        "ConsumptionBreakdown",
        backref="assessment",
        cascade="all, delete-orphan",
        lazy=True
    )

    # Generated Recommendations (1-to-Many)
    recommendations = db.relationship(
        "Recommendation",
        backref="assessment",
        cascade="all, delete-orphan",
        lazy=True,
        order_by="desc(Recommendation.created_at)"
    )

    def to_dict(self, include_details=True):
        """Converts assessment record into a comprehensive dictionary."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "assessment_type": self.assessment_type,
            "assessment_date": self.assessment_date.strftime("%Y-%m-%d") if self.assessment_date else None,
            "daily_consumption": round(self.daily_consumption, 1),
            "weekly_consumption": round(self.weekly_consumption, 1),
            "monthly_consumption": round(self.monthly_consumption, 1),
            "water_saver_score": self.water_saver_score,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "calculation": self.calculation_details,
        }

        if include_details:
            if self.assessment_type == "household" and self.household_details:
                data["details"] = self.household_details.to_dict()
            elif self.assessment_type == "farmer" and self.farmer_details:
                data["details"] = self.farmer_details.to_dict()
            else:
                data["details"] = None

            data["breakdown"] = [b.to_dict() for b in self.breakdowns]
            data["recommendations"] = [r.to_dict() for r in self.recommendations]

        return data

    def __repr__(self):
        return f"<Assessment id={self.id} user_id={self.user_id} daily={self.daily_consumption}L score={self.water_saver_score}>"
