"""
NutriLens – Dietary Suitability Rules & Dictionaries (Day 6)
Contains canonical allergen synonyms, dietary restriction dictionaries,
and nutrition goal threshold benchmarks.
"""
from typing import Dict, List, Set, Any

SUITABILITY_ENGINE_VERSION = "suitability-rules-v1.0"

# Result Status Constants (Standardized Day 6 Enum)
STATUS_SUITABLE = "Suitable based on available information"
STATUS_CAUTION = "Caution"
STATUS_CONFLICT = "Declared restriction conflict"
STATUS_INSUFFICIENT = "Insufficient information"

STATUS_COLOR_MAP = {
    STATUS_SUITABLE: "emerald",
    STATUS_CAUTION: "amber",
    STATUS_CONFLICT: "rose",
    STATUS_INSUFFICIENT: "slate",
}

# ---------------------------------------------------------------------------
# Allergen Synonyms & Lexicon
# ---------------------------------------------------------------------------
ALLERGEN_SYNONYMS: Dict[str, Set[str]] = {
    "peanuts": {"peanut", "peanuts", "groundnut", "groundnuts", "arachis", "monkey nuts", "mungfali"},
    "tree nuts": {
        "tree nut", "tree nuts", "almond", "almonds", "cashew", "cashews", "walnut", "walnuts",
        "pistachio", "pistachios", "hazelnut", "hazelnuts", "pecan", "pecans", "macadamia",
        "badam", "kaju", "akhrot", "pista",
    },
    "milk": {
        "milk", "dairy", "butter", "ghee", "cheese", "cream", "paneer", "curd", "yogurt",
        "whey", "casein", "caseinate", "lactose", "milk solids", "skimmed milk", "whole milk powder",
    },
    "eggs": {"egg", "eggs", "albumin", "albumen", "egg white", "egg yolk", "lysozyme", "ovalbumin"},
    "wheat": {
        "wheat", "refined wheat flour", "maida", "atta", "whole wheat", "semolina", "suji",
        "rava", "durum wheat", "bulgur", "spelt", "wheat bran", "wheat gluten",
    },
    "gluten": {
        "gluten", "wheat", "barley", "rye", "oats", "spelt", "malt", "malt extract",
        "brewer's yeast", "triticale", "maida", "suji",
    },
    "soy": {"soy", "soya", "soybean", "soybeans", "tofu", "edamame", "soy lecithin", "soy protein", "hydrolyzed soy"},
    "fish": {"fish", "salmon", "tuna", "cod", "anchovy", "anchovies", "tilapia", "gelatin (fish)", "fish sauce"},
    "crustacean shellfish": {
        "shellfish", "crustacean", "shrimp", "shrimps", "prawn", "prawns", "crab", "crabs", "lobster",
    },
    "molluscs": {"mollusc", "molluscs", "squid", "calamari", "oyster", "oysters", "clam", "clams", "mussel"},
    "sesame": {"sesame", "sesame seeds", "tahini", "til", "gingelly"},
    "mustard": {"mustard", "mustard seeds", "sarson", "rai"},
    "celery": {"celery", "celeriac", "celery seeds"},
    "sulphites": {"sulphite", "sulphites", "sulfite", "sulfites", "sulfur dioxide", "sodium metabisulphite", "e220", "e221", "e222", "e223", "e224"},
    "lupin": {"lupin", "lupine", "lupin flour"},
}

# ---------------------------------------------------------------------------
# Dietary Restriction Lexicons
# ---------------------------------------------------------------------------
NON_VEGETARIAN_TERMS: Set[str] = {
    "meat", "chicken", "beef", "pork", "bacon", "mutton", "lamb", "veal", "ham",
    "fish", "salmon", "tuna", "prawn", "shrimp", "crab", "gelatin", "gelatine",
    "animal fat", "lard", "tallow", "animal rennet", "carmine", "cochineal", "e120",
    "isinglass", "bone phosphate", "bone meal",
}

NON_VEGAN_TERMS: Set[str] = NON_VEGETARIAN_TERMS | {
    "milk", "dairy", "butter", "ghee", "cheese", "cream", "curd", "yogurt", "whey",
    "casein", "caseinate", "lactose", "egg", "eggs", "honey", "beeswax", "e901",
    "shellac", "e904", "vitamin d3 (cholecalciferol from lanolin)",
}

NON_JAIN_TERMS: Set[str] = NON_VEGETARIAN_TERMS | {
    "egg", "eggs", "onion", "onions", "garlic", "garlics", "potato", "potatoes",
    "carrot", "carrots", "radish", "radishes", "ginger", "gingers", "beetroot",
    "sweet potato", "turnip", "yam", "shallots", "leeks", "alcohol", "wine", "beer",
}

# Ambiguous ingredients requiring caution for vegetarians/vegans
AMBIGUOUS_VEGETARIAN_TERMS: Set[str] = {
    "mono- and diglycerides of fatty acids", "ins 471", "e471", "emulsifier (471)",
    "glycerol", "glycerin", "ins 422", "e422", "lecithin", "ins 322", "e322",
    "natural flavor", "natural flavoring", "shortening", "rennet",
}

# ---------------------------------------------------------------------------
# Nutrition Goal Thresholds
# ---------------------------------------------------------------------------
GOAL_THRESHOLDS = {
    "low_sugar": {"nutrient": "total_sugar_g", "max_threshold": 10.0, "unit": "g", "label": "Low Sugar"},
    "low_sodium": {"nutrient": "sodium_mg", "max_threshold": 400.0, "unit": "mg", "label": "Low Sodium / Heart Health"},
    "low_saturated_fat": {"nutrient": "saturated_fat_g", "max_threshold": 3.0, "unit": "g", "label": "Low Saturated Fat"},
    "high_protein": {"nutrient": "protein_g", "min_threshold": 8.0, "unit": "g", "label": "High Protein"},
    "high_fibre": {"nutrient": "dietary_fibre_g", "min_threshold": 4.0, "unit": "g", "label": "High Fibre"},
    "keto_friendly": {"nutrient": "carbohydrates_g", "max_threshold": 10.0, "unit": "g", "label": "Keto / Low Carb"},
    "zero_trans_fat": {"nutrient": "trans_fat_g", "max_threshold": 0.0, "unit": "g", "label": "Zero Trans Fat"},
}

SAFETY_DISCLAIMER = (
    "NutriLens suitability assessments are rule-based educational evaluations calculated "
    "from declared package labels. Not detecting an allergen does not prove that a product "
    "is allergen-free. Precautionary ('may contain') statements indicate possible cross-contact. "
    "This platform does not provide medical diagnosis, treatment, or guarantees of safety. "
    "Always consult a qualified healthcare provider for clinical food allergies."
)
