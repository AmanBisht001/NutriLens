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
        # Skip generic section headers or nutrient names (including truncated OCR like 'itional facts', 'ervings')
        if re.search(r"\b(?:facts|nutrition|[a-z]*tional\s+facts|approx|values|[a-z]*ervings?|per\s*(?:pack|[0-9]+)|pack:\s*\d+|ingredients?|allergen|batch|mfg|exp|mrp)\b", line, re.IGNORECASE):
            continue
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
        r"(?:serving\s*size|portion\s*size|per\s*serve|serve\s*size|\bsize)[:\s*]*([0-9]+(?:\.[0-9]+)?\s*(?:g|ml|oz|piece|pieces|biscuit|biscuits|slice|slices))\b",
        r"(?:approx\.\s*)?([0-9]+(?:\.[0-9]+)?\s*(?:g|ml)\s*\([^)]+\))",
        r"(?:per\s+serving\s*\(([^)]+)\))",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            clean_val = m.group(1).strip().rstrip("*").strip()
            return clean_val
    return None


def normalize_ingredient_name(raw_name: str) -> str:
    """
    Normalizes an ingredient token by:
    - Stripping leading bullets, numbering, or symbols (*, -, •, 1., etc.)
    - Cleaning up whitespace inside parentheses and brackets
    - Formatting INS codes cleanly (e.g. 'INS  500  (ii)' -> 'INS 500(ii)')
    - Preserving exact parenthetical context and additive numbers (E319, INS 500ii, etc.)
    """
    cleaned = raw_name.strip()
    # Remove leading bullets, numbers, hyphens, asterisks
    cleaned = re.sub(r"^[\s\-\*\•\d\.\:\)]+", "", cleaned).strip()
    # Clean up whitespace inside parentheses and brackets
    cleaned = re.sub(r"\(\s+", "(", cleaned)
    cleaned = re.sub(r"\s+\)", ")", cleaned)
    cleaned = re.sub(r"\[\s+", "[", cleaned)
    cleaned = re.sub(r"\s+\]", "]", cleaned)
    # Clean up INS codes: e.g. 'INS  500  (ii)' -> 'INS 500(ii)'
    cleaned = re.sub(r"\bINS\s*[-_]?\s*(\d{3,4})\s*\(\s*([a-zA-Z0-9]+)\s*\)", r"INS \1(\2)", cleaned, flags=re.I)
    # Strip terminal punctuation
    cleaned = re.sub(r"[\.,;:_]+$", "", cleaned).strip()
    return cleaned


def split_ingredients_list(raw_ing_text: str) -> List[str]:
    """
    Splits ingredients by commas and semicolons, strictly respecting nested parentheses,
    square brackets, and curly braces (e.g. for additives, INS codes, and sub-ingredients).
    E.g.: 'Refined Wheat Flour, Sugar, Raising Agents [INS 503(ii), INS 500(ii)], Salt'
    -> ['Refined Wheat Flour', 'Sugar', 'Raising Agents [INS 503(ii), INS 500(ii)]', 'Salt']
    """
    if not raw_ing_text or not raw_ing_text.strip():
        return []

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
        elif char == "\n" and depth == 0:
            # Newlines outside parentheses can act as delimiters if followed by a capital letter
            current.append(" ")
        else:
            current.append(char)

    last_token = "".join(current).strip()
    if last_token:
        items.append(last_token)

    # Clean up each item: remove trailing periods, numbers, clean whitespace
    cleaned = []
    for item in items:
        # Strip trailing dot
        norm = normalize_ingredient_name(item)
        # Filter out noise fragments (e.g. single letters or pure numbers)
        if len(norm) >= 2 and not re.match(r"^[0-9\.\%\s]+$", norm):
            cleaned.append(norm)

    return cleaned


def extract_ingredients(text: str, ocr_lines: Optional[List[Any]] = None) -> Tuple[Optional[str], List[str], str, float]:
    """
    Detects ingredients section and returns:
    (raw_ingredients_text, list_of_individual_ingredients, extraction_method, confidence).

    Hierarchical detection:
    - Level 1: Explicit header match (Ingredients:, List of Ingredients, Contains:)
    - Level 2 / 3: Heuristic dense ingredient phrase clustering when header is slightly occluded
    """
    if not text or not text.strip():
        return None, [], "none", 0.0

    # Strip artificial section delimiters like '--- [INGREDIENTS LABEL] ---'
    search_text = re.sub(r"-{2,}\s*\[.*?LABEL\]\s*-{2,}", "", text, flags=re.IGNORECASE).strip()

    # 1. Regex to find starting tag: "INGREDIENTS:", "INGREDIENTS -", "LIST OF INGREDIENTS", "NGREDIENTS", etc.
    start_match = re.search(
        r"\b(?:list\s+of\s+i[ng]{1,2}red[a-z]*|i[ng]{1,2}rediente?s?(?:\s*\(as\s+consumed\))?|i[ng]{1,2}red[a-z]*|samagri)\s*[:\-\.\n\(\s]\s*",
        search_text,
        re.IGNORECASE,
    )

    raw_section: Optional[str] = None
    extraction_method = "ocr_header"
    confidence = 0.92

    if start_match:
        start_idx = start_match.end()
        remaining = search_text[start_idx:]

        # Stop at allergen declaration, nutrition table, manufacturing details, or barcode
        stop_match = re.search(
            r"(?:\n\s*\n|ALLERGEN\s+(?:INFORMATION|ADVICE|DECLARATION)|ALLERGENS?\s*[:\-]|CONTAINS\s+ALLERGENS?|MAY\s+CONTAIN|MFD\s+BY|MANUFACTURED\s+BY|NUTRITION(?:AL)?\s+FACTS|NUTRITION(?:AL)?\s+INFORMATION|STORE\s+IN|NET\s+QUANTITY|NET\s+WT|BATCH\s+NO|BEST\s+BEFORE|FSSAI|LIC\s*NO)",
            remaining,
            re.IGNORECASE,
        )
        if stop_match:
            raw_section = remaining[: stop_match.start()]
        else:
            # If no explicit stop, take up to 8 lines or 800 characters
            lines = remaining.split("\n")
            raw_section = " ".join([l.strip() for l in lines[:8] if l.strip()])
    else:
        # Check alternative: text starting with "Contains: ..." where ingredients are listed directly
        contains_match = re.search(
            r"\b(?:contains)\s*[:\-\n]\s*([a-zA-Z0-9\s,\(\)%\-\._\[\]]{20,})",
            search_text,
            re.IGNORECASE,
        )
        if contains_match and ("," in contains_match.group(1) or ";" in contains_match.group(1)):
            raw_section = contains_match.group(1).split("\n\n")[0].strip()
            extraction_method = "ocr_contains"
            confidence = 0.82
        else:
            # Level 3: Density heuristic - check for line with multiple food-related terms and commas
            food_terms = [
                "flour", "sugar", "salt", "oil", "water", "milk", "wheat", "cocoa", "butter",
                "fat", "emulsifier", "preservative", "lecithin", "starch", "yeast", "spices",
                "flavour", "acid", "gum", "syrup", "extract", "protein", "ins",
            ]
            lines = search_text.split("\n")
            candidate_lines = []
            for line in lines:
                l_lower = line.lower()
                matches = sum(1 for term in food_terms if term in l_lower)
                commas = line.count(",") + line.count(";")
                if (matches >= 2 and commas >= 1) or (matches >= 3):
                    candidate_lines.append(line.strip())

            if candidate_lines:
                raw_section = " ".join(candidate_lines)
                extraction_method = "ocr_density_heuristic"
                confidence = 0.68

    if not raw_section or not raw_section.strip():
        return None, [], "none", 0.0

    raw_section = " ".join(raw_section.split()).strip()
    raw_section = re.sub(r"\.+$", "", raw_section).strip()

    items = split_ingredients_list(raw_section)
    if not items:
        return None, [], "none", 0.0

    return (raw_section, items, extraction_method, confidence)


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


def _get_line_info(l: Any) -> Optional[Dict[str, Any]]:
    """Helper to extract text and geometry from an OCRLine or dict."""
    if isinstance(l, dict):
        text = str(l.get("text", "")).strip()
        box = l.get("box")
        conf = float(l.get("confidence", 0.0))
    else:
        text = str(getattr(l, "text", "")).strip()
        box = getattr(l, "box", None)
        conf = float(getattr(l, "confidence", 0.0))

    if not text or not box or len(box) < 4:
        return None
    try:
        xmin = min(p[0] for p in box)
        xmax = max(p[0] for p in box)
        ymin = min(p[1] for p in box)
        ymax = max(p[1] for p in box)
        xc = (xmin + xmax) / 2.0
        yc = (ymin + ymax) / 2.0
        h_box = ymax - ymin
        return {
            "text": text,
            "xmin": xmin, "xmax": xmax,
            "ymin": ymin, "ymax": ymax,
            "xc": xc, "yc": yc, "h": h_box,
            "conf": conf,
        }
    except Exception:
        return None


def extract_nutrition_facts_spatial(
    ocr_lines: List[Any],
) -> Tuple[Dict[str, Optional[float]], Dict[str, Optional[float]]]:
    """
    2D Spatial Table Extractor.
    Extracts nutrient values from multi-column nutrition facts tables using
    bounding-box geometric relationships and camera tilt estimation.
    Returns: (per_100_facts, per_serving_facts)
    """
    per_100_facts: Dict[str, Optional[float]] = {
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
    per_serving_facts: Dict[str, Optional[float]] = {k: None for k in per_100_facts}

    items = []
    for l in ocr_lines:
        info = _get_line_info(l)
        if info:
            items.append(info)

    if len(items) < 2:
        return per_100_facts, per_serving_facts

    # Estimate median camera tilt slope across horizontal text pairs
    slopes = []
    for i in range(len(items)):
        for j in range(len(items)):
            if i == j:
                continue
            dx = items[j]['xc'] - items[i]['xc']
            dy = items[j]['yc'] - items[i]['yc']
            if 40 <= dx <= 250 and abs(dy) <= 30:
                slopes.append(dy / dx)

    tilt_slope = 0.0
    if slopes:
        slopes.sort()
        tilt_slope = slopes[len(slopes) // 2]
        tilt_slope = max(-0.3, min(0.3, tilt_slope))

    targets = [
        ("energy_kcal", [r"(?:energy|calories|\(kcal\)|kcal\b)"]),
        ("protein_g", [r"(?:protein|crude\s+protein|\bN\s*\(g\)|\btein\s*\(g\))"]),
        ("carbohydrates_g", [r"(?:carbohydrate|carbs|hydrates?\s*\(g\)|[a-z]*ydrate)"]),
        ("total_sugar_g", [r"(?:total\s+sugars?|sugars?\s*\(g\)|(?<!added\s)(?<!\.d)sugars?)"]),
        ("added_sugar_g", [r"(?:added\s+sugars?|\.dsugars?|ed\s*sugars?)"]),
        ("dietary_fibre_g", [r"(?:dietary\s+fib|fibre?\s*\(g\)|fib(?:re|er)|ary\s+fibre)"]),
        ("total_fat_g", [r"(?:total\s+fat|crude\s+fat|\blfat\s*\(g\)|\bfat\s*\(g\))"]),
        ("saturated_fat_g", [r"(?:saturated\s+fat|urated\s+fat|sat\s+fat)"]),
        ("trans_fat_g", [r"(?:trans\s+fat|ansfat)"]),
        ("cholesterol_mg", [r"(?:cholesterol|olesterol)"]),
        ("salt_g", [r"(?:total\s+salt|alsalt|salt\b)"]),
        ("sodium_mg", [r"(?:sodium|dium\s*\(mg\))"]),
    ]

    extracted_salt_100 = None
    extracted_salt_serv = None

    for key, patterns in targets:
        matched_label = None
        for item in items:
            if key == "total_fat_g" and any(re.search(r"saturated|urated|trans|ans", item['text'], re.I) for _ in [1]):
                continue
            if key == "total_sugar_g" and any(re.search(r"added|\.d|ed\s*sugar", item['text'], re.I) for _ in [1]):
                continue
            if key == "salt_g" and any(re.search(r"dium", item['text'], re.I) for _ in [1]):
                continue

            for pat in patterns:
                if re.search(pat, item['text'], re.I):
                    matched_label = item
                    break
            if matched_label:
                break

        if not matched_label:
            continue

        candidates = []
        for item in items:
            if item == matched_label:
                continue
            if item['xmin'] < matched_label['xmax'] - 10:
                continue

            expected_y = matched_label['yc'] + tilt_slope * (item['xc'] - matched_label['xc'])
            v_dist = abs(item['yc'] - expected_y)

            if v_dist <= 14.0:
                m = re.search(r"^[<>]?([0-9]+(?:[\.,][0-9]+)?)\.?$", item['text'])
                if m:
                    val = float(m.group(1).replace(",", "."))
                    candidates.append((item['xmin'], val, v_dist))

        candidates.sort(key=lambda c: c[0])
        if candidates:
            c1_val = candidates[0][1]
            c2_val = candidates[1][1] if len(candidates) > 1 else None
            if key == "salt_g":
                extracted_salt_100 = c1_val
                extracted_salt_serv = c2_val
            elif key != "cholesterol_mg":
                per_100_facts[key] = c1_val
                per_serving_facts[key] = c2_val

    # Convert salt to sodium if sodium was not directly detected
    if per_100_facts.get("sodium_mg") is None and extracted_salt_100 is not None:
        if extracted_salt_100 <= 15.0:
            per_100_facts["sodium_mg"] = round(extracted_salt_100 * 400.0, 2)
        else:
            per_100_facts["sodium_mg"] = round(extracted_salt_100, 2)

    if per_serving_facts.get("sodium_mg") is None and extracted_salt_serv is not None:
        if extracted_salt_serv <= 15.0:
            per_serving_facts["sodium_mg"] = round(extracted_salt_serv * 400.0, 2)
        else:
            per_serving_facts["sodium_mg"] = round(extracted_salt_serv, 2)

    return per_100_facts, per_serving_facts


def extract_nutrition_facts(text: str, ocr_lines: Optional[List[Any]] = None) -> Dict[str, Optional[float]]:
    """
    Extracts key macronutrients from nutrition facts text.
    Handles:
    - 2D spatial table alignment when ocr_lines are available
    - Single-line (e.g. 'Energy: 460 kcal', 'Energy (kcal) 554')
    - Multi-line table rows (e.g. 'Energy (kcal)\\n554')
    - Units inside parentheses or brackets in label names (e.g. 'Total Fat (g)', 'Sodium [mg]')
    - Multi-column tables (e.g. 'Energy (kcal) 554 111' -> extracts 554 per 100g)
    - Indian packaging misreads (e.g. 'ydrate', 'ated Fat', 'ans Fat', 'JedSugars', 'N(g)')
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

    # 0. Spatial table extraction (highest fidelity for multi-column grids)
    if ocr_lines:
        spatial_100, _ = extract_nutrition_facts_spatial(ocr_lines)
        for k, v in spatial_100.items():
            if v is not None:
                facts[k] = v

    # 1. Energy / Calories (kcal or kJ/kcal split e.g. '2110 kJ / 504 kcal')
    if facts["energy_kcal"] is None:
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
                r"(?:^|\n)[ \t]*(?:\(kcal\)|kcal)[ \t]+([0-9]+(?:[\.,][0-9]+)?)",
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
    if facts["saturated_fat_g"] is None:
        facts["saturated_fat_g"] = _extract_number(
            [
                r"(?:saturated\s+fat|saturated\s+fatty\s+acids|of\s+which\s+saturates|saturates|sat\s+fat|[a-z]*urated\s+fat|[a-z]*ated\s+fat)(?:\s*[\(\[]\s*g\s*[\)\]]?)?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
                r"(?:saturated\s+fat|saturated\s+fatty\s+acids|of\s+which\s+saturates|saturates|[a-z]*urated\s+fat|[a-z]*ated\s+fat)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
            ],
            text,
        )

    # 3. Trans Fat
    if facts["trans_fat_g"] is None:
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
    if facts["total_fat_g"] is None:
        facts["total_fat_g"] = _extract_number(
            [
                # Specific "Total Fat" label — highest priority
                r"(?:total\s+fat|crude\s+fat|[a-z]?l\s*fat)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
                # Truncated OCR: line containing only 'It', 'it', 'Fat', or similar followed by value on next line
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
    if facts["carbohydrates_g"] is None:
        facts["carbohydrates_g"] = _extract_number(
            [
                r"(?:carbohydrates?|total\s+carbohydrates?|total\s+carbs|carbs|[a-z]*(?:hydrate|ydrate)s?)(?:\s*[\(\[]\s*g\s*[\)\]]?)?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
                r"(?:carbohydrate|carbohydrates|total\s+carbohydrates|total\s+carbs|carbs|[a-z]*(?:hydrate|ydrate)s?)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
            ],
            text,
        )

    # 6. Added Sugars (checked before Total Sugars to prevent Added Sugars from being captured as Total)
    if facts["added_sugar_g"] is None:
        facts["added_sugar_g"] = _extract_number(
            [
                r"(?:added\s*sugars?|of\s+which\s+added\s+sugars?|[a-z]*ed\s*sugars?|\.dsugars?|[a-z]?dsugars?)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
                r"(?:added\s*sugars?|[a-z]*ed\s*sugars?|\.dsugars?|[a-z]?dsugars?)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
            ],
            text,
        )

    # 7. Total Sugars / 'of which sugars'
    if facts["total_sugar_g"] is None:
        facts["total_sugar_g"] = _extract_number(
            [
                r"(?:total\s+sugars?|of\s+which\s+sugars?|[a-z]?lsugars?)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
                r"(?<!added\s)(?<!jed\s)(?<!\.d)(?<![a-z]ed\s)\bsugars?(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
                r"(?:total\s+sugars?|of\s+which\s+sugars?|[a-z]?lsugars?|(?<!added\s)(?<!jed\s)(?<!\.d)(?<![a-z]ed\s)\bsugars?)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
            ],
            text,
        )

    # 8. Dietary Fibre / Fibre / Fiber
    if facts["dietary_fibre_g"] is None:
        facts["dietary_fibre_g"] = _extract_number(
            [
                r"(?:dietary\s+fib(?:re|er)|crude\s+fib(?:re|er)|fib(?:re|er)|[a-z]*ary\s*fib(?:re|er)|[a-z]*fib(?:re|er))(?:\s*[\(\[]\s*g\s*[\)\]]?)?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
                r"(?:dietary\s+fib(?:re|er)|fib(?:re|er)|[a-z]*ary\s*fib(?:re|er)|[a-z]*fib(?:re|er))[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
            ],
            text,
        )

    # 9. Protein
    if facts["protein_g"] is None:
        facts["protein_g"] = _extract_number(
            [
                r"(?:protein|crude\s+protein|[a-z]*tein|\bN)(?:\s*[\(\[]\s*g\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|go\b|\s)",
                r"(?:protein|crude\s+protein|[a-z]*tein)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|go\b|\s)",
            ],
            text,
        )
    # Positional check: in standard Indian nutrition tables, Protein is the row between Energy (kcal) and Carbohydrate
    if facts["protein_g"] is None:
        table_protein = re.search(r"kcal[\s\S]*?(?<!size:)(?<!size\s)\b([0-9]+(?:\.[0-9]+)?)\s*g\b[\s\S]*?[a-z]*(?:hydrate|ydrate)", text, re.IGNORECASE)
        if table_protein:
            try:
                facts["protein_g"] = float(table_protein.group(1).replace(",", "."))
            except ValueError:
                pass

    # 10. Sodium (mg or g) or Salt (g converted: 1g salt ≈ 400mg sodium)
    if facts["sodium_mg"] is None:
        sodium_val = _extract_number(
            [
                r"(?:sodium|[a-z]*dium)(?:\s*[\(\[]\s*(?:mg|g|mq)\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:mg|mq)?",
                r"(?:sodium|[a-z]*dium)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:mg|mq)?",
            ],
            text,
        )
        if sodium_val is not None:
            m_g = re.search(r"(?:sodium|[a-z]*dium)(?:\s*[\(\[]\s*g\s*[\)\]]|[\s:\-–—\t]*[0-9]+(?:[\.,][0-9]+)?\s*g\b)", text, re.IGNORECASE)
            if m_g:
                sodium_val = sodium_val * 1000.0
            facts["sodium_mg"] = sodium_val
        else:
            mg_match = re.search(r"\b([0-9]+(?:\.[0-9]+)?)\s*(?:mg|mq)\b", text, re.IGNORECASE)
            if mg_match:
                try:
                    facts["sodium_mg"] = float(mg_match.group(1).replace(",", "."))
                except ValueError:
                    pass
            if facts["sodium_mg"] is None:
                salt_val = _extract_number(
                    [
                        r"(?:total\s+salt|salt|[a-z]*salt)(?:\s*[\(\[]\s*(?:g|mg)\s*[\)\]])?[\s:\-–—\t]*\n?[\s:\-–—\t]*([0-9]+(?:[\.,][0-9]+)?)\s*(?:g\b|mg\b)?",
                        r"(?:total\s+salt|salt|[a-z]*salt)[\s:\-]+([0-9]+(?:\.[0-9]+)?)\s*(?:g\b|mg\b)?",
                    ],
                    text,
                )
                if salt_val is not None:
                    m_salt_mg = re.search(r"(?:total\s+salt|salt|[a-z]*salt)(?:\s*[\(\[]\s*mg\s*[\)\]]|[\s:\-–—\t]*[0-9]+(?:\.[0-9]+)?\s*mg\b)", text, re.IGNORECASE)
                    if m_salt_mg:
                        facts["sodium_mg"] = round(salt_val * 0.4, 2)
                    elif salt_val <= 15.0:
                        facts["sodium_mg"] = round(salt_val * 400.0, 2)
                    else:
                        facts["sodium_mg"] = round(salt_val, 2)

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


def extract_uncertain_allergens(text: str) -> List[str]:
    """Identifies potential hidden allergen sources with ambiguous declarations."""
    uncertain: List[str] = []
    uncertain_patterns = [
        (r"\b(?:lecithin)\b(?!.*\b(?:soy|sunflower|egg)\b)", "Lecithin (source unverified)"),
        (r"\b(?:modified\s+starch)\b", "Modified Starch (wheat vs corn source unspecified)"),
        (r"\b(?:gluten)\b", "Gluten source declared"),
        (r"\b(?:casein|whey)\b", "Milk derivative (Casein/Whey)"),
    ]
    for pat, label in uncertain_patterns:
        if re.search(pat, text, re.IGNORECASE):
            uncertain.append(label)
    return uncertain


def extract_structured_label_info(
    raw_ocr_text: str,
    ocr_confidence: float = 0.0,
    ocr_engine: str = "fallback",
    ocr_lines: Optional[List[Any]] = None,
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
    if not serving_size:
        # Check column header declarations like 'PER 50g' (avoiding 'PER 100g')
        m_serv = re.search(r"\bper\s*([1-9][0-9]*(?:\.[0-9]+)?\s*(?:g|ml))\b", cleaned, re.IGNORECASE)
        if m_serv and "100" not in m_serv.group(1):
            serving_size = m_serv.group(1).strip()

    raw_ingredients_text, ingredients_list, ing_method, ing_conf = extract_ingredients(cleaned, ocr_lines=ocr_lines)
    nutrition_facts = extract_nutrition_facts(cleaned, ocr_lines=ocr_lines)

    per_serving_facts: Dict[str, Optional[float]] = {}
    if ocr_lines:
        _, per_serving_facts = extract_nutrition_facts_spatial(ocr_lines)

    declared_allergens, precautionary_allergens = extract_allergens(cleaned)
    uncertain_allergens = extract_uncertain_allergens(cleaned)

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
        "ingredient_extraction_method": ing_method,
        "ingredient_extraction_confidence": ing_conf,
        "nutrition_facts": nutrition_facts,
        "per_serving_nutrition_facts": per_serving_facts,
        "declared_allergens": declared_allergens,
        "precautionary_allergens": precautionary_allergens,
        "uncertain_allergens": uncertain_allergens,
        "ocr_confidence": round(ocr_confidence, 4),
        "ocr_engine": ocr_engine,
        "uncertainty_flags": uncertainty_flags,
        "is_verified": False,  # Never treat raw/extracted OCR as verified
    }
