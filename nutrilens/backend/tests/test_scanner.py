"""
NutriLens – Food Scanner Test Suite (Day 4)
Tests:
- Image validation (file size, extension, MIME, corruption)
- Preprocessing (orientation, OpenCV CLAHE and bilateral filtering)
- OCR Engine adapter (Paddle, Fallback, Mock)
- Information extraction pipeline (Brand, Name, Ingredients, Nutrition, Allergens, Uncertainty)
- API Endpoints:
  - POST /api/products/scan
  - GET /api/scans/{id}
  - PUT /api/scans/{id}/correction
  - POST /api/scans/{id}/confirm
  - GET /api/scans/images/{filename}
"""
import io
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from app.food_scanner.preprocessor import (
    validate_image_bytes,
    preprocess_image,
    ImageValidationError,
)
from app.food_scanner.ocr_engine import (
    MockOCREngine,
    FallbackOCREngine,
    set_active_engine,
    get_ocr_engine,
)
from app.food_scanner.extractor import (
    clean_text,
    extract_brand,
    extract_product_name,
    extract_serving_size,
    split_ingredients_list,
    extract_ingredients,
    extract_nutrition_facts,
    extract_allergens,
    extract_structured_label_info,
)


def _create_synthetic_image_bytes(width=200, height=200, format="JPEG", color="white") -> bytes:
    """Helper creating in-memory image bytes for testing."""
    img = Image.new("RGB", (width, height), color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


# ===========================================================================
# 1. Image Preprocessor & Validation Tests
# ===========================================================================

def test_validate_empty_image():
    with pytest.raises(ImageValidationError) as exc:
        validate_image_bytes(b"", "test.jpg", "image/jpeg")
    assert "empty" in exc.value.detail.lower()


def test_validate_oversized_image():
    oversized = b"0" * (11 * 1024 * 1024)  # 11MB
    with pytest.raises(ImageValidationError) as exc:
        validate_image_bytes(oversized, "huge.jpg", "image/jpeg")
    assert "exceeds maximum allowed limit" in exc.value.detail.lower()


def test_validate_unsupported_extension():
    data = _create_synthetic_image_bytes()
    with pytest.raises(ImageValidationError) as exc:
        validate_image_bytes(data, "document.pdf", "image/jpeg")
    assert "unsupported file extension" in exc.value.detail.lower()


def test_validate_unsupported_content_type():
    data = _create_synthetic_image_bytes()
    with pytest.raises(ImageValidationError) as exc:
        validate_image_bytes(data, "test.jpg", "application/pdf")
    assert "unsupported image type" in exc.value.detail.lower()


def test_validate_corrupted_image():
    corrupted = b"this is clearly not an image data file at all"
    with pytest.raises(ImageValidationError) as exc:
        validate_image_bytes(corrupted, "corrupt.jpg", "image/jpeg")
    assert "invalid or corrupted" in exc.value.detail.lower()


def test_preprocess_image_pipeline():
    img_bytes = _create_synthetic_image_bytes(width=120, height=120, color="gray")
    processed_img, meta = preprocess_image(img_bytes, enhance_for_ocr=True)

    assert meta["enhanced"] is True
    assert meta["original_width"] == 120
    assert meta["original_height"] == 120
    assert processed_img.shape == (120, 120)  # Grayscale enhanced image


# ===========================================================================
# 2. OCR Engine Adapter Tests
# ===========================================================================

def test_mock_ocr_engine():
    mock = MockOCREngine(predefined_text="Britannia Good Day\nIngredients: Wheat flour, Butter", confidence=0.92)
    dummy_img = _create_synthetic_image_bytes()
    res = mock.extract_text(dummy_img)

    assert res.engine == "mock"
    assert res.ocr_available is True
    assert res.confidence == 0.92
    assert "Britannia Good Day" in res.raw_text
    assert len(res.lines) == 2


def test_fallback_ocr_engine_no_fabrication():
    fallback = FallbackOCREngine(reason="Test reason")
    dummy_img = _create_synthetic_image_bytes()
    res = fallback.extract_text(dummy_img)

    assert res.engine == "fallback"
    assert res.ocr_available is False
    assert res.raw_text == ""  # Does not fake results
    assert "Test reason" in res.notes


# ===========================================================================
# 3. Information Extractor Pipeline Tests
# ===========================================================================

def test_extract_brand():
    text = "Britannia Marie Gold Biscuits\nManufactured by Britannia Industries"
    brand = extract_brand(text)
    assert brand == "Britannia"


def test_split_ingredients_nested_parentheses():
    raw = "Refined Wheat Flour (Maida), Edible Vegetable Oil (Palm Oil, Antioxidant (E319)), Sugar, Salt"
    items = split_ingredients_list(raw)
    assert len(items) == 4
    assert items[0] == "Refined Wheat Flour (Maida)"
    assert items[1] == "Edible Vegetable Oil (Palm Oil, Antioxidant (E319))"
    assert items[2] == "Sugar"
    assert items[3] == "Salt"


def test_extract_nutrition_facts_parsing():
    sample_text = """
    NUTRITION FACTS
    Per 100g
    Energy: 460 kcal
    Total Fat: 14.5g
    Saturated Fat: 6.5g
    Trans Fat: 0.1g
    Carbohydrates: 75.0g
    Total Sugars: 22.0g
    Added Sugars: 18.0g
    Protein: 7.2g
    Dietary Fibre: 3.5g
    Sodium: 320mg
    """
    facts = extract_nutrition_facts(sample_text)
    assert facts["energy_kcal"] == 460.0
    assert facts["total_fat_g"] == 14.5
    assert facts["saturated_fat_g"] == 6.5
    assert facts["trans_fat_g"] == 0.1
    assert facts["carbohydrates_g"] == 75.0
    assert facts["total_sugar_g"] == 22.0
    assert facts["added_sugar_g"] == 18.0
    assert facts["protein_g"] == 7.2
    assert facts["dietary_fibre_g"] == 3.5
    assert facts["sodium_mg"] == 320.0


def test_extract_allergens_parsing():
    sample_text = """
    ALLERGEN ADVICE: CONTAINS WHEAT, MILK, SOY.
    MAY CONTAIN PEANUTS AND TREE NUTS.
    """
    declared, precautionary = extract_allergens(sample_text)
    assert any("Wheat" in d for d in declared)
    assert any("Milk" in d for d in declared)
    assert any("Soy" in d for d in declared)
    assert any("Peanuts" in p for p in precautionary)
    assert any("Tree nuts" in p for p in precautionary)


def test_extractor_uncertainty_flags():
    # Empty or poor text flags missing fields
    res = extract_structured_label_info("Random blurry text with no nutrients or ingredients", ocr_confidence=0.4)
    assert len(res["uncertainty_flags"]) > 0
    assert res["is_verified"] is False
    assert any("Ingredients list not found" in flag for flag in res["uncertainty_flags"])


# ===========================================================================
# 4. End-to-End API Scanner Tests
# ===========================================================================

SAMPLE_OCR_FIXTURE = """
Britannia NutriChoice Digestive
Serving Size: 2 biscuits (30g)

INGREDIENTS:
Whole Wheat Flour (50%), Edible Vegetable Oil (Palm), Sugar, Wheat Bran (4.5%), Invert Sugar Syrup, Raising Agents (INS 500ii, INS 503ii), Iodised Salt, Emulsifier (INS 322 from Soy).

ALLERGEN INFORMATION: CONTAINS WHEAT AND SOY.
MAY CONTAIN MILK AND NUTS.

NUTRITION FACTS (Per 100g):
Energy: 485 kcal
Total Fat: 21.0g
Saturated Fat: 10.0g
Trans Fat: 0g
Carbohydrates: 66.0g
Total Sugars: 15.0g
Added Sugars: 13.0g
Dietary Fibre: 6.0g
Protein: 8.0g
Sodium: 450mg
"""


def test_api_scan_workflow(client: TestClient):
    # Setup mock OCR engine fixture for test determinism
    mock_engine = MockOCREngine(predefined_text=SAMPLE_OCR_FIXTURE, confidence=0.94)
    set_active_engine(mock_engine)

    # 1. Upload scan image
    img_data = _create_synthetic_image_bytes(width=300, height=300, color="lightyellow")
    files = [
        ("files", ("label.jpg", img_data, "image/jpeg")),
    ]
    data = {
        "label_types": "ingredients",
    }

    resp = client.post("/api/products/scan", files=files, data=data)
    assert resp.status_code == 201, resp.text
    scan_json = resp.json()

    scan_id = scan_json["id"]
    assert scan_json["status"] == "extracted"
    assert len(scan_json["images"]) == 1
    assert "Whole Wheat Flour" in scan_json["raw_ocr_text"]

    extracted = scan_json["extracted_data"]
    assert extracted["brand"] == "Britannia"
    assert len(extracted["ingredients"]) >= 5
    assert extracted["nutrition_facts"]["energy_kcal"] == 485.0
    assert extracted["nutrition_facts"]["protein_g"] == 8.0
    assert any("Wheat" in a for a in extracted["declared_allergens"])

    # 2. GET /api/scans/{id}
    get_resp = client.get(f"/api/scans/{scan_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == scan_id

    # 3. PUT /api/scans/{id}/correction (Manual review & edits)
    correction_payload = {
        "product_name": "Britannia NutriChoice Digestive High Fibre",
        "category": "Biscuits & Cookies",
        "ingredients": [
            "Whole Wheat Flour (50%)",
            "Palm Oil",
            "Sugar",
            "Wheat Bran (4.5%)",
            "Iodised Salt",
        ],
    }
    corr_resp = client.put(f"/api/scans/{scan_id}/correction", json=correction_payload)
    assert corr_resp.status_code == 200
    corr_json = corr_resp.json()
    assert corr_json["status"] == "corrected"
    assert corr_json["corrected_data"]["product_name"] == "Britannia NutriChoice Digestive High Fibre"
    # Extracted data is preserved and distinct from corrected data
    assert corr_json["extracted_data"]["product_name"] != corr_json["corrected_data"]["product_name"]

    # 4. POST /api/scans/{id}/confirm (Commit to catalogue)
    confirm_payload = {
        "product_name": "Britannia NutriChoice Digestive High Fibre",
        "brand": "Britannia",
        "category": "Biscuits & Cookies",
        "serving_size": "2 biscuits (30g)",
        "barcode": "8901063012345",
        "ingredients": [
            "Whole Wheat Flour (50%)",
            "Palm Oil",
            "Sugar",
            "Wheat Bran (4.5%)",
            "Iodised Salt",
        ],
        "raw_ingredients_text": extracted["raw_ingredients_text"],
        "nutrition_facts": {
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
        },
        "declared_allergens": ["Wheat", "Soy"],
        "precautionary_allergens": ["Milk", "Tree nuts"],
    }

    conf_resp = client.post(f"/api/scans/{scan_id}/confirm", json=confirm_payload)
    assert conf_resp.status_code == 201, conf_resp.text
    conf_json = conf_resp.json()
    product_id = conf_json["product_id"]
    assert product_id is not None
    assert conf_json["product"]["name"] == "Britannia NutriChoice Digestive High Fibre"

    # 5. Verify newly created product in catalogue
    prod_resp = client.get(f"/api/products/{product_id}")
    assert prod_resp.status_code == 200
    prod_data = prod_resp.json()
    assert prod_data["name"] == "Britannia NutriChoice Digestive High Fibre"
    assert prod_data["brand"] == "Britannia"
    assert prod_data["data_source"] == "scan"
    assert prod_data["is_verified"] is False
    assert prod_data["nutrition_facts"]["energy_kcal"] == 485.0
    assert len(prod_data["product_ingredients"]) == 5
    assert len(prod_data["product_allergens"]) == 4  # 2 declared + 2 precautionary


def test_api_scan_image_serving(client: TestClient):
    mock_engine = MockOCREngine(predefined_text="Test Front Label", confidence=0.9)
    set_active_engine(mock_engine)

    img_data = _create_synthetic_image_bytes(color="lightblue")
    files = [("files", ("front.jpg", img_data, "image/jpeg"))]
    resp = client.post("/api/products/scan", files=files)
    assert resp.status_code == 201
    scan_json = resp.json()

    saved_url = scan_json["images"][0]["url"]  # /api/scans/images/...
    img_resp = client.get(saved_url)
    assert img_resp.status_code == 200
    assert img_resp.headers["content-type"].startswith("image/")
