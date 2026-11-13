"""
NutriLens – Scoring Engine Explanations & Narratives (Day 5)
Generates transparent, human-readable explanations, nutrient evaluations,
and summaries for every calculated NutriLens score.
"""
from typing import Dict, List, Any, Optional
from app.scoring_engine.rules import (
    get_nutrient_thresholds,
    SCORING_RULE_VERSION,
)

DISCLAIMER_TEXT = (
    "The NutriLens Nutrition Score is an algorithmic educational reference calculated "
    "deterministically from declared nutritional values. It does not constitute an "
    "official FSSAI score, medical rating, or professional dietary advice."
)


def evaluate_individual_nutrients(
    nutrients: Dict[str, Optional[float]],
    is_liquid: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluates each nutrient against standard reference thresholds,
    assigning 'low', 'moderate', or 'high' qualitative levels.
    """
    thresholds = get_nutrient_thresholds(is_liquid)
    evaluations: Dict[str, Dict[str, Any]] = {}

    unit_mapping = {
        "energy_kcal": "kcal",
        "sodium_mg": "mg",
    }

    labels = {
        "energy_kcal": "Energy / Calories",
        "total_fat_g": "Total Fat",
        "saturated_fat_g": "Saturated Fat",
        "trans_fat_g": "Trans Fat",
        "carbohydrates_g": "Carbohydrates",
        "total_sugar_g": "Total Sugar",
        "added_sugar_g": "Added Sugar",
        "dietary_fibre_g": "Dietary Fibre",
        "protein_g": "Protein",
        "sodium_mg": "Sodium",
    }

    for key, label in labels.items():
        val = nutrients.get(key)
        unit = unit_mapping.get(key, "g")

        if val is None:
            evaluations[key] = {
                "name": label,
                "value": None,
                "unit": unit,
                "level": "not_declared",
                "badge_color": "slate",
                "description": f"{label} is not declared on label.",
            }
            continue

        # Trans fat special evaluation
        if key == "trans_fat_g":
            if val == 0.0:
                level = "low"
                badge = "emerald"
                desc = "Zero trans fat declared."
            elif val <= 0.5:
                level = "moderate"
                badge = "amber"
                desc = f"Contains {val}g trans fat (moderate concern)."
            else:
                level = "high"
                badge = "rose"
                desc = f"High trans fat ({val}g) – harmful for cardiovascular health."
            evaluations[key] = {
                "name": label,
                "value": val,
                "unit": unit,
                "level": level,
                "badge_color": badge,
                "description": desc,
            }
            continue

        # Carbs general evaluation
        if key == "carbohydrates_g":
            level = "moderate" if val <= 60 else "high"
            evaluations[key] = {
                "name": label,
                "value": val,
                "unit": unit,
                "level": level,
                "badge_color": "slate",
                "description": f"{val}g carbohydrates per 100{'ml' if is_liquid else 'g'}.",
            }
            continue

        th = thresholds.get(key)
        if not th:
            evaluations[key] = {
                "name": label,
                "value": val,
                "unit": unit,
                "level": "moderate",
                "badge_color": "slate",
                "description": f"{val}{unit}",
            }
            continue

        # Positive nutrients (Fibre & Protein: high is good)
        if key in ("dietary_fibre_g", "protein_g"):
            if val >= th.high:
                level = "high"
                badge = "emerald"
                desc = f"High in {label.lower()} ({val}{unit})."
            elif val >= th.moderate:
                level = "moderate"
                badge = "green"
                desc = f"Good source of {label.lower()} ({val}{unit})."
            else:
                level = "low"
                badge = "slate"
                desc = f"Low in {label.lower()} ({val}{unit})."
        else:
            # Negative nutrients (Sugar, Sat Fat, Sodium, Energy: low is good)
            if val <= th.low:
                level = "low"
                badge = "emerald"
                desc = f"Low in {label.lower()} ({val}{unit})."
            elif val <= th.high:
                level = "moderate"
                badge = "amber"
                desc = f"Moderate {label.lower()} ({val}{unit})."
            else:
                level = "high"
                badge = "rose"
                desc = f"High in {label.lower()} ({val}{unit})."

        evaluations[key] = {
            "name": label,
            "value": val,
            "unit": unit,
            "level": level,
            "badge_color": badge,
            "description": desc,
            "thresholds": {"low": th.low, "moderate": th.moderate, "high": th.high},
        }

    return evaluations


def build_factors_and_narratives(
    nutrients: Dict[str, Optional[float]],
    calculation_result: Dict[str, Any],
    evaluations: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Constructs positive factors, negative factors (attention required),
    and a holistic summary narrative explaining the score.
    """
    penalties = calculation_result.get("penalties", {})
    bonuses = calculation_result.get("bonuses", {})
    is_liquid = calculation_result.get("is_liquid", False)
    u = "100ml" if is_liquid else "100g"

    positive_factors: List[Dict[str, Any]] = []
    attention_factors: List[Dict[str, Any]] = []

    # 1. Sugar factor
    sugar = nutrients.get("total_sugar_g")
    if sugar is not None:
        if "sugar" in penalties:
            attention_factors.append({
                "factor": "Sugar Content",
                "impact": f"-{penalties['sugar']:.1f} pts",
                "severity": "high" if sugar > 15.0 else "moderate",
                "description": f"Contains {sugar}g total sugar per {u}.",
            })
        elif sugar <= (2.5 if is_liquid else 5.0):
            positive_factors.append({
                "factor": "Low Sugar",
                "impact": "+0 pts",
                "description": f"Low in total sugar ({sugar}g per {u}).",
            })

    # Added sugar separate mention
    added_sugar = nutrients.get("added_sugar_g")
    if added_sugar is not None and added_sugar > 5.0:
        attention_factors.append({
            "factor": "Added Sugars",
            "impact": "Included in sugar penalty",
            "severity": "moderate",
            "description": f"Contains {added_sugar}g added refined sugars per {u}.",
        })

    # 2. Saturated fat factor
    sat_fat = nutrients.get("saturated_fat_g")
    if sat_fat is not None:
        if "saturated_fat" in penalties:
            attention_factors.append({
                "factor": "Saturated Fat",
                "impact": f"-{penalties['saturated_fat']:.1f} pts",
                "severity": "high" if sat_fat > 5.0 else "moderate",
                "description": f"Contains {sat_fat}g saturated fat per {u}.",
            })
        elif sat_fat <= (0.75 if is_liquid else 1.5):
            positive_factors.append({
                "factor": "Low Saturated Fat",
                "impact": "+0 pts",
                "description": f"Naturally low in saturated fat ({sat_fat}g per {u}).",
            })

    # 3. Trans fat factor
    trans_fat = nutrients.get("trans_fat_g")
    if trans_fat is not None:
        if trans_fat > 0.0:
            attention_factors.append({
                "factor": "Trans Fat",
                "impact": f"-{penalties.get('trans_fat', 0):.1f} pts",
                "severity": "critical",
                "description": f"Contains {trans_fat}g trans fat; recommended intake is 0g.",
            })
        else:
            positive_factors.append({
                "factor": "Zero Trans Fat",
                "impact": "Safe baseline",
                "description": "Zero trans fatty acids declared.",
            })

    # 4. Sodium factor
    sodium = nutrients.get("sodium_mg")
    if sodium is not None:
        if "sodium" in penalties:
            attention_factors.append({
                "factor": "Sodium",
                "impact": f"-{penalties['sodium']:.1f} pts",
                "severity": "high" if sodium > 600 else "moderate",
                "description": f"Contains {sodium:.0f}mg sodium per {u}.",
            })
        elif sodium <= (60 if is_liquid else 120):
            positive_factors.append({
                "factor": "Low Sodium",
                "impact": "+0 pts",
                "description": f"Low in sodium ({sodium:.0f}mg per {u}).",
            })

    # 5. Fibre factor
    fibre = nutrients.get("dietary_fibre_g")
    if fibre is not None and "fibre" in bonuses:
        positive_factors.append({
            "factor": "Dietary Fibre",
            "impact": f"+{bonuses['fibre']:.1f} pts",
            "description": f"Provides {fibre}g dietary fibre per {u}.",
        })

    # 6. Protein factor
    protein = nutrients.get("protein_g")
    if protein is not None and "protein" in bonuses:
        positive_factors.append({
            "factor": "Protein Source",
            "impact": f"+{bonuses['protein']:.1f} pts",
            "description": f"Provides {protein}g protein per {u}.",
        })

    # 7. Overall Nutrition Summary Narrative
    score = calculation_result["score"]
    grade = calculation_result["grade"]
    rating = calculation_result["rating_label"]

    summary_clauses: List[str] = []
    if positive_factors:
        pos_names = [f["factor"].lower() for f in positive_factors[:2]]
        summary_clauses.append(f"benefits from {' and '.join(pos_names)}")
    if attention_factors:
        att_names = [f["factor"].lower() for f in attention_factors[:2]]
        summary_clauses.append(f"requires attention for {' and '.join(att_names)}")

    if summary_clauses:
        summary_text = f"This product ({rating}, Score {score}/100) {' but '.join(summary_clauses)}."
    else:
        summary_text = f"This product scores {score}/100 with a balanced nutritional distribution."

    # Score breakdown explanation narrative
    base = calculation_result["base_score"]
    tot_p = calculation_result["total_penalties"]
    tot_b = calculation_result["total_bonuses"]
    explanation_narrative = (
        f"Calculated starting from a neutral baseline of {base:.0f} points. "
        f"A total of {tot_p:.1f} penalty points were deducted for elevated nutrient levels "
        f"and {tot_b:.1f} bonus points were awarded for beneficial dietary components, "
        f"resulting in a final score of {score}/100 (Grade {grade})."
    )

    return {
        "nutrition_summary": summary_text,
        "score_explanation": explanation_narrative,
        "positive_factors": positive_factors,
        "attention_factors": attention_factors,
    }
