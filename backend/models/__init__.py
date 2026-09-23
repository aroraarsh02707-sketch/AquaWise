"""
AquaWise Database Models Package.
Initializes SQLAlchemy instance and exports all 11 database entities.
"""
from flask_sqlalchemy import SQLAlchemy

# Shared SQLAlchemy database instance
db = SQLAlchemy()

# Import all models to register them with SQLAlchemy metadata
from backend.models.user import User
from backend.models.assessment import Assessment
from backend.models.usage import HouseholdUsageDetails, FarmerUsageDetails, ConsumptionBreakdown
from backend.models.recommendation import Recommendation
from backend.models.ai import AIConversation, AIMessage
from backend.models.gamification import Achievement, UserAchievement, Streak

__all__ = [
    "db",
    "User",
    "Assessment",
    "HouseholdUsageDetails",
    "FarmerUsageDetails",
    "ConsumptionBreakdown",
    "Recommendation",
    "AIConversation",
    "AIMessage",
    "Achievement",
    "UserAchievement",
    "Streak",
]
