"""
Product categories endpoint (Day 3)
GET /categories – returns distinct categories with product counts
"""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.product import Product
from app.schemas.product import CategoryItem, CategoryListResponse

router = APIRouter()


@router.get(
    "",
    response_model=CategoryListResponse,
    summary="List all product categories with product counts",
)
def list_categories(db: Session = Depends(get_db)) -> CategoryListResponse:
    """Return distinct product categories sorted alphabetically with counts."""
    rows = (
        db.query(Product.category, func.count(Product.id).label("cnt"))
        .filter(Product.category.isnot(None))
        .group_by(Product.category)
        .order_by(Product.category)
        .all()
    )
    return CategoryListResponse(
        categories=[CategoryItem(name=row[0], product_count=row[1]) for row in rows]
    )
