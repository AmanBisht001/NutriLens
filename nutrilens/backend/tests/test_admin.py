"""
NutriLens – Administration & RBAC Test Suite (Day 9)
Covers:
- Strict role-based access control (normal users receive 403 Forbidden on all admin APIs)
- Admin authentication and authorization
- Actual database dashboard statistics (users, products, ingredients, scans, issues)
- Product CRUD, verification, nutrition facts, and mappings
- Canonical ingredient CRUD and allergen registry management
- Scoring rule version management (create, preserve, validate thresholds, activate)
- User-reported data issues & corrections review
"""
import uuid
import pytest
from fastapi.testclient import TestClient

from app.seed import seed_database
from app.models.user import User, UserProfile
from app.models.product import Product, NutritionFacts, Ingredient, Allergen
from app.models.issue import ProductIssue
from app.models.scoring_rules import ScoringRuleVersion
from app.core.security import get_password_hash


def create_user_with_role(db_session, email: str, role: str = "user", is_admin: bool = False) -> User:
    """Helper to create a user with a specific role."""
    uid = str(uuid.uuid4())
    user = User(
        id=uid,
        email=email,
        hashed_password=get_password_hash("Password123!"),
        full_name=f"{role.capitalize()} User",
        role=role,
        is_admin=is_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        dietary_preference="None",
        allergies=[],
        dietary_restrictions=[],
        nutrition_goals=[],
        monitored_nutrients=[],
    )
    db_session.add(profile)
    db_session.commit()
    return user


def get_auth_headers(client: TestClient, email: str, password: str = "Password123!") -> dict:
    """Log in and return Authorization header dict."""
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
def setup_seed(db_session):
    """Seed base allergens and sample products."""
    seed_database(db_session)


# ===========================================================================
# 1. Admin RBAC & Authorization Enforcement
# ===========================================================================

def test_admin_rbac_authorization_enforced(client: TestClient, db_session):
    """Ensure normal users receive 403 Forbidden while admins receive 200 OK."""
    normal_user = create_user_with_role(db_session, "normal_user@example.com", role="user", is_admin=False)
    admin_user = create_user_with_role(db_session, "admin_user@example.com", role="admin", is_admin=True)

    normal_headers = get_auth_headers(client, normal_user.email)
    admin_headers = get_auth_headers(client, admin_user.email)

    # 1. Unauthenticated request -> 401 Unauthorized
    resp_unauth = client.get("/api/admin/dashboard/stats")
    assert resp_unauth.status_code == 401

    # 2. Normal authenticated user -> 403 Forbidden
    resp_normal = client.get("/api/admin/dashboard/stats", headers=normal_headers)
    assert resp_normal.status_code == 403
    assert "Administrative privileges required" in resp_normal.json()["detail"]

    # 3. Admin user -> 200 OK
    resp_admin = client.get("/api/admin/dashboard/stats", headers=admin_headers)
    assert resp_admin.status_code == 200
    data = resp_admin.json()
    assert "total_products" in data
    assert "total_users" in data


def test_normal_user_blocked_from_mutating_admin_endpoints(client: TestClient, db_session):
    """Ensure normal users cannot create products, ingredients, or scoring rules."""
    normal_user = create_user_with_role(db_session, "blocked_user@example.com", role="user", is_admin=False)
    headers = get_auth_headers(client, normal_user.email)

    # Product create
    assert client.post("/api/admin/products", headers=headers, json={"name": "Hacked Product"}).status_code == 403

    # Product update
    assert client.put("/api/admin/products/dummy-id", headers=headers, json={"name": "Hacked"}).status_code == 403

    # Ingredient create
    assert client.post("/api/admin/ingredients", headers=headers, json={"name": "Hacked Ingredient"}).status_code == 403

    # Scoring rule create
    assert client.post("/api/admin/scoring-rules", headers=headers, json={"version": "v99", "name": "Fake"}).status_code == 403


# ===========================================================================
# 2. Dashboard Real Statistics
# ===========================================================================

def test_admin_dashboard_stats_accuracy(client: TestClient, db_session):
    """Ensure dashboard statistics reflect actual database counts."""
    admin = create_user_with_role(db_session, "stats_admin@example.com", role="admin", is_admin=True)
    headers = get_auth_headers(client, admin.email)

    resp = client.get("/api/admin/dashboard/stats", headers=headers)
    assert resp.status_code == 200
    stats = resp.json()

    # Seed data has at least 10 products and 30 ingredients
    assert stats["total_products"] >= 10
    assert stats["total_ingredients"] >= 30
    assert stats["total_users"] >= 1
    assert "active_scoring_rule_version" in stats
    assert len(stats["top_categories"]) > 0


# ===========================================================================
# 3. Product Management (CRUD & Verification)
# ===========================================================================

def test_admin_product_full_crud_and_verification(client: TestClient, db_session):
    """Test admin creating, updating, verifying, and deleting a product."""
    admin = create_user_with_role(db_session, "product_admin@example.com", role="admin", is_admin=True)
    headers = get_auth_headers(client, admin.email)

    # 1. Create Product with Nutrition Facts and Allergen mappings
    create_payload = {
        "name": "Admin Test Protein Bar",
        "brand": "NutriAdmin",
        "category": "Snacks & Namkeen",
        "serving_size": "60g",
        "is_verified": False,
        "nutrition_facts": {
            "energy_kcal": 220.0,
            "protein_g": 20.0,
            "total_fat_g": 7.0,
            "saturated_fat_g": 2.5,
            "carbohydrates_g": 22.0,
            "total_sugar_g": 3.0,
            "sodium_mg": 150.0,
        },
        "ingredient_mappings": [
            {"ingredient_name": "Soy Protein Isolate", "order_index": 1, "percentage": 40.0},
            {"ingredient_name": "Almonds", "order_index": 2, "percentage": 20.0},
        ],
        "allergen_mappings": [
            {"allergen_name": "Soy", "declaration_type": "declared"},
            {"allergen_name": "Tree Nuts", "declaration_type": "declared"},
        ],
    }

    create_resp = client.post("/api/admin/products", headers=headers, json=create_payload)
    assert create_resp.status_code == 201
    prod = create_resp.json()
    prod_id = prod["id"]

    assert prod["name"] == "Admin Test Protein Bar"
    assert prod["is_verified"] is False
    assert prod["nutrition_facts"]["protein_g"] == 20.0
    assert len(prod["product_ingredients"]) == 2
    assert len(prod["product_allergens"]) == 2

    # 2. Update Product
    update_payload = {
        "name": "Admin Test Protein Bar (Updated Formula)",
        "nutrition_facts": {
            "protein_g": 22.0,
        },
    }
    update_resp = client.put(f"/api/admin/products/{prod_id}", headers=headers, json=update_payload)
    assert update_resp.status_code == 200
    updated = update_resp.json()
    assert updated["name"] == "Admin Test Protein Bar (Updated Formula)"
    assert updated["nutrition_facts"]["protein_g"] == 22.0

    # 3. Verify Product
    verify_resp = client.patch(
        f"/api/admin/products/{prod_id}/verify",
        headers=headers,
        json={"is_verified": True, "verification_note": "FSSAI laboratory certificate #12345 verified"},
    )
    assert verify_resp.status_code == 200
    verified = verify_resp.json()
    assert verified["is_verified"] is True
    assert "FSSAI laboratory" in verified["verification_note"]

    # 4. Delete Product
    del_resp = client.delete(f"/api/admin/products/{prod_id}", headers=headers)
    assert del_resp.status_code == 200

    # Check 404
    get_resp = client.get(f"/api/products/{prod_id}")
    assert get_resp.status_code == 404


# ===========================================================================
# 4. Ingredient & Allergen Management
# ===========================================================================

def test_admin_ingredient_crud(client: TestClient, db_session):
    """Test admin adding, updating, and removing canonical ingredients."""
    admin = create_user_with_role(db_session, "ingredient_admin@example.com", role="admin", is_admin=True)
    headers = get_auth_headers(client, admin.email)

    # 1. Create Ingredient
    ing_payload = {
        "name": "Organic Erythritol",
        "category": "sweetener",
        "concern_level": "safe",
        "ins_number": "E968",
        "description": "Zero-calorie sugar alcohol fermented from corn.",
        "aliases": ["erythritol", "sugar alcohol"],
        "is_common_allergen": False,
        "source_reference": "https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2023.8430",
    }
    create_resp = client.post("/api/admin/ingredients", headers=headers, json=ing_payload)
    assert create_resp.status_code == 201
    ing = create_resp.json()
    ing_id = ing["id"]

    assert ing["name"] == "Organic Erythritol"
    assert ing["normalized_name"] == "organic erythritol"
    assert ing["ins_number"] == "E968"

    # Duplicate rejection
    dup_resp = client.post("/api/admin/ingredients", headers=headers, json=ing_payload)
    assert dup_resp.status_code == 400

    # 2. Update Ingredient
    update_resp = client.put(
        f"/api/admin/ingredients/{ing_id}",
        headers=headers,
        json={"concern_level": "moderate", "purpose": "Low-glycemic bulk sweetener"},
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["concern_level"] == "moderate"
    assert update_resp.json()["purpose"] == "Low-glycemic bulk sweetener"

    # 3. Delete Ingredient
    del_resp = client.delete(f"/api/admin/ingredients/{ing_id}", headers=headers)
    assert del_resp.status_code == 200


def test_admin_allergen_management(client: TestClient, db_session):
    """Test admin allergen listing and creation."""
    admin = create_user_with_role(db_session, "allergen_admin@example.com", role="admin", is_admin=True)
    headers = get_auth_headers(client, admin.email)

    # List
    list_resp = client.get("/api/admin/allergens", headers=headers)
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 8

    # Create new allergen
    new_allg = {"name": "Lupin", "code": "EU_14", "description": "Lupin flour allergy"}
    create_resp = client.post("/api/admin/allergens", headers=headers, json=new_allg)
    assert create_resp.status_code == 201
    assert create_resp.json()["name"] == "Lupin"


# ===========================================================================
# 5. Scoring Rule Version Management
# ===========================================================================

def test_admin_scoring_rule_versioning_and_validation(client: TestClient, db_session):
    """Test viewing, creating, validating, and activating scoring rule versions."""
    admin = create_user_with_role(db_session, "scoring_admin@example.com", role="admin", is_admin=True)
    headers = get_auth_headers(client, admin.email)

    # 1. List rules
    list_resp = client.get("/api/admin/scoring-rules", headers=headers)
    assert list_resp.status_code == 200
    rules = list_resp.json()
    assert len(rules) >= 1
    v1 = next((r for r in rules if r["is_active"]), None)
    assert v1 is not None

    # 2. Validation: low < moderate < high failure
    invalid_payload = {
        "version": "nutrilens-score-invalid",
        "name": "Invalid Rules",
        "thresholds_food": {
            "total_sugar_g": {"low": 20.0, "moderate": 10.0, "high": 5.0},  # Backwards!
        },
    }
    inv_resp = client.post("/api/admin/scoring-rules", headers=headers, json=invalid_payload)
    assert inv_resp.status_code == 400

    # 3. Create a valid new version: nutrilens-score-v1.1
    valid_payload = {
        "version": "nutrilens-score-v1.1",
        "name": "NutriLens Revised Sugar & Sodium Model v1.1",
        "description": "Stricter liquid sugar deduction and bonus for whole grain dietary fibre.",
        "is_active": False,
    }
    create_resp = client.post("/api/admin/scoring-rules", headers=headers, json=valid_payload)
    assert create_resp.status_code == 201
    new_v = create_resp.json()
    assert new_v["version"] == "nutrilens-score-v1.1"
    assert new_v["is_active"] is False

    # 4. Activate new version
    act_resp = client.put(f"/api/admin/scoring-rules/{new_v['id']}/activate", headers=headers)
    assert act_resp.status_code == 200
    assert act_resp.json()["is_active"] is True

    # Check that previous version was preserved and deactivated
    v1_recheck = client.get(f"/api/admin/scoring-rules/{v1['id']}", headers=headers)
    assert v1_recheck.status_code == 200
    assert v1_recheck.json()["is_active"] is False


# ===========================================================================
# 6. User-Reported Issue Review Workflow
# ===========================================================================

def test_user_report_and_admin_review_issue(client: TestClient, db_session):
    """Test consumer reporting wrong product info and admin reviewing and resolving it."""
    admin = create_user_with_role(db_session, "issue_admin@example.com", role="admin", is_admin=True)
    consumer = create_user_with_role(db_session, "consumer@example.com", role="user", is_admin=False)

    admin_headers = get_auth_headers(client, admin.email)
    consumer_headers = get_auth_headers(client, consumer.email)

    # Find a product to report
    prod = db_session.query(Product).first()
    assert prod is not None

    # Consumer reports wrong sodium value
    report_payload = {
        "product_id": prod.id,
        "issue_type": "incorrect_nutrition",
        "description": "The sodium on the package is 320mg, but the app shows 500mg.",
        "proposed_correction": {"sodium_mg": 320.0},
    }
    report_resp = client.post("/api/admin/issues", headers=consumer_headers, json=report_payload)
    assert report_resp.status_code == 201
    issue = report_resp.json()
    issue_id = issue["id"]
    assert issue["status"] == "pending"

    # Admin lists pending issues
    list_resp = client.get("/api/admin/issues?status=pending", headers=admin_headers)
    assert list_resp.status_code == 200
    issues = list_resp.json()
    assert any(i["id"] == issue_id for i in issues)

    # Admin reviews and resolves issue
    resolve_payload = {
        "status": "resolved",
        "admin_notes": "Verified against latest package batch photograph. Updated sodium facts.",
    }
    resolve_resp = client.put(f"/api/admin/issues/{issue_id}", headers=admin_headers, json=resolve_payload)
    assert resolve_resp.status_code == 200
    resolved = resolve_resp.json()
    assert resolved["status"] == "resolved"
    assert "Verified against latest package" in resolved["admin_notes"]
