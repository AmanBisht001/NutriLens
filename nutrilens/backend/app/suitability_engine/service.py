"""
NutriLens – Suitability Service Orchestrator (Day 6)
Coordinates dietary profile loading, product attribute extraction,
and rule-based suitability evaluation.
"""
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.product import Product, ProductIngredient, ProductAllergen
from app.models.user import User, UserProfile
from app.suitability_engine.rules import (
    STATUS_SUITABLE,
    STATUS_CAUTION,
    STATUS_CONFLICT,
    STATUS_INSUFFICIENT,
    SAFETY_DISCLAIMER,
    SUITABILITY_ENGINE_VERSION,
)
from app.suitability_engine.matcher import (
    evaluate_suitability,
    SuitabilityEvaluation,
)


def extract_product_data_for_suitability(product: Product) -> Dict[str, Any]:
    """Helper to convert SQLAlchemy Product into normalized dictionary for the matcher."""
    # 1. Ingredients
    ingredients_list: List[Dict[str, Any]] = []
    if product.product_ingredients:
        for pi in product.product_ingredients:
            ing_name = pi.ingredient.name if pi.ingredient else ""
            ingredients_list.append({
                "name": ing_name,
                "normalized_name": pi.ingredient.normalized_name if pi.ingredient else "",
                "original_text": pi.original_text or ing_name,
                "category": pi.ingredient.category if pi.ingredient else None,
            })

    # 2. Allergens
    allergens_list: List[Dict[str, Any]] = []
    if product.product_allergens:
        for pa in product.product_allergens:
            alg_name = pa.allergen.name if pa.allergen else ""
            allergens_list.append({
                "name": alg_name,
                "declaration_type": pa.declaration_type or "declared",
            })

    # 3. Nutrition Facts
    nf_dict: Optional[Dict[str, Optional[float]]] = None
    if product.nutrition_facts:
        nf = product.nutrition_facts
        nf_dict = {
            "energy_kcal": nf.energy_kcal,
            "total_fat_g": nf.total_fat_g,
            "saturated_fat_g": nf.saturated_fat_g,
            "trans_fat_g": nf.trans_fat_g,
            "carbohydrates_g": nf.carbohydrates_g,
            "total_sugar_g": nf.total_sugar_g,
            "added_sugar_g": nf.added_sugar_g,
            "dietary_fibre_g": nf.dietary_fibre_g,
            "protein_g": nf.protein_g,
            "sodium_mg": nf.sodium_mg,
        }

    return {
        "product_id": product.id,
        "product_name": product.name,
        "ingredients": ingredients_list,
        "allergens": allergens_list,
        "raw_ingredients_text": product.raw_ingredients_text,
        "nutrition_facts": nf_dict,
    }


def evaluate_product_suitability(
    product: Product,
    user_preference: Optional[str] = "None",
    user_allergies: Optional[List[str]] = None,
    user_restrictions: Optional[List[str]] = None,
    user_nutrition_goals: Optional[List[str]] = None,
    user_monitored_nutrients: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Evaluates personal suitability for a given Product against specified dietary preferences.
    Guarantees strict independence from the general NutriLens score.
    """
    pdata = extract_product_data_for_suitability(product)

    res: SuitabilityEvaluation = evaluate_suitability(
        product_name=pdata["product_name"],
        product_ingredients=pdata["ingredients"],
        product_allergens=pdata["allergens"],
        raw_ingredients_text=pdata["raw_ingredients_text"],
        nutrition_facts=pdata["nutrition_facts"],
        user_preference=user_preference,
        user_allergies=user_allergies or [],
        user_restrictions=user_restrictions or [],
        user_nutrition_goals=user_nutrition_goals or [],
        user_monitored_nutrients=user_monitored_nutrients or [],
    )

    return {
        "status": res.status,
        "status_label": res.status_label,
        "badge_color": res.badge_color,
        "is_suitable": res.is_suitable,
        "product_id": product.id,
        "product_name": product.name,
        "summary_narrative": res.summary_narrative,
        "evaluated_preferences": {
            "dietary_preference": user_preference or "None",
            "allergies": user_allergies or [],
            "dietary_restrictions": user_restrictions or [],
            "nutrition_goals": user_nutrition_goals or [],
            "monitored_nutrients": user_monitored_nutrients or [],
        },
        "conflicts": [
            {
                "category": c.category,
                "severity": c.severity,
                "title": c.title,
                "detail": c.detail,
                "source_ingredient": c.source_ingredient,
                "is_precautionary": c.is_precautionary,
            }
            for c in res.conflicts
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
            for c in res.cautions
        ],
        "positive_observations": [
            {
                "category": c.category,
                "severity": c.severity,
                "title": c.title,
                "detail": c.detail,
            }
            for c in res.positive_observations
        ],
        "safety_warnings": res.safety_warnings,
        "rules_applied": res.rules_applied,
        "engine_version": res.engine_version,
        "disclaimer": res.disclaimer,
    }


def get_user_dietary_profile(user_id: str, db: Session) -> Optional[UserProfile]:
    """Retrieves the dietary profile for a given user."""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def update_user_dietary_profile(
    user_id: str,
    dietary_preference: Optional[str],
    allergies: Optional[List[str]],
    dietary_restrictions: Optional[List[str]],
    nutrition_goals: Optional[List[str]],
    monitored_nutrients: Optional[List[str]],
    db: Session,
) -> UserProfile:
    """Updates user dietary preferences, allergies, goals, and monitored nutrients."""
    profile = get_user_dietary_profile(user_id, db)
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)

    if dietary_preference is not None:
        profile.dietary_preference = dietary_preference
    if allergies is not None:
        profile.allergies = allergies
    if dietary_restrictions is not None:
        profile.dietary_restrictions = dietary_restrictions
    if nutrition_goals is not None:
        profile.nutrition_goals = nutrition_goals
    if monitored_nutrients is not None:
        profile.monitored_nutrients = monitored_nutrients

    db.commit()
    db.refresh(profile)
    return profile
