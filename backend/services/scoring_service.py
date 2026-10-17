"""
AquaWise Deterministic Scoring & Gamification Service.

Responsibilities:
1. Calculate the Water Saver Score (0–100 integer) using pure deterministic rules.
   - Household score applies fixed rules to estimated per-capita use and reported habits.
   - Farmer score applies fixed rules to reported irrigation practices.
   - The score is strictly reproducible, explainable, and independent of AI.
2. Manage User Streaks:
   - Tracks consecutive days of water conservation activity.
   - Handles same-day idempotency, consecutive day increment, and broken streak reset.
3. Evaluate Gamification Achievements:
   - Awards milestone badges (First Assessment, Water Saver, Smart Water User, Consistent Saver, Conservation Champion).
"""

from datetime import date, timedelta
from typing import Any
from backend.models import db, Achievement, UserAchievement, Streak, Assessment
from backend.utils.constants import (
    BENCHMARK_HOUSEHOLD_LPCD,
    HIGH_CONSUMPTION_THRESHOLD_LPCD,
)

# ---------------------------------------------------------------------------
# Score Tier Definitions (from PRD Section 16)
# ---------------------------------------------------------------------------

SCORE_TIERS = [
    {"min": 85, "max": 100, "label": "Water Champion", "icon": "trophy"},
    {"min": 75, "max": 84,  "label": "Smart Water User", "icon": "shield"},
    {"min": 50, "max": 74,  "label": "Water Saver", "icon": "leaf"},
    {"min": 0,  "max": 49,  "label": "Getting Started", "icon": "droplet"},
]


def get_score_tier(score: int) -> dict[str, str]:
    """Return label and icon for a given Water Saver Score."""
    clamped = max(0, min(100, int(score)))
    for tier in SCORE_TIERS:
        if tier["min"] <= clamped <= tier["max"]:
            return {"label": tier["label"], "icon": tier["icon"]}
    return {"label": "Getting Started", "icon": "droplet"}


# ---------------------------------------------------------------------------
# Deterministic Water Saver Score Calculation
# ---------------------------------------------------------------------------

def calculate_water_saver_score(
    daily_consumption: float,
    user_type: str = "household",
    details: dict[str, Any] | None = None,
) -> int:
    """
    Calculate a deterministic Water Saver Score on a scale of 0 to 100.

    Parameters:
        daily_consumption: Total estimated daily water use in litres.
        user_type: "household" or "farmer".
        details: Optional dictionary of usage inputs (e.g. household_size,
                 showers_per_day, irrigation_method, etc.) for habit adjustments.

    Returns:
        Integer score between 0 and 100 inclusive.
    """
    details = details or {}
    user_type_norm = (user_type or "household").strip().lower()

    if user_type_norm == "household":
        # 1. Determine per-capita daily consumption (Litres Per Capita per Day)
        household_size = max(1, int(float(details.get("household_size", 1))))
        lpcd = max(0.0, float(daily_consumption) / household_size)

        # 2. Base score uses 150 L/person/day as a reference point.
        # lpcd <= 75  -> base 95-100 (exemplary conservation)
        # lpcd = 150  -> base 70 (the reference point)
        # lpcd = 200  -> base 55 (high threshold)
        # lpcd = 300  -> base 30
        # lpcd >= 450 -> base 5
        if lpcd <= 75.0:
            base_score = 100.0 - (lpcd / 75.0) * 5.0  # 95 to 100
        elif lpcd <= BENCHMARK_HOUSEHOLD_LPCD:  # 75 to 150
            ratio = (lpcd - 75.0) / (BENCHMARK_HOUSEHOLD_LPCD - 75.0)
            base_score = 95.0 - ratio * 25.0  # 70 to 95
        elif lpcd <= HIGH_CONSUMPTION_THRESHOLD_LPCD:  # 150 to 200
            ratio = (lpcd - BENCHMARK_HOUSEHOLD_LPCD) / (HIGH_CONSUMPTION_THRESHOLD_LPCD - BENCHMARK_HOUSEHOLD_LPCD)
            base_score = 70.0 - ratio * 15.0  # 55 to 70
        elif lpcd <= 300.0:  # 200 to 300
            ratio = (lpcd - HIGH_CONSUMPTION_THRESHOLD_LPCD) / 100.0
            base_score = 55.0 - ratio * 25.0  # 30 to 55
        else:  # > 300
            excess = min(150.0, lpcd - 300.0)
            base_score = max(5.0, 30.0 - (excess / 150.0) * 25.0)  # 5 to 30

        # 3. Habit-based adjustments
        adjustments = 0.0

        # Short showers bonus / penalty
        duration = float(details.get("shower_duration_minutes", 0.0))
        if 0 < duration <= 5.0:
            adjustments += 4.0
        elif duration >= 12.0:
            adjustments -= 5.0

        # Vehicle washing habits
        veh_freq_value = details.get("vehicle_washing_frequency")
        if veh_freq_value is not None and veh_freq_value != "":
            veh_freq = float(veh_freq_value)
            if veh_freq == 0:
                adjustments += 2.0
            elif veh_freq >= 3.0:
                adjustments -= 4.0

        # Kitchen efficiency
        kitchen_mins = float(details.get("kitchen_usage_minutes", 0.0))
        if 0 < kitchen_mins <= 15.0:
            adjustments += 2.0
        elif kitchen_mins >= 45.0:
            adjustments -= 3.0

        final_score = int(round(base_score + adjustments))

    else:
        # Agricultural / Farmer Scoring
        method = str(details.get("irrigation_method", "flood")).strip().lower()
        has_rainwater = bool(details.get("rainwater_harvesting", False))
        freq = float(details.get("irrigation_frequency", 0.0))

        # Base score from irrigation technology efficiency
        if method == "drip":
            base_score = 85.0  # Drip application efficiency > 90%
        elif method == "sprinkler":
            base_score = 70.0  # Sprinkler efficiency ~75-80%
        elif method == "flood":
            base_score = 45.0  # Flood irrigation loses 40-50%
        else:
            base_score = 55.0

        # Rainwater harvesting credit
        if has_rainwater:
            base_score += 10.0

        # Moderate frequency bonus
        if 0 < freq <= 3.0:
            base_score += 5.0
        elif freq >= 6.0:
            base_score -= 5.0

        final_score = int(round(base_score))

    # Strict clamping between 0 and 100
    return max(0, min(100, final_score))


# ---------------------------------------------------------------------------
# Streak Maintenance Logic
# ---------------------------------------------------------------------------

def update_user_streak(user_id: int, activity_date: date | None = None) -> Streak:
    """
    Update or create a user's conservation streak based on activity date.

    Rules:
    - Same-day activity: maintains current streak (idempotent, does not double-count).
    - Consecutive day activity (yesterday -> today): increments current_streak by 1.
    - Broken streak (gap > 1 day): resets current_streak to 1.
    - Updates longest_streak whenever current_streak surpasses it.
    """
    today = activity_date or date.today()

    streak = Streak.query.filter_by(user_id=user_id).first()
    if not streak:
        streak = Streak(
            user_id=user_id,
            current_streak=1,
            longest_streak=1,
            last_activity_date=today,
        )
        db.session.add(streak)
        return streak

    if streak.last_activity_date is None:
        streak.current_streak = 1
        streak.longest_streak = max(1, streak.longest_streak)
        streak.last_activity_date = today
        return streak

    last = streak.last_activity_date

    # Same day activity: idempotent, no change to streak count
    if last == today:
        return streak

    # Consecutive day activity: increment streak
    if last == today - timedelta(days=1):
        streak.current_streak += 1
        if streak.current_streak > streak.longest_streak:
            streak.longest_streak = streak.current_streak
        streak.last_activity_date = today
        return streak

    # Broken streak: more than 1 day missed, restart at 1
    if last < today - timedelta(days=1):
        streak.current_streak = 1
        if streak.longest_streak == 0:
            streak.longest_streak = 1
        streak.last_activity_date = today
        return streak

    # Activity date is in the past (historical backfill): keep current streak unchanged
    return streak


# ---------------------------------------------------------------------------
# Achievement Evaluation Logic
# ---------------------------------------------------------------------------

def evaluate_user_achievements(
    user_id: int,
    assessment: Assessment | None = None,
) -> list[UserAchievement]:
    """
    Check if the user qualifies for any unearned achievements and award them.

    Milestone Requirements evaluated:
    - "assessments_count": Total completed assessments >= requirement_value
    - "score_above": Assessment score >= requirement_value
    - "streak_days": User current or longest streak >= requirement_value

    Returns:
        List of newly awarded UserAchievement records.
    """
    # Fetch all existing earned achievement IDs for this user
    earned_records = UserAchievement.query.filter_by(user_id=user_id).all()
    earned_ids = {r.achievement_id for r in earned_records}

    # Fetch all available achievements in the system
    all_achievements = Achievement.query.all()
    if not all_achievements:
        return []

    # Calculate user metrics
    assessments_count = Assessment.query.filter_by(user_id=user_id).count()
    user_streak = Streak.query.filter_by(user_id=user_id).first()
    max_streak = (
        max(user_streak.current_streak, user_streak.longest_streak)
        if user_streak
        else 0
    )

    current_score = assessment.water_saver_score if assessment else 0

    newly_awarded: list[UserAchievement] = []

    for ach in all_achievements:
        if ach.id in earned_ids:
            continue

        qualifies = False

        if ach.requirement_type == "assessments_count":
            if assessments_count >= ach.requirement_value:
                qualifies = True

        elif ach.requirement_type == "score_above":
            # Check current assessment score or any prior high score
            if current_score >= ach.requirement_value:
                qualifies = True
            else:
                high_score = (
                    db.session.query(db.func.max(Assessment.water_saver_score))
                    .filter(Assessment.user_id == user_id)
                    .scalar()
                )
                if high_score and high_score >= ach.requirement_value:
                    qualifies = True

        elif ach.requirement_type == "streak_days":
            if max_streak >= ach.requirement_value:
                qualifies = True

        if qualifies:
            new_record = UserAchievement(
                user_id=user_id,
                achievement_id=ach.id,
            )
            db.session.add(new_record)
            newly_awarded.append(new_record)

    return newly_awarded
