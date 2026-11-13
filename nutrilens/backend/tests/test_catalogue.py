"""
Day 3 – Product catalogue and ingredient API tests.
Uses in-memory SQLite and the seed helpers to populate test data.
"""
import pytest
from fastapi.testclient import TestClient
from app.seed import seed_database


@pytest.fixture(autouse=True)
def seed_catalogue(db_session):
    """Seed demo products and ingredients into the test DB for every test in this module."""
    seed_database(db_session)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

class TestCategories:
    def test_list_categories_ok(self, client: TestClient):
        resp = client.get("/api/v1/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert isinstance(data["categories"], list)
        assert len(data["categories"]) > 0

    def test_direct_api_categories(self, client: TestClient):
        resp = client.get("/api/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data

    def test_categories_have_counts(self, client: TestClient):
        resp = client.get("/api/v1/categories")
        for cat in resp.json()["categories"]:
            assert "name" in cat
            assert cat["product_count"] >= 1


# ---------------------------------------------------------------------------
# Products – listing
# ---------------------------------------------------------------------------

class TestProductList:
    def test_list_products_ok(self, client: TestClient):
        resp = client.get("/api/v1/products")
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert data["total"] >= 10
        assert data["page"] == 1

    def test_direct_api_products(self, client: TestClient):
        resp = client.get("/api/products")
        assert resp.status_code == 200
        assert resp.json()["total"] >= 10

    def test_search_by_name(self, client: TestClient):
        resp = client.get("/api/v1/products", params={"search": "NutriDemo Cola"})
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any("Cola" in p["name"] for p in items)

    def test_search_by_brand(self, client: TestClient):
        resp = client.get("/api/v1/products", params={"search": "NutriDemo"})
        assert resp.status_code == 200
        assert resp.json()["total"] >= 10

    def test_filter_by_category(self, client: TestClient):
        resp = client.get("/api/v1/products", params={"category": "Beverages"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 3
        for item in data["items"]:
            assert item["category"] == "Beverages"

    def test_pagination(self, client: TestClient):
        resp1 = client.get("/api/v1/products", params={"page": 1, "page_size": 3})
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert len(d1["items"]) == 3
        assert d1["page"] == 1

        resp2 = client.get("/api/v1/products", params={"page": 2, "page_size": 3})
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["page"] == 2
        # Pages should not overlap
        ids1 = {p["id"] for p in d1["items"]}
        ids2 = {p["id"] for p in d2["items"]}
        assert ids1.isdisjoint(ids2)

    def test_empty_search_returns_no_results(self, client: TestClient):
        resp = client.get("/api/v1/products", params={"search": "ZZZNOTEXIST999"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_demo_data_flagged(self, client: TestClient):
        resp = client.get("/api/v1/products")
        for item in resp.json()["items"]:
            assert item["is_demo_data"] is True

    def test_nutrition_facts_in_summary(self, client: TestClient):
        resp = client.get("/api/v1/products")
        for item in resp.json()["items"]:
            assert item["nutrition_facts"] is not None
            assert "energy_kcal" in item["nutrition_facts"]
            assert item["nutrition_facts"]["is_illustrative"] is True


# ---------------------------------------------------------------------------
# Products – detail
# ---------------------------------------------------------------------------

class TestProductDetail:
    def _get_first_product_id(self, client: TestClient) -> str:
        resp = client.get("/api/v1/products")
        return resp.json()["items"][0]["id"]

    def test_get_product_detail_ok(self, client: TestClient):
        pid = self._get_first_product_id(client)
        resp = client.get(f"/api/v1/products/{pid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == pid
        assert "product_ingredients" in data
        assert "product_allergens" in data
        assert "raw_ingredients_text" in data

    def test_product_has_ingredient_list(self, client: TestClient):
        # Find the choco biscuits (has known ingredients)
        resp = client.get("/api/v1/products", params={"search": "Choco Wheat Biscuits"})
        pid = resp.json()["items"][0]["id"]
        detail = client.get(f"/api/v1/products/{pid}").json()
        assert len(detail["product_ingredients"]) >= 1
        for pi in detail["product_ingredients"]:
            assert "ingredient" in pi
            assert "name" in pi["ingredient"]
            assert "concern_level" in pi["ingredient"]

    def test_product_has_allergens(self, client: TestClient):
        resp = client.get("/api/v1/products", params={"search": "Choco Wheat Biscuits"})
        pid = resp.json()["items"][0]["id"]
        detail = client.get(f"/api/v1/products/{pid}").json()
        allergens = detail["product_allergens"]
        assert len(allergens) >= 1
        allergen_names = [a["allergen"]["name"] for a in allergens]
        assert "Gluten / Wheat" in allergen_names

    def test_product_not_found(self, client: TestClient):
        resp = client.get("/api/v1/products/nonexistent-id-9999")
        assert resp.status_code == 404

    def test_product_nutrition_is_illustrative(self, client: TestClient):
        pid = self._get_first_product_id(client)
        detail = client.get(f"/api/v1/products/{pid}").json()
        assert detail["nutrition_facts"]["is_illustrative"] is True


# ---------------------------------------------------------------------------
# Ingredients
# ---------------------------------------------------------------------------

class TestIngredients:
    def test_list_ingredients_ok(self, client: TestClient):
        resp = client.get("/api/v1/ingredients")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 30
        assert isinstance(data["items"], list)

    def test_search_ingredient_by_name(self, client: TestClient):
        resp = client.get("/api/v1/ingredients", params={"search": "Aspartame"})
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any("Aspartame" in i["name"] for i in items)

    def test_search_ingredient_by_ins_number(self, client: TestClient):
        resp = client.get("/api/v1/ingredients", params={"search": "E211"})
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert any(i["ins_number"] == "E211" for i in items)

    def test_filter_by_category(self, client: TestClient):
        resp = client.get("/api/v1/ingredients", params={"category": "preservative"})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["category"] == "preservative"

    def test_filter_by_concern_level(self, client: TestClient):
        resp = client.get("/api/v1/ingredients", params={"concern_level": "high"})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["concern_level"] == "high"

    def test_get_ingredient_detail_ok(self, client: TestClient):
        list_resp = client.get("/api/v1/ingredients", params={"search": "Sodium Benzoate"})
        iid = list_resp.json()["items"][0]["id"]
        resp = client.get(f"/api/v1/ingredients/{iid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Sodium Benzoate"
        assert data["ins_number"] == "E211"
        assert data["concern_level"] == "moderate"
        assert data["description"] is not None

    def test_ingredient_not_found(self, client: TestClient):
        resp = client.get("/api/v1/ingredients/nonexistent-999")
        assert resp.status_code == 404

    def test_ingredients_pagination(self, client: TestClient):
        r1 = client.get("/api/v1/ingredients", params={"page": 1, "page_size": 10})
        r2 = client.get("/api/v1/ingredients", params={"page": 2, "page_size": 10})
        ids1 = {i["id"] for i in r1.json()["items"]}
        ids2 = {i["id"] for i in r2.json()["items"]}
        assert ids1.isdisjoint(ids2)
