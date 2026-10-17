"""
AquaWise AI Service Layer.

Acts as an abstraction layer between AquaWise and external Large Language Model
APIs (Google Gemini).

Architecture Principles
-----------------------
1. AI is an ENHANCEMENT, NOT the source of truth for numerical calculations:
   - Water consumption numbers and breakdowns are calculated deterministically
     by `backend/services/calculation_service.py`.
   - The AI service personalizes wording, structures conversational advice, and
     contextualizes recommendations. It NEVER invents or alters consumption figures.
2. Graceful Offline Fallback:
   - If `AI_API_KEY` or `GEMINI_API_KEY` is absent, or if an API call fails / times out,
     the service falls back seamlessly to deterministic rule-based recommendations
     and structured educational answers.
   - The application never crashes due to AI unavailability.
3. Security & Privacy:
   - Credentials are read exclusively from environment variables or Flask configuration.
   - API keys are never exposed in responses, client payloads, or logs.
   - Assessment data sent to the AI contains only non-sensitive water usage parameters.
"""

import os
import json
import logging
import requests
from typing import Any

from backend.utils.constants import (
    SHOWER_FLOW_RATE_LPM,
    LAUNDRY_WATER_PER_LOAD_L,
    KITCHEN_TAP_FLOW_RATE_LPM,
    VEHICLE_WASH_HOSE_L,
    VEHICLE_WASH_BUCKET_L,
    HOUSEHOLD_ASSESSMENT_DEFAULTS,
)

logger = logging.getLogger(__name__)

# Standard disclaimers
CALCULATION_DISCLAIMER = (
    "AquaWise provides estimated water consumption based on user inputs "
    "and typical usage benchmarks. Actual consumption may vary."
)
FARMING_DISCLAIMER = (
    "Agricultural suggestions are general water conservation benchmarks. "
    "Consult local agronomic extension services for crop-specific guidance."
)


# ---------------------------------------------------------------------------
# Configuration & Credentials Helper
# ---------------------------------------------------------------------------

def _get_api_key(override_key: str | None = None) -> str:
    """Retrieve API key from argument, Flask config, or environment variables."""
    if override_key:
        return override_key.strip()
    try:
        from flask import current_app, has_app_context
        if has_app_context():
            key = current_app.config.get("AI_API_KEY") or current_app.config.get("GEMINI_API_KEY")
            if key:
                return str(key).strip()
    except ImportError:
        pass
    return (os.environ.get("AI_API_KEY") or os.environ.get("GEMINI_API_KEY") or "").strip()


def _get_model_name(override_model: str | None = None) -> str:
    """Retrieve model name from argument, Flask config, or environment variables."""
    if override_model:
        return override_model.strip()
    try:
        from flask import current_app, has_app_context
        if has_app_context():
            model = current_app.config.get("AI_MODEL")
            if model:
                return str(model).strip()
    except ImportError:
        pass
    return os.environ.get("AI_MODEL", "gemini-2.5-flash").strip()


def is_ai_available(api_key: str | None = None) -> bool:
    """Check if AI capabilities are configured with a valid non-empty key."""
    return bool(_get_api_key(api_key))


def get_ai_status() -> dict[str, Any]:
    """Return public status of the AI service (without leaking secrets)."""
    available = is_ai_available()
    return {
        "available": available,
        "provider": "google-gemini",
        "model": _get_model_name(),
        "mode": "online" if available else "offline_fallback",
    }


# ---------------------------------------------------------------------------
# External Gemini API Communicator
# ---------------------------------------------------------------------------

def _call_gemini_api(
    prompt: str,
    system_instruction: str | None = None,
    api_key: str | None = None,
    model: str | None = None,
    timeout: int = 10,
) -> str | None:
    """
    Call the Google Gemini REST API using standard HTTP requests.

    Returns the response text on success, or None on failure/timeout.
    Never raises an uncaught exception or leaks credentials.
    """
    key = _get_api_key(api_key)
    if not key:
        return None

    model_name = _get_model_name(model)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={key}"
    headers = {"Content-Type": "application/json"}

    payload: dict[str, Any] = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 1024,
        },
    }

    if system_instruction:
        payload["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if response.status_code != 200:
            logger.warning(
                "Gemini API returned non-200 status code: %s", response.status_code
            )
            return None

        data = response.json()
        candidates = data.get("candidates", [])
        if not candidates:
            return None

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])
        if not parts:
            return None

        return parts[0].get("text", "").strip()

    except requests.Timeout:
        logger.warning("Gemini API call timed out after %s seconds.", timeout)
        return None
    except requests.RequestException as e:
        logger.warning("Gemini API request failed: %s", type(e).__name__)
        return None
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        logger.warning("Failed to parse Gemini API response: %s", type(e).__name__)
        return None
    except Exception as e:
        logger.warning("Unexpected error during Gemini API call: %s", type(e).__name__)
        return None


# ---------------------------------------------------------------------------
# Deterministic Fallback Recommendation Generator
# ---------------------------------------------------------------------------

def get_fallback_recommendations(
    assessment_data: dict[str, Any],
    calculation_results: dict[str, Any],
    user_type: str = "household",
) -> list[dict[str, Any]]:
    """
    Generate deterministic, rule-based recommendations.

    Evaluates user input and calculation breakdown against standard benchmarks.
    Guaranteed to return structured recommendations with realistic potential savings.
    """
    recommendations: list[dict[str, Any]] = []
    user_type_norm = (user_type or "household").lower()

    breakdown_map = {
        item.get("category", ""): item.get("litres_per_day", 0.0)
        for item in calculation_results.get("breakdown", [])
    }
    daily_total = float(calculation_results.get("daily_consumption", 0.0))

    if user_type_norm == "household" and (assessment_data.get("assessment_version") == 2 or assessment_data.get("extended_answers")):
        return _get_household_assessment_v2_recommendations(assessment_data, calculation_results, breakdown_map)

    if user_type_norm == "household":
        size = max(1, int(float(assessment_data.get("household_size", 1))))
        showers_per_day = float(assessment_data.get("showers_per_day", 0.0))
        shower_duration = float(assessment_data.get("shower_duration_minutes", 0.0))
        toilet_uses = float(assessment_data.get("toilet_uses_per_day", 0.0))
        kitchen_minutes = float(assessment_data.get("kitchen_usage_minutes", 0.0))
        laundry_loads = float(assessment_data.get("laundry_loads_per_week", 0.0))
        vehicle_freq = float(assessment_data.get("vehicle_washing_frequency", 0.0))
        gardening_freq = float(assessment_data.get("gardening_frequency", 0.0))

        # 1. Shower / Bathing recommendation
        if showers_per_day > 0 and shower_duration > 5:
            excess_minutes = max(2.0, shower_duration - 5.0)
            potential = round(size * showers_per_day * excess_minutes * SHOWER_FLOW_RATE_LPM * 0.7, 1)
            bathing_share = (breakdown_map.get("Bathing", 0.0) / daily_total * 100) if daily_total > 0 else 0
            recommendations.append({
                "category": "Bathing",
                "title": "Shorten Showers & Install Low-Flow Aerators",
                "description": (
                    f"Reducing average shower duration from {int(shower_duration)} to 5 minutes "
                    f"and fitting aerators can save significant water for your {size}-person household."
                ),
                "priority": "high" if bathing_share > 30 else "medium",
                "source": "rule_based",
                "potential_saving": max(10.0, potential),
            })

        # 2. Toilet flushing recommendation
        if toilet_uses >= 3:
            potential = round(size * toilet_uses * 2.5, 1)
            recommendations.append({
                "category": "Toilet",
                "title": "Switch to Dual-Flush or Install Cistern Bags",
                "description": (
                    "Standard single flushes use ~6 litres per flush. Installing dual-flush mechanisms "
                    "or water displacement bags in the cistern saves 2–3 litres on every flush."
                ),
                "priority": "high" if toilet_uses >= 5 else "medium",
                "source": "rule_based",
                "potential_saving": max(8.0, potential),
            })

        # 3. Kitchen tap recommendation
        if kitchen_minutes >= 15:
            potential = round(kitchen_minutes * 0.3 * KITCHEN_TAP_FLOW_RATE_LPM, 1)
            recommendations.append({
                "category": "Kitchen",
                "title": "Use a Wash Basin & Avoid Running Tap While Cleaning",
                "description": (
                    "Washing dishes and produce in a filled basin rather than under a running tap "
                    "reduces kitchen water consumption by up to 30%."
                ),
                "priority": "medium",
                "source": "rule_based",
                "potential_saving": max(5.0, potential),
            })

        # 4. Vehicle washing recommendation
        if vehicle_freq > 0:
            potential = round((VEHICLE_WASH_HOSE_L - VEHICLE_WASH_BUCKET_L) * vehicle_freq / 7.0, 1)
            recommendations.append({
                "category": "Vehicle Washing",
                "title": "Use Bucket & Sponge Instead of Running Hose",
                "description": (
                    "A running garden hose can discharge over 150 litres per vehicle wash. "
                    "Switching to two 15-litre buckets saves up to 120 litres per wash."
                ),
                "priority": "high" if vehicle_freq >= 2 else "medium",
                "source": "rule_based",
                "potential_saving": max(15.0, potential),
            })

        # 5. Gardening recommendation
        if gardening_freq > 0:
            gardening_daily = breakdown_map.get("Gardening", 20.0)
            potential = round(gardening_daily * 0.3, 1)
            recommendations.append({
                "category": "Gardening",
                "title": "Water Plants at Dawn/Dusk and Apply Mulch",
                "description": (
                    "Irrigate garden plants early in the morning or in the evening to minimize "
                    "evaporative water loss. Layering organic mulch retains soil moisture longer."
                ),
                "priority": "medium",
                "source": "rule_based",
                "potential_saving": max(6.0, potential),
            })

        # 6. Laundry efficiency
        if laundry_loads >= 4:
            potential = round((1.0 * LAUNDRY_WATER_PER_LOAD_L) / 7.0, 1)
            recommendations.append({
                "category": "Laundry",
                "title": "Consolidate Laundry into Full Loads",
                "description": (
                    "Running only full washing machine cycles reduces weekly wash cycles and "
                    "saves both electricity and water."
                ),
                "priority": "low",
                "source": "rule_based",
                "potential_saving": max(8.0, potential),
            })

        # Baseline leak detection if fewer than 2 recommendations generated
        if len(recommendations) < 2:
            recommendations.append({
                "category": "General",
                "title": "Inspect Plumbing Fixtures for Silent Leaks",
                "description": (
                    "Check faucets, toilet flappers, and pipe joints. A single dripping tap can "
                    "waste 20 to 50 litres of clean water every day."
                ),
                "priority": "medium",
                "source": "rule_based",
                "potential_saving": 20.0,
            })

    else:
        # Farmer recommendations
        irrigation_method = str(assessment_data.get("irrigation_method", "flood")).lower()
        daily_irrigation = breakdown_map.get("Irrigation", daily_total)
        has_rainwater = bool(assessment_data.get("rainwater_harvesting", False))

        if irrigation_method == "flood":
            potential = round(daily_irrigation * 0.45, 1)
            recommendations.append({
                "category": "Irrigation",
                "title": "Transition from Flood to Drip or Micro-Irrigation",
                "description": (
                    "Flood irrigation loses 40% to 50% of water to deep percolation and evaporation. "
                    "Drip irrigation delivers water directly to root zones at over 90% application efficiency."
                ),
                "priority": "high",
                "source": "rule_based",
                "potential_saving": max(50.0, potential),
            })
        elif irrigation_method == "sprinkler":
            potential = round(daily_irrigation * 0.20, 1)
            recommendations.append({
                "category": "Irrigation",
                "title": "Upgrade Sprinkler Nozzles & Maintain Operating Pressure",
                "description": (
                    "Inspect sprinkler heads for nozzle wear and maintain optimal pressure to "
                    "prevent misting and wind drift losses."
                ),
                "priority": "medium",
                "source": "rule_based",
                "potential_saving": max(25.0, potential),
            })
        else:
            potential = round(daily_irrigation * 0.10, 1)
            recommendations.append({
                "category": "Irrigation",
                "title": "Maintain Drip Emitters & Flush Lateral Lines",
                "description": (
                    "Perform routine acid flushes and screen filter maintenance to prevent emitter "
                    "clogging and maintain uniform field discharge."
                ),
                "priority": "medium",
                "source": "rule_based",
                "potential_saving": max(15.0, potential),
            })

        # Irrigation scheduling & timing
        time_potential = round(daily_irrigation * 0.15, 1)
        recommendations.append({
            "category": "Irrigation",
            "title": "Shift Irrigation to Cooler Non-Peak Evaporation Hours",
            "description": (
                "Watering crops during early mornings (before 8 AM) or evenings reduces surface "
                "evaporation loss by up to 20%."
            ),
            "priority": "high" if daily_irrigation > 500 else "medium",
            "source": "rule_based",
            "potential_saving": max(30.0, time_potential),
        })

        # Rainwater harvesting for farms
        if not has_rainwater:
            harvest_potential = round(daily_irrigation * 0.10, 1)
            recommendations.append({
                "category": "Conservation",
                "title": "Construct On-Farm Rainwater Ponds or Catchment Trenches",
                "description": (
                    "Capturing monsoon runoff in farm ponds helps recharge the aquifer and provides "
                    "critical protective irrigation during dry spells."
                ),
                "priority": "medium",
                "source": "rule_based",
                "potential_saving": max(20.0, harvest_potential),
            })

        # Soil mulching
        mulch_potential = round(daily_irrigation * 0.15, 1)
        recommendations.append({
            "category": "Soil Management",
            "title": "Apply Crop Residue Mulch to Retain Root-Zone Moisture",
            "description": (
                "Organic mulching with crop stubble suppresses weeds, buffers soil temperature, and "
                "drastically curtails surface moisture loss."
            ),
            "priority": "medium",
            "source": "rule_based",
            "potential_saving": max(25.0, mulch_potential),
        })

    # Sort descending by potential saving
    recommendations.sort(key=lambda r: r["potential_saving"], reverse=True)
    return recommendations


def _get_household_assessment_v2_recommendations(assessment_data, calculation_results, breakdown_map):
    """Return recommendations only when the submitted answers support them."""
    answers = assessment_data.get("extended_answers") or {}
    measures = set(answers.get("conservation_measures") or [])
    recs = []

    def add(category, title, reason, action, trigger, priority="medium", effort="low", saving=None, assumptions=None):
        recs.append({
            "category": category,
            "title": title,
            "description": f"{reason} Action: {action}",
            "priority": priority,
            "source": "rule_based",
            "potential_saving": saving,
            "evidence": {
                "trigger": trigger,
                "effort": effort,
                "saving_basis": "illustrative scenario, not guaranteed" if saving is not None else None,
                "assumptions": assumptions or [],
            },
        })

    leak = answers.get("leak_status")
    if leak in {"minor", "significant", "unsure"}:
        fixture = answers.get("leak_fixture")
        urgency = "Reported fixture: " + fixture if fixture else "Reported leak status: " + leak
        add("Leaks", "Inspect and repair the reported leak", f"You reported {leak} leak concern" + (f" at {fixture}." if fixture else "."), "Check the fixture or arrange a plumbing inspection; no leakage volume is assumed.", urgency, "high" if leak in {"significant", "unsure"} else "medium", "moderate")

    duration = _optional_float(answers.get("shower_duration_minutes"))
    showers = _optional_float(answers.get("showers_per_person_per_day"))
    if answers.get("bathing_method") in {"shower", "both"} and duration is not None and showers and duration >= 8:
        size = max(1, int(float(assessment_data.get("household_size", 1))))
        flow = _optional_float(answers.get("shower_flow_rate_lpm"))
        assumptions = []
        saving = None
        if flow is None:
            flow = HOUSEHOLD_ASSESSMENT_DEFAULTS["shower_flow_lpm"]
            assumptions.append(f"Default flow {flow:g} L/min")
        reduction = min(duration, HOUSEHOLD_ASSESSMENT_DEFAULTS["shower_scenario_reduction_minutes"])
        saving = round(showers * reduction * flow * size, 1)
        add("Bathing & showers", "Try a one-minute shorter shower", f"Your reported shower duration is {duration:g} minutes, and showers contribute to the measured estimate.", "Try reducing shower time by one minute and compare the next assessment.", "shower_duration_minutes", "medium", "low", saving, assumptions + ["Scenario assumes a one-minute duration reduction for each reported daily shower."])
        if "low_flow_showerhead" not in measures:
            add("Bathing & showers", "Check the shower flow rate", "The shower flow rate is a key driver of the bathing estimate.", "Measure flow with a timed container before deciding whether a lower-flow fixture is suitable.", "bathing_method and shower use", "low", "moderate")

    if answers.get("tap_off_while_brushing") is False and "tap_aerators" not in measures:
        add("Bathroom taps", "Turn off the tap while brushing", "You reported that the tap usually runs during brushing.", "Turn the tap off during brushing and shaving, then compare your next estimate.", "tap_off_while_brushing", "medium", "low")

    if answers.get("toilet_type") == "standard" and "dual_flush_toilet" not in measures:
        add("Toilet flushing", "Check whether a dual-flush upgrade fits", "You reported a standard-flush toilet.", "Confirm the fixture's actual flush volume and compatibility before considering an upgrade.", "toilet_type", "low", "moderate")

    dish_method = answers.get("dishwashing_method")
    if answers.get("has_dishwasher") is not True and (dish_method == "running_water" or answers.get("kitchen_tap_runs_while_washing") is True):
        add("Kitchen & dishwashing", "Use a filled basin for dishwashing", "Your answers indicate that water runs while dishes are washed.", "Wash in a filled sink or basin where practical; kitchen preparation water is accounted for separately.", "dishwashing_method", "medium", "low")

    if answers.get("laundry_full_loads") is False and (answers.get("laundry_loads_per_week") or 0) > 0:
        add("Laundry", "Combine partial laundry loads", "You reported that laundry is often washed in partial loads.", "Group compatible items into a full load and use the machine's appropriate water setting.", "laundry_full_loads", "low", "low")

    if answers.get("has_garden") is True and answers.get("garden_method") in {"hose", "sprinkler"}:
        if "efficient_irrigation" not in measures:
            add("Outdoor watering", "Review how the garden is watered", f"Your reported method is {answers.get('garden_method')}.", "Water when evaporation is lower and consider targeted watering only where it suits the plants and site.", "garden_method", "low", "low")

    if not recs:
        return []
    priority_rank = {"high": 0, "medium": 1, "low": 2}
    recs.sort(key=lambda item: (priority_rank[item["priority"]], -(item["potential_saving"] or 0)))
    return recs


def _optional_float(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# AI Recommendation Enhancement
# ---------------------------------------------------------------------------

def enhance_recommendations(
    assessment_data: dict[str, Any],
    calculation_results: dict[str, Any],
    user_type: str = "household",
    api_key: str | None = None,
) -> list[dict[str, Any]]:
    """
    Enhance recommendations with personalized language via Gemini AI.

    Key Safety Constraints:
    - Base numerical potential savings and priorities are strictly determined
      by the deterministic rule engine.
    - AI is only asked to rephrase, personalize, and contextualize titles and descriptions.
    - If the AI call fails or is unavailable, the deterministic base recommendations
      are returned immediately with source='rule_based'.
    """
    base_recs = get_fallback_recommendations(assessment_data, calculation_results, user_type)
    if not is_ai_available(api_key):
        return base_recs

    # Format structured context for the AI prompt
    user_type_str = (user_type or "household").capitalize()
    daily_litres = calculation_results.get("daily_consumption", 0.0)
    breakdown_str = ", ".join(
        f"{b.get('category')}: {b.get('litres_per_day')} L/day ({b.get('percentage')}%)"
        for b in calculation_results.get("breakdown", [])
    )

    base_items_json = json.dumps([
        {
            "category": r["category"],
            "title": r["title"],
            "description": r["description"],
            "priority": r["priority"],
            "potential_saving": r["potential_saving"],
        }
        for r in base_recs
    ], indent=2)

    prompt = f"""
You are the AquaWise Water Conservation Expert.
Enhance and personalize the following water conservation recommendations for a {user_type_str} user.

User Context:
- User Type: {user_type_str}
- Estimated Daily Water Consumption: {daily_litres} Litres/day
- Activity Breakdown: {breakdown_str}

Pre-calculated Base Recommendations:
{base_items_json}

Instructions:
1. Provide engaging, friendly, and practical personalized titles and descriptions for each recommendation.
2. STRICT REQUIREMENT: Keep the EXACT same category, priority, and potential_saving values for each recommendation. Do NOT change, calculate, or alter any numbers.
3. Keep descriptions under 40 words each, focusing on clear, actionable advice.
4. Return ONLY a valid JSON array of objects with keys: "category", "title", "description", "priority", "potential_saving". No markdown, no commentary outside the JSON.
"""

    system_instruction = (
        "You are AquaWise AI, a specialized water conservation assistant. "
        "You enhance recommendation wording without modifying numerical facts."
    )

    response_text = _call_gemini_api(prompt, system_instruction=system_instruction, api_key=api_key)
    if not response_text:
        return base_recs

    # Attempt to parse AI JSON response
    try:
        clean_text = response_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        enhanced_items = json.loads(clean_text)
        if isinstance(enhanced_items, list) and len(enhanced_items) > 0:
            merged_recs: list[dict[str, Any]] = []
            for i, base in enumerate(base_recs):
                enhanced = enhanced_items[i] if i < len(enhanced_items) else {}
                merged_recs.append({
                    "category": base["category"],
                    "title": str(enhanced.get("title") or base["title"]).strip(),
                    "description": str(enhanced.get("description") or base["description"]).strip(),
                    "priority": base["priority"],
                    "source": "hybrid",
                    "potential_saving": base["potential_saving"],  # Preserved from deterministic logic
                })
            return merged_recs
    except Exception as e:
        logger.warning("Failed to parse enhanced recommendations JSON from AI: %s", type(e).__name__)

    return base_recs


# ---------------------------------------------------------------------------
# Conversational AI Assistant & Offline Chat Fallback
# ---------------------------------------------------------------------------

def _get_fallback_chat_response(user_message: str, user_context: dict[str, Any] | None = None) -> str:
    """
    Intelligent keyword-driven response engine for offline chat.

    Provides rich, contextual, educational water conservation advice
    when the AI service is not available.
    """
    msg = user_message.lower().strip()
    context_prefix = ""

    if user_context:
        u_type = user_context.get("user_type", "user")
        daily = user_context.get("daily_consumption")
        top_cat = user_context.get("top_category")
        if daily and top_cat:
            context_prefix = (
                f"*(Note: In your recent {u_type} assessment, your estimated usage was "
                f"{daily} L/day with '{top_cat}' as your highest activity.)*\n\n"
            )

    # 1. Shower and bathing
    if any(k in msg for k in ["shower", "bath", "bathing", "bucket", "shampoo"]):
        return context_prefix + (
            "**Shower & Bathing Conservation Tips:**\n\n"
            "• **Keep showers under 5 minutes:** Every extra minute in a standard shower discharges 9–12 litres.\n"
            "• **Install aerating showerheads:** Low-flow aerators reduce water flow by 30–50% while maintaining spray pressure.\n"
            "• **Consider bucket baths:** Traditional bucket baths use 15–20 litres, compared to 60–90 litres for an average 8-minute shower.\n"
            "• **Turn off while soaping:** Shut the tap while applying shampoo or soap."
        )

    # 2. Toilet flushing and leaks
    if any(k in msg for k in ["toilet", "flush", "cistern", "commode"]):
        return context_prefix + (
            "**Toilet Water Conservation Tips:**\n\n"
            "• **Upgrade to Dual-Flush:** Dual-flush systems offer a 3L half-flush for liquids and 6L for solids.\n"
            "• **Use a Cistern Displacement Bag:** Placing a sealed water bottle or displacement bag into an older single-flush tank saves 1–2 litres per flush.\n"
            "• **Check for Silent Flapper Leaks:** Place 3 drops of food coloring into your toilet tank. If color appears in the bowl after 15 minutes without flushing, your flapper valve needs replacement."
        )

    # 3. Kitchen and dishwashing
    if any(k in msg for k in ["kitchen", "dish", "dishes", "sink", "cooking", "plate"]):
        return context_prefix + (
            "**Kitchen Water Conservation Tips:**\n\n"
            "• **Two-Basin Method:** Soak and scrub dishes in one basin or container, and rinse in a second, rather than letting the tap run.\n"
            "• **Install Tap Aerators:** Screw-on aerators mix air with water to reduce tap flow from 8 L/min to under 5 L/min.\n"
            "• **Scrape, Don't Pre-Rinse:** Scrape leftover food into composting bins instead of rinsing under running water."
        )

    # 4. Laundry and washing machine
    if any(k in msg for k in ["laundry", "clothes", "washing machine", "rinse", "fabric"]):
        return context_prefix + (
            "**Laundry Water Conservation Tips:**\n\n"
            "• **Always Run Full Loads:** Washing machines consume nearly the same water regardless of load size. Wait for a full batch.\n"
            "• **Reuse Final Rinse Water:** Drain greywater from gentle rinse cycles to mop floors or wash driveways.\n"
            "• **Front-Loaders Save Water:** When replacing a machine, note that front-loaders typically use 40–50% less water than top-loaders."
        )

    # 5. Vehicle washing
    if any(k in msg for k in ["car", "vehicle", "bike", "scooter", "motorcycle", "auto"]):
        return context_prefix + (
            "**Vehicle Cleaning Water Tips:**\n\n"
            "• **Bucket vs. Hose:** A running garden hose uses 150–200 litres per wash. A bucket and sponge uses only 25–35 litres.\n"
            "• **Waterless Wash Sprays:** For light dust, use eco-friendly waterless car wash sprays and microfiber towels.\n"
            "• **Wash on Grass:** If washing at home, park on your lawn so the wash water waters your grass rather than running into the storm drain."
        )

    # 6. Gardening and lawn care
    if any(k in msg for k in ["garden", "lawn", "plant", "flower", "grass", "tree", "landscap"]):
        return context_prefix + (
            "**Gardening & Lawn Water Conservation:**\n\n"
            "• **Water Early or Late:** Water before 8 AM or after 6 PM to prevent up to 30% of water from evaporating in the sun.\n"
            "• **Organic Mulching:** Place 2–3 inches of bark, straw, or leaves around plants to keep root soil moist and cool.\n"
            "• **Target the Roots:** Always water at soil level around the roots rather than spraying foliage overhead."
        )

    # 7. Agricultural / Farm irrigation
    if any(k in msg for k in ["irrigation", "drip", "sprinkler", "flood", "farm", "crop", "paddy", "wheat", "acre", "hectare"]):
        return context_prefix + (
            "**Agricultural Irrigation Guidance:**\n\n"
            "• **Drip Irrigation Efficiency:** Drip systems deliver water directly to crop roots with 90%+ efficiency, saving 40–60% compared to flood irrigation.\n"
            "• **Irrigation Scheduling:** Irrigate during night or early dawn to minimize wind drift and evapotranspiration.\n"
            "• **Soil Moisture Monitoring:** Use tensiometers or simple feel tests before irrigating to avoid overwatering.\n\n"
            f"> *{FARMING_DISCLAIMER}*"
        )

    # 8. Rainwater harvesting
    if any(k in msg for k in ["rain", "rainwater", "harvest", "rooftop", "catchment", "storage"]):
        return context_prefix + (
            "**Rainwater Harvesting Basics:**\n\n"
            "• **Rooftop Catchment:** Every 100 sq. meters of rooftop collects ~80,000 litres of water annually in regions with 800 mm rainfall.\n"
            "• **First-Flush Diverter:** Ensure your system diverts the first 15–20 minutes of rain to flush dust and debris away from storage tanks.\n"
            "• **Groundwater Recharge:** Excess rainwater directed into recharge pits restores local borewell levels."
        )

    # 9. Leaks and detection
    if any(k in msg for k in ["leak", "meter", "drip", "pipe", "burst"]):
        return context_prefix + (
            "**How to Detect Household Water Leaks:**\n\n"
            "1. **The 2-Hour Meter Test:** Turn off all taps and water-consuming appliances for 2 hours. If the water meter dial moves, you have a leak.\n"
            "2. **Toilet Leak Test:** Put food coloring in your toilet tank. Wait 15 minutes. If color seeps into the bowl, replace the flapper valve.\n"
            "3. **Check Pipe Joints:** Inspect under sinks and around washing machine hoses for dampness or lime scale buildup."
        )

    # 10. Water Saver Score / AquaWise
    if any(k in msg for k in ["score", "saver score", "aquawise", "how it works", "calculation", "benchmark"]):
        return context_prefix + (
            "**About AquaWise & Water Saver Score:**\n\n"
            "• **Water Saver Score (0–100):** Benchmarks your water efficiency based on daily per-capita usage against CPHEEO urban guidelines (150 L/capita/day) and sustainable farming standards.\n"
            "• **Deterministic Calculations:** All consumption figures are calculated by backend math formulas, not generative AI.\n"
            "• **Track Over Time:** Take recurring assessments to increase your streak and earn conservation achievements!"
        )

    # 11. Greetings
    if any(k in msg for k in ["hello", "hi", "hey", "greetings", "good morning", "good evening"]):
        return context_prefix + (
            "Hello! I am your AquaWise Water Conservation Assistant.\n\n"
            "I can help you understand your water consumption assessment, find practical ways "
            "to reduce household or farm water usage, detect leaks, and learn about efficient irrigation. "
            "What water-saving topic would you like to explore?"
        )

    # General fallback response
    return context_prefix + (
        "**AquaWise Water Conservation Advisor:**\n\n"
        "Water conservation starts with small, consistent daily habits:\n"
        "• **In Bathrooms:** Keep showers short (under 5 mins) and repair dripping taps promptly.\n"
        "• **In Kitchens & Laundry:** Wash full loads and turn taps off when scrubbing dishes or produce.\n"
        "• **Outdoors & Farms:** Water early in the morning and consider drip irrigation or soil mulching.\n\n"
        "Ask me about specific areas like **showers, toilets, gardens, drip irrigation, or leak detection** for detailed tips!"
    )


def chat_with_assistant(
    user_message: str,
    conversation_history: list[dict[str, str]] | None = None,
    user_context: dict[str, Any] | None = None,
    api_key: str | None = None,
) -> dict[str, Any]:
    """
    Handle a conversational user message with the AquaWise Assistant.

    Returns:
        {
            "response": str,
            "source": "ai" | "fallback",
            "success": bool,
            "disclaimer": str,
        }
    """
    cleaned_msg = (user_message or "").strip()
    if not cleaned_msg:
        return {
            "response": "Please enter a question or topic about water conservation.",
            "source": "fallback",
            "success": False,
            "disclaimer": CALCULATION_DISCLAIMER,
        }

    # Offline mode if no key configured
    if not is_ai_available(api_key):
        fallback_text = _get_fallback_chat_response(cleaned_msg, user_context)
        return {
            "response": fallback_text,
            "source": "fallback",
            "success": True,
            "disclaimer": CALCULATION_DISCLAIMER,
        }

    # Build prompt with persona, user context, and conversation history
    context_lines = []
    if user_context:
        context_lines.append(f"User Type: {user_context.get('user_type', 'household')}")
        if user_context.get("daily_consumption"):
            context_lines.append(f"Estimated Daily Usage: {user_context.get('daily_consumption')} L/day")
        if user_context.get("top_category"):
            context_lines.append(f"Largest Consumption Category: {user_context.get('top_category')}")
        if user_context.get("water_saver_score"):
            context_lines.append(f"Water Saver Score: {user_context.get('water_saver_score')}/100")

    context_str = "\n".join(context_lines) if context_lines else "None provided."

    history_lines = []
    if conversation_history:
        for turn in conversation_history[-4:]:  # Include last 4 turns for context
            role = "User" if turn.get("role") == "user" else "Assistant"
            history_lines.append(f"{role}: {turn.get('message', '')}")
    history_str = "\n".join(history_lines) if history_lines else "None."

    prompt = f"""
User Assessment Context:
{context_str}

Recent Conversation History:
{history_str}

User Question:
{cleaned_msg}

Answer the user's question with practical, accurate, and encouraging water conservation advice.
"""

    system_instruction = (
        "You are AquaWise Assistant, a polite, encouraging, and knowledgeable water conservation expert. "
        "Guidelines:\n"
        "1. Focus on practical water-saving tips and explain consumption patterns clearly.\n"
        "2. Keep responses concise (under 200 words) using clean markdown formatting and bullet points.\n"
        "3. Never claim that estimated numbers are exact physical meter readings.\n"
        "4. For farming/crop irrigation queries, include a reminder that local soil and climate vary.\n"
        "5. Never provide unsafe advice regarding drinking water sanitation."
    )

    ai_reply = _call_gemini_api(prompt, system_instruction=system_instruction, api_key=api_key)
    if ai_reply:
        return {
            "response": ai_reply,
            "source": "ai",
            "success": True,
            "disclaimer": CALCULATION_DISCLAIMER,
        }

    # Graceful fallback if Gemini API call failed or timed out
    fallback_text = _get_fallback_chat_response(cleaned_msg, user_context)
    return {
        "response": fallback_text,
        "source": "fallback",
        "success": True,
        "disclaimer": CALCULATION_DISCLAIMER,
    }
