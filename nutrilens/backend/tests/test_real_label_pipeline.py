"""
NutriLens – Integration Tests on Real Packaged Food Label Images (Day 11)
Tests:
1. Real nutrition facts image inference with PaddleOCR
2. Information extraction from real label OCR tokens
3. Unit normalization and accurate nutrient parsing
4. Deterministic NutriLens score calculation from real label values
5. Image blur and quality assessment
6. Multimodal vision schema compliance and fallback structure
"""
import os
import pytest
import numpy as np
import cv2
from app.food_scanner.ocr_engine import PaddleOCREngine
from app.food_scanner.preprocessor import preprocess_image, assess_image_quality
from app.food_scanner.extractor import extract_structured_label_info, extract_serving_size
from app.food_scanner.vision_extractor import EXTRACTION_PROMPT, _clean_json_response
from app.scoring_engine.service import analyze_nutrition_payload

REAL_IMAGE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "app", "uploads", "scans", "bb0b435f-91e4-4543-99ec-32592bd94dcd_0_other.png"
)


def test_real_food_label_paddleocr_inference():
    """Verify that PaddleOCR successfully reads the real food label image."""
    if not os.path.exists(REAL_IMAGE_PATH):
        pytest.skip(f"Test image not found at {REAL_IMAGE_PATH}")

    engine = PaddleOCREngine()
    with open(REAL_IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    ocr_res = engine.extract_text(img_bytes)
    assert ocr_res.ocr_available is True
    assert ocr_res.engine == "paddleocr"
    assert len(ocr_res.lines) > 10
    assert ocr_res.confidence > 0.80

    # Ensure key label tokens are detected
    raw_lower = ocr_res.raw_text.lower()
    assert "nutrition" in raw_lower
    assert "energy" in raw_lower
    assert "protein" in raw_lower
    assert "fat" in raw_lower


def test_real_food_label_extraction_and_scoring():
    """Verify that text from real label parses nutrients and computes score."""
    if not os.path.exists(REAL_IMAGE_PATH):
        pytest.skip(f"Test image not found at {REAL_IMAGE_PATH}")

    engine = PaddleOCREngine()
    with open(REAL_IMAGE_PATH, "rb") as f:
        img_bytes = f.read()

    preprocessed_img, meta = preprocess_image(img_bytes, enhance_for_ocr=True)
    ocr_res = engine.extract_text(preprocessed_img)

    parsed = extract_structured_label_info(
        raw_ocr_text=ocr_res.raw_text,
        ocr_confidence=ocr_res.confidence,
        ocr_engine="paddleocr",
    )

    # Verify extracted nutrients
    facts = parsed["nutrition_facts"]
    assert facts["energy_kcal"] == 554.0
    assert facts["total_fat_g"] == 33.4
    assert facts["saturated_fat_g"] == 15.1
    assert facts["trans_fat_g"] == 0.1
    assert facts["carbohydrates_g"] == 57.5
    assert facts["total_sugar_g"] == 1.4
    assert facts["added_sugar_g"] == 0.8
    assert facts["protein_g"] == 6.0
    assert facts["sodium_mg"] == 694.0

    # Verify serving size
    assert parsed["serving_size"] == "20g"

    # Verify scoring
    analysis = analyze_nutrition_payload(
        nutrients_per_100=facts,
        category="Snacks & Namkeen",
        serving_size_str=parsed["serving_size"],
    )
    assert analysis["status"] == "complete"
    assert analysis["score"] is not None
    assert 0 <= analysis["score"] <= 100
    assert analysis["grade"] == "E"
    assert len(analysis["attention_factors"]) > 0


def test_blur_assessment_synthetic():
    """Verify blur detection on clear vs blurred images."""
    clear_img = np.zeros((200, 200, 3), dtype=np.uint8)
    # Add sharp high-frequency edges
    cv2.putText(clear_img, "SHARP TEXT 123", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
    clear_quality = assess_image_quality(clear_img)
    assert clear_quality["is_blurry"] is False

    # Heavy blur
    blurred_img = cv2.GaussianBlur(clear_img, (25, 25), 0)
    blurred_quality = assess_image_quality(blurred_img)
    assert blurred_quality["is_blurry"] is True
    assert blurred_quality["quality_warning"] is not None


def test_vision_schema_cleaner():
    """Verify that vision LLM JSON response parser handles code fences."""
    raw_markdown = '```json\n{"product_name": "Test Oats", "nutrition_facts": {"energy_kcal": 380}}\n```'
    parsed = _clean_json_response(raw_markdown)
    assert parsed is not None
    assert parsed["product_name"] == "Test Oats"
    assert parsed["nutrition_facts"]["energy_kcal"] == 380
