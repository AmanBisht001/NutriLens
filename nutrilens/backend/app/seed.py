"""
NutriLens – Database Seed Script (Day 3)
========================================
Populates the development database with:
  • 8 canonical allergens
  • 30 ingredient knowledge-base entries
  • 10 clearly-labelled DEMO products with nutrition facts, ingredient links, and allergen links

IMPORTANT: All nutritional values are ILLUSTRATIVE / DEMONSTRATION DATA.
They do NOT represent real-world verified product nutrition facts.
Products are clearly marked with is_demo_data=True and verification_note to
prevent confusion with verified records.

Usage:
    cd nutrilens/backend
    .\\venv\\Scripts\\python.exe -m app.seed
"""
import sys
import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.core.security import get_password_hash
from app.models.user import User, UserProfile
from app.models.scoring_rules import ScoringRuleVersion
from app.api.v1.endpoints.admin import get_default_scoring_rules_dict
from app.scoring_engine.rules import SCORING_RULE_VERSION

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

DEMO_NOTE = "DEMO DATA – illustrative values only, not verified nutritional facts"


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Seed data definitions
# ---------------------------------------------------------------------------

ALLERGEN_DEFS = [
    {"name": "Peanuts",           "code": "FDA_01", "description": "Groundnut/peanut allergy – one of the Big-9 allergens regulated by FDA."},
    {"name": "Tree Nuts",         "code": "FDA_02", "description": "Almonds, cashews, walnuts, pecans, etc. Big-9 allergen."},
    {"name": "Milk / Dairy",      "code": "FDA_03", "description": "Cow's milk proteins including casein and whey. Big-9 allergen."},
    {"name": "Gluten / Wheat",    "code": "FDA_04", "description": "Wheat, rye, barley and related grains containing gluten. Big-9 allergen."},
    {"name": "Eggs",              "code": "FDA_05", "description": "Egg proteins from chicken and other poultry. Big-9 allergen."},
    {"name": "Soy",               "code": "FDA_06", "description": "Soybean proteins. Big-9 allergen."},
    {"name": "Fish",              "code": "FDA_07", "description": "Finfish including salmon, tuna, cod. Big-9 allergen."},
    {"name": "Crustacean Shellfish", "code": "FDA_08", "description": "Shrimp, crab, lobster, prawns. Big-9 allergen."},
    {"name": "Sesame",            "code": "FDA_09", "description": "Sesame seeds and sesame oil. Big-9 allergen added 2023."},
]

INGREDIENT_DEFS = [
    # Preservatives
    {"name": "Sodium Benzoate",        "normalized_name": "sodium benzoate",        "category": "preservative", "ins_number": "E211", "concern_level": "moderate", "purpose": "Prevents microbial growth in acidic foods", "description": "A common preservative used in beverages and condiments. Some studies associate it with hyperactivity in children when combined with certain food colours.", "is_common_allergen": False},
    {"name": "Potassium Sorbate",      "normalized_name": "potassium sorbate",      "category": "preservative", "ins_number": "E202", "concern_level": "safe",     "purpose": "Inhibits mould and yeast growth",             "description": "Widely used food preservative considered safe at approved levels.", "is_common_allergen": False},
    {"name": "BHA (Butylated Hydroxyanisole)", "normalized_name": "bha butylated hydroxyanisole", "category": "antioxidant", "ins_number": "E320", "concern_level": "high", "purpose": "Prevents fat oxidation and rancidity", "description": "Synthetic antioxidant listed as possibly carcinogenic by IARC. Permitted at trace levels in many countries.", "is_common_allergen": False},
    {"name": "TBHQ",                   "normalized_name": "tbhq tertiary butylhydroquinone", "category": "antioxidant", "ins_number": "E319", "concern_level": "moderate", "purpose": "Extends shelf life of fats and oils", "description": "Synthetic antioxidant. Banned in Japan and other countries; permitted at ≤0.02% in the US.", "is_common_allergen": False},

    # Emulsifiers
    {"name": "Soy Lecithin",           "normalized_name": "soy lecithin",           "category": "emulsifier",   "ins_number": "E322", "concern_level": "safe",     "purpose": "Blends water and fat phases in processed foods", "description": "Derived from soybeans. Contains trace soy protein. Generally well-tolerated but relevant for soy allergies.", "is_common_allergen": True},
    {"name": "Mono- and Diglycerides", "normalized_name": "mono and diglycerides",  "category": "emulsifier",   "ins_number": "E471", "concern_level": "safe",     "purpose": "Improves texture and extends shelf life",        "description": "Derived from fats (animal or vegetable). Widely used in baked goods and margarine.", "is_common_allergen": False},
    {"name": "Polysorbate 80",         "normalized_name": "polysorbate 80",         "category": "emulsifier",   "ins_number": "E433", "concern_level": "moderate", "purpose": "Prevents oil separation and improves texture",   "description": "Synthetic emulsifier associated with gut microbiome disruption in some animal studies at high doses.", "is_common_allergen": False},
    {"name": "DATEM",                  "normalized_name": "datem diacetyl tartaric acid esters of mono and diglycerides", "category": "emulsifier", "ins_number": "E472e", "concern_level": "safe", "purpose": "Improves dough strength and loaf volume in bread", "description": "Common bread-making additive. Considered safe at approved levels.", "is_common_allergen": False},

    # Sweeteners
    {"name": "High Fructose Corn Syrup", "normalized_name": "high fructose corn syrup", "category": "sweetener", "ins_number": None, "concern_level": "moderate", "purpose": "Sweetener and humectant derived from corn starch", "description": "Linked to obesity, insulin resistance, and metabolic syndrome in epidemiological studies when consumed in excess.", "is_common_allergen": False},
    {"name": "Aspartame",              "normalized_name": "aspartame",              "category": "sweetener",   "ins_number": "E951", "concern_level": "moderate", "purpose": "Low-calorie artificial sweetener", "description": "Classified as 'possibly carcinogenic to humans' (Group 2B) by IARC in 2023. Acceptable daily intake set by EFSA and FDA remains in place.", "is_common_allergen": False},
    {"name": "Sucralose",              "normalized_name": "sucralose",              "category": "sweetener",   "ins_number": "E955", "concern_level": "safe",     "purpose": "No-calorie sweetener approximately 600× sweeter than sugar", "description": "Chlorinated derivative of sucrose. Passes through the body largely unchanged.", "is_common_allergen": False},
    {"name": "Stevia Extract",         "normalized_name": "stevia extract rebaudioside a", "category": "sweetener", "ins_number": "E960", "concern_level": "safe", "purpose": "Plant-derived zero-calorie sweetener", "description": "Extracted from Stevia rebaudiana leaves. Approved by FDA as GRAS.", "is_common_allergen": False},

    # Colours
    {"name": "Sunset Yellow FCF",      "normalized_name": "sunset yellow fcf",      "category": "colour",       "ins_number": "E110", "concern_level": "moderate", "purpose": "Orange-yellow food colouring", "description": "Part of the Southampton Six colours associated with increased hyperactivity in children. Requires warning label in EU.", "is_common_allergen": False},
    {"name": "Tartrazine",             "normalized_name": "tartrazine",             "category": "colour",       "ins_number": "E102", "concern_level": "moderate", "purpose": "Yellow food colouring", "description": "Azo dye. Southampton Six. Can trigger reactions in aspirin-sensitive individuals. Warning label required in EU.", "is_common_allergen": False},
    {"name": "Caramel Colour Class IV","normalized_name": "caramel colour class iv", "category": "colour",      "ins_number": "E150d","concern_level": "moderate", "purpose": "Brown colouring for colas and sauces", "description": "Produced with ammonium compounds. Contains 4-MEI, a compound linked to cancer in animal studies at high doses.", "is_common_allergen": False},
    {"name": "Beta-Carotene",          "normalized_name": "beta carotene",          "category": "colour",       "ins_number": "E160a","concern_level": "safe",     "purpose": "Natural orange colouring and provitamin A source", "description": "Natural pigment from carrots and other vegetables. Converted to vitamin A in the body.", "is_common_allergen": False},

    # Flavour enhancers
    {"name": "Monosodium Glutamate",   "normalized_name": "monosodium glutamate",   "category": "flavour_enhancer", "ins_number": "E621", "concern_level": "safe",  "purpose": "Enhances umami (savoury) taste", "description": "Salt form of glutamic acid, an amino acid naturally present in tomatoes, cheese, and meat. FDA classifies as GRAS.", "is_common_allergen": False},
    {"name": "Disodium Inosinate",     "normalized_name": "disodium inosinate",     "category": "flavour_enhancer", "ins_number": "E631", "concern_level": "safe",  "purpose": "Synergistic flavour enhancer used with MSG", "description": "Often used with MSG and disodium guanylate. Derived from meat or fish.", "is_common_allergen": False},

    # Thickeners / Stabilisers
    {"name": "Carrageenan",            "normalized_name": "carrageenan",            "category": "thickener",    "ins_number": "E407", "concern_level": "moderate", "purpose": "Thickens and gels dairy products and plant milks", "description": "Extracted from red seaweed. Degraded (poligeenan) form is carcinogenic; food-grade carrageenan safety is debated.", "is_common_allergen": False},
    {"name": "Xanthan Gum",            "normalized_name": "xanthan gum",            "category": "thickener",    "ins_number": "E415", "concern_level": "safe",     "purpose": "Stabilises and thickens sauces, dressings, gluten-free products", "description": "Produced by bacterial fermentation of glucose. GRAS status. Can be derived from wheat or soy.", "is_common_allergen": False},
    {"name": "Guar Gum",               "normalized_name": "guar gum",               "category": "thickener",    "ins_number": "E412", "concern_level": "safe",     "purpose": "Thickener and fibre supplement", "description": "Extracted from guar beans. High fibre content. Can cause bloating in sensitive individuals.", "is_common_allergen": False},
    {"name": "Carboxymethyl Cellulose","normalized_name": "carboxymethyl cellulose", "category": "thickener",   "ins_number": "E466", "concern_level": "moderate", "purpose": "Prevents ice crystal formation; stabiliser in ice cream", "description": "Synthetic fibre derived from cellulose. Some research suggests disruption of gut microbiome at high levels.", "is_common_allergen": False},

    # Acids
    {"name": "Citric Acid",            "normalized_name": "citric acid",            "category": "acid",         "ins_number": "E330", "concern_level": "safe",     "purpose": "Flavour acidulant and preservative", "description": "Naturally occurring acid found in citrus fruits. Also produced by microbial fermentation (Aspergillus niger).", "is_common_allergen": False},
    {"name": "Phosphoric Acid",        "normalized_name": "phosphoric acid",        "category": "acid",         "ins_number": "E338", "concern_level": "moderate", "purpose": "Provides sharp/tangy flavour in colas", "description": "Associated with reduced bone density in high dietary intakes. Used as an acidulant in cola beverages.", "is_common_allergen": False},

    # Leavening
    {"name": "Sodium Bicarbonate",     "normalized_name": "sodium bicarbonate",     "category": "leavening",    "ins_number": "E500", "concern_level": "safe",     "purpose": "Leavening agent in baked goods", "description": "Common baking soda. Reacts with acids to produce CO2 for lift. GRAS.", "is_common_allergen": False},
    {"name": "Sodium Aluminium Phosphate", "normalized_name": "sodium aluminium phosphate", "category": "leavening", "ins_number": "E541", "concern_level": "moderate", "purpose": "Slow-acting leavening acid for baked goods", "description": "Aluminium-containing leavening agent. Aluminium accumulation is associated with neurotoxicity at high exposure.", "is_common_allergen": False},

    # Natural ingredients
    {"name": "Palm Oil",               "normalized_name": "palm oil",               "category": "fat",          "ins_number": None,   "concern_level": "moderate", "purpose": "Cooking fat and texture agent", "description": "High in saturated fat. Environmental concerns around deforestation and biodiversity loss in production regions.", "is_common_allergen": False},
    {"name": "Refined Wheat Flour",    "normalized_name": "refined wheat flour",    "category": "grain",        "ins_number": None,   "concern_level": "safe",     "purpose": "Primary structure ingredient in baked goods", "description": "Contains gluten. Refined flour has lower fibre content compared to wholegrain alternatives.", "is_common_allergen": True},
    {"name": "Skimmed Milk Powder",    "normalized_name": "skimmed milk powder",    "category": "dairy",        "ins_number": None,   "concern_level": "safe",     "purpose": "Dairy protein and flavour source", "description": "Contains milk proteins (casein, whey) and lactose. Relevant for dairy allergies and lactose intolerance.", "is_common_allergen": True},
    {"name": "Cocoa Powder",           "normalized_name": "cocoa powder",           "category": "flavour",      "ins_number": None,   "concern_level": "safe",     "purpose": "Chocolate flavour and colour source", "description": "Ground cacao beans. Contains theobromine and caffeine. May be processed on shared equipment with nuts.", "is_common_allergen": False},
    {"name": "Sugar (Sucrose)",        "normalized_name": "sugar sucrose",          "category": "sweetener",    "ins_number": None,   "concern_level": "safe",     "purpose": "Sweetener and preservative", "description": "Common table sugar. High intake linked to dental caries, obesity, and metabolic disease.", "is_common_allergen": False},
    {"name": "Salt (Sodium Chloride)", "normalized_name": "salt sodium chloride",   "category": "seasoning",    "ins_number": None,   "concern_level": "safe",     "purpose": "Flavour enhancer and preservative", "description": "Essential mineral. Excess dietary sodium associated with hypertension and cardiovascular risk.", "is_common_allergen": False},
]

# ---------------------------------------------------------------------------
# Demo products
# Each product has: core fields, nutrition_facts, ingredient list, allergen list
# ---------------------------------------------------------------------------

PRODUCT_DEFS = [
    {
        "name": "NutriDemo Choco Wheat Biscuits",
        "brand": "NutriDemo",
        "category": "Biscuits & Cookies",
        "barcode": "5901234123457",
        "serving_size": "30g (3 biscuits)",
        "raw_ingredients_text": "Refined Wheat Flour, Sugar (Sucrose), Palm Oil, Cocoa Powder, Skimmed Milk Powder, Sodium Bicarbonate, Salt (Sodium Chloride), Soy Lecithin, Vanilla Flavour",
        "nutrition": {"energy_kcal": 480, "total_fat_g": 20, "saturated_fat_g": 9, "trans_fat_g": 0, "carbohydrates_g": 65, "total_sugar_g": 28, "added_sugar_g": 25, "dietary_fibre_g": 2.5, "protein_g": 7, "sodium_mg": 310},
        "ingredients": ["refined wheat flour", "sugar sucrose", "palm oil", "cocoa powder", "skimmed milk powder", "sodium bicarbonate", "salt sodium chloride", "soy lecithin"],
        "allergens": [("Gluten / Wheat", "declared"), ("Milk / Dairy", "declared"), ("Soy", "declared")],
    },
    {
        "name": "NutriDemo Lemon Fizz Drink",
        "brand": "NutriDemo",
        "category": "Beverages",
        "barcode": "5901234123458",
        "serving_size": "250ml",
        "raw_ingredients_text": "Carbonated Water, High Fructose Corn Syrup, Citric Acid, Sodium Benzoate, Tartrazine (E102), Natural Lemon Flavour",
        "nutrition": {"energy_kcal": 108, "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0, "carbohydrates_g": 27, "total_sugar_g": 27, "added_sugar_g": 27, "dietary_fibre_g": 0, "protein_g": 0, "sodium_mg": 55},
        "ingredients": ["high fructose corn syrup", "citric acid", "sodium benzoate", "tartrazine"],
        "allergens": [],
    },
    {
        "name": "NutriDemo Classic Cola",
        "brand": "NutriDemo",
        "category": "Beverages",
        "barcode": "5901234123459",
        "serving_size": "355ml",
        "raw_ingredients_text": "Carbonated Water, High Fructose Corn Syrup, Caramel Colour Class IV, Phosphoric Acid, Natural Flavours, Caffeine",
        "nutrition": {"energy_kcal": 140, "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0, "carbohydrates_g": 39, "total_sugar_g": 39, "added_sugar_g": 39, "dietary_fibre_g": 0, "protein_g": 0, "sodium_mg": 45},
        "ingredients": ["high fructose corn syrup", "caramel colour class iv", "phosphoric acid"],
        "allergens": [],
    },
    {
        "name": "NutriDemo Peanut Butter Crunch Bar",
        "brand": "NutriDemo",
        "category": "Snack Bars",
        "barcode": "5901234123460",
        "serving_size": "45g (1 bar)",
        "raw_ingredients_text": "Peanuts, Sugar (Sucrose), Palm Oil, Refined Wheat Flour, Salt (Sodium Chloride), Soy Lecithin, BHA (E320), TBHQ (E319)",
        "nutrition": {"energy_kcal": 530, "total_fat_g": 32, "saturated_fat_g": 8, "trans_fat_g": 0.2, "carbohydrates_g": 48, "total_sugar_g": 20, "added_sugar_g": 18, "dietary_fibre_g": 3, "protein_g": 12, "sodium_mg": 280},
        "ingredients": ["sugar sucrose", "palm oil", "refined wheat flour", "salt sodium chloride", "soy lecithin", "bha butylated hydroxyanisole", "tbhq tertiary butylhydroquinone"],
        "allergens": [("Peanuts", "declared"), ("Gluten / Wheat", "declared"), ("Soy", "declared")],
    },
    {
        "name": "NutriDemo Vanilla Ice Cream",
        "brand": "NutriDemo",
        "category": "Frozen Desserts",
        "barcode": "5901234123461",
        "serving_size": "100ml",
        "raw_ingredients_text": "Skimmed Milk, Sugar (Sucrose), Cream, Skimmed Milk Powder, Mono- and Diglycerides, Carboxymethyl Cellulose, Polysorbate 80, Natural Vanilla Flavour",
        "nutrition": {"energy_kcal": 195, "total_fat_g": 10, "saturated_fat_g": 6.5, "trans_fat_g": 0.1, "carbohydrates_g": 23, "total_sugar_g": 20, "added_sugar_g": 18, "dietary_fibre_g": 0, "protein_g": 3.5, "sodium_mg": 65},
        "ingredients": ["sugar sucrose", "skimmed milk powder", "mono and diglycerides", "carboxymethyl cellulose", "polysorbate 80"],
        "allergens": [("Milk / Dairy", "declared")],
    },
    {
        "name": "NutriDemo Whole Wheat Bread",
        "brand": "NutriDemo",
        "category": "Bread & Bakery",
        "barcode": "5901234123462",
        "serving_size": "30g (1 slice)",
        "raw_ingredients_text": "Refined Wheat Flour, Water, Yeast, Sugar (Sucrose), Salt (Sodium Chloride), Soy Lecithin, DATEM, Potassium Sorbate",
        "nutrition": {"energy_kcal": 265, "total_fat_g": 3, "saturated_fat_g": 0.5, "trans_fat_g": 0, "carbohydrates_g": 50, "total_sugar_g": 5, "added_sugar_g": 3, "dietary_fibre_g": 3, "protein_g": 9, "sodium_mg": 490},
        "ingredients": ["refined wheat flour", "sugar sucrose", "salt sodium chloride", "soy lecithin", "datem diacetyl tartaric acid esters of mono and diglycerides", "potassium sorbate"],
        "allergens": [("Gluten / Wheat", "declared"), ("Soy", "precautionary")],
    },
    {
        "name": "NutriDemo Diet Lemon Tea",
        "brand": "NutriDemo",
        "category": "Beverages",
        "barcode": "5901234123463",
        "serving_size": "250ml",
        "raw_ingredients_text": "Water, Tea Extract, Citric Acid, Aspartame (E951), Acesulfame K, Natural Lemon Flavour, Ascorbic Acid (Vitamin C)",
        "nutrition": {"energy_kcal": 2, "total_fat_g": 0, "saturated_fat_g": 0, "trans_fat_g": 0, "carbohydrates_g": 0.5, "total_sugar_g": 0, "added_sugar_g": 0, "dietary_fibre_g": 0, "protein_g": 0, "sodium_mg": 20},
        "ingredients": ["citric acid", "aspartame"],
        "allergens": [],
    },
    {
        "name": "NutriDemo Oat & Honey Granola",
        "brand": "NutriDemo",
        "category": "Breakfast Cereals",
        "barcode": "5901234123464",
        "serving_size": "45g",
        "raw_ingredients_text": "Rolled Oats, Honey, Sugar (Sucrose), Palm Oil, Almonds, Salt (Sodium Chloride), Natural Flavour",
        "nutrition": {"energy_kcal": 450, "total_fat_g": 15, "saturated_fat_g": 3, "trans_fat_g": 0, "carbohydrates_g": 68, "total_sugar_g": 22, "added_sugar_g": 15, "dietary_fibre_g": 7, "protein_g": 10, "sodium_mg": 160},
        "ingredients": ["sugar sucrose", "palm oil", "salt sodium chloride"],
        "allergens": [("Tree Nuts", "declared"), ("Gluten / Wheat", "precautionary")],
    },
    {
        "name": "NutriDemo Stevia Zero Yoghurt",
        "brand": "NutriDemo",
        "category": "Dairy & Alternatives",
        "barcode": "5901234123465",
        "serving_size": "150g",
        "raw_ingredients_text": "Skimmed Milk, Yoghurt Culture, Stevia Extract (E960), Citric Acid, Xanthan Gum, Natural Strawberry Flavour",
        "nutrition": {"energy_kcal": 55, "total_fat_g": 0.1, "saturated_fat_g": 0.1, "trans_fat_g": 0, "carbohydrates_g": 7, "total_sugar_g": 5, "added_sugar_g": 0, "dietary_fibre_g": 0, "protein_g": 5.5, "sodium_mg": 55},
        "ingredients": ["skimmed milk powder", "stevia extract rebaudioside a", "citric acid", "xanthan gum"],
        "allergens": [("Milk / Dairy", "declared")],
    },
    {
        "name": "NutriDemo Kettle Chips Original",
        "brand": "NutriDemo",
        "category": "Chips & Crisps",
        "barcode": "5901234123466",
        "serving_size": "30g",
        "raw_ingredients_text": "Potatoes, Sunflower Oil, Salt (Sodium Chloride), Monosodium Glutamate (E621)",
        "nutrition": {"energy_kcal": 480, "total_fat_g": 24, "saturated_fat_g": 2.5, "trans_fat_g": 0, "carbohydrates_g": 60, "total_sugar_g": 0.5, "added_sugar_g": 0, "dietary_fibre_g": 4, "protein_g": 5, "sodium_mg": 580},
        "ingredients": ["salt sodium chloride", "monosodium glutamate"],
        "allergens": [],
    },
]


# ---------------------------------------------------------------------------
# Seeder function
# ---------------------------------------------------------------------------

def seed_database(db: Session) -> None:
    from app.models.product import (
        Allergen, Ingredient, Product, NutritionFacts, ProductIngredient, ProductAllergen
    )

    # ---- Allergens ----
    logger.info("Seeding allergens ...")
    allergen_map: dict[str, Allergen] = {}
    for adef in ALLERGEN_DEFS:
        existing = db.query(Allergen).filter(Allergen.name == adef["name"]).first()
        if existing:
            allergen_map[adef["name"]] = existing
        else:
            obj = Allergen(id=_uuid(), **adef)
            db.add(obj)
            allergen_map[adef["name"]] = obj
    db.flush()
    logger.info(f"  {len(allergen_map)} allergens ready.")

    # ---- Ingredients ----
    logger.info("Seeding ingredient knowledge base ...")
    ingredient_map: dict[str, Ingredient] = {}
    for idef in INGREDIENT_DEFS:
        normalized = idef["normalized_name"]
        existing = db.query(Ingredient).filter(Ingredient.normalized_name == normalized).first()
        if existing:
            ingredient_map[normalized] = existing
        else:
            obj = Ingredient(id=_uuid(), **idef)
            db.add(obj)
            ingredient_map[normalized] = obj
    db.flush()
    logger.info(f"  {len(ingredient_map)} ingredients ready.")

    # ---- Products ----
    logger.info("Seeding demo products ...")
    seeded = 0
    for pdef in PRODUCT_DEFS:
        existing = db.query(Product).filter(Product.barcode == pdef["barcode"]).first()
        if existing:
            logger.info(f"  Skipping existing: {pdef['name']}")
            continue

        product = Product(
            id=_uuid(),
            name=pdef["name"],
            brand=pdef["brand"],
            category=pdef["category"],
            barcode=pdef["barcode"],
            serving_size=pdef["serving_size"],
            raw_ingredients_text=pdef["raw_ingredients_text"],
            data_source="demo",
            is_demo_data=True,
            is_verified=False,
            verification_note=DEMO_NOTE,
        )
        db.add(product)
        db.flush()  # get product.id

        # Nutrition facts (illustrative)
        nf = NutritionFacts(
            id=_uuid(),
            product_id=product.id,
            serving_unit="per_100g",
            is_illustrative=True,
            **pdef["nutrition"],
        )
        db.add(nf)

        # Ingredient links
        for idx, ing_key in enumerate(pdef["ingredients"]):
            ingredient = ingredient_map.get(ing_key)
            if ingredient is None:
                logger.warning(f"  Ingredient key '{ing_key}' not found in map, skipping.")
                continue
            pi = ProductIngredient(
                id=_uuid(),
                product_id=product.id,
                ingredient_id=ingredient.id,
                original_text=ingredient.name,
                order_index=idx,
                is_verified=False,
            )
            db.add(pi)

        # Allergen links
        for allergen_name, decl_type in pdef["allergens"]:
            allergen = allergen_map.get(allergen_name)
            if allergen is None:
                logger.warning(f"  Allergen '{allergen_name}' not found, skipping.")
                continue
            pa = ProductAllergen(
                id=_uuid(),
                product_id=product.id,
                allergen_id=allergen.id,
                declaration_type=decl_type,
            )
            db.add(pa)

        seeded += 1
        logger.info(f"  + {pdef['name']}")

    # 4. Seed default administrator user if not exists
    admin_email = "admin@nutrilens.com"
    admin_user = db.query(User).filter(User.email == admin_email).first()
    if not admin_user:
        admin_user = User(
            id=_uuid(),
            email=admin_email,
            hashed_password=get_password_hash("Admin123!"),
            full_name="NutriLens Administrator",
            role="admin",
            is_admin=True,
            is_active=True,
        )
        db.add(admin_user)
        db.flush()
        admin_profile = UserProfile(
            id=_uuid(),
            user_id=admin_user.id,
            dietary_preference="None",
            allergies=[],
            dietary_restrictions=[],
            nutrition_goals=[],
            monitored_nutrients=[],
        )
        db.add(admin_profile)
        logger.info(f"  + Admin user seeded: {admin_email}")

    # 5. Seed default scoring rule version if not exists
    default_rule = db.query(ScoringRuleVersion).filter(ScoringRuleVersion.version == SCORING_RULE_VERSION).first()
    if not default_rule:
        defaults = get_default_scoring_rules_dict()
        default_rule = ScoringRuleVersion(
            id=_uuid(),
            version=SCORING_RULE_VERSION,
            name="NutriLens Baseline Scoring Model v1.0",
            description="Initial deterministic scoring rules calibrated against WHO/ICMR references.",
            is_active=True,
            thresholds_food=defaults["thresholds_food"],
            thresholds_beverage=defaults["thresholds_beverage"],
            category_weights=defaults["category_weights"],
            general_weights=defaults["general_weights"],
        )
        db.add(default_rule)
        logger.info(f"  + Default scoring rule version seeded: {SCORING_RULE_VERSION}")

    db.commit()
    logger.info(f"Seed complete. {seeded} new demo products inserted.")


def main() -> None:
    from app.database.session import SessionLocal, check_db_connection
    if not check_db_connection():
        logger.error("Database is not reachable. Start PostgreSQL and retry.")
        sys.exit(1)

    from app.database.base import Base
    from app.database.session import engine
    import app.models  # noqa: F401 – register all models

    logger.info("Creating tables if they do not exist ...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
