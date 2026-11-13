"""
NutriLens – Personalized Dietary Suitability Test Suite (Day 6)
Covers:
- Allergen checking: Declared conflicts vs Precautionary warnings separation
- Dietary restrictions: Vegetarian, Vegan, Jain, Gluten-Free, Halal
- Nutrition goals and monitored nutrients
- Missing ingredient safety warnings
- Independence of general NutriLens score from personal suitability
- API Endpoints:
  - POST /api/products/{id}/suitability
  - GET /api/profile/dietary-preferences
  - PUT /api/profile/dietary-preferences
"""
import pytest
from fastapi.testclient import TestClient

from app.seed import seed_database
from app.suitability_engine.rules import (
    STATUS_SUITABLE,
    STATUS_CAUTION,
    STATUS_CONFLICT,
    STATUS_INSUFFICIENT,
)
from app.suitability_engine.matcher import evaluate_suitability


# ===========================================================================
# 1. Matcher Unit Tests – Allergens & Precautionary Statements
# ===========================================================================

def test_declared_allergen_conflict():
    product_ingredients = [
        {"name": "Peanut Butter", "original_text": "Roasted Peanuts (90%), Sugar, Salt"},
    ]
    product_allergens = [
        {"name": "Peanuts", "declaration_type": "declared"},
    ]

    res = evaluate_suitability(
        product_name="Peanut Crunch",
        product_ingredients=product_ingredients,
        product_allergens=product_allergens,
        raw_ingredients_text="Roasted Peanuts, Sugar, Salt",
        nutrition_facts=None,
        user_preference="None",
        user_allergies=["Peanuts"],
        user_restrictions=[],
        user_nutrition_goals=[],
        user_monitored_nutrients=[],
    )

    assert res.status == STATUS_CONFLICT
    assert res.is_suitable is False
    assert len(res.conflicts) == 1
    assert "Declared Allergen" in res.conflicts[0].title
    assert res.conflicts[0].is_precautionary is False


def test_precautionary_statement_results_in_caution_not_conflict():
    # Crucial safety requirement: May contain != Declared allergen
    product_ingredients = [
        {"name": "Whole Wheat Flour", "original_text": "Wheat Flour, Water, Yeast"},
    ]
    product_allergens = [
        {"name": "Peanuts", "declaration_type": "precautionary"},
    ]

    res = evaluate_suitability(
        product_name="Whole Wheat Bread",
        product_ingredients=product_ingredients,
        product_allergens=product_allergens,
        raw_ingredients_text="Wheat Flour, Water, Yeast. May contain traces of peanuts.",
        nutrition_facts=None,
        user_preference="None",
        user_allergies=["Peanuts"],
        user_restrictions=[],
        user_nutrition_goals=[],
        user_monitored_nutrients=[],
    )

    # Must be Caution, NOT Declared restriction conflict
    assert res.status == STATUS_CAUTION
    assert res.is_suitable is False
    assert len(res.conflicts) == 0
    assert len(res.cautions) >= 1
    assert res.cautions[0].is_precautionary is True
    assert "Precautionary" in res.cautions[0].title


# ===========================================================================
# 2. Matcher Unit Tests – Vegetarian, Vegan, Jain, Gluten-Free
# ===========================================================================

def test_vegetarian_preference_detects_animal_gelatin():
    product_ingredients = [
        {"name": "Sugar", "original_text": "Sugar"},
        {"name": "Gelatin", "original_text": "Gelatin (pork source)"},
    ]
    res = evaluate_suitability(
        product_name="Gummy Bears",
        product_ingredients=product_ingredients,
        product_allergens=[],
        raw_ingredients_text="Sugar, Gelatin, Citric acid",
        nutrition_facts=None,
        user_preference="Vegetarian",
        user_allergies=[],
        user_restrictions=[],
        user_nutrition_goals=[],
        user_monitored_nutrients=[],
    )

    assert res.status == STATUS_CONFLICT
    assert any("Non-Vegetarian" in c.title for c in res.conflicts)


def test_vegan_preference_detects_dairy_whey():
    product_ingredients = [
        {"name": "Cocoa", "original_text": "Cocoa powder"},
        {"name": "Whey Powder", "original_text": "Milk Whey (from cow milk)"},
    ]
    res = evaluate_suitability(
        product_name="Chocolate Drink",
        product_ingredients=product_ingredients,
        product_allergens=[],
        raw_ingredients_text="Cocoa powder, Whey Powder",
        nutrition_facts=None,
        user_preference="Vegan",
        user_allergies=[],
        user_restrictions=[],
        user_nutrition_goals=[],
        user_monitored_nutrients=[],
    )

    assert res.status == STATUS_CONFLICT
    assert any("Vegan" in c.detail for c in res.conflicts)


def test_jain_preference_detects_root_vegetables():
    product_ingredients = [
        {"name": "Potato", "original_text": "Dehydrated Potato Flakes"},
        {"name": "Onion Powder", "original_text": "Onion Powder"},
    ]
    res = evaluate_suitability(
        product_name="Potato Chips",
        product_ingredients=product_ingredients,
        product_allergens=[],
        raw_ingredients_text="Potato, Onion powder, Salt",
        nutrition_facts=None,
        user_preference="Jain",
        user_allergies=[],
        user_restrictions=[],
        user_nutrition_goals=[],
        user_monitored_nutrients=[],
    )

    assert res.status == STATUS_CONFLICT
    assert any("Jain" in c.title or "Jain" in c.detail for c in res.conflicts)


def test_gluten_free_restriction():
    product_ingredients = [
        {"name": "Maida", "original_text": "Refined Wheat Flour (Maida)"},
    ]
    res = evaluate_suitability(
        product_name="Biscuits",
        product_ingredients=product_ingredients,
        product_allergens=[],
        raw_ingredients_text="Maida, Sugar, Palm oil",
        nutrition_facts=None,
        user_preference="None",
        user_allergies=[],
        user_restrictions=["Gluten-Free"],
        user_nutrition_goals=[],
        user_monitored_nutrients=[],
    )

    assert res.status == STATUS_CONFLICT
    assert any("Gluten" in c.title for c in res.conflicts)


# ===========================================================================
# 3. Nutrition Goals & Missing Information Safety
# ===========================================================================

def test_nutrition_goal_and_monitored_nutrients():
    nutrition_facts = {
        "energy_kcal": 450.0,
        "total_sugar_g": 22.0,  # Exceeds low_sugar threshold (10g)
        "sodium_mg": 750.0,     # Exceeds monitored sodium limit (500mg)
        "protein_g": 10.0,      # Meets high_protein goal (>=8g)
    }
    product_ingredients = [
        {"name": "Wheat Flour", "original_text": "Wheat Flour"},
    ]

    res = evaluate_suitability(
        product_name="Savory Crackers",
        product_ingredients=product_ingredients,
        product_allergens=[],
        raw_ingredients_text="Wheat Flour, Salt, Sugar",
        nutrition_facts=nutrition_facts,
        user_preference="None",
        user_allergies=[],
        user_restrictions=[],
        user_nutrition_goals=["low_sugar", "high_protein"],
        user_monitored_nutrients=["sodium_mg"],
    )

    # Goal violations lead to Caution status
    assert res.status == STATUS_CAUTION
    assert any("Low Sugar" in c.title for c in res.cautions)
    assert any("High Sodium" in c.title for c in res.cautions)
    assert any("High Protein" in p.title for p in res.positive_observations)


def test_missing_ingredients_returns_insufficient_information():
    res = evaluate_suitability(
        product_name="Unknown Unlabeled Product",
        product_ingredients=[],  # Missing
        product_allergens=[],
        raw_ingredients_text=None,
        nutrition_facts=None,
        user_preference="Vegetarian",
        user_allergies=["Peanuts"],
        user_restrictions=[],
        user_nutrition_goals=[],
        user_monitored_nutrients=[],
    )

    assert res.status == STATUS_INSUFFICIENT
    assert res.is_suitable is False
    assert any("Missing ingredient" in w for w in res.safety_warnings)
    assert any("Not detecting an allergen" in w for w in res.safety_warnings)


# ===========================================================================
# 4. Independence of General NutriLens Score & Personal Suitability
# ===========================================================================

def test_general_score_remains_independent_of_user_suitability(client: TestClient, db_session):
    seed_database(db_session)

    # Seed database with demo products (NutriDemo Digestive Biscuits contains Wheat & Milk)
    cat_resp = client.get("/api/products?search=NutriDemo")
    assert cat_resp.status_code == 200
    items = cat_resp.json()["items"]
    assert len(items) > 0
    product_id = items[0]["id"]

    # Check general analysis score
    gen_analysis_resp = client.get(f"/api/products/{product_id}/analysis")
    assert gen_analysis_resp.status_code == 200
    general_score = gen_analysis_resp.json()["score"]

    # User 1: Clean profile (no allergies, general eater)
    suit_u1 = client.post(
        f"/api/products/{product_id}/suitability",
        json={"dietary_preference": "None", "allergies": []},
    )
    assert suit_u1.status_code == 200
    res_u1 = suit_u1.json()
    assert res_u1["status"] == STATUS_SUITABLE

    # User 2: Gluten allergy
    suit_u2 = client.post(
        f"/api/products/{product_id}/suitability",
        json={"dietary_preference": "None", "allergies": ["Wheat"]},
    )
    assert suit_u2.status_code == 200
    res_u2 = suit_u2.json()
    assert res_u2["status"] == STATUS_CONFLICT

    # Re-verify general nutrition score has NOT changed
    gen_analysis_recheck = client.get(f"/api/products/{product_id}/analysis")
    assert gen_analysis_recheck.json()["score"] == general_score


# ===========================================================================
# 5. API Endpoints Tests
# ===========================================================================

def test_api_dietary_preferences_flow(client: TestClient):
    # Register and authenticate user
    reg_payload = {
        "email": "suitability_tester@example.com",
        "password": "Password123!",
        "full_name": "Suitability User",
        "dietary_preference": "Vegetarian",
        "allergies": ["Peanuts"],
        "dietary_restrictions": ["Low-Sodium"],
        "nutrition_goals": ["heart_health"],
    }
    auth_resp = client.post("/api/auth/register", json=reg_payload)
    assert auth_resp.status_code == 201
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/profile/dietary-preferences
    get_resp = client.get("/api/profile/dietary-preferences", headers=headers)
    assert get_resp.status_code == 200
    pref_data = get_resp.json()
    assert pref_data["dietary_preference"] == "Vegetarian"
    assert "Peanuts" in pref_data["allergies"]

    # 2. PUT /api/profile/dietary-preferences
    update_payload = {
        "dietary_preference": "Vegan",
        "allergies": ["Peanuts", "Soy"],
        "dietary_restrictions": ["Gluten-Free"],
        "nutrition_goals": ["high_protein"],
        "monitored_nutrients": ["sodium_mg", "total_sugar_g"],
    }
    put_resp = client.put("/api/profile/dietary-preferences", json=update_payload, headers=headers)
    assert put_resp.status_code == 200
    updated_data = put_resp.json()
    assert updated_data["dietary_preference"] == "Vegan"
    assert "Soy" in updated_data["allergies"]
    assert "Gluten-Free" in updated_data["dietary_restrictions"]
    assert "sodium_mg" in updated_data["monitored_nutrients"]
