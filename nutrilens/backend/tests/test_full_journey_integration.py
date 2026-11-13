"""
NutriLens – Day 10 Comprehensive Full User Journey End-to-End Integration Test
Verifies the complete 14-step user journey across all integrated subsystems:
1. User registers
2. User logs in
3. User configures dietary preferences
4. User scans a packaged food label
5. OCR extracts product information
6. User corrects and confirms extracted information
7. Product information is saved to catalogue
8. Nutrition score is calculated
9. Personalized suitability is evaluated
10. User compares products
11. Alternative products are recommended
12. User explicitly logs consumed products
13. Analytics display actual logged consumption
14. Admin manages product and ingredient information
"""
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.food_scanner.ocr_engine import MockOCREngine, set_active_engine
from app.models.user import User
from app.core.security import get_password_hash


def _create_synthetic_image_bytes(width=150, height=150, format="JPEG") -> bytes:
    img = Image.new("RGB", (width, height), color="lightgreen")
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


MOCK_LABEL_OCR = """
BRAND: OrganoHarvest
PRODUCT: Organic Crunchy Oat Clusters
SERVING SIZE: 1 bowl (40g)

NUTRITION FACTS (Per 100g):
Energy: 420 kcal
Total Fat: 12.0 g
Saturated Fat: 2.5 g
Trans Fat: 0.0 g
Carbohydrates: 68.0 g
Total Sugar: 11.0 g
Added Sugar: 8.0 g
Dietary Fibre: 8.5 g
Protein: 10.5 g
Sodium: 180 mg

INGREDIENTS:
Rolled Whole Oats (65%), Raw Honey, Cold Pressed Sunflower Oil,
Flax Seeds (5%), Chia Seeds (3%), Cinnamon Powder, Sea Salt.

ALLERGEN DECLARATIONS:
Contains: Oats (Gluten).
May Contain: Almonds, Peanuts, Milk.
"""


def test_complete_14_step_user_journey(client: TestClient, db_session):
    # Setup OCR Mock Engine
    mock_engine = MockOCREngine(predefined_text=MOCK_LABEL_OCR, confidence=0.92)
    set_active_engine(mock_engine)

    # Pre-seed Admin User
    admin = User(
        email="admin_journey@nutrilens.com",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin Director",
        role="admin",
        is_admin=True,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()

    # =========================================================================
    # STEP 1: User Registers
    # =========================================================================
    user_email = "consumer_journey@nutrilens.com"
    user_pass = "ConsumerSecure2026!"
    reg_resp = client.post(
        "/api/auth/register",
        json={
            "email": user_email,
            "password": user_pass,
            "full_name": "Aarav Sharma",
            "age": 29,
            "dietary_preference": "Vegetarian",
            "allergies": ["Peanuts"],
            "dietary_restrictions": ["No Artificial Colors"],
            "nutrition_goals": ["Low Sugar", "High Fibre"],
        },
    )
    assert reg_resp.status_code == 201, reg_resp.text
    reg_data = reg_resp.json()
    assert reg_data["user"]["email"] == user_email
    assert reg_data["user"]["full_name"] == "Aarav Sharma"
    user_token = reg_data["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}

    # =========================================================================
    # STEP 2: User Logs In
    # =========================================================================
    login_resp = client.post(
        "/api/auth/login",
        json={"email": user_email, "password": user_pass},
    )
    assert login_resp.status_code == 200
    login_token = login_resp.json()["access_token"]
    assert login_token is not None
    user_headers = {"Authorization": f"Bearer {login_token}"}

    # =========================================================================
    # STEP 3: User Configures Dietary Preferences
    # =========================================================================
    pref_update_resp = client.put(
        "/api/profile/dietary-preferences",
        headers=user_headers,
        json={
            "dietary_preference": "Vegetarian",
            "allergies": ["Peanuts"],
            "dietary_restrictions": ["No Artificial Colors"],
            "nutrition_goals": ["Low Sugar", "High Fibre"],
            "monitored_nutrients": ["total_sugar", "sodium"],
        },
    )
    assert pref_update_resp.status_code == 200
    prefs = pref_update_resp.json()
    assert "Peanuts" in prefs["allergies"]
    assert "total_sugar" in prefs["monitored_nutrients"]

    # =========================================================================
    # STEP 4: User Scans a Packaged Food Label
    # =========================================================================
    img_bytes = _create_synthetic_image_bytes()
    files = [("files", ("oats_label.jpg", img_bytes, "image/jpeg"))]
    scan_resp = client.post("/api/products/scan", headers=user_headers, files=files)
    assert scan_resp.status_code == 201
    scan_data = scan_resp.json()
    scan_id = scan_data["id"]
    assert scan_id is not None

    # =========================================================================
    # STEP 5: OCR Extracts Product Information
    # =========================================================================
    assert scan_data["status"] == "extracted"
    extracted = scan_data["extracted_data"]
    assert extracted["brand"] == "OrganoHarvest"
    assert "Rolled Whole Oats" in extracted["raw_ingredients_text"]
    assert extracted["nutrition_facts"]["energy_kcal"] == 420.0
    assert extracted["nutrition_facts"]["dietary_fibre_g"] == 8.5
    assert extracted["nutrition_facts"]["protein_g"] == 10.5

    # =========================================================================
    # STEP 6: User Corrects Extracted Information
    # =========================================================================
    correction_payload = {
        "product_name": "OrganoHarvest Crunchy Oat Clusters Deluxe",
        "category": "Breakfast Cereals",
        "ingredients": [
            "Rolled Whole Oats (65%)",
            "Raw Honey",
            "Sunflower Oil",
            "Flax Seeds",
            "Chia Seeds",
            "Cinnamon Powder",
            "Sea Salt",
        ],
    }
    corr_resp = client.put(
        f"/api/scans/{scan_id}/correction",
        headers=user_headers,
        json=correction_payload,
    )
    assert corr_resp.status_code == 200
    assert corr_resp.json()["status"] == "corrected"
    assert corr_resp.json()["corrected_data"]["product_name"] == "OrganoHarvest Crunchy Oat Clusters Deluxe"

    # =========================================================================
    # STEP 7: Product Information Is Saved to Catalogue
    # =========================================================================
    confirm_payload = {
        "product_name": "OrganoHarvest Crunchy Oat Clusters Deluxe",
        "brand": "OrganoHarvest",
        "category": "Breakfast Cereals",
        "serving_size": "40g",
        "barcode": "8908877665544",
        "ingredients": [
            "Rolled Whole Oats",
            "Raw Honey",
            "Sunflower Oil",
            "Flax Seeds",
            "Chia Seeds",
            "Cinnamon Powder",
            "Sea Salt",
        ],
        "raw_ingredients_text": extracted["raw_ingredients_text"],
        "nutrition_facts": {
            "energy_kcal": 420.0,
            "total_fat_g": 12.0,
            "saturated_fat_g": 2.5,
            "trans_fat_g": 0.0,
            "carbohydrates_g": 68.0,
            "total_sugar_g": 11.0,
            "added_sugar_g": 8.0,
            "dietary_fibre_g": 8.5,
            "protein_g": 10.5,
            "sodium_mg": 180.0,
        },
        "declared_allergens": ["Gluten"],
        "precautionary_allergens": ["Tree nuts", "Milk"],
    }
    conf_resp = client.post(
        f"/api/scans/{scan_id}/confirm",
        headers=user_headers,
        json=confirm_payload,
    )
    assert conf_resp.status_code == 201
    confirmed_product = conf_resp.json()["product"]
    product_id = confirmed_product["id"]
    assert product_id is not None

    # Verify saved in catalogue
    cat_resp = client.get(f"/api/products/{product_id}")
    assert cat_resp.status_code == 200
    assert cat_resp.json()["name"] == "OrganoHarvest Crunchy Oat Clusters Deluxe"

    # =========================================================================
    # STEP 8: Nutrition Score Is Calculated
    # =========================================================================
    score_resp = client.get(f"/api/products/{product_id}/analysis")
    assert score_resp.status_code == 200
    analysis = score_resp.json()
    assert analysis["status"] == "complete"
    assert 0 <= analysis["score"] <= 100
    assert analysis["grade"] in ["A", "B", "C", "D", "E"]
    assert "nutrilens-score" in analysis["scoring_rule_version"]
    assert len(analysis["positive_factors"]) > 0

    # =========================================================================
    # STEP 9: Personalized Suitability Is Evaluated
    # =========================================================================
    suit_resp = client.post(
        f"/api/products/{product_id}/suitability",
        headers=user_headers,
        json={},
    )
    assert suit_resp.status_code == 200
    suit_data = suit_resp.json()
    # User has allergy to Peanuts and Vegetarian; product is vegetarian with Oats
    assert suit_data["status"] in [
        "Suitable based on available information",
        "Caution",
    ]
    assert len(suit_data["safety_warnings"]) > 0
    assert "medical" in suit_data["disclaimer"].lower()

    # =========================================================================
    # STEP 10: User Compares Products
    # =========================================================================
    # Create a 2nd product to compare against
    p2_resp = client.post(
        "/api/products/scan",
        headers=user_headers,
        files=[("files", ("cornflakes.jpg", img_bytes, "image/jpeg"))],
    )
    p2_scan_id = p2_resp.json()["id"]
    client.post(
        f"/api/scans/{p2_scan_id}/confirm",
        headers=user_headers,
        json={
            "product_name": "Standard Corn Flakes",
            "brand": "CerealCo",
            "category": "Breakfast Cereals",
            "serving_size": "30g",
            "barcode": "8901122334455",
            "ingredients": ["Corn", "Sugar", "Malt Extract", "Salt"],
            "nutrition_facts": {
                "energy_kcal": 380.0,
                "total_fat_g": 1.0,
                "saturated_fat_g": 0.2,
                "trans_fat_g": 0.0,
                "carbohydrates_g": 85.0,
                "total_sugar_g": 24.0,
                "added_sugar_g": 20.0,
                "dietary_fibre_g": 1.5,
                "protein_g": 6.0,
                "sodium_mg": 700.0,
            },
            "declared_allergens": ["Gluten"],
            "precautionary_allergens": [],
        },
    )
    # Get product 2 id
    p2_search = client.get("/api/products?search=Standard+Corn+Flakes").json()
    product_2_id = p2_search["items"][0]["id"]

    compare_resp = client.post(
        "/api/products/compare",
        headers=user_headers,
        json={
            "product_ids": [product_id, product_2_id],
            "priorities": ["lower_sugar", "higher_fibre", "lower_sodium"],
        },
    )
    assert compare_resp.status_code == 200
    compare_data = compare_resp.json()
    assert len(compare_data["products"]) == 2
    assert "priority_evaluations" in compare_data
    assert len(compare_data["priority_evaluations"]) >= 3

    # =========================================================================
    # STEP 11: Alternative Products Are Recommended
    # =========================================================================
    # Request alternatives for Corn Flakes (which has high sugar and low fibre)
    alt_resp = client.get(
        f"/api/products/{product_2_id}/alternatives",
        headers=user_headers,
    )
    assert alt_resp.status_code == 200
    alt_data = alt_resp.json()
    assert "alternatives" in alt_data
    # Oat clusters has lower sugar (11g vs 24g) and higher fibre (8.5g vs 1.5g)
    alt_ids = [a["product_id"] for a in alt_data["alternatives"]]
    assert product_id in alt_ids
    # Check traceable reasons
    matched_alt = next(a for a in alt_data["alternatives"] if a["product_id"] == product_id)
    assert len(matched_alt["reasons"]) > 0

    # =========================================================================
    # STEP 12: User Explicitly Logs Consumed Products
    # =========================================================================
    # Log 80g of the Oat Clusters (2 servings of 40g)
    journal_log_resp = client.post(
        "/api/journal",
        headers=user_headers,
        json={
            "product_id": product_id,
            "meal_type": "breakfast",
            "quantity": 2.0,
            "serving_size_g": 40.0,
            "total_weight_g": 80.0,
            "consumed_at": "2026-11-13T08:30:00Z",
            "notes": "Enjoyed with almond milk",
        },
    )
    assert journal_log_resp.status_code == 201, journal_log_resp.text
    log_data = journal_log_resp.json()
    assert log_data["total_weight_g"] == 80.0
    # Nutrient scaling verification: 80g is 80% of per-100g values
    # Energy: 420 * 0.8 = 336 kcal
    assert log_data["nutrients"]["energy_kcal"] == pytest.approx(336.0, rel=1e-2)
    # Protein: 10.5 * 0.8 = 8.4 g
    assert log_data["nutrients"]["protein_g"] == pytest.approx(8.4, rel=1e-2)

    # =========================================================================
    # STEP 13: Analytics Display Actual Logged Consumption
    # =========================================================================
    # 13a. Daily summary
    daily_resp = client.get(
        "/api/journal/summary/daily?date=2026-11-13",
        headers=user_headers,
    )
    assert daily_resp.status_code == 200
    daily_data = daily_resp.json()
    assert daily_data["total_entries"] == 1
    assert "breakfast" in daily_data["meals"]
    assert daily_data["totals"]["energy_kcal"]["total"] == pytest.approx(336.0, rel=1e-2)
    assert len(daily_data["goal_progress"]) > 0

    # 13b. Weekly trends
    weekly_resp = client.get(
        "/api/journal/analytics/weekly?end_date=2026-11-13",
        headers=user_headers,
    )
    assert weekly_resp.status_code == 200
    weekly_data = weekly_resp.json()
    assert len(weekly_data["daily_trends"]) == 7
    assert weekly_data["total_logged_meals"] >= 1

    # 13c. Monthly trends
    monthly_resp = client.get(
        "/api/journal/analytics/monthly?year=2026&month=11",
        headers=user_headers,
    )
    assert monthly_resp.status_code == 200
    assert monthly_resp.json()["total_logged_meals"] >= 1

    # 13d. Frequent products
    frequent_resp = client.get(
        "/api/journal/analytics/frequent",
        headers=user_headers,
    )
    assert frequent_resp.status_code == 200
    freq_items = frequent_resp.json()["items"]
    assert len(freq_items) >= 1
    assert freq_items[0]["product_id"] == product_id

    # =========================================================================
    # STEP 14: Admin Manages Product and Ingredient Information
    # =========================================================================
    # 14a. Non-admin blocked
    blocked_resp = client.get("/api/admin/dashboard/stats", headers=user_headers)
    assert blocked_resp.status_code == 403

    # 14b. Admin logs in
    admin_login = client.post(
        "/api/auth/login",
        json={"email": "admin_journey@nutrilens.com", "password": "AdminPass123!"},
    )
    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 14c. Admin checks stats
    stats_resp = client.get("/api/admin/dashboard/stats", headers=admin_headers)
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    assert stats["total_products"] >= 2
    assert stats["total_scans"] >= 2

    # 14d. Admin verifies the scanned product
    verify_resp = client.patch(
        f"/api/admin/products/{product_id}/verify",
        headers=admin_headers,
        json={"is_verified": True},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["is_verified"] is True

    # 14e. Admin manages ingredient taxonomy
    ingr_resp = client.post(
        "/api/admin/ingredients",
        headers=admin_headers,
        json={
            "name": "Organic Golden Flaxseed",
            "category": "Seeds & Grains",
            "description": "Rich in alpha-linolenic acid (ALA) omega-3 fatty acids.",
            "concern_level": "low",
            "is_additive": False,
            "aliases": ["Linum usitatissimum", "Flax"],
        },
    )
    assert ingr_resp.status_code == 201

    # 14f. Consumer reports an issue on product
    report_resp = client.post(
        f"/api/products/{product_id}/report-issue",
        headers=user_headers,
        json={
            "issue_type": "inaccurate_nutrition",
            "description": "Sodium content on packaging claims 150mg instead of 180mg.",
        },
    )
    assert report_resp.status_code == 201
    issue_id = report_resp.json()["issue_id"]

    # 14g. Admin reviews and resolves issue
    admin_issues = client.get("/api/admin/issues?status=pending", headers=admin_headers)
    assert admin_issues.status_code == 200
    assert any(i["id"] == issue_id for i in admin_issues.json())

    resolve_resp = client.put(
        f"/api/admin/issues/{issue_id}",
        headers=admin_headers,
        json={
            "status": "resolved",
            "admin_notes": "Cross-verified with updated packaging batch #2026B; verified record.",
        },
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "resolved"
