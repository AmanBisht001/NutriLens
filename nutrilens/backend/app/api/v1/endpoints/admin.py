"""
NutriLens – Administrative Endpoints (Day 9)
Covers:
- Strict role-based access control (require_admin_user dependency)
- Dashboard stats (real database statistics)
- Product CRUD, verification, nutrition facts, and mappings
- Canonical ingredient CRUD and allergen registry management
- Versioned scoring rule management (create, preserve, activate)
- User-reported data issues & corrections review
"""
import json
import math
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, desc
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_db, require_admin_user, get_current_user_optional
from app.models.user import User
from app.models.product import (
    Product,
    NutritionFacts,
    Ingredient,
    ProductIngredient,
    Allergen,
    ProductAllergen,
)
from app.models.scan import ProductScan
from app.models.scoring_rules import ScoringRuleVersion
from app.models.issue import ProductIssue
from app.scoring_engine.rules import (
    SCORING_RULE_VERSION,
    THRESHOLDS_FOOD,
    THRESHOLDS_BEVERAGE,
    CATEGORY_RULES,
)
from app.schemas.admin import (
    AdminDashboardStats,
    AdminProductCreate,
    AdminProductUpdate,
    AdminProductVerifyPayload,
    AdminIngredientCreate,
    AdminIngredientUpdate,
    AdminAllergenCreate,
    AdminAllergenUpdate,
    ScoringRuleVersionCreate,
    ScoringRuleVersionResponse,
    ProductIssueCreate,
    ProductIssueUpdate,
    ProductIssueResponse,
)
from app.schemas.product import (
    ProductDetail,
    IngredientResponse,
    PaginatedIngredients,
    AllergenResponse,
    PaginatedProducts,
    ProductSummary,
)

router = APIRouter()


def _uuid() -> str:
    return str(uuid.uuid4())


def get_default_scoring_rules_dict() -> Dict[str, Any]:
    """Serializes in-memory rules from rules.py into dicts for DB persistence."""
    food_th = {
        k: {"low": v.low, "moderate": v.moderate, "high": v.high}
        for k, v in THRESHOLDS_FOOD.items()
    }
    bev_th = {
        k: {"low": v.low, "moderate": v.moderate, "high": v.high}
        for k, v in THRESHOLDS_BEVERAGE.items()
    }
    cat_weights = {
        k: {
            "category_name": v.category_name,
            "is_liquid": v.is_liquid,
            "base_score": v.base_score,
            "sugar_weight": v.sugar_weight,
            "saturated_fat_weight": v.saturated_fat_weight,
            "trans_fat_weight": v.trans_fat_weight,
            "sodium_weight": v.sodium_weight,
            "energy_weight": v.energy_weight,
            "fibre_weight": v.fibre_weight,
            "protein_weight": v.protein_weight,
        }
        for k, v in CATEGORY_RULES.items()
    }
    return {
        "thresholds_food": food_th,
        "thresholds_beverage": bev_th,
        "category_weights": cat_weights,
        "general_weights": {
            "sugar_weight": 1.0,
            "saturated_fat_weight": 1.0,
            "trans_fat_weight": 1.5,
            "sodium_weight": 1.0,
            "energy_weight": 0.8,
            "fibre_weight": 1.0,
            "protein_weight": 1.0,
        },
    }


# ===========================================================================
# 1. Dashboard Statistics
# ===========================================================================

@router.get(
    "/dashboard/stats",
    response_model=AdminDashboardStats,
    summary="Get real database statistics for admin dashboard",
)
def get_admin_dashboard_stats(
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    """
    Computes actual database counts across users, products, ingredients,
    scans, verification statuses, and reported data issues.
    """
    total_users = db.query(User).count()
    total_products = db.query(Product).count()
    total_ingredients = db.query(Ingredient).count()
    total_scans = db.query(ProductScan).count()
    verified_products = db.query(Product).filter(Product.is_verified == True).count()
    unverified_products = db.query(Product).filter(Product.is_verified == False).count()

    total_issues = db.query(ProductIssue).count()
    pending_issues = db.query(ProductIssue).filter(ProductIssue.status == "pending").count()
    resolved_issues = db.query(ProductIssue).filter(ProductIssue.status == "resolved").count()

    # Category breakdown
    category_counts = (
        db.query(Product.category, func.count(Product.id))
        .filter(Product.category != None)
        .group_by(Product.category)
        .order_by(desc(func.count(Product.id)))
        .limit(6)
        .all()
    )
    top_categories = [{"category": c or "Uncategorized", "count": cnt} for c, cnt in category_counts]

    # Active scoring rule version
    active_version = (
        db.query(ScoringRuleVersion)
        .filter(ScoringRuleVersion.is_active == True)
        .first()
    )
    active_version_str = active_version.version if active_version else SCORING_RULE_VERSION

    return AdminDashboardStats(
        total_users=total_users,
        total_products=total_products,
        total_ingredients=total_ingredients,
        total_scans=total_scans,
        verified_products=verified_products,
        unverified_products=unverified_products,
        total_issues=total_issues,
        pending_issues=pending_issues,
        resolved_issues=resolved_issues,
        top_categories=top_categories,
        active_scoring_rule_version=active_version_str,
    )


# ===========================================================================
# 2. Product Management
# ===========================================================================

@router.get(
    "/products",
    response_model=PaginatedProducts,
    summary="Admin list products with status filters",
)
def admin_list_products(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_verified: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(Product).options(joinedload(Product.nutrition_facts))

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(or_(Product.name.ilike(term), Product.brand.ilike(term)))

    if category:
        query = query.filter(Product.category == category)

    if is_verified is not None:
        query = query.filter(Product.is_verified == is_verified)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    items = (
        query.order_by(Product.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    summaries = [ProductSummary.model_validate(p) for p in items]
    return PaginatedProducts(
        items=summaries,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/products",
    response_model=ProductDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Admin add new product record with nutrition and mappings",
)
def admin_create_product(
    payload: AdminProductCreate,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    prod_id = _uuid()
    product = Product(
        id=prod_id,
        name=payload.name.strip(),
        brand=payload.brand.strip() if payload.brand else None,
        category=payload.category.strip() if payload.category else None,
        barcode=payload.barcode.strip() if payload.barcode else None,
        serving_size=payload.serving_size.strip() if payload.serving_size else None,
        label_image_url=payload.label_image_url,
        raw_ingredients_text=payload.raw_ingredients_text,
        data_source="curated",
        is_demo_data=False,
        is_verified=payload.is_verified,
        verification_note=payload.verification_note,
    )
    db.add(product)
    db.flush()

    # Nutrition facts
    if payload.nutrition_facts:
        nf_data = payload.nutrition_facts.model_dump(exclude_unset=True)
        nf = NutritionFacts(
            id=_uuid(),
            product_id=prod_id,
            is_illustrative=False,
            **nf_data,
        )
        db.add(nf)

    # Ingredient mappings
    if payload.ingredient_mappings:
        for idx, m in enumerate(payload.ingredient_mappings):
            ing_id = m.ingredient_id
            if not ing_id and m.ingredient_name:
                # Look up ingredient by normalized name or create
                norm = m.ingredient_name.lower().strip()
                existing_ing = db.query(Ingredient).filter(Ingredient.normalized_name == norm).first()
                if existing_ing:
                    ing_id = existing_ing.id
                else:
                    new_ing = Ingredient(
                        id=_uuid(),
                        name=m.ingredient_name.strip(),
                        normalized_name=norm,
                        category="other",
                        concern_level="safe",
                    )
                    db.add(new_ing)
                    db.flush()
                    ing_id = new_ing.id

            if ing_id:
                pi = ProductIngredient(
                    id=_uuid(),
                    product_id=prod_id,
                    ingredient_id=ing_id,
                    original_text=m.ingredient_name or "Ingredient",
                    order_index=m.order_index or idx,
                    is_verified=payload.is_verified,
                )
                db.add(pi)

    # Allergen mappings
    if payload.allergen_mappings:
        for m in payload.allergen_mappings:
            all_id = m.allergen_id
            if not all_id and m.allergen_name:
                existing_all = db.query(Allergen).filter(Allergen.name.ilike(m.allergen_name.strip())).first()
                if existing_all:
                    all_id = existing_all.id

            if all_id:
                pa = ProductAllergen(
                    id=_uuid(),
                    product_id=prod_id,
                    allergen_id=all_id,
                    declaration_type=m.declaration_type or "declared",
                )
                db.add(pa)

    db.commit()

    # Re-fetch complete record
    saved = (
        db.query(Product)
        .options(
            joinedload(Product.nutrition_facts),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
        )
        .filter(Product.id == prod_id)
        .first()
    )
    return ProductDetail.model_validate(saved)


@router.put(
    "/products/{product_id}",
    response_model=ProductDetail,
    summary="Admin update product record and mappings",
)
def admin_update_product(
    product_id: str,
    payload: AdminProductUpdate,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .options(
            joinedload(Product.nutrition_facts),
            selectinload(Product.product_ingredients),
            selectinload(Product.product_allergens),
        )
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if payload.name is not None:
        product.name = payload.name.strip()
    if payload.brand is not None:
        product.brand = payload.brand.strip() if payload.brand else None
    if payload.category is not None:
        product.category = payload.category.strip() if payload.category else None
    if payload.barcode is not None:
        product.barcode = payload.barcode.strip() if payload.barcode else None
    if payload.serving_size is not None:
        product.serving_size = payload.serving_size.strip() if payload.serving_size else None
    if payload.label_image_url is not None:
        product.label_image_url = payload.label_image_url
    if payload.raw_ingredients_text is not None:
        product.raw_ingredients_text = payload.raw_ingredients_text
    if payload.is_verified is not None:
        product.is_verified = payload.is_verified
    if payload.verification_note is not None:
        product.verification_note = payload.verification_note

    # Update Nutrition Facts
    if payload.nutrition_facts is not None:
        nf_dict = payload.nutrition_facts.model_dump(exclude_unset=True)
        if product.nutrition_facts:
            for k, v in nf_dict.items():
                setattr(product.nutrition_facts, k, v)
        else:
            new_nf = NutritionFacts(id=_uuid(), product_id=product.id, **nf_dict)
            db.add(new_nf)

    # Update Ingredient Mappings if provided
    if payload.ingredient_mappings is not None:
        db.query(ProductIngredient).filter(ProductIngredient.product_id == product.id).delete()
        for idx, m in enumerate(payload.ingredient_mappings):
            ing_id = m.ingredient_id
            if ing_id:
                pi = ProductIngredient(
                    id=_uuid(),
                    product_id=product.id,
                    ingredient_id=ing_id,
                    original_text=m.ingredient_name or "Ingredient",
                    order_index=m.order_index or idx,
                    is_verified=product.is_verified,
                )
                db.add(pi)

    # Update Allergen Mappings if provided
    if payload.allergen_mappings is not None:
        db.query(ProductAllergen).filter(ProductAllergen.product_id == product.id).delete()
        for m in payload.allergen_mappings:
            all_id = m.allergen_id
            if all_id:
                pa = ProductAllergen(
                    id=_uuid(),
                    product_id=product.id,
                    allergen_id=all_id,
                    declaration_type=m.declaration_type or "declared",
                )
                db.add(pa)

    db.commit()

    saved = (
        db.query(Product)
        .options(
            joinedload(Product.nutrition_facts),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
        )
        .filter(Product.id == product_id)
        .first()
    )
    return ProductDetail.model_validate(saved)


@router.patch(
    "/products/{product_id}/verify",
    response_model=ProductDetail,
    summary="Admin verify or unverify product record",
)
def admin_verify_product(
    product_id: str,
    payload: AdminProductVerifyPayload,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product.is_verified = payload.is_verified
    if payload.verification_note is not None:
        product.verification_note = payload.verification_note
    db.commit()

    saved = (
        db.query(Product)
        .options(
            joinedload(Product.nutrition_facts),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
        )
        .filter(Product.id == product_id)
        .first()
    )
    return ProductDetail.model_validate(saved)


@router.delete(
    "/products/{product_id}",
    summary="Admin delete product record",
)
def admin_delete_product(
    product_id: str,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(product)
    db.commit()
    return {"message": "Product deleted successfully", "id": product_id}


# ===========================================================================
# 3. Ingredient & Allergen Management
# ===========================================================================

@router.get(
    "/ingredients",
    response_model=PaginatedIngredients,
    summary="Admin list ingredients with filtering",
)
def admin_list_ingredients(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    concern_level: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    query = db.query(Ingredient)
    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Ingredient.name.ilike(term),
                Ingredient.normalized_name.ilike(term),
                Ingredient.ins_number.ilike(term),
            )
        )
    if category:
        query = query.filter(Ingredient.category == category)
    if concern_level:
        query = query.filter(Ingredient.concern_level == concern_level)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    items = (
        query.order_by(Ingredient.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return PaginatedIngredients(
        items=[IngredientResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/ingredients",
    response_model=IngredientResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin create canonical ingredient",
)
def admin_create_ingredient(
    payload: AdminIngredientCreate,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    norm = (payload.normalized_name or payload.name).lower().strip()
    existing = db.query(Ingredient).filter(Ingredient.normalized_name == norm).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Ingredient with normalized name '{norm}' already exists")

    aliases_str = json.dumps(payload.aliases or [])
    ing = Ingredient(
        id=_uuid(),
        name=payload.name.strip(),
        normalized_name=norm,
        category=payload.category.strip() if payload.category else None,
        description=payload.description,
        aliases=aliases_str,
        purpose=payload.purpose,
        concern_level=payload.concern_level or "safe",
        ins_number=payload.ins_number.strip() if payload.ins_number else None,
        source_reference=payload.source_reference,
        is_common_allergen=payload.is_common_allergen,
    )
    db.add(ing)
    db.commit()
    db.refresh(ing)
    return IngredientResponse.model_validate(ing)


@router.put(
    "/ingredients/{ingredient_id}",
    response_model=IngredientResponse,
    summary="Admin update canonical ingredient",
)
def admin_update_ingredient(
    ingredient_id: str,
    payload: AdminIngredientUpdate,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    if payload.name is not None:
        ing.name = payload.name.strip()
    if payload.normalized_name is not None:
        ing.normalized_name = payload.normalized_name.lower().strip()
    if payload.category is not None:
        ing.category = payload.category.strip() if payload.category else None
    if payload.description is not None:
        ing.description = payload.description
    if payload.aliases is not None:
        ing.aliases = json.dumps(payload.aliases)
    if payload.purpose is not None:
        ing.purpose = payload.purpose
    if payload.concern_level is not None:
        ing.concern_level = payload.concern_level
    if payload.ins_number is not None:
        ing.ins_number = payload.ins_number.strip() if payload.ins_number else None
    if payload.source_reference is not None:
        ing.source_reference = payload.source_reference
    if payload.is_common_allergen is not None:
        ing.is_common_allergen = payload.is_common_allergen

    db.commit()
    db.refresh(ing)
    return IngredientResponse.model_validate(ing)


@router.delete(
    "/ingredients/{ingredient_id}",
    summary="Admin delete canonical ingredient",
)
def admin_delete_ingredient(
    ingredient_id: str,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    ing = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ing:
        raise HTTPException(status_code=404, detail="Ingredient not found")

    db.delete(ing)
    db.commit()
    return {"message": "Ingredient deleted successfully", "id": ingredient_id}


@router.get(
    "/allergens",
    response_model=List[AllergenResponse],
    summary="Admin list all canonical allergens",
)
def admin_list_allergens(
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    items = db.query(Allergen).order_by(Allergen.name.asc()).all()
    return [AllergenResponse.model_validate(a) for a in items]


@router.post(
    "/allergens",
    response_model=AllergenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Admin add allergen to registry",
)
def admin_create_allergen(
    payload: AdminAllergenCreate,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    existing = db.query(Allergen).filter(Allergen.name.ilike(payload.name.strip())).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Allergen '{payload.name}' already exists")

    allg = Allergen(
        id=_uuid(),
        name=payload.name.strip(),
        code=payload.code.strip() if payload.code else None,
        description=payload.description,
    )
    db.add(allg)
    db.commit()
    db.refresh(allg)
    return AllergenResponse.model_validate(allg)


# ===========================================================================
# 4. Scoring Rule Version Management
# ===========================================================================

@router.get(
    "/scoring-rules",
    response_model=List[ScoringRuleVersionResponse],
    summary="List all scoring rule versions",
)
def admin_list_scoring_rules(
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    """
    Returns all scoring rule versions. If database is fresh, initializes the default v1.0 version.
    """
    rules = db.query(ScoringRuleVersion).order_by(ScoringRuleVersion.created_at.desc()).all()
    if not rules:
        # Initialize default version from rules.py
        defaults = get_default_scoring_rules_dict()
        default_rule = ScoringRuleVersion(
            id=_uuid(),
            version=SCORING_RULE_VERSION,
            name="NutriLens Baseline Scoring Model v1.0",
            description="Initial deterministic scoring rules calibrated against WHO/ICMR references.",
            is_active=True,
            thresholds_food=defaults["thresholds_food"],
            thresholds_beverage=defaults["thresholds_beverage"],
            category_weights=defaults["category_weights"],
            general_weights=defaults["general_weights"],
        )
        db.add(default_rule)
        db.commit()
        db.refresh(default_rule)
        rules = [default_rule]

    return [ScoringRuleVersionResponse.model_validate(r) for r in rules]


@router.get(
    "/scoring-rules/{version_or_id}",
    response_model=ScoringRuleVersionResponse,
    summary="Get single scoring rule version details",
)
def admin_get_scoring_rule(
    version_or_id: str,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    rule = (
        db.query(ScoringRuleVersion)
        .filter(
            or_(
                ScoringRuleVersion.id == version_or_id,
                ScoringRuleVersion.version == version_or_id,
            )
        )
        .first()
    )
    if not rule:
        raise HTTPException(status_code=404, detail="Scoring rule version not found")
    return ScoringRuleVersionResponse.model_validate(rule)


@router.post(
    "/scoring-rules",
    response_model=ScoringRuleVersionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new scoring rule version and preserve previous versions",
)
def admin_create_scoring_rule_version(
    payload: ScoringRuleVersionCreate,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    """
    Validates thresholds and weights, then creates an immutable new scoring-rule version.
    """
    # 1. Version key unique check
    existing = db.query(ScoringRuleVersion).filter(ScoringRuleVersion.version == payload.version.strip()).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Scoring rule version '{payload.version}' already exists. Use a new version identifier.",
        )

    # 2. Defaults merging
    defaults = get_default_scoring_rules_dict()
    th_food = payload.thresholds_food or defaults["thresholds_food"]
    th_bev = payload.thresholds_beverage or defaults["thresholds_beverage"]
    cat_weights = payload.category_weights or defaults["category_weights"]
    gen_weights = payload.general_weights or defaults["general_weights"]

    # 3. Validation: thresholds low < moderate < high
    for nutrient, vals in th_food.items():
        if isinstance(vals, dict):
            low = vals.get("low", 0)
            mod = vals.get("moderate", 0)
            high = vals.get("high", 0)
            if not (low < mod < high):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid thresholds for food '{nutrient}': low ({low}) must be < moderate ({mod}) < high ({high})",
                )

    for nutrient, vals in th_bev.items():
        if isinstance(vals, dict):
            low = vals.get("low", 0)
            mod = vals.get("moderate", 0)
            high = vals.get("high", 0)
            if not (low < mod < high):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid thresholds for beverage '{nutrient}': low ({low}) must be < moderate ({mod}) < high ({high})",
                )

    # 4. If activated, deactivate other versions
    if payload.is_active:
        db.query(ScoringRuleVersion).update({ScoringRuleVersion.is_active: False})

    new_rule = ScoringRuleVersion(
        id=_uuid(),
        version=payload.version.strip(),
        name=payload.name.strip(),
        description=payload.description,
        is_active=payload.is_active,
        thresholds_food=th_food,
        thresholds_beverage=th_bev,
        category_weights=cat_weights,
        general_weights=gen_weights,
    )
    db.add(new_rule)
    db.commit()
    db.refresh(new_rule)
    return ScoringRuleVersionResponse.model_validate(new_rule)


@router.put(
    "/scoring-rules/{rule_id}/activate",
    response_model=ScoringRuleVersionResponse,
    summary="Activate a scoring rule version",
)
def admin_activate_scoring_rule(
    rule_id: str,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    rule = db.query(ScoringRuleVersion).filter(ScoringRuleVersion.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Scoring rule version not found")

    # Deactivate all others
    db.query(ScoringRuleVersion).update({ScoringRuleVersion.is_active: False})
    rule.is_active = True
    db.commit()
    db.refresh(rule)
    return ScoringRuleVersionResponse.model_validate(rule)


# ===========================================================================
# 5. User-Reported Issue Management
# ===========================================================================

@router.post(
    "/issues",
    response_model=ProductIssueResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Report incorrect information on a product",
)
def report_product_issue(
    payload: ProductIssueCreate,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Allows users to report data discrepancies or nutrition errors.
    """
    prod = db.query(Product).filter(Product.id == payload.product_id).first()
    if not prod:
        raise HTTPException(status_code=404, detail="Product not found")

    issue = ProductIssue(
        id=_uuid(),
        user_id=current_user.id if current_user else None,
        product_id=prod.id,
        issue_type=payload.issue_type,
        description=payload.description.strip(),
        proposed_correction=payload.proposed_correction,
        status="pending",
    )
    db.add(issue)
    db.commit()
    db.refresh(issue)

    return ProductIssueResponse(
        id=issue.id,
        user_id=issue.user_id,
        user_email=current_user.email if current_user else None,
        product_id=prod.id,
        product_name=prod.name,
        product_brand=prod.brand,
        issue_type=issue.issue_type,
        description=issue.description,
        proposed_correction=issue.proposed_correction,
        status=issue.status,
        admin_notes=issue.admin_notes,
        resolved_by=issue.resolved_by,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )


@router.get(
    "/issues",
    response_model=List[ProductIssueResponse],
    summary="Admin list reported data issues",
)
def admin_list_issues(
    issue_status: Optional[str] = Query(None, alias="status"),
    product_id: Optional[str] = Query(None),
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(ProductIssue)
        .options(joinedload(ProductIssue.product), joinedload(ProductIssue.user))
    )
    if issue_status:
        query = query.filter(ProductIssue.status == issue_status.lower())
    if product_id:
        query = query.filter(ProductIssue.product_id == product_id)

    items = query.order_by(ProductIssue.created_at.desc()).all()
    results = []
    for item in items:
        results.append(
            ProductIssueResponse(
                id=item.id,
                user_id=item.user_id,
                user_email=item.user.email if item.user else None,
                product_id=item.product_id,
                product_name=item.product.name if item.product else "Unknown Product",
                product_brand=item.product.brand if item.product else None,
                issue_type=item.issue_type,
                description=item.description,
                proposed_correction=item.proposed_correction,
                status=item.status,
                admin_notes=item.admin_notes,
                resolved_by=item.resolved_by,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )
    return results


@router.put(
    "/issues/{issue_id}",
    response_model=ProductIssueResponse,
    summary="Admin update and resolve reported issue",
)
def admin_update_issue(
    issue_id: str,
    payload: ProductIssueUpdate,
    admin_user: User = Depends(require_admin_user),
    db: Session = Depends(get_db),
):
    issue = (
        db.query(ProductIssue)
        .options(joinedload(ProductIssue.product), joinedload(ProductIssue.user))
        .filter(ProductIssue.id == issue_id)
        .first()
    )
    if not issue:
        raise HTTPException(status_code=404, detail="Issue report not found")

    issue.status = payload.status.lower()
    if payload.admin_notes is not None:
        issue.admin_notes = payload.admin_notes
    issue.resolved_by = admin_user.id

    db.commit()
    db.refresh(issue)

    return ProductIssueResponse(
        id=issue.id,
        user_id=issue.user_id,
        user_email=issue.user.email if issue.user else None,
        product_id=issue.product_id,
        product_name=issue.product.name if issue.product else "Unknown Product",
        product_brand=issue.product.brand if issue.product else None,
        issue_type=issue.issue_type,
        description=issue.description,
        proposed_correction=issue.proposed_correction,
        status=issue.status,
        admin_notes=issue.admin_notes,
        resolved_by=issue.resolved_by,
        created_at=issue.created_at,
        updated_at=issue.updated_at,
    )
