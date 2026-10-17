"""
Assessment REST API Routes.

Provides endpoints for managing user water assessments:
- POST   /api/assessments       : Create and calculate a new water assessment
- GET    /api/assessments       : List historical assessments for current user (paginated)
- GET    /api/assessments/<id>  : Retrieve full assessment details with breakdown and recommendations
- DELETE /api/assessments/<id>  : Delete an assessment (with cascade cleanup)

All endpoints enforce strict authentication and user ownership checks.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.models import (
    db,
    Assessment,
    HouseholdUsageDetails,
    FarmerUsageDetails,
    ConsumptionBreakdown,
    Recommendation,
)
from backend.utils.validators import validate_assessment
from backend.services.calculation_service import (
    calculate_household_consumption,
    calculate_farmer_consumption,
)
from backend.services.scoring_service import (
    calculate_water_saver_score,
    update_user_streak,
    evaluate_user_achievements,
)
from backend.services.ai_service import get_fallback_recommendations

assessment_bp = Blueprint("assessments", __name__, url_prefix="/api/assessments")


@assessment_bp.route("", methods=["POST"])
@login_required
def create_assessment():
    """
    Create a new water consumption assessment.
    
    1. Validates input via validate_assessment.
    2. Runs deterministic calculation engine.
    3. Calculates Water Saver Score.
    4. Generates baseline recommendations.
    5. Safely persists all entities inside a single database transaction.
    6. Updates user activity streak and evaluates unlocked achievements.
    """
    data = request.get_json(silent=True) or {}

    # Default assessment_type to user_type if omitted in payload
    if "assessment_type" not in data or not data["assessment_type"]:
        data["assessment_type"] = current_user.user_type

    errors = validate_assessment(data)
    if errors:
        first_err = next(iter(errors.values()))
        return jsonify({
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": first_err,
                "details": errors
            }
        }), 400

    assessment_type = data["assessment_type"].strip().lower()

    # 1. Deterministic Calculation
    if assessment_type == "household":
        calc_results = calculate_household_consumption(data)
    else:
        calc_results = calculate_farmer_consumption(data)

    # 2. Deterministic Water Saver Score
    daily_consumption = calc_results["daily_consumption"]
    score = calculate_water_saver_score(
        daily_consumption=daily_consumption,
        user_type=assessment_type,
        details=data
    )

    # 3. Baseline Rule-Based Recommendations
    base_recs = get_fallback_recommendations(
        assessment_data=data,
        calculation_results=calc_results,
        user_type=assessment_type
    )

    # 4. Atomic Database Transaction
    try:
        assessment = Assessment(
            user_id=current_user.id,
            assessment_type=assessment_type,
            daily_consumption=daily_consumption,
            weekly_consumption=calc_results["weekly_consumption"],
            monthly_consumption=calc_results["monthly_consumption"],
            water_saver_score=score,
            calculation_details=calc_results,
        )
        db.session.add(assessment)
        db.session.flush()  # Allocate assessment.id

        # Add details based on user type
        if assessment_type == "household":
            details = HouseholdUsageDetails(
                assessment_id=assessment.id,
                household_size=int(float(data.get("household_size", 1))),
                showers_per_day=float(data.get("showers_per_day", 0.0)),
                shower_duration_minutes=float(data.get("shower_duration_minutes", 0.0)),
                toilet_uses_per_day=float(data.get("toilet_uses_per_day", 0.0)),
                laundry_loads_per_week=float(data.get("laundry_loads_per_week", 0.0)),
                kitchen_usage_minutes=float(data.get("kitchen_usage_minutes", 0.0)),
                vehicle_washing_frequency=float(data.get("vehicle_washing_frequency", 0.0)),
                gardening_frequency=float(data.get("gardening_frequency", 0.0)),
                gardening_duration_minutes=float(data.get("gardening_duration_minutes", 0.0)),
                other_usage_litres=float(data.get("other_usage_litres", 0.0)),
                extended_answers=data.get("extended_answers"),
            )
            db.session.add(details)
        else:
            details = FarmerUsageDetails(
                assessment_id=assessment.id,
                farm_area=float(data.get("farm_area", 0.0)),
                farm_area_unit=data.get("farm_area_unit", "acre"),
                crop_type=data.get("crop_type", ""),
                irrigation_method=data.get("irrigation_method", "flood"),
                irrigation_frequency=float(data.get("irrigation_frequency", 0.0)),
                irrigation_duration_minutes=float(data.get("irrigation_duration_minutes", 0.0)),
                water_source=data.get("water_source", "groundwater"),
                rainfall_information=data.get("rainfall_information"),
                rainwater_harvesting=bool(data.get("rainwater_harvesting", False)),
                estimated_irrigation_litres=float(data.get("estimated_irrigation_litres", 0.0)),
            )
            db.session.add(details)

        # Add consumption breakdown
        for item in calc_results.get("breakdown", []):
            breakdown_entry = ConsumptionBreakdown(
                assessment_id=assessment.id,
                category=item["category"],
                litres_per_day=item["litres_per_day"],
                percentage=item["percentage"]
            )
            db.session.add(breakdown_entry)

        # Add baseline recommendations
        for rec in base_recs:
            rec_entry = Recommendation(
                assessment_id=assessment.id,
                category=rec["category"],
                title=rec["title"],
                description=rec["description"],
                priority=rec.get("priority", "medium"),
                source=rec.get("source", "rule_based"),
                potential_saving=rec.get("potential_saving", 0.0),
                evidence=rec.get("evidence"),
            )
            db.session.add(rec_entry)

        # Update streak
        streak = update_user_streak(current_user.id)

        # Evaluate achievement unlocks
        newly_awarded = evaluate_user_achievements(current_user.id, assessment)

        db.session.commit()

        # Build clean response object
        response_data = assessment.to_dict(include_details=True)
        response_data["streak"] = streak.to_dict()
        response_data["new_achievements"] = [ua.to_dict() for ua in newly_awarded]

        return jsonify({
            "success": True,
            "data": response_data
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": {
                "code": "ASSESSMENT_CREATION_FAILED",
                "message": "Failed to save assessment. All changes rolled back."
            }
        }), 500


@assessment_bp.route("", methods=["GET"])
@login_required
def get_assessments():
    """
    Retrieve historical assessments for the current user.
    Supports pagination via ?page=1&limit=10.
    """
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    limit = min(max(1, limit), 100)
    include_details = request.args.get("include_details", "false").lower() == "true"

    query = Assessment.query.filter_by(user_id=current_user.id).order_by(
        Assessment.assessment_date.desc(),
        Assessment.id.desc()
    )

    total = query.count()
    items = query.offset((page - 1) * limit).limit(limit).all()

    return jsonify({
        "success": True,
        "data": {
            "assessments": [a.to_dict(include_details=include_details) for a in items],
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "pages": (total + limit - 1) // limit if limit > 0 else 0
            }
        }
    }), 200


@assessment_bp.route("/<int:assessment_id>", methods=["GET"])
@login_required
def get_assessment(assessment_id: int):
    """
    Retrieve details for a specific assessment.
    Enforces user data privacy (404 if missing, 403 if belonging to another user).
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

    if assessment.user_id != current_user.id:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": "You do not have permission to view this assessment."
            }
        }), 403

    return jsonify({
        "success": True,
        "data": assessment.to_dict(include_details=True)
    }), 200


@assessment_bp.route("/<int:assessment_id>", methods=["DELETE"])
@login_required
def delete_assessment(assessment_id: int):
    """
    Delete an assessment and its associated details, breakdowns, and recommendations.
    Enforces ownership validation before deletion.
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

    if assessment.user_id != current_user.id:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": "You do not have permission to delete this assessment."
            }
        }), 403

    try:
        db.session.delete(assessment)
        db.session.commit()
        return jsonify({
            "success": True,
            "data": {
                "message": "Assessment deleted successfully."
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": {
                "code": "DELETE_FAILED",
                "message": "An error occurred while deleting the assessment."
            }
        }), 500
