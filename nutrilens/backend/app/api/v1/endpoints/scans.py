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

from app.api.deps import get_db, get_current_user_optional
from app.models.user import User
from app.schemas.scan import (
    ScanResponse,
    ScanCorrectionRequest,
    ScanConfirmRequest,
    ScanConfirmResponse,
)
from app.food_scanner.service import (
    process_scan_upload,
    get_scan_by_id,
    update_scan_correction,
    confirm_scan_and_create_product,
    UPLOAD_DIR,
)

router = APIRouter()


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


@router.get(
    "/scans/{scan_id}",
    response_model=ScanResponse,
    summary="Retrieve scan session details and OCR results",
)
def get_scan(
    scan_id: str,
    db: Session = Depends(get_db),
):
    """Returns the scan record, raw OCR text, structured extracted fields, and any user corrections."""
    return get_scan_by_id(scan_id, db)


@router.put(
    "/scans/{scan_id}/correction",
    response_model=ScanResponse,
    summary="Update manual corrections on extracted scan fields",
)
def save_scan_correction(
    scan_id: str,
    correction: ScanCorrectionRequest,
    db: Session = Depends(get_db),
):
    """Allows user to correct OCR errors (product name, brand, ingredients, nutrition facts, allergens)."""
    return update_scan_correction(scan_id, correction, db)


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
