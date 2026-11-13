"""
NutriLens – Food Journal Nutrition Calculator (Day 8)
Calculates actual consumption nutrients by proportionally scaling the product's
per-100g/per-100ml values according to the consumed weight.
Missing nutrients are handled honestly without assuming 0.
"""
import re
from typing import Optional, List, Tuple
from app.models.product import NutritionFacts
from app.schemas.journal import CalculatedNutrients

NUTRIENT_FIELDS: List[Tuple[str, str]] = [
    ("energy_kcal", "Energy"),
    ("total_fat_g", "Total Fat"),
    ("saturated_fat_g", "Saturated Fat"),
    ("trans_fat_g", "Trans Fat"),
    ("cholesterol_mg", "Cholesterol"),
    ("carbohydrates_g", "Carbohydrates"),
    ("total_sugar_g", "Total Sugar"),
    ("added_sugar_g", "Added Sugar"),
    ("dietary_fibre_g", "Dietary Fibre"),
    ("protein_g", "Protein"),
    ("sodium_mg", "Sodium"),
    ("calcium_mg", "Calcium"),
    ("iron_mg", "Iron"),
    ("vitamin_c_mg", "Vitamin C"),
]


def extract_grams_from_serving_size(serving_size_str: Optional[str]) -> Optional[float]:
    """
    Attempts to extract numeric weight in grams or milliliters from a serving size string.
    Examples:
      "30g" -> 30.0
      "2 biscuits (30 g)" -> 30.0
      "100ml" -> 100.0
      "1 pack (45.5g)" -> 45.5
    """
    if not serving_size_str:
        return None

    # Match numeric followed by g, gram, grams, ml, or milliliter
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:g|gram|grams|ml|milliliter|millilitres|milliliters)\b", serving_size_str, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass

    # Secondary match: simple number if whole string is numeric
    stripped = serving_size_str.strip()
    if stripped.replace(".", "", 1).isdigit():
        try:
            return float(stripped)
        except ValueError:
            pass

    return None


def calculate_entry_weight(
    quantity: float,
    serving_unit: str = "g",
    serving_size_g: Optional[float] = None,
    total_weight_g: Optional[float] = None,
    product_serving_size_str: Optional[str] = None,
) -> float:
    """
    Determines the total consumed weight in grams/ml.
    Priority:
    1. Explicit total_weight_g
    2. quantity * serving_size_g
    3. quantity * extracted_product_serving_size
    4. Default: quantity * 100.0g
    """
    if total_weight_g is not None and total_weight_g > 0:
        return round(float(total_weight_g), 2)

    if serving_size_g is not None and serving_size_g > 0:
        return round(float(quantity * serving_size_g), 2)

    extracted_size = extract_grams_from_serving_size(product_serving_size_str)
    if extracted_size is not None and extracted_size > 0:
        return round(float(quantity * extracted_size), 2)

    # Standard per 100g unit assumption
    return round(float(quantity * 100.0), 2)


def calculate_entry_nutrients(
    nutrition_facts: Optional[NutritionFacts],
    total_weight_g: float,
) -> CalculatedNutrients:
    """
    Calculates actual nutrient intake scaled to total_weight_g from per-100g facts.
    Formula: scaled_nutrient = per_100g_nutrient * (total_weight_g / 100.0)

    If a nutrient is None in nutrition_facts, it remains None and is tracked
    in missing_nutrients to ensure complete honesty.
    """
    scale_factor = max(0.0, total_weight_g / 100.0)
    missing: List[str] = []
    nutrients_dict = {
        "scale_factor": round(scale_factor, 4),
        "missing_nutrients": missing,
    }

    if not nutrition_facts:
        for field, label in NUTRIENT_FIELDS:
            nutrients_dict[field] = None
            missing.append(label)
        return CalculatedNutrients(**nutrients_dict)

    for field, label in NUTRIENT_FIELDS:
        val = getattr(nutrition_facts, field, None)
        if val is None:
            nutrients_dict[field] = None
            missing.append(label)
        else:
            scaled = round(val * scale_factor, 2)
            nutrients_dict[field] = scaled

    return CalculatedNutrients(**nutrients_dict)
