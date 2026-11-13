"""
NutriLens – Scoring Engine Test Suite (Day 5)
Covers:
- Serving size parsing and standardization (per 100g/ml vs per serving)
- Nutrition validation and data completeness handling
- Deterministic score generation across categories
- Explanations, positive factors, attention factors, and disclaimer
- Insufficient data handling (no manufactured score)
- API endpoints: GET /api/products/{id}/analysis and POST /api/analysis/score
"""
import pytest
from fastapi.testclient import TestClient

from app.seed import seed_database
from app.scoring_engine.rules import SCORING_RULE_VERSION
from app.scoring_engine.validators import validate_nutrition_data
from app.scoring_engine.calculator import (
    parse_serving_size,
    calculate_serving_values,
    calculate_deterministic_score,
)
from app.scoring_engine.service import (
    analyze_nutrition_payload,
)


# ===========================================================================
# 1. Serving Size Parsing & Scaling Tests
# ===========================================================================

def test_parse_serving_size_patterns():
    qty, unit = parse_serving_size("30g")
    assert qty == 30.0
    assert unit == "g"

    qty, unit = parse_serving_size("2 biscuits (30g)")
    assert qty == 30.0
    assert unit == "g"

    qty, unit = parse_serving_size("250ml")
    assert qty == 250.0
    assert unit == "ml"

    qty, unit = parse_serving_size("1 bottle (330 ml)")
    assert qty == 330.0
    assert unit == "ml"

    qty, unit = parse_serving_size(None)
    assert qty is None
    assert unit == "g"


def test_calculate_serving_values():
    per_100 = {
        "energy_kcal": 450.0,
        "total_fat_g": 20.0,
        "saturated_fat_g": 10.0,
        "trans_fat_g": None,  # Not present
        "carbohydrates_g": 60.0,
        "total_sugar_g": 20.0,
        "sodium_mg": 300.0,
    }
    # 30g serving size
    serving = calculate_serving_values(per_100, serving_quantity=30.0)

    assert serving["energy_kcal"] == 135.0  # 450 * 0.3
    assert serving["total_fat_g"] == 6.0    # 20 * 0.3
    assert serving["saturated_fat_g"] == 3.0
    assert serving["trans_fat_g"] is None   # Must NOT assume absent values
    assert serving["sodium_mg"] == 90.0


# ===========================================================================
# 2. Nutrition Data Validation & Completeness Tests
# ===========================================================================

def test_validation_complete_data():
    complete_nutrients = {
        "energy_kcal": 400.0,
        "total_fat_g": 12.0,
        "saturated_fat_g": 4.0,
        "trans_fat_g": 0.0,
        "carbohydrates_g": 65.0,
        "total_sugar_g": 15.0,
        "added_sugar_g": 10.0,
        "dietary_fibre_g": 5.0,
        "protein_g": 8.0,
        "sodium_mg": 250.0,
    }
    res = validate_nutrition_data(complete_nutrients)
    assert res.is_valid is True
    assert res.is_scoreable is True
    assert res.data_completeness_pct == 100.0
    assert len(res.missing_critical_fields) == 0


def test_validation_missing_critical_data():
    incomplete = {
        "energy_kcal": 400.0,
        "total_fat_g": 12.0,
        # Missing saturated_fat_g, total_sugar_g, protein_g, sodium_mg
        "carbohydrates_g": 65.0,
    }
    res = validate_nutrition_data(incomplete)
    assert res.is_scoreable is False
    assert "total_sugar_g" in res.missing_critical_fields
    assert "saturated_fat_g" in res.missing_critical_fields
    assert "protein_g" in res.missing_critical_fields
    assert "sodium_mg" in res.missing_critical_fields


def test_validation_inconsistent_fat_error():
    inconsistent = {
        "energy_kcal": 400.0,
        "total_fat_g": 5.0,
        "saturated_fat_g": 10.0,  # Sat fat > Total fat!
        "carbohydrates_g": 50.0,
        "total_sugar_g": 10.0,
        "protein_g": 5.0,
        "sodium_mg": 200.0,
    }
    res = validate_nutrition_data(inconsistent)
    assert res.is_valid is False
    assert res.is_scoreable is False
    assert any("cannot exceed total fat" in issue.message for issue in res.issues)


# ===========================================================================
# 3. Deterministic Scoring Calculation Tests
# ===========================================================================

def test_score_is_strictly_deterministic():
    nutrients = {
        "energy_kcal": 485.0,
        "total_fat_g": 21.0,
        "saturated_fat_g": 10.0,
        "trans_fat_g": 0.0,
        "carbohydrates_g": 66.0,
        "total_sugar_g": 15.0,
        "added_sugar_g": 13.0,
        "dietary_fibre_g": 6.0,
        "protein_g": 8.0,
        "sodium_mg": 450.0,
    }
    run1 = calculate_deterministic_score(nutrients, category="Biscuits & Cookies")
    run2 = calculate_deterministic_score(nutrients, category="Biscuits & Cookies")

    assert run1["score"] == run2["score"]
    assert run1["penalties"] == run2["penalties"]
    assert run1["bonuses"] == run2["bonuses"]
    assert 0 <= run1["score"] <= 100


def test_healthy_food_scores_higher_than_high_sugar_snack():
    # 1. Healthy oats profile
    oats = {
        "energy_kcal": 380.0,
        "total_fat_g": 6.5,
        "saturated_fat_g": 1.2,
        "trans_fat_g": 0.0,
        "carbohydrates_g": 60.0,
        "total_sugar_g": 1.0,
        "added_sugar_g": 0.0,
        "dietary_fibre_g": 10.0,
        "protein_g": 13.0,
        "sodium_mg": 10.0,
    }
    # 2. Sugary candy profile
    candy = {
        "energy_kcal": 520.0,
        "total_fat_g": 28.0,
        "saturated_fat_g": 15.0,
        "trans_fat_g": 0.5,
        "carbohydrates_g": 65.0,
        "total_sugar_g": 50.0,
        "added_sugar_g": 48.0,
        "dietary_fibre_g": 0.5,
        "protein_g": 2.0,
        "sodium_mg": 350.0,
    }

    score_oats = calculate_deterministic_score(oats, category="Breakfast Cereals")
    score_candy = calculate_deterministic_score(candy, category="Chocolates & Sweets")

    assert score_oats["score"] > score_candy["score"]
    assert score_oats["score"] >= 75
    assert score_candy["score"] <= 40


def test_trans_fat_penalty():
    clean_product = {
        "energy_kcal": 400.0,
        "total_fat_g": 15.0,
        "saturated_fat_g": 4.0,
        "trans_fat_g": 0.0,
        "carbohydrates_g": 55.0,
        "total_sugar_g": 10.0,
        "protein_g": 7.0,
        "sodium_mg": 300.0,
    }
    trans_fat_product = dict(clean_product)
    trans_fat_product["trans_fat_g"] = 1.2

    score_clean = calculate_deterministic_score(clean_product, category="General")
    score_trans = calculate_deterministic_score(trans_fat_product, category="General")

    assert score_trans["score"] < score_clean["score"]
    assert "trans_fat" in score_trans["penalties"]


def test_beverage_category_awareness():
    # 8g sugar in beverage vs 8g sugar in solid food
    bev_nutrients = {
        "energy_kcal": 40.0,
        "total_fat_g": 0.0,
        "saturated_fat_g": 0.0,
        "carbohydrates_g": 8.0,
        "total_sugar_g": 8.0,
        "protein_g": 0.0,
        "sodium_mg": 20.0,
    }
    food_nutrients = dict(bev_nutrients)
    food_nutrients["energy_kcal"] = 150.0

    score_bev = calculate_deterministic_score(bev_nutrients, category="Beverages")
    score_food = calculate_deterministic_score(food_nutrients, category="General")

    # In beverages, liquid sugar is penalized more heavily
    assert score_bev["penalties"]["sugar"] > score_food["penalties"]["sugar"]


# ===========================================================================
# 4. End-to-End Analysis Pipeline & Insufficient Data Handling
# ===========================================================================

def test_analysis_pipeline_insufficient_data():
    incomplete = {
        "energy_kcal": 400.0,
        # missing total_sugar_g and saturated_fat_g
        "protein_g": 5.0,
        "sodium_mg": 100.0,
    }
    res = analyze_nutrition_payload(incomplete, category="General")

    assert res["status"] == "insufficient_data"
    assert res["score"] is None
    assert res["grade"] is None
    assert "total_sugar_g" in res["missing_critical_fields"]
    assert res["scoring_rule_version"] == SCORING_RULE_VERSION
    assert "official FSSAI score" in res["disclaimer"]


def test_analysis_pipeline_complete():
    nutrients = {
        "energy_kcal": 460.0,
        "total_fat_g": 18.0,
        "saturated_fat_g": 8.0,
        "trans_fat_g": 0.0,
        "carbohydrates_g": 64.0,
        "total_sugar_g": 18.0,
        "added_sugar_g": 12.0,
        "dietary_fibre_g": 4.5,
        "protein_g": 7.5,
        "sodium_mg": 380.0,
    }
    res = analyze_nutrition_payload(
        nutrients,
        category="Biscuits & Cookies",
        serving_size_str="2 biscuits (30g)",
    )

    assert res["status"] == "complete"
    assert isinstance(res["score"], int)
    assert 0 <= res["score"] <= 100
    assert res["grade"] in ("A", "B", "C", "D", "E")
    assert res["serving_size_info"]["quantity"] == 30.0
    assert res["per_serving_values"]["energy_kcal"] == 138.0
    assert len(res["positive_factors"]) > 0
    assert len(res["attention_factors"]) > 0
    assert res["scoring_rule_version"] == SCORING_RULE_VERSION
    assert res["nutrient_evaluations"]["total_sugar_g"]["level"] in ("moderate", "high")


# ===========================================================================
# 5. API Endpoints Tests
# ===========================================================================

def test_api_custom_score_endpoint(client: TestClient):
    payload = {
        "nutrients": {
            "energy_kcal": 485.0,
            "total_fat_g": 21.0,
            "saturated_fat_g": 10.0,
            "trans_fat_g": 0.0,
            "carbohydrates_g": 66.0,
            "total_sugar_g": 15.0,
            "dietary_fibre_g": 6.0,
            "protein_g": 8.0,
            "sodium_mg": 450.0,
        },
        "category": "Biscuits & Cookies",
        "serving_size": "30g",
    }
    resp = client.post("/api/analysis/score", json=payload)
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["status"] == "complete"
    assert data["score"] is not None
    assert data["grade"] is not None
    assert data["per_serving_values"]["energy_kcal"] == 145.5
    assert len(data["positive_factors"]) >= 1


def test_api_custom_score_insufficient_data(client: TestClient):
    payload = {
        "nutrients": {
            "energy_kcal": 100.0,
            # missing all macros
        },
        "category": "General",
        "serving_size": "100g",
    }
    resp = client.post("/api/analysis/score", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "insufficient_data"
    assert data["score"] is None
    assert len(data["missing_critical_fields"]) > 0


def test_api_product_analysis_endpoint_and_embed(client: TestClient, db_session):
    # Seed catalogue demo products into test database
    seed_database(db_session)

    # Fetch existing catalogue products from seed
    cat_resp = client.get("/api/products?page_size=1")
    assert cat_resp.status_code == 200
    items = cat_resp.json()["items"]
    assert len(items) > 0
    product_id = items[0]["id"]

    # 1. Dedicated analysis endpoint: GET /api/products/{id}/analysis
    analysis_resp = client.get(f"/api/products/{product_id}/analysis")
    assert analysis_resp.status_code == 200
    an_data = analysis_resp.json()
    assert an_data["product_id"] == product_id
    assert an_data["status"] == "complete"
    assert an_data["score"] is not None
    assert an_data["scoring_rule_version"] == SCORING_RULE_VERSION

    # 2. Embedded in GET /api/products/{id}
    prod_resp = client.get(f"/api/products/{product_id}")
    assert prod_resp.status_code == 200
    prod_data = prod_resp.json()
    assert "nutrition_analysis" in prod_data
    assert prod_data["nutrition_analysis"]["score"] == an_data["score"]
