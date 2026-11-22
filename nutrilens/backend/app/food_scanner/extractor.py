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
from typing import Dict, Any, List, Optional, Tuple


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
    """Removes weird OCR characters and standardizes line breaks."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Replace common OCR misreads in nutrient tables
    text = re.sub(r"[|—–]", " ", text)
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
    Splits ingredients by commas, respecting parentheses.
    E.g.: 'Refined Wheat Flour, Sugar, Edible Vegetable Oil (Palm, Soy), Salt'
    -> ['Refined Wheat Flour', 'Sugar', 'Edible Vegetable Oil (Palm, Soy)', 'Salt']
    """
    items = []
    current: List[str] = []
    depth = 0

    for char in raw_ing_text:
        if char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
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
    """
    # Regex to find starting tag: "INGREDIENTS:", "INGREDIENTS -", or standalone "INGREDIENTS" line
    start_match = re.search(r"\bINGREDIENTS?\s*[:\-\n]\s*", text, re.IGNORECASE)
    if not start_match:
        # Check alternative: text starting with "Contains: ..." where no other ingredients block exists
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


def _extract_number(pattern: str, text: str) -> Optional[float]:
    """Helper to find float nutrient values from regex pattern, supporting space-separated lines."""
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        try:
            val_str = m.group(1).replace(",", ".")
            return float(val_str)
        except ValueError:
            return None
    return None


def extract_nutrition_facts(text: str) -> Dict[str, Optional[float]]:
    """
    Extracts key macronutrients from nutrition facts text.
    Handles per 100g or per serving figures across both inline and multi-line formats,
    recognizing Indian, UK/EU, and US packaged food label variations:
    - Energy / Calories (including 'kJ / kcal' split e.g. '2110 / 504')
    - Total Fat / Fat
    - Saturated Fat / Saturates / of which saturates
    - Trans Fat
    - Carbohydrates / Carbs
    - Total Sugars / Sugars / of which sugars
    - Added Sugars
    - Dietary Fibre / Fibre / Fiber
    - Protein
    - Sodium (mg) or Salt (g converted to sodium: salt_g * 400 mg)
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

    # 1. Energy / Calories (kcal or kJ/kcal)
    # Check for split format e.g. "Energy (kJ/kcal) 2110 / 504" or "2110 kJ / 504 kcal"
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
            r"(?:energy|calories|energy\s+value)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:kcal|cal)?",
            text,
        )

    # 2. Total Fat (find "Total Fat" or standalone "Fat", avoiding Saturated or Trans)
    fat_match = re.search(
        r"(?:total\s+fat|(?<!saturated\s)(?<!trans\s)\bfat|crude\s+fat)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        text,
        re.IGNORECASE,
    )
    if fat_match:
        try:
            facts["total_fat_g"] = float(fat_match.group(1).replace(",", "."))
        except ValueError:
            pass

    # 3. Saturated Fat / Saturates / 'of which saturates'
    facts["saturated_fat_g"] = _extract_number(
        r"(?:saturated\s+fat|saturated\s+fatty\s+acids|of\s+which\s+saturates|saturates)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        text,
    )

    # 4. Trans Fat
    facts["trans_fat_g"] = _extract_number(
        r"(?:trans\s+fat|trans\s+fatty\s+acids)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        text,
    )

    # 5. Carbohydrates
    facts["carbohydrates_g"] = _extract_number(
        r"(?:carbohydrate|carbohydrates|total\s+carbohydrates|total\s+carbs|carbs)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        text,
    )

    # 6. Total Sugars / 'of which sugars'
    sug_match = re.search(
        r"(?:total\s+sugars?|of\s+which\s+sugars?|(?<!added\s)\bsugars?)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        text,
        re.IGNORECASE,
    )
    if sug_match:
        try:
            facts["total_sugar_g"] = float(sug_match.group(1).replace(",", "."))
        except ValueError:
            pass

    # 7. Added Sugars
    facts["added_sugar_g"] = _extract_number(
        r"(?:added\s+sugars?)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        text,
    )

    # 8. Dietary Fibre / Fibre / Fiber
    facts["dietary_fibre_g"] = _extract_number(
        r"(?:dietary\s+fib(?:re|er)|fib(?:re|er))[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        text,
    )

    # 9. Protein
    facts["protein_g"] = _extract_number(
        r"(?:protein|crude\s+protein)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
        text,
    )

    # 10. Sodium (mg or g) or Salt (g converted: 1g salt ≈ 400mg sodium)
    sodium_val = _extract_number(
        r"(?:sodium)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:mg)?",
        text,
    )
    if sodium_val is not None:
        # Check if unit was grams
        m_g = re.search(r"(?:sodium)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*g\b", text, re.IGNORECASE)
        if m_g:
            sodium_val = sodium_val * 1000.0  # Convert grams to mg
        facts["sodium_mg"] = sodium_val
    else:
        # Check for Salt declaration (common on Indian and UK packaged goods)
        salt_val = _extract_number(
            r"(?:salt)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|mg\b)?",
            text,
        )
        if salt_val is not None:
            # If declared in grams (standard on food labels), convert to sodium in mg: 1g salt = 400mg sodium
            m_salt_mg = re.search(r"(?:salt)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*mg\b", text, re.IGNORECASE)
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
