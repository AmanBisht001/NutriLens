"""
NutriLens – Food Journal & Nutrition Analytics Test Suite (Day 8)
Covers:
- Authenticated consumption logging (explicit separation from scanning)
- Proportional nutritional calculations scaled to entered weight
- Honest missing nutrient handling (no assumed zeros)
- Edit and delete journal entries
- User data isolation (cross-user access blocked)
- Daily journal summaries with meal groupings (breakfast, lunch, dinner, snack, other)
- Weekly and monthly longitudinal trend analytics
- Frequently consumed products aggregation
- Non-medical goal progress evaluations and benchmarks
- Empty states handling
"""
import uuid
from datetime import datetime, date, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.seed import seed_database
from app.models.product import Product, NutritionFacts
from app.models.journal import FoodJournalEntry


def register_user(client: TestClient, email: str, goals=None, monitored=None) -> dict:
    """Helper to register and authenticate a test user."""
    payload = {
        "email": email,
        "password": "Password123!",
        "full_name": "Journal Tester",
        "dietary_preference": "None",
        "allergies": [],
        "dietary_restrictions": [],
        "nutrition_goals": goals or [],
    }
    resp = client.post("/api/auth/register", json=payload)
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    user_id = resp.json()["user"]["id"]

    if monitored:
        headers = {"Authorization": f"Bearer {token}"}
        client.put(
            "/api/profile/dietary-preferences",
            headers=headers,
            json={
                "dietary_preference": "None",
                "allergies": [],
                "dietary_restrictions": [],
                "nutrition_goals": goals or [],
                "monitored_nutrients": monitored,
            },
        )

    return {"headers": {"Authorization": f"Bearer {token}"}, "token": token, "user_id": user_id}


def create_test_product(db_session, name: str, category: str = "Snacks", energy: float = 400.0, sugar: float = 20.0, sodium: float = 500.0, protein: float = 10.0, fibre: float = 5.0) -> Product:
    """Helper to create a product with known per-100g nutritional facts."""
    pid = str(uuid.uuid4())
    prod = Product(
        id=pid,
        name=name,
        brand="TestBrand",
        category=category,
        serving_size="50g",
        is_verified=True,
    )
    db_session.add(prod)
    db_session.flush()

    facts = NutritionFacts(
        product_id=pid,
        energy_kcal=energy,
        total_sugar_g=sugar,
        added_sugar_g=sugar * 0.8 if sugar else None,
        total_fat_g=15.0,
        saturated_fat_g=5.0,
        trans_fat_g=None,  # Intentionally undeclared
        carbohydrates_g=55.0,
        dietary_fibre_g=fibre,
        protein_g=protein,
        sodium_mg=sodium,
    )
    db_session.add(facts)
    db_session.commit()
    return prod


# ===========================================================================
# 1. Proportional Nutritional Calculations Tests
# ===========================================================================

def test_create_journal_entry_proportional_scaling(client: TestClient, db_session):
    """Test logging 50g scales per-100g nutritional values to exactly 50%."""
    user = register_user(client, "scaler@example.com")
    prod = create_test_product(db_session, "Crunchy Granola", energy=400.0, sugar=20.0, sodium=500.0, protein=10.0)

    payload = {
        "product_id": prod.id,
        "quantity": 1.0,
        "total_weight_g": 50.0,
        "meal_type": "breakfast",
        "notes": "Morning bowl",
    }
    resp = client.post("/api/journal", headers=user["headers"], json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert data["product_id"] == prod.id
    assert data["total_weight_g"] == 50.0
    assert data["meal_type"] == "breakfast"
    assert data["notes"] == "Morning bowl"

    # Scaled nutrients (50g consumed -> 50% of per-100g)
    nutrients = data["nutrients"]
    assert nutrients["scale_factor"] == 0.5
    assert nutrients["energy_kcal"] == 200.0
    assert nutrients["total_sugar_g"] == 10.0
    assert nutrients["sodium_mg"] == 250.0
    assert nutrients["protein_g"] == 5.0
    assert nutrients["total_fat_g"] == 7.5


def test_serving_size_and_quantity_calculation(client: TestClient, db_session):
    """Test quantity=2 with serving_size_g=30 produces total_weight_g=60g (60% scaling)."""
    user = register_user(client, "servings@example.com")
    prod = create_test_product(db_session, "Oat Biscuits", energy=500.0, sugar=25.0)

    payload = {
        "product_id": prod.id,
        "quantity": 2.0,
        "serving_size_g": 30.0,
        "meal_type": "snack",
    }
    resp = client.post("/api/journal", headers=user["headers"], json=payload)
    assert resp.status_code == 201
    data = resp.json()

    assert data["total_weight_g"] == 60.0
    assert data["nutrients"]["scale_factor"] == 0.6
    assert data["nutrients"]["energy_kcal"] == 300.0
    assert data["nutrients"]["total_sugar_g"] == 15.0


def test_honest_handling_of_missing_nutrients(client: TestClient, db_session):
    """Test undeclared nutrients remain None and are tracked in missing_nutrients."""
    user = register_user(client, "honest@example.com")
    prod = create_test_product(db_session, "Plain Rice Cakes", energy=380.0, sugar=1.0, fibre=None)

    payload = {
        "product_id": prod.id,
        "total_weight_g": 100.0,
    }
    resp = client.post("/api/journal", headers=user["headers"], json=payload)
    assert resp.status_code == 201
    data = resp.json()

    nutrients = data["nutrients"]
    # Trans fat was intentionally None on test product
    assert nutrients["trans_fat_g"] is None
    assert nutrients["dietary_fibre_g"] is None
    assert "Trans Fat" in nutrients["missing_nutrients"]
    assert "Dietary Fibre" in nutrients["missing_nutrients"]


# ===========================================================================
# 2. Edit & Delete Journal Entries
# ===========================================================================

def test_edit_journal_entry(client: TestClient, db_session):
    """Test editing an entry updates weight and recalculates scaled nutrients."""
    user = register_user(client, "editor@example.com")
    prod = create_test_product(db_session, "Almond Milk", energy=60.0, sugar=4.0)

    # Initial log: 100g
    init_resp = client.post(
        "/api/journal",
        headers=user["headers"],
        json={"product_id": prod.id, "total_weight_g": 100.0, "meal_type": "snack"},
    )
    entry_id = init_resp.json()["id"]

    # Update to 200g and meal_type "breakfast"
    put_resp = client.put(
        f"/api/journal/{entry_id}",
        headers=user["headers"],
        json={"total_weight_g": 200.0, "meal_type": "breakfast", "notes": "Big mug"},
    )
    assert put_resp.status_code == 200
    updated = put_resp.json()

    assert updated["total_weight_g"] == 200.0
    assert updated["meal_type"] == "breakfast"
    assert updated["notes"] == "Big mug"
    assert updated["nutrients"]["energy_kcal"] == 120.0
    assert updated["nutrients"]["total_sugar_g"] == 8.0


def test_delete_journal_entry(client: TestClient, db_session):
    """Test deleting an entry removes it from the database."""
    user = register_user(client, "deleter@example.com")
    prod = create_test_product(db_session, "Granola Bar")

    resp = client.post(
        "/api/journal",
        headers=user["headers"],
        json={"product_id": prod.id, "total_weight_g": 40.0},
    )
    entry_id = resp.json()["id"]

    del_resp = client.delete(f"/api/journal/{entry_id}", headers=user["headers"])
    assert del_resp.status_code == 200

    # Attempting to fetch again should return 404
    get_resp = client.get(f"/api/journal/{entry_id}", headers=user["headers"])
    assert get_resp.status_code == 404


# ===========================================================================
# 3. User Data Isolation
# ===========================================================================

def test_user_data_isolation(client: TestClient, db_session):
    """Test User A's entries are strictly protected and invisible to User B."""
    user_a = register_user(client, "user_a@example.com")
    user_b = register_user(client, "user_b@example.com")
    prod = create_test_product(db_session, "Private Food")

    # User A logs an entry
    post_a = client.post(
        "/api/journal",
        headers=user_a["headers"],
        json={"product_id": prod.id, "total_weight_g": 100.0, "notes": "Secret snack"},
    )
    entry_id = post_a.json()["id"]

    # User B cannot access entry by ID
    get_b = client.get(f"/api/journal/{entry_id}", headers=user_b["headers"])
    assert get_b.status_code == 404

    # User B cannot edit User A's entry
    put_b = client.put(f"/api/journal/{entry_id}", headers=user_b["headers"], json={"total_weight_g": 200.0})
    assert put_b.status_code == 404

    # User B cannot delete User A's entry
    del_b = client.delete(f"/api/journal/{entry_id}", headers=user_b["headers"])
    assert del_b.status_code == 404

    # User B's journal list does not contain User A's item
    list_b = client.get("/api/journal", headers=user_b["headers"])
    assert list_b.json()["total"] == 0
    assert len(list_b.json()["items"]) == 0


# ===========================================================================
# 4. Daily Summary & Meal Groupings
# ===========================================================================

def test_daily_journal_summary_and_meal_grouping(client: TestClient, db_session):
    """Test daily summary groups meals correctly and computes total nutrients."""
    user = register_user(client, "daily_summary@example.com")
    prod1 = create_test_product(db_session, "Morning Oats", energy=300.0, sugar=5.0, protein=10.0)
    prod2 = create_test_product(db_session, "Lunch Salad Bowl", energy=200.0, sugar=8.0, protein=6.0)

    today_str = datetime.now(timezone.utc).date().isoformat()

    # Log breakfast and lunch
    client.post(
        "/api/journal",
        headers=user["headers"],
        json={"product_id": prod1.id, "total_weight_g": 100.0, "meal_type": "breakfast"},
    )
    client.post(
        "/api/journal",
        headers=user["headers"],
        json={"product_id": prod2.id, "total_weight_g": 150.0, "meal_type": "lunch"},
    )

    summary_resp = client.get(f"/api/journal/summary/daily?date={today_str}", headers=user["headers"])
    assert summary_resp.status_code == 200
    summary = summary_resp.json()

    assert summary["date"] == today_str
    assert summary["total_entries"] == 2
    assert summary["total_weight_g"] == 250.0

    # Meals check
    meals = summary["meals"]
    assert len(meals["breakfast"]["entries"]) == 1
    assert meals["breakfast"]["total_calories"] == 300.0
    assert len(meals["lunch"]["entries"]) == 1
    assert meals["lunch"]["total_calories"] == 300.0  # 200 * 1.5 = 300.0
    assert len(meals["dinner"]["entries"]) == 0

    # Totals check: total calories = 300 + 300 = 600 kcal
    totals = summary["totals"]
    assert totals["energy_kcal"]["total"] == 600.0
    assert totals["energy_kcal"]["declared_items"] == 2
    assert totals["energy_kcal"]["missing_items"] == 0

    # Disclaimer check
    assert "disclaimer" in summary
    assert "medical advice" in summary["disclaimer"].lower()


# ===========================================================================
# 5. Goal Progress Comparisons (Non-Medical)
# ===========================================================================

def test_goal_progress_comparison(client: TestClient, db_session):
    """Test that configured user nutrition goals generate benchmark progress evaluations."""
    user = register_user(
        client,
        "goal_tracker@example.com",
        goals=["low_sugar", "high_protein"],
    )
    prod = create_test_product(db_session, "Protein Shake", energy=250.0, sugar=15.0, protein=30.0)

    # Log 2 servings (200g) -> Sugar: 30g, Protein: 60g
    client.post(
        "/api/journal",
        headers=user["headers"],
        json={"product_id": prod.id, "total_weight_g": 200.0, "meal_type": "snack"},
    )

    today_str = datetime.now(timezone.utc).date().isoformat()
    resp = client.get(f"/api/journal/summary/daily?date={today_str}", headers=user["headers"])
    assert resp.status_code == 200
    summary = resp.json()

    goal_progress = summary["goal_progress"]
    assert len(goal_progress) >= 2

    sugar_eval = next((g for g in goal_progress if g["goal_key"] == "low_sugar"), None)
    protein_eval = next((g for g in goal_progress if g["goal_key"] == "high_protein"), None)

    assert sugar_eval is not None
    assert sugar_eval["current_value"] == 30.0
    assert sugar_eval["status"] == "on_track"  # <= 50g WHO reference

    assert protein_eval is not None
    assert protein_eval["current_value"] == 60.0
    assert protein_eval["status"] == "on_track"  # >= 50g reference


# ===========================================================================
# 6. Weekly & Monthly Analytics Trends
# ===========================================================================

def test_weekly_analytics_trend(client: TestClient, db_session):
    """Test 7-day weekly analytics aggregates daily trends and averages."""
    user = register_user(client, "weekly_user@example.com")
    prod = create_test_product(db_session, "Daily Snack", energy=200.0, sugar=10.0, sodium=100.0)

    now = datetime.now(timezone.utc)
    # Log one meal today, and one meal 2 days ago
    client.post(
        "/api/journal",
        headers=user["headers"],
        json={
            "product_id": prod.id,
            "total_weight_g": 100.0,
            "consumed_at": now.isoformat(),
        },
    )
    client.post(
        "/api/journal",
        headers=user["headers"],
        json={
            "product_id": prod.id,
            "total_weight_g": 100.0,
            "consumed_at": (now - timedelta(days=2)).isoformat(),
        },
    )

    resp = client.get("/api/journal/analytics/weekly", headers=user["headers"])
    assert resp.status_code == 200
    data = resp.json()

    assert len(data["daily_trends"]) == 7
    assert data["active_days"] == 2
    assert data["total_logged_meals"] == 2
    assert data["averages"]["calories"] is not None
    assert "disclaimer" in data


def test_frequently_consumed_products(client: TestClient, db_session):
    """Test frequently consumed products API returns products ordered by frequency."""
    user = register_user(client, "frequent_user@example.com")
    prod_a = create_test_product(db_session, "Product Alpha")
    prod_b = create_test_product(db_session, "Product Beta")

    # Log Product Alpha 3 times
    for _ in range(3):
        client.post(
            "/api/journal",
            headers=user["headers"],
            json={"product_id": prod_a.id, "total_weight_g": 50.0},
        )

    # Log Product Beta 1 time
    client.post(
        "/api/journal",
        headers=user["headers"],
        json={"product_id": prod_b.id, "total_weight_g": 100.0},
    )

    resp = client.get("/api/journal/analytics/frequent", headers=user["headers"])
    assert resp.status_code == 200
    items = resp.json()["items"]

    assert len(items) == 2
    assert items[0]["product_id"] == prod_a.id
    assert items[0]["log_count"] == 3
    assert items[0]["total_weight_g"] == 150.0
    assert items[1]["product_id"] == prod_b.id
    assert items[1]["log_count"] == 1


# ===========================================================================
# 7. Empty State Handling
# ===========================================================================

def test_empty_journal_states(client: TestClient):
    """Test empty state handling when user has no logged meals."""
    user = register_user(client, "empty_state_user@example.com")

    # List entries
    list_resp = client.get("/api/journal", headers=user["headers"])
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0
    assert list_resp.json()["items"] == []

    # Daily summary
    daily_resp = client.get("/api/journal/summary/daily", headers=user["headers"])
    assert daily_resp.status_code == 200
    assert daily_resp.json()["total_entries"] == 0
    assert daily_resp.json()["total_weight_g"] == 0.0

    # Weekly analytics
    weekly_resp = client.get("/api/journal/analytics/weekly", headers=user["headers"])
    assert weekly_resp.status_code == 200
    assert weekly_resp.json()["active_days"] == 0
    assert weekly_resp.json()["total_logged_meals"] == 0

    # Frequent products
    freq_resp = client.get("/api/journal/analytics/frequent", headers=user["headers"])
    assert freq_resp.status_code == 200
    assert freq_resp.json()["items"] == []
