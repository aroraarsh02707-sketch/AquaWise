"""
Dashboard & Trends REST API Routes.

Provides endpoints for retrieving dashboard metrics and trends for the current user:
- GET /api/dashboard : Retrieve the latest assessment metrics, category breakdown, streak, and top category
- GET /api/dashboard/trends : Retrieve chronological historical assessment data
"""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user
from backend.models import db, Assessment, Streak, ConsumptionBreakdown

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/api/dashboard", methods=["GET"])
@login_required
def get_dashboard():
    """Retrieve dashboard metrics and the saved category breakdown for the latest assessment."""
    assessment_count = db.session.query(Assessment).filter_by(user_id=current_user.id).count()

    streak = db.session.query(Streak).filter_by(user_id=current_user.id).first()
    current_streak = streak.current_streak if streak else 0

    latest_assessment = db.session.query(Assessment)\
        .filter_by(user_id=current_user.id)\
        .order_by(Assessment.created_at.desc())\
        .first()

    if not latest_assessment:
        return jsonify({
            "success": True,
            "data": {
                "assessment_count": 0,
                "latest_daily_consumption": None,
                "latest_weekly_consumption": None,
                "latest_monthly_consumption": None,
                "latest_water_saver_score": None,
                "latest_assessment_id": None,
                "latest_assessment_type": None,
                "latest_calculation": None,
                "current_streak": current_streak,
                "top_category": None,
                "category_breakdown": [],
                "recommendations": []
            }
        }), 200

    breakdown_rows = db.session.query(ConsumptionBreakdown)\
        .filter_by(assessment_id=latest_assessment.id)\
        .order_by(ConsumptionBreakdown.litres_per_day.desc())\
        .all()
    category_breakdown = [row.to_dict() for row in breakdown_rows]
    top_category = category_breakdown[0]["category"] if category_breakdown else None

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
            "latest_assessment_id": latest_assessment.id,
            "latest_assessment_type": latest_assessment.assessment_type,
            "latest_calculation": latest_assessment.calculation_details,
            "current_streak": current_streak,
            "top_category": top_category,
            "category_breakdown": category_breakdown,
            "recommendations": recs_list
        }
    }), 200


@dashboard_bp.route("/api/dashboard/trends", methods=["GET"])
@login_required
def get_trends():
    """Retrieve chronological historical assessment data for the current user."""
    assessments = db.session.query(Assessment)\
        .filter_by(user_id=current_user.id)\
        .order_by(Assessment.assessment_date.asc(), Assessment.created_at.asc())\
        .all()

    trends = [{
        "assessment_id": assessment.id,
        "date": assessment.assessment_date.strftime("%Y-%m-%d"),
        "daily_consumption": round(assessment.daily_consumption, 1),
        "water_saver_score": assessment.water_saver_score
    } for assessment in assessments]

    return jsonify({"success": True, "data": {"trends": trends}}), 200
