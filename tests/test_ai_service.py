"""
Tests for AquaWise AI Service (backend/services/ai_service.py).

Validates:
1. AI service configuration and status reporting (without leaking credentials).
2. Deterministic rule-based fallback recommendation generation for household and farmer users.
3. Safe offline fallback when AI API key is missing.
4. AI recommendation enhancement with preservation of deterministic numbers.
5. Graceful handling of API errors, timeouts, and malformed responses.
6. Conversational AI Assistant responses in offline mode and mocked online mode.
7. Verification that AI is never used as the source of truth for numerical calculations.
"""

import json
from unittest.mock import patch, MagicMock
import requests

from backend.services.ai_service import (
    is_ai_available,
    get_ai_status,
    get_fallback_recommendations,
    enhance_recommendations,
    chat_with_assistant,
    _get_fallback_chat_response,
)
from backend.services.calculation_service import (
    calculate_household_consumption,
    calculate_farmer_consumption,
)


# ===========================================================================
# Sample Assessment Fixtures
# ===========================================================================

def sample_household_data():
    return {
        "household_size": 4,
        "showers_per_day": 2,
        "shower_duration_minutes": 10,
        "toilet_uses_per_day": 5,
        "laundry_loads_per_week": 4,
        "kitchen_usage_minutes": 30,
        "vehicle_washing_frequency": 2,
        "gardening_frequency": 3,
        "gardening_duration_minutes": 20,
        "other_usage_litres": 10,
    }


def sample_farmer_data():
    return {
        "farm_area": 5.0,
        "farm_area_unit": "acre",
        "crop_type": "rice",
        "irrigation_method": "flood",
        "irrigation_frequency": 3,
        "irrigation_duration_minutes": 120,
        "water_source": "canal",
        "rainwater_harvesting": False,
        "estimated_irrigation_litres": 0,
    }


# ===========================================================================
# Test Group 1: Configuration & Availability
# ===========================================================================

class TestAIConfiguration:

    def test_offline_when_key_empty(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        assert is_ai_available() is False

    def test_online_when_key_present(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "test-secret-key-12345")
        assert is_ai_available() is True

    def test_status_does_not_leak_key(self, monkeypatch):
        secret = "super-secret-key-do-not-leak"
        monkeypatch.setenv("AI_API_KEY", secret)
        status = get_ai_status()
        assert status["available"] is True
        assert status["provider"] == "google-gemini"
        assert status["mode"] == "online"
        # Verify secret key is nowhere in the status dict
        status_str = json.dumps(status)
        assert secret not in status_str

    def test_offline_status_mode(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        status = get_ai_status()
        assert status["available"] is False
        assert status["mode"] == "offline_fallback"


# ===========================================================================
# Test Group 2: Deterministic Fallback Recommendations
# ===========================================================================

class TestFallbackRecommendations:

    def test_household_fallback_recommendations_structure(self):
        data = sample_household_data()
        calc = calculate_household_consumption(data)
        recs = get_fallback_recommendations(data, calc, user_type="household")

        assert len(recs) >= 3
        for r in recs:
            assert "category" in r
            assert "title" in r
            assert "description" in r
            assert r["priority"] in ["high", "medium", "low"]
            assert r["source"] == "rule_based"
            assert isinstance(r["potential_saving"], float)
            assert r["potential_saving"] > 0

    def test_household_high_shower_triggers_bathing_recommendation(self):
        data = sample_household_data()
        calc = calculate_household_consumption(data)
        recs = get_fallback_recommendations(data, calc, user_type="household")

        categories = [r["category"] for r in recs]
        assert "Bathing" in categories
        bathing_rec = next(r for r in recs if r["category"] == "Bathing")
        assert bathing_rec["priority"] in ["high", "medium"]
        assert bathing_rec["potential_saving"] > 10.0

    def test_household_vehicle_washing_triggers_bucket_recommendation(self):
        data = sample_household_data()
        calc = calculate_household_consumption(data)
        recs = get_fallback_recommendations(data, calc, user_type="household")

        veh_rec = next((r for r in recs if r["category"] == "Vehicle Washing"), None)
        assert veh_rec is not None
        assert "bucket" in veh_rec["description"].lower()

    def test_farmer_flood_irrigation_triggers_drip_upgrade(self):
        data = sample_farmer_data()
        calc = calculate_farmer_consumption(data)
        recs = get_fallback_recommendations(data, calc, user_type="farmer")

        irr_rec = next((r for r in recs if r["category"] == "Irrigation"), None)
        assert irr_rec is not None
        assert irr_rec["priority"] == "high"
        assert "drip" in irr_rec["title"].lower()
        # Savings should be substantial for flood irrigation
        assert irr_rec["potential_saving"] >= 50.0

    def test_farmer_no_rainwater_triggers_catchment_recommendation(self):
        data = sample_farmer_data()
        data["rainwater_harvesting"] = False
        calc = calculate_farmer_consumption(data)
        recs = get_fallback_recommendations(data, calc, user_type="farmer")

        titles = [r["title"].lower() for r in recs]
        assert any("rainwater" in t for t in titles)

    def test_recommendations_sorted_by_potential_saving(self):
        data = sample_household_data()
        calc = calculate_household_consumption(data)
        recs = get_fallback_recommendations(data, calc, user_type="household")

        savings = [r["potential_saving"] for r in recs]
        assert savings == sorted(savings, reverse=True)


# ===========================================================================
# Test Group 3: AI Recommendation Enhancement & Offline Safety
# ===========================================================================

class TestRecommendationEnhancement:

    def test_enhance_in_offline_mode_returns_rule_based(self, monkeypatch):
        """When no API key is provided, enhancement seamlessly returns rule-based recs."""
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")

        data = sample_household_data()
        calc = calculate_household_consumption(data)
        recs = enhance_recommendations(data, calc, user_type="household")

        assert len(recs) > 0
        for r in recs:
            assert r["source"] == "rule_based"

    @patch("backend.services.ai_service.requests.post")
    def test_enhance_with_ai_preserves_deterministic_numbers(self, mock_post, monkeypatch):
        """AI must personalize wording while strictly preserving deterministic savings and categories."""
        monkeypatch.setenv("AI_API_KEY", "mock-key")

        data = sample_household_data()
        calc = calculate_household_consumption(data)
        base_recs = get_fallback_recommendations(data, calc, user_type="household")

        # Mock successful AI JSON response
        mock_ai_json = [
            {
                "category": base_recs[0]["category"],
                "title": "Smart Bathing Makeover for Your Family",
                "description": "Cut shower times by just 3 minutes with aerators to save big on water!",
                "priority": base_recs[0]["priority"],
                "potential_saving": 999999.0,  # Deliberately fake number from AI to test protection
            }
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": f"```json\n{json.dumps(mock_ai_json)}\n```"}
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        enhanced = enhance_recommendations(data, calc, user_type="household")

        assert len(enhanced) == len(base_recs)
        # First recommendation title was personalized by AI
        assert enhanced[0]["title"] == "Smart Bathing Makeover for Your Family"
        assert enhanced[0]["source"] == "hybrid"
        # CRITICAL TEST: Deterministic saving from base_recs MUST be preserved, NOT the AI fake number!
        assert enhanced[0]["potential_saving"] == base_recs[0]["potential_saving"]
        assert enhanced[0]["potential_saving"] != 999999.0

    @patch("backend.services.ai_service.requests.post")
    def test_enhance_falls_back_gracefully_on_api_error(self, mock_post, monkeypatch):
        """Network errors or 500 status codes must fall back to rule-based without raising exceptions."""
        monkeypatch.setenv("AI_API_KEY", "mock-key")
        mock_post.side_effect = requests.RequestException("Network connection failed")

        data = sample_household_data()
        calc = calculate_household_consumption(data)
        recs = enhance_recommendations(data, calc, user_type="household")

        assert len(recs) > 0
        assert all(r["source"] == "rule_based" for r in recs)

    @patch("backend.services.ai_service.requests.post")
    def test_enhance_falls_back_on_timeout(self, mock_post, monkeypatch):
        """API timeouts must fall back gracefully to rule-based."""
        monkeypatch.setenv("AI_API_KEY", "mock-key")
        mock_post.side_effect = requests.Timeout("Gateway timed out")

        data = sample_household_data()
        calc = calculate_household_consumption(data)
        recs = enhance_recommendations(data, calc, user_type="household")

        assert len(recs) > 0
        assert all(r["source"] == "rule_based" for r in recs)

    @patch("backend.services.ai_service.requests.post")
    def test_enhance_falls_back_on_garbage_json(self, mock_post, monkeypatch):
        """Non-JSON output from AI falls back cleanly."""
        monkeypatch.setenv("AI_API_KEY", "mock-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [{"content": {"parts": [{"text": "Sorry, I cannot help with that."}]}}]
        }
        mock_post.return_value = mock_response

        data = sample_household_data()
        calc = calculate_household_consumption(data)
        recs = enhance_recommendations(data, calc, user_type="household")

        assert len(recs) > 0
        assert all(r["source"] == "rule_based" for r in recs)


# ===========================================================================
# Test Group 4: Conversational AI Assistant
# ===========================================================================

class TestAIAssistant:

    def test_empty_message_returns_prompt(self):
        res = chat_with_assistant("")
        assert res["success"] is False
        assert "question" in res["response"].lower()

    def test_offline_shower_advice(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")

        res = chat_with_assistant("How can I save water in the shower?")
        assert res["success"] is True
        assert res["source"] == "fallback"
        assert "aerat" in res["response"].lower() or "5 minutes" in res["response"]

    def test_offline_irrigation_advice(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")

        res = chat_with_assistant("What is the best irrigation method for my farm crops?")
        assert res["success"] is True
        assert res["source"] == "fallback"
        assert "drip" in res["response"].lower()
        # Farming disclaimer should be present
        assert "agronomic" in res["response"].lower() or "extension" in res["response"].lower()

    def test_offline_leak_detection_advice(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "")
        monkeypatch.setenv("GEMINI_API_KEY", "")

        res = chat_with_assistant("How do I check for water leaks in my pipes?")
        assert res["success"] is True
        assert res["source"] == "fallback"
        assert "meter" in res["response"].lower() or "toilet" in res["response"].lower()

    def test_offline_greeting(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "")
        res = chat_with_assistant("Hello there!")
        assert res["success"] is True
        assert "aquawise" in res["response"].lower()

    def test_offline_with_user_context(self, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "")
        context = {
            "user_type": "household",
            "daily_consumption": 420.0,
            "top_category": "Bathing",
            "water_saver_score": 68,
        }
        res = chat_with_assistant("How can I improve my water usage?", user_context=context)
        assert res["success"] is True
        assert "420.0" in res["response"]
        assert "Bathing" in res["response"]

    @patch("backend.services.ai_service.requests.post")
    def test_online_chat_success(self, mock_post, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "valid-test-key")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Installing tap aerators will cut your kitchen water use by 40%."}
                        ]
                    }
                }
            ]
        }
        mock_post.return_value = mock_response

        res = chat_with_assistant("What should I do in the kitchen?")
        assert res["success"] is True
        assert res["source"] == "ai"
        assert "aerators" in res["response"]

    @patch("backend.services.ai_service.requests.post")
    def test_online_chat_falls_back_on_failure(self, mock_post, monkeypatch):
        monkeypatch.setenv("AI_API_KEY", "valid-test-key")
        mock_post.side_effect = requests.ConnectionError("Failed to reach Google API")

        res = chat_with_assistant("How can I save water in the bathroom?")
        # Must gracefully fall back without throwing an error
        assert res["success"] is True
        assert res["source"] == "fallback"
        assert len(res["response"]) > 0
