"""
NutriLens – Automated Food Label Scanning & Analysis Tests
Tests the fully automated scanning workflow and the 5 specific image scenarios:
1. Clear image with both ingredients and nutrition facts
2. Image containing only ingredients (scoring unavailable, ingredients analyzed)
3. Image containing only nutrition table (scoring works, ingredients unavailable)
4. Blurry image (low confidence, uncertainty flags, graceful handling)
5. Incomplete information (missing critical fields, no guessing, no zero assumptions)
Plus:
6. Post-analysis editing and immediate re-analysis
7. Product identification independence (works for 'Unknown Product')
"""
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.food_scanner.ocr_engine import MockOCREngine, set_active_engine
from app.food_scanner.service import run_scan_analysis


def _create_synthetic_image(width=200, height=200, color="white") -> bytes:
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Scenario 1: Clear image with ingredients & nutrition
# ---------------------------------------------------------------------------
SCENARIO_1_OCR = """
Britannia Healthy Digestive
Serving Size: 30g

INGREDIENTS:
Refined Wheat Flour, Sugar (Sucrose), Palm Oil, Cocoa Powder, Skimmed Milk Powder, Salt (Sodium Chloride), Soy Lecithin.

ALLERGEN INFORMATION: CONTAINS WHEAT, MILK, SOY.

NUTRITION FACTS (Per 100g):
Energy: 460 kcal
Total Fat: 18.0g
Saturated Fat: 8.5g
Carbohydrates: 68.0g
Total Sugars: 22.0g
Added Sugars: 18.0g
Dietary Fibre: 4.0g
Protein: 7.0g
Sodium: 320mg
"""


def test_scenario_1_clear_image_full_analysis(client: TestClient):
    mock = MockOCREngine(predefined_text=SCENARIO_1_OCR, confidence=0.95)
    set_active_engine(mock)

    files = [("files", ("label.jpg", _create_synthetic_image(), "image/jpeg"))]
    resp = client.post("/api/products/scan", files=files)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["status"] == "extracted"
    assert "analysis" in data
    analysis = data["analysis"]

    # Product Overview
    assert analysis["product_name"] == "Britannia Healthy Digestive"
    assert analysis["brand"] == "Britannia"

    # Nutrition Scoring
    nutrition = analysis["nutrition_analysis"]
    assert nutrition["is_available"] is True
    assert nutrition["status"] == "complete"
    assert nutrition["score"] is not None
    assert 0 <= nutrition["score"] <= 100
    assert nutrition["grade"] in ["A", "B", "C", "D", "E"]
    assert len(nutrition["positive_factors"]) > 0 or len(nutrition["attention_factors"]) > 0

    # Ingredient Intelligence
    ingredients = analysis["ingredient_intelligence"]
    assert ingredients["is_available"] is True
    assert ingredients["total_count"] >= 5
    assert ingredients["recognized_count"] > 0
    # Wheat flour, palm oil, sugar should be recognized
    rec_names = [it["name"].lower() for it in ingredients["recognized"]]
    assert any("wheat" in n or "flour" in n for n in rec_names)
    assert any("sugar" in n for n in rec_names)

    # Suitability Analysis
    suitability = analysis["suitability_analysis"]
    assert suitability["status"] is not None
    assert suitability["badge_color"] in ["emerald", "amber", "rose", "slate"]

    # Data Quality
    assert analysis["data_quality"]["ocr_confidence"] >= 0.90
    assert analysis["data_quality"]["is_verified"] is False


# ---------------------------------------------------------------------------
# Scenario 2: Image containing ingredients only (no nutrition facts)
# ---------------------------------------------------------------------------
SCENARIO_2_OCR = """
Artisan Bakery Cookies
INGREDIENTS:
Refined Wheat Flour, Sugar (Sucrose), Butter, Skimmed Milk Powder, Vanilla Extract, Salt.
CONTAINS WHEAT, MILK.
"""


def test_scenario_2_ingredients_only(client: TestClient):
    mock = MockOCREngine(predefined_text=SCENARIO_2_OCR, confidence=0.92)
    set_active_engine(mock)

    files = [("files", ("label.jpg", _create_synthetic_image(), "image/jpeg"))]
    resp = client.post("/api/products/scan", files=files)
    assert resp.status_code == 201
    data = resp.json()
    analysis = data["analysis"]

    # Nutrition scoring MUST be marked unavailable, score must NOT be 0 or guessed
    nutrition = analysis["nutrition_analysis"]
    assert nutrition["is_available"] is False
    assert nutrition["score"] is None
    assert nutrition["grade"] is None
    assert "unavailable" in nutrition["message"].lower() or "insufficient" in nutrition["message"].lower()

    # Ingredient analysis MUST work
    ingredients = analysis["ingredient_intelligence"]
    assert ingredients["is_available"] is True
    assert ingredients["total_count"] >= 4
    assert ingredients["recognized_count"] > 0

    # Suitability should evaluate using ingredients & allergens
    suitability = analysis["suitability_analysis"]
    assert suitability["status"] is not None


# ---------------------------------------------------------------------------
# Scenario 3: Image containing nutrition table only (no ingredients)
# ---------------------------------------------------------------------------
SCENARIO_3_OCR = """
Generic Cereal Box
Serving Size: 30g

NUTRITION FACTS (Per 100g):
Energy: 380 kcal
Total Fat: 3.5g
Saturated Fat: 1.0g
Carbohydrates: 78.0g
Total Sugars: 12.0g
Dietary Fibre: 7.0g
Protein: 9.0g
Sodium: 180mg
"""


def test_scenario_3_nutrition_only(client: TestClient):
    mock = MockOCREngine(predefined_text=SCENARIO_3_OCR, confidence=0.91)
    set_active_engine(mock)

    files = [("files", ("label.jpg", _create_synthetic_image(), "image/jpeg"))]
    resp = client.post("/api/products/scan", files=files)
    assert resp.status_code == 201
    data = resp.json()
    analysis = data["analysis"]

    # Nutrition scoring MUST work
    nutrition = analysis["nutrition_analysis"]
    assert nutrition["is_available"] is True
    assert nutrition["status"] == "complete"
    assert nutrition["score"] is not None
    assert 0 <= nutrition["score"] <= 100

    # Ingredient intelligence MUST be explicitly marked unavailable
    ingredients = analysis["ingredient_intelligence"]
    assert ingredients["is_available"] is False
    assert ingredients["total_count"] == 0
    assert "unavailable" in ingredients["message"].lower()

    # Suitability MUST warn about missing ingredients
    suitability = analysis["suitability_analysis"]
    assert suitability["status"] == "Insufficient information"
    assert any("ingredient" in w.lower() for w in suitability["safety_warnings"])


# ---------------------------------------------------------------------------
# Scenario 4: Blurry image (low confidence, noisy OCR, no crash)
# ---------------------------------------------------------------------------
SCENARIO_4_OCR = """
%#@! B!urr7 T3xt
Ingr... Wht Flr??
Nutr: Cal 2??g
"""


def test_scenario_4_blurry_image(client: TestClient):
    mock = MockOCREngine(predefined_text=SCENARIO_4_OCR, confidence=0.35)
    set_active_engine(mock)

    files = [("files", ("blurry.jpg", _create_synthetic_image(), "image/jpeg"))]
    resp = client.post("/api/products/scan", files=files)
    assert resp.status_code == 201
    data = resp.json()

    # Must not crash, should return extracted scan with uncertainty flags
    analysis = data["analysis"]
    data_quality = analysis["data_quality"]
    assert data_quality["ocr_confidence"] < 0.60
    assert len(data_quality["uncertainty_flags"]) > 0

    # Default to Unknown Product if product name cannot be resolved
    assert analysis["product_name"] in ["%#@! B!urr7 T3xt", "Unknown Product"] or len(analysis["product_name"]) > 0


# ---------------------------------------------------------------------------
# Scenario 5: Incomplete nutritional information (missing critical fields)
# ---------------------------------------------------------------------------
SCENARIO_5_OCR = """
Fruit Juice Drink
Serving Size: 200ml

NUTRITION FACTS:
Energy: 55 kcal
Carbohydrates: 13.0g
"""


def test_scenario_5_incomplete_nutrition(client: TestClient):
    mock = MockOCREngine(predefined_text=SCENARIO_5_OCR, confidence=0.88)
    set_active_engine(mock)

    files = [("files", ("label.jpg", _create_synthetic_image(), "image/jpeg"))]
    resp = client.post("/api/products/scan", files=files)
    assert resp.status_code == 201
    data = resp.json()
    analysis = data["analysis"]

    # Critical fields like fat, sugar, protein, sodium are missing
    # Scoring engine MUST NOT fabricate zero values or produce a fake score
    nutrition = analysis["nutrition_analysis"]
    assert nutrition["is_available"] is False
    assert nutrition["status"] == "insufficient_data"
    assert nutrition["score"] is None
    assert nutrition["grade"] is None
    assert len(nutrition["missing_critical_fields"]) > 0


# ---------------------------------------------------------------------------
# Scenario 6: Product name independence (works with missing product name)
# ---------------------------------------------------------------------------
SCENARIO_6_OCR = """
INGREDIENTS:
Sugar (Sucrose), Palm Oil, Salt (Sodium Chloride).

NUTRITION FACTS:
Energy: 500 kcal
Total Fat: 30g
Saturated Fat: 15g
Carbohydrates: 55g
Total Sugars: 40g
Sodium: 200mg
Protein: 2g
Dietary Fibre: 1g
"""


def test_product_identity_independence(client: TestClient):
    mock = MockOCREngine(predefined_text=SCENARIO_6_OCR, confidence=0.90)
    set_active_engine(mock)

    files = [("files", ("label.jpg", _create_synthetic_image(), "image/jpeg"))]
    resp = client.post("/api/products/scan", files=files)
    assert resp.status_code == 201
    data = resp.json()

    analysis = data["analysis"]
    # If no title line was detected, default to "Unknown Product"
    assert analysis["product_name"] == "Unknown Product"
    # Everything else executes independently of product name or barcode!
    assert analysis["nutrition_analysis"]["score"] is not None
    assert analysis["ingredient_intelligence"]["recognized_count"] >= 2


# ---------------------------------------------------------------------------
# Scenario 7: Post-analysis editing and immediate re-analysis
# ---------------------------------------------------------------------------
def test_post_analysis_correction_and_recalculation(client: TestClient):
    # Start with ingredients only
    mock = MockOCREngine(predefined_text=SCENARIO_2_OCR, confidence=0.90)
    set_active_engine(mock)

    files = [("files", ("label.jpg", _create_synthetic_image(), "image/jpeg"))]
    resp = client.post("/api/products/scan", files=files)
    assert resp.status_code == 201
    scan_id = resp.json()["id"]

    # Initial state: nutrition scoring unavailable
    assert resp.json()["analysis"]["nutrition_analysis"]["is_available"] is False

    # User corrects by providing nutrition facts
    correction = {
        "product_name": "Corrected Artisan Cookies",
        "nutrition_facts": {
            "energy_kcal": 420.0,
            "total_fat_g": 16.0,
            "saturated_fat_g": 7.0,
            "carbohydrates_g": 62.0,
            "total_sugar_g": 18.0,
            "dietary_fibre_g": 3.0,
            "protein_g": 6.5,
            "sodium_mg": 280.0,
        },
    }
    put_resp = client.put(f"/api/scans/{scan_id}/correction", json=correction)
    assert put_resp.status_code == 200
    updated_data = put_resp.json()

    # Re-analysis must now be complete with calculated score
    updated_analysis = updated_data["analysis"]
    assert updated_analysis["product_name"] == "Corrected Artisan Cookies"
    assert updated_analysis["nutrition_analysis"]["is_available"] is True
    assert updated_analysis["nutrition_analysis"]["score"] is not None
    assert 0 <= updated_analysis["nutrition_analysis"]["score"] <= 100
