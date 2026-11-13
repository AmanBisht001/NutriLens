"""
NutriLens – Product Comparison Engine (Day 7)
Compares 2 or more products across standardized nutritional values,
NutriLens scores, ingredients, allergens, personal suitability, and user priorities.
"""
from typing import List, Optional, Dict, Any, Set
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models.product import Product, ProductIngredient, ProductAllergen
from app.models.user import User
from app.schemas.user import DietaryPreferencesPayload
from app.schemas.comparison import (
    ProductComparisonItem,
    PriorityEvaluationItem,
    PriorityRanking,
    ComparisonMatrixResponse,
    VALID_PRIORITIES,
)
from app.scoring_engine.service import (
    extract_nutrient_dict_from_model,
    analyze_nutrition_payload,
)
from app.scoring_engine.calculator import (
    parse_serving_size,
    calculate_serving_values,
)
from app.scoring_engine.rules import get_category_config, UNIT_PER_100ML, UNIT_PER_100G
from app.suitability_engine.service import evaluate_product_suitability


PRIORITY_LABELS: Dict[str, str] = {
    "lower_sugar": "Lower Sugar",
    "lower_sodium": "Lower Sodium",
    "lower_saturated_fat": "Lower Saturated Fat",
    "higher_protein": "Higher Protein",
    "higher_fibre": "Higher Fibre",
    "fewer_restriction_conflicts": "Fewer Restriction Conflicts",
}


def _resolve_user_preferences(
    user_preferences: Optional[DietaryPreferencesPayload],
    user: Optional[User],
) -> Dict[str, Any]:
    """Helper to extract active user dietary profile parameters."""
    if user_preferences:
        return {
            "user_preference": user_preferences.dietary_preference or "None",
            "user_allergies": user_preferences.allergies or [],
            "user_restrictions": user_preferences.dietary_restrictions or [],
            "user_goals": user_preferences.nutrition_goals or [],
            "monitored_nutrients": user_preferences.monitored_nutrients or [],
        }

    if user and user.profile:
        prof = user.profile
        return {
            "user_preference": prof.dietary_preference or "None",
            "user_allergies": prof.allergies or [],
            "user_restrictions": prof.dietary_restrictions or [],
            "user_goals": prof.nutrition_goals or [],
            "monitored_nutrients": getattr(prof, "monitored_nutrients", []) or [],
        }

    return {
        "user_preference": "None",
        "user_allergies": [],
        "user_restrictions": [],
        "user_goals": [],
        "monitored_nutrients": [],
    }


def compare_products(
    db: Session,
    product_ids: List[str],
    priorities: Optional[List[str]] = None,
    user_preferences: Optional[DietaryPreferencesPayload] = None,
    user: Optional[User] = None,
) -> ComparisonMatrixResponse:
    """
    Core product comparison service.
    Normalizes comparable metrics, preserves missing data states,
    evaluates user priorities, and calculates ingredient/allergen overlaps.
    """
    if len(product_ids) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 products are required for comparison.",
        )

    # 1. Fetch products from database
    products_db = (
        db.query(Product)
        .options(
            joinedload(Product.nutrition_facts),
            selectinload(Product.product_ingredients).joinedload(ProductIngredient.ingredient),
            selectinload(Product.product_allergens).joinedload(ProductAllergen.allergen),
        )
        .filter(Product.id.in_(product_ids))
        .all()
    )

    # Map by id to preserve order requested
    product_map = {p.id: p for p in products_db}
    ordered_products: List[Product] = [product_map[pid] for pid in product_ids if pid in product_map]

    if len(ordered_products) < 2:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Could not find at least 2 valid products in the catalogue for the provided IDs. Found {len(ordered_products)}.",
        )

    # Resolve active dietary profile for suitability checks
    prefs = _resolve_user_preferences(user_preferences, user)

    # 2. Build normalized comparison items
    items: List[ProductComparisonItem] = []
    all_ingredients_sets: List[Set[str]] = []
    all_allergens_sets: List[Set[str]] = []

    for prod in ordered_products:
        config = get_category_config(prod.category)
        is_liquid = config.is_liquid
        standard_unit = UNIT_PER_100ML if is_liquid else UNIT_PER_100G

        # Nutrients (per 100g / 100ml)
        nutrients_per_100 = extract_nutrient_dict_from_model(prod.nutrition_facts)
        missing_nutrients = [k for k, v in nutrients_per_100.items() if v is None]

        # Per serving values
        serving_qty, _ = parse_serving_size(prod.serving_size)
        nutrients_per_serving = calculate_serving_values(nutrients_per_100, serving_qty)

        # Deterministic scoring
        analysis = analyze_nutrition_payload(
            nutrients_per_100=nutrients_per_100,
            category=prod.category,
            serving_size_str=prod.serving_size,
        )

        # Personal suitability evaluation
        suit_eval = evaluate_product_suitability(
            product=prod,
            user_preference=prefs["user_preference"],
            user_allergies=prefs["user_allergies"],
            user_restrictions=prefs["user_restrictions"],
            user_nutrition_goals=prefs["user_goals"],
            user_monitored_nutrients=prefs["monitored_nutrients"],
        )

        conflict_titles = [c["title"] for c in suit_eval.get("conflicts", [])]

        # Ingredients list
        ing_names: List[str] = []
        if prod.product_ingredients:
            for pi in prod.product_ingredients:
                if pi.ingredient and pi.ingredient.name:
                    ing_names.append(pi.ingredient.name)
        elif prod.raw_ingredients_text:
            # Fallback to raw text items
            ing_names = [item.strip() for item in prod.raw_ingredients_text.split(",") if item.strip()]

        # Allergens lists
        declared_allergens: List[str] = []
        precautionary_allergens: List[str] = []
        if prod.product_allergens:
            for pa in prod.product_allergens:
                if pa.allergen and pa.allergen.name:
                    if pa.declaration_type == "declared":
                        declared_allergens.append(pa.allergen.name)
                    else:
                        precautionary_allergens.append(pa.allergen.name)

        all_ingredients_sets.append({ing.lower() for ing in ing_names})
        all_allergens_sets.append({alg.lower() for alg in declared_allergens})

        items.append(
            ProductComparisonItem(
                product_id=prod.id,
                name=prod.name,
                brand=prod.brand,
                category=prod.category,
                serving_size=prod.serving_size,
                label_image_url=prod.label_image_url,
                standard_unit=standard_unit,
                score=analysis.get("score"),
                grade=analysis.get("grade"),
                rating_label=analysis.get("rating_label"),
                rating_color=analysis.get("rating_color"),
                data_completeness_pct=analysis.get("data_completeness_pct", 0.0),
                nutrients_per_100=nutrients_per_100,
                nutrients_per_serving=nutrients_per_serving,
                missing_nutrients=missing_nutrients,
                ingredients=ing_names,
                allergens_declared=declared_allergens,
                allergens_precautionary=precautionary_allergens,
                suitability_status=suit_eval["status"],
                suitability_badge=suit_eval["badge_color"],
                suitability_conflicts=conflict_titles,
                price=None,  # Price is only populated when verified data exists
                price_display="Not declared",
            )
        )

    # 3. Intersections: Common ingredients and common allergens
    common_ingredients_set = all_ingredients_sets[0].intersection(*all_ingredients_sets[1:]) if all_ingredients_sets else set()
    # Format common ingredients title-cased
    common_ingredients = sorted([ing.title() for ing in common_ingredients_set])

    common_allergens_set = all_allergens_sets[0].intersection(*all_allergens_sets[1:]) if all_allergens_sets else set()
    common_allergens = sorted([alg.title() for alg in common_allergens_set])

    # 4. User priorities evaluation
    eval_priorities = priorities or []
    # Deduplicate and validate
    eval_priorities = [p for p in eval_priorities if p in VALID_PRIORITIES]
    if not eval_priorities:
        # Default priority set for comprehensive comparison
        eval_priorities = ["lower_sugar", "higher_protein", "fewer_restriction_conflicts"]

    priority_evaluations: List[PriorityEvaluationItem] = []
    for prio in eval_priorities:
        eval_item = _evaluate_single_priority(prio, items)
        if eval_item:
            priority_evaluations.append(eval_item)

    # 5. Formulate human-readable summary narrative
    summary = _build_comparison_summary(items, priority_evaluations)

    return ComparisonMatrixResponse(
        products=items,
        common_ingredients=common_ingredients,
        common_allergens=common_allergens,
        priorities_evaluated=eval_priorities,
        priority_evaluations=priority_evaluations,
        summary=summary,
    )


def _evaluate_single_priority(
    priority: str,
    items: List[ProductComparisonItem],
) -> Optional[PriorityEvaluationItem]:
    """Evaluates a single priority across compared products."""
    label = PRIORITY_LABELS.get(priority, priority.replace("_", " ").title())

    # Map priority to target nutrient or attribute
    if priority == "lower_sugar":
        # Lower sugar (total_sugar_g) is better
        ranked: List[PriorityRanking] = []
        valid_items = []
        for it in items:
            val = it.nutrients_per_100.get("total_sugar_g")
            valid_items.append((it, val))

        # Sort: items with numbers ascending, None at the end
        sorted_items = sorted(
            valid_items,
            key=lambda x: (x[1] is None, x[1] if x[1] is not None else float("inf")),
        )

        for idx, (it, val) in enumerate(sorted_items, start=1):
            note = f"{val:.1f}g sugar/{it.standard_unit}" if val is not None else "Sugar content not declared"
            ranked.append(
                PriorityRanking(
                    product_id=it.product_id,
                    product_name=it.name,
                    value=val,
                    unit="g",
                    rank=idx,
                    note=note,
                )
            )

        best = sorted_items[0] if sorted_items and sorted_items[0][1] is not None else None
        worst = sorted_items[-1] if sorted_items and sorted_items[-1][1] is not None else None

        if best and worst and best[0].product_id != worst[0].product_id:
            diff = worst[1] - best[1]
            pct = round((diff / worst[1] * 100)) if worst[1] > 0 else 0
            summary = (
                f"{best[0].name} has the lowest sugar at {best[1]:.1f}g/{best[0].standard_unit} "
                f"({diff:.1f}g or {pct}% less than {worst[0].name})."
            )
        elif best:
            summary = f"{best[0].name} leads on sugar reduction at {best[1]:.1f}g/{best[0].standard_unit}."
        else:
            summary = "Sugar data is not declared for the compared products."

        return PriorityEvaluationItem(
            priority=priority,
            priority_label=label,
            best_product_id=best[0].product_id if best else None,
            best_product_name=best[0].name if best else None,
            summary=summary,
            rankings=ranked,
        )

    elif priority == "lower_sodium":
        ranked = []
        valid_items = [(it, it.nutrients_per_100.get("sodium_mg")) for it in items]
        sorted_items = sorted(
            valid_items,
            key=lambda x: (x[1] is None, x[1] if x[1] is not None else float("inf")),
        )
        for idx, (it, val) in enumerate(sorted_items, start=1):
            note = f"{val:.0f}mg sodium/{it.standard_unit}" if val is not None else "Sodium not declared"
            ranked.append(
                PriorityRanking(
                    product_id=it.product_id,
                    product_name=it.name,
                    value=val,
                    unit="mg",
                    rank=idx,
                    note=note,
                )
            )
        best = sorted_items[0] if sorted_items and sorted_items[0][1] is not None else None
        worst = sorted_items[-1] if sorted_items and sorted_items[-1][1] is not None else None
        if best and worst and best[0].product_id != worst[0].product_id:
            diff = worst[1] - best[1]
            summary = (
                f"{best[0].name} has the lowest sodium at {best[1]:.0f}mg/{best[0].standard_unit} "
                f"({diff:.0f}mg less than {worst[0].name})."
            )
        elif best:
            summary = f"{best[0].name} has the lowest sodium at {best[1]:.0f}mg/{best[0].standard_unit}."
        else:
            summary = "Sodium content is not declared for the compared products."

        return PriorityEvaluationItem(
            priority=priority,
            priority_label=label,
            best_product_id=best[0].product_id if best else None,
            best_product_name=best[0].name if best else None,
            summary=summary,
            rankings=ranked,
        )

    elif priority == "lower_saturated_fat":
        ranked = []
        valid_items = [(it, it.nutrients_per_100.get("saturated_fat_g")) for it in items]
        sorted_items = sorted(
            valid_items,
            key=lambda x: (x[1] is None, x[1] if x[1] is not None else float("inf")),
        )
        for idx, (it, val) in enumerate(sorted_items, start=1):
            note = f"{val:.1f}g saturated fat/{it.standard_unit}" if val is not None else "Saturated fat not declared"
            ranked.append(
                PriorityRanking(
                    product_id=it.product_id,
                    product_name=it.name,
                    value=val,
                    unit="g",
                    rank=idx,
                    note=note,
                )
            )
        best = sorted_items[0] if sorted_items and sorted_items[0][1] is not None else None
        worst = sorted_items[-1] if sorted_items and sorted_items[-1][1] is not None else None
        if best and worst and best[0].product_id != worst[0].product_id:
            diff = worst[1] - best[1]
            summary = (
                f"{best[0].name} has the least saturated fat ({best[1]:.1f}g vs {worst[1]:.1f}g in {worst[0].name})."
            )
        elif best:
            summary = f"{best[0].name} has the lowest saturated fat at {best[1]:.1f}g/{best[0].standard_unit}."
        else:
            summary = "Saturated fat is not declared for the compared products."

        return PriorityEvaluationItem(
            priority=priority,
            priority_label=label,
            best_product_id=best[0].product_id if best else None,
            best_product_name=best[0].name if best else None,
            summary=summary,
            rankings=ranked,
        )

    elif priority == "higher_protein":
        ranked = []
        valid_items = [(it, it.nutrients_per_100.get("protein_g")) for it in items]
        sorted_items = sorted(
            valid_items,
            key=lambda x: (x[1] is None, -x[1] if x[1] is not None else float("inf")),
        )
        for idx, (it, val) in enumerate(sorted_items, start=1):
            note = f"{val:.1f}g protein/{it.standard_unit}" if val is not None else "Protein not declared"
            ranked.append(
                PriorityRanking(
                    product_id=it.product_id,
                    product_name=it.name,
                    value=val,
                    unit="g",
                    rank=idx,
                    note=note,
                )
            )
        best = sorted_items[0] if sorted_items and sorted_items[0][1] is not None else None
        worst = sorted_items[-1] if sorted_items and sorted_items[-1][1] is not None else None
        if best and worst and best[0].product_id != worst[0].product_id:
            diff = best[1] - worst[1]
            summary = (
                f"{best[0].name} offers the highest protein with {best[1]:.1f}g/{best[0].standard_unit} "
                f"(+{diff:.1f}g over {worst[0].name})."
            )
        elif best:
            summary = f"{best[0].name} leads in protein with {best[1]:.1f}g/{best[0].standard_unit}."
        else:
            summary = "Protein content is not declared for the compared products."

        return PriorityEvaluationItem(
            priority=priority,
            priority_label=label,
            best_product_id=best[0].product_id if best else None,
            best_product_name=best[0].name if best else None,
            summary=summary,
            rankings=ranked,
        )

    elif priority == "higher_fibre":
        ranked = []
        valid_items = [(it, it.nutrients_per_100.get("dietary_fibre_g")) for it in items]
        sorted_items = sorted(
            valid_items,
            key=lambda x: (x[1] is None, -x[1] if x[1] is not None else float("inf")),
        )
        for idx, (it, val) in enumerate(sorted_items, start=1):
            note = f"{val:.1f}g dietary fibre/{it.standard_unit}" if val is not None else "Fibre not declared"
            ranked.append(
                PriorityRanking(
                    product_id=it.product_id,
                    product_name=it.name,
                    value=val,
                    unit="g",
                    rank=idx,
                    note=note,
                )
            )
        best = sorted_items[0] if sorted_items and sorted_items[0][1] is not None else None
        worst = sorted_items[-1] if sorted_items and sorted_items[-1][1] is not None else None
        if best and worst and best[0].product_id != worst[0].product_id:
            diff = best[1] - worst[1]
            summary = (
                f"{best[0].name} provides the most dietary fibre at {best[1]:.1f}g/{best[0].standard_unit} "
                f"(+{diff:.1f}g compared to {worst[0].name})."
            )
        elif best:
            summary = f"{best[0].name} leads in dietary fibre at {best[1]:.1f}g/{best[0].standard_unit}."
        else:
            summary = "Dietary fibre is not declared for the compared products."

        return PriorityEvaluationItem(
            priority=priority,
            priority_label=label,
            best_product_id=best[0].product_id if best else None,
            best_product_name=best[0].name if best else None,
            summary=summary,
            rankings=ranked,
        )

    elif priority == "fewer_restriction_conflicts":
        # Fewer conflicts with declared restrictions
        status_weight = {
            "Suitable based on available information": 0,
            "Caution": 1,
            "Insufficient information": 2,
            "Declared restriction conflict": 3,
        }
        ranked = []
        valid_items = [
            (
                it,
                len(it.suitability_conflicts),
                status_weight.get(it.suitability_status, 2),
            )
            for it in items
        ]
        # Sort by conflict count ascending, then by status weight ascending
        sorted_items = sorted(valid_items, key=lambda x: (x[1], x[2]))
        for idx, (it, conflicts, _) in enumerate(sorted_items, start=1):
            note = (
                f"{it.suitability_status} ({conflicts} conflicts)"
                if conflicts > 0
                else it.suitability_status
            )
            ranked.append(
                PriorityRanking(
                    product_id=it.product_id,
                    product_name=it.name,
                    value=float(conflicts),
                    unit="conflicts",
                    rank=idx,
                    note=note,
                )
            )
        best = sorted_items[0]
        if best[1] == 0:
            summary = f"{best[0].name} has 0 declared restriction conflicts and is {best[0].suitability_status}."
        else:
            summary = f"{best[0].name} has the fewest restriction conflicts ({best[1]} conflicts)."

        return PriorityEvaluationItem(
            priority=priority,
            priority_label=label,
            best_product_id=best[0].product_id,
            best_product_name=best[0].name,
            summary=summary,
            rankings=ranked,
        )

    return None


def _build_comparison_summary(
    items: List[ProductComparisonItem],
    priority_evaluations: List[PriorityEvaluationItem],
) -> str:
    """Builds a cohesive paragraph summarizing key trade-offs between compared products."""
    parts: List[str] = []

    # 1. Score comparison
    items_with_score = [it for it in items if it.score is not None]
    if items_with_score:
        sorted_by_score = sorted(items_with_score, key=lambda x: x.score or 0, reverse=True)
        top_scorer = sorted_by_score[0]
        parts.append(
            f"Overall, {top_scorer.name} achieved the highest NutriLens score of {top_scorer.score}/100 (Grade {top_scorer.grade})."
        )

    # 2. Key priority highlights
    for eval_item in priority_evaluations[:2]:
        parts.append(eval_item.summary)

    # 3. Personal suitability note
    conflicted = [it for it in items if it.suitability_status == "Declared restriction conflict"]
    if conflicted:
        names = ", ".join(c.name for c in conflicted)
        parts.append(f"Caution: {names} contain ingredients conflicting with your profile preferences.")

    return " ".join(parts)
