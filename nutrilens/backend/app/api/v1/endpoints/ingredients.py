"""
Ingredient knowledge base API endpoints (Day 3)
GET /ingredients          – paginated list with search + category filter
GET /ingredients/{id}     – full ingredient detail
"""
import math
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.product import Ingredient
from app.schemas.product import IngredientResponse, PaginatedIngredients

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedIngredients,
    summary="List ingredients with optional search and category filter",
)
def list_ingredients(
    search: Optional[str] = Query(None, description="Search by ingredient name or INS number"),
    category: Optional[str] = Query(None, description="Filter by ingredient category"),
    concern_level: Optional[str] = Query(None, description="Filter by concern level: safe | moderate | high"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> PaginatedIngredients:
    """List canonical ingredient entries with search and filtering."""
    query = db.query(Ingredient)

    if search:
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Ingredient.name.ilike(term),
                Ingredient.ins_number.ilike(term),
                Ingredient.normalized_name.ilike(term),
            )
        )

    if category:
        query = query.filter(Ingredient.category == category)

    if concern_level:
        query = query.filter(Ingredient.concern_level == concern_level)

    total = query.count()
    total_pages = max(1, math.ceil(total / page_size))
    offset = (page - 1) * page_size

    items = (
        query
        .order_by(Ingredient.name)
        .offset(offset)
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


@router.get(
    "/{ingredient_id}",
    response_model=IngredientResponse,
    summary="Get full ingredient detail",
)
def get_ingredient(
    ingredient_id: str,
    db: Session = Depends(get_db),
) -> IngredientResponse:
    """Return a single ingredient by ID with full knowledge-base detail."""
    ingredient = db.query(Ingredient).filter(Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingredient '{ingredient_id}' was not found.",
        )
    return IngredientResponse.model_validate(ingredient)
