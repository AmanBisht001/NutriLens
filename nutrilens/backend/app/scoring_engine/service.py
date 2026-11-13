"""
NutriLens – Scoring Engine Service Orchestrator (Day 5)
Orchestrates serving size standardization, validation, deterministic scoring,
and explanation generation for products or standalone nutritional payloads.
"""
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.product import Product, NutritionFacts
from app.scoring_engine.rules import (
    SCORING_RULE_VERSION,
    UNIT_PER_100G,
    UNIT_PER_100ML,
    get_category_config,
)
from app.scoring_engine.validators import validate_nutrition_data
from app.scoring_engine.calculator import (
    parse_serving_size,
    calculate_serving_values,
    calculate_deterministic_score,
)
from app.scoring_engine.explanations import (
    evaluate_individual_nutrients,
    build_factors_and_narratives,
    DISCLAIMER_TEXT,
)


def extract_nutrient_dict_from_model(nf: Optional[NutritionFacts]) -> Dict[str, Optional[float]]:
    """Extracts raw per-100g/ml nutrient dictionary from SQLAlchemy NutritionFacts model."""
    if not nf:
        return {
            "energy_kcal": None,
            "total_fat_g": None,
            "saturated_fat_g": None,
            "trans_fat_g": None,
            "carbohydrates_g": None,
            "total_sugar_g": None,
            "added_sugar_g": None,
            "dietary_fibre_g": None,
            "protein_g": None,
            "sodium_mg": None,
        }

    return {
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


def analyze_nutrition_payload(
    nutrients_per_100: Dict[str, Optional[float]],
    category: Optional[str] = None,
    serving_size_str: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Core deterministic pipeline analyzing normalized nutritional values.
    Returns complete analysis or insufficient-data result when critical fields are absent.
    """
    config = get_category_config(category)
    is_liquid = config.is_liquid
    standard_unit = UNIT_PER_100ML if is_liquid else UNIT_PER_100G

    # 1. Serving size standardization
    serving_qty, serving_unit = parse_serving_size(serving_size_str)
    per_serving_values = calculate_serving_values(nutrients_per_100, serving_qty)

    serving_size_info = {
        "raw_text": serving_size_str,
        "quantity": serving_qty,
        "unit": serving_unit,
        "standard_reference": f"100{serving_unit}",
    }

    # 2. Validation & completeness check
    validation = validate_nutrition_data(nutrients_per_100)

    # 3. Handle Insufficient Data: Do not manufacture a score when critical fields are missing
    if not validation.is_scoreable:
        return {
            "status": "insufficient_data",
            "score": None,
            "grade": None,
            "rating_label": "Insufficient Data",
            "rating_color": "slate",
            "standard_unit": standard_unit,
            "per_100_values": nutrients_per_100,
            "per_serving_values": per_serving_values,
            "serving_size_info": serving_size_info,
            "data_completeness_pct": validation.data_completeness_pct,
            "missing_critical_fields": validation.missing_critical_fields,
            "missing_optional_fields": validation.missing_optional_fields,
            "issues": [
                {"field": i.field, "severity": i.severity, "message": i.message}
                for i in validation.issues
            ],
            "nutrition_summary": (
                "Insufficient nutritional data declared to compute a reliable NutriLens score. "
                f"Missing critical fields: {', '.join(validation.missing_critical_fields)}."
            ),
            "score_explanation": "Score calculation requires all critical macronutrients to be declared on the label.",
            "positive_factors": [],
            "attention_factors": [],
            "nutrient_evaluations": evaluate_individual_nutrients(nutrients_per_100, is_liquid=is_liquid),
            "scoring_rule_version": SCORING_RULE_VERSION,
            "disclaimer": DISCLAIMER_TEXT,
        }

    # 4. Deterministic score calculation
    calc = calculate_deterministic_score(nutrients_per_100, category=category)

    # 5. Nutrient evaluations and narrative generation
    evaluations = evaluate_individual_nutrients(nutrients_per_100, is_liquid=is_liquid)
    narratives = build_factors_and_narratives(nutrients_per_100, calc, evaluations)

    return {
        "status": "complete",
        "score": calc["score"],
        "grade": calc["grade"],
        "rating_label": calc["rating_label"],
        "rating_color": calc["rating_color"],
        "standard_unit": standard_unit,
        "per_100_values": nutrients_per_100,
        "per_serving_values": per_serving_values,
        "serving_size_info": serving_size_info,
        "data_completeness_pct": validation.data_completeness_pct,
        "missing_critical_fields": validation.missing_critical_fields,
        "missing_optional_fields": validation.missing_optional_fields,
        "issues": [
            {"field": i.field, "severity": i.severity, "message": i.message}
            for i in validation.issues
        ],
        "nutrition_summary": narratives["nutrition_summary"],
        "score_explanation": narratives["score_explanation"],
        "positive_factors": narratives["positive_factors"],
        "attention_factors": narratives["attention_factors"],
        "nutrient_evaluations": evaluations,
        "score_breakdown": {
            "base_score": calc["base_score"],
            "total_penalties": calc["total_penalties"],
            "total_bonuses": calc["total_bonuses"],
            "penalties": calc["penalties"],
            "bonuses": calc["bonuses"],
            "category_used": calc["category_used"],
        },
        "scoring_rule_version": SCORING_RULE_VERSION,
        "disclaimer": DISCLAIMER_TEXT,
    }


def analyze_product_by_id(product_id: str, db: Session) -> Optional[Dict[str, Any]]:
    """Fetches product by ID and runs complete nutritional analysis."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    nutrients = extract_nutrient_dict_from_model(product.nutrition_facts)
    analysis = analyze_nutrition_payload(
        nutrients_per_100=nutrients,
        category=product.category,
        serving_size_str=product.serving_size,
    )
    analysis["product_id"] = product.id
    analysis["product_name"] = product.name
    return analysis
