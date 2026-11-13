"""
NutriLens – Product Comparison & Alternative Recommendation Test Suite (Day 7)
Covers:
- Comparing 2 or more products from the catalogue
- Standardized unit normalization (per 100g / 100ml)
- Preserving missing values as None (never fabricated as zero)
- User priorities evaluation (lower sugar, higher protein, lower sodium, etc.)
- Ingredient & allergen overlap detection
- Personal suitability integration into comparison
- Deterministic alternative recommendation engine
- Category compatibility and traceable explanations
- Safety constraint: never recommending products with declared restriction conflicts
- API endpoints:
  - POST /api/products/compare
  - GET /api/products/{id}/alternatives
"""
import pytest
from fastapi.testclient import TestClient

from app.seed import seed_database
from app.models.product import Product, NutritionFacts


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    """Ensure database has seed data before each test."""
    seed_database(db_session)


# ===========================================================================
# 1. Product Comparison Tests
# ===========================================================================

def test_compare_products_success(client: TestClient, db_session):
    """Test comparing two products returns normalized metrics and scores."""
    # Find two beverages from seed data (Classic Cola and Diet Lemon Tea)
    cola = db_session.query(Product).filter(Product.name.ilike("%Cola%")).first()
    tea = db_session.query(Product).filter(Product.name.ilike("%Diet Lemon Tea%")).first()

    assert cola is not None
    assert tea is not None

    payload = {
        "product_ids": [cola.id, tea.id],
        "priorities": ["lower_sugar", "lower_sodium"],
    }
    resp = client.post("/api/products/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["products"]) == 2
    cola_item = next(p for p in data["products"] if p["product_id"] == cola.id)
    tea_item = next(p for p in data["products"] if p["product_id"] == tea.id)

    # Standardized unit for beverages
    assert cola_item["standard_unit"] == "per_100ml"
    assert tea_item["standard_unit"] == "per_100ml"

    # Normalized nutrient values
    assert cola_item["nutrients_per_100"]["total_sugar_g"] == 39.0
    assert tea_item["nutrients_per_100"]["total_sugar_g"] == 0.0

    # Score comparison
    assert cola_item["score"] is not None
    assert tea_item["score"] is not None
    assert tea_item["score"] > cola_item["score"]

    # Price handling: not declared
    assert cola_item["price"] is None
    assert cola_item["price_display"] == "Not declared"

    # Priorities evaluated
    assert "lower_sugar" in data["priorities_evaluated"]
    sugar_eval = next(e for e in data["priority_evaluations"] if e["priority"] == "lower_sugar")
    assert sugar_eval["best_product_id"] == tea.id
    assert "lowest sugar" in sugar_eval["summary"].lower()


def test_compare_requires_at_least_two_products(client: TestClient, db_session):
    """Validation test: sending fewer than 2 products must fail."""
    tea = db_session.query(Product).filter(Product.name.ilike("%Diet Lemon Tea%")).first()

    resp = client.post("/api/products/compare", json={"product_ids": [tea.id]})
    assert resp.status_code in [400, 422]


def test_compare_with_three_products(client: TestClient, db_session):
    """Test comparing 3 distinct products across categories."""
    prods = db_session.query(Product).limit(3).all()
    p_ids = [p.id for p in prods]

    resp = client.post("/api/products/compare", json={"product_ids": p_ids})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["products"]) == 3
    assert len(data["summary"]) > 0


def test_compare_missing_nutrient_preservation(client: TestClient, db_session):
    """Verify missing nutritional data is preserved as None, never assumed 0."""
    # Create a product with missing fibre and added sugar
    test_prod = Product(
        name="Test Incomplete Biscuit",
        category="Biscuits & Cookies",
        serving_size="30g",
        data_source="manual",
    )
    db_session.add(test_prod)
    db_session.flush()

    nf = NutritionFacts(
        product_id=test_prod.id,
        energy_kcal=400,
        total_fat_g=15,
        saturated_fat_g=5,
        total_sugar_g=20,
        added_sugar_g=None,       # Missing!
        dietary_fibre_g=None,     # Missing!
        protein_g=6,
        sodium_mg=200,
    )
    db_session.add(nf)
    db_session.commit()

    other_prod = db_session.query(Product).filter(Product.id != test_prod.id).first()

    resp = client.post(
        "/api/products/compare",
        json={"product_ids": [test_prod.id, other_prod.id]},
    )
    assert resp.status_code == 200
    data = resp.json()

    item = next(p for p in data["products"] if p["product_id"] == test_prod.id)
    assert item["nutrients_per_100"]["dietary_fibre_g"] is None
    assert item["nutrients_per_100"]["added_sugar_g"] is None
    assert "dietary_fibre_g" in item["missing_nutrients"]
    assert "added_sugar_g" in item["missing_nutrients"]


def test_compare_personal_suitability_integrated(client: TestClient, db_session):
    """Test personal suitability check is integrated into product comparison."""
    # NutriDemo Peanut Butter Crunch Bar contains Peanuts
    peanut_bar = db_session.query(Product).filter(Product.name.ilike("%Peanut Butter%")).first()
    oats = db_session.query(Product).filter(Product.name.ilike("%Oat & Honey%")).first()

    payload = {
        "product_ids": [peanut_bar.id, oats.id],
        "priorities": ["fewer_restriction_conflicts"],
        "user_preferences": {
            "dietary_preference": "None",
            "allergies": ["Peanuts"],
            "dietary_restrictions": [],
            "nutrition_goals": [],
        },
    }
    resp = client.post("/api/products/compare", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    peanut_item = next(p for p in data["products"] if p["product_id"] == peanut_bar.id)
    oats_item = next(p for p in data["products"] if p["product_id"] == oats.id)

    assert peanut_item["suitability_status"] == "Declared restriction conflict"
    assert any("Peanut" in c for c in peanut_item["suitability_conflicts"])

    # Oats does not contain peanuts
    assert oats_item["suitability_status"] != "Declared restriction conflict"

    # Restriction priority highlights oats as winner
    prio_eval = next(e for e in data["priority_evaluations"] if e["priority"] == "fewer_restriction_conflicts")
    assert prio_eval["best_product_id"] == oats.id


def test_compare_ingredient_and_allergen_overlap(client: TestClient, db_session):
    """Test common ingredients and allergens are correctly determined."""
    cola = db_session.query(Product).filter(Product.name.ilike("%Cola%")).first()
    lemon = db_session.query(Product).filter(Product.name.ilike("%Lemon Fizz%")).first()

    resp = client.post("/api/products/compare", json={"product_ids": [cola.id, lemon.id]})
    assert resp.status_code == 200
    data = resp.json()

    # Both contain High Fructose Corn Syrup
    common = [ing.lower() for ing in data["common_ingredients"]]
    assert any("corn syrup" in ing for ing in common)


# ===========================================================================
# 2. Alternative Recommendation Engine Tests
# ===========================================================================

def test_alternatives_endpoint_same_category(client: TestClient, db_session):
    """Test getting alternative recommendations for a high-sugar cola beverage."""
    cola = db_session.query(Product).filter(Product.name.ilike("%Cola%")).first()
    assert cola is not None

    resp = client.get(f"/api/products/{cola.id}/alternatives?limit=3")
    assert resp.status_code == 200
    data = resp.json()

    assert data["target_product_id"] == cola.id
    assert len(data["alternatives"]) > 0

    # Top recommendation for high sugar cola should be Diet Lemon Tea (0g sugar, higher score)
    top_alt = data["alternatives"][0]
    assert "Diet Lemon Tea" in top_alt["name"]
    assert top_alt["score"] > data["target_score"]


def test_alternatives_traceable_explanations(client: TestClient, db_session):
    """Verify alternative recommendations include traceable, deterministic reasons."""
    cola = db_session.query(Product).filter(Product.name.ilike("%Cola%")).first()

    resp = client.get(f"/api/products/{cola.id}/alternatives")
    assert resp.status_code == 200
    data = resp.json()

    top_alt = data["alternatives"][0]
    assert len(top_alt["reasons"]) > 0
    # Must explain score difference or category match
    assert any("Score" in r or "category" in r.lower() or "sugar" in r.lower() for r in top_alt["reasons"])
    assert len(top_alt["nutritional_advantages"]) > 0


def test_alternatives_respects_user_priorities(client: TestClient, db_session):
    """Verify passing user priorities influences recommendation ranking and reasons."""
    biscuits = db_session.query(Product).filter(Product.name.ilike("%Choco Wheat Biscuits%")).first()
    assert biscuits is not None

    resp = client.get(f"/api/products/{biscuits.id}/alternatives?priorities=higher_protein,higher_fibre")
    assert resp.status_code == 200
    data = resp.json()

    assert "higher_protein" in data["applied_priorities"]
    assert "higher_fibre" in data["applied_priorities"]


def test_alternatives_excludes_declared_allergen_conflicts(client: TestClient, db_session):
    """Safety requirement: Alternative engine must never recommend products conflicting with user allergies."""
    # Register user with Peanut allergy
    user_payload = {
        "email": "allergy_recommender@example.com",
        "password": "Password123!",
        "full_name": "Allergy User",
        "dietary_preference": "None",
        "allergies": ["Peanuts"],
        "dietary_restrictions": [],
        "nutrition_goals": [],
    }
    auth_resp = client.post("/api/auth/register", json=user_payload)
    assert auth_resp.status_code == 201
    token = auth_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Request alternatives for biscuits
    biscuits = db_session.query(Product).filter(Product.name.ilike("%Choco Wheat Biscuits%")).first()

    resp = client.get(f"/api/products/{biscuits.id}/alternatives", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    # None of the recommended alternatives should be the Peanut bar!
    for alt in data["alternatives"]:
        assert "Peanut" not in alt["name"]
        assert alt["suitability_status"] != "Declared restriction conflict"


def test_alternatives_nonexistent_product_returns_404(client: TestClient):
    """Verify requesting alternatives for invalid ID returns 404."""
    resp = client.get("/api/products/non-existent-uuid-12345/alternatives")
    assert resp.status_code == 404
