"""
AquaWise Server-Side Input Validators.

Validation is ALWAYS performed on the backend, even when the frontend also
validates the same fields.  The backend is the authoritative source of data
quality.  These functions return a dict of field-level error messages (empty
dict means the data is valid).

Allowed enum values are kept here so they are easy to update and are not
scattered across multiple route files.
"""

import math
import re

# ---------------------------------------------------------------------------
# Allowed enum values (single source of truth for valid option strings)
# ---------------------------------------------------------------------------

VALID_USER_TYPES = {"household", "farmer"}

VALID_IRRIGATION_METHODS = {"flood", "drip", "sprinkler", "other"}

VALID_WATER_SOURCES = {"groundwater", "canal", "rainwater", "tank", "other"}

VALID_FARM_AREA_UNITS = {"acre", "hectare"}

VALID_CROP_TYPES = {
    "wheat", "rice", "maize", "vegetables", "pulses", "fruits", "other"
}

VALID_ROLES = {"user", "assistant"}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _is_valid_email(email: str) -> bool:
    """Basic e-mail format check: must contain @ and a domain with at least one dot."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email.strip()))


def _clamp_errors(errors: dict, data: dict, rules: list) -> None:
    """
    Apply a list of numeric range rules to `data` and populate `errors`.

    Each rule is a tuple:
        (field_name, min_value, max_value, required, label)
    where required=True means the field must be present and non-None.
    """
    for field, min_val, max_val, required, label in rules:
        raw = data.get(field)
        if raw is None or raw == "":
            if required:
                errors[field] = f"{label} is required."
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError, OverflowError):
            errors[field] = f"{label} must be a number."
            continue
        if not math.isfinite(value):
            errors[field] = f"{label} must be a finite number."
            continue
        if value < min_val:
            errors[field] = f"{label} must be at least {min_val}."
        elif value > max_val:
            errors[field] = f"{label} must not exceed {max_val}."


# ---------------------------------------------------------------------------
# Authentication validators
# ---------------------------------------------------------------------------

def validate_registration(data: dict) -> dict:
    """
    Validate user registration payload.

    Expected keys: name, email, password, confirm_password, user_type.
    Returns: dict of field -> error message (empty if valid).
    """
    errors = {}

    name = (data.get("name") or "").strip()
    if not name:
        errors["name"] = "Name is required."
    elif len(name) > 100:
        errors["name"] = "Name must not exceed 100 characters."

    email = (data.get("email") or "").strip().lower()
    if not email:
        errors["email"] = "Email address is required."
    elif not _is_valid_email(email):
        errors["email"] = "Please enter a valid email address."
    elif len(email) > 120:
        errors["email"] = "Email address must not exceed 120 characters."

    password = data.get("password") or ""
    if not password:
        errors["password"] = "Password is required."
    elif len(password) < 6:
        errors["password"] = "Password must be at least 6 characters."
    elif len(password) > 200:
        errors["password"] = "Password is too long."

    confirm_password = data.get("confirm_password") or ""
    if not errors.get("password") and password != confirm_password:
        errors["confirm_password"] = "Passwords do not match."

    user_type = (data.get("user_type") or "").strip().lower()
    if not user_type:
        errors["user_type"] = "User type is required."
    elif user_type not in VALID_USER_TYPES:
        errors["user_type"] = "User type must be 'household' or 'farmer'."

    return errors


def validate_login(data: dict) -> dict:
    """
    Validate login payload.

    Expected keys: email, password.
    """
    errors = {}

    email = (data.get("email") or "").strip()
    if not email:
        errors["email"] = "Email address is required."
    elif not _is_valid_email(email):
        errors["email"] = "Please enter a valid email address."

    if not (data.get("password") or "").strip():
        errors["password"] = "Password is required."

    return errors


# ---------------------------------------------------------------------------
# Household assessment validator
# ---------------------------------------------------------------------------

def validate_household_assessment(data: dict) -> dict:
    """
    Validate a household assessment payload.

    Rules (from TRD Section 30 and PRD Section 29):
      - household_size: integer >= 1 and <= 50
      - showers_per_day: float >= 0 and <= 20
      - shower_duration_minutes: float >= 0 and <= 60
      - toilet_uses_per_day: float >= 0 and <= 60
      - laundry_loads_per_week: float >= 0 and <= 30
      - kitchen_usage_minutes: float >= 0 and <= 180
      - vehicle_washing_frequency: float >= 0 and <= 14 (sessions per week)
      - gardening_frequency: float >= 0 and <= 14 (sessions per week)
      - gardening_duration_minutes: float >= 0 and <= 240
      - other_usage_litres: float >= 0 and <= 1000 (direct litre estimate)
    """
    if data.get("assessment_version") == 2 or data.get("extended_answers"):
        return validate_household_assessment_v2(data)

    errors = {}

    numeric_rules = [
        # (field, min, max, required, display_label)
        ("household_size",          1,    50,  True,  "Household size"),
        ("showers_per_day",         0,    20,  True,  "Showers per day"),
        ("shower_duration_minutes", 0,    60,  True,  "Average shower duration"),
        ("toilet_uses_per_day",     0,    60,  True,  "Toilet flushes per day"),
        ("laundry_loads_per_week",  0,    30,  True,  "Laundry loads per week"),
        ("kitchen_usage_minutes",   0,   180,  True,  "Kitchen tap usage (minutes/day)"),
        ("vehicle_washing_frequency", 0,  14,  False, "Vehicle washing frequency (per week)"),
        ("gardening_frequency",     0,    14,  False, "Gardening sessions per week"),
        ("gardening_duration_minutes", 0, 240, False, "Gardening duration (minutes)"),
        ("other_usage_litres",      0,  1000,  False, "Other water usage (litres/day)"),
    ]
    _clamp_errors(errors, data, numeric_rules)
    household_size = data.get("household_size")
    try:
        if household_size not in (None, "") and math.isfinite(float(household_size)) and not float(household_size).is_integer():
            errors["household_size"] = "Household size must be a whole number of people."
    except (TypeError, ValueError, OverflowError):
        pass

    return errors


def validate_household_assessment_v2(data: dict) -> dict:
    """Validate versioned household answers while preserving the legacy API."""
    errors = {}
    answers = data.get("extended_answers")
    if not isinstance(answers, dict):
        return {"extended_answers": "Household answers must be provided."}

    legacy_payload = {key: value for key, value in data.items() if key not in {"assessment_version", "extended_answers"}}
    errors.update(validate_household_assessment(legacy_payload))
    numeric = {
        "showers_per_person_per_day": (0, 20, "Showers per person per day"),
        "shower_duration_minutes": (0, 120, "Shower duration"),
        "shower_flow_rate_lpm": (0.1, 40, "Shower flow rate"),
        "bucket_baths_per_person_per_day": (0, 20, "Bucket baths per person per day"),
        "buckets_per_bath": (0, 50, "Buckets per bath"),
        "bucket_capacity_litres": (0.1, 100, "Bucket capacity"),
        "toilet_flushes_per_person_per_day": (0, 60, "Toilet flushes per person per day"),
        "toilet_flush_volume_litres": (0.1, 40, "Toilet flush volume"),
        "bathroom_tap_minutes_per_person_per_day": (0, 300, "Bathroom tap time"),
        "bathroom_tap_flow_rate_lpm": (0.1, 40, "Bathroom tap flow rate"),
        "kitchen_tap_minutes_per_day": (0, 600, "Kitchen tap time"),
        "kitchen_tap_flow_rate_lpm": (0.1, 40, "Kitchen tap flow rate"),
        "dishwashing_tap_minutes_per_day": (0, 600, "Dishwashing tap time"),
        "dishwashing_litres_per_day": (0, 3000, "Dishwashing volume"),
        "dishwasher_cycles_per_week": (0, 100, "Dishwasher cycles per week"),
        "dishwasher_litres_per_cycle": (0.1, 300, "Dishwasher volume per cycle"),
        "laundry_loads_per_week": (0, 100, "Laundry loads per week"),
        "laundry_litres_per_load": (0.1, 500, "Laundry volume per load"),
        "handwash_litres_per_load": (0.1, 1000, "Handwashing volume per load"),
        "handwash_buckets_per_load": (0.1, 100, "Buckets per laundry load"),
        "handwash_bucket_capacity_litres": (0.1, 100, "Laundry bucket capacity"),
        "cleaning_sessions_per_week": (0, 100, "Cleaning sessions per week"),
        "cleaning_minutes_per_session": (0, 600, "Cleaning time per session"),
        "cleaning_flow_rate_lpm": (0.1, 60, "Cleaning flow rate"),
        "cleaning_litres_per_session": (0, 5000, "Cleaning volume per session"),
        "garden_sessions_per_week": (0, 100, "Garden watering sessions per week"),
        "garden_minutes_per_session": (0, 600, "Watering time per session"),
        "garden_flow_rate_lpm": (0.1, 60, "Watering flow rate"),
        "garden_litres_per_session": (0, 5000, "Watering volume per session"),
    }
    for name, (minimum, maximum, label) in numeric.items():
        value = answers.get(name)
        if value in (None, ""):
            continue
        try:
            number = float(value)
            if number != number or number in (float("inf"), float("-inf")):
                raise ValueError
        except (TypeError, ValueError, OverflowError):
            errors[f"extended_answers.{name}"] = f"{label} must be a valid number."
            continue
        if number < minimum or number > maximum:
            errors[f"extended_answers.{name}"] = f"{label} must be between {minimum:g} and {maximum:g}."

    enums = {
        "bathing_method": {"shower", "bucket", "both"},
        "toilet_type": {"standard", "dual_flush", "low_flow", "unknown"},
        "dishwashing_method": {"running_water", "basin", "other"},
        "laundry_method": {"front_load", "top_load", "hand_wash", "other_machine"},
        "cleaning_method": {"bucket_mop", "hose", "equipment", "other"},
        "garden_method": {"watering_can", "hose", "sprinkler", "drip"},
        "leak_status": {"none", "minor", "significant", "unsure"},
    }
    for name, options in enums.items():
        value = answers.get(name)
        if value is not None and value not in options:
            errors[f"extended_answers.{name}"] = f"Choose a valid {name.replace('_', ' ')} option."

    for name in ("has_dishwasher", "has_garden", "tap_off_while_brushing", "laundry_full_loads", "kitchen_tap_runs_while_washing"):
        if name in answers and not isinstance(answers[name], bool):
            errors[f"extended_answers.{name}"] = "Choose yes or no."
    if answers.get("has_dishwasher") is not True and _num_for_validation(answers.get("dishwasher_cycles_per_week")) not in (None, 0):
        errors["extended_answers.dishwasher_cycles_per_week"] = "Dishwasher cycles require a dishwasher."

    list_options = {
        "water_sources": {"municipal", "borewell", "private_well", "tanker", "rainwater", "multiple"},
        "conservation_measures": {"tap_aerators", "low_flow_showerhead", "dual_flush_toilet", "rainwater_harvesting", "greywater_reuse", "efficient_irrigation", "prompt_leak_repairs", "other"},
    }
    for name, options in list_options.items():
        value = answers.get(name, [])
        if not isinstance(value, list) or any(item not in options for item in value) or (name == "water_sources" and not value):
            errors[f"extended_answers.{name}"] = "Select valid options."
    fixture = answers.get("leak_fixture")
    if fixture is not None and (not isinstance(fixture, str) or len(fixture) > 100):
        errors["extended_answers.leak_fixture"] = "Fixture description must be 100 characters or fewer."
    return errors


def _num_for_validation(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError, OverflowError):
        return None


# ---------------------------------------------------------------------------
# Farmer assessment validator
# ---------------------------------------------------------------------------

def validate_farmer_assessment(data: dict) -> dict:
    """
    Validate a farmer / agricultural assessment payload.

    Rules (from TRD Section 30 and PRD Sections 8, 29):
      - farm_area: float > 0 and <= 10,000 (acres or hectares)
      - farm_area_unit: must be 'acre' or 'hectare'
      - crop_type: required string, <= 100 characters
      - irrigation_method: one of flood / drip / sprinkler / other
      - irrigation_frequency: float >= 0 and <= 30 (sessions per week)
      - irrigation_duration_minutes: float >= 0 and <= 1440 (max 24 h per session)
      - water_source: one of the allowed sources
      - estimated_irrigation_litres: float >= 0 (optional override; 0 means unknown)
    """
    errors = {}

    numeric_rules = [
        ("farm_area",                  0.001, 10000, True,  "Farm area"),
        ("irrigation_frequency",       0,       30,  False, "Irrigation sessions per week"),
        ("irrigation_duration_minutes",0,     1440,  False, "Irrigation duration (minutes)"),
        ("estimated_irrigation_litres",0,  1_000_000, False, "Estimated irrigation volume (litres)"),
    ]
    _clamp_errors(errors, data, numeric_rules)

    farm_area_unit = (data.get("farm_area_unit") or "acre").strip().lower()
    if farm_area_unit not in VALID_FARM_AREA_UNITS:
        errors["farm_area_unit"] = "Farm area unit must be 'acre' or 'hectare'."

    crop_type = (data.get("crop_type") or "").strip()
    if not crop_type:
        errors["crop_type"] = "Crop type is required."
    elif len(crop_type) > 100:
        errors["crop_type"] = "Crop type must not exceed 100 characters."

    irrigation_method = (data.get("irrigation_method") or "").strip().lower()
    if not irrigation_method:
        errors["irrigation_method"] = "Irrigation method is required."
    elif irrigation_method not in VALID_IRRIGATION_METHODS:
        errors["irrigation_method"] = (
            "Irrigation method must be one of: flood, drip, sprinkler, other."
        )

    water_source = (data.get("water_source") or "").strip().lower()
    if water_source and water_source not in VALID_WATER_SOURCES:
        errors["water_source"] = (
            "Water source must be one of: groundwater, canal, rainwater, tank, other."
        )

    return errors


# ---------------------------------------------------------------------------
# Generic assessment router
# ---------------------------------------------------------------------------

def validate_assessment(data: dict) -> dict:
    """
    Dispatch validation based on assessment_type in `data`.
    Always validates assessment_type is present and valid first.
    """
    errors = {}

    assessment_type = (data.get("assessment_type") or "").strip().lower()
    if not assessment_type:
        errors["assessment_type"] = "Assessment type is required."
        return errors
    if assessment_type not in VALID_USER_TYPES:
        errors["assessment_type"] = "Assessment type must be 'household' or 'farmer'."
        return errors

    if assessment_type == "household":
        errors.update(validate_household_assessment(data))
    else:
        errors.update(validate_farmer_assessment(data))

    return errors
