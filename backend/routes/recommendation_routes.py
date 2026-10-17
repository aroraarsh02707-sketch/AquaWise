"""
Recommendation REST API Routes.

Provides endpoints for retrieving water conservation recommendations:
- GET /api/assessments/<id>/recommendations : Retrieve recommendations for a specific assessment
  Optional query parameter: ?enhance=true to request AI-personalized wording.

All endpoints enforce strict authentication and user ownership checks.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.models import db, Assessment
from backend.services.ai_service import enhance_recommendations

recommendation_bp = Blueprint("recommendations", __name__)


@recommendation_bp.route("/api/assessments/<int:assessment_id>/recommendations", methods=["GET"])
@recommendation_bp.route("/api/recommendations/<int:assessment_id>", methods=["GET"])
@login_required
def get_assessment_recommendations(assessment_id: int):
    """
    Retrieve recommendations for an assessment.
    
    Query Parameters:
      enhance (bool): If 'true', calls AI service to personalize recommendation wording
                      while strictly preserving deterministic savings and priorities.
    """
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "Assessment not found."
            }
        }), 404

    # Strict user ownership check
    if assessment.user_id != current_user.id:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": "You do not have permission to view recommendations for this assessment."
            }
        }), 403

    # If the assessment has no stored recommendations, return clean empty list
    stored_recs = assessment.recommendations or []
    if not stored_recs:
        return jsonify({
            "success": True,
            "data": {
                "assessment_id": assessment.id,
                "enhanced": False,
                "source": "empty",
                "count": 0,
                "recommendations": []
            }
        }), 200

    enhance_requested = request.args.get("enhance", "false").lower() == "true"

    if enhance_requested:
        # Prepare context for AI enhancement from stored assessment details & breakdown
        details = assessment.household_details.to_dict() if assessment.household_details else {}

        calc_results = {
            "daily_consumption": assessment.daily_consumption,
            "weekly_consumption": assessment.weekly_consumption,
            "monthly_consumption": assessment.monthly_consumption,
            "breakdown": [b.to_dict() for b in assessment.breakdowns],
        }

        # Enhance via AI service (falls back gracefully to rule-based if offline/error)
        recs_list = enhance_recommendations(
            assessment_data=details,
            calculation_results=calc_results,
        )

        overall_source = "hybrid" if any(r.get("source") == "hybrid" for r in recs_list) else "rule_based"
    else:
        # Return the stored deterministic recommendations as-is
        recs_list = [r.to_dict() for r in stored_recs]
        overall_source = stored_recs[0].source if stored_recs else "rule_based"

    # Always sort recommendations by potential water savings descending
    recs_list.sort(key=lambda r: float(r.get("potential_saving") or 0.0), reverse=True)

    return jsonify({
        "success": True,
        "data": {
            "assessment_id": assessment.id,
            "enhanced": enhance_requested and overall_source == "hybrid",
            "source": overall_source,
            "count": len(recs_list),
            "recommendations": recs_list
        }
    }), 200
