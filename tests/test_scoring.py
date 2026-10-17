"""
Tests for AquaWise Deterministic Scoring & Streak Service (Task 2).

Validates:
1. Deterministic Water Saver Score calculation for household and farmer inputs.
2. Bounds enforcement (0 <= score <= 100).
3. Score tier classification.
4. Streak maintenance logic (same day, consecutive day, broken streak reset, longest streak retention).
5. Achievement evaluation and milestone badge unlocking.
"""

from datetime import date, timedelta
import pytest
from app import create_app, seed_achievements
from backend.models import db, User, Assessment, Streak, Achievement, UserAchievement
from backend.services.scoring_service import (
    calculate_water_saver_score,
    get_score_tier,
    update_user_streak,
    evaluate_user_achievements,
)


@pytest.fixture
def app():
    """Create test application configured with an in-memory database."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        seed_achievements()
        yield test_app
        db.session.remove()
        db.drop_all()


class TestWaterSaverScoreCalculation:

    def test_missing_vehicle_frequency_has_no_bonus_but_explicit_zero_keeps_bonus(self):
        base_details = {"household_size": 1, "shower_duration_minutes": 0, "kitchen_usage_minutes": 0}
        missing_score = calculate_water_saver_score(150.0, "household", {**base_details, "vehicle_washing_frequency": None})
        zero_score = calculate_water_saver_score(150.0, "household", {**base_details, "vehicle_washing_frequency": 0})
        assert missing_score == 70
        assert zero_score == 72

    def test_low_consumption_household_gets_high_score(self):
        """A household with 60 L/capita/day should score in the Champion tier (>= 90)."""
        score = calculate_water_saver_score(
            daily_consumption=120.0,
            user_type="household",
            details={"household_size": 2, "shower_duration_minutes": 4.0}
        )
        assert 90 <= score <= 100

    def test_benchmark_consumption_household_score(self):
        """A household at the CPHEEO benchmark (150 L/capita/day) scores around 70."""
        score = calculate_water_saver_score(
            daily_consumption=300.0,
            user_type="household",
            details={"household_size": 2}
        )
        assert 65 <= score <= 75

    def test_high_consumption_household_gets_low_score(self):
        """A household with 400 L/capita/day should receive a low score (<= 30)."""
        score = calculate_water_saver_score(
            daily_consumption=800.0,
            user_type="household",
            details={"household_size": 2, "shower_duration_minutes": 15.0}
        )
        assert score <= 30

    def test_score_always_bounded_between_0_and_100(self):
        """Even extreme zero or absurdly large inputs must remain strictly within [0, 100]."""
        zero_score = calculate_water_saver_score(0.0, user_type="household")
        assert 0 <= zero_score <= 100

        huge_score = calculate_water_saver_score(1_000_000.0, user_type="household")
        assert 0 <= huge_score <= 100

    def test_farmer_drip_with_rainwater_high_score(self):
        """Drip irrigation with rainwater harvesting should score high (>= 90)."""
        score = calculate_water_saver_score(
            daily_consumption=1500.0,
            user_type="farmer",
            details={
                "irrigation_method": "drip",
                "rainwater_harvesting": True,
                "irrigation_frequency": 2.0,
            }
        )
        assert score >= 90

    def test_farmer_flood_irrigation_moderate_low_score(self):
        """Flood irrigation without rainwater harvesting should score moderate/low (~40-50)."""
        score = calculate_water_saver_score(
            daily_consumption=5000.0,
            user_type="farmer",
            details={
                "irrigation_method": "flood",
                "rainwater_harvesting": False,
                "irrigation_frequency": 5.0,
            }
        )
        assert 40 <= score <= 50

    def test_score_tiers(self):
        assert get_score_tier(92)["label"] == "Water Champion"
        assert get_score_tier(78)["label"] == "Smart Water User"
        assert get_score_tier(60)["label"] == "Water Saver"
        assert get_score_tier(35)["label"] == "Getting Started"


class TestStreakMaintenance:

    @pytest.fixture
    def test_user(self, app):
        user = User(name="Streak User", email="streak@example.com", user_type="household")
        user.set_password("Password123")
        db.session.add(user)
        db.session.commit()
        return user

    def test_initial_streak_creation(self, test_user):
        today = date(2026, 9, 24)
        streak = update_user_streak(test_user.id, activity_date=today)
        db.session.commit()

        assert streak.current_streak == 1
        assert streak.longest_streak == 1
        assert streak.last_activity_date == today

    def test_same_day_activity_is_idempotent(self, test_user):
        today = date(2026, 9, 24)
        streak = update_user_streak(test_user.id, activity_date=today)
        db.session.commit()

        # Second assessment on the exact same day
        streak_again = update_user_streak(test_user.id, activity_date=today)
        db.session.commit()

        assert streak_again.current_streak == 1
        assert streak_again.longest_streak == 1

    def test_consecutive_day_increments_streak(self, test_user):
        day1 = date(2026, 9, 24)
        day2 = date(2026, 9, 25)

        update_user_streak(test_user.id, activity_date=day1)
        db.session.commit()

        streak = update_user_streak(test_user.id, activity_date=day2)
        db.session.commit()

        assert streak.current_streak == 2
        assert streak.longest_streak == 2
        assert streak.last_activity_date == day2

    def test_broken_streak_resets_current_to_one(self, test_user):
        day1 = date(2026, 9, 20)
        day2 = date(2026, 9, 21)
        day4 = date(2026, 9, 24)  # 3 days later, missed Sept 22 and 23

        update_user_streak(test_user.id, activity_date=day1)
        db.session.commit()
        update_user_streak(test_user.id, activity_date=day2)
        db.session.commit()

        # Broken streak
        streak = update_user_streak(test_user.id, activity_date=day4)
        db.session.commit()

        assert streak.current_streak == 1
        assert streak.longest_streak == 2  # High water mark preserved
        assert streak.last_activity_date == day4


class TestAchievementEvaluation:

    @pytest.fixture
    def test_user(self, app):
        user = User(name="Achiever", email="achiever@example.com", user_type="household")
        user.set_password("Password123")
        db.session.add(user)
        db.session.commit()
        return user

    def test_first_assessment_achievement_unlocked(self, test_user):
        # Create user's first assessment
        assessment = Assessment(
            user_id=test_user.id,
            assessment_type="household",
            daily_consumption=200.0,
            weekly_consumption=1400.0,
            monthly_consumption=6000.0,
            water_saver_score=70
        )
        db.session.add(assessment)
        db.session.commit()

        awarded = evaluate_user_achievements(test_user.id, assessment)
        db.session.commit()

        names = [ua.achievement.name for ua in awarded]
        assert "First Assessment" in names

    def test_water_saver_score_achievement_unlocked(self, test_user):
        # Assessment with high score (>= 75)
        assessment = Assessment(
            user_id=test_user.id,
            assessment_type="household",
            daily_consumption=120.0,
            weekly_consumption=840.0,
            monthly_consumption=3600.0,
            water_saver_score=80
        )
        db.session.add(assessment)
        db.session.commit()

        awarded = evaluate_user_achievements(test_user.id, assessment)
        db.session.commit()

        names = [ua.achievement.name for ua in awarded]
        assert "First Assessment" in names
        assert "Water Saver" in names

    def test_smart_water_user_score_85_unlocked(self, test_user):
        assessment = Assessment(
            user_id=test_user.id,
            assessment_type="household",
            daily_consumption=80.0,
            weekly_consumption=560.0,
            monthly_consumption=2400.0,
            water_saver_score=90
        )
        db.session.add(assessment)
        db.session.commit()

        awarded = evaluate_user_achievements(test_user.id, assessment)
        db.session.commit()

        names = [ua.achievement.name for ua in awarded]
        assert "Water Saver" in names
        assert "Smart Water User" in names

    def test_streak_achievement_unlocked(self, test_user):
        # Setup 7-day streak for user
        streak = Streak(user_id=test_user.id, current_streak=7, longest_streak=7)
        db.session.add(streak)
        db.session.commit()

        awarded = evaluate_user_achievements(test_user.id)
        db.session.commit()

        names = [ua.achievement.name for ua in awarded]
        assert "Consistent Saver" in names

    def test_no_duplicate_achievements_awarded(self, test_user):
        assessment = Assessment(
            user_id=test_user.id,
            assessment_type="household",
            daily_consumption=200.0,
            weekly_consumption=1400.0,
            monthly_consumption=6000.0,
            water_saver_score=70
        )
        db.session.add(assessment)
        db.session.commit()

        # First evaluation awards "First Assessment"
        awarded1 = evaluate_user_achievements(test_user.id, assessment)
        db.session.commit()
        assert len(awarded1) >= 1

        # Second evaluation must NOT duplicate it
        awarded2 = evaluate_user_achievements(test_user.id, assessment)
        db.session.commit()
        assert len(awarded2) == 0
