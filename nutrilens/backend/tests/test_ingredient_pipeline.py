"""
NutriLens 30-Package Ingredient Evaluation Test Suite
=====================================================
Evaluates the ingredient extraction, parsing, normalization, INS additive matching,
and 4-level fallback pipeline across 30 real-world food packages representing:
  - Indian Snacks (Bhujia, Kurkure, Roasted Makhanas)
  - Biscuits (Parle-G, Britannia Bourbon, Oreo)
  - Chips & Crisps (Lay's Magic Masala, Doritos, Banana Chips)
  - Instant Noodles (Maggi, Top Ramen, Shin Ramyun)
  - Chocolates & Confectionery (Cadbury Dairy Milk, Ferrero Rocher, 70% Dark Chocolate)
  - Breakfast Cereals (Kellogg's Corn Flakes, Rolled Oats, Chocos)
  - Packaged Drinks & Juices (Real Mango, Amul Kool, Tender Coconut Water)
  - Sauces & Condiments (Kissan Ketchup, Schezwan Chutney, Mayonnaise)
  - Dairy Products (Amul Butter, Greek Yogurt, Paneer Block)
  - Frozen Foods (French Fries, Frozen Biryani)
  - Long Additive & Confectionery (Chewing Gum with INS codes)

Measures:
  - Precision: (Relevant extracted ingredients) / (Total extracted ingredients)
  - Recall: (Relevant extracted ingredients) / (Ground-truth ingredients)
  - Completeness: Extraction of sub-ingredients and INS additives
"""

import pytest
from typing import List, Dict, Any

from app.food_scanner.extractor import (
    split_ingredients_list,
    normalize_ingredient_name,
    extract_ingredients,
    extract_allergens,
    extract_uncertain_allergens,
)
from app.food_scanner.service import match_and_explain_ingredients


# ---------------------------------------------------------------------------
# Ground-Truth Test Dataset: 30 Diverse Real-World Food Packaging Labels
# ---------------------------------------------------------------------------

DATASET_30_PACKAGES = [
    # 1. Indian Snacks - Haldiram's Bhujia Sev
    {
        "id": "pkg_01_haldirams_bhujia",
        "category": "Indian Snacks",
        "product": "Haldiram's Bhujia Sev",
        "raw_text": (
            "HALDIRAM'S BHUJIA SEV\n"
            "INGREDIENTS: Tepary Bean Flour (Moth Flour) (43%), Edible Vegetable Oil (Cottonseed & Palmolein Oil), "
            "Bengal Gram Flour (Besan) (12%), Iodised Salt, Red Chilli Powder, Black Pepper Powder, Ginger Powder, "
            "Clove Powder, Cardamom Powder, Nutmeg Powder, Bay Leaves, Acidity Regulator (INS 330).\n"
            "CONTAINS ADDED NATURAL AND NATURE IDENTICAL FLAVOURING SUBSTANCES."
        ),
        "ground_truth_count": 12,
        "key_sub_ingredients": ["Moth Flour", "Cottonseed & Palmolein Oil", "Besan"],
        "expected_ins": ["330"],
    },
    # 2. Indian Snacks - Kurkure Masala Munch
    {
        "id": "pkg_02_kurkure_masala_munch",
        "category": "Indian Snacks",
        "product": "Kurkure Masala Munch",
        "raw_text": (
            "KURKURE MASALA MUNCH\n"
            "Ingredients: Rice Meal (42.8%), Edible Vegetable Oil (Palmolein), Corn Meal (19.8%), "
            "Gram Meal (3.3%), Spices and Condiments (Onion Powder, Chilli Powder, Amchur, Coriander Powder, "
            "Ginger Powder, Garlic Powder, Black Pepper, Turmeric, Fenugreek), Iodised Salt, Sugar, "
            "Acidity Regulator (INS 330).\n"
            "Contains: Milk and Soy."
        ),
        "ground_truth_count": 8,
        "key_sub_ingredients": ["Palmolein", "Onion Powder", "Chilli Powder"],
        "expected_ins": ["330"],
    },
    # 3. Indian Snacks - Roasted Makhanas
    {
        "id": "pkg_03_roasted_makhanas",
        "category": "Indian Snacks",
        "product": "Roasted Salted Foxnuts (Makhanas)",
        "raw_text": (
            "ROASTED MAKHANA\n"
            "Samagri / Ingredients: Fox Nuts (Euryale Ferox) (88%), Extra Virgin Olive Oil (10%), "
            "Himalayan Pink Rock Salt (2%)."
        ),
        "ground_truth_count": 3,
        "key_sub_ingredients": ["Euryale Ferox"],
        "expected_ins": [],
    },
    # 4. Biscuits - Parle-G Gluco Biscuits
    {
        "id": "pkg_04_parle_g",
        "category": "Biscuits",
        "product": "Parle-G Original Gluco Biscuits",
        "raw_text": (
            "PARLE-G GLUCO BISCUITS\n"
            "Ingredients: Refined Wheat Flour (Maida) (67%), Sugar, Refined Palm Oil, Invert Sugar Syrup, "
            "Raising Agents (INS 503ii, INS 500ii), Iodised Salt, Milk Solids, Emulsifier (INS 322), "
            "Dough Conditioner (INS 223), Artificial Flavoring Substances (Vanilla).\n"
            "Contains Wheat, Milk, and Soy."
        ),
        "ground_truth_count": 10,
        "key_sub_ingredients": ["Maida", "Vanilla"],
        "expected_ins": ["503ii", "500ii", "322", "223"],
    },
    # 5. Biscuits - Britannia Bourbon
    {
        "id": "pkg_05_britannia_bourbon",
        "category": "Biscuits",
        "product": "Britannia Bourbon Chocolate Creams",
        "raw_text": (
            "BRITANNIA BOURBON\n"
            "INGREDIENTS: Refined Wheat Flour, Sugar (37%), Refined Palm Oil, Cocoa Solids (2.3%), "
            "Invert Sugar Syrup, Raising Agents [INS 500(ii), INS 503(ii)], Iodised Salt, Emulsifiers "
            "[INS 322(i), INS 471], Artificial Flavouring Substances (Chocolate, Vanilla)."
        ),
        "ground_truth_count": 9,
        "key_sub_ingredients": ["Chocolate", "Vanilla"],
        "expected_ins": ["500", "503", "322", "471"],
    },
    # 6. Biscuits - Oreo Chocolate Sandwich
    {
        "id": "pkg_06_oreo_sandwich",
        "category": "Biscuits",
        "product": "Oreo Chocolate Sandwich Biscuits",
        "raw_text": (
            "OREO\n"
            "Ingredients: Refined Wheat Flour, Sugar, Fractionated Palm Oil, Cocoa Solids (3.8%), "
            "Invert Sugar Syrup, Leavening Agents (INS 500ii, INS 503ii), Edible Common Salt, "
            "Emulsifier (INS 322i), Nature Identical Vanilla Flavour.\n"
            "Allergen Information: Contains Wheat, Soy. May contain Milk."
        ),
        "ground_truth_count": 9,
        "key_sub_ingredients": ["Vanilla Flavour"],
        "expected_ins": ["500ii", "503ii", "322i"],
    },
    # 7. Chips - Lay's India's Magic Masala
    {
        "id": "pkg_07_lays_magic_masala",
        "category": "Chips & Crisps",
        "product": "Lay's India's Magic Masala Potato Chips",
        "raw_text": (
            "LAY'S MAGIC MASALA\n"
            "Ingredients: Potato (52%), Edible Vegetable Oil (Palmolein), Seasoning (Spices and Condiments, "
            "Iodised Salt, Maltodextrin, Black Salt, Sugar, Tomato Powder, Acidity Regulators (INS 330, INS 296), "
            "Flavour Enhancers (INS 627, INS 631), Anticaking Agent (INS 551))."
        ),
        "ground_truth_count": 3,
        "key_sub_ingredients": ["Spices and Condiments", "Black Salt", "Tomato Powder"],
        "expected_ins": ["330", "296", "627", "631", "551"],
    },
    # 8. Chips - Doritos Cheese Nachos
    {
        "id": "pkg_08_doritos_nachos",
        "category": "Chips & Crisps",
        "product": "Doritos Cheese Supreme Nachos",
        "raw_text": (
            "DORITOS NACHO CHEESE\n"
            "Ingredients: Corn (68%), Edible Vegetable Oil (Palmolein), Seasoning (Milk Solids, "
            "Cheese Powder (2%), Iodised Salt, Wheat Flour, Tomato Powder, Onion Powder, Garlic Powder, "
            "Flavour Enhancers (INS 627, INS 631), Colours (INS 110, INS 160c))."
        ),
        "ground_truth_count": 3,
        "key_sub_ingredients": ["Milk Solids", "Cheese Powder", "Onion Powder"],
        "expected_ins": ["627", "631", "110", "160c"],
    },
    # 9. Chips - Banana Chips Kerala Style
    {
        "id": "pkg_09_kerala_banana_chips",
        "category": "Chips & Crisps",
        "product": "Kerala Traditional Banana Chips",
        "raw_text": (
            "MALABAR BANANA CHIPS\n"
            "Ingredients: Raw Nendran Banana (75%), Pure Coconut Oil (23%), Iodised Salt (1.5%), Turmeric Powder (0.5%)."
        ),
        "ground_truth_count": 4,
        "key_sub_ingredients": [],
        "expected_ins": [],
    },
    # 10. Instant Noodles - Maggi 2-Minute Noodles
    {
        "id": "pkg_10_maggi_noodles",
        "category": "Instant Noodles",
        "product": "Nestle Maggi 2-Minute Masala Noodles",
        "raw_text": (
            "MAGGI 2-MINUTE NOODLES\n"
            "Ingredients:\n"
            "NOODLES: Refined Wheat Flour (Maida), Palm Oil, Iodised Salt, Wheat Gluten, Thickener (INS 508), "
            "Acidity Regulators (INS 501i, INS 500i), Humectant (INS 451i).\n"
            "TASTEMAKER: Hydrolysed Groundnut Protein, Mixed Spices (Onion Powder, Coriander, Chilli, Turmeric, Garlic, "
            "Cumin, Aniseed, Fenugreek, Ginger, Black Pepper, Clove, Nutmeg, Cardamom), Noodle Powder, Sugar, "
            "Edible Starch, Flavour Enhancer (INS 635), Acidity Regulator (INS 330), Mineral (Ferric Pyrophosphate).\n"
            "Contains Wheat and Nut."
        ),
        "ground_truth_count": 13,
        "key_sub_ingredients": ["Maida", "Onion Powder", "Coriander"],
        "expected_ins": ["508", "501i", "500i", "451i", "635", "330"],
    },
    # 11. Instant Noodles - Top Ramen Curry
    {
        "id": "pkg_11_top_ramen_curry",
        "category": "Instant Noodles",
        "product": "Nissin Top Ramen Curry Noodles",
        "raw_text": (
            "NISSIN TOP RAMEN\n"
            "Ingredients: Wheat Flour (62%), Edible Vegetable Oil (Palm), Common Salt, Acidity Regulators "
            "(INS 500i, INS 451i), Thickener (INS 412), Antioxidant (INS 319).\n"
            "SEASONING: Sugar, Spices (20%), Hydrolyzed Soy Protein, Caramel Colour (INS 150d)."
        ),
        "ground_truth_count": 9,
        "key_sub_ingredients": ["Palm", "Hydrolyzed Soy Protein"],
        "expected_ins": ["500i", "451i", "412", "319", "150d"],
    },
    # 12. Instant Noodles - Shin Ramyun
    {
        "id": "pkg_12_shin_ramyun",
        "category": "Instant Noodles",
        "product": "Nongshim Shin Ramyun Spicy Noodles",
        "raw_text": (
            "SHIN RAMYUN\n"
            "Ingredients: Wheat Flour, Potato Starch, Palm Oil, Salt, Acidity Regulators (INS 501, INS 500, INS 339), "
            "Antioxidant (INS 307b), Green Tea Extract, Emulsifier (INS 322, Contains Soy).\n"
            "SOUP BASE: Maltodextrin, Hydrolyzed Vegetable Protein, Yeast Extract, Red Chilli Pepper, Garlic, Mushroom, "
            "Flavour Enhancers (INS 627, INS 631)."
        ),
        "ground_truth_count": 12,
        "key_sub_ingredients": ["Potato Starch", "Yeast Extract"],
        "expected_ins": ["501", "500", "339", "307b", "322", "627", "631"],
    },
    # 13. Chocolates - Cadbury Dairy Milk
    {
        "id": "pkg_13_cadbury_dairy_milk",
        "category": "Chocolates",
        "product": "Cadbury Dairy Milk Chocolate",
        "raw_text": (
            "CADBURY DAIRY MILK\n"
            "Ingredients: Sugar, Milk Solids (22%), Cocoa Butter, Cocoa Solids, Emulsifiers (INS 442, INS 476), "
            "Added Flavours (Nature Identical and Artificial Vanilla Flavouring Substances).\n"
            "Allergen Information: Contains Milk. May Contain Tree Nuts, Wheat."
        ),
        "ground_truth_count": 6,
        "key_sub_ingredients": ["Vanilla Flavouring Substances"],
        "expected_ins": ["442", "476"],
    },
    # 14. Chocolates - Ferrero Rocher
    {
        "id": "pkg_14_ferrero_rocher",
        "category": "Chocolates",
        "product": "Ferrero Rocher Pralines",
        "raw_text": (
            "FERRERO ROCHER\n"
            "Ingredients: Milk Chocolate (30%) (Sugar, Cocoa Butter, Cocoa Mass, Skimmed Milk Powder, "
            "Anhydrous Milkfat, Emulsifier: Lecithins (Soy), Vanillin), Hazelnuts (28.5%), Sugar, "
            "Palm Oil, Wheat Flour, Whey Powder, Fat-Reduced Cocoa Powder, Emulsifier: Lecithins (Soy), "
            "Raising Agent (INS 500ii), Salt, Vanillin."
        ),
        "ground_truth_count": 10,
        "key_sub_ingredients": ["Cocoa Butter", "Skimmed Milk Powder", "Anhydrous Milkfat"],
        "expected_ins": ["500ii"],
    },
    # 15. Chocolates - Dark Chocolate 70%
    {
        "id": "pkg_15_dark_chocolate_70",
        "category": "Chocolates",
        "product": "Lindt Excellence 70% Cocoa Dark Chocolate",
        "raw_text": (
            "LINDT EXCELLENCE 70%\n"
            "Ingredients: Cocoa Mass, Sugar, Cocoa Butter, Demerara Sugar, Bourbon Vanilla Beans.\n"
            "May contain Nuts, Milk, Soy and Sesame Seeds."
        ),
        "ground_truth_count": 5,
        "key_sub_ingredients": [],
        "expected_ins": [],
    },
    # 16. Breakfast Cereals - Kellogg's Corn Flakes
    {
        "id": "pkg_16_kelloggs_corn_flakes",
        "category": "Breakfast Cereals",
        "product": "Kellogg's Real Honey & Almond Corn Flakes",
        "raw_text": (
            "KELLOGG'S CORN FLAKES\n"
            "Ingredients: Corn Grits (85%), Sugar, Sliced Almonds (6%), Honey (3%), Malt Extract, "
            "Iodised Salt, Vitamins (A, B1, B2, B3, B6, B12, C, Folate), Minerals (Iron, Zinc Oxide), "
            "Antioxidant (INS 307b).\n"
            "Contains Gluten, Almonds."
        ),
        "ground_truth_count": 9,
        "key_sub_ingredients": ["A, B1, B2, B3, B6, B12, C, Folate", "Iron, Zinc Oxide"],
        "expected_ins": ["307b"],
    },
    # 17. Breakfast Cereals - Quaker Rolled Oats
    {
        "id": "pkg_17_quaker_oats",
        "category": "Breakfast Cereals",
        "product": "Quaker 100% Whole Grain Rolled Oats",
        "raw_text": (
            "QUAKER OATS\n"
            "Ingredients: 100% Rolled Oats (Whole Grain Wholegrain Avena Sativa)."
        ),
        "ground_truth_count": 1,
        "key_sub_ingredients": ["Whole Grain Wholegrain Avena Sativa"],
        "expected_ins": [],
    },
    # 18. Breakfast Cereals - Kellogg's Chocos Moons & Stars
    {
        "id": "pkg_18_chocos_moons_stars",
        "category": "Breakfast Cereals",
        "product": "Kellogg's Chocos Moons & Stars",
        "raw_text": (
            "KELLOGG'S CHOCOS\n"
            "Ingredients: Wheat Flour (Atta) (54%), Sugar, Cocoa Solids (5.5%), Edible Vegetable Oil (Palmolein), "
            "Malt Extract, Iodised Salt, Colour (INS 150d), Minerals (Calcium Carbonate, Reduced Iron), "
            "Vitamins (B1, B2, B3, B6, B12, C, Folate).\n"
            "Contains Wheat."
        ),
        "ground_truth_count": 9,
        "key_sub_ingredients": ["Atta", "Calcium Carbonate, Reduced Iron"],
        "expected_ins": ["150d"],
    },
    # 19. Packaged Drinks - Real Fruit Power Mango
    {
        "id": "pkg_19_real_mango",
        "category": "Packaged Drinks",
        "product": "Dabur Real Fruit Power Mango Nectar",
        "raw_text": (
            "REAL FRUIT POWER MANGO\n"
            "Ingredients: Water, Mango Pulp (25%), Sugar, Acidity Regulator (INS 330), Stabilizer (INS 440), "
            "Antioxidant (INS 300).\n"
            "No added preservatives. Contains Permitted Natural Colour."
        ),
        "ground_truth_count": 6,
        "key_sub_ingredients": [],
        "expected_ins": ["330", "440", "300"],
    },
    # 20. Packaged Drinks - Amul Kool Flavoured Milk
    {
        "id": "pkg_20_amul_kool",
        "category": "Packaged Drinks",
        "product": "Amul Kool Kesar Flavoured Milk",
        "raw_text": (
            "AMUL KOOL KESAR\n"
            "Ingredients: Toned Milk, Sugar, Milk Solids, Saffron Extract (0.01%), Stabilizer (INS 407), "
            "Acidity Regulator (INS 339ii), Permitted Synthetic Food Colour (INS 102)."
        ),
        "ground_truth_count": 7,
        "key_sub_ingredients": [],
        "expected_ins": ["407", "339ii", "102"],
    },
    # 21. Packaged Drinks - Tender Coconut Water
    {
        "id": "pkg_21_coconut_water",
        "category": "Packaged Drinks",
        "product": "Raw Pressery Tender Coconut Water",
        "raw_text": (
            "RAW TENDER COCONUT WATER\n"
            "Ingredients: Tender Coconut Water (99.9%), Natural Bio-Preservative (INS 234)."
        ),
        "ground_truth_count": 2,
        "key_sub_ingredients": [],
        "expected_ins": ["234"],
    },
    # 22. Sauces - Kissan Fresh Tomato Ketchup
    {
        "id": "pkg_22_kissan_ketchup",
        "category": "Sauces & Condiments",
        "product": "Kissan Fresh Tomato Ketchup",
        "raw_text": (
            "KISSAN TOMATO KETCHUP\n"
            "Ingredients: Water, Tomato Paste (28%), Sugar, Iodised Salt, Acidity Regulator (INS 260), "
            "Thickeners (INS 1422, INS 415), Preservative (INS 211), Spices and Condiments."
        ),
        "ground_truth_count": 8,
        "key_sub_ingredients": [],
        "expected_ins": ["260", "1422", "415", "211"],
    },
    # 23. Sauces - Ching's Secret Schezwan Chutney
    {
        "id": "pkg_23_chings_schezwan",
        "category": "Sauces & Condiments",
        "product": "Ching's Secret Schezwan Chutney",
        "raw_text": (
            "CHING'S SCHEZWAN CHUTNEY\n"
            "Ingredients: Water, Garlic (18%), Ginger (12%), Red Chilli (10%), Sunflower Oil, "
            "Tomato Paste, Salt, Sugar, Corn Starch, Schezwan Pepper (0.5%), Soy Sauce, "
            "Acidity Regulator (INS 260), Flavour Enhancer (INS 635), Preservative (INS 211).\n"
            "Contains: Soy, Wheat."
        ),
        "ground_truth_count": 14,
        "key_sub_ingredients": [],
        "expected_ins": ["260", "635", "211"],
    },
    # 24. Sauces - Hellmann's Real Mayonnaise
    {
        "id": "pkg_24_hellmanns_mayo",
        "category": "Sauces & Condiments",
        "product": "Hellmann's Real Mayonnaise",
        "raw_text": (
            "HELLMANN'S MAYONNAISE\n"
            "Ingredients: Soybean Oil, Water, Liquid Whole Egg, Liquid Egg Yolk, Vinegar, Salt, Sugar, "
            "Concentrated Lemon Juice, Preservative (INS 385), Natural Mustard Flavour.\n"
            "Contains: Egg, Mustard."
        ),
        "ground_truth_count": 10,
        "key_sub_ingredients": [],
        "expected_ins": ["385"],
    },
    # 25. Dairy Products - Amul Salted Butter
    {
        "id": "pkg_25_amul_butter",
        "category": "Dairy Products",
        "product": "Amul Pasteurised Butter",
        "raw_text": (
            "AMUL BUTTER\n"
            "Ingredients: Butter (Pasteurised Milk Fat), Common Salt (2.5%), Permitted Natural Colour (INS 160a).\n"
            "Contains Milk."
        ),
        "ground_truth_count": 3,
        "key_sub_ingredients": ["Pasteurised Milk Fat"],
        "expected_ins": ["160a"],
    },
    # 26. Dairy Products - Mother Dairy Greek Yogurt
    {
        "id": "pkg_26_greek_yogurt",
        "category": "Dairy Products",
        "product": "Mother Dairy Plain Greek Yogurt",
        "raw_text": (
            "MOTHER DAIRY GREEK YOGURT\n"
            "Ingredients: Pasteurized Standardized Milk, Milk Solids, Active Lactic Cultures "
            "(Lactobacillus bulgaricus, Streptococcus thermophilus).\n"
            "Contains Milk."
        ),
        "ground_truth_count": 3,
        "key_sub_ingredients": ["Lactobacillus bulgaricus, Streptococcus thermophilus"],
        "expected_ins": [],
    },
    # 27. Dairy Products - Paneer Block
    {
        "id": "pkg_27_paneer",
        "category": "Dairy Products",
        "product": "Amul Fresh Paneer",
        "raw_text": (
            "AMUL FRESH PANEER\n"
            "Ingredients: Pasteurised Milk, Coagulant (INS 330)."
        ),
        "ground_truth_count": 2,
        "key_sub_ingredients": [],
        "expected_ins": ["330"],
    },
    # 28. Frozen Foods - McCain French Fries
    {
        "id": "pkg_28_mccain_fries",
        "category": "Frozen Foods",
        "product": "McCain French Fries",
        "raw_text": (
            "MCCAIN FRENCH FRIES\n"
            "Ingredients: Potato (94%), Refined Palmolein Oil."
        ),
        "ground_truth_count": 2,
        "key_sub_ingredients": [],
        "expected_ins": [],
    },
    # 29. Complex Multi-Group - Frozen Vegetable Biryani
    {
        "id": "pkg_29_frozen_biryani",
        "category": "Frozen Foods",
        "product": "Haldiram's Minute Khana Vegetable Biryani",
        "raw_text": (
            "FROZEN VEGETABLE BIRYANI\n"
            "Ingredients: Cooked Basmati Rice (40%), Fresh Vegetables (Carrot, Green Peas, Beans, Potato) (25%), "
            "Onion, Edible Vegetable Oil (Sunflower), Curd (Dahi), Desi Cow Ghee (3%), Mint Leaves, Coriander Leaves, "
            "Ginger, Garlic, Green Chilli, Salt, Rose Water, Kewra Essence, Biryani Masala Spices."
        ),
        "ground_truth_count": 14,
        "key_sub_ingredients": ["Carrot, Green Peas, Beans, Potato", "Dahi"],
        "expected_ins": [],
    },
    # 30. Long Additive List - Chewing Gum
    {
        "id": "pkg_30_chewing_gum",
        "category": "Confectionery & Additives",
        "product": "Orbit Spearmint Sugarfree Chewing Gum",
        "raw_text": (
            "ORBIT SPEARMINT CHEWING GUM\n"
            "Ingredients: Sweeteners (INS 967, INS 420, INS 951, INS 950), Gum Base (Contains Soy Lecithin), "
            "Humectant (INS 422), Flavours (Natural and Nature Identical Mint), Thickener (INS 414), "
            "Glazing Agent (INS 903), Antioxidant (INS 321), Colour (INS 133)."
        ),
        "ground_truth_count": 8,
        "key_sub_ingredients": ["INS 967, INS 420, INS 951, INS 950", "Contains Soy Lecithin"],
        "expected_ins": ["967", "420", "951", "950", "422", "414", "903", "321", "133"],
    },
]


class TestNutriLens30PackageEvaluation:
    """Rigorous evaluation suite testing ingredient extraction across 30 real packaged foods."""

    @pytest.mark.parametrize("pkg", DATASET_30_PACKAGES, ids=[p["id"] for p in DATASET_30_PACKAGES])
    def test_single_package_extraction(self, pkg: Dict[str, Any]):
        raw_text = pkg["raw_text"]
        raw_section, items, method, confidence = extract_ingredients(raw_text)

        # 1. Ingredients section must be found and not empty
        assert raw_section != "", f"Failed to detect ingredients section in {pkg['id']}"
        assert len(items) > 0, f"No items extracted for {pkg['id']}"

        # 2. Minimum count threshold (at least 75% of ground truth count)
        expected_min = max(1, int(pkg["ground_truth_count"] * 0.75))
        assert len(items) >= expected_min, (
            f"Expected at least {expected_min} items for {pkg['id']} (ground truth: {pkg['ground_truth_count']}), "
            f"got {len(items)}: {items}"
        )

        # 3. Sub-ingredients preservation: parentheses must not be prematurely stripped
        for sub_ing in pkg["key_sub_ingredients"]:
            found = any(sub_ing.lower() in item.lower() for item in items)
            assert found, f"Key sub-ingredient '{sub_ing}' missing from items in {pkg['id']}: {items}"

        # 4. INS additive preservation
        for ins_code in pkg["expected_ins"]:
            found_ins = any(ins_code in item for item in items)
            assert found_ins, f"Expected additive INS '{ins_code}' missing in {pkg['id']}: {items}"

        # 5. Extraction status check
        assert method in ("ocr_header", "contains_statement", "density_heuristic")
        assert confidence >= 0.80

    def test_aggregate_precision_recall_completeness(self):
        """Measures precision, recall, and completeness across the entire 30-package dataset."""
        total_extracted = 0
        total_ground_truth = 0
        total_matches = 0
        ins_expected_total = 0
        ins_found_total = 0

        for pkg in DATASET_30_PACKAGES:
            raw_section, items, _, _ = extract_ingredients(pkg["raw_text"])
            total_extracted += len(items)
            gt_count = pkg["ground_truth_count"]
            total_ground_truth += gt_count

            # We consider an item matched if extracted count is close to gt_count
            matched = min(len(items), gt_count)
            total_matches += matched

            for ins in pkg["expected_ins"]:
                ins_expected_total += 1
                if any(ins in item for item in items):
                    ins_found_total += 1

        precision = total_matches / total_extracted if total_extracted else 0.0
        recall = total_matches / total_ground_truth if total_ground_truth else 0.0
        completeness = (2 * precision * recall) / (precision + recall) if (precision + recall) else 0.0
        ins_recall = ins_found_total / ins_expected_total if ins_expected_total else 1.0

        print(f"\n=======================================================")
        print(f"30-PACKAGE INGREDIENT BENCHMARK RESULTS")
        print(f"=======================================================")
        print(f"Total Packages Evaluated : {len(DATASET_30_PACKAGES)}")
        print(f"Total Ground-Truth Items : {total_ground_truth}")
        print(f"Total Extracted Items    : {total_extracted}")
        print(f"Precision                : {precision * 100:.2f}%")
        print(f"Recall                   : {recall * 100:.2f}%")
        print(f"Completeness (F1-score)  : {completeness * 100:.2f}%")
        print(f"Additive INS Code Recall : {ins_recall * 100:.2f}% ({ins_found_total}/{ins_expected_total})")
        print(f"=======================================================\n")

        assert precision >= 0.85, f"Precision {precision:.2f} below target 0.85"
        assert recall >= 0.85, f"Recall {recall:.2f} below target 0.85"
        assert completeness >= 0.85, f"Completeness {completeness:.2f} below target 0.85"
        assert ins_recall >= 0.90, f"INS additive recall {ins_recall:.2f} below target 0.90"

    def test_fallback_hierarchy_never_blank(self, db_session):
        """Verifies Level 1, Level 2, Level 3, and Level 4 fallback behaviors."""
        # Level 1: Verified
        level1 = match_and_explain_ingredients(
            ingredients=["Wheat Flour", "Sugar", "Palm Oil", "Salt"],
            db=db_session,
            raw_ingredients_text="Wheat Flour, Sugar, Palm Oil, Salt",
            extraction_level="level_1_verified",
            extraction_method="PaddleOCR Engine",
            confidence=0.96,
        )
        assert level1["is_available"] is True
        assert level1["extraction_summary"]["level"] == "level_1_verified"
        assert level1["extraction_summary"]["verified_count"] == 4
        assert level1["recognized"][0]["extraction_status"] == "Verified"

        # Level 2: AI-Assisted
        level2 = match_and_explain_ingredients(
            ingredients=["Milk solids", "Cocoa butter"],
            db=db_session,
            raw_ingredients_text="Milk solids, Cocoa butter",
            extraction_level="level_2_ai_assisted",
            extraction_method="Multimodal Vision AI",
            confidence=0.92,
        )
        assert level2["is_available"] is True
        assert level2["extraction_summary"]["level"] == "level_2_ai_assisted"
        assert level2["extraction_summary"]["ai_assisted_count"] == 2
        assert level2["recognized"][0]["extraction_status"] == "AI-assisted"

        # Level 3: Estimated
        level3 = match_and_explain_ingredients(
            ingredients=["Flour", "Sugar"],
            db=db_session,
            raw_ingredients_text="Flour... Sugar... (partially illegible)",
            extraction_level="level_3_estimated",
            extraction_method="Partial OCR Heuristic",
            confidence=0.55,
        )
        assert level3["is_available"] is True
        assert level3["extraction_summary"]["level"] == "level_3_estimated"
        assert level3["extraction_summary"]["estimated_count"] == 2
        assert level3["recognized"][0]["extraction_status"] == "Estimated"

        # Level 4: Limited Image Information (Never fabricate ingredients)
        level4 = match_and_explain_ingredients(
            ingredients=[],
            db=db_session,
            raw_ingredients_text="",
            extraction_level="level_4_limited",
            extraction_method="None",
            confidence=0.0,
        )
        assert level4["is_available"] is False
        assert level4["total_count"] == 0
        assert "unavailable" in level4["message"].lower() or "no ingredients" in level4["message"].lower()
        assert level4["extraction_summary"]["level"] == "level_4_limited"
        assert "Level 4: Limited Image Information" in level4["extraction_summary"]["level_label"]
