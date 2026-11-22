"""
NutriLens – Food Label Information Extraction Pipeline (Day 4)
Extracts structured product attributes from raw OCR text:
- Product Name & Brand
- Serving Size
- Ingredient List (with nested parentheses handling)
- Nutrition Facts table (Calories, Fats, Carbs, Sugars, Protein, Sodium)
- Declared & Precautionary Allergens
- Uncertainty & Confidence Flags
"""
import re
from typing import Dict, Any, List, Optional, Tuple, Union


KNOWN_BRANDS = [
    "Britannia", "Parle", "Nestle", "Kellogg's", "Amul", "Quaker",
    "Tata", "Dabur", "Haldiram's", "Cadbury", "Oreo", "Sunfeast",
    "Patanjali", "Saffola", "MTR", "Real", "Tropicana", "Lay's",
    "Doritos", "Kurkure", "Maggi", "Knorr", "Hershey's", "Bikaji",
    "Mother Dairy", "Epigamia", "Borges", "Nutella", "Chocos",
]

KNOWN_CATEGORIES = [
    "Biscuits & Cookies", "Breakfast Cereals", "Dairy & Milks",
    "Snacks & Namkeen", "Chocolates & Sweets", "Beverages",
    "Instant Foods & Noodles", "Condiments & Sauces", "Staples & Grains",
]


def clean_text(text: str) -> str:
    """Removes weird OCR characters, standardizes line breaks and whitespace."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-breaking spaces, zero-width spaces, and tabs
    text = re.sub(r"[\u00a0\u200b\u200c\u200d\uFEFF\t]", " ", text)
    # Replace Unicode dashes and hyphens with standard hyphen
    text = re.sub(r"[—–−‐]", "-", text)
    # Replace table vertical bars with space
    text = re.sub(r"[|]", " ", text)
    # Replace multiple spaces with a single space while preserving newlines
    text = re.sub(r"[ ]{2,}", " ", text)
    return text.strip()


def extract_brand(text: str) -> Optional[str]:
    """Finds known brand names or extracts 'Brand: <name>' pattern."""
    # 1. Regex brand declaration
    brand_match = re.search(r"(?:Brand|Manufactured by|Mfg by|Mfd by)[:\s]+([A-Za-z0-9&'\s]+?)(?:,|\.|\n|$)", text, re.IGNORECASE)
    if brand_match:
        cand = brand_match.group(1).strip()
        if len(cand) >= 2 and len(cand) <= 50:
            for b in KNOWN_BRANDS:
                if b.lower() in cand.lower():
                    return b
            return cand

    # 2. Known brand search
    for brand in KNOWN_BRANDS:
        pattern = r"\b" + re.escape(brand) + r"\b"
        if re.search(pattern, text, re.IGNORECASE):
            return brand

    return None


def extract_product_name(text: str, detected_brand: Optional[str] = None) -> Optional[str]:
    """
    Extracts probable product name from first non-empty lines,
    skipping obvious headers, section markers, ingredient lists, or standalone brand names.
    """
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    in_ingredients = False
    in_nutrition = False

    for line in lines[:15]:
        # Skip OCR label section header markers (e.g. --- [OTHER LABEL] ---)
        if line.startswith("---") or line.endswith("---") or (line.startswith("[") and line.endswith("]")):
            continue
        # Track ingredients start
        if re.match(r"^ingredients?\b", line, re.IGNORECASE):
            in_ingredients = True
            in_nutrition = False
            continue
        # Track nutrition start
        if re.match(r"^nutrition\b", line, re.IGNORECASE):
            in_ingredients = False
            in_nutrition = True
            continue
        # If inside ingredients or nutrition block, skip
        if in_ingredients or in_nutrition:
            continue
        # Skip generic section headers or nutrient names
        if re.match(r"^(nutrition facts|nutrition information|ingredients|contains|allergen|net wt|batch|mfg|exp|mrp|energy|fat|carbohydrate|sugar|protein|sodium|serving|per\b)", line, re.IGNORECASE):
            continue
        # Skip pure brand line if identical
        if detected_brand and line.strip().lower() == detected_brand.lower():
            continue
        # Skip lines with multiple commas (typically lists of ingredients)
        if line.count(",") >= 2:
            continue
        # Skip lines with numbers and units (like 500 kcal or 40g)
        if re.search(r"\b\d+\s*(?:g|mg|kcal|kj|ml)\b", line, re.IGNORECASE):
            continue
        # Skip lines with no letters/numbers
        clean_alpha = re.sub(r"[^a-zA-Z0-9\s]", "", line).strip()
        if len(clean_alpha) < 3:
            continue
        # Return plausible title
        if len(line) >= 3 and len(line) <= 100:
            return line
    return None


def extract_serving_size(text: str) -> Optional[str]:
    """
    Detects serving size patterns:
    'Serving Size: 30g', 'Serve Size20g*', 'Serve Size 20g', 'Per serve (25g)', 'Per 100g', etc.
    """
    patterns = [
        r"(?:serving\s*size|portion\s*size|per\s*serve|serve\s*size)[:\s*]*([0-9]+(?:\.[0-9]+)?\s*(?:g|ml|oz|piece|pieces|biscuit|biscuits|slice|slices)[^,\n\.]*)",
        r"(?:approx\.\s*)?([0-9]+(?:\.[0-9]+)?\s*(?:g|ml)\s*\([^)]+\))",
        r"(?:per\s+serving\s*\(([^)]+)\))",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            clean_val = m.group(1).strip().rstrip("*").strip()
            return clean_val
    return None


def split_ingredients_list(raw_ing_text: str) -> List[str]:
    """
    Splits ingredients by commas and semicolons, respecting nested parentheses,
    square brackets, and curly braces (e.g. for additives, INS codes, and sub-ingredients).
    E.g.: 'Refined Wheat Flour, Sugar, Raising Agents [INS 503(ii), INS 500(ii)], Salt'
    -> ['Refined Wheat Flour', 'Sugar', 'Raising Agents [INS 503(ii), INS 500(ii)]', 'Salt']
    """
    items = []
    current: List[str] = []
    depth = 0

    for char in raw_ing_text:
        if char in ("(", "[", "{"):
            depth += 1
            current.append(char)
        elif char in (")", "]", "}"):
            depth = max(0, depth - 1)
            current.append(char)
        elif char in (",", ";") and depth == 0:
            token = "".join(current).strip()
            if token:
                items.append(token)
            current = []
        else:
            current.append(char)

    last_token = "".join(current).strip()
    if last_token:
        items.append(last_token)

    # Clean up each item: remove trailing periods, numbers, clean whitespace
    cleaned = []
    for item in items:
        # Strip trailing dot
        item = re.sub(r"\.+$", "", item).strip()
        # Remove leading bullets or dashes
        item = re.sub(r"^[\s\-\*\•\d\.]+", "", item).strip()
        if len(item) >= 2:
            cleaned.append(item)

    return cleaned


def extract_ingredients(text: str) -> Tuple[Optional[str], List[str]]:
    """
    Detects ingredients section and returns (raw_ingredients_text, list_of_individual_ingredients).
    Handles Indian packaging declarations, parenthesis groups, and additive codes.
    """
    # Regex to find starting tag: "INGREDIENTS:", "INGREDIENTS -", "LIST OF INGREDIENTS:", etc.
    start_match = re.search(
        r"\b(?:list\s+of\s+ingredients?|ingredients?(?:\s*\(as\s+consumed\))?|ingred[a-z]*)\s*[:\-\.\n\(]\s*",
        text,
        re.IGNORECASE,
    )
    if not start_match:
        # Check alternative: text starting with "Contains: ..." where ingredients are listed directly
        contains_match = re.search(r"\b(?:contains)\s*[:\-\n]\s*([a-zA-Z0-9\s,\(\)%\-\._]{15,})", text, re.IGNORECASE)
        if contains_match and "," in contains_match.group(1):
            raw_section = contains_match.group(1).split("\n\n")[0].strip()
            items = split_ingredients_list(raw_section)
            return (raw_section if items else None, items)
        return None, []

    start_idx = start_match.end()
    remaining = text[start_idx:]

    # Stop at allergen declaration, nutrition table, or manufacturing details
    stop_match = re.search(
        r"(?:\n\s*\n|ALLERGEN\s+INFORMATION|ALLERGENS?|CONTAINS\s+ALLERGENS?|MAY\s+CONTAIN|MFD\s+BY|NUTRITION\s+FACTS|NUTRITION\s+INFORMATION|STORE\s+IN|NET\s+QUANTITY|BATCH\s+NO)",
        remaining,
        re.IGNORECASE,
    )
    if stop_match:
        raw_section = remaining[: stop_match.start()]
    else:
        # If no explicit stop, take up to 6 lines or 600 characters
        lines = remaining.split("\n")
        raw_section = " ".join([l.strip() for l in lines[:6] if l.strip()])

    raw_section = " ".join(raw_section.split()).strip()
    # Remove terminal period
    raw_section = re.sub(r"\.+$", "", raw_section).strip()

    items = split_ingredients_list(raw_section)
    return (raw_section if raw_section else None, items)


def _extract_number(patterns: Union[str, List[str]], text: str) -> Optional[float]:
    """
    Robust helper to extract numerical nutrient values from single or multiple regex patterns.
    Handles parenthesized units like '(kcal)', '(g)', '(mg)', colons, spaces, and multi-line breaks.
    Uses MULTILINE so that ^ / $ anchors in patterns match line boundaries correctly.
    """
    if isinstance(patterns, str):
        patterns = [patterns]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if m:
            try:
                val_str = m.group(1).replace(",", ".").rstrip(".")
                return float(val_str)
            except (ValueError, IndexError):
                continue
    return None


def extract_nutrition_facts(text: str) -> Dict[str, Optional[float]]:
    """
    Extracts key macronutrients from nutrition facts text.
    Handles:
    - Single-line (e.g. 'Energy: 460 kcal', 'Energy (kcal) 554')
    - Multi-line table rows (e.g. 'Energy (kcal)\\n554')
    - Units inside parentheses or brackets in label names (e.g. 'Total Fat (g)', 'Sodium [mg]')
    - Multi-column tables (e.g. 'Energy (kcal) 554 111' -> extracts 554 per 100g)
    - Indian packaging misreads (e.g. 'ydrate', 'ated Fat', 'ans Fat', 'JedSugars')
    - UK/EU formats ('of which saturates', 'of which sugars', 'Salt' converted to sodium)
    - Standalone unit deduction (e.g. solitary '554 kcal' -> Energy, '694 mg' -> Sodium)
    """
    facts: Dict[str, Optional[float]] = {
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

    # 1. Energy / Calories (kcal or kJ/kcal split e.g. '2110 kJ / 504 kcal')
    split_energy = re.search(
        r"(?:energy|calories|energy\s+value)[^\n\d]*\d+\s*(?:kj)?\s*/\s*([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|cal)?",
        text,
        re.IGNORECASE,
    )
    if split_energy:
        try:
            facts["energy_kcal"] = float(split_energy.group(1).replace(",", "."))
        except ValueError:
            pass

    if facts["energy_kcal"] is None:
        facts["energy_kcal"] = _extract_number(
            [
                r"(?:energy|calories|energy\s+value|caloric\s+value)(?:\s*[\(\[]\s*(?:kcal|kj|cal)\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)(?:\s*(?:kcal|cal))?",
                r"(?:energy|calories)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|cal)?",
            ],
            text,
        )

    # Unit-based fallback for Energy: in food labels, 'kcal' is exclusively used for Energy
    if facts["energy_kcal"] is None:
        kcal_match = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*kcal\b", text, re.IGNORECASE)
        if kcal_match:
            try:
                facts["energy_kcal"] = float(kcal_match.group(1).replace(",", "."))
            except ValueError:
                pass

    # 2. Saturated Fat (checked before Total Fat to prevent overlap)
    facts["saturated_fat_g"] = _extract_number(
        [
            r"(?:saturated\s+fat|saturated\s+fatty\s+acids|of\s+which\s+saturates|saturates|sat\s+fat|[a-z]*ated\s+fat)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?:saturated\s+fat|saturated\s+fatty\s+acids|of\s+which\s+saturates|saturates|[a-z]*ated\s+fat)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        ],
        text,
    )

    # 3. Trans Fat
    facts["trans_fat_g"] = _extract_number(
        [
            r"(?:trans\s+fat|trans\s+fatty\s+acids|of\s+which\s+trans|transfat|[a-z]*ans\s+fat)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?:trans\s+fat|trans\s+fatty\s+acids|[a-z]*ans\s+fat)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        ],
        text,
    )
    if facts["trans_fat_g"] is None and facts["saturated_fat_g"] is not None:
        post_sat_trans = re.search(r"(?:ated|saturated)\s+fat[\s\S]*?\bFat[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b)", text, re.IGNORECASE)
        if post_sat_trans:
            try:
                facts["trans_fat_g"] = float(post_sat_trans.group(1).replace(",", "."))
            except ValueError:
                pass

    # 4. Total Fat (find "Total Fat" or standalone "Fat", avoiding Saturated or Trans)
    # NOTE: truncated-OCR pattern must come FIRST to avoid matching Trans Fat "Fat 0.1g" label.
    # On cropped Indian food labels, "Total Fat" is often truncated to "It" or just "Fat" at line start.
    facts["total_fat_g"] = _extract_number(
        [
            # Specific "Total Fat" label — highest priority
            r"(?:total\s+fat|crude\s+fat)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            # Truncated OCR: line containing only 'It', 'it', 'Fat', or similar followed by value on next line
            # This handles cropped labels where "Fat" or "Total Fat" gets cut to "It" at line boundary
            r"^[ \t]*(?:[a-z]{0,2}[Ii]t|[Tt]otal\s+[Ff]at)[ \t]*$\n[ \t]*([0-9]+(?:\.[0-9]+)?)[ \t]*g\b",
            # Generic standalone "Fat" — lowest priority (also matches Trans Fat label row)
            r"(?<!saturated\s)(?<!ated\s)(?<!trans\s)(?<!ans\s)\bfat(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?:total\s+fat|(?<!saturated\s)(?<!ated\s)(?<!trans\s)(?<!ans\s)\bfat|crude\s+fat)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        ],
        text,
    )

    # Re-validate Total Fat does not duplicate Saturated or Trans Fat
    if facts["total_fat_g"] is not None:
        if facts["total_fat_g"] == facts["saturated_fat_g"] or facts["total_fat_g"] == facts["trans_fat_g"]:
            facts["total_fat_g"] = None

    # Positional check: Total Fat is usually the number preceding Saturated Fat
    if facts["total_fat_g"] is None and facts["saturated_fat_g"] is not None:
        pre_sat_fat = re.search(r"(?:^|[^\w])([0-9]+(?:\.[0-9]+)?)\s*(?:g|go)\b[^\n\d]*\n?[^\n\d]*(?:ated|saturated)\s+fat", text, re.IGNORECASE)
        if pre_sat_fat:
            try:
                facts["total_fat_g"] = float(pre_sat_fat.group(1).replace(",", "."))
            except ValueError:
                pass

    # 5. Carbohydrates (handles 'carbohydrates', 'carbs', and truncated 'ydrate')
    facts["carbohydrates_g"] = _extract_number(
        [
            r"(?:carbohydrates?|total\s+carbohydrates?|total\s+carbs|carbs|[a-z]*(?:hydrate|ydrate))(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?:carbohydrate|carbohydrates|total\s+carbohydrates|total\s+carbs|carbs|[a-z]*(?:hydrate|ydrate))[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        ],
        text,
    )

    # 6. Added Sugars (checked before Total Sugars to prevent Added Sugars from being captured as Total)
    facts["added_sugar_g"] = _extract_number(
        [
            r"(?:added\s*sugars?|of\s+which\s+added\s+sugars?|[a-z]*ed\s*sugars?)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?:added\s*sugars?|[a-z]*ed\s*sugars?)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        ],
        text,
    )

    # 7. Total Sugars / 'of which sugars'
    facts["total_sugar_g"] = _extract_number(
        [
            r"(?:total\s+sugars?|of\s+which\s+sugars?)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?<!added\s)(?<!jed\s)(?<![a-z]ed\s)\bsugars?(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?:total\s+sugars?|of\s+which\s+sugars?|(?<!added\s)(?<!jed\s)(?<![a-z]ed\s)\bsugars?)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        ],
        text,
    )

    # 8. Dietary Fibre / Fibre / Fiber
    facts["dietary_fibre_g"] = _extract_number(
        [
            r"(?:dietary\s+fib(?:re|er)|crude\s+fib(?:re|er)|fib(?:re|er))(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?:dietary\s+fib(?:re|er)|fib(?:re|er))[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        ],
        text,
    )

    # 9. Protein
    facts["protein_g"] = _extract_number(
        [
            r"(?:protein|crude\s+protein)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
            r"(?:protein|crude\s+protein)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        ],
        text,
    )
    # Positional check: in standard Indian nutrition tables, Protein is the row between Energy (kcal) and Carbohydrate
    if facts["protein_g"] is None:
        table_protein = re.search(r"kcal[\s\S]*?\b([0-9]+(?:\.[0-9]+)?)\s*g\b[\s\S]*?[a-z]*(?:hydrate|ydrate)", text, re.IGNORECASE)
        if table_protein:
            try:
                facts["protein_g"] = float(table_protein.group(1).replace(",", "."))
            except ValueError:
                pass

    # 10. Sodium (mg or g) or Salt (g converted: 1g salt ≈ 400mg sodium)
    sodium_val = _extract_number(
        [
            r"(?:sodium|[a-z]*dium)(?:\s*[\(\[]\s*(?:mg|g)\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:mg)?",
            r"(?:sodium|[a-z]*dium)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:mg)?",
        ],
        text,
    )
    if sodium_val is not None:
        # Check if unit was grams
        m_g = re.search(r"(?:sodium|[a-z]*dium)(?:\s*[\(\[]\s*g\s*[\)\]]|[\s:\-–—\t]*[0-9]+(?:[\.,][0-9]+)?\s*g\b)", text, re.IGNORECASE)
        if m_g:
            sodium_val = sodium_val * 1000.0  # Convert grams to mg
        facts["sodium_mg"] = sodium_val
    else:
        # Check for standalone mg in table
        mg_match = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*mg\b", text, re.IGNORECASE)
        if mg_match:
            try:
                facts["sodium_mg"] = float(mg_match.group(1).replace(",", "."))
            except ValueError:
                pass
        # Check for Salt declaration (common on Indian and UK packaged goods)
        if facts["sodium_mg"] is None:
            salt_val = _extract_number(
                [
                    r"(?:salt)(?:\s*[\(\[]\s*(?:g|mg)\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|mg\b)?",
                    r"(?:salt)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|mg\b)?",
                ],
                text,
            )
            if salt_val is not None:
                # If declared in grams (standard on food labels), convert to sodium in mg: 1g salt = 400mg sodium
                m_salt_mg = re.search(r"(?:salt)(?:\s*[\(\[]\s*mg\s*[\)\]]|[\s:\-–—\t]*[0-9]+(?:\.[0-9]+)?\s*mg\b)", text, re.IGNORECASE)
                if m_salt_mg:
                    facts["sodium_mg"] = round(salt_val * 0.4, 2)
                else:
                    facts["sodium_mg"] = round(salt_val * 400.0, 2)

    return facts


def extract_allergens(text: str) -> Tuple[List[str], List[str]]:
    """
    Extracts declared allergens and precautionary allergen statements.
    Returns: (declared_allergens, precautionary_allergens)
    """
    declared: List[str] = []
    precautionary: List[str] = []

    # 1. Declared allergens: "Contains: Wheat, Milk, Soy" or "Contains Wheat, Soy"
    decl_match = re.search(
        r"(?:ALLERGEN\s+(?:ADVICE|INFORMATION|DECLARATION)[:\s]*)?(?:CONTAINS|ALLERGENS?)[:\s]+(?!MAY\b)([^\.\n]+)",
        text,
        re.IGNORECASE,
    )
    if decl_match:
        raw_decl = decl_match.group(1).strip()
        items = re.split(r"[,;&]|\band\b", raw_decl, flags=re.IGNORECASE)
        for it in items:
            cleaned = re.sub(r"^(?:contains|allergens?:?)\s*", "", it, flags=re.IGNORECASE).strip().strip(".")
            if len(cleaned) >= 2 and not re.match(r"^(and|or)$", cleaned, re.IGNORECASE):
                declared.append(cleaned.capitalize())

    # 2. Precautionary allergens: "May contain: Peanuts, Tree Nuts" or "Processed in facility..."
    prec_match = re.search(
        r"(?:MAY\s+CONTAIN|MANUFACTURED\s+IN\s+A\s+FACILITY\s+THAT\s+ALSO\s+PROCESSES|MADE\s+ON\s+EQUIPMENT\s+THAT\s+ALSO\s+PROCESSES)[:\s]+([^\.\n]+)",
        text,
        re.IGNORECASE,
    )
    if prec_match:
        raw_prec = prec_match.group(1).strip()
        items = re.split(r"[,;&]|\band\b", raw_prec, flags=re.IGNORECASE)
        for it in items:
            cleaned = re.sub(r"^(?:may\s+contain|also\s+processes|contains)\s*", "", it, flags=re.IGNORECASE).strip().strip(".")
            if len(cleaned) >= 2 and not re.match(r"^(and|or)$", cleaned, re.IGNORECASE):
                precautionary.append(cleaned.capitalize())

    return declared, precautionary


def extract_structured_label_info(
    raw_ocr_text: str,
    ocr_confidence: float = 0.0,
    ocr_engine: str = "fallback",
) -> Dict[str, Any]:
    """
    Master pipeline transforming raw OCR text into structured product data,
    generating uncertainty flags where values are missing or ambiguous.
    """
    cleaned = clean_text(raw_ocr_text)
    uncertainty_flags: List[str] = []

    # Extract components
    brand = extract_brand(cleaned)
    product_name = extract_product_name(cleaned, detected_brand=brand)
    serving_size = extract_serving_size(cleaned)
    raw_ingredients_text, ingredients_list = extract_ingredients(cleaned)
    nutrition_facts = extract_nutrition_facts(cleaned)
    declared_allergens, precautionary_allergens = extract_allergens(cleaned)

    # Uncertainty checks:
    if not product_name:
        uncertainty_flags.append("Product name not clearly detected; please review.")
    if not brand:
        uncertainty_flags.append("Brand name could not be automatically identified.")
    if not serving_size:
        uncertainty_flags.append("Serving size not found on label.")
    if not ingredients_list or len(ingredients_list) == 0:
        uncertainty_flags.append("Ingredients list not found or could not be parsed.")
    if ocr_confidence < 0.60 and ocr_engine != "fallback":
        uncertainty_flags.append(f"Low overall OCR confidence ({ocr_confidence:.0%}).")

    # Check for empty nutrition facts
    found_nutrients = [k for k, v in nutrition_facts.items() if v is not None]
    if len(found_nutrients) == 0:
        uncertainty_flags.append("No nutrition facts values detected.")
    elif len(found_nutrients) < 3:
        uncertainty_flags.append("Nutrition facts appear incomplete.")

    return {
        "product_name": product_name,
        "brand": brand,
        "category": "Snacks & Namkeen" if "biscuit" not in (product_name or "").lower() else "Biscuits & Cookies",
        "serving_size": serving_size or "100g",
        "raw_ingredients_text": raw_ingredients_text,
        "ingredients": ingredients_list,
        "nutrition_facts": nutrition_facts,
        "declared_allergens": declared_allergens,
        "precautionary_allergens": precautionary_allergens,
        "ocr_confidence": round(ocr_confidence, 4),
        "ocr_engine": ocr_engine,
        "uncertainty_flags": uncertainty_flags,
        "is_verified": False,  # Never treat raw/extracted OCR as verified
    }
