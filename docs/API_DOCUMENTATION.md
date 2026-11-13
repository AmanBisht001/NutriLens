# NutriLens – API Documentation

## 1. Overview
The NutriLens backend is built using FastAPI, providing automatic interactive OpenAPI documentation, strict request/response data contracts via Pydantic, and predictable error structures.

- **Base URL (Local)**: `http://localhost:8000`
- **Interactive Swagger UI**: `http://localhost:8000/api/v1/docs`
- **ReDoc UI**: `http://localhost:8000/api/v1/redoc`
- **OpenAPI JSON**: `http://localhost:8000/api/v1/openapi.json`

## 2. Authentication & Authorization
- **Token Type**: Bearer token authentication via standard HTTP `Authorization: Bearer <JWT>` header.
- **Algorithm**: `HS256`.
- **Token Validity**: Configured via `ACCESS_TOKEN_EXPIRE_MINUTES` (defaults to 7 days in development).
- **Password Hashing**: Salted `bcrypt` hashing with auto-generated salts.

---

## 3. Implemented Endpoints

### System Discovery & Health

#### `GET /`
Returns service discovery metadata and links.

##### Response `200 OK`
```json
{
  "app": "NutriLens API",
  "version": "0.1.0",
  "docs": "/api/v1/docs",
  "health": "/api/health"
}
```

---

#### `GET /api/health`
Direct health monitor endpoint evaluating API service state and database connectivity.

##### Response `200 OK`
```json
{
  "status": "healthy",
  "app": "NutriLens API",
  "version": "0.1.0",
  "environment": "development",
  "database": "connected"
}
```

---

#### `GET /api/v1/health`
Versioned health check endpoint matching `/api/health`.

---

### Authentication & User Profiles (Day 2)

#### `POST /api/auth/register` (also available as `POST /api/v1/auth/register`)
Registers a new user account, creates their personalized dietary profile, securely hashes their password with bcrypt, and issues a JWT access token.

##### Request Body
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Maya Lin",
  "age": 28,
  "dietary_preference": "Vegetarian",
  "allergies": ["Peanuts", "Tree Nuts"],
  "dietary_restrictions": ["Low-Sodium"],
  "nutrition_goals": ["Heart Health", "Clean Eating"]
}
```

##### Response `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "c1f76d90-3cb8-4f8e-bdf1-d3a39e248b3b",
    "email": "user@example.com",
    "full_name": "Maya Lin",
    "age": 28,
    "is_active": true,
    "profile": {
      "id": "e2a91e5c-091a-4d76-b605-7f918e15467c",
      "user_id": "c1f76d90-3cb8-4f8e-bdf1-d3a39e248b3b",
      "dietary_preference": "Vegetarian",
      "allergies": ["Peanuts", "Tree Nuts"],
      "dietary_restrictions": ["Low-Sodium"],
      "nutrition_goals": ["Heart Health", "Clean Eating"],
      "created_at": "2026-11-04T09:20:00Z",
      "updated_at": "2026-11-04T09:20:00Z"
    },
    "created_at": "2026-11-04T09:20:00Z",
    "updated_at": "2026-11-04T09:20:00Z"
  }
}
```

---

#### `POST /api/auth/login` (also available as `POST /api/v1/auth/login`)
Authenticates credentials against the bcrypt password hash and returns a signed JWT access token.

##### Request Body
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

##### Response `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "c1f76d90-3cb8-4f8e-bdf1-d3a39e248b3b",
    "email": "user@example.com",
    "full_name": "Maya Lin",
    "age": 28,
    "is_active": true,
    "profile": { ... }
  }
}
```

---

#### `GET /api/auth/me` (also available as `GET /api/v1/auth/me`)
Retrieves the authenticated user's details and active dietary profile.

##### Headers
`Authorization: Bearer <access_token>`

##### Response `200 OK`
```json
{
  "id": "c1f76d90-3cb8-4f8e-bdf1-d3a39e248b3b",
  "email": "user@example.com",
  "full_name": "Maya Lin",
  "age": 28,
  "is_active": true,
  "profile": {
    "id": "e2a91e5c-091a-4d76-b605-7f918e15467c",
    "user_id": "c1f76d90-3cb8-4f8e-bdf1-d3a39e248b3b",
    "dietary_preference": "Vegetarian",
    "allergies": ["Peanuts", "Tree Nuts"],
    "dietary_restrictions": ["Low-Sodium"],
    "nutrition_goals": ["Heart Health", "Clean Eating"]
  }
}
```

---

#### `PUT /api/auth/profile` (also accepts `PUT /api/auth/me`)
Updates the authenticated user's name, age, dietary preferences, allergens, restrictions, and personal nutrition goals.

##### Headers
`Authorization: Bearer <access_token>`

##### Request Body
```json
{
  "full_name": "Maya Lin-Zhang",
  "age": 29,
  "dietary_preference": "Pescatarian",
  "allergies": ["Peanuts", "Shellfish"],
  "dietary_restrictions": ["Low-Sodium", "Low-Sugar"],
  "nutrition_goals": ["Heart Health", "High Protein"]
}
```

##### Response `200 OK`
Returns the updated `UserResponse` object.

---

#### `POST /api/auth/logout`
Explicit session termination endpoint.

##### Response `200 OK`
```json
{
  "message": "Successfully logged out.",
  "detail": null
}
```

---

### Product Catalogue & Ingredients (Day 3)

#### `GET /api/products` (also available as `GET /api/v1/products`)
List products with optional search, category filter, and pagination.

##### Query Parameters
- `search` (string, optional): Search by product name or brand (e.g. "Cola", "NutriDemo")
- `category` (string, optional): Filter by exact category name (e.g. "Beverages", "Biscuits & Cookies")
- `page` (integer, default: 1): Page number (1-indexed)
- `page_size` (integer, default: 20): Results per page (max 100)

##### Response `200 OK`
```json
{
  "items": [
    {
      "id": "e4a291f0-0a25-4c01-bf50-51c36b6920f2",
      "name": "NutriDemo Classic Cola",
      "brand": "NutriDemo",
      "category": "Beverages",
      "barcode": "5901234123459",
      "serving_size": "355ml",
      "data_source": "demo",
      "is_demo_data": true,
      "is_verified": false,
      "nutrition_facts": {
        "id": "f8a12e34-5678-4abc-9012-3456789abcde",
        "energy_kcal": 140,
        "total_fat_g": 0,
        "saturated_fat_g": 0,
        "trans_fat_g": 0,
        "carbohydrates_g": 39,
        "total_sugar_g": 39,
        "added_sugar_g": 39,
        "dietary_fibre_g": 0,
        "protein_g": 0,
        "sodium_mg": 45,
        "serving_unit": "per_100g",
        "is_illustrative": true
      }
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

---

#### `GET /api/products/{id}` (also available as `GET /api/v1/products/{id}`)
Get complete product detail including structured ingredient knowledge base and allergen declarations.

##### Response `200 OK`
```json
{
  "id": "e4a291f0-0a25-4c01-bf50-51c36b6920f2",
  "name": "NutriDemo Classic Cola",
  "brand": "NutriDemo",
  "category": "Beverages",
  "barcode": "5901234123459",
  "serving_size": "355ml",
  "data_source": "demo",
  "is_demo_data": true,
  "is_verified": false,
  "verification_note": "DEMO DATA – illustrative values only, not verified nutritional facts",
  "raw_ingredients_text": "Carbonated Water, High Fructose Corn Syrup, Caramel Colour Class IV, Phosphoric Acid, Natural Flavours, Caffeine",
  "nutrition_facts": {
    "id": "f8a12e34-5678-4abc-9012-3456789abcde",
    "energy_kcal": 140,
    "total_fat_g": 0,
    "saturated_fat_g": 0,
    "trans_fat_g": 0,
    "carbohydrates_g": 39,
    "total_sugar_g": 39,
    "added_sugar_g": 39,
    "dietary_fibre_g": 0,
    "protein_g": 0,
    "sodium_mg": 45,
    "serving_unit": "per_100g",
    "is_illustrative": true
  },
  "product_ingredients": [
    {
      "ingredient": {
        "id": "b1a23456-789a-bcde-f012-3456789abcde",
        "name": "High Fructose Corn Syrup",
        "category": "sweetener",
        "concern_level": "moderate",
        "ins_number": null,
        "purpose": "Sweetener and humectant derived from corn starch"
      },
      "original_text": "High Fructose Corn Syrup",
      "order_index": 0,
      "is_verified": false
    }
  ],
  "product_allergens": []
}
```

---

#### `GET /api/categories` (also available as `GET /api/v1/categories`)
List distinct product categories with respective product counts.

##### Response `200 OK`
```json
{
  "categories": [
    {
      "name": "Beverages",
      "product_count": 3
    },
    {
      "name": "Biscuits & Cookies",
      "product_count": 1
    },
    {
      "name": "Bread & Bakery",
      "product_count": 1
    },
    {
      "name": "Breakfast Cereals",
      "product_count": 1
    },
    {
      "name": "Chips & Crisps",
      "product_count": 1
    },
    {
      "name": "Dairy & Alternatives",
      "product_count": 1
    },
    {
      "name": "Frozen Desserts",
      "product_count": 1
    },
    {
      "name": "Snack Bars",
      "product_count": 1
    }
  ]
}
```

---

#### `GET /api/ingredients` (also available as `GET /api/v1/ingredients`)
List canonical ingredients from the structured knowledge base with search and filters.

##### Query Parameters
- `search` (string, optional): Search by name, normalized name, or INS/E-number (e.g. "Aspartame", "E211")
- `category` (string, optional): Filter by function (e.g. "preservative", "emulsifier", "sweetener")
- `concern_level` (string, optional): Filter by level ("safe", "moderate", "high")
- `page` (integer, default: 1): Page number
- `page_size` (integer, default: 50): Results per page

##### Response `200 OK`
```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "name": "Sodium Benzoate",
      "normalized_name": "sodium benzoate",
      "category": "preservative",
      "description": "A common preservative used in beverages and condiments.",
      "aliases": null,
      "purpose": "Prevents microbial growth in acidic foods",
      "concern_level": "moderate",
      "ins_number": "E211",
      "source_reference": null,
      "is_common_allergen": false,
      "created_at": "2026-11-11T13:41:58Z"
    }
  ],
  "total": 30,
  "page": 1,
  "page_size": 50,
  "total_pages": 1
}
```

---

#### `GET /api/ingredients/{id}` (also available as `GET /api/v1/ingredients/{id}`)
Get complete knowledge-base record for an individual ingredient.

##### Response `200 OK`
Returns the `IngredientResponse` object.

---

### Food Scanner & OCR Endpoints (Day 4)

#### `POST /api/products/scan` (also available as `POST /api/v1/products/scan`)
Uploads 1 or more food package label images (e.g. front label, ingredients list, nutrition table, allergen notice), validates files, applies OpenCV preprocessing (EXIF rotation, CLAHE, bilateral filter), executes OCR engine adapter (PaddleOCR / graceful fallback), and parses structured fields.

- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `files`: Array of image binary files (JPEG, PNG, WebP; max 10MB each).
  - `label_types` (optional): Form array or comma-separated list of image types: `"front"`, `"ingredients"`, `"nutrition"`, `"allergens"`, `"other"`.
- **Authentication**: Optional. If authenticated, scan is linked to the user's account.

##### Response `201 Created`
```json
{
  "id": "c1f7a2b9-0000-4000-8000-000000000001",
  "status": "extracted",
  "images": [
    {
      "filename": "label.jpg",
      "saved_filename": "c1f7a2b9_0_ingredients.jpg",
      "label_type": "ingredients",
      "url": "/api/scans/images/c1f7a2b9_0_ingredients.jpg",
      "size_bytes": 102400
    }
  ],
  "raw_ocr_text": "--- [INGREDIENTS LABEL] ---\nWhole Wheat Flour...",
  "extracted_data": {
    "product_name": "NutriChoice Digestive",
    "brand": "Britannia",
    "category": "Biscuits & Cookies",
    "serving_size": "2 biscuits (30g)",
    "raw_ingredients_text": "Whole Wheat Flour (50%), Edible Vegetable Oil...",
    "ingredients": [
      "Whole Wheat Flour (50%)",
      "Edible Vegetable Oil",
      "Sugar"
    ],
    "nutrition_facts": {
      "energy_kcal": 485.0,
      "total_fat_g": 21.0,
      "saturated_fat_g": 10.0,
      "trans_fat_g": 0.0,
      "carbohydrates_g": 66.0,
      "total_sugar_g": 15.0,
      "added_sugar_g": 13.0,
      "dietary_fibre_g": 6.0,
      "protein_g": 8.0,
      "sodium_mg": 450.0
    },
    "declared_allergens": ["Wheat", "Soy"],
    "precautionary_allergens": ["Milk", "Tree Nuts"],
    "ocr_confidence": 0.94,
    "ocr_engine": "paddleocr",
    "uncertainty_flags": [],
    "is_verified": false
  },
  "corrected_data": null,
  "product_id": null,
  "created_at": "2026-11-11T14:40:00Z",
  "updated_at": "2026-11-11T14:40:00Z"
}
```

---

#### `GET /api/scans/{id}` (also available as `GET /api/v1/scans/{id}`)
Retrieves scan session details, uploaded source images, raw OCR output, structured extraction, and any saved user corrections.

##### Response `200 OK`
Returns the `ScanResponse` object.

---

#### `PUT /api/scans/{id}/correction` (also available as `PUT /api/v1/scans/{id}/correction`)
Updates manual review overrides on extracted product attributes without finalizing to the product catalogue.

##### Request Body
```json
{
  "product_name": "Britannia NutriChoice Digestive High Fibre",
  "category": "Biscuits & Cookies",
  "ingredients": [
    "Whole Wheat Flour (50%)",
    "Palm Oil",
    "Sugar",
    "Iodised Salt"
  ],
  "nutrition_facts": {
    "energy_kcal": 485.0,
    "protein_g": 8.0
  }
}
```

##### Response `200 OK`
Returns updated `ScanResponse` with `status: "corrected"`. Original `extracted_data` remains preserved and distinct from `corrected_data`.

---

#### `POST /api/scans/{id}/confirm` (also available as `POST /api/v1/scans/{id}/confirm`)
Finalizes review and commits verified product attributes into the canonical catalogue tables (`products`, `nutrition_facts`, `product_ingredients`, `product_allergens`). Links the scan session to the created product.

##### Request Body
```json
{
  "product_name": "Britannia NutriChoice Digestive High Fibre",
  "brand": "Britannia",
  "category": "Biscuits & Cookies",
  "serving_size": "2 biscuits (30g)",
  "barcode": "8901063012345",
  "ingredients": [
    "Whole Wheat Flour (50%)",
    "Palm Oil",
    "Sugar",
    "Iodised Salt"
  ],
  "raw_ingredients_text": "Whole Wheat Flour (50%), Palm Oil, Sugar, Iodised Salt",
  "nutrition_facts": {
    "energy_kcal": 485.0,
    "total_fat_g": 21.0,
    "saturated_fat_g": 10.0,
    "trans_fat_g": 0.0,
    "carbohydrates_g": 66.0,
    "total_sugar_g": 15.0,
    "added_sugar_g": 13.0,
    "dietary_fibre_g": 6.0,
    "protein_g": 8.0,
    "sodium_mg": 450.0
  },
  "declared_allergens": ["Wheat", "Soy"],
  "precautionary_allergens": ["Milk", "Tree Nuts"]
}
```

##### Response `201 Created`
```json
{
  "message": "Product successfully verified and added to catalogue from food scan.",
  "scan_id": "c1f7a2b9-0000-4000-8000-000000000001",
  "product_id": "d2e8b1a4-1111-4000-8000-000000000002",
  "product": {
    "id": "d2e8b1a4-1111-4000-8000-000000000002",
    "name": "Britannia NutriChoice Digestive High Fibre",
    "brand": "Britannia",
    "category": "Biscuits & Cookies",
    "serving_size": "2 biscuits (30g)",
    "data_source": "scan",
    "is_verified": false
  }
}
```

---

#### `GET /api/scans/images/{filename}`
Safely serves uploaded scan images for in-browser visual verification and side-by-side inspection.

---

### Nutrition Analysis & Scoring Endpoints (Day 5)

#### `GET /api/products/{id}/analysis` (also available as `GET /api/v1/products/{id}/analysis`)
Calculates the deterministic NutriLens Nutrition Score (0–100) and complete nutritional evaluation for a catalogue product.

##### Response `200 OK`
```json
{
  "status": "complete",
  "product_id": "d2e8b1a4-1111-4000-8000-000000000002",
  "product_name": "Britannia NutriChoice Digestive",
  "score": 68,
  "grade": "B",
  "rating_label": "Good",
  "rating_color": "green",
  "standard_unit": "per_100g",
  "per_100_values": {
    "energy_kcal": 485.0,
    "total_fat_g": 21.0,
    "saturated_fat_g": 10.0,
    "trans_fat_g": 0.0,
    "carbohydrates_g": 66.0,
    "total_sugar_g": 15.0,
    "added_sugar_g": 13.0,
    "dietary_fibre_g": 6.0,
    "protein_g": 8.0,
    "sodium_mg": 450.0
  },
  "per_serving_values": {
    "energy_kcal": 145.5,
    "total_fat_g": 6.3,
    "saturated_fat_g": 3.0,
    "trans_fat_g": 0.0,
    "carbohydrates_g": 19.8,
    "total_sugar_g": 4.5,
    "added_sugar_g": 3.9,
    "dietary_fibre_g": 1.8,
    "protein_g": 2.4,
    "sodium_mg": 135.0
  },
  "serving_size_info": {
    "raw_text": "2 biscuits (30g)",
    "quantity": 30.0,
    "unit": "g",
    "standard_reference": "100g"
  },
  "data_completeness_pct": 100.0,
  "missing_critical_fields": [],
  "missing_optional_fields": [],
  "nutrition_summary": "This product (Good, Score 68/100) benefits from dietary fibre and protein source but requires attention for sugar content and saturated fat.",
  "score_explanation": "Calculated starting from a neutral baseline of 70 points. A total of 18.0 penalty points were deducted for elevated nutrient levels and 16.0 bonus points were awarded for beneficial dietary components, resulting in a final score of 68/100 (Grade B).",
  "positive_factors": [
    {
      "factor": "Dietary Fibre",
      "impact": "+9.0 pts",
      "description": "Provides 6.0g dietary fibre per 100g."
    },
    {
      "factor": "Protein Source",
      "impact": "+7.0 pts",
      "description": "Provides 8.0g protein per 100g."
    }
  ],
  "attention_factors": [
    {
      "factor": "Sugar Content",
      "impact": "-10.0 pts",
      "severity": "moderate",
      "description": "Contains 15.0g total sugar per 100g."
    },
    {
      "factor": "Saturated Fat",
      "impact": "-8.0 pts",
      "severity": "moderate",
      "description": "Contains 10.0g saturated fat per 100g."
    }
  ],
  "scoring_rule_version": "nutrilens-score-v1.0",
  "disclaimer": "The NutriLens Nutrition Score is an algorithmic educational reference calculated deterministically from declared nutritional values. It does not constitute an official FSSAI score, medical rating, or professional dietary advice."
}
```

---

#### `POST /api/analysis/score` (also available as `POST /api/v1/analysis/score`)
Calculates deterministic score and explanations for arbitrary nutritional inputs (e.g. food scan review, user custom simulation).

##### Request Body
```json
{
  "nutrients": {
    "energy_kcal": 380.0,
    "total_fat_g": 6.5,
    "saturated_fat_g": 1.2,
    "trans_fat_g": 0.0,
    "carbohydrates_g": 60.0,
    "total_sugar_g": 1.0,
    "dietary_fibre_g": 10.0,
    "protein_g": 13.0,
    "sodium_mg": 10.0
  },
  "category": "Breakfast Cereals",
  "serving_size": "40g"
}
```

##### Response `200 OK`
Returns `NutritionAnalysisResponse`. When critical fields are missing, returns `status: "insufficient_data"`, `score: null`, and lists `missing_critical_fields` without fabricating a score.

---

## 5. Error Structure Conventions
All error responses follow standard HTTP codes and provide informative error details:
```json
{
  "detail": "Descriptive error message"
}
```
Validation errors return field-level issues:
```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```
Authentication failures return HTTP `401 Unauthorized` with `WWW-Authenticate: Bearer` header.


---

## Day 6 Endpoints – Personalized Dietary Suitability

### `POST /api/products/{product_id}/suitability`
Evaluates a product against the authenticated user's dietary profile. The general NutriLens Nutrition Score is completely independent of this endpoint.

**Authentication**: Required (Bearer JWT).

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| `product_id` | UUID string | Product to evaluate |

**Request Body** (optional — overrides from stored profile):
```json
{
  "allergies": ["Peanuts"],
  "dietary_restrictions": ["Gluten-Free"],
  "dietary_preference": "Vegetarian",
  "nutrition_goals": ["Low Sugar"],
  "monitored_nutrients": ["Sodium", "Sugar"]
}
```

**Response `200 OK`**:
```json
{
  "status": "Declared restriction conflict",
  "status_label": "Declared restriction conflict",
  "badge_color": "rose",
  "is_suitable": false,
  "product_id": "...",
  "product_name": "NutriDemo Whole Wheat Digestive Biscuits",
  "summary_narrative": "This product contains declared Wheat allergen which conflicts with your declared restriction.",
  "evaluated_preferences": {
    "dietary_preference": "none",
    "allergies": ["Gluten / Wheat"],
    "dietary_restrictions": [],
    "nutrition_goals": [],
    "monitored_nutrients": []
  },
  "conflicts": [
    {
      "category": "allergen",
      "severity": "conflict",
      "title": "Allergen Conflict: Wheat",
      "detail": "Declared allergen 'Wheat' found in product ingredients.",
      "source_ingredient": "Wheat",
      "is_precautionary": false
    }
  ],
  "cautions": [],
  "positive_observations": [],
  "safety_warnings": [
    "Not detecting an allergen does not prove a product is allergen-free. Always verify with the manufacturer."
  ],
  "rules_applied": ["allergen_check", "restriction_check"],
  "engine_version": "nutrilens-suitability-v1.0",
  "disclaimer": "This assessment is not medical advice..."
}
```

**Status Values**:
| Status | Meaning | Badge Color |
|---|---|---|
| `Suitable based on available information` | No conflicts or cautions detected | `emerald` |
| `Caution` | Precautionary statements or ambiguous ingredients | `amber` |
| `Declared restriction conflict` | Hard conflict with declared allergy or restriction | `rose` |
| `Insufficient information` | Missing ingredient data prevents evaluation | `slate` |

**Error Responses**:
- `401 Unauthorized` — Not authenticated.
- `404 Not Found` — Product not found.

---

### `GET /api/profile/dietary-preferences`
Returns the authenticated user's current dietary preferences including monitored nutrients.

**Authentication**: Required (Bearer JWT).

**Response `200 OK`**:
```json
{
  "dietary_preference": "Vegetarian",
  "allergies": ["Peanuts", "Milk / Dairy"],
  "dietary_restrictions": ["Gluten-Free"],
  "nutrition_goals": ["High Protein", "Low Sugar"],
  "monitored_nutrients": ["Sugar", "Sodium", "Saturated Fat"],
  "updated_at": "2026-11-11T15:00:00Z"
}
```

**Error Responses**:
- `401 Unauthorized` — Not authenticated.

---

### `PUT /api/profile/dietary-preferences`
Updates the authenticated user's dietary preferences. Partial updates are supported.

**Authentication**: Required (Bearer JWT).

**Request Body** (all fields optional):
```json
{
  "dietary_preference": "Vegan",
  "allergies": ["Peanuts"],
  "dietary_restrictions": ["Halal"],
  "nutrition_goals": ["Weight Loss"],
  "monitored_nutrients": ["Sugar", "Sodium"]
}
```

**Response `200 OK`**: Returns the updated dietary preferences (same shape as GET response).

**Error Responses**:
- `401 Unauthorized` — Not authenticated.
- `422 Unprocessable Entity` — Validation errors.


---

## Day 7 Endpoints – Product Comparison & Alternative Recommendations

### `POST /api/products/compare`
Compares 2 to 6 products side-by-side with standardized unit normalization (per 100g / 100ml), missing value indicators, personal suitability evaluation, and user priority rankings.

**Authentication**: Optional (Bearer JWT). If authenticated, uses the user's stored dietary profile unless overridden in the request body.

**Request Body**:
```json
{
  "product_ids": [
    "product-uuid-1",
    "product-uuid-2"
  ],
  "priorities": [
    "lower_sugar",
    "lower_sodium",
    "higher_protein"
  ],
  "user_preferences": {
    "dietary_preference": "Vegetarian",
    "allergies": ["Peanuts"],
    "dietary_restrictions": ["Low-Sodium"]
  }
}
```

**Supported Priorities**:
- `lower_sugar`
- `lower_sodium`
- `lower_saturated_fat`
- `higher_protein`
- `higher_fibre`
- `fewer_restriction_conflicts`

**Response `200 OK`**:
```json
{
  "products": [
    {
      "product_id": "...",
      "name": "NutriDemo Classic Cola",
      "brand": "NutriDemo",
      "category": "Beverages",
      "serving_size": "355ml",
      "standard_unit": "per_100ml",
      "score": 35,
      "grade": "D",
      "rating_label": "Poor",
      "rating_color": "rose",
      "data_completeness_pct": 100.0,
      "nutrients_per_100": {
        "energy_kcal": 140.0,
        "total_sugar_g": 39.0,
        "added_sugar_g": 39.0,
        "total_fat_g": 0.0,
        "saturated_fat_g": 0.0,
        "trans_fat_g": 0.0,
        "sodium_mg": 45.0,
        "protein_g": 0.0,
        "dietary_fibre_g": 0.0,
        "carbohydrates_g": 39.0
      },
      "nutrients_per_serving": { ... },
      "missing_nutrients": [],
      "ingredients": ["Carbonated Water", "High Fructose Corn Syrup", ...],
      "allergens_declared": [],
      "allergens_precautionary": [],
      "suitability_status": "Suitable based on available information",
      "suitability_badge": "emerald",
      "suitability_conflicts": [],
      "price": null,
      "price_display": "Not declared"
    }
  ],
  "common_ingredients": ["Carbonated Water", "High Fructose Corn Syrup"],
  "common_allergens": [],
  "priorities_evaluated": ["lower_sugar", "higher_protein"],
  "priority_evaluations": [
    {
      "priority": "lower_sugar",
      "priority_label": "Lower Sugar",
      "best_product_id": "product-uuid-2",
      "best_product_name": "NutriDemo Diet Lemon Tea",
      "summary": "NutriDemo Diet Lemon Tea has the lowest sugar at 0.0g/per_100ml (39.0g or 100% less than NutriDemo Classic Cola).",
      "rankings": [
        {
          "product_id": "...",
          "product_name": "NutriDemo Diet Lemon Tea",
          "value": 0.0,
          "unit": "g",
          "rank": 1,
          "note": "0.0g sugar/per_100ml"
        }
      ]
    }
  ],
  "summary": "Overall, NutriDemo Diet Lemon Tea achieved the highest NutriLens score of 82/100 (Grade A)..."
}
```

**Error Responses**:
- `400 Bad Request` — Fewer than 2 products provided.
- `404 Not Found` — Products could not be found in the catalogue.

---

### `GET /api/products/{id}/alternatives`
Retrieves personalized, healthier alternative recommendations for a given target product from the actual catalogue.

**Authentication**: Optional (Bearer JWT). If authenticated, cross-checks candidate products against the user's dietary preferences and allergies to ensure safety.

**Path Parameters**:
| Parameter | Type | Description |
|---|---|---|
| `id` | UUID string | Target product ID to find alternatives for |

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `limit` | integer | `5` | Maximum number of alternative products to return (1-20) |
| `priorities` | string | `null` | Comma-separated priorities (e.g. `lower_sugar,higher_protein`) |

**Response `200 OK`**:
```json
{
  "target_product_id": "...",
  "target_product_name": "NutriDemo Classic Cola",
  "target_category": "Beverages",
  "target_score": 35,
  "applied_priorities": ["lower_sugar", "higher_protein"],
  "total_candidates_evaluated": 9,
  "alternatives": [
    {
      "product_id": "...",
      "name": "NutriDemo Diet Lemon Tea",
      "brand": "NutriDemo",
      "category": "Beverages",
      "serving_size": "250ml",
      "score": 82,
      "grade": "A",
      "rating_label": "Excellent",
      "rating_color": "emerald",
      "suitability_status": "Suitable based on available information",
      "suitability_badge": "emerald",
      "match_score": 142.0,
      "reasons": [
        "Higher NutriLens Score: 82/100 (+47 pts over NutriDemo Classic Cola)",
        "Direct category match (Beverages)",
        "Significantly lower sugar: 0.0g vs 39.0g per 100g"
      ],
      "nutritional_advantages": [
        "Contains 39.0g less sugar per 100g (-100%)",
        "Contains 25mg less sodium per 100g"
      ],
      "nutrients_per_100": { ... },
      "missing_nutrients": []
    }
  ]
}
```

**Error Responses**:
- `404 Not Found` — Target product not found in the catalogue.

---

## 8. Food Journal & Nutrition Analytics API (Day 8)

The Food Journal API tracks explicitly consumed food products, scales nutritional values proportionally to the logged weight, preserves missing nutrient values honestly, and provides longitudinal aggregations (daily summary with meal grouping, 7-day weekly trends, 30-day monthly overviews, and frequently consumed items) compared against user-configured dietary goals without inventing medical targets.

---

### `POST /api/journal` (also available as `POST /api/v1/journal`)
Logs an explicitly consumed packaged food product into the authenticated user's personal journal.

**Authentication**: Required (`Bearer <token>`).

**Request Body**:
```json
{
  "product_id": "3e8e61f8-d036-4a1b-9c2d-3e4f5a6b7c8d",
  "consumed_at": "2026-11-12T08:30:00Z",
  "meal_type": "breakfast",
  "quantity": 1.5,
  "serving_unit": "g",
  "serving_size_g": 30.0,
  "total_weight_g": 45.0,
  "notes": "With unsweetened almond milk"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `product_id` | UUID string | Yes | ID of the consumed product from the catalogue |
| `consumed_at` | ISO-8601 string | No | Consumption timestamp (defaults to current UTC time) |
| `meal_type` | string | No | `breakfast`, `lunch`, `dinner`, `snack`, `other` (defaults to `snack`) |
| `quantity` | float | No | Number of servings (defaults to 1.0) |
| `serving_unit` | string | No | Serving unit (`g`, `ml`, `serving`, defaults to `g`) |
| `serving_size_g` | float | No | Grams or ml per serving |
| `total_weight_g` | float | No | Explicit total grams consumed (defaults to `quantity * serving_size_g` or 100g) |
| `notes` | string | No | Optional user notes (max 200 chars) |

**Response `201 Created`**:
```json
{
  "id": "f6a3b2d1-c401-4e2a-8b3c-9d0e1f2a3b4c",
  "user_id": "...",
  "product_id": "3e8e61f8-d036-4a1b-9c2d-3e4f5a6b7c8d",
  "product_name": "NutriDemo Crunchy Granola",
  "product_brand": "NutriDemo",
  "product_category": "Breakfast Cereals",
  "product_image_url": null,
  "consumed_at": "2026-11-12T08:30:00Z",
  "meal_type": "breakfast",
  "quantity": 1.5,
  "serving_unit": "g",
  "serving_size_g": 30.0,
  "total_weight_g": 45.0,
  "notes": "With unsweetened almond milk",
  "nutrients": {
    "energy_kcal": 180.0,
    "total_fat_g": 6.75,
    "saturated_fat_g": 2.25,
    "trans_fat_g": null,
    "carbohydrates_g": 24.75,
    "total_sugar_g": 9.0,
    "added_sugar_g": 7.2,
    "dietary_fibre_g": 2.25,
    "protein_g": 4.5,
    "sodium_mg": 112.5,
    "missing_nutrients": ["Trans Fat"],
    "scale_factor": 0.45
  },
  "created_at": "...",
  "updated_at": "..."
}
```

---

### `GET /api/journal` (also available as `GET /api/v1/journal`)
Lists consumption entries strictly belonging to the authenticated user.

**Authentication**: Required (`Bearer <token>`).

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `date` | string | `null` | Filter by exact date (`YYYY-MM-DD`) |
| `start_date` | string | `null` | Filter entries on or after `YYYY-MM-DD` |
| `end_date` | string | `null` | Filter entries on or before `YYYY-MM-DD` |
| `meal_type` | string | `null` | Filter by meal type (`breakfast`, `lunch`, `dinner`, `snack`, `other`) |
| `page` | integer | `1` | Page number |
| `page_size` | integer | `20` | Items per page (max 100) |

---

### `GET /api/journal/summary/daily` (also available as `GET /api/v1/journal/summary/daily`)
Retrieves daily aggregated nutritional intake, meal groupings, and goal benchmark comparisons.

**Authentication**: Required (`Bearer <token>`).

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `date` | string | today | Target date (`YYYY-MM-DD`) |

**Response `200 OK`**:
```json
{
  "date": "2026-11-12",
  "total_entries": 3,
  "total_weight_g": 320.0,
  "meals": {
    "breakfast": {
      "meal_type": "breakfast",
      "label": "Breakfast",
      "entries": [ ... ],
      "total_calories": 300.0,
      "total_weight_g": 100.0
    },
    "lunch": { ... },
    "dinner": { ... },
    "snack": { ... },
    "other": { ... }
  },
  "totals": {
    "energy_kcal": { "total": 650.0, "unit": "kcal", "declared_items": 3, "missing_items": 0 },
    "total_sugar_g": { "total": 24.5, "unit": "g", "declared_items": 3, "missing_items": 0 },
    "sodium_mg": { "total": 420.0, "unit": "mg", "declared_items": 2, "missing_items": 1 }
  },
  "goal_progress": [
    {
      "goal_key": "low_sugar",
      "goal_label": "Low Sugar",
      "current_value": 24.5,
      "target_benchmark": 50.0,
      "unit": "g",
      "status": "on_track",
      "message": "Logged sugar (24.5g) is within standard general population reference limit (≤ 50g)."
    }
  ],
  "disclaimer": "NutriLens nutritional benchmarks reflect general population reference intakes and do not constitute medical advice, therapeutic prescriptions, or diagnostic recommendations."
}
```

---

### `GET /api/journal/analytics/weekly`
Computes 7-day longitudinal trends and daily average intake.

**Authentication**: Required (`Bearer <token>`).

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `end_date` | string | today | End of 7-day window (`YYYY-MM-DD`) |

---

### `GET /api/journal/analytics/monthly`
Computes 30-day daily breakdown and monthly summary metrics.

**Authentication**: Required (`Bearer <token>`).

---

### `GET /api/journal/analytics/frequent`
Retrieves user's most frequently logged packaged products with frequency count and total weight.

**Authentication**: Required (`Bearer <token>`).

---

### `PUT /api/journal/{id}` & `DELETE /api/journal/{id}`
Updates or deletes an existing journal entry owned by the authenticated user.


---

## Day 9 – Admin Dashboard & Knowledge Management APIs

> **Authorization**: All `/api/admin/*` endpoints require an authenticated user with `is_admin = true` or `role` in `["admin", "superadmin"]`. Normal authenticated users receive `403 FORBIDDEN`. Authorization is enforced at the backend API level regardless of frontend route access.

---

### `GET /api/admin/dashboard/stats`
Returns real-time platform statistics directly from the database.

**Authentication**: Required — Admin only.

**Response fields**:
| Field | Type | Description |
|---|---|---|
| `total_users` | integer | Registered consumer accounts |
| `total_products` | integer | Catalogued products |
| `total_ingredients` | integer | Canonical ingredient records |
| `total_scans` | integer | OCR scan sessions |
| `verified_products` | integer | Products marked `is_verified = true` |
| `unverified_products` | integer | Products pending verification |
| `pending_issues` | integer | User-reported issues awaiting admin review |
| `resolved_issues` | integer | Resolved issue reports |
| `total_issues` | integer | All submitted issue reports |
| `active_scoring_rule_version` | string | Currently active NutriLens scoring version |
| `category_breakdown` | object | Product count by category |

---

### `GET /api/admin/products`
Paginated, filterable list of all products for admin management.

**Authentication**: Required — Admin only.

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `search` | string | — | Filter by name, brand, or barcode |
| `category` | string | — | Filter by product category |
| `is_verified` | boolean | — | Filter by verification status |
| `page` | integer | 1 | Page number |
| `page_size` | integer | 20 | Items per page |

---

### `POST /api/admin/products`
Creates a new product with optional nutrition facts, ingredients, and allergens.

**Authentication**: Required — Admin only.

**Body fields**: `name` (required), `brand`, `category`, `barcode`, `description`, `serving_size`, `serving_unit`, `is_verified`, `image_url`, `nutrition_facts` (object), `ingredients` (array of `{name, order_index}`), `allergens` (array of `{name, declaration_type}`).

---

### `PUT /api/admin/products/{product_id}`
Updates all fields of an existing product record.

**Authentication**: Required — Admin only.

---

### `PATCH /api/admin/products/{product_id}/verify`
Toggles the `is_verified` status of a product.

**Authentication**: Required — Admin only.

**Body**: `{ "is_verified": true }`

---

### `DELETE /api/admin/products/{product_id}`
Permanently deletes a product and all associated nutrition facts, ingredient mappings, and allergen declarations.

**Authentication**: Required — Admin only.

---

### `GET /api/admin/ingredients`
Paginated ingredient taxonomy listing.

**Authentication**: Required — Admin only.

**Query Parameters**: `search`, `category`, `concern_level`, `page`, `page_size`.

---

### `POST /api/admin/ingredients`
Adds a new canonical ingredient entry.

**Authentication**: Required — Admin only.

**Body fields**: `name` (required), `category`, `description`, `concern_level` (`low`/`moderate`/`high`), `is_additive`, `ins_number`, `source_evidence`, `aliases` (string array).

Returns `409 CONFLICT` if an ingredient with the same name already exists.

---

### `PUT /api/admin/ingredients/{ingredient_id}`
Updates an existing canonical ingredient record.

**Authentication**: Required — Admin only.

---

### `DELETE /api/admin/ingredients/{ingredient_id}`
Removes an ingredient from the taxonomy registry.

**Authentication**: Required — Admin only.

---

### `GET /api/admin/allergens`
Returns all registered standard allergen categories.

**Authentication**: Required — Admin only.

---

### `POST /api/admin/allergens`
Registers a new standard allergen category.

**Authentication**: Required — Admin only.

**Body fields**: `name` (required), `code`, `description`.

---

### `GET /api/admin/scoring-rules`
Returns all NutriLens scoring rule versions (active and archived).

**Authentication**: Required — Admin only.

---

### `GET /api/admin/scoring-rules/{version_or_id}`
Returns the full thresholds, weights, and metadata for a specific rule version.

**Authentication**: Required — Admin only.

---

### `POST /api/admin/scoring-rules`
Creates a new immutable scoring rule version. All previous versions are preserved.

**Authentication**: Required — Admin only.

**Body fields**: `version` (required), `name` (required), `description`, `is_active`, `thresholds_food` (object), `thresholds_beverage` (object), `general_weights` (object), `category_weights` (object).

**Validation**: Thresholds must satisfy `low < moderate < high`. Weights must be positive. Returns `400 BAD REQUEST` on invalid configuration.

---

### `PUT /api/admin/scoring-rules/{rule_id}/activate`
Sets a specific scoring rule version as the active default for all new product analyses. Deactivates all other versions atomically.

**Authentication**: Required — Admin only.

---

### `POST /api/products/{product_id}/report-issue`
Allows any authenticated user to submit a data accuracy issue report for a product.

**Authentication**: Required — Any authenticated user.

**Body fields**:
| Field | Type | Required | Description |
|---|---|---|---|
| `issue_type` | string | Yes | Category: `incorrect_ingredients`, `inaccurate_nutrition`, `mislabeled_allergens`, `incorrect_barcode`, `ocr_error`, `other` |
| `description` | string | Yes | Detailed description of the discrepancy |
| `proposed_correction` | object | No | Optional structured correction data |

---

### `GET /api/admin/issues`
Returns all user-reported data issues with optional status filtering.

**Authentication**: Required — Admin only.

**Query Parameters**:
| Parameter | Type | Default | Description |
|---|---|---|---|
| `status` | string | — | Filter by `pending`, `reviewed`, `resolved`, or `rejected` |

---

### `PUT /api/admin/issues/{issue_id}`
Updates the status and optional audit notes for a reported issue.

**Authentication**: Required — Admin only.

**Body fields**:
| Field | Type | Required | Description |
|---|---|---|---|
| `status` | string | Yes | `pending`, `reviewed`, `resolved`, or `rejected` |
| `admin_notes` | string | No | Audit log entry explaining the resolution decision |

