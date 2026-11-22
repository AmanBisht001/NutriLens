"""
NutriLens – Food Scanner Endpoints (Day 4)
Handles:
- POST /api/products/scan
- GET /api/scans/{id}
- PUT /api/scans/{id}/correction
- POST /api/scans/{id}/confirm
- GET /api/scans/images/{filename}
"""
import os
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user_optional, get_current_user
from app.models.user import User
from app.schemas.scan import (
    ScanResponse,
    ScanCorrectionRequest,
    ScanConfirmRequest,
    ScanConfirmResponse,
    ScanHistoryResponse,
)
from app.food_scanner.service import (
    process_scan_upload,
    get_scan_by_id,
    get_user_scan_history,
    update_scan_correction,
    confirm_scan_and_create_product,
    UPLOAD_DIR,
)
from app.food_scanner.ocr_engine import get_ocr_engine
from app.food_scanner.preprocessor import preprocess_image
from app.food_scanner.extractor import extract_structured_label_info
import cv2
import time
import numpy as np

router = APIRouter()


@router.get(
    "/scans/history",
    response_model=ScanHistoryResponse,
    summary="Retrieve the authenticated user's chronological scan history",
)
def list_user_scans(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns the authenticated user's scans, sorted newest first, with NutriLens scores and images."""
    return get_user_scan_history(
        user_id=current_user.id,
        db=db,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/products/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload food label images for OCR extraction",
)
async def scan_food_product(
    files: List[UploadFile] = File(..., description="1 or more food label images"),
    label_types: Optional[List[str]] = Form(None, description="Label types corresponding to files"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Accepts 1 or more images of a food package (e.g. ingredients list,
    nutrition facts table, front of package, allergens).
    Validates, preprocesses via OpenCV, runs OCR, and extracts structured fields.
    """
    types_list = label_types or []
    # If a single comma-separated string or form list was sent
    if types_list and len(types_list) == 1 and "," in types_list[0]:
        types_list = [t.strip() for t in types_list[0].split(",")]

    scan_record = await process_scan_upload(
        files=files,
        label_types=types_list,
        current_user=current_user,
        db=db,
    )
    return scan_record


@router.post(
    "/scans/debug-ocr",
    summary="Development diagnostic endpoint to inspect raw OCR output directly",
)
async def debug_ocr_endpoint(
    file: UploadFile = File(..., description="Food label image to inspect"),
):
    """
    Accepts a food-label image and returns exact raw OCR results,
    detected text regions, bounding boxes, confidences, and parser output.
    """
    t0 = time.perf_counter()
    errors = []
    content = await file.read()
    
    # Check decoding
    image_decoded = False
    img_shape = None
    try:
        nparr = np.frombuffer(content, np.uint8)
        img_cv = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img_cv is not None:
            image_decoded = True
            img_shape = list(img_cv.shape)
        else:
            errors.append("cv2.imdecode returned None.")
    except Exception as e:
        errors.append(f"Image decoding failed: {e}")

    # Inspect OCR engine
    engine = get_ocr_engine()
    engine_name = engine.__class__.__name__

    # Installed PaddleOCR version
    paddle_version = "unknown"
    try:
        import paddleocr
        paddle_version = getattr(paddleocr, "__version__", "unknown")
    except Exception as e:
        paddle_version = f"not installed ({e})"

    recognized_text = []
    lines_info = []
    confidences = []

    if image_decoded:
        try:
            ocr_res = engine.extract_text(img_cv)
            for line in ocr_res.lines:
                recognized_text.append(line.text)
                confidences.append(line.confidence)
                lines_info.append({
                    "text": line.text,
                    "confidence": round(line.confidence, 4),
                    "box": line.box,
                })
        except Exception as e:
            errors.append(f"OCR execution failed: {e}")

    avg_conf = (sum(confidences) / len(confidences)) if confidences else 0.0
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # Also run information extractor to verify end-to-end parsed result
    raw_text = "\n".join(recognized_text)
    extracted_data = extract_structured_label_info(
        raw_ocr_text=raw_text,
        ocr_confidence=avg_conf,
        ocr_engine=engine_name.lower().replace("engine", ""),
    )

    return {
        "image_decoded": image_decoded,
        "image_shape": img_shape,
        "file_size_bytes": len(content),
        "ocr_engine": engine_name,
        "ocr_version": paddle_version,
        "detected_text_regions": len(recognized_text),
        "average_confidence": round(avg_conf, 4),
        "processing_time_ms": round(elapsed_ms, 2),
        "recognized_text": recognized_text,
        "lines": lines_info,
        "raw_text": raw_text,
        "extracted_nutrition": extracted_data.get("nutrition_facts"),
        "extracted_ingredients": extracted_data.get("ingredients"),
        "product_name": extracted_data.get("product_name"),
        "errors": errors,
    }


@router.get(
    "/scans/{scan_id}",
    response_model=ScanResponse,
    summary="Retrieve scan session details, analysis, and OCR results",
)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Returns the scan record, raw OCR text, structured extracted fields, automated analysis, and user corrections."""
    return get_scan_by_id(scan_id, db, current_user=current_user)


@router.put(
    "/scans/{scan_id}/correction",
    response_model=ScanResponse,
    summary="Update manual corrections on extracted scan fields and re-analyze",
)
def save_scan_correction(
    scan_id: str,
    correction: ScanCorrectionRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Allows user to correct OCR fields and re-computes score, ingredient intelligence, and personal suitability."""
    return update_scan_correction(scan_id, correction, db, current_user=current_user)


@router.post(
    "/scans/{scan_id}/confirm",
    response_model=ScanConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm scan and commit product into catalogue",
)
def confirm_scan(
    scan_id: str,
    confirm_data: ScanConfirmRequest,
    db: Session = Depends(get_db),
):
    """
    Validates user-reviewed fields and saves the product, nutrition facts,
    ingredients, and allergens into the canonical NutriLens database.
    """
    scan, product = confirm_scan_and_create_product(scan_id, confirm_data, db)
    return ScanConfirmResponse(
        message="Product successfully verified and added to catalogue from food scan.",
        scan_id=scan.id,
        product_id=product.id,
        product={
            "id": product.id,
            "name": product.name,
            "brand": product.brand,
            "category": product.category,
            "serving_size": product.serving_size,
            "data_source": product.data_source,
            "is_verified": product.is_verified,
        },
    )


@router.get(
    "/scans/images/{filename}",
    summary="Serve uploaded scan image",
)
def get_scan_image(filename: str):
    """Safely serves saved scan image files for frontend preview."""
    # Prevent path traversal
    safe_name = os.path.basename(filename)
    file_path = os.path.join(UPLOAD_DIR, safe_name)
    if not os.path.isfile(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Requested image not found.",
        )
    return FileResponse(file_path)
