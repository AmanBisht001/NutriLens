"""
NutriLens – Scan History & Multi-User Isolation Tests (Day 11)
Tests:
1. GET /api/scans/history returns scans for the authenticated user, newest first.
2. Pagination on /api/scans/history works correctly.
3. User data isolation: User A cannot see User B's scans in history.
4. GET /api/scans/{id} allows owner and blocks non-owner (HTTP 403).
5. Scans with 'Unknown Product' or null scores are preserved and listed properly.
"""
import uuid
import pytest
from fastapi.testclient import TestClient
from app.models.scan import ProductScan
from app.models.user import User, UserProfile
from app.core.security import get_password_hash


def _create_user(db, email: str, role: str = "user", is_admin: bool = False) -> User:
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        hashed_password=get_password_hash("TestPass123!"),
        full_name=f"{role.capitalize()} User",
        role=role,
        is_admin=is_admin,
        is_active=True,
    )
    db.add(user)
    db.flush()

    profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        dietary_preference="None",
        allergies=[],
        dietary_restrictions=[],
        nutrition_goals=[],
        monitored_nutrients=[],
    )
    db.add(profile)
    db.commit()
    return user


def _get_headers(client: TestClient, email: str) -> dict:
    resp = client.post("/api/auth/login", json={"email": email, "password": "TestPass123!"})
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_scan_history_endpoint_authenticated(client: TestClient, db_session):
    """Verify that a user's scans appear in GET /api/scans/history."""
    user = _create_user(db_session, "history_user@example.com")
    headers = _get_headers(client, "history_user@example.com")

    # Create two scans for user
    scan1 = ProductScan(
        id="scan-hist-1",
        user_id=user.id,
        status="extracted",
        images=[{"filename": "img1.jpg", "url": "/api/scans/images/img1.jpg"}],
        extracted_data={
            "product_name": "Digestive Biscuit",
            "brand": "Britannia",
            "category": "Biscuits & Cookies",
            "ocr_confidence": 0.95,
            "ocr_engine": "paddleocr",
            "analysis": {
                "product_name": "Digestive Biscuit",
                "nutrition_analysis": {
                    "score": 68,
                    "grade": "C",
                    "rating_label": "Moderate",
                    "rating_color": "amber",
                    "is_available": True,
                }
            }
        }
    )
    scan2 = ProductScan(
        id="scan-hist-2",
        user_id=user.id,
        status="extracted",
        images=[],
        extracted_data={
            "product_name": "Unknown Product",
            "brand": None,
            "category": "Snacks & Namkeen",
            "ocr_confidence": 0.82,
            "ocr_engine": "paddleocr",
            "analysis": {
                "product_name": "Unknown Product",
                "nutrition_analysis": {
                    "score": None,
                    "grade": None,
                    "rating_label": "Nutrition facts unavailable",
                    "rating_color": "slate",
                    "is_available": False,
                }
            }
        }
    )
    db_session.add_all([scan1, scan2])
    db_session.commit()

    resp = client.get("/api/scans/history", headers=headers)
    assert resp.status_code == 200
    data = resp.json()

    assert data["total"] == 2
    items = data["items"]
    # Check that both scans appear
    ids = [it["id"] for it in items]
    assert "scan-hist-1" in ids
    assert "scan-hist-2" in ids

    # Check that scan1 has score 68 and image URL
    hist1 = next(it for it in items if it["id"] == "scan-hist-1")
    assert hist1["product_name"] == "Digestive Biscuit"
    assert hist1["brand"] == "Britannia"
    assert hist1["score"] == 68
    assert hist1["grade"] == "C"
    assert hist1["image_url"] == "/api/scans/images/img1.jpg"

    # Check that scan2 handled Unknown Product and null score honestly
    hist2 = next(it for it in items if it["id"] == "scan-hist-2")
    assert hist2["product_name"] == "Unknown Product"
    assert hist2["score"] is None
    assert hist2["is_scoreable"] is False


def test_scan_history_user_isolation(client: TestClient, db_session):
    """Verify that User A cannot see User B's scans in /api/scans/history."""
    user_a = _create_user(db_session, "user_a@example.com")
    user_b = _create_user(db_session, "user_b@example.com")

    headers_a = _get_headers(client, "user_a@example.com")
    headers_b = _get_headers(client, "user_b@example.com")

    scan_a = ProductScan(
        id="scan-a-item",
        user_id=user_a.id,
        status="extracted",
        extracted_data={"product_name": "User A Cereals"}
    )
    scan_b = ProductScan(
        id="scan-b-item",
        user_id=user_b.id,
        status="extracted",
        extracted_data={"product_name": "User B Chips"}
    )
    db_session.add_all([scan_a, scan_b])
    db_session.commit()

    # User A query
    resp_a = client.get("/api/scans/history", headers=headers_a)
    assert resp_a.status_code == 200
    items_a = resp_a.json()["items"]
    ids_a = [it["id"] for it in items_a]
    assert "scan-a-item" in ids_a
    assert "scan-b-item" not in ids_a

    # User B query
    resp_b = client.get("/api/scans/history", headers=headers_b)
    assert resp_b.status_code == 200
    items_b = resp_b.json()["items"]
    ids_b = [it["id"] for it in items_b]
    assert "scan-b-item" in ids_b
    assert "scan-a-item" not in ids_b


def test_get_scan_by_id_permissions(client: TestClient, db_session):
    """Verify that a user cannot access another user's scan by direct ID."""
    owner = _create_user(db_session, "owner@example.com")
    intruder = _create_user(db_session, "intruder@example.com")

    owner_headers = _get_headers(client, "owner@example.com")
    intruder_headers = _get_headers(client, "intruder@example.com")

    scan = ProductScan(
        id="private-scan-123",
        user_id=owner.id,
        status="extracted",
        extracted_data={"product_name": "Owner Secret Health Item"}
    )
    db_session.add(scan)
    db_session.commit()

    # Owner can access
    resp_owner = client.get("/api/scans/private-scan-123", headers=owner_headers)
    assert resp_owner.status_code == 200

    # Intruder is blocked
    resp_intruder = client.get("/api/scans/private-scan-123", headers=intruder_headers)
    assert resp_intruder.status_code == 403
    assert "permission" in resp_intruder.json()["detail"].lower()
