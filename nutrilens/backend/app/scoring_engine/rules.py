"""
NutriLens – Scoring Engine Rules & Configurations (Day 5)
Defines deterministic, configurable, category-aware nutrition scoring parameters.

NOTE: This is a project-defined algorithmic scoring model for educational and
consumer empowerment purposes. It is NOT an official FSSAI rating or medical prescription.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

SCORING_RULE_VERSION = "nutrilens-score-v1.0"

# Standard units
UNIT_PER_100G = "per_100g"
UNIT_PER_100ML = "per_100ml"

# Critical fields required to compute a valid score without manufacturing data
CRITICAL_NUTRIENT_FIELDS = [
    "energy_kcal",
    "total_fat_g",
    "saturated_fat_g",
    "carbohydrates_g",
    "total_sugar_g",
    "protein_g",
    "sodium_mg",
]

ALL_TRACKED_NUTRIENT_FIELDS = [
    "energy_kcal",
    "total_fat_g",
    "saturated_fat_g",
    "trans_fat_g",
    "carbohydrates_g",
    "total_sugar_g",
    "added_sugar_g",
    "dietary_fibre_g",
    "protein_g",
    "sodium_mg",
]


@dataclass(frozen=True)
class NutrientThresholds:
    low: float
    moderate: float
    high: float


# Baseline European / WHO / ICMR reference thresholds per 100g (foods) and per 100ml (beverages)
THRESHOLDS_FOOD = {
    "total_sugar_g": NutrientThresholds(low=5.0, moderate=12.5, high=22.5),
    "added_sugar_g": NutrientThresholds(low=2.5, moderate=6.0, high=12.0),
    "saturated_fat_g": NutrientThresholds(low=1.5, moderate=5.0, high=10.0),
    "total_fat_g": NutrientThresholds(low=3.0, moderate=10.0, high=17.5),
    "sodium_mg": NutrientThresholds(low=120.0, moderate=400.0, high=600.0),
    "dietary_fibre_g": NutrientThresholds(low=1.5, moderate=3.0, high=6.0),
    "protein_g": NutrientThresholds(low=3.0, moderate=5.0, high=10.0),
    "energy_kcal": NutrientThresholds(low=150.0, moderate=350.0, high=450.0),
}

THRESHOLDS_BEVERAGE = {
    "total_sugar_g": NutrientThresholds(low=2.5, moderate=5.0, high=10.0),
    "added_sugar_g": NutrientThresholds(low=1.5, moderate=3.0, high=6.0),
    "saturated_fat_g": NutrientThresholds(low=0.75, moderate=2.0, high=4.0),
    "total_fat_g": NutrientThresholds(low=1.5, moderate=3.0, high=6.0),
    "sodium_mg": NutrientThresholds(low=60.0, moderate=150.0, high=300.0),
    "dietary_fibre_g": NutrientThresholds(low=1.0, moderate=2.0, high=3.0),
    "protein_g": NutrientThresholds(low=1.5, moderate=3.0, high=5.0),
    "energy_kcal": NutrientThresholds(low=30.0, moderate=60.0, high=100.0),
}


@dataclass
class CategoryScoringConfig:
    category_name: str
    is_liquid: bool = False
    base_score: float = 70.0
    sugar_weight: float = 1.0
    saturated_fat_weight: float = 1.0
    trans_fat_weight: float = 1.5
    sodium_weight: float = 1.0
    energy_weight: float = 0.8
    fibre_weight: float = 1.0
    protein_weight: float = 1.0


# Category-specific rule registry
CATEGORY_RULES: Dict[str, CategoryScoringConfig] = {
    "Beverages": CategoryScoringConfig(
        category_name="Beverages",
        is_liquid=True,
        base_score=75.0,
        sugar_weight=1.5,      # Liquid sugar is rapidly absorbed; higher penalty
        energy_weight=1.0,
        saturated_fat_weight=0.8,
        sodium_weight=0.8,
    ),
    "Biscuits & Cookies": CategoryScoringConfig(
        category_name="Biscuits & Cookies",
        is_liquid=False,
        base_score=70.0,
        sugar_weight=1.2,
        saturated_fat_weight=1.2,
        trans_fat_weight=1.5,
    ),
    "Breakfast Cereals": CategoryScoringConfig(
        category_name="Breakfast Cereals",
        is_liquid=False,
        base_score=70.0,
        sugar_weight=1.3,      # Cereals often hide excess added sugars
        fibre_weight=1.3,      # Whole grains rewarded
        protein_weight=1.1,
    ),
    "Dairy & Milks": CategoryScoringConfig(
        category_name="Dairy & Milks",
        is_liquid=True,
        base_score=72.0,
        protein_weight=1.2,
        saturated_fat_weight=0.9,  # Dairy fats have distinct matrix
        sugar_weight=1.2,
    ),
    "Snacks & Namkeen": CategoryScoringConfig(
        category_name="Snacks & Namkeen",
        is_liquid=False,
        base_score=70.0,
        sodium_weight=1.4,     # Salt content in namkeen is critical
        saturated_fat_weight=1.3,
        trans_fat_weight=1.6,
    ),
    "Chocolates & Sweets": CategoryScoringConfig(
        category_name="Chocolates & Sweets",
        is_liquid=False,
        base_score=68.0,
        sugar_weight=1.4,
        saturated_fat_weight=1.3,
    ),
    "Instant Foods & Noodles": CategoryScoringConfig(
        category_name="Instant Foods & Noodles",
        is_liquid=False,
        base_score=70.0,
        sodium_weight=1.5,     # MSG and sodium load are high in instant foods
        saturated_fat_weight=1.2,
    ),
    "General": CategoryScoringConfig(
        category_name="General",
        is_liquid=False,
        base_score=70.0,
    ),
}


def get_category_config(category: Optional[str]) -> CategoryScoringConfig:
    """Return matching CategoryScoringConfig or General default."""
    if not category:
        return CATEGORY_RULES["General"]
    for cat_key, config in CATEGORY_RULES.items():
        if cat_key.lower() in category.lower():
            return config
    return CATEGORY_RULES["General"]


def get_nutrient_thresholds(is_liquid: bool) -> Dict[str, NutrientThresholds]:
    """Returns thresholds for food or beverage."""
    return THRESHOLDS_BEVERAGE if is_liquid else THRESHOLDS_FOOD
