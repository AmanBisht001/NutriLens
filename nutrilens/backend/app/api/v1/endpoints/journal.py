"""
NutriLens – Food Journal & Nutrition Analytics Endpoints (Day 8)
Handles:
- POST /api/journal (log food consumption)
- GET /api/journal (list logged meals with filters)
- GET /api/journal/summary/daily (daily total nutrients & meal groups)
- GET /api/journal/analytics/weekly (7-day trend aggregations)
- GET /api/journal/analytics/monthly (30-day / monthly trend aggregations)
- GET /api/journal/analytics/frequent (frequently consumed products)
- GET /api/journal/{entry_id} (get specific entry)
- PUT /api/journal/{entry_id} (update entry)
- DELETE /api/journal/{entry_id} (delete entry)
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_db, get_current_active_user
from app.models.journal import FoodJournalEntry
from app.models.product import Product
from app.models.user import User
from app.schemas.journal import (
    JournalEntryCreate,
    JournalEntryUpdate,
    JournalEntryResponse,
    JournalEntryListResponse,
    DailyJournalSummaryResponse,
    WeeklyAnalyticsResponse,
    MonthlyAnalyticsResponse,
    FrequentProductsResponse,
)
from app.journal_engine import (
    calculate_entry_weight,
    build_daily_summary,
    build_weekly_analytics,
    build_monthly_analytics,
    get_frequently_consumed_products,
)
from app.journal_engine.analytics import entry_to_response

router = APIRouter()


@router.post(
    "",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Log consumed food product into personal journal",
)
def create_journal_entry(
    payload: JournalEntryCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Explicitly logs a consumed food product for the authenticated user.
    Nutrients are scaled to actual consumed weight; scanning alone does not create journal records.
    """
    product = (
        db.query(Product)
        .options(joinedload(Product.nutrition_facts))
        .filter(Product.id == payload.product_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{payload.product_id}' not found",
        )

    consumed_time = payload.consumed_at or datetime.now(timezone.utc)

    total_weight = calculate_entry_weight(
        quantity=payload.quantity,
        serving_unit=payload.serving_unit,
        serving_size_g=payload.serving_size_g,
        total_weight_g=payload.total_weight_g,
        product_serving_size_str=product.serving_size,
    )

    entry = FoodJournalEntry(
        user_id=current_user.id,
        product_id=product.id,
        consumed_at=consumed_time,
        meal_type=payload.meal_type.lower() if payload.meal_type else "snack",
        quantity=payload.quantity,
        serving_unit=payload.serving_unit,
        serving_size_g=payload.serving_size_g,
        total_weight_g=total_weight,
        notes=payload.notes,
    )

    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry_to_response(entry)


@router.get(
    "",
    response_model=JournalEntryListResponse,
    summary="List authenticated user's journal entries",
)
def list_journal_entries(
    target_date: Optional[str] = Query(None, alias="date", description="Filter by date YYYY-MM-DD"),
    start_date: Optional[str] = Query(None, description="Start date YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="End date YYYY-MM-DD"),
    meal_type: Optional[str] = Query(None, description="Filter by meal type (breakfast, lunch, dinner, snack, other)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Lists consumption entries belonging strictly to the authenticated user.
    """
    query = (
        db.query(FoodJournalEntry)
        .options(
            joinedload(FoodJournalEntry.product).joinedload(Product.nutrition_facts)
        )
        .filter(FoodJournalEntry.user_id == current_user.id)
    )

    if target_date:
        try:
            d_val = datetime.strptime(target_date, "%Y-%m-%d").date()
            d_start = datetime(d_val.year, d_val.month, d_val.day, 0, 0, 0, tzinfo=timezone.utc)
            d_end = datetime(d_val.year, d_val.month, d_val.day, 23, 59, 59, 999999, tzinfo=timezone.utc)
            query = query.filter(FoodJournalEntry.consumed_at >= d_start, FoodJournalEntry.consumed_at <= d_end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

    if start_date:
        try:
            sd_val = datetime.strptime(start_date, "%Y-%m-%d").date()
            sd_start = datetime(sd_val.year, sd_val.month, sd_val.day, 0, 0, 0, tzinfo=timezone.utc)
            query = query.filter(FoodJournalEntry.consumed_at >= sd_start)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format. Expected YYYY-MM-DD.")

    if end_date:
        try:
            ed_val = datetime.strptime(end_date, "%Y-%m-%d").date()
            ed_end = datetime(ed_val.year, ed_val.month, ed_val.day, 23, 59, 59, 999999, tzinfo=timezone.utc)
            query = query.filter(FoodJournalEntry.consumed_at <= ed_end)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Expected YYYY-MM-DD.")

    if meal_type:
        query = query.filter(FoodJournalEntry.meal_type == meal_type.lower())

    total = query.count()
    entries = (
        query.order_by(FoodJournalEntry.consumed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [entry_to_response(e) for e in entries]

    return JournalEntryListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/summary/daily",
    response_model=DailyJournalSummaryResponse,
    summary="Get daily nutritional totals and meal group breakdown",
)
def get_daily_journal_summary(
    target_date: Optional[str] = Query(None, alias="date", description="Target date YYYY-MM-DD (defaults to today)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Computes daily nutritional totals, meal breakdown, and goal progress.
    """
    if target_date:
        try:
            d_val = datetime.strptime(target_date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")
    else:
        d_val = datetime.now(timezone.utc).date()

    d_str = d_val.isoformat()
    d_start = datetime(d_val.year, d_val.month, d_val.day, 0, 0, 0, tzinfo=timezone.utc)
    d_end = datetime(d_val.year, d_val.month, d_val.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

    entries = (
        db.query(FoodJournalEntry)
        .options(
            joinedload(FoodJournalEntry.product).joinedload(Product.nutrition_facts)
        )
        .filter(
            FoodJournalEntry.user_id == current_user.id,
            FoodJournalEntry.consumed_at >= d_start,
            FoodJournalEntry.consumed_at <= d_end,
        )
        .order_by(FoodJournalEntry.consumed_at.asc())
        .all()
    )

    return build_daily_summary(
        entries=entries,
        target_date=d_str,
        user_profile=current_user.profile,
    )


@router.get(
    "/analytics/weekly",
    response_model=WeeklyAnalyticsResponse,
    summary="Get 7-day longitudinal daily nutritional trends",
)
def get_weekly_analytics(
    end_date_str: Optional[str] = Query(None, alias="end_date", description="End date YYYY-MM-DD (defaults to today)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Computes 7-day daily trend series (calories, sugar, sodium, protein, fibre, fat, carbs)
    and daily average metrics.
    """
    if end_date_str:
        try:
            ed_val = datetime.strptime(end_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format. Expected YYYY-MM-DD.")
    else:
        ed_val = datetime.now(timezone.utc).date()

    sd_val = ed_val - timedelta(days=6)
    d_start = datetime(sd_val.year, sd_val.month, sd_val.day, 0, 0, 0, tzinfo=timezone.utc)
    d_end = datetime(ed_val.year, ed_val.month, ed_val.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

    entries = (
        db.query(FoodJournalEntry)
        .options(
            joinedload(FoodJournalEntry.product).joinedload(Product.nutrition_facts)
        )
        .filter(
            FoodJournalEntry.user_id == current_user.id,
            FoodJournalEntry.consumed_at >= d_start,
            FoodJournalEntry.consumed_at <= d_end,
        )
        .order_by(FoodJournalEntry.consumed_at.asc())
        .all()
    )

    return build_weekly_analytics(
        entries=entries,
        start_date=sd_val,
        end_date=ed_val,
    )


@router.get(
    "/analytics/monthly",
    response_model=MonthlyAnalyticsResponse,
    summary="Get 30-day / monthly nutritional trends",
)
def get_monthly_analytics(
    year: Optional[int] = Query(None, description="Year (e.g. 2026)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Month (1-12)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Computes 30-day monthly longitudinal trends and summary averages.
    """
    now = datetime.now(timezone.utc)
    target_year = year or now.year
    target_month = month or now.month

    # Build 30-day window ending at target month end or today
    if year and month:
        import calendar
        _, last_day = calendar.monthrange(target_year, target_month)
        sd_val = date(target_year, target_month, 1)
        ed_val = date(target_year, target_month, last_day)
    else:
        ed_val = now.date()
        sd_val = ed_val - timedelta(days=29)

    d_start = datetime(sd_val.year, sd_val.month, sd_val.day, 0, 0, 0, tzinfo=timezone.utc)
    d_end = datetime(ed_val.year, ed_val.month, ed_val.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

    entries = (
        db.query(FoodJournalEntry)
        .options(
            joinedload(FoodJournalEntry.product).joinedload(Product.nutrition_facts)
        )
        .filter(
            FoodJournalEntry.user_id == current_user.id,
            FoodJournalEntry.consumed_at >= d_start,
            FoodJournalEntry.consumed_at <= d_end,
        )
        .order_by(FoodJournalEntry.consumed_at.asc())
        .all()
    )

    return build_monthly_analytics(
        entries=entries,
        year=target_year,
        month=target_month,
        start_date=sd_val,
        end_date=ed_val,
    )


@router.get(
    "/analytics/frequent",
    response_model=FrequentProductsResponse,
    summary="Get user's frequently consumed packaged foods",
)
def get_frequent_products(
    limit: int = Query(10, ge=1, le=50, description="Max items to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Aggregates top logged products from the user's personal journal history.
    """
    return get_frequently_consumed_products(
        db=db,
        user_id=current_user.id,
        limit=limit,
    )


@router.get(
    "/{entry_id}",
    response_model=JournalEntryResponse,
    summary="Get single journal entry by ID",
)
def get_journal_entry(
    entry_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Retrieves a single journal entry, strictly isolated to the authenticated user.
    """
    entry = (
        db.query(FoodJournalEntry)
        .options(
            joinedload(FoodJournalEntry.product).joinedload(Product.nutrition_facts)
        )
        .filter(
            FoodJournalEntry.id == entry_id,
            FoodJournalEntry.user_id == current_user.id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry '{entry_id}' not found",
        )

    return entry_to_response(entry)


@router.put(
    "/{entry_id}",
    response_model=JournalEntryResponse,
    summary="Update a journal entry",
)
def update_journal_entry(
    entry_id: str,
    payload: JournalEntryUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Updates an existing journal entry and re-calculates scaled nutritional values.
    """
    entry = (
        db.query(FoodJournalEntry)
        .options(
            joinedload(FoodJournalEntry.product).joinedload(Product.nutrition_facts)
        )
        .filter(
            FoodJournalEntry.id == entry_id,
            FoodJournalEntry.user_id == current_user.id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry '{entry_id}' not found",
        )

    if payload.consumed_at is not None:
        entry.consumed_at = payload.consumed_at
    if payload.meal_type is not None:
        entry.meal_type = payload.meal_type.lower()
    if payload.quantity is not None:
        entry.quantity = payload.quantity
    if payload.serving_unit is not None:
        entry.serving_unit = payload.serving_unit
    if payload.serving_size_g is not None:
        entry.serving_size_g = payload.serving_size_g
    if payload.notes is not None:
        entry.notes = payload.notes

    # Recompute total_weight_g if weight or quantity fields changed
    if payload.total_weight_g is not None:
        entry.total_weight_g = payload.total_weight_g
    elif payload.quantity is not None or payload.serving_size_g is not None:
        entry.total_weight_g = calculate_entry_weight(
            quantity=entry.quantity,
            serving_unit=entry.serving_unit,
            serving_size_g=entry.serving_size_g,
            total_weight_g=None,
            product_serving_size_str=entry.product.serving_size if entry.product else None,
        )

    db.commit()
    db.refresh(entry)

    return entry_to_response(entry)


@router.delete(
    "/{entry_id}",
    summary="Delete a journal entry",
)
def delete_journal_entry(
    entry_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """
    Deletes a consumption entry owned by the authenticated user.
    """
    entry = (
        db.query(FoodJournalEntry)
        .filter(
            FoodJournalEntry.id == entry_id,
            FoodJournalEntry.user_id == current_user.id,
        )
        .first()
    )
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Journal entry '{entry_id}' not found",
        )

    db.delete(entry)
    db.commit()

    return {"message": "Journal entry deleted successfully", "id": entry_id}
