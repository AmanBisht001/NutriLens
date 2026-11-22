"""
NutriLens – Food Scanner Service (Day 4)
Orchestrates image upload, validation, preprocessing, OCR execution,
structured extraction, manual correction, and database confirmation into the catalogue.
"""
import os
import re
import gc
import time
import uuid
import asyncio
import collections
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
import psutil

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
    generate_thumbnail,
)
from app.food_scanner.ocr_engine import get_ocr_engine
from app.food_scanner.extractor import extract_structured_label_info
from app.food_scanner.vision_extractor import MultimodalVisionExtractor
from app.schemas.scan import ScanCorrectionRequest, ScanConfirmRequest
from app.scoring_engine.service import analyze_nutrition_payload
from app.suitability_engine.matcher import evaluate_suitability

logger = logging.getLogger(__name__)

# Uploads directory
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "scans")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Concurrency control: limits simultaneous heavy OCR scans to 1 on memory-constrained servers (Render 512MB RAM)
_SCAN_SEMAPHORE = asyncio.Semaphore(1)

# In-memory rolling buffer of recent scan performance metrics for diagnostic monitoring
RECENT_SCAN_METRICS = collections.deque(maxlen=100)


def record_scan_metric(scan_id: str, total_ms: float, ocr_ms: float, vision_ms: float, prep_ms: float):
    """Records performance timing and RAM usage for monitoring."""
    try:
        proc = psutil.Process()
        mem_info = proc.memory_info()
        rss_mb = round(mem_info.rss / (1024 * 1024), 2)
    except Exception:
        rss_mb = 0.0

    metric = {
        "scan_id": scan_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_ms": round(total_ms, 2),
        "ocr_ms": round(ocr_ms, 2),
        "vision_ms": round(vision_ms, 2),
        "preprocess_ms": round(prep_ms, 2),
        "rss_mb": rss_mb,
    }
    RECENT_SCAN_METRICS.append(metric)
    logger.info(
        f"[PERF_SCAN] scan_id={scan_id} total_ms={total_ms:.1f} ocr_ms={ocr_ms:.1f} "
        f"vision_ms={vision_ms:.1f} prep_ms={prep_ms:.1f} rss={rss_mb}MB"
    )


class IngredientKnowledgeCache:
    """
    High-performance in-memory cache for canonical ingredients.
    Indexes all canonical ingredients into O(1) hash maps:
    - by_norm: Dict[normalized_name_lower, dict]
    - by_name: Dict[name_lower, dict]
    - by_ins: Dict[ins_code_upper, dict]
    - by_alias: Dict[alias_lower, dict]
    - substring_list: List[Tuple[name_lower, dict]] for fallback
    Eliminates database roundtrips and O(N*M) nested loops on every scan.
    """
    _by_norm: Dict[str, Dict[str, Any]] = {}
    _by_name: Dict[str, Dict[str, Any]] = {}
    _by_ins: Dict[str, Dict[str, Any]] = {}
    _by_alias: Dict[str, Dict[str, Any]] = {}
    _substring_list: List[Tuple[str, Dict[str, Any]]] = []
    _last_loaded: float = 0.0
    _ttl_seconds: float = 3600.0  # 1 hour cache TTL

    @classmethod
    def get_or_refresh(cls, db: Session):
        now = time.time()
        if cls._last_loaded > 0 and (now - cls._last_loaded) < cls._ttl_seconds and cls._by_name:
            return cls

        try:
            all_ings = db.query(Ingredient).all()
            by_norm = {}
            by_name = {}
            by_ins = {}
            by_alias = {}
            sub_list = []

            for ing in all_ings:
                info = {
                    "name": ing.name,
                    "normalized_name": ing.normalized_name,
                    "category": ing.category or "General",
                    "purpose": ing.purpose or ing.description or "Ingredient component",
                    "concern_level": ing.concern_level or "safe",
                    "ins_number": ing.ins_number,
                    "is_common_allergen": bool(ing.is_common_allergen),
                    "source_reference": ing.source_reference,
                    "description": ing.description,
                }
                if ing.normalized_name:
                    by_norm[ing.normalized_name.lower().strip()] = info
                if ing.name:
                    nl = ing.name.lower().strip()
                    by_name[nl] = info
                    if len(nl) >= 4:
                        sub_list.append((nl, info))
                if ing.ins_number:
                    codes = re.findall(r"\d{3,4}[a-z]?", ing.ins_number, re.IGNORECASE)
                    for c in codes:
                        by_ins[c.upper()] = info
                if ing.aliases:
                    aliases_list = [
                        a.strip().lower()
                        for a in ing.aliases.replace("[", "").replace("]", "").replace('"', '').split(",")
                        if a.strip()
                    ]
                    for a in aliases_list:
                        by_alias[a] = info

            cls._by_norm = by_norm
            cls._by_name = by_name
            cls._by_ins = by_ins
            cls._by_alias = by_alias
            cls._substring_list = sorted(sub_list, key=lambda x: len(x[0]), reverse=True)
            cls._last_loaded = now
            logger.info(f"IngredientKnowledgeCache loaded {len(all_ings)} canonical ingredients into memory index.")
        except Exception as e:
            logger.warning(f"Failed to refresh IngredientKnowledgeCache: {e}")

        return cls

    @classmethod
    def match_token(cls, token_lower: str) -> Optional[Dict[str, Any]]:
        # 1. Exact match on normalized_name
        if token_lower in cls._by_norm:
            return cls._by_norm[token_lower]
        # 2. Exact match on name
        if token_lower in cls._by_name:
            return cls._by_name[token_lower]
        # 3. Check INS / E number
        ins_match = re.search(r"\b(?:ins|e)\s*[-_]?\s*(\d{3,4}[a-z]?)\b", token_lower)
        if ins_match:
            code = ins_match.group(1).upper()
            if code in cls._by_ins:
                return cls._by_ins[code]
        # 4. Check aliases
        if token_lower in cls._by_alias:
            return cls._by_alias[token_lower]
        for a, info in cls._by_alias.items():
            if a in token_lower:
                return info
        # 5. Substring match
        for s_name, info in cls._substring_list:
            if s_name in token_lower or token_lower in s_name:
                return info
        return None


def match_and_explain_ingredients(
    ingredients: List[str],
    db: Session,
) -> Dict[str, Any]:
    """
    Matches extracted ingredients against canonical Ingredient knowledge base.
    Uses IngredientKnowledgeCache for O(1) in-memory index lookups instead of repetitive DB queries.
    Separates recognized ingredients (with purpose, category, concern level, INS, allergen info)
    from unrecognized ingredients.
    """
    if not ingredients or len(ingredients) == 0:
        return {
            "is_available": False,
            "message": "Ingredient analysis unavailable - no ingredients list detected on label.",
            "total_count": 0,
            "recognized_count": 0,
            "unrecognized_count": 0,
            "recognized": [],
            "unrecognized": [],
            "concerns": [],
        }

    recognized = []
    unrecognized = []
    concerns = []

    # Get cached indexed knowledge base (zero DB queries on repeated scans)
    cache = IngredientKnowledgeCache.get_or_refresh(db)

    for token in ingredients:
        clean_token = token.strip()
        if not clean_token:
            continue

        token_lower = clean_token.lower()
        matched_info = cache.match_token(token_lower)

        if matched_info:
            item_info = {
                "name": matched_info["name"],
                "original_text": clean_token,
                "category": matched_info.get("category") or "General",
                "purpose": matched_info.get("purpose") or "Ingredient component",
                "concern_level": matched_info.get("concern_level") or "safe",
                "ins_number": matched_info.get("ins_number"),
                "is_common_allergen": bool(matched_info.get("is_common_allergen")),
                "source_reference": matched_info.get("source_reference"),
            }
            recognized.append(item_info)

            # Check if this ingredient raises concern
            concern_level = matched_info.get("concern_level")
            is_common_allergen = bool(matched_info.get("is_common_allergen"))
            if concern_level in ("high", "moderate") or is_common_allergen:
                concerns.append({
                    "ingredient": matched_info["name"],
                    "concern_level": concern_level,
                    "is_common_allergen": is_common_allergen,
                    "note": matched_info.get("description") or matched_info.get("purpose") or f"Concern level: {concern_level}",
                })
        else:
            unrecognized.append({
                "name": clean_token,
                "original_text": clean_token,
                "category": "Uncategorized",
                "purpose": "Not found in standard additives knowledge base",
                "concern_level": "unknown",
            })

    return {
        "is_available": True,
        "message": None,
        "total_count": len(recognized) + len(unrecognized),
        "recognized_count": len(recognized),
        "unrecognized_count": len(unrecognized),
        "recognized": recognized,
        "unrecognized": unrecognized,
        "concerns": concerns,
    }


def run_scan_analysis(
    extracted_data: Dict[str, Any],
    current_user: Optional[User],
    db: Session,
) -> Dict[str, Any]:
    """
    Full automated analysis of scanned label:
    1. Product metadata (defaulting to 'Unknown Product' if unreadable)
    2. Deterministic nutrition scoring & breakdown (honest about missing values)
    3. Ingredient intelligence & additives analysis
    4. Personalized suitability evaluation based on saved user profile
    5. Data quality & uncertainty audit
    """
    product_name = extracted_data.get("product_name") or "Unknown Product"
    brand = extracted_data.get("brand")
    category = extracted_data.get("category") or "General"
    serving_size = extracted_data.get("serving_size") or "100g"
    ingredients = extracted_data.get("ingredients") or []
    raw_ingredients_text = extracted_data.get("raw_ingredients_text")
    nutrition_facts = extracted_data.get("nutrition_facts") or {}
    declared_allergens = extracted_data.get("declared_allergens") or []
    precautionary_allergens = extracted_data.get("precautionary_allergens") or []

    # 1. Ingredient Intelligence
    ingredient_intel = match_and_explain_ingredients(ingredients, db)

    # 2. Nutrition Scoring
    has_nutrients = False
    if isinstance(nutrition_facts, dict):
        has_nutrients = any(v is not None for v in nutrition_facts.values())

    if not has_nutrients:
        nutrition_analysis = {
            "is_available": False,
            "status": "unavailable",
            "score": None,
            "grade": None,
            "rating_label": "Nutrition facts unavailable",
            "rating_color": "slate",
            "standard_unit": "per_100g",
            "message": "Nutritional scoring unavailable - no nutrition table detected on label.",
            "score_explanation": "Nutritional scoring requires declared label values. Missing information is never assumed to be zero.",
            "positive_factors": [],
            "attention_factors": [],
            "per_100_values": nutrition_facts or {},
            "per_serving_values": {},
            "serving_size_info": {
                "raw_text": serving_size,
                "quantity": 100.0,
                "unit": "g",
                "standard_reference": "100g",
            },
            "nutrient_evaluations": [],
            "disclaimer": "Nutritional scoring requires declared label values. NutriLens never invents missing nutritional facts.",
        }
    else:
        nutrition_analysis = analyze_nutrition_payload(
            nutrients_per_100=nutrition_facts,
            category=category,
            serving_size_str=serving_size,
        )
        if nutrition_analysis.get("status") == "insufficient_data":
            nutrition_analysis["is_available"] = False
            nutrition_analysis["message"] = (
                "Nutritional scoring unavailable - insufficient nutritional data on label. "
                f"Missing critical fields: {', '.join(nutrition_analysis.get('missing_critical_fields', []))}."
            )
        else:
            nutrition_analysis["is_available"] = True

    # 3. Personalized Dietary Suitability
    user_pref = "None"
    user_allergies: List[str] = []
    user_restrictions: List[str] = []
    user_goals: List[str] = []
    user_monitored: List[str] = []
    is_personalized = False

    if current_user and getattr(current_user, "profile", None):
        prof = current_user.profile
        user_pref = prof.dietary_preference or "None"
        user_allergies = prof.allergies or []
        user_restrictions = prof.dietary_restrictions or []
        user_goals = prof.nutrition_goals or []
        user_monitored = prof.monitored_nutrients or []
        is_personalized = True

    matcher_ingredients = []
    for it in ingredient_intel.get("recognized", []):
        matcher_ingredients.append({
            "name": it.get("name"),
            "original_text": it.get("original_text"),
            "category": it.get("category"),
        })
    for it in ingredient_intel.get("unrecognized", []):
        matcher_ingredients.append({
            "name": it.get("name"),
            "original_text": it.get("original_text"),
            "category": "Uncategorized",
        })

    matcher_allergens = (
        [{"name": a, "declaration_type": "declared"} for a in declared_allergens]
        + [{"name": a, "declaration_type": "precautionary"} for a in precautionary_allergens]
    )

    suitability_eval = evaluate_suitability(
        product_name=product_name,
        product_ingredients=matcher_ingredients,
        product_allergens=matcher_allergens,
        raw_ingredients_text=raw_ingredients_text,
        nutrition_facts=nutrition_facts if has_nutrients else None,
        user_preference=user_pref,
        user_allergies=user_allergies,
        user_restrictions=user_restrictions,
        user_nutrition_goals=user_goals,
        user_monitored_nutrients=user_monitored,
    )

    suitability_analysis = {
        "status": suitability_eval.status,
        "status_label": suitability_eval.status_label,
        "badge_color": suitability_eval.badge_color,
        "is_suitable": suitability_eval.is_suitable,
        "summary_narrative": suitability_eval.summary_narrative,
        "conflicts": [
            {
                "category": c.category,
                "severity": c.severity,
                "title": c.title,
                "detail": c.detail,
                "source_ingredient": c.source_ingredient,
                "is_precautionary": c.is_precautionary,
            }
            for c in suitability_eval.conflicts
        ],
        "cautions": [
            {
                "category": c.category,
                "severity": c.severity,
                "title": c.title,
                "detail": c.detail,
                "source_ingredient": c.source_ingredient,
                "is_precautionary": c.is_precautionary,
            }
            for c in suitability_eval.cautions
        ],
        "positive_observations": [
            {
                "category": c.category,
                "severity": c.severity,
                "title": c.title,
                "detail": c.detail,
                "source_ingredient": c.source_ingredient,
                "is_precautionary": c.is_precautionary,
            }
            for c in suitability_eval.positive_observations
        ],
        "safety_warnings": suitability_eval.safety_warnings,
        "rules_applied": suitability_eval.rules_applied,
        "is_personalized": is_personalized,
        "guest_notice": None if is_personalized else "Log in to check suitability against your personal dietary preferences and allergies.",
        "evaluated_preferences": {
            "dietary_preference": user_pref,
            "allergies": user_allergies,
            "dietary_restrictions": user_restrictions,
            "nutrition_goals": user_goals,
            "monitored_nutrients": user_monitored,
        },
        "disclaimer": suitability_eval.disclaimer,
    }

    # 4. Data Quality & Uncertainty
    data_quality = {
        "ocr_confidence": extracted_data.get("ocr_confidence", 0.0),
        "ocr_engine": extracted_data.get("ocr_engine", "unknown"),
        "uncertainty_flags": extracted_data.get("uncertainty_flags", []),
        "is_verified": False,
        "disclaimer": "This analysis is automatically generated from package label OCR for informational and educational purposes only. It is not medical or nutritional advice.",
    }

    return {
        "product_name": product_name,
        "brand": brand,
        "category": category,
        "serving_size": serving_size,
        "scan_timestamp": datetime.now(timezone.utc).isoformat(),
        "nutrition_analysis": nutrition_analysis,
        "ingredient_intelligence": ingredient_intel,
        "suitability_analysis": suitability_analysis,
        "data_quality": data_quality,
    }


async def process_scan_upload(
    files: List[UploadFile],
    label_types: List[str],
    current_user: Optional[User],
    db: Session,
) -> ProductScan:
    """
    Accepts 1 or more uploaded images belonging to one product scan.
    Optimized for low-RAM cloud hosting:
    - Serialized under _SCAN_SEMAPHORE to prevent concurrent memory spikes on 512MB RAM hosts
    - CPU-bound OpenCV and OCR operations run in worker threads via asyncio.to_thread
    - Creates lightweight thumbnails (~15-25KB) alongside original images
    - Automatically cleans up memory and triggers garbage collection
    """
    if not files or len(files) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one image file must be uploaded.",
        )

    t_start = time.perf_counter()
    scan_id = str(uuid.uuid4())
    images_meta: List[Dict[str, Any]] = []
    ocr_raw_sections: List[str] = []
    confidences: List[float] = []
    total_prep_ms = 0.0
    total_ocr_ms = 0.0
    total_vis_ms = 0.0

    async with _SCAN_SEMAPHORE:
        engine = get_ocr_engine()
        vision_extractor = MultimodalVisionExtractor()
        vision_task: Optional[asyncio.Task] = None

        for idx, file in enumerate(files):
            ltype = label_types[idx] if idx < len(label_types) else "other"
            filename = file.filename or f"image_{idx}.jpg"

            content = await file.read()

            # 1. Validation (size, type, decodability)
            validate_image_bytes(
                content=content,
                filename=filename,
                content_type=file.content_type,
            )

            # 2. Save original image locally
            safe_ext = os.path.splitext(filename)[1].lower() or ".jpg"
            saved_filename = f"{scan_id}_{idx}_{ltype}{safe_ext}"
            saved_path = os.path.join(UPLOAD_DIR, saved_filename)
            with open(saved_path, "wb") as f:
                f.write(content)

            relative_url = f"/api/scans/images/{saved_filename}"

            # 2b. Generate and save low-memory thumbnail (~15-25KB)
            saved_thumb_filename = f"{scan_id}_{idx}_{ltype}_thumb.jpg"
            saved_thumb_path = os.path.join(UPLOAD_DIR, saved_thumb_filename)
            try:
                thumb_bytes = generate_thumbnail(content)
                with open(saved_thumb_path, "wb") as f:
                    f.write(thumb_bytes)
                del thumb_bytes
                relative_thumb_url = f"/api/scans/images/{saved_thumb_filename}"
            except Exception as e:
                logger.warning(f"Failed to generate thumbnail: {e}")
                relative_thumb_url = relative_url

            images_meta.append({
                "filename": filename,
                "saved_filename": saved_filename,
                "label_type": ltype,
                "file_path": saved_path,
                "url": relative_url,
                "thumbnail_url": relative_thumb_url,
                "size_bytes": len(content),
            })

            # Start vision extraction in parallel for the first label image if configured
            # This completely avoids sequential waiting, saving 5-8 seconds.
            if idx == 0 and vision_extractor.is_available() and vision_task is None:
                mime = "image/png" if saved_filename.endswith(".png") else "image/jpeg"
                vision_task = asyncio.create_task(
                    asyncio.to_thread(
                        vision_extractor.extract_from_image_bytes,
                        content,
                        mime,
                    )
                )

            # 3. Preprocess image in thread (EXIF fix + downscaling + CLAHE)
            t_p0 = time.perf_counter()
            preprocessed_img, _ = await asyncio.to_thread(preprocess_image, content, True)
            total_prep_ms += (time.perf_counter() - t_p0) * 1000

            # 4. OCR text extraction in thread (keeps event loop responsive)
            t_o0 = time.perf_counter()
            ocr_res = await asyncio.to_thread(engine.extract_text, preprocessed_img)
            total_ocr_ms += (time.perf_counter() - t_o0) * 1000

            if ocr_res.raw_text:
                header = f"--- [{ltype.upper()} LABEL] ---"
                ocr_raw_sections.append(f"{header}\n{ocr_res.raw_text}")
                confidences.append(ocr_res.confidence)

            # Clean up intermediate numpy arrays and byte buffers
            del preprocessed_img
            del content
            gc.collect()

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

        # 5b. Multimodal Vision Fallback / Complementary check
        # Only engage vision LLM if OCR could not detect nutrients or ingredients
        has_ocr_nutrients = any(v is not None for v in (extracted_data.get("nutrition_facts") or {}).values())
        has_ocr_ingredients = bool(extracted_data.get("ingredients"))

        if (not has_ocr_nutrients or not has_ocr_ingredients) and vision_task is not None:
            logger.info("OCR output incomplete; utilizing parallel multimodal vision extraction...")
            t_v0 = time.perf_counter()
            try:
                # Wait for vision task with a strict 7-second cap
                vision_result = await asyncio.wait_for(vision_task, timeout=7.0)
                total_vis_ms = (time.perf_counter() - t_v0) * 1000

                if vision_result:
                    if not extracted_data.get("product_name") and vision_result.get("product_name"):
                        extracted_data["product_name"] = vision_result.get("product_name")
                    if not extracted_data.get("brand") and vision_result.get("brand"):
                        extracted_data["brand"] = vision_result.get("brand")
                    if (extracted_data.get("serving_size") == "100g" or not extracted_data.get("serving_size")) and vision_result.get("serving_size"):
                        extracted_data["serving_size"] = vision_result.get("serving_size")

                    if not has_ocr_ingredients and vision_result.get("ingredients"):
                        extracted_data["ingredients"] = vision_result.get("ingredients")
                        extracted_data["raw_ingredients_text"] = vision_result.get("raw_ingredients_text") or ", ".join(vision_result.get("ingredients"))

                    if not has_ocr_nutrients and vision_result.get("nutrition_facts"):
                        extracted_data["nutrition_facts"] = vision_result.get("nutrition_facts")

                    if not extracted_data.get("declared_allergens") and vision_result.get("declared_allergens"):
                        extracted_data["declared_allergens"] = vision_result.get("declared_allergens")
                    if not extracted_data.get("precautionary_allergens") and vision_result.get("precautionary_allergens"):
                        extracted_data["precautionary_allergens"] = vision_result.get("precautionary_allergens")

                    extracted_data["ocr_engine"] = f"{extracted_data['ocr_engine']}+vision"
                    extracted_data["uncertainty_flags"].append("Augmented with multimodal vision analysis.")
            except asyncio.TimeoutError:
                logger.warning("Parallel vision extraction timed out after 7s; proceeding with OCR results.")
            except Exception as e:
                logger.warning(f"Multimodal vision fallback error: {e}")
        elif vision_task is not None:
            # OCR already found everything; cancel vision task if still pending to save quota
            if not vision_task.done():
                vision_task.cancel()

        # Automated analysis: scoring, ingredient intelligence, personalized suitability
        analysis = run_scan_analysis(
            extracted_data=extracted_data,
            current_user=current_user,
            db=db,
        )
        extracted_data["analysis"] = analysis

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

        total_ms = (time.perf_counter() - t_start) * 1000
        record_scan_metric(
            scan_id=scan_id,
            total_ms=total_ms,
            ocr_ms=total_ocr_ms,
            vision_ms=total_vis_ms,
            prep_ms=total_prep_ms,
        )
        gc.collect()

        return scan_record


def get_scan_by_id(
    scan_id: str,
    db: Session,
    current_user: Optional[User] = None,
) -> ProductScan:
    """Fetch scan record or 404, ensuring automated analysis is present and enforcing ownership when user is authenticated."""
    scan = db.query(ProductScan).filter(ProductScan.id == scan_id).first()
    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan record with ID '{scan_id}' not found.",
        )

    # If the scan was created by a registered user, ensure the requesting user matches (or is an admin)
    if scan.user_id and current_user:
        is_owner = scan.user_id == current_user.id
        is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", "user") in ["admin", "superadmin"]
        if not is_owner and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this scan record.",
            )

    # Ensure analysis exists
    target_data = scan.corrected_data if scan.corrected_data else scan.extracted_data
    if target_data and not target_data.get("analysis"):
        user = current_user
        if user is None and scan.user_id:
            user = db.query(User).filter(User.id == scan.user_id).first()
        analysis = run_scan_analysis(target_data, current_user=user, db=db)
        if scan.corrected_data:
            updated_corr = dict(scan.corrected_data)
            updated_corr["analysis"] = analysis
            scan.corrected_data = updated_corr
        elif scan.extracted_data:
            updated_extr = dict(scan.extracted_data)
            updated_extr["analysis"] = analysis
            scan.extracted_data = updated_extr
        db.commit()
        db.refresh(scan)

    return scan


def get_user_scan_history(
    user_id: str,
    db: Session,
    page: int = 1,
    page_size: int = 20,
) -> Dict[str, Any]:
    """
    Retrieves chronological scan history for an authenticated user.
    Newest scans first. Formats scan items with score, grade, and thumbnail image URL.
    """
    offset = max(0, (page - 1) * page_size)
    query = (
        db.query(ProductScan)
        .filter(ProductScan.user_id == user_id)
        .order_by(ProductScan.created_at.desc())
    )
    total = query.count()
    records = query.offset(offset).limit(page_size).all()

    items = []
    for rec in records:
        data = rec.corrected_data if rec.corrected_data else (rec.extracted_data or {})
        analysis = data.get("analysis") or {}
        nutr_analysis = analysis.get("nutrition_analysis") or {}

        # Image thumbnail URL
        image_url = None
        thumbnail_url = None
        if rec.images and len(rec.images) > 0:
            first_img = rec.images[0]
            if isinstance(first_img, dict):
                image_url = first_img.get("url")
                thumbnail_url = first_img.get("thumbnail_url") or image_url

        product_name = (
            analysis.get("product_name")
            or data.get("product_name")
            or "Unknown Product"
        )
        brand = analysis.get("brand") or data.get("brand")
        category = analysis.get("category") or data.get("category")

        score = nutr_analysis.get("score")
        grade = nutr_analysis.get("grade")
        rating_label = nutr_analysis.get("rating_label")
        rating_color = nutr_analysis.get("rating_color")
        is_scoreable = nutr_analysis.get("is_available", False)

        ocr_confidence = data.get("ocr_confidence", 0.0)
        ocr_engine = data.get("ocr_engine", "paddleocr")

        items.append({
            "id": rec.id,
            "product_name": product_name,
            "brand": brand,
            "category": category,
            "created_at": rec.created_at,
            "status": rec.status,
            "score": score,
            "grade": grade,
            "rating_label": rating_label,
            "rating_color": rating_color,
            "image_url": image_url,
            "thumbnail_url": thumbnail_url,
            "ocr_confidence": round(ocr_confidence, 4) if isinstance(ocr_confidence, (int, float)) else 0.0,
            "ocr_engine": ocr_engine,
            "is_scoreable": is_scoreable,
        })

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": items,
    }


def update_scan_correction(
    scan_id: str,
    correction: ScanCorrectionRequest,
    db: Session,
    current_user: Optional[User] = None,
) -> ProductScan:
    """
    Saves user corrections to the scan record and immediately re-computes
    automated scoring, ingredient intelligence, and personalized suitability.
    """
    scan = get_scan_by_id(scan_id, db, current_user=current_user)

    # Base on existing extracted data or previous corrections
    corrected = dict(scan.corrected_data or scan.extracted_data or {})

    # Apply provided non-None fields
    req_dict = correction.model_dump(exclude_unset=True)
    for k, v in req_dict.items():
        if v is not None:
            if k == "nutrition_facts" and isinstance(v, dict):
                current_nf = dict(corrected.get("nutrition_facts") or {})
                for nk, nv in v.items():
                    if nv is not None:
                        current_nf[nk] = nv
                corrected["nutrition_facts"] = current_nf
            else:
                corrected[k] = v

    user = current_user
    if user is None and scan.user_id:
        user = db.query(User).filter(User.id == scan.user_id).first()

    analysis = run_scan_analysis(
        extracted_data=corrected,
        current_user=user,
        db=db,
    )
    corrected["analysis"] = analysis

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
