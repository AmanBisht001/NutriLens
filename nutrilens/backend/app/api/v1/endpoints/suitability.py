"""
NutriLens – Personalized Dietary Suitability Endpoints (Day 6)
Handles:
- POST /api/products/{id}/suitability
- GET /api/profile/dietary-preferences
- PUT /api/profile/dietary-preferences
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import get_db, get_current_user_optional, get_current_active_user
from app.models.product import Product, ProductIngredient, ProductAllergen
from app.models.user import User, UserProfile
from app.schemas.suitability import SuitabilityRequest, SuitabilityResponse
from app.schemas.user import DietaryPreferencesPayload, DietaryPreferencesResponse
from app.suitability_engine.service import (
    evaluate_product_suitability,
    get_user_dietary_profile,
    update_user_dietary_profile,
)

router = APIRouter()


@router.post(
    "/products/{product_id}/suitability",
    response_model=SuitabilityResponse,
    summary="Evaluate personalized dietary suitability for a product",
)
def evaluate_product_personal_suitability(
    product_id: str,
    custom_request: Optional[SuitabilityRequest] = None,
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    """
    Evaluates whether a product is suitable for a user's dietary profile
    (allergies, dietary pattern, restrictions, nutrition goals, monitored nutrients).
    The general NutriLens nutrition score remains completely independent.
    """
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
            detail=f"Product with ID '{product_id}' was not found in the catalogue.",
        )

    # Determine user preferences from custom request payload or authenticated profile
    user_pref = "None"
    user_allergies = []
    user_restrictions = []
    user_goals = []
    user_monitored = []

    # 1. Base on authenticated user's profile if available
    if current_user and current_user.profile:
        p = current_user.profile
        user_pref = p.dietary_preference or "None"
        user_allergies = list(p.allergies or [])
        user_restrictions = list(p.dietary_restrictions or [])
        user_goals = list(p.nutrition_goals or [])
        user_monitored = list(p.monitored_nutrients or [])

    # 2. Override with custom request fields if supplied
    if custom_request:
        if custom_request.dietary_preference is not None:
            user_pref = custom_request.dietary_preference
        if custom_request.allergies is not None:
            user_allergies = custom_request.allergies
        if custom_request.dietary_restrictions is not None:
            user_restrictions = custom_request.dietary_restrictions
        if custom_request.nutrition_goals is not None:
            user_goals = custom_request.nutrition_goals
        if custom_request.monitored_nutrients is not None:
            user_monitored = custom_request.monitored_nutrients

    return evaluate_product_suitability(
        product=product,
        user_preference=user_pref,
        user_allergies=user_allergies,
        user_restrictions=user_restrictions,
        user_nutrition_goals=user_goals,
        user_monitored_nutrients=user_monitored,
    )


@router.get(
    "/profile/dietary-preferences",
    response_model=DietaryPreferencesResponse,
    summary="Get authenticated user's dietary preferences, allergies, and goals",
)
def get_user_dietary_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Retrieve current user's personal dietary profile."""
    profile = get_user_dietary_profile(current_user.id, db)
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)

    return DietaryPreferencesResponse(
        dietary_preference=profile.dietary_preference,
        allergies=profile.allergies or [],
        dietary_restrictions=profile.dietary_restrictions or [],
        nutrition_goals=profile.nutrition_goals or [],
        monitored_nutrients=profile.monitored_nutrients or [],
        updated_at=profile.updated_at,
    )


@router.put(
    "/profile/dietary-preferences",
    response_model=DietaryPreferencesResponse,
    summary="Update authenticated user's dietary preferences, allergies, and goals",
)
def update_user_dietary_preferences(
    payload: DietaryPreferencesPayload,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    """Update user's personal dietary profile settings."""
    profile = update_user_dietary_profile(
        user_id=current_user.id,
        dietary_preference=payload.dietary_preference,
        allergies=payload.allergies,
        dietary_restrictions=payload.dietary_restrictions,
        nutrition_goals=payload.nutrition_goals,
        monitored_nutrients=payload.monitored_nutrients,
        db=db,
    )
    return DietaryPreferencesResponse(
        dietary_preference=profile.dietary_preference,
        allergies=profile.allergies or [],
        dietary_restrictions=profile.dietary_restrictions or [],
        nutrition_goals=profile.nutrition_goals or [],
        monitored_nutrients=profile.monitored_nutrients or [],
        updated_at=profile.updated_at,
    )
