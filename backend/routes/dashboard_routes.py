"""
Dashboard & Trends REST API Routes.

Provides endpoints for retrieving dashboard metrics and trend data for the current user:
- GET /api/dashboard : Retrieve the latest assessment metrics, streak, and top category
- GET /api/dashboard/trends : Retrieve chronological historical assessment data
"""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from backend.models import db, Assessment, Streak, ConsumptionBreakdown

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard", methods=["GET"])
@login_required
def get_dashboard():
    """
    Retrieve dashboard metrics for the current user.
    """
    # Assessment count
    assessment_count = db.session.query(Assessment).filter_by(user_id=current_user.id).count()
    
    # Current streak
    streak = db.session.query(Streak).filter_by(user_id=current_user.id).first()
    current_streak = streak.current_streak if streak else 0

    # Latest assessment
    latest_assessment = db.session.query(Assessment)\
        .filter_by(user_id=current_user.id)\
        .order_by(Assessment.created_at.desc())\
        .first()

    if not latest_assessment:
        # Empty state for new users
        return jsonify({
            "success": True,
            "data": {
                "assessment_count": 0,
                "latest_daily_consumption": None,
                "latest_weekly_consumption": None,
                "latest_monthly_consumption": None,
                "latest_water_saver_score": None,
                "current_streak": current_streak,
                "top_category": None,
                "recommendations": []
            }
        }), 200

    # Top category
    top_breakdown = db.session.query(ConsumptionBreakdown)\
        .filter_by(assessment_id=latest_assessment.id)\
        .order_by(ConsumptionBreakdown.litres_per_day.desc())\
        .first()
    top_category = top_breakdown.category if top_breakdown else None

    # Recommendations
    recs_list = [r.to_dict() for r in latest_assessment.recommendations]
    recs_list.sort(key=lambda r: float(r.get("potential_saving", 0.0)), reverse=True)

    return jsonify({
        "success": True,
        "data": {
            "assessment_count": assessment_count,
            "latest_daily_consumption": round(latest_assessment.daily_consumption, 1),
            "latest_weekly_consumption": round(latest_assessment.weekly_consumption, 1),
            "latest_monthly_consumption": round(latest_assessment.monthly_consumption, 1),
            "latest_water_saver_score": latest_assessment.water_saver_score,
            "current_streak": current_streak,
            "top_category": top_category,
            "recommendations": recs_list
        }
    }), 200


@dashboard_bp.route("/api/dashboard/trends", methods=["GET"])
@login_required
def get_trends():
    """
    Retrieve chronological historical assessment data for the current user.
    """
    assessments = db.session.query(Assessment)\
        .filter_by(user_id=current_user.id)\
        .order_by(Assessment.assessment_date.asc(), Assessment.created_at.asc())\
        .all()

    trends = []
    for a in assessments:
        trends.append({
            "assessment_id": a.id,
            "date": a.assessment_date.strftime("%Y-%m-%d"),
            "daily_consumption": round(a.daily_consumption, 1),
            "water_saver_score": a.water_saver_score
        })

    return jsonify({
        "success": True,
        "data": {
            "trends": trends
        }
    }), 200
