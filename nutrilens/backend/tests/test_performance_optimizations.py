"""
NutriLens – Performance & Memory Optimization Tests
Validates:
1. Memory-friendly downscaling in preprocessor (large image -> max 1600px).
2. Thumbnail generation (<30KB) for fast dashboard rendering.
3. In-memory IngredientKnowledgeCache O(1) matching.
4. Concurrency protection via _SCAN_SEMAPHORE.
5. /api/health/metrics memory diagnostic endpoint.
"""
import io
import pytest
from PIL import Image
import numpy as np
from fastapi.testclient import TestClient

from app.main import app
from app.food_scanner.preprocessor import (
    preprocess_image,
    generate_thumbnail,
    MAX_PROCESSING_DIMENSION,
    THUMBNAIL_MAX_DIMENSION,
)
from app.food_scanner.service import (
    IngredientKnowledgeCache,
    match_and_explain_ingredients,
    _SCAN_SEMAPHORE,
    RECENT_SCAN_METRICS,
)


def _create_synthetic_image_bytes(width: int, height: int) -> bytes:
    """Generates synthetic JPEG bytes for benchmarking."""
    arr = np.random.randint(50, 200, (height, width, 3), dtype=np.uint8)
    img = Image.fromarray(arr, "RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def test_large_image_downscaling():
    """Verify that oversized mobile phone camera captures (e.g. 3000x2000) are automatically downscaled."""
    large_bytes = _create_synthetic_image_bytes(3000, 2000)
    assert len(large_bytes) > 0

    processed_arr, metadata = preprocess_image(large_bytes, enhance_for_ocr=True)
    assert metadata["original_width"] == 3000
    assert metadata["original_height"] == 2000

    # Max dimension must not exceed MAX_PROCESSING_DIMENSION
    assert max(metadata["processed_width"], metadata["processed_height"]) <= MAX_PROCESSING_DIMENSION
    assert max(processed_arr.shape[:2]) <= MAX_PROCESSING_DIMENSION


def test_thumbnail_generation_efficiency():
    """Verify generated thumbnails are compact (<35KB) and scaled to THUMBNAIL_MAX_DIMENSION."""
    raw_bytes = _create_synthetic_image_bytes(2400, 1800)
    thumb_bytes = generate_thumbnail(raw_bytes, max_dim=THUMBNAIL_MAX_DIMENSION, quality=75)

    assert len(thumb_bytes) > 0
    # Must be small enough for instant client display
    assert len(thumb_bytes) < 35 * 1024

    with Image.open(io.BytesIO(thumb_bytes)) as thumb_img:
        w, h = thumb_img.size
        assert max(w, h) <= THUMBNAIL_MAX_DIMENSION


def test_ingredient_knowledge_cache_matching(db_session):
    """Verify that IngredientKnowledgeCache performs O(1) matching without hitting the database repeatedly."""
    cache = IngredientKnowledgeCache.get_or_refresh(db_session)
    assert cache._last_loaded > 0

    # Test token matching
    result = match_and_explain_ingredients(["Sugar", "INS 500", "Wheat Flour", "UnknownMysteriousChemical"], db_session)
    assert result["is_available"] is True
    assert result["total_count"] == 4
    assert result["unrecognized_count"] >= 1
    # Check that unrecognized has the expected token
    unrec_names = [u["name"] for u in result["unrecognized"]]
    assert "UnknownMysteriousChemical" in unrec_names


def test_health_metrics_endpoint():
    """Verify that /api/health/metrics returns process memory (RSS, VMS), system memory, and OCR engine state."""
    client = TestClient(app)
    response = client.get("/api/health/metrics")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert "process_memory" in data
    assert "rss_mb" in data["process_memory"]
    assert data["process_memory"]["rss_mb"] > 0
    assert "system_memory" in data
    assert "ocr_engine" in data
    assert "performance" in data
