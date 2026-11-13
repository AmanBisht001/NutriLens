"""
NutriLens – Scoring Engine Validators (Day 5)
Validates nutritional integrity, bounds, logical consistency,
and assesses data completeness for score generation.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from app.scoring_engine.rules import (
    CRITICAL_NUTRIENT_FIELDS,
    ALL_TRACKED_NUTRIENT_FIELDS,
)


@dataclass
class ValidationIssue:
    field: str
    severity: str  # "warning" | "error"
    message: str


@dataclass
class NutritionValidationResult:
    is_valid: bool
    is_scoreable: bool
    data_completeness_pct: float
    present_fields: List[str] = field(default_factory=list)
    missing_critical_fields: List[str] = field(default_factory=list)
    missing_optional_fields: List[str] = field(default_factory=list)
    issues: List[ValidationIssue] = field(default_factory=list)


def validate_nutrition_data(nutrients: Dict[str, Optional[float]]) -> NutritionValidationResult:
    """
    Validates a dictionary of nutrient values (per 100g/ml).
    Checks physical plausibility, logical consistency, and completeness.
    """
    issues: List[ValidationIssue] = []
    present_fields: List[str] = []
    missing_critical_fields: List[str] = []
    missing_optional_fields: List[str] = []

    # 1. Non-negativity and bounds check
    for field_name in ALL_TRACKED_NUTRIENT_FIELDS:
        val = nutrients.get(field_name)
        if val is not None:
            present_fields.append(field_name)
            if val < 0:
                issues.append(
                    ValidationIssue(
                        field=field_name,
                        severity="error",
                        message=f"{field_name} cannot be negative ({val}).",
                    )
                )
        else:
            if field_name in CRITICAL_NUTRIENT_FIELDS:
                missing_critical_fields.append(field_name)
            else:
                missing_optional_fields.append(field_name)

    # 2. Logical consistency checks
    sat_fat = nutrients.get("saturated_fat_g")
    tot_fat = nutrients.get("total_fat_g")
    if sat_fat is not None and tot_fat is not None:
        if sat_fat > (tot_fat + 0.1):
            issues.append(
                ValidationIssue(
                    field="saturated_fat_g",
                    severity="error",
                    message=f"Saturated fat ({sat_fat}g) cannot exceed total fat ({tot_fat}g).",
                )
            )

    trans_fat = nutrients.get("trans_fat_g")
    if trans_fat is not None and tot_fat is not None:
        if trans_fat > (tot_fat + 0.1):
            issues.append(
                ValidationIssue(
                    field="trans_fat_g",
                    severity="error",
                    message=f"Trans fat ({trans_fat}g) cannot exceed total fat ({tot_fat}g).",
                )
            )

    added_sugar = nutrients.get("added_sugar_g")
    tot_sugar = nutrients.get("total_sugar_g")
    if added_sugar is not None and tot_sugar is not None:
        if added_sugar > (tot_sugar + 0.1):
            issues.append(
                ValidationIssue(
                    field="added_sugar_g",
                    severity="warning",
                    message=f"Declared added sugar ({added_sugar}g) exceeds total sugar ({tot_sugar}g).",
                )
            )

    carbs = nutrients.get("carbohydrates_g")
    protein = nutrients.get("protein_g")
    if tot_fat is not None and carbs is not None and protein is not None:
        macro_sum = tot_fat + carbs + protein
        if macro_sum > 105.0:  # Allow 5% tolerance for moisture/ash/analytical variance
            issues.append(
                ValidationIssue(
                    field="macros_sum",
                    severity="warning",
                    message=f"Sum of macronutrients ({macro_sum:.1f}g) exceeds 100g sample weight.",
                )
            )

    # Has critical errors?
    has_blocking_errors = any(issue.severity == "error" for issue in issues)

    # Completeness calculation
    total_fields = len(ALL_TRACKED_NUTRIENT_FIELDS)
    completeness_pct = round((len(present_fields) / total_fields) * 100.0, 1)

    # Scoreable if no critical fields missing and no severe errors
    is_scoreable = (len(missing_critical_fields) == 0) and not has_blocking_errors

    return NutritionValidationResult(
        is_valid=not has_blocking_errors,
        is_scoreable=is_scoreable,
        data_completeness_pct=completeness_pct,
        present_fields=present_fields,
        missing_critical_fields=missing_critical_fields,
        missing_optional_fields=missing_optional_fields,
        issues=issues,
    )
