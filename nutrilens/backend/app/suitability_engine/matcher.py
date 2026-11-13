"""
NutriLens – Suitability Matcher & Conflict Detector (Day 6)
Executes rule-based matching across declared allergens, precautionary statements,
dietary preferences (veg/vegan/jain), restrictions, and nutritional goals.
"""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Any

from app.suitability_engine.rules import (
    STATUS_SUITABLE,
    STATUS_CAUTION,
    STATUS_CONFLICT,
    STATUS_INSUFFICIENT,
    STATUS_COLOR_MAP,
    ALLERGEN_SYNONYMS,
    NON_VEGETARIAN_TERMS,
    NON_VEGAN_TERMS,
    NON_JAIN_TERMS,
    AMBIGUOUS_VEGETARIAN_TERMS,
    GOAL_THRESHOLDS,
    SAFETY_DISCLAIMER,
    SUITABILITY_ENGINE_VERSION,
)


@dataclass
class SuitabilityItem:
    category: str       # "allergen" | "dietary_preference" | "dietary_restriction" | "nutrition_goal" | "safety"
    severity: str       # "conflict" | "caution" | "aligned" | "info"
    title: str
    detail: str
    source_ingredient: Optional[str] = None
    is_precautionary: bool = False


@dataclass
class SuitabilityEvaluation:
    status: str
    status_label: str
    badge_color: str
    is_suitable: bool
    summary_narrative: str
    conflicts: List[SuitabilityItem] = field(default_factory=list)
    cautions: List[SuitabilityItem] = field(default_factory=list)
    positive_observations: List[SuitabilityItem] = field(default_factory=list)
    safety_warnings: List[str] = field(default_factory=list)
    rules_applied: List[str] = field(default_factory=list)
    engine_version: str = SUITABILITY_ENGINE_VERSION
    disclaimer: str = SAFETY_DISCLAIMER


def _normalize_text(text: str) -> str:
    return re.sub(r"[^\w\s]", " ", text.lower()).strip()


def _get_synonyms_for_allergen(user_allergen: str) -> Set[str]:
    clean = user_allergen.strip().lower()
    for canon, syns in ALLERGEN_SYNONYMS.items():
        if clean == canon or clean in syns or canon in clean:
            return syns
    return {clean}


def evaluate_suitability(
    product_name: str,
    product_ingredients: List[Dict[str, Any]],
    product_allergens: List[Dict[str, Any]],
    raw_ingredients_text: Optional[str],
    nutrition_facts: Optional[Dict[str, Optional[float]]],
    user_preference: Optional[str],
    user_allergies: List[str],
    user_restrictions: List[str],
    user_nutrition_goals: List[str],
    user_monitored_nutrients: List[str],
) -> SuitabilityEvaluation:
    """
    Main rule-based suitability evaluator.
    Maintains strict separation between declared allergens and 'may contain' warnings.
    Handles missing ingredient information safely.
    """
    conflicts: List[SuitabilityItem] = []
    cautions: List[SuitabilityItem] = []
    positive_obs: List[SuitabilityItem] = []
    safety_warnings: List[str] = []
    rules_applied: List[str] = []

    # 1. Missing Ingredients Check (Requirement: Missing ingredient info must produce uncertainty warning)
    has_ingredients = bool(product_ingredients and len(product_ingredients) > 0) or bool(raw_ingredients_text and len(raw_ingredients_text.strip()) > 5)

    if not has_ingredients:
        safety_warnings.append(
            "Missing ingredient declarations. Suitability cannot be verified without declared package ingredients."
        )
        safety_warnings.append(
            "Not detecting an allergen does not prove that the product is allergen-free."
        )
        return SuitabilityEvaluation(
            status=STATUS_INSUFFICIENT,
            status_label=STATUS_INSUFFICIENT,
            badge_color=STATUS_COLOR_MAP[STATUS_INSUFFICIENT],
            is_suitable=False,
            summary_narrative="Ingredient information is not available for this product. Personal dietary suitability cannot be reliably determined.",
            conflicts=[],
            cautions=[],
            positive_observations=[],
            safety_warnings=safety_warnings,
            rules_applied=["Rule: Missing ingredient declaration check"],
        )

    # Compile declared ingredient text tokens (excluding any trailing precautionary clauses)
    declared_ingredient_strings: List[str] = []
    for ing in product_ingredients:
        name = ing.get("name") or ing.get("original_text") or ""
        if name:
            declared_ingredient_strings.append(name.strip())

    precautionary_raw_text = ""
    if raw_ingredients_text:
        # Separate declared ingredients block from precautionary "may contain" clauses
        prec_split = re.split(
            r"(?:may\s+contain|manufactured\s+in\s+a\s+facility|made\s+on\s+equipment)",
            raw_ingredients_text,
            flags=re.IGNORECASE,
        )
        clean_raw_declared = prec_split[0]
        if clean_raw_declared.strip():
            declared_ingredient_strings.append(clean_raw_declared.strip())
        if len(prec_split) > 1:
            precautionary_raw_text = " ".join(prec_split[1:]).lower()

    declared_ingredients_corpus = " ".join(declared_ingredient_strings).lower()
    full_ingredient_corpus = f"{declared_ingredients_corpus} {precautionary_raw_text}".strip()

    # -----------------------------------------------------------------------
    # 2. Check User Food Allergies
    # Strict separation: Declared allergen = Conflict | May contain = Caution
    # -----------------------------------------------------------------------
    if user_allergies:
        rules_applied.append(f"Rule: Allergen cross-check against {len(user_allergies)} declared allergy profile(s)")

        # Compile declared vs precautionary product allergens
        declared_allergens_set: Set[str] = set()
        precautionary_allergens_set: Set[str] = set()

        for pa in product_allergens:
            name = (pa.get("name") or "").strip().lower()
            decl_type = (pa.get("declaration_type") or "declared").strip().lower()
            if decl_type == "declared":
                declared_allergens_set.add(name)
            else:
                precautionary_allergens_set.add(name)

        for user_alg in user_allergies:
            clean_alg = user_alg.strip().lower()
            if not clean_alg:
                continue

            synonyms = _get_synonyms_for_allergen(clean_alg)
            detected_declared = False

            # A. Check Declared Allergens table
            for decl in declared_allergens_set:
                if any(syn in decl or decl in syn for syn in synonyms):
                    conflicts.append(SuitabilityItem(
                        category="allergen",
                        severity="conflict",
                        title=f"Declared Allergen: {user_alg.capitalize()}",
                        detail=f"Product explicitly declares containing '{decl.capitalize()}', matching your declared allergy to {user_alg}.",
                        source_ingredient=decl,
                        is_precautionary=False,
                    ))
                    detected_declared = True
                    break

            # B. Check Declared Ingredients (NEVER match against precautionary text here)
            if not detected_declared:
                for syn in synonyms:
                    pattern = r"\b" + re.escape(syn) + r"\b"
                    if re.search(pattern, declared_ingredients_corpus):
                        conflicts.append(SuitabilityItem(
                            category="allergen",
                            severity="conflict",
                            title=f"Declared Ingredient Allergen: {user_alg.capitalize()}",
                            detail=f"Detected ingredient '{syn}' matching your declared allergy to {user_alg}.",
                            source_ingredient=syn,
                            is_precautionary=False,
                        ))
                        detected_declared = True
                        break

            # C. Check Precautionary Allergens (ONLY if not already a declared conflict)
            if not detected_declared:
                matched_precautionary = False
                for prec in precautionary_allergens_set:
                    if any(syn in prec or prec in syn for syn in synonyms):
                        cautions.append(SuitabilityItem(
                            category="allergen",
                            severity="caution",
                            title=f"Precautionary Warning: {user_alg.capitalize()}",
                            detail=f"Label includes a cross-contact advisory: 'May contain {prec.capitalize()}'. (Precautionary statement, not a declared ingredient).",
                            source_ingredient=prec,
                            is_precautionary=True,
                        ))
                        matched_precautionary = True
                        break

                if not matched_precautionary and precautionary_raw_text:
                    # Scan precautionary text block for matching allergen
                    for syn in synonyms:
                        pattern = r"\b" + re.escape(syn) + r"\b"
                        if re.search(pattern, precautionary_raw_text):
                            cautions.append(SuitabilityItem(
                                category="allergen",
                                severity="caution",
                                title=f"Precautionary Advisory: {user_alg.capitalize()}",
                                detail=f"Advisory statement indicates potential cross-contact with {user_alg}.",
                                source_ingredient=syn,
                                is_precautionary=True,
                            ))
                            break

    # -----------------------------------------------------------------------
    # 3. Check Dietary Preference (Vegetarian / Vegan / Jain)
    # -----------------------------------------------------------------------
    pref_clean = (user_preference or "none").strip().lower()

    if pref_clean in ("vegetarian", "lacto-vegetarian", "lacto-ovo vegetarian"):
        rules_applied.append("Rule: Vegetarian dietary pattern check")
        found_non_veg = []
        for term in NON_VEGETARIAN_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", full_ingredient_corpus):
                found_non_veg.append(term)

        if found_non_veg:
            conflicts.append(SuitabilityItem(
                category="dietary_preference",
                severity="conflict",
                title="Non-Vegetarian Ingredient Detected",
                detail=f"Product contains animal-derived ingredient(s): {', '.join(set(found_non_veg))}, conflicting with your Vegetarian preference.",
                source_ingredient=", ".join(set(found_non_veg)),
            ))
        else:
            # Check ambiguous terms
            ambiguous_found = [t for t in AMBIGUOUS_VEGETARIAN_TERMS if re.search(r"\b" + re.escape(t) + r"\b", full_ingredient_corpus)]
            if ambiguous_found:
                cautions.append(SuitabilityItem(
                    category="dietary_preference",
                    severity="caution",
                    title="Ambiguous Ingredient Origin",
                    detail=f"Contains ingredient(s) that may be of plant or animal origin: {', '.join(set(ambiguous_found))}. Plant-based origin not explicitly verified on label.",
                    source_ingredient=", ".join(set(ambiguous_found)),
                ))
            else:
                positive_obs.append(SuitabilityItem(
                    category="dietary_preference",
                    severity="aligned",
                    title="Vegetarian Aligned",
                    detail="No animal-derived or meat ingredients identified.",
                ))

    elif pref_clean == "vegan":
        rules_applied.append("Rule: Vegan 100% plant-based check")
        found_non_vegan = []
        for term in NON_VEGAN_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", full_ingredient_corpus):
                found_non_vegan.append(term)

        if found_non_vegan:
            conflicts.append(SuitabilityItem(
                category="dietary_preference",
                severity="conflict",
                title="Animal/Dairy Ingredient Detected",
                detail=f"Contains animal, dairy, or insect-derived item(s): {', '.join(set(found_non_vegan))}, conflicting with your Vegan preference.",
                source_ingredient=", ".join(set(found_non_vegan)),
            ))
        else:
            positive_obs.append(SuitabilityItem(
                category="dietary_preference",
                severity="aligned",
                title="Vegan Aligned",
                detail="No animal, dairy, egg, or honey ingredients declared.",
            ))

    elif pref_clean == "jain":
        rules_applied.append("Rule: Jain vegetarian dietary check")
        found_non_jain = []
        for term in NON_JAIN_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", full_ingredient_corpus):
                found_non_jain.append(term)

        if found_non_jain:
            conflicts.append(SuitabilityItem(
                category="dietary_preference",
                severity="conflict",
                title="Non-Jain Ingredient Detected",
                detail=f"Contains root vegetable or restricted ingredient(s): {', '.join(set(found_non_jain))}, conflicting with Jain dietary principles.",
                source_ingredient=", ".join(set(found_non_jain)),
            ))
        else:
            positive_obs.append(SuitabilityItem(
                category="dietary_preference",
                severity="aligned",
                title="Jain Aligned",
                detail="No root vegetables, tubers, meat, or eggs detected.",
            ))

    # -----------------------------------------------------------------------
    # 4. Check Specific Dietary Restrictions (Gluten-Free, Halal, etc.)
    # -----------------------------------------------------------------------
    if user_restrictions:
        for rest in user_restrictions:
            clean_rest = rest.strip().lower()

            if "gluten" in clean_rest:
                rules_applied.append("Rule: Gluten-Free restriction check")
                gluten_found = []
                for syn in ALLERGEN_SYNONYMS["gluten"]:
                    if re.search(r"\b" + re.escape(syn) + r"\b", full_ingredient_corpus):
                        gluten_found.append(syn)
                if gluten_found:
                    conflicts.append(SuitabilityItem(
                        category="dietary_restriction",
                        severity="conflict",
                        title="Gluten Source Detected",
                        detail=f"Contains gluten-bearing grain(s): {', '.join(set(gluten_found))}, conflicting with your Gluten-Free restriction.",
                        source_ingredient=", ".join(set(gluten_found)),
                    ))
                else:
                    positive_obs.append(SuitabilityItem(
                        category="dietary_restriction",
                        severity="aligned",
                        title="Gluten-Free Aligned",
                        detail="No gluten-containing grains declared in ingredients list.",
                    ))

            elif "lactose" in clean_rest or "dairy" in clean_rest:
                rules_applied.append("Rule: Dairy/Lactose-Free restriction check")
                dairy_found = []
                for syn in ALLERGEN_SYNONYMS["milk"]:
                    if re.search(r"\b" + re.escape(syn) + r"\b", full_ingredient_corpus):
                        dairy_found.append(syn)
                if dairy_found:
                    conflicts.append(SuitabilityItem(
                        category="dietary_restriction",
                        severity="conflict",
                        title="Dairy/Lactose Ingredient Detected",
                        detail=f"Contains dairy-derived ingredient(s): {', '.join(set(dairy_found))}.",
                        source_ingredient=", ".join(set(dairy_found)),
                    ))

            elif "halal" in clean_rest:
                rules_applied.append("Rule: Halal compliance check")
                haram_found = [t for t in ("pork", "bacon", "lard", "alcohol", "wine", "beer", "gelatin") if re.search(r"\b" + re.escape(t) + r"\b", full_ingredient_corpus)]
                if haram_found:
                    conflicts.append(SuitabilityItem(
                        category="dietary_restriction",
                        severity="conflict",
                        title="Restricted Ingredient for Halal",
                        detail=f"Contains ingredient(s) requiring verified Halal certification: {', '.join(set(haram_found))}.",
                        source_ingredient=", ".join(set(haram_found)),
                    ))

    # -----------------------------------------------------------------------
    # 5. Check User Nutrition Goals & Monitored Nutrients
    # -----------------------------------------------------------------------
    if nutrition_facts:
        if user_nutrition_goals:
            for goal in user_nutrition_goals:
                clean_goal = goal.strip().lower()
                cfg = GOAL_THRESHOLDS.get(clean_goal)
                if cfg:
                    rules_applied.append(f"Rule: Nutrition goal evaluation ({cfg['label']})")
                    val = nutrition_facts.get(cfg["nutrient"])
                    if val is not None:
                        if "max_threshold" in cfg and val > cfg["max_threshold"]:
                            cautions.append(SuitabilityItem(
                                category="nutrition_goal",
                                severity="caution",
                                title=f"Goal Advisory: {cfg['label']}",
                                detail=f"Contains {val}{cfg['unit']} of {cfg['nutrient'].replace('_', ' ')} per 100g (Target: <={cfg['max_threshold']}{cfg['unit']}).",
                            ))
                        elif "min_threshold" in cfg:
                            if val >= cfg["min_threshold"]:
                                positive_obs.append(SuitabilityItem(
                                    category="nutrition_goal",
                                    severity="aligned",
                                    title=f"Goal Aligned: {cfg['label']}",
                                    detail=f"Provides {val}{cfg['unit']} of {cfg['nutrient'].replace('_', ' ')} per 100g (Target: >={cfg['min_threshold']}{cfg['unit']}).",
                                ))

        if user_monitored_nutrients:
            for nut in user_monitored_nutrients:
                val = nutrition_facts.get(nut)
                if val is not None:
                    rules_applied.append(f"Rule: Monitored nutrient tracking ({nut})")
                    # Check if high according to general benchmarks
                    if nut == "sodium_mg" and val > 500:
                        cautions.append(SuitabilityItem(
                            category="nutrition_goal",
                            severity="caution",
                            title="Monitored Nutrient Notice: High Sodium",
                            detail=f"Product contains {val:.0f}mg sodium per 100g, which you have flagged to monitor.",
                        ))
                    elif "sugar" in nut and val > 15:
                        cautions.append(SuitabilityItem(
                            category="nutrition_goal",
                            severity="caution",
                            title="Monitored Nutrient Notice: Elevated Sugar",
                            detail=f"Product contains {val:.1f}g sugar per 100g, which you have flagged to monitor.",
                        ))

    # -----------------------------------------------------------------------
    # 6. Overall Status Determination
    # -----------------------------------------------------------------------
    if conflicts:
        overall_status = STATUS_CONFLICT
        is_suitable = False
        summary = (
            f"Declared restriction conflict detected. This product conflicts with your "
            f"profile: {', '.join([c.title for c in conflicts[:2]])}."
        )
    elif cautions:
        overall_status = STATUS_CAUTION
        is_suitable = False  # Caution requires consumer attention
        summary = (
            f"Caution advised based on available declarations. Precautionary or goal-related advisories: "
            f"{', '.join([c.title for c in cautions[:2]])}."
        )
    else:
        overall_status = STATUS_SUITABLE
        is_suitable = True
        summary = (
            "Suitable based on available information. No declared conflicts or precautionary "
            "warnings matched your dietary profile."
        )

    # Standard safety reminders
    safety_warnings.append(
        "Not detecting an allergen does not prove that the product is completely allergen-free."
    )
    if any(c.is_precautionary for c in cautions):
        safety_warnings.append(
            "Precautionary statements indicate possible shared equipment or facility cross-contact."
        )

    return SuitabilityEvaluation(
        status=overall_status,
        status_label=overall_status,
        badge_color=STATUS_COLOR_MAP[overall_status],
        is_suitable=is_suitable,
        summary_narrative=summary,
        conflicts=conflicts,
        cautions=cautions,
        positive_observations=positive_obs,
        safety_warnings=safety_warnings,
        rules_applied=rules_applied,
    )
