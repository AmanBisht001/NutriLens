"""
Product Catalogue API endpoints (Day 3)
GET /products          – paginated list with search + filter
GET /products/{id}     – full product detail
GET /categories        – distinct categories with counts
"""
import math
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_db, get_current_user_optional
from app.models.product import (
    Allergen, NutritionFacts, Product, ProductIngredient, ProductAllergen, Ingredient
)
from app.models.user import User
from app.schemas.product import (
    CategoryItem,
    CategoryListResponse,
    PaginatedProducts,
    ProductDetail,
    ProductSummary,
)
from app.schemas.comparison import (
    ComparisonRequest,
    ComparisonMatrixResponse,
    ProductAlternativesResponse,
)
from app.comparison_engine.comparator import compare_products
from app.comparison_engine.recommendations import get_alternative_recommendations

logger = logging.getLogger(__name__)
router = APIRouter()


# ---------------------------------------------------------------------------
# GET /products
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=PaginatedProducts,
    summary="List products with search and category filter",
)
def list_products(
    search: Optional[str] = Query(None, description="Search by product name or brand"),
    category: Optional[str] = Query(None, description="Filter by exact category name"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
    db: Session = Depends(get_db),
) -> PaginatedProducts:
    """Return paginated product catalogue. Supports name/brand search and category filter."""
    query = db.query(Product)

    if search:
        words = search.strip().split()
        for word in words:
            term = f"%{word}%"
            query = query.filter(
                or_(
                    Product.name.ilike(term),
                    Product.brand.ilike(term),
                )
            )

    if category:
        query = query.filter(Product.category == category)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    products = (
        query
        .options(joinedload(Product.nutrition_facts))
        .order_by(Product.name)
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return PaginatedProducts(
        items=[ProductSummary.model_validate(p) for p in products],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


# ---------------------------------------------------------------------------
# POST /products/compare (Day 7)
# ---------------------------------------------------------------------------

@router.post(
    "/compare",
    response_model=ComparisonMatrixResponse,
    summary="Compare two or more products side-by-side with priority rankings",
)
def compare_products_endpoint(
    payload: ComparisonRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> ComparisonMatrixResponse:
    """
    Compare 2 to 6 products side-by-side.
    Normalizes nutritional metrics (per 100g / 100ml), preserves missing values,
    evaluates user priorities, cross-checks declared restrictions, and identifies trade-offs.
    """
    return compare_products(
        db=db,
        product_ids=payload.product_ids,
        priorities=payload.priorities,
        user_preferences=payload.user_preferences,
        user=current_user,
    )


# ---------------------------------------------------------------------------
# GET /products/{product_id}/alternatives (Day 7)
# ---------------------------------------------------------------------------

@router.get(
    "/{product_id}/alternatives",
    response_model=ProductAlternativesResponse,
    summary="Get personalized alternative recommendations for a product",
)
def get_product_alternatives_endpoint(
    product_id: str,
    limit: int = Query(5, ge=1, le=20, description="Max recommendations to return"),
    priorities: Optional[str] = Query(
        None,
        description="Comma-separated user priorities (e.g. 'lower_sugar,higher_protein')",
    ),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> ProductAlternativesResponse:
    """
    Deterministic alternative recommendation service.
    Recommends healthier/compatible alternative packaged items from the actual catalogue.
    """
    priority_list = [p.strip() for p in priorities.split(",")] if priorities else None
    return get_alternative_recommendations(
        db=db,
        target_product_id=product_id,
        limit=limit,
        priorities=priority_list,
        user_preferences=None,
        user=current_user,
    )


# ---------------------------------------------------------------------------
# GET /products/{id}
# ---------------------------------------------------------------------------

@router.get(
    "/{product_id}",
    response_model=ProductDetail,
    summary="Get full product detail including ingredients and allergens",
)
def get_product(
    product_id: str,
    db: Session = Depends(get_db),
) -> ProductDetail:
    """Return complete product data: nutrition facts, resolved ingredient list, allergens."""
    product = (
        db.query(Product)
        .options(
            joinedload(Product.nutrition_facts),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
        )
        .filter(Product.id == product_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{product_id}' was not found in the catalogue.",
        )
    prod_data = ProductDetail.model_validate(product)

    # Compute deterministic nutrition analysis
    from app.scoring_engine.service import (
        analyze_nutrition_payload,
        extract_nutrient_dict_from_model,
    )
    nutrients = extract_nutrient_dict_from_model(product.nutrition_facts)
    prod_data.nutrition_analysis = analyze_nutrition_payload(
        nutrients_per_100=nutrients,
        category=product.category,
        serving_size_str=product.serving_size,
    )
    return prod_data


@router.post(
    "/{product_id}/report-issue",
    summary="Report data inaccuracy or wrong label information on product",
    status_code=status.HTTP_201_CREATED,
)
def report_product_issue_endpoint(
    product_id: str,
    payload: dict,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """Allows consumers to report incorrect nutrition, ingredients, or allergens."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    from app.models.issue import ProductIssue
    import uuid

    issue = ProductIssue(
        id=str(uuid.uuid4()),
        user_id=current_user.id if current_user else None,
        product_id=product.id,
        issue_type=payload.get("issue_type", "incorrect_nutrition"),
        description=payload.get("description", "").strip(),
        proposed_correction=payload.get("proposed_correction"),
        status="pending",
    )
    if not issue.description:
        raise HTTPException(status_code=400, detail="Description is required")

    db.add(issue)
    db.commit()
    db.refresh(issue)

    return {
        "message": "Thank you for reporting this issue. Our administrative review team will verify the package label.",
        "issue_id": issue.id,
        "status": issue.status,
    }
