"""
NutriLens – Alternative Recommendation Engine (Day 7)
Provides deterministic, personalized packaged food alternative recommendations
from the actual catalogue based on category compatibility, NutriLens score improvements,
dietary suitability, and user priorities.
"""
from typing import List, Optional, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.product import Product, ProductIngredient, ProductAllergen
from app.models.user import User
from app.schemas.user import DietaryPreferencesPayload
from app.schemas.comparison import (
    ProductAlternativesResponse,
    AlternativeRecommendationItem,
    VALID_PRIORITIES,
)
from app.scoring_engine.service import (
    extract_nutrient_dict_from_model,
    analyze_nutrition_payload,
)
from app.suitability_engine.service import evaluate_product_suitability
from app.comparison_engine.comparator import _resolve_user_preferences


def get_alternative_recommendations(
    db: Session,
    target_product_id: str,
    limit: int = 5,
    priorities: Optional[List[str]] = None,
    user_preferences: Optional[DietaryPreferencesPayload] = None,
    user: Optional[User] = None,
) -> ProductAlternativesResponse:
    """
    Deterministic alternative recommendation service.
    Recommends healthier and suitable alternative products from the catalogue.
    """
    # 1. Fetch target product
    target_product = (
        db.query(Product)
        .options(
            joinedload(Product.nutrition_facts),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
        )
        .filter(Product.id == target_product_id)
        .first()
    )

    if not target_product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID '{target_product_id}' was not found in the catalogue.",
        )

    # Resolve active dietary profile
    prefs = _resolve_user_preferences(user_preferences, user)

    # Analyze target product nutrients and score
    target_nutrients = extract_nutrient_dict_from_model(target_product.nutrition_facts)
    target_analysis = analyze_nutrition_payload(
        nutrients_per_100=target_nutrients,
        category=target_product.category,
        serving_size_str=target_product.serving_size,
    )
    target_score = target_analysis.get("score")

    # Target suitability
    target_suit = evaluate_product_suitability(
        product=target_product,
        user_preference=prefs["user_preference"],
        user_allergies=prefs["user_allergies"],
        user_restrictions=prefs["user_restrictions"],
        user_nutrition_goals=prefs["user_goals"],
        user_monitored_nutrients=prefs["monitored_nutrients"],
    )

    # 2. Filter & select candidate products from catalogue
    # Must NOT be the target product itself
    # Prefer same category first
    query = (
        db.query(Product)
        .options(
            joinedload(Product.nutrition_facts),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
        )
        .filter(Product.id != target_product.id)
    )

    # Check if there are candidates in the same category
    same_category_candidates = query.filter(Product.category == target_product.category).all()
    if len(same_category_candidates) >= 1:
        candidates = same_category_candidates
    else:
        # Fall back to entire catalogue if no products in same category
        candidates = query.all()

    # Deduplicate and validate priorities
    eval_priorities = priorities or []
    eval_priorities = [p for p in eval_priorities if p in VALID_PRIORITIES]
    if not eval_priorities:
        eval_priorities = ["lower_sugar", "higher_protein"]

    # 3. Evaluate each candidate deterministically
    recommendations: List[AlternativeRecommendationItem] = []

    for cand in candidates:
        cand_nutrients = extract_nutrient_dict_from_model(cand.nutrition_facts)
        missing_cand_nutrients = [k for k, v in cand_nutrients.items() if v is None]

        cand_analysis = analyze_nutrition_payload(
            nutrients_per_100=cand_nutrients,
            category=cand.category,
            serving_size_str=cand.serving_size,
        )

        # Exclude candidates with insufficient critical nutrition data
        if cand_analysis.get("status") == "insufficient_data":
            continue

        cand_score = cand_analysis.get("score")
        if cand_score is None:
            continue

        # Evaluate candidate suitability
        cand_suit = evaluate_product_suitability(
            product=cand,
            user_preference=prefs["user_preference"],
            user_allergies=prefs["user_allergies"],
            user_restrictions=prefs["user_restrictions"],
            user_nutrition_goals=prefs["user_goals"],
            user_monitored_nutrients=prefs["monitored_nutrients"],
        )

        cand_status = cand_suit.get("status", "Suitable based on available information")
        cand_badge = cand_suit.get("badge_color", "emerald")

        # Exclude candidates that trigger a declared restriction conflict for the user!
        # Safety rule: Never recommend a food with a declared allergy conflict
        if cand_status == "Declared restriction conflict":
            continue

        # Calculate match & ranking score
        # Base: candidate's NutriLens score
        match_score = float(cand_score)

        # Category compatibility bonus
        is_same_category = (cand.category == target_product.category)
        if is_same_category:
            match_score += 25.0

        # Suitability bonus
        if cand_status == "Suitable based on available information":
            match_score += 15.0
        elif cand_status == "Caution":
            match_score -= 5.0

        # Reasons and nutritional advantages
        reasons: List[str] = []
        advantages: List[str] = []

        # Compare NutriLens scores
        if target_score is not None:
            score_diff = cand_score - target_score
            if score_diff > 0:
                match_score += min(score_diff, 30.0)
                reasons.append(
                    f"Higher NutriLens Score: {cand_score}/100 (+{score_diff} pts over {target_product.name})"
                )

        # Category context
        if is_same_category and cand.category:
            reasons.append(f"Direct category match ({cand.category})")

        # Suitability reasoning
        target_status = target_suit.get("status")
        if cand_status == "Suitable based on available information":
            if target_status == "Declared restriction conflict":
                match_score += 30.0
                reasons.append("Resolves your profile restriction conflict (fully suitable)")
            elif len(prefs["user_allergies"]) > 0 or len(prefs["user_restrictions"]) > 0:
                reasons.append("Suitable for your declared dietary preferences and allergies")

        # Nutrient comparisons:
        # 1. Sugar
        cand_sugar = cand_nutrients.get("total_sugar_g")
        target_sugar = target_nutrients.get("total_sugar_g")
        if cand_sugar is not None and target_sugar is not None:
            sugar_diff = target_sugar - cand_sugar
            if sugar_diff > 0:
                pct = round((sugar_diff / target_sugar * 100)) if target_sugar > 0 else 100
                advantages.append(f"Contains {sugar_diff:.1f}g less sugar per 100g (-{pct}%)")
                if "lower_sugar" in eval_priorities:
                    match_score += min(sugar_diff * 1.5, 25.0)
                    reasons.append(f"Significantly lower sugar: {cand_sugar:.1f}g vs {target_sugar:.1f}g per 100g")

        # 2. Saturated Fat
        cand_sat_fat = cand_nutrients.get("saturated_fat_g")
        target_sat_fat = target_nutrients.get("saturated_fat_g")
        if cand_sat_fat is not None and target_sat_fat is not None:
            sat_diff = target_sat_fat - cand_sat_fat
            if sat_diff > 0:
                advantages.append(f"Lower saturated fat: {cand_sat_fat:.1f}g vs {target_sat_fat:.1f}g per 100g")
                if "lower_saturated_fat" in eval_priorities:
                    match_score += min(sat_diff * 2.0, 20.0)
                    reasons.append(f"Less saturated fat (-{sat_diff:.1f}g per 100g)")

        # 3. Sodium
        cand_sod = cand_nutrients.get("sodium_mg")
        target_sod = target_nutrients.get("sodium_mg")
        if cand_sod is not None and target_sod is not None:
            sod_diff = target_sod - cand_sod
            if sod_diff > 0:
                advantages.append(f"Contains {sod_diff:.0f}mg less sodium per 100g")
                if "lower_sodium" in eval_priorities:
                    match_score += min(sod_diff * 0.05, 20.0)
                    reasons.append(f"Reduced sodium ({cand_sod:.0f}mg vs {target_sod:.0f}mg)")

        # 4. Protein
        cand_prot = cand_nutrients.get("protein_g")
        target_prot = target_nutrients.get("protein_g")
        if cand_prot is not None and target_prot is not None:
            prot_diff = cand_prot - target_prot
            if prot_diff > 0:
                advantages.append(f"Provides {prot_diff:.1f}g more protein per 100g")
                if "higher_protein" in eval_priorities:
                    match_score += min(prot_diff * 2.5, 25.0)
                    reasons.append(f"Higher protein (+{prot_diff:.1f}g per 100g)")

        # 5. Fibre
        cand_fib = cand_nutrients.get("dietary_fibre_g")
        target_fib = target_nutrients.get("dietary_fibre_g")
        if cand_fib is not None and target_fib is not None:
            fib_diff = cand_fib - target_fib
            if fib_diff > 0:
                advantages.append(f"Higher dietary fibre: +{fib_diff:.1f}g per 100g")
                if "higher_fibre" in eval_priorities:
                    match_score += min(fib_diff * 2.5, 25.0)
                    reasons.append(f"More dietary fibre (+{fib_diff:.1f}g)")

        # Ensure at least one traceable explanation exists
        if not reasons:
            if cand_score > (target_score or 0):
                reasons.append(f"Overall healthier choice with NutriLens Score {cand_score}/100")
            else:
                reasons.append("Comparable alternative from the verified catalogue")

        recommendations.append(
            AlternativeRecommendationItem(
                product_id=cand.id,
                name=cand.name,
                brand=cand.brand,
                category=cand.category,
                serving_size=cand.serving_size,
                label_image_url=cand.label_image_url,
                score=cand_score,
                grade=cand_analysis.get("grade"),
                rating_label=cand_analysis.get("rating_label"),
                rating_color=cand_analysis.get("rating_color"),
                suitability_status=cand_status,
                suitability_badge=cand_badge,
                match_score=round(match_score, 1),
                reasons=reasons,
                nutritional_advantages=advantages,
                nutrients_per_100=cand_nutrients,
                missing_nutrients=missing_cand_nutrients,
            )
        )

    # Sort candidates by match_score descending
    recommendations.sort(key=lambda r: r.match_score, reverse=True)

    # Slice top results
    top_recommendations = recommendations[: max(1, min(limit, 20))]

    return ProductAlternativesResponse(
        target_product_id=target_product.id,
        target_product_name=target_product.name,
        target_category=target_product.category,
        target_score=target_score,
        applied_priorities=eval_priorities,
        total_candidates_evaluated=len(candidates),
        alternatives=top_recommendations,
    )
