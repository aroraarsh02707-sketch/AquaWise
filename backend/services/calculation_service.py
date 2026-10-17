"""
AquaWise Water Consumption Calculation Engine.

All calculations here are DETERMINISTIC and INDEPENDENT of any AI service.
The AI layer (Phase 4) may later personalise the *language* of recommendations,
but it must never alter the numerical results produced by this module.

Calculations are based on the configurable assumptions in
`backend/utils/constants.py`.  The application must communicate to users that
results are *estimated* values, not direct meter readings.

Public API
----------
calculate_household_consumption(data) -> dict
    Accepts validated household assessment data and returns a result dict.

calculate_farmer_consumption(data) -> dict
    Accepts validated farmer assessment data and returns a result dict.

Both functions return the same shape:
    {
        "daily_consumption":   float,   # litres/day
        "weekly_consumption":  float,   # litres/week  (daily * 7)
        "monthly_consumption": float,   # litres/month (daily * 30)
        "breakdown": [                  # one entry per category
            {"category": str, "litres_per_day": float, "percentage": float},
            ...
        ]
    }
"""

import math

from backend.utils.constants import (
    # Shower
    SHOWER_FLOW_RATE_LPM,
    BUCKET_BATH_VOLUME_L,
    # Toilet
    TOILET_FLUSH_DEFAULT_L,
    # Laundry
    LAUNDRY_WATER_PER_LOAD_L,
    # Kitchen
    KITCHEN_TAP_FLOW_RATE_LPM,
    # Vehicle
    VEHICLE_WASH_HOSE_L,
    VEHICLE_WASH_BUCKET_L,
    VEHICLE_WASH_PRESSURE_WASHER_L,
    VEHICLE_WASH_DEFAULT_L,
    # Gardening
    GARDENING_HOSE_FLOW_RATE_LPM,
    GARDENING_SPRINKLER_FLOW_RATE_LPM,
    GARDENING_DRIP_FLOW_RATE_LPM,
    GARDENING_BUCKET_FLOW_RATE_LPM,
    GARDENING_DEFAULT_FLOW_RATE_LPM,
    # Irrigation
    ACRES_TO_HECTARES,
    IRRIGATION_RATE_L_PER_HA_PER_HOUR,
    IRRIGATION_RATE_DEFAULT,
    # Time constants
    DAYS_IN_WEEK,
    DAYS_IN_MONTH,
    HOUSEHOLD_ASSESSMENT_DEFAULTS,
)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _safe_float(value, default: float = 0.0) -> float:
    """Convert a value to float, returning `default` if conversion fails."""
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return default
    return max(0.0, number) if math.isfinite(number) else default


def _build_breakdown(category_litres: dict[str, float]) -> tuple[float, list[dict]]:
    """
    Given a dict of {category: litres_per_day}, calculate the total daily
    consumption and construct the breakdown list with percentages.

    Returns: (total_daily, breakdown_list)
    """
    normalized = {}
    for category, value in category_litres.items():
        litres = float(value)
        if not math.isfinite(litres):
            raise ValueError(f"Non-finite water estimate for {category}.")
        normalized[category] = max(0.0, litres)
    total = sum(normalized.values())
    if not math.isfinite(total):
        raise ValueError("Water estimate total is outside the supported numeric range.")

    breakdown = []
    for category, litres in normalized.items():
        pct = (litres / total * 100.0) if total > 0 else 0.0
        breakdown.append({
            "category": category,
            "litres_per_day": round(litres, 2),
            "percentage": round(pct, 1),
        })

    # Sort descending so the highest consumer is always first
    breakdown.sort(key=lambda x: x["litres_per_day"], reverse=True)

    return round(total, 2), breakdown


def _project(daily: float, days: int) -> float:
    projected = daily * days
    if not math.isfinite(projected):
        raise ValueError("Water estimate projection is outside the supported numeric range.")
    return round(projected, 2)


def _to_weekly(daily: float) -> float:
    return _project(daily, DAYS_IN_WEEK)


def _to_monthly(daily: float) -> float:
    return _project(daily, DAYS_IN_MONTH)


def _result(daily: float, breakdown: list[dict]) -> dict:
    """Package the final result in the standard shape expected by routes."""
    return {
        "daily_consumption": daily,
        "weekly_consumption": _to_weekly(daily),
        "monthly_consumption": _to_monthly(daily),
        "breakdown": breakdown,
    }


# ---------------------------------------------------------------------------
# Household calculation
# ---------------------------------------------------------------------------

def calculate_household_consumption(data: dict) -> dict:
    """
    Estimate a household's daily water consumption from usage inputs.

    Parameters
    ----------
    data : dict
        Validated household assessment data with the following numeric fields.
        All values must already be validated and should be float-compatible.

        Field                       Unit          Converted to daily as
        -----------------------     ----------    -----------------------------------
        household_size              integer       multiplied into shower/toilet totals
        showers_per_day             per day       already daily
        shower_duration_minutes     minutes       × SHOWER_FLOW_RATE_LPM
        toilet_uses_per_day         per day       × TOILET_FLUSH_DEFAULT_L
        laundry_loads_per_week      per week      ÷ 7
        kitchen_usage_minutes       minutes/day   × KITCHEN_TAP_FLOW_RATE_LPM
        vehicle_washing_frequency   per week      ÷ 7
        gardening_frequency         per week      ÷ 7
        gardening_duration_minutes  minutes/sess  × flow_rate
        other_usage_litres          litres/day    used directly

    Notes
    -----
    - Showers and toilet usage are multiplied by household_size because the
      inputs (showers_per_day, toilet_uses_per_day) are per-person values
      that apply to every member of the household.
    - Kitchen minutes is treated as total household daily usage, not per person.
    - Laundry, vehicle, gardening are weekly activities converted to daily.
    - If optional fields are absent (0 or None), they contribute 0 L/day.
    """
    if data.get("assessment_version") == 2 or data.get("extended_answers"):
        return calculate_household_assessment_v2(data)

    size = max(1, int(_safe_float(data.get("household_size"), 1)))

    # --- Bathing ---
    showers_per_day          = _safe_float(data.get("showers_per_day"))
    shower_duration_minutes  = _safe_float(data.get("shower_duration_minutes"))
    bathing_litres_per_day   = showers_per_day * shower_duration_minutes * SHOWER_FLOW_RATE_LPM * size
    # Assumption: each person takes `showers_per_day` showers of `shower_duration_minutes`

    # --- Toilet ---
    toilet_uses_per_day  = _safe_float(data.get("toilet_uses_per_day"))
    toilet_litres_per_day = toilet_uses_per_day * TOILET_FLUSH_DEFAULT_L * size
    # Assumption: `toilet_uses_per_day` flushes per person; multiplied by household size

    # --- Laundry ---
    laundry_loads_per_week = _safe_float(data.get("laundry_loads_per_week"))
    laundry_litres_per_day = (laundry_loads_per_week * LAUNDRY_WATER_PER_LOAD_L) / DAYS_IN_WEEK
    # Assumption: weekly loads divided by 7 to get daily equivalent

    # --- Kitchen / Tap ---
    kitchen_minutes_per_day = _safe_float(data.get("kitchen_usage_minutes"))
    kitchen_litres_per_day  = kitchen_minutes_per_day * KITCHEN_TAP_FLOW_RATE_LPM
    # Assumption: total household kitchen tap-on time per day

    # --- Vehicle Washing ---
    vehicle_freq_per_week   = _safe_float(data.get("vehicle_washing_frequency"))
    vehicle_litres_per_day  = (vehicle_freq_per_week * VEHICLE_WASH_DEFAULT_L) / DAYS_IN_WEEK
    # Assumption: washes per week at the default mixed-method volume ÷ 7

    # --- Gardening ---
    gardening_freq_per_week     = _safe_float(data.get("gardening_frequency"))
    gardening_duration_minutes  = _safe_float(data.get("gardening_duration_minutes"))
    gardening_litres_per_day    = (
        gardening_freq_per_week * gardening_duration_minutes * GARDENING_DEFAULT_FLOW_RATE_LPM
    ) / DAYS_IN_WEEK
    # Assumption: sessions per week × minutes per session × default flow rate ÷ 7

    # --- Other (direct estimate provided by user) ---
    other_litres_per_day = _safe_float(data.get("other_usage_litres"))
    # Assumption: user provides a direct litres-per-day estimate for any other activity

    # --- Build breakdown and total ---
    category_litres = {
        "Bathing":        bathing_litres_per_day,
        "Toilet":         toilet_litres_per_day,
        "Laundry":        laundry_litres_per_day,
        "Kitchen":        kitchen_litres_per_day,
        "Vehicle Washing": vehicle_litres_per_day,
        "Gardening":      gardening_litres_per_day,
        "Other":          other_litres_per_day,
    }

    daily, breakdown = _build_breakdown(category_litres)
    return _result(daily, breakdown)


def _optional_number(value):
    """Return a finite non-negative value, or None when the answer is unknown."""
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def calculate_household_assessment_v2(data: dict) -> dict:
    """Calculate a household assessment from explicit answers and disclosed defaults.

    Categories with insufficient data are omitted from ``breakdown``; they are
    not silently treated as zero. A zero only contributes when the user
    explicitly entered zero or selected a not-applicable answer.
    """
    answers = data.get("extended_answers") or {}
    size = max(1, int(_safe_float(data.get("household_size"), 1)))
    defaults = HOUSEHOLD_ASSESSMENT_DEFAULTS
    category_values: dict[str, float] = {}
    category_sources: dict[str, str] = {}
    source_litres = {"user": 0.0, "assumption": 0.0}
    assumptions: list[str] = []
    incomplete_categories: set[str] = set()

    def add(category, value, source="user"):
        if value is None:
            return
        litres = max(0.0, float(value))
        category_values[category] = category_values.get(category, 0.0) + litres
        existing_source = category_sources.get(category)
        category_sources[category] = source if existing_source in (None, source) else "mixed"
        if source in source_litres:
            source_litres[source] += litres

    def assumed(key, label):
        assumptions.append(f"{label}: {defaults[key]}")
        return float(defaults[key])

    # 1. Bathing: shower and bucket-bath components are added only when selected.
    method = answers.get("bathing_method", "shower")
    bath_incomplete = False
    bath_components = []
    if method in {"shower", "both"}:
        count = _optional_number(answers.get("showers_per_person_per_day"))
        duration = _optional_number(answers.get("shower_duration_minutes"))
        if count is None or duration is None:
            bath_incomplete = True
        else:
            flow = _optional_number(answers.get("shower_flow_rate_lpm"))
            source = "user"
            if flow is None and count > 0 and duration > 0:
                flow = assumed("shower_flow_lpm", "Default shower flow (L/min)")
                source = "assumption"
            bath_components.append((count * duration * (flow or 0) * size, source))
    if method in {"bucket", "both"}:
        baths = _optional_number(answers.get("bucket_baths_per_person_per_day"))
        buckets = _optional_number(answers.get("buckets_per_bath"))
        if baths is None or buckets is None:
            bath_incomplete = True
        else:
            capacity = _optional_number(answers.get("bucket_capacity_litres"))
            source = "user"
            if capacity is None and baths > 0 and buckets > 0:
                capacity = assumed("bucket_capacity_l", "Default bucket capacity (L)")
                source = "assumption"
            bath_components.append((baths * buckets * (capacity or 0) * size, source))
    if method in {"shower", "bucket", "both"}:
        for litres, source in bath_components:
            add("Bathing & showers", litres, source)
        if bath_incomplete and bath_components:
            incomplete_categories.add("Bathing & showers")

    # 2. Toilet: specific known flush volumes override configurable type defaults.
    flushes = _optional_number(answers.get("toilet_flushes_per_person_per_day"))
    if flushes is not None:
        flush_volume = _optional_number(answers.get("toilet_flush_volume_litres"))
        source = "user"
        if flush_volume is None:
            toilet_type = answers.get("toilet_type", "unknown")
            flush_volume = float(defaults["toilet_flush_l"].get(toilet_type, defaults["toilet_flush_l"]["unknown"]))
            assumptions.append(f"Default {toilet_type.replace('_', ' ')} toilet flush volume: {flush_volume:g} L/flush")
            source = "assumption"
        add("Toilet flushing", flushes * flush_volume * size, source)

    # 3. Bathroom taps: daily minutes per resident × configurable/known flow.
    tap_minutes = _optional_number(answers.get("bathroom_tap_minutes_per_person_per_day"))
    if tap_minutes is not None:
        tap_flow = _optional_number(answers.get("bathroom_tap_flow_rate_lpm"))
        source = "user"
        if tap_flow is None:
            tap_flow = assumed("tap_flow_lpm", "Default bathroom tap flow (L/min)")
            source = "assumption"
        add("Bathroom taps", tap_minutes * tap_flow * size, source)

    # 4. Kitchen and dishwashing. Known components remain in the total when a
    # separate optional dishwashing detail is unknown; that partial category is disclosed.
    kitchen_minutes = _optional_number(answers.get("kitchen_tap_minutes_per_day"))
    dish_mode = answers.get("dishwashing_method")
    dishwasher = answers.get("has_dishwasher") is True
    kitchen_components = []
    kitchen_incomplete = kitchen_minutes is None
    kitchen_category = "Kitchen & dishwashing"
    if kitchen_minutes is not None:
        flow = _optional_number(answers.get("kitchen_tap_flow_rate_lpm"))
        source = "user"
        if kitchen_minutes > 0 and flow is None:
            flow = assumed("tap_flow_lpm", "Default kitchen tap flow (L/min)")
            source = "assumption"
        kitchen_components.append((kitchen_minutes * (flow or 0), source))
    if dishwasher:
        cycles = _optional_number(answers.get("dishwasher_cycles_per_week"))
        if cycles is None:
            kitchen_incomplete = True
        else:
            per_cycle = _optional_number(answers.get("dishwasher_litres_per_cycle"))
            source = "user"
            if cycles > 0 and per_cycle is None:
                per_cycle = assumed("dishwasher_l_per_cycle", "Default dishwasher use (L/cycle)")
                source = "assumption"
            kitchen_components.append((cycles * (per_cycle or 0) / DAYS_IN_WEEK, source))
    elif dish_mode == "running_water":
        dish_minutes = _optional_number(answers.get("dishwashing_tap_minutes_per_day"))
        if dish_minutes is None:
            kitchen_incomplete = True
        else:
            flow = _optional_number(answers.get("kitchen_tap_flow_rate_lpm"))
            source = "user"
            if dish_minutes > 0 and flow is None:
                flow = assumed("tap_flow_lpm", "Default kitchen tap flow (L/min)")
                source = "assumption"
            kitchen_components.append((dish_minutes * (flow or 0), source))
    elif dish_mode in {"basin", "other"}:
        volume = _optional_number(answers.get("dishwashing_litres_per_day"))
        if volume is None:
            kitchen_incomplete = True
        else:
            kitchen_components.append((volume, "user"))
    else:
        kitchen_incomplete = True

    for litres, source in kitchen_components:
        add(kitchen_category, litres, source)
    if kitchen_incomplete and kitchen_components:
        incomplete_categories.add(kitchen_category)

    # 5. Laundry: machine default is configurable; hand washing requires a supplied volume.
    loads = _optional_number(answers.get("laundry_loads_per_week"))
    laundry_method = answers.get("laundry_method")
    if loads is not None:
        if loads == 0:
            add("Laundry", 0)
        elif laundry_method in {"front_load", "top_load", "other_machine"}:
            per_load = _optional_number(answers.get("laundry_litres_per_load"))
            source = "user"
            if per_load is None:
                per_load = assumed("machine_laundry_l_per_load", "Default washing-machine use (L/load)")
                source = "assumption"
            add("Laundry", loads * per_load / DAYS_IN_WEEK, source)
        elif laundry_method == "hand_wash":
            per_load = _optional_number(answers.get("handwash_litres_per_load"))
            source = "user"
            if per_load is None:
                buckets = _optional_number(answers.get("handwash_buckets_per_load"))
                if buckets is not None:
                    capacity = _optional_number(answers.get("handwash_bucket_capacity_litres"))
                    if capacity is None and buckets > 0:
                        capacity = assumed("bucket_capacity_l", "Default laundry bucket capacity (L)")
                        source = "assumption"
                    per_load = buckets * (capacity or 0)
            if per_load is not None:
                add("Laundry", loads * per_load / DAYS_IN_WEEK, source)

    # 6. Cleaning: hoses use flow × duration; other methods need a session volume.
    cleaning_frequency = _optional_number(answers.get("cleaning_sessions_per_week"))
    cleaning_method = answers.get("cleaning_method")
    if cleaning_frequency is not None:
        if cleaning_frequency == 0:
            add("Household cleaning", 0)
        elif cleaning_method == "hose":
            minutes = _optional_number(answers.get("cleaning_minutes_per_session"))
            if minutes is not None:
                flow = _optional_number(answers.get("cleaning_flow_rate_lpm"))
                source = "user"
                if flow is None:
                    flow = assumed("hose_flow_lpm", "Default hose flow (L/min)")
                    source = "assumption"
                add("Household cleaning", cleaning_frequency * minutes * flow / DAYS_IN_WEEK, source)
        else:
            volume = _optional_number(answers.get("cleaning_litres_per_session"))
            if volume is not None:
                add("Household cleaning", cleaning_frequency * volume / DAYS_IN_WEEK)

    # 7. Outdoor watering: can volumes are user-entered; timed methods use a disclosed flow default.
    has_garden = answers.get("has_garden")
    garden_frequency = _optional_number(answers.get("garden_sessions_per_week"))
    garden_method = answers.get("garden_method")
    if has_garden is False:
        add("Outdoor watering", 0)
    elif has_garden is True and garden_frequency is not None:
        if garden_frequency == 0:
            add("Outdoor watering", 0)
        elif garden_method == "watering_can":
            volume = _optional_number(answers.get("garden_litres_per_session"))
            if volume is not None:
                add("Outdoor watering", garden_frequency * volume / DAYS_IN_WEEK)
        elif garden_method in {"hose", "sprinkler", "drip"}:
            minutes = _optional_number(answers.get("garden_minutes_per_session"))
            if minutes is not None:
                flow = _optional_number(answers.get("garden_flow_rate_lpm"))
                source = "user"
                if flow is None:
                    key = {"hose": "hose_flow_lpm", "sprinkler": "sprinkler_flow_lpm", "drip": "drip_flow_lpm"}[garden_method]
                    flow = assumed(key, f"Default {garden_method} flow (L/min)")
                    source = "assumption"
                add("Outdoor watering", garden_frequency * minutes * flow / DAYS_IN_WEEK, source)

    daily, breakdown = _build_breakdown(category_values)
    category_order = ["Bathing & showers", "Toilet flushing", "Bathroom taps", "Kitchen & dishwashing", "Laundry", "Household cleaning", "Outdoor watering"]
    unavailable = [name for name in category_order if name not in category_values]
    user_categories = sum(source in {"user", "mixed"} for source in category_sources.values())
    assumed_categories = sum(source in {"assumption", "mixed"} for source in category_sources.values())
    mixed_categories = sum(source == "mixed" for source in category_sources.values())
    user_input_litres = source_litres["user"]
    assumption_litres = source_litres["assumption"]
    result = _result(daily, breakdown)
    result.update({
        "daily_per_person": round(daily / size, 2),
        "estimate_kind": "rough" if unavailable or incomplete_categories or assumptions else "input_based estimate",
        "category_count": len(category_values),
        "category_total": len(category_order),
        "unavailable_categories": unavailable,
        "incomplete_categories": sorted(incomplete_categories),
        "user_input_categories": user_categories,
        "assumption_categories": assumed_categories,
        "mixed_categories": mixed_categories,
        "user_input_litres_per_day": round(user_input_litres, 2),
        "assumption_litres_per_day": round(assumption_litres, 2),
        "category_sources": category_sources,
        "assumptions": assumptions,
        "assumption_disclaimer": "Defaults are configurable product estimates. Actual use depends on fixtures, behavior, and local conditions; a meter or measured flow rate improves accuracy.",
        "calculation_version": 2,
    })
    return result


# ---------------------------------------------------------------------------
# Farmer / Agricultural calculation
# ---------------------------------------------------------------------------

def calculate_farmer_consumption(data: dict) -> dict:
    """
    Estimate a farm's daily water consumption for irrigation.

    Parameters
    ----------
    data : dict
        Validated farmer assessment data.

        Field                       Unit
        -----------------------     ---------------
        farm_area                   float (numeric)
        farm_area_unit              'acre' or 'hectare'
        irrigation_method           flood / drip / sprinkler / other
        irrigation_frequency        sessions per week
        irrigation_duration_minutes minutes per session
        estimated_irrigation_litres litres per session (user-provided override)
        rainwater_harvesting        bool — contextual only; no volume supplied

    Strategy
    --------
    Priority 1 — User-provided estimate:
        If `estimated_irrigation_litres > 0`, use that value directly as the
        litres per irrigation session.  This is the most accurate because it
        comes from the farmer's own observation.

    Priority 2 — Model estimate from area + method + duration:
        If no user estimate is provided, calculate:
            litres_per_session = area_ha × (duration_h) × rate_L_ha_h
        where `rate_L_ha_h` depends on the irrigation method (see constants.py).

    Rainwater harvesting:
        The yes/no flag is recorded as context only. It does not quantify the
        share of irrigation supplied by rainwater, so it cannot safely reduce
        the consumption estimate.

    Notes
    -----
    - Irrigation sessions are per week; divide by 7 for daily equivalent.
    - If frequency or duration is 0, the calculated result will be 0 L/day.
    """
    farm_area           = _safe_float(data.get("farm_area"))
    farm_area_unit      = (data.get("farm_area_unit") or "acre").strip().lower()
    irrigation_method   = (data.get("irrigation_method") or "other").strip().lower()
    freq_per_week       = _safe_float(data.get("irrigation_frequency"))
    duration_minutes    = _safe_float(data.get("irrigation_duration_minutes"))
    user_estimate_L     = _safe_float(data.get("estimated_irrigation_litres"))
    rainwater_harvesting = bool(data.get("rainwater_harvesting", False))

    # Convert area to hectares
    if farm_area_unit == "acre":
        area_ha = farm_area * ACRES_TO_HECTARES
    else:
        area_ha = farm_area  # already in hectares

    # Determine litres per irrigation session
    if user_estimate_L > 0:
        # Priority 1: use the farmer's own estimate
        litres_per_session = user_estimate_L
        source_note = "user-provided estimate"
    else:
        # Priority 2: model from area × duration × method rate
        duration_hours = duration_minutes / 60.0
        rate = IRRIGATION_RATE_L_PER_HA_PER_HOUR.get(irrigation_method, IRRIGATION_RATE_DEFAULT)
        litres_per_session = area_ha * duration_hours * rate
        source_note = f"estimated from area={farm_area} {farm_area_unit}, method={irrigation_method}"

    # Daily irrigation equivalent (sessions per week ÷ 7)
    irrigation_litres_per_day = (litres_per_session * freq_per_week) / DAYS_IN_WEEK

    category_litres = {
        "Irrigation": max(0.0, irrigation_litres_per_day),
    }

    daily, breakdown = _build_breakdown(category_litres)

    result = _result(daily, breakdown)
    result["calculation_note"] = f"Irrigation estimate based on {source_note}."
    if rainwater_harvesting:
        result["calculation_note"] += " Rainwater harvesting was reported, but no volume credit was applied because the supplied share is unknown."
    return result
