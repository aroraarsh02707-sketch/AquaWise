"""
Profile & Gamification REST API Routes (Task 7).

Endpoints:
- GET /api/profile : Get current user's profile, streak stats, assessment count, and earned badges.
- PUT /api/profile : Update permitted profile fields (name).
- GET /api/profile/achievements : Get all achievements and user's unlock status.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.models import db, User, Streak, Achievement, UserAchievement, Assessment

profile_bp = Blueprint("profile", __name__)


def _validate_profile_update(data: dict) -> dict:
    errors = {}
    
    if "name" in data:
        name = str(data["name"]).strip()
        if not name:
            errors["name"] = "Name is required."
        elif len(name) > 100:
            errors["name"] = "Name must not exceed 100 characters."
            
    if "user_type" in data:
        errors["user_type"] = "Account type cannot be changed."
            
    return errors


@profile_bp.route("/api/profile", methods=["GET"])
@login_required
def get_profile():
    # User basic info
    profile_data = current_user.to_dict()
    
    # Assessment count
    assessment_count = db.session.query(Assessment).filter_by(user_id=current_user.id).count()
    
    # Streak stats
    streak = db.session.query(Streak).filter_by(user_id=current_user.id).first()
    streak_data = streak.to_dict() if streak else {
        "current_streak": 0,
        "longest_streak": 0,
        "last_activity_date": None
    }
    
    # Earned badges/achievements
    user_achievements = db.session.query(UserAchievement)\
        .filter_by(user_id=current_user.id)\
        .order_by(UserAchievement.earned_at.desc())\
        .all()
    
    badges = [ua.to_dict() for ua in user_achievements]
    
    profile_data["assessment_count"] = assessment_count
    profile_data["streak"] = streak_data
    profile_data["badges"] = badges

    return jsonify({
        "success": True,
        "data": {
            "profile": profile_data
        }
    }), 200


@profile_bp.route("/api/profile", methods=["PUT"])
@login_required
def update_profile():
    data = request.get_json() or {}
    
    # Validation
    errors = _validate_profile_update(data)
    if errors:
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid profile data.",
                "details": errors
            }
        }), 400
        
    # Apply updates
    updated = False
    if "name" in data:
        current_user.name = str(data["name"]).strip()
        updated = True
        
    if updated:
        db.session.commit()
        
    return jsonify({
        "success": True,
        "data": {
            "profile": current_user.to_dict()
        }
    }), 200


@profile_bp.route("/api/profile/achievements", methods=["GET"])
@login_required
def get_achievements():
    all_achievements = db.session.query(Achievement).all()
    user_achievements = db.session.query(UserAchievement).filter_by(user_id=current_user.id).all()
    
    unlocked_dict = {ua.achievement_id: ua for ua in user_achievements}
    
    results = []
    for ach in all_achievements:
        ach_data = ach.to_dict()
        if ach.id in unlocked_dict:
            ach_data["unlocked"] = True
            ach_data["earned_at"] = unlocked_dict[ach.id].earned_at.isoformat() if unlocked_dict[ach.id].earned_at else None
        else:
            ach_data["unlocked"] = False
            ach_data["earned_at"] = None
        results.append(ach_data)
        
    return jsonify({
        "success": True,
        "data": {
            "achievements": results
        }
    }), 200
