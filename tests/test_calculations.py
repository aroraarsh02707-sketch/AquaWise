"""
Tests for backend/services/calculation_service.py and backend/utils/validators.py.

All tests are independent of the database and of any AI service.
Floating-point results are tested with a tolerance of ±0.5 L to accommodate
rounding in the calculation engine.
"""

import pytest
from backend.services.calculation_service import (
    calculate_household_consumption,
    calculate_farmer_consumption,
)
from backend.utils.validators import (
    validate_registration,
    validate_login,
    validate_household_assessment,
    validate_farmer_assessment,
    validate_assessment,
)
from backend.utils import constants as C


# ===========================================================================
# Fixtures — minimal valid payloads
# ===========================================================================

@pytest.fixture
def minimal_household():
    """Smallest valid household payload (all optional fields omitted)."""
    return {
        "household_size": 1,
        "showers_per_day": 1,
        "shower_duration_minutes": 5,
        "toilet_uses_per_day": 4,
        "laundry_loads_per_week": 2,
        "kitchen_usage_minutes": 15,
        # Optional fields omitted → default to 0
    }


@pytest.fixture
def full_household():
    """Full household payload (4-person home with all activities)."""
    return {
        "household_size": 4,
        "showers_per_day": 2,
        "shower_duration_minutes": 8,
        "toilet_uses_per_day": 5,
        "laundry_loads_per_week": 5,
        "kitchen_usage_minutes": 30,
        "vehicle_washing_frequency": 1,      # once a week
        "gardening_frequency": 3,            # 3 sessions a week
        "gardening_duration_minutes": 20,
        "other_usage_litres": 15,
    }


@pytest.fixture
def minimal_farmer():
    """Smallest valid farmer payload using a user-provided estimate."""
    return {
        "farm_area": 2.0,
        "farm_area_unit": "acre",
        "crop_type": "wheat",
        "irrigation_method": "drip",
        "irrigation_frequency": 3,           # 3 sessions/week
        "irrigation_duration_minutes": 60,
        "water_source": "groundwater",
        "estimated_irrigation_litres": 2000, # user-provided: 2000 L per session
        "rainwater_harvesting": False,
    }


# ===========================================================================
# Calculation tests — Household
# ===========================================================================

class TestHouseholdCalculation:

    def test_returns_required_keys(self, minimal_household):
        result = calculate_household_consumption(minimal_household)
        assert "daily_consumption" in result
        assert "weekly_consumption" in result
        assert "monthly_consumption" in result
        assert "breakdown" in result

    def test_weekly_is_seven_times_daily(self, full_household):
        result = calculate_household_consumption(full_household)
        expected_weekly = round(result["daily_consumption"] * 7, 2)
        assert result["weekly_consumption"] == expected_weekly

    def test_monthly_is_thirty_times_daily(self, full_household):
        result = calculate_household_consumption(full_household)
        expected_monthly = round(result["daily_consumption"] * 30, 2)
        assert result["monthly_consumption"] == expected_monthly

    def test_breakdown_percentages_sum_to_100(self, full_household):
        result = calculate_household_consumption(full_household)
        total_pct = sum(b["percentage"] for b in result["breakdown"])
        assert abs(total_pct - 100.0) < 0.5, f"Percentages sum to {total_pct}, expected ~100"

    def test_breakdown_litres_sum_equals_daily(self, full_household):
        result = calculate_household_consumption(full_household)
        breakdown_total = sum(b["litres_per_day"] for b in result["breakdown"])
        assert abs(breakdown_total - result["daily_consumption"]) < 0.5

    def test_breakdown_contains_expected_categories(self, full_household):
        result = calculate_household_consumption(full_household)
        categories = {b["category"] for b in result["breakdown"]}
        expected = {"Bathing", "Toilet", "Laundry", "Kitchen", "Vehicle Washing", "Gardening", "Other"}
        assert expected == categories

    def test_bathing_formula(self):
        """
        Bathing = showers_per_day × duration_min × SHOWER_FLOW_RATE × size.
        With 1 person, 1 shower/day, 10-minute shower:
          expected = 1 × 10 × 9.0 = 90 L/day
        """
        data = {
            "household_size": 1,
            "showers_per_day": 1,
            "shower_duration_minutes": 10,
            "toilet_uses_per_day": 0,
            "laundry_loads_per_week": 0,
            "kitchen_usage_minutes": 0,
        }
        result = calculate_household_consumption(data)
        bathing = next(b for b in result["breakdown"] if b["category"] == "Bathing")
        expected = 1 * 10 * C.SHOWER_FLOW_RATE_LPM   # 90 L
        assert abs(bathing["litres_per_day"] - expected) < 0.5

    def test_toilet_formula(self):
        """
        Toilet = toilet_uses_per_day × FLUSH_VOLUME × size.
        1 person, 6 flushes/day, standard 6 L flush:
          expected = 6 × 6 = 36 L/day
        """
        data = {
            "household_size": 1,
            "showers_per_day": 0,
            "shower_duration_minutes": 0,
            "toilet_uses_per_day": 6,
            "laundry_loads_per_week": 0,
            "kitchen_usage_minutes": 0,
        }
        result = calculate_household_consumption(data)
        toilet = next(b for b in result["breakdown"] if b["category"] == "Toilet")
        expected = 6 * C.TOILET_FLUSH_DEFAULT_L   # 36 L
        assert abs(toilet["litres_per_day"] - expected) < 0.5

    def test_laundry_weekly_to_daily_conversion(self):
        """
        Laundry daily = (loads_per_week × LAUNDRY_WATER_PER_LOAD) / 7.
        7 loads/week × 60 L/load / 7 = 60 L/day
        """
        data = {
            "household_size": 1,
            "showers_per_day": 0,
            "shower_duration_minutes": 0,
            "toilet_uses_per_day": 0,
            "laundry_loads_per_week": 7,
            "kitchen_usage_minutes": 0,
        }
        result = calculate_household_consumption(data)
        laundry = next(b for b in result["breakdown"] if b["category"] == "Laundry")
        expected = (7 * C.LAUNDRY_WATER_PER_LOAD_L) / 7   # 60 L/day
        assert abs(laundry["litres_per_day"] - expected) < 0.5

    def test_zero_usage_returns_zero_daily(self):
        """All-zero inputs must return zero daily consumption."""
        data = {
            "household_size": 1,
            "showers_per_day": 0,
            "shower_duration_minutes": 0,
            "toilet_uses_per_day": 0,
            "laundry_loads_per_week": 0,
            "kitchen_usage_minutes": 0,
        }
        result = calculate_household_consumption(data)
        assert result["daily_consumption"] == 0.0
        assert result["weekly_consumption"] == 0.0
        assert result["monthly_consumption"] == 0.0

    def test_household_size_scales_shower_and_toilet(self):
        """
        Doubling household_size should double bathing and toilet totals
        (other categories are household-level, not per-person).
        """
        base = {
            "household_size": 2,
            "showers_per_day": 1,
            "shower_duration_minutes": 5,
            "toilet_uses_per_day": 4,
            "laundry_loads_per_week": 0,
            "kitchen_usage_minutes": 0,
        }
        large = dict(base, household_size=4)

        r_base = calculate_household_consumption(base)
        r_large = calculate_household_consumption(large)

        assert abs(r_large["daily_consumption"] - 2 * r_base["daily_consumption"]) < 0.5

    def test_breakdown_sorted_descending(self, full_household):
        """The category with the highest usage should appear first in breakdown."""
        result = calculate_household_consumption(full_household)
        litres = [b["litres_per_day"] for b in result["breakdown"]]
        assert litres == sorted(litres, reverse=True)

    def test_daily_consumption_reasonable_range(self, full_household):
        """A 4-person household with typical usage should fall between 200-2000 L/day."""
        result = calculate_household_consumption(full_household)
        assert 200 <= result["daily_consumption"] <= 2000, (
            f"Daily consumption {result['daily_consumption']} outside plausible range"
        )


# ===========================================================================
# Calculation tests — Farmer
# ===========================================================================

class TestFarmerCalculation:

    def test_returns_required_keys(self, minimal_farmer):
        result = calculate_farmer_consumption(minimal_farmer)
        assert "daily_consumption" in result
        assert "weekly_consumption" in result
        assert "monthly_consumption" in result
        assert "breakdown" in result

    def test_weekly_is_seven_times_daily(self, minimal_farmer):
        result = calculate_farmer_consumption(minimal_farmer)
        expected = round(result["daily_consumption"] * 7, 2)
        assert result["weekly_consumption"] == expected

    def test_monthly_is_thirty_times_daily(self, minimal_farmer):
        result = calculate_farmer_consumption(minimal_farmer)
        expected = round(result["daily_consumption"] * 30, 2)
        assert result["monthly_consumption"] == expected

    def test_user_estimate_used_when_provided(self, minimal_farmer):
        """
        When estimated_irrigation_litres=2000 and frequency=3/week:
          daily = (2000 × 3) / 7 ≈ 857.14 L/day
        """
        result = calculate_farmer_consumption(minimal_farmer)
        expected_daily = (2000 * 3) / 7
        assert abs(result["daily_consumption"] - expected_daily) < 1.0

    def test_model_estimate_used_when_no_user_estimate(self):
        """
        Without a user estimate, use area × duration × method rate.
        1 acre = 0.404686 ha; drip rate = 650 L/ha/hr; 1 hr duration; 2/week.
          litres_per_session = 0.404686 × 1.0 × 650 = 263.05
          daily = (263.05 × 2) / 7 ≈ 75.16 L/day
        """
        data = {
            "farm_area": 1.0,
            "farm_area_unit": "acre",
            "crop_type": "vegetables",
            "irrigation_method": "drip",
            "irrigation_frequency": 2,
            "irrigation_duration_minutes": 60,   # 1 hour
            "water_source": "groundwater",
            "estimated_irrigation_litres": 0,     # no user estimate
            "rainwater_harvesting": False,
        }
        result = calculate_farmer_consumption(data)
        area_ha = 1.0 * C.ACRES_TO_HECTARES
        rate = C.IRRIGATION_RATE_L_PER_HA_PER_HOUR["drip"]
        expected_per_session = area_ha * 1.0 * rate
        expected_daily = (expected_per_session * 2) / 7
        assert abs(result["daily_consumption"] - expected_daily) < 1.0

    def test_rainwater_credit_reduces_consumption(self):
        """Enabling rainwater harvesting must produce a lower result (10 % credit)."""
        base_data = {
            "farm_area": 2.0,
            "farm_area_unit": "acre",
            "crop_type": "rice",
            "irrigation_method": "flood",
            "irrigation_frequency": 3,
            "irrigation_duration_minutes": 60,
            "water_source": "canal",
            "estimated_irrigation_litres": 0,
            "rainwater_harvesting": False,
        }
        with_credit = dict(base_data, rainwater_harvesting=True)

        r_base   = calculate_farmer_consumption(base_data)
        r_credit = calculate_farmer_consumption(with_credit)

        assert r_credit["daily_consumption"] < r_base["daily_consumption"]
        credit_applied = r_base["daily_consumption"] * 0.10
        assert abs(r_base["daily_consumption"] - r_credit["daily_consumption"] - credit_applied) < 1.0

    def test_zero_frequency_gives_zero_daily(self):
        """If irrigation_frequency is 0, daily consumption must be 0."""
        data = {
            "farm_area": 5.0,
            "farm_area_unit": "hectare",
            "crop_type": "maize",
            "irrigation_method": "sprinkler",
            "irrigation_frequency": 0,
            "irrigation_duration_minutes": 60,
            "water_source": "groundwater",
            "estimated_irrigation_litres": 0,
            "rainwater_harvesting": False,
        }
        result = calculate_farmer_consumption(data)
        assert result["daily_consumption"] == 0.0

    def test_hectare_unit_uses_area_directly(self):
        """
        A 1-hectare farm should give a higher result than a 1-acre farm
        (1 hectare ≈ 2.47 acres).
        """
        acre_data = {
            "farm_area": 1.0,
            "farm_area_unit": "acre",
            "crop_type": "wheat",
            "irrigation_method": "sprinkler",
            "irrigation_frequency": 3,
            "irrigation_duration_minutes": 60,
            "water_source": "groundwater",
            "estimated_irrigation_litres": 0,
            "rainwater_harvesting": False,
        }
        hectare_data = dict(acre_data, farm_area_unit="hectare")

        r_acre    = calculate_farmer_consumption(acre_data)
        r_hectare = calculate_farmer_consumption(hectare_data)

        assert r_hectare["daily_consumption"] > r_acre["daily_consumption"]

    def test_calculation_note_present(self, minimal_farmer):
        """Result should contain a 'calculation_note' describing the method used."""
        result = calculate_farmer_consumption(minimal_farmer)
        assert "calculation_note" in result
        assert len(result["calculation_note"]) > 0


# ===========================================================================
# Validator tests — Registration
# ===========================================================================

class TestRegistrationValidation:

    def _valid(self):
        return {
            "name": "Alice Green",
            "email": "alice@example.com",
            "password": "Secure123",
            "confirm_password": "Secure123",
            "user_type": "household",
        }

    def test_valid_registration_returns_no_errors(self):
        assert validate_registration(self._valid()) == {}

    def test_missing_name(self):
        data = self._valid(); data["name"] = ""
        errors = validate_registration(data)
        assert "name" in errors

    def test_invalid_email(self):
        data = self._valid(); data["email"] = "not-an-email"
        errors = validate_registration(data)
        assert "email" in errors

    def test_short_password(self):
        data = self._valid(); data["password"] = "abc"; data["confirm_password"] = "abc"
        errors = validate_registration(data)
        assert "password" in errors

    def test_mismatched_passwords(self):
        data = self._valid(); data["confirm_password"] = "Different1"
        errors = validate_registration(data)
        assert "confirm_password" in errors

    def test_invalid_user_type(self):
        data = self._valid(); data["user_type"] = "admin"
        errors = validate_registration(data)
        assert "user_type" in errors

    def test_valid_farmer_type(self):
        data = self._valid(); data["user_type"] = "farmer"
        assert validate_registration(data) == {}


# ===========================================================================
# Validator tests — Household Assessment
# ===========================================================================

class TestHouseholdValidation:

    def _valid(self):
        return {
            "household_size": 3,
            "showers_per_day": 2,
            "shower_duration_minutes": 8,
            "toilet_uses_per_day": 5,
            "laundry_loads_per_week": 4,
            "kitchen_usage_minutes": 20,
        }

    def test_valid_payload_returns_no_errors(self):
        assert validate_household_assessment(self._valid()) == {}

    def test_zero_household_size_rejected(self):
        data = self._valid(); data["household_size"] = 0
        errors = validate_household_assessment(data)
        assert "household_size" in errors

    def test_negative_showers_rejected(self):
        data = self._valid(); data["showers_per_day"] = -1
        errors = validate_household_assessment(data)
        assert "showers_per_day" in errors

    def test_excessive_shower_duration_rejected(self):
        data = self._valid(); data["shower_duration_minutes"] = 999
        errors = validate_household_assessment(data)
        assert "shower_duration_minutes" in errors

    def test_missing_required_kitchen_field(self):
        data = self._valid(); del data["kitchen_usage_minutes"]
        errors = validate_household_assessment(data)
        assert "kitchen_usage_minutes" in errors

    def test_optional_gardening_absent_is_ok(self):
        """gardening_frequency is optional; absent should not cause an error."""
        data = self._valid()
        data.pop("gardening_frequency", None)
        errors = validate_household_assessment(data)
        assert "gardening_frequency" not in errors

    def test_boundary_values_accepted(self):
        data = self._valid()
        data["showers_per_day"] = 0
        data["shower_duration_minutes"] = 0
        assert validate_household_assessment(data) == {}


# ===========================================================================
# Validator tests — Farmer Assessment
# ===========================================================================

class TestFarmerValidation:

    def _valid(self):
        return {
            "farm_area": 5.0,
            "farm_area_unit": "acre",
            "crop_type": "rice",
            "irrigation_method": "drip",
            "irrigation_frequency": 3,
            "irrigation_duration_minutes": 60,
            "water_source": "canal",
            "estimated_irrigation_litres": 0,
            "rainwater_harvesting": False,
        }

    def test_valid_payload_returns_no_errors(self):
        assert validate_farmer_assessment(self._valid()) == {}

    def test_zero_farm_area_rejected(self):
        data = self._valid(); data["farm_area"] = 0
        errors = validate_farmer_assessment(data)
        assert "farm_area" in errors

    def test_negative_farm_area_rejected(self):
        data = self._valid(); data["farm_area"] = -2
        errors = validate_farmer_assessment(data)
        assert "farm_area" in errors

    def test_invalid_irrigation_method_rejected(self):
        data = self._valid(); data["irrigation_method"] = "laser"
        errors = validate_farmer_assessment(data)
        assert "irrigation_method" in errors

    def test_all_valid_irrigation_methods_accepted(self):
        for method in ["flood", "drip", "sprinkler", "other"]:
            data = self._valid(); data["irrigation_method"] = method
            errors = validate_farmer_assessment(data)
            assert "irrigation_method" not in errors, f"Method '{method}' incorrectly rejected"

    def test_invalid_water_source_rejected(self):
        data = self._valid(); data["water_source"] = "magic_spring"
        errors = validate_farmer_assessment(data)
        assert "water_source" in errors

    def test_missing_crop_type_rejected(self):
        data = self._valid(); data["crop_type"] = ""
        errors = validate_farmer_assessment(data)
        assert "crop_type" in errors

    def test_hectare_unit_accepted(self):
        data = self._valid(); data["farm_area_unit"] = "hectare"
        assert validate_farmer_assessment(data) == {}

    def test_invalid_area_unit_rejected(self):
        data = self._valid(); data["farm_area_unit"] = "square_feet"
        errors = validate_farmer_assessment(data)
        assert "farm_area_unit" in errors


# ===========================================================================
# Validator tests — Generic assessment dispatch
# ===========================================================================

class TestAssessmentDispatch:

    def test_missing_assessment_type_rejected(self):
        errors = validate_assessment({})
        assert "assessment_type" in errors

    def test_invalid_assessment_type_rejected(self):
        errors = validate_assessment({"assessment_type": "factory"})
        assert "assessment_type" in errors

    def test_dispatches_to_household(self):
        data = {
            "assessment_type": "household",
            "household_size": -1,   # invalid
            "showers_per_day": 1,
            "shower_duration_minutes": 5,
            "toilet_uses_per_day": 4,
            "laundry_loads_per_week": 2,
            "kitchen_usage_minutes": 15,
        }
        errors = validate_assessment(data)
        assert "household_size" in errors

    def test_dispatches_to_farmer(self):
        data = {
            "assessment_type": "farmer",
            "farm_area": 0,         # invalid
            "crop_type": "wheat",
            "irrigation_method": "drip",
        }
        errors = validate_assessment(data)
        assert "farm_area" in errors
