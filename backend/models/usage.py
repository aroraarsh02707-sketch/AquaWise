"""
Usage Models.
Stores household details, historical assessment details, and category breakdowns.
"""
from backend.models import db

class HouseholdUsageDetails(db.Model):
    __tablename__ = "household_usage_details"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    household_size = db.Column(db.Integer, nullable=False)
    showers_per_day = db.Column(db.Float, default=0.0)
    shower_duration_minutes = db.Column(db.Float, default=0.0)
    toilet_uses_per_day = db.Column(db.Float, default=0.0)
    laundry_loads_per_week = db.Column(db.Float, default=0.0)
    kitchen_usage_minutes = db.Column(db.Float, default=0.0)
    vehicle_washing_frequency = db.Column(db.Float, default=0.0)
    gardening_frequency = db.Column(db.Float, default=0.0)
    gardening_duration_minutes = db.Column(db.Float, default=0.0)
    other_usage_litres = db.Column(db.Float, default=0.0)
    # Optional structured answers for the expanded household assessment.
    # Nullable so legacy assessment rows and API clients remain compatible.
    extended_answers = db.Column(db.JSON, nullable=True)

    def to_dict(self):
        return {
            "household_size": self.household_size,
            "showers_per_day": self.showers_per_day,
            "shower_duration_minutes": self.shower_duration_minutes,
            "toilet_uses_per_day": self.toilet_uses_per_day,
            "laundry_loads_per_week": self.laundry_loads_per_week,
            "kitchen_usage_minutes": self.kitchen_usage_minutes,
            "vehicle_washing_frequency": self.vehicle_washing_frequency,
            "gardening_frequency": self.gardening_frequency,
            "gardening_duration_minutes": self.gardening_duration_minutes,
            "other_usage_litres": self.other_usage_litres,
            "extended_answers": self.extended_answers,
        }


class FarmerUsageDetails(db.Model):
    """Legacy table mapping retained to preserve existing assessment rows."""
    __tablename__ = "farmer_usage_details"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True
    )
    farm_area = db.Column(db.Float, nullable=False)
    farm_area_unit = db.Column(db.String(20), default="acre")  # acre / hectare
    crop_type = db.Column(db.String(100), nullable=False)
    irrigation_method = db.Column(db.String(50), nullable=False)  # flood, drip, sprinkler, other
    irrigation_frequency = db.Column(db.Float, default=0.0)       # sessions per week or month
    irrigation_duration_minutes = db.Column(db.Float, default=0.0)
    water_source = db.Column(db.String(50), default="groundwater")  # groundwater, canal, rainwater, tank, other
    rainfall_information = db.Column(db.String(200), nullable=True)
    rainwater_harvesting = db.Column(db.Boolean, default=False)
    estimated_irrigation_litres = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            "farm_area": self.farm_area,
            "farm_area_unit": self.farm_area_unit,
            "crop_type": self.crop_type,
            "irrigation_method": self.irrigation_method,
            "irrigation_frequency": self.irrigation_frequency,
            "irrigation_duration_minutes": self.irrigation_duration_minutes,
            "water_source": self.water_source,
            "rainfall_information": self.rainfall_information,
            "rainwater_harvesting": self.rainwater_harvesting,
            "estimated_irrigation_litres": self.estimated_irrigation_litres,
        }


class ConsumptionBreakdown(db.Model):
    __tablename__ = "consumption_breakdowns"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer,
        db.ForeignKey("assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    category = db.Column(db.String(50), nullable=False)
    litres_per_day = db.Column(db.Float, nullable=False)
    percentage = db.Column(db.Float, nullable=False)

    def to_dict(self):
        return {
            "category": self.category,
            "litres_per_day": round(self.litres_per_day, 1),
            "percentage": round(self.percentage, 1),
        }
