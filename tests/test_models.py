import pytest
from datetime import datetime, date, timezone
from app import create_app
from backend.models import (
    db,
    User,
    Assessment,
    HouseholdUsageDetails,
    FarmerUsageDetails,
    ConsumptionBreakdown,
    Recommendation,
    AIConversation,
    AIMessage,
    Achievement,
    UserAchievement,
    Streak,
)

@pytest.fixture
def app():
    """Create test application configured for testing."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def session(app):
    """Database session for testing."""
    return db.session

def test_user_password_hashing(session):
    """Test user creation and secure password hashing with Werkzeug."""
    user = User(
        name="Alice Green",
        email="alice@example.com",
        user_type="household"
    )
    user.set_password("Secret123!")
    session.add(user)
    session.commit()

    assert user.id is not None
    assert user.password_hash != "Secret123!"
    assert user.check_password("Secret123!") is True
    assert user.check_password("WrongPassword") is False
    assert user.to_dict()["email"] == "alice@example.com"
    assert "password_hash" not in user.to_dict()

def test_user_invalid_password():
    """Test rejection of invalid short passwords."""
    user = User(name="Bob", email="bob@example.com")
    with pytest.raises(ValueError):
        user.set_password("123")  # too short

def test_household_assessment_and_relationships(session):
    """Test Assessment with HouseholdUsageDetails, ConsumptionBreakdown, and Recommendations."""
    user = User(name="Charlie", email="charlie@example.com", user_type="household")
    user.set_password("Password999")
    session.add(user)
    session.commit()

    assessment = Assessment(
        user_id=user.id,
        assessment_type="household",
        daily_consumption=350.0,
        weekly_consumption=2450.0,
        monthly_consumption=10500.0,
        water_saver_score=75
    )
    session.add(assessment)
    session.commit()

    # Add household usage details
    details = HouseholdUsageDetails(
        assessment_id=assessment.id,
        household_size=3,
        showers_per_day=3.0,
        shower_duration_minutes=8.0,
        toilet_uses_per_day=12.0,
        laundry_loads_per_week=4.0,
        kitchen_usage_minutes=25.0,
        vehicle_washing_frequency=1.0,
        gardening_frequency=2.0,
        gardening_duration_minutes=15.0,
        other_usage_litres=10.0
    )
    session.add(details)

    # Add consumption breakdowns
    b1 = ConsumptionBreakdown(assessment_id=assessment.id, category="Bathing", litres_per_day=180.0, percentage=51.4)
    b2 = ConsumptionBreakdown(assessment_id=assessment.id, category="Toilet", litres_per_day=72.0, percentage=20.6)
    session.add_all([b1, b2])

    # Add recommendations
    r1 = Recommendation(
        assessment_id=assessment.id,
        category="Bathing",
        title="Reduce Shower Time",
        description="Try shaving 2 minutes off daily shower time.",
        priority="high",
        source="rule_based",
        potential_saving=36.0
    )
    session.add(r1)
    session.commit()

    # Verify query and to_dict
    refreshed = db.session.get(Assessment, assessment.id)
    assert refreshed is not None
    assert refreshed.user.email == "charlie@example.com"
    assert refreshed.household_details.household_size == 3
    assert len(refreshed.breakdowns) == 2
    assert len(refreshed.recommendations) == 1

    d = refreshed.to_dict()
    assert d["daily_consumption"] == 350.0
    assert d["details"]["household_size"] == 3
    assert len(d["breakdown"]) == 2
    assert len(d["recommendations"]) == 1

def test_legacy_assessment_details_are_preserved(session):
    """Legacy usage rows remain mapped and serializable without a migration."""
    user = User(name="Farmer Dave", email="dave@farm.com", user_type="farmer")
    user.set_password("SecureFarmPass")
    session.add(user)
    session.commit()

    assessment = Assessment(
        user_id=user.id,
        assessment_type="farmer",
        daily_consumption=2500.0,
        weekly_consumption=17500.0,
        monthly_consumption=75000.0,
        water_saver_score=82
    )
    session.add(assessment)
    session.commit()

    farmer_details = FarmerUsageDetails(
        assessment_id=assessment.id,
        farm_area=5.5,
        farm_area_unit="acre",
        crop_type="Wheat",
        irrigation_method="drip",
        irrigation_frequency=3.0,
        irrigation_duration_minutes=120.0,
        water_source="canal",
        rainwater_harvesting=True,
        estimated_irrigation_litres=2500.0
    )
    session.add(farmer_details)
    session.commit()

    refreshed = db.session.get(Assessment, assessment.id)
    assert refreshed.farmer_details.crop_type == "Wheat"
    assert refreshed.farmer_details.irrigation_method == "drip"
    assert refreshed.farmer_details.rainwater_harvesting is True

def test_cascade_delete_assessment(session):
    """Test that deleting an assessment cascades to delete details, breakdowns, and recommendations."""
    user = User(name="Eve", email="eve@example.com", user_type="household")
    user.set_password("PasswordEve1")
    session.add(user)
    session.commit()

    assessment = Assessment(
        user_id=user.id,
        assessment_type="household",
        daily_consumption=100.0,
        weekly_consumption=700.0,
        monthly_consumption=3000.0,
        water_saver_score=90
    )
    session.add(assessment)
    session.commit()

    details = HouseholdUsageDetails(assessment_id=assessment.id, household_size=1)
    b = ConsumptionBreakdown(assessment_id=assessment.id, category="Tap", litres_per_day=50.0, percentage=50.0)
    rec = Recommendation(assessment_id=assessment.id, category="General", title="Keep it up", description="Great job!")
    session.add_all([details, b, rec])
    session.commit()

    # Now delete assessment
    session.delete(assessment)
    session.commit()

    assert HouseholdUsageDetails.query.filter_by(assessment_id=assessment.id).first() is None
    assert ConsumptionBreakdown.query.filter_by(assessment_id=assessment.id).first() is None
    assert Recommendation.query.filter_by(assessment_id=assessment.id).first() is None

def test_ai_conversations_and_messages(session):
    """Test AIConversation and AIMessage models."""
    user = User(name="Frank", email="frank@example.com", user_type="household")
    user.set_password("PasswordFrank1")
    session.add(user)
    session.commit()

    conv = AIConversation(user_id=user.id, title="Water Saving Advice")
    session.add(conv)
    session.commit()

    m1 = AIMessage(conversation_id=conv.id, role="user", message="How can I save water in the kitchen?")
    m2 = AIMessage(conversation_id=conv.id, role="assistant", message="Wash dishes using a filled basin rather than a running tap.")
    session.add_all([m1, m2])
    session.commit()

    refreshed_conv = db.session.get(AIConversation, conv.id)
    assert len(refreshed_conv.messages) == 2
    assert refreshed_conv.messages[0].role == "user"
    assert refreshed_conv.messages[1].role == "assistant"

    # Test conversation to_dict
    data = refreshed_conv.to_dict(include_messages=True)
    assert data["message_count"] == 2
    assert len(data["messages"]) == 2

def test_gamification_achievements_and_streaks(session):
    """Test Achievement, UserAchievement, and Streak models."""
    user = User(name="Grace", email="grace@example.com", user_type="household")
    user.set_password("PasswordGrace1")
    session.add(user)
    session.commit()

    # Create achievement
    ach = Achievement(
        name="First Drop",
        description="Completed your first assessment.",
        icon="droplet",
        requirement_type="assessments_count",
        requirement_value=1.0
    )
    session.add(ach)
    session.commit()

    # Award achievement to user
    user_ach = UserAchievement(user_id=user.id, achievement_id=ach.id)
    session.add(user_ach)

    # Set up user streak
    streak = Streak(
        user_id=user.id,
        current_streak=5,
        longest_streak=10,
        last_activity_date=date.today()
    )
    session.add(streak)
    session.commit()

    # Verify relationships
    refreshed_user = db.session.get(User, user.id)
    assert len(refreshed_user.user_achievements) == 1
    assert refreshed_user.user_achievements[0].achievement.name == "First Drop"
    assert refreshed_user.streak.current_streak == 5
    assert refreshed_user.streak.longest_streak == 10
