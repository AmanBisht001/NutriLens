"""
NutriLens – Scoring Engine Calculations & Serving Standardizer (Day 5)
Provides deterministic mathematical scoring and serving size conversions.
"""
import re
from typing import Dict, Any, Optional, Tuple
from app.scoring_engine.rules import (
    CategoryScoringConfig,
    get_category_config,
    get_nutrient_thresholds,
    UNIT_PER_100G,
    UNIT_PER_100ML,
)


def parse_serving_size(serving_size_str: Optional[str]) -> Tuple[Optional[float], str]:
    """
    Parses a serving size string (e.g. '30g', '2 biscuits (30g)', '250ml')
    into a numerical quantity and unit ('g' or 'ml').
    """
    if not serving_size_str or not serving_size_str.strip():
        return None, "g"

    text = serving_size_str.strip().lower()

    # Match patterns like: (30g), 30 g, 250ml, 250 ml
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(g|gm|gms|ml|milliliters?|grams?)\b", text)
    if m:
        qty = float(m.group(1))
        raw_unit = m.group(2)
        unit = "ml" if "ml" in raw_unit else "g"
        return qty, unit

    # Match pure number fallback
    m_num = re.search(r"([0-9]+(?:\.[0-9]+)?)", text)
    if m_num:
        return float(m_num.group(1)), "g"

    return None, "g"


def calculate_serving_values(
    per_100_values: Dict[str, Optional[float]],
    serving_quantity: Optional[float],
) -> Dict[str, Optional[float]]:
    """
    Scales per-100g/ml nutritional values to the specified serving size quantity.
    Does NOT assume values that are not present (None remains None).
    """
    if serving_quantity is None or serving_quantity <= 0:
        return {k: None for k in per_100_values}

    ratio = serving_quantity / 100.0
    serving_values: Dict[str, Optional[float]] = {}

    for key, val in per_100_values.items():
        if val is None:
            serving_values[key] = None
        else:
            scaled = val * ratio
            # Precision formatting: energy & sodium integers/1-decimal; others 1-2 decimals
            if key in ("energy_kcal", "sodium_mg"):
                serving_values[key] = round(scaled, 1)
            else:
                serving_values[key] = round(scaled, 2)

    return serving_values


def calculate_deterministic_score(
    nutrients: Dict[str, Optional[float]],
    category: Optional[str],
) -> Dict[str, Any]:
    """
    Calculates the 0–100 NutriLens Nutrition Score and returns full contribution breakdown.
    Guaranteed deterministic: identical inputs yield identical outputs.
    """
    config: CategoryScoringConfig = get_category_config(category)
    is_liquid = config.is_liquid

    base_score = config.base_score
    penalties: Dict[str, float] = {}
    bonuses: Dict[str, float] = {}

    # Extract nutrients (all per 100g or 100ml)
    sugar = nutrients.get("total_sugar_g") or 0.0
    added_sugar = nutrients.get("added_sugar_g")
    sat_fat = nutrients.get("saturated_fat_g") or 0.0
    trans_fat = nutrients.get("trans_fat_g")
    sodium = nutrients.get("sodium_mg") or 0.0
    energy = nutrients.get("energy_kcal") or 0.0
    fibre = nutrients.get("dietary_fibre_g")
    protein = nutrients.get("protein_g") or 0.0

    # 1. Sugar Penalty
    sugar_deduction = 0.0
    if is_liquid:
        if sugar > 2.5:
            if sugar <= 5.0:
                sugar_deduction = ((sugar - 2.5) / 2.5) * 8.0
            elif sugar <= 10.0:
                sugar_deduction = 8.0 + ((sugar - 5.0) / 5.0) * 12.0
            else:
                sugar_deduction = 20.0 + min(12.0, ((sugar - 10.0) / 10.0) * 12.0)
    else:
        if sugar > 5.0:
            if sugar <= 12.5:
                sugar_deduction = ((sugar - 5.0) / 7.5) * 6.0
            elif sugar <= 22.5:
                sugar_deduction = 6.0 + ((sugar - 12.5) / 10.0) * 8.0
            else:
                sugar_deduction = 14.0 + min(14.0, ((sugar - 22.5) / 25.0) * 14.0)

    # Added sugar separate consideration
    if added_sugar is not None and added_sugar > 5.0:
        sugar_deduction += min(6.0, ((added_sugar - 5.0) / 10.0) * 4.0)

    sugar_deduction *= config.sugar_weight
    if sugar_deduction > 0.0:
        penalties["sugar"] = round(sugar_deduction, 2)

    # 2. Saturated Fat Penalty
    sat_fat_deduction = 0.0
    if is_liquid:
        if sat_fat > 1.0:
            sat_fat_deduction = min(15.0, ((sat_fat - 1.0) / 4.0) * 15.0)
    else:
        if sat_fat > 1.5:
            if sat_fat <= 5.0:
                sat_fat_deduction = ((sat_fat - 1.5) / 3.5) * 7.0
            elif sat_fat <= 10.0:
                sat_fat_deduction = 7.0 + ((sat_fat - 5.0) / 5.0) * 8.0
            else:
                sat_fat_deduction = 15.0 + min(9.0, ((sat_fat - 10.0) / 15.0) * 9.0)

    sat_fat_deduction *= config.saturated_fat_weight
    if sat_fat_deduction > 0.0:
        penalties["saturated_fat"] = round(sat_fat_deduction, 2)

    # 3. Trans Fat Penalty (severe penalty for industrial trans fats)
    if trans_fat is not None and trans_fat > 0.0:
        if trans_fat <= 0.2:
            trans_deduction = 6.0
        elif trans_fat <= 0.5:
            trans_deduction = 12.0
        elif trans_fat <= 1.0:
            trans_deduction = 18.0
        else:
            trans_deduction = 24.0
        trans_deduction *= config.trans_fat_weight
        penalties["trans_fat"] = round(trans_deduction, 2)

    # 4. Sodium Penalty
    sodium_deduction = 0.0
    if is_liquid:
        if sodium > 100.0:
            sodium_deduction = min(18.0, ((sodium - 100.0) / 300.0) * 18.0)
    else:
        if sodium > 120.0:
            if sodium <= 400.0:
                sodium_deduction = ((sodium - 120.0) / 280.0) * 6.0
            elif sodium <= 800.0:
                sodium_deduction = 6.0 + ((sodium - 400.0) / 400.0) * 8.0
            else:
                sodium_deduction = 14.0 + min(12.0, ((sodium - 800.0) / 1000.0) * 12.0)

    sodium_deduction *= config.sodium_weight
    if sodium_deduction > 0.0:
        penalties["sodium"] = round(sodium_deduction, 2)

    # 5. Energy Density Penalty
    energy_deduction = 0.0
    if is_liquid:
        if energy > 50.0:
            energy_deduction = min(10.0, ((energy - 50.0) / 70.0) * 10.0)
    else:
        if energy > 350.0:
            energy_deduction = min(10.0, ((energy - 350.0) / 200.0) * 10.0)

    energy_deduction *= config.energy_weight
    if energy_deduction > 0.0:
        penalties["energy"] = round(energy_deduction, 2)

    # 6. Fibre Bonus
    fibre_bonus = 0.0
    if fibre is not None and fibre >= 1.5:
        if fibre <= 3.0:
            fibre_bonus = ((fibre - 1.5) / 1.5) * 4.0
        elif fibre <= 6.0:
            fibre_bonus = 4.0 + ((fibre - 3.0) / 3.0) * 5.0
        else:
            fibre_bonus = 9.0 + min(4.0, ((fibre - 6.0) / 4.0) * 4.0)

    fibre_bonus *= config.fibre_weight
    if fibre_bonus > 0.0:
        bonuses["fibre"] = round(fibre_bonus, 2)

    # 7. Protein Bonus
    protein_bonus = 0.0
    if protein >= 3.0:
        if protein <= 5.0:
            protein_bonus = ((protein - 3.0) / 2.0) * 3.5
        elif protein <= 10.0:
            protein_bonus = 3.5 + ((protein - 5.0) / 5.0) * 4.5
        else:
            protein_bonus = 8.0 + min(4.0, ((protein - 10.0) / 10.0) * 4.0)

    protein_bonus *= config.protein_weight
    if protein_bonus > 0.0:
        bonuses["protein"] = round(protein_bonus, 2)

    # Final score aggregation
    total_penalties = sum(penalties.values())
    total_bonuses = sum(bonuses.values())

    raw_final = base_score - total_penalties + total_bonuses
    bounded_score = int(round(max(0.0, min(100.0, raw_final))))

    # Score grade determination
    if bounded_score >= 80:
        grade = "A"
        rating_label = "Excellent"
        rating_color = "emerald"
    elif bounded_score >= 60:
        grade = "B"
        rating_label = "Good"
        rating_color = "green"
    elif bounded_score >= 40:
        grade = "C"
        rating_label = "Moderate"
        rating_color = "amber"
    elif bounded_score >= 20:
        grade = "D"
        rating_label = "Low"
        rating_color = "orange"
    else:
        grade = "E"
        rating_label = "Poor"
        rating_color = "rose"

    return {
        "score": bounded_score,
        "grade": grade,
        "rating_label": rating_label,
        "rating_color": rating_color,
        "base_score": base_score,
        "total_penalties": round(total_penalties, 2),
        "total_bonuses": round(total_bonuses, 2),
        "penalties": penalties,
        "bonuses": bonuses,
        "category_used": config.category_name,
        "is_liquid": is_liquid,
    }
