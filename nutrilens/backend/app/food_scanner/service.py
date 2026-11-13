"""
NutriLens – Food Scanner Service (Day 4)
Orchestrates image upload, validation, preprocessing, OCR execution,
structured extraction, manual correction, and database confirmation into the catalogue.
"""
import os
import uuid
import logging
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session

from app.models.scan import ProductScan
from app.models.product import (
    Product,
    NutritionFacts,
    Ingredient,
    ProductIngredient,
    Allergen,
    ProductAllergen,
)
from app.models.user import User
from app.food_scanner.preprocessor import (
    validate_image_bytes,
    preprocess_image,
)
from app.food_scanner.ocr_engine import get_ocr_engine
from app.food_scanner.extractor import extract_structured_label_info
from app.schemas.scan import ScanCorrectionRequest, ScanConfirmRequest

logger = logging.getLogger(__name__)

# Uploads directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "scans")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def process_scan_upload(
    files: List[UploadFile],
    label_types: List[str],
    current_user: Optional[User],
    db: Session,
) -> ProductScan:
    """
    Accepts 1 or more uploaded images belonging to one product scan.
    Validates, preprocesses, extracts OCR text, structures the output,
    and stores a ProductScan record.
    """
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image file must be uploaded.",
        )

    scan_id = str(uuid.uuid4())
    images_meta: List[Dict[str, Any]] = []
    ocr_raw_sections: List[str] = []
    confidences: List[float] = []

    engine = get_ocr_engine()

    for idx, file in enumerate(files):
        # Determine label type (e.g. "front", "ingredients", "nutrition", "allergens")
        ltype = label_types[idx] if idx < len(label_types) else "other"
        filename = file.filename or f"image_{idx}.jpg"

        content = await file.read()

        # 1. Validation (size, type, decodability)
        validate_image_bytes(
            content=content,
            filename=filename,
            content_type=file.content_type,
        )

        # 2. Save file locally
        safe_ext = os.path.splitext(filename)[1].lower() or ".jpg"
        saved_filename = f"{scan_id}_{idx}_{ltype}{safe_ext}"
        saved_path = os.path.join(UPLOAD_DIR, saved_filename)
        with open(saved_path, "wb") as f:
            f.write(content)

        relative_url = f"/api/scans/images/{saved_filename}"
        images_meta.append({
            "filename": filename,
            "saved_filename": saved_filename,
            "label_type": ltype,
            "file_path": saved_path,
            "url": relative_url,
            "size_bytes": len(content),
        })

        # 3. Preprocess image with OpenCV (EXIF fix + CLAHE/denoise)
        preprocessed_img, _ = preprocess_image(content, enhance_for_ocr=True)

        # 4. OCR text extraction
        ocr_res = engine.extract_text(preprocessed_img)
        if ocr_res.raw_text:
            header = f"--- [{ltype.upper()} LABEL] ---"
            ocr_raw_sections.append(f"{header}\n{ocr_res.raw_text}")
            confidences.append(ocr_res.confidence)

    combined_raw_text = "\n\n".join(ocr_raw_sections)
    avg_confidence = (
        sum(confidences) / len(confidences) if confidences else 0.0
    )

    # 5. Information Extraction Pipeline
    extracted_data = extract_structured_label_info(
        raw_ocr_text=combined_raw_text,
        ocr_confidence=avg_confidence,
        ocr_engine=engine.__class__.__name__.lower().replace("engine", ""),
    )

    # 6. Persist ProductScan record
    scan_record = ProductScan(
        id=scan_id,
        user_id=current_user.id if current_user else None,
        status="extracted",
        images=images_meta,
        raw_ocr_text=combined_raw_text,
        extracted_data=extracted_data,
        corrected_data=None,
        product_id=None,
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)

    return scan_record


def get_scan_by_id(scan_id: str, db: Session) -> ProductScan:
    """Fetch scan record or 404."""
    scan = db.query(ProductScan).filter(ProductScan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan record with ID '{scan_id}' not found.",
        )
    return scan


def update_scan_correction(
    scan_id: str,
    correction: ScanCorrectionRequest,
    db: Session,
) -> ProductScan:
    """
    Saves user corrections to the scan record without immediately publishing to catalogue.
    """
    scan = get_scan_by_id(scan_id, db)

    # Base on existing extracted data or previous corrections
    corrected = dict(scan.corrected_data or scan.extracted_data or {})

    # Apply provided non-None fields
    req_dict = correction.model_dump(exclude_unset=True)
    for k, v in req_dict.items():
        if v is not None:
            corrected[k] = v

    scan.corrected_data = corrected
    scan.status = "corrected"
    db.commit()
    db.refresh(scan)
    return scan


def confirm_scan_and_create_product(
    scan_id: str,
    confirm_req: ScanConfirmRequest,
    db: Session,
) -> Tuple[ProductScan, Product]:
    """
    Takes confirmed fields from the scan review workflow, creates canonical Product,
    NutritionFacts, ProductIngredient, and ProductAllergen records, and marks the scan as confirmed.
    """
    scan = get_scan_by_id(scan_id, db)

    # 1. Determine main image URL from scan images if available
    label_image_url = None
    if scan.images and len(scan.images) > 0:
        label_image_url = scan.images[0].get("url")

    # 2. Create Product
    product = Product(
        name=confirm_req.product_name.strip(),
        brand=confirm_req.brand.strip() if confirm_req.brand else None,
        category=confirm_req.category.strip() if confirm_req.category else "Snacks & Namkeen",
        serving_size=confirm_req.serving_size.strip() if confirm_req.serving_size else "100g",
        barcode=confirm_req.barcode.strip() if confirm_req.barcode else None,
        label_image_url=label_image_url,
        raw_ingredients_text=confirm_req.raw_ingredients_text,
        data_source="scan",
        is_demo_data=False,
        is_verified=False,  # Scanned records require moderator/curator verification
        verification_note="Scanned via NutriLens OCR pipeline; verified by user.",
    )
    db.add(product)
    db.flush()  # populate product.id

    # 3. Create Nutrition Facts
    if confirm_req.nutrition_facts:
        nf_data = confirm_req.nutrition_facts.model_dump()
        nutrition = NutritionFacts(
            product_id=product.id,
            energy_kcal=nf_data.get("energy_kcal"),
            total_fat_g=nf_data.get("total_fat_g"),
            saturated_fat_g=nf_data.get("saturated_fat_g"),
            trans_fat_g=nf_data.get("trans_fat_g"),
            carbohydrates_g=nf_data.get("carbohydrates_g"),
            total_sugar_g=nf_data.get("total_sugar_g"),
            added_sugar_g=nf_data.get("added_sugar_g"),
            dietary_fibre_g=nf_data.get("dietary_fibre_g"),
            protein_g=nf_data.get("protein_g"),
            sodium_mg=nf_data.get("sodium_mg"),
            serving_unit="per_100g",
            is_illustrative=False,
        )
        db.add(nutrition)

    # 4. Resolve Ingredients
    scan_conf = 0.85
    if scan.extracted_data and isinstance(scan.extracted_data, dict):
        scan_conf = scan.extracted_data.get("ocr_confidence", 0.85)

    for idx, ing_name in enumerate(confirm_req.ingredients):
        clean_name = ing_name.strip()
        if not clean_name:
            continue
        norm_name = clean_name.lower()

        # Find or create Ingredient in registry
        ingredient_rec = (
            db.query(Ingredient)
            .filter(Ingredient.normalized_name == norm_name)
            .first()
        )
        if not ingredient_rec:
            ingredient_rec = Ingredient(
                name=clean_name,
                normalized_name=norm_name,
                category="General",
                concern_level="safe",
                description=f"Ingredient extracted from {product.name}",
            )
            db.add(ingredient_rec)
            db.flush()

        # Link via ProductIngredient
        # Check uniqueness constraint (product_id, ingredient_id)
        existing_link = (
            db.query(ProductIngredient)
            .filter(
                ProductIngredient.product_id == product.id,
                ProductIngredient.ingredient_id == ingredient_rec.id,
            )
            .first()
        )
        if not existing_link:
            prod_ing = ProductIngredient(
                product_id=product.id,
                ingredient_id=ingredient_rec.id,
                original_text=clean_name,
                order_index=idx,
                ocr_confidence=scan_conf,
                is_verified=False,
            )
            db.add(prod_ing)

    # 5. Resolve Declared Allergens
    for allergen_name in confirm_req.declared_allergens:
        clean_alg = allergen_name.strip()
        if not clean_alg:
            continue
        alg_rec = db.query(Allergen).filter(Allergen.name.ilike(clean_alg)).first()
        if not alg_rec:
            alg_rec = Allergen(name=clean_alg.capitalize(), description=f"Allergen: {clean_alg}")
            db.add(alg_rec)
            db.flush()

        prod_alg = ProductAllergen(
            product_id=product.id,
            allergen_id=alg_rec.id,
            declaration_type="declared",
        )
        db.add(prod_alg)

    # 6. Resolve Precautionary Allergens
    for allergen_name in confirm_req.precautionary_allergens:
        clean_alg = allergen_name.strip()
        if not clean_alg:
            continue
        alg_rec = db.query(Allergen).filter(Allergen.name.ilike(clean_alg)).first()
        if not alg_rec:
            alg_rec = Allergen(name=clean_alg.capitalize(), description=f"Allergen: {clean_alg}")
            db.add(alg_rec)
            db.flush()

        prod_alg = ProductAllergen(
            product_id=product.id,
            allergen_id=alg_rec.id,
            declaration_type="precautionary",
        )
        db.add(prod_alg)

    # 7. Update scan record
    scan.product_id = product.id
    scan.status = "confirmed"
    db.commit()
    db.refresh(scan)
    db.refresh(product)

    return scan, product
