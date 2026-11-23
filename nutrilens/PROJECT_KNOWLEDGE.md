# NutriLens – Comprehensive Project Architecture & Knowledge Base

> **Version:** 1.0.0 | **Author:** NutriLens Engineering Team | **Project Type:** Major Academic & Production Project

---

## 1. Executive Summary & Purpose

### 1.1 What is NutriLens?
**NutriLens** is an AI-powered, evidence-based food transparency and personalized nutrition intelligence platform. It bridges the gap between confusing, deceptive packaged food labels and health-conscious consumers. By scanning or photographing food packaging (nutrition facts tables, ingredients declarations, and front-of-pack branding), NutriLens automatically extracts, normalizes, audits, and interprets the data in real time.

### 1.2 Core Problems Solved
1. **Deceptive Food Marketing:** Consumers struggle to interpret marketing buzzwords (e.g., "healthy", "guilt-free", "natural", "diet") that often conceal excessive hidden sugars, saturated fats, sodium, or ultra-processed chemical additives.
2. **Complex Ingredient Declarations:** Chemical food additives, emulsifiers, artificial sweeteners, and preservatives are frequently listed under obscure INS/E-numbers (e.g., `INS 621` for Monosodium Glutamate, `INS 951` for Aspartame, `INS 102` for Tartrazine).
3. **Severe Food Allergies & Dietary Restrictions:** Individuals with celiac disease, peanut allergies, lactose intolerance, vegan preferences, or specific clinical goals (e.g., diabetes, hypertension) risk accidental consumption due to obscure allergen declarations or cross-contamination statements ("May contain traces of...").
4. **Indian & Global Food Label Variabilities:** Unlike US FDA labels with standard tabular layouts, Indian (FSSAI) food labels exhibit extreme formatting diversity (horizontal lines, truncated headers, `Per 100g` vs `Per serving` dual columns, bilingual labels, and inconsistent sodium/salt units).

---

## 2. Full Technology Stack

| Layer | Technologies & Libraries | Purpose & Key Highlights |
| :--- | :--- | :--- |
| **Frontend Framework** | **React 18**, **TypeScript**, **Vite** | Blazing-fast Single Page Application (SPA), strict typing, instant HMR |
| **Styling & UI Kit** | **Tailwind CSS**, **shadcn/ui**, **Lucide React** | Modern accessible UI, responsive layouts, dark/light themes |
| **Client State & Cache**| **TanStack React Query v5**, **Axios** | Declarative query caching, automatic retries, optimistic updates |
| **Routing** | **React Router DOM v6** | Client-side routing, protected routes for authenticated users |
| **Backend Framework** | **FastAPI** (Python 3.11.9), **Uvicorn** | High-throughput asynchronous REST API with automatic OpenAPI / Swagger |
| **Validation & Schema** | **Pydantic v2** | Request/response data validation, strict serialization, field filters |
| **ORM & Migrations** | **SQLAlchemy 2.0**, **Alembic** | Declarative data modeling, connection pooling, versioned migrations |
| **Primary Database** | **PostgreSQL** (Production / Supabase), **SQLite** (Dev) | Relational integrity, ACID compliance, JSONB for flexible nutrients |
| **OCR Engine** | **PaddleOCR** (PP-OCRv4 / v2.10.0) | High-accuracy scene text recognition, multi-language support |
| **Computer Vision** | **OpenCV (`cv2`)**, **Pillow (`PIL`)**, **NumPy** | EXIF rotation correction, CLAHE contrast enhancement, 2D geometry |
| **Multimodal Vision AI**| **Google Gemini Flash (2.0 / 1.5)**, **OpenAI GPT-4o-mini** | Visual reasoning fallback when OCR is occluded, truncated, or low-contrast |
| **Authentication** | **JWT (python-jose)**, **passlib (bcrypt)** | Stateless Bearer token auth, salted password hashing, 7-day sessions |
| **Deployment & Hosting**| **Render** (Backend), **Vercel** (Frontend) | Auto CI/CD from GitHub, cloud-native containerized architecture |

---

## 3. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Client["Frontend Client (React + TypeScript)"]
        UI[User Interface / Camera / File Upload]
        RQ[React Query & Axios Client]
        UI --> RQ
    end

    subgraph Gateway["API Gateway (FastAPI)"]
        CORS[CORS & Rate Limiting]
        AUTH[JWT Auth Guards & Dependency Injection]
        ROUTERS[API Routers /api/v1]
        RQ --> CORS --> AUTH --> ROUTERS
    end

    subgraph Pipeline["Food Scanner & OCR Pipeline"]
        PRE[Preprocessor: EXIF, 960px Scale, CLAHE]
        OCR[PaddleOCR Engine / Spatial 2D Clustering]
        VIS[Gemini / OpenAI Vision AI Fallback]
        EXT[Structured Information Extractor]
        ROUTERS --> PRE --> OCR --> EXT
        PRE -.-> VIS -.-> EXT
    end

    subgraph Engines["Core Analytical & Decision Engines"]
        SCORE[NutriLens Deterministic Scoring Engine]
        ING[Ingredient Intelligence & INS Additives Engine]
        SUIT[Personalized Dietary Suitability Matcher]
        COMP[Product Comparison & Recommendation Engine]
        JOURN[Food Diary & Journal Engine]
        EXT --> SCORE
        EXT --> ING
        EXT --> SUIT
    end

    subgraph Data["Persistence Layer"]
        ORM[SQLAlchemy 2.0 ORM]
        PG[(PostgreSQL / Supabase Database)]
        SCORE --> ORM
        ING --> ORM
        SUIT --> ORM
        COMP --> ORM
        JOURN --> ORM
        ORM --> PG
    end
```

---

## 4. Deep Dive: Core Engines & Subsystems

### 4.1 Food Scanner & OCR Extraction Pipeline (`food_scanner/`)
The food scanner takes an uploaded package photo or camera capture and converts it into structured, validated data.

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as React ScanFoodPage
    participant API as FastAPI /api/products/scan
    participant Pre as Image Preprocessor
    participant OCR as PaddleOCR Engine
    participant Ext as 2D Spatial Extractor
    participant Vis as Gemini Vision AI
    participant DB as PostgreSQL Database

    User->>Frontend: Select / capture photo of package
    Frontend->>Frontend: Client-side scale (max 1600px, JPEG 0.88)
    Frontend->>API: POST /api/products/scan (multipart/form-data)
    API->>Pre: validate_image_bytes() & preprocess_image()
    Note over Pre: Correct EXIF tilt, downscale to 960px (memory safety),<br/>apply CLAHE contrast & bilateral filtering
    API->>OCR: extract_text(preprocessed_img)
    Note over OCR: Run PP-OCRv4 detection & recognition.<br/>Calculate median camera tilt slope m = dy/dx.<br/>Cluster into visual horizontal rows.
    alt PaddleOCR successful
        OCR-->>API: OCRResult (spatially sorted lines, confidence > 85%)
        API->>Ext: extract_structured_label_info(lines)
        Note over Ext: 2D column matching: match labels (Energy, Sugar)<br/>with Per 100g and Per Serving values
    else OCR Low Confidence / No Nutrients
        API->>Vis: Parallel Gemini 2.0 Flash fallback
        Vis-->>API: Structured JSON (product, nutrients, ingredients)
        API->>Ext: Merge OCR + Vision data
    end
    API->>DB: Save ProductScan record with extracted JSON
    API-->>Frontend: 201 Created (Complete ScanSession payload)
    Frontend->>User: Render 6-Section Comprehensive Analysis Report
```

#### Key Innovations in the Extraction Pipeline:
1. **Camera Tilt-Compensated Row Reconstruction:**
   Handheld package photos are rarely perfectly level. The engine calculates the median tilt slope $m = \frac{\Delta y}{\Delta x}$ across adjacent horizontal text bounding boxes, adjusts line centers via $y_{\text{adj}} = y_c - m \cdot x_c$, and clusters them into true visual lines within a dynamic $\pm 12\text{px}$ threshold.
2. **2D Dual-Column Spatial Matching:**
   Food labels often declare nutrition in a grid:
   ```
   NUTRIENT       | PER 100g | PER SERVING (50g)
   Energy (kcal)  | 364      | 182
   Protein (g)    | 26.0     | 13.0
   ```
   Traditional 1D regex matches the first number it sees (often mixing up Per 100g and Per Serving). The NutriLens 2D Spatial Extractor uses horizontal $x$-coordinate bounding box columns to independently extract **both** `Per 100g` and `Per serving` values.
3. **FSSAI Truncation Resiliency:**
   Indian packaging frequently wraps or truncates words at margin boundaries. The parser contains specialized pattern recognizers for:
   - `(kcal)` or `GY(kcal)` $\rightarrow$ Energy
   - `N(g)` or `EIN(g)` $\rightarrow$ Protein
   - `HYDRATES(g)` $\rightarrow$ Carbohydrates
   - `SUGARS(g)` / `.DSUGARS(g)` $\rightarrow$ Total / Added Sugars
   - `ARY FIBRE (g)` $\rightarrow$ Dietary Fibre
   - `LFAT(g)` / `URATED FAT (g)` / `ANSFAT(g)` $\rightarrow$ Total / Saturated / Trans Fat
   - `ALSALT(g)` / `DIUM(mg)` $\rightarrow$ Salt / Sodium (with automatic salt-to-sodium conversion: $\text{Sodium} = \text{Salt} \times 400$).

---

### 4.2 Deterministic Nutrition Scoring Engine (`scoring_engine/`)
NutriLens rejects opaque, non-deterministic "black-box" AI scoring. Instead, it implements a transparent, evidence-based algorithm derived from international standards (Nutri-Score, WHO, and FSSAI guidelines).

#### Scoring Logic:
- **Scale:** Deterministic integer from **0 to 100**.
- **Letter Grades:**
  - **A (80–100):** Excellent nutritional quality (high protein/fiber, minimal sugar/sodium).
  - **B (65–79):** Good everyday choice.
  - **C (50–64):** Moderate nutritional quality; consume mindfully.
  - **D (35–49):** High in critical nutrients of concern (sugar, sat fat, sodium).
  - **E (0–34):** Ultra-processed or nutritionally depleted; limit intake.

#### Algorithmic Breakdown:
$$\text{NutriLens Score} = 70 - \text{Negative Points} + \text{Positive Points}$$

1. **Negative Points (Nutrients to Limit):**
   - **Energy Density:** High calories per 100g (penalties start $> 335\text{ kJ} / 80\text{ kcal}$).
   - **Total & Added Sugars:** Graded penalties starting at $> 4.5\text{g} / 100\text{g}$ up to $> 45\text{g} / 100\text{g}$.
   - **Saturated Fat:** Penalties scale from $> 1\text{g} / 100\text{g}$ to $> 10\text{g} / 100\text{g}$.
   - **Trans Fat:** Severe penalty for any declared trans fat $> 0.1\text{g}$.
   - **Sodium:** Penalties scale from $> 90\text{mg} / 100\text{g}$ ($0.225\text{g}$ salt) up to $> 900\text{mg} / 100\text{g}$.
2. **Positive Points (Nutrients to Encourage):**
   - **Dietary Fibre:** $+1$ to $+5$ points for fiber content from $0.9\text{g}$ to $> 4.7\text{g} / 100\text{g}$.
   - **Protein:** $+1$ to $+5$ points for protein content from $1.6\text{g}$ to $> 8.0\text{g} / 100\text{g}$.
3. **No-Guessing Principle:**
   If essential nutrients (energy, sugar, sodium, saturated fat) are missing from the label, NutriLens **never** assumes they are zero. Instead, it marks the score as `unavailable` or `insufficient_data` and explicitly tells the user which fields are required.

---

### 4.3 Ingredient Intelligence Engine (`ingredient_engine/`)
The ingredient engine tokenizes complex ingredient declarations, strips percentages and parentheses, and matches tokens against a canonical knowledge base.

#### Features:
- **High-Performance In-Memory Cache (`IngredientKnowledgeCache`):**
  Loads canonical ingredients at startup into multiple $O(1)$ hash maps:
  - `by_norm`: Normalized lower-case names.
  - `by_ins`: INS/E-number codes (e.g., `500II`, `621`, `322`).
  - `by_alias`: Common trade and alternative names.
  - `substring_list`: Substring matching for compound ingredients.
- **Additive Recognition & Purpose Explanations:**
  Explains what each additive does in plain language (e.g., *"INS 322 (Lecithin): Emulsifier derived from soy or sunflower, prevents oil and water separation"*).
- **Concern Classification:**
  Tags ingredients as **Safe**, **Moderate Concern** (e.g., artificial sweeteners like Sucralose, Acesulfame K), or **High Concern** (e.g., hydrogenated vegetable oils, partially hydrogenated fats, Potassium Bromate).
- **Allergen Cross-Referencing:**
  Identifies mandatory allergens (Milk, Eggs, Peanuts, Tree Nuts, Wheat/Gluten, Soy, Fish, Crustaceans, Sesame, Mustard, Sulphites).

---

### 4.4 Personalized Dietary Suitability Engine (`suitability_engine/`)
Unlike generic calorie counters, NutriLens compares food items against the authenticated user's individual profile:

```mermaid
flowchart LR
    A[Extracted Food Data] --> M{Suitability Matcher}
    B[User Dietary Profile] --> M

    subgraph User Profile
        B1[Dietary Pattern: Vegan, Vegetarian, Halal]
        B2[Allergies: Peanuts, Gluten, Dairy]
        B3[Restrictions: Low-Sodium, Low-Sugar]
        B4[Goals: High-Protein, Heart-Health]
    end

    M --> O1[Suitable: Safe to consume]
    M --> O2[Caution: Potential risk / precautionary]
    M --> O3[Conflict: Explicit allergen or diet violation]
    M --> O4[Insufficient Info: Missing label data]
```

#### Decision Rules:
1. **Allergen Conflict (Severity: Critical):** Triggers if any declared ingredient matches the user's saved allergen list (e.g., Whey Powder for a Dairy-allergic user).
2. **Precautionary Allergen Caution (Severity: Warning):** Triggers if the label declares "May contain traces of [Allergen]".
3. **Dietary Restriction Conflict (Severity: High):**
   - E.g., Gelatin, Carmine (INS 120), or Bone Phosphate in a Vegetarian or Vegan profile.
   - High sodium ($> 400\text{mg} / 100\text{g}$) for a user with Hypertension / Low-Sodium restrictions.
   - High added sugar ($> 10\text{g} / 100\text{g}$) for a user with Diabetes / Low-Sugar restrictions.
4. **Nutritional Goal Alignment (Severity: Positive):**
   - E.g., $> 15\text{g}$ protein per serving flags *"Aligns with your High-Protein goal"*.
   - $> 6\text{g}$ dietary fiber flags *"Supports your Digestive Health goal"*.

---

### 4.5 Product Comparison & Recommendation Engine (`comparison_engine/`)
Enables side-by-side evaluation of up to 4 products simultaneously:
- **Radar & Bar Charts:** Visual comparison of calories, sugars, fats, fiber, and protein.
- **Smart Recommendations:** When viewing a low-scoring product (Grade D or E), the engine queries the catalogue for products in the exact same category with higher NutriLens scores (Grade A or B) and identical dietary suitability.

---

### 4.6 Food Journal & Daily Intake Engine (`journal_engine/`)
Allows users to maintain a daily nutritional log:
- Logs specific portion sizes (e.g., $1.5 \times \text{serving}$).
- Aggregates daily caloric intake, total sugar, saturated fat, sodium, and protein against WHO recommended daily limits.
- Provides interactive historical charts showing 7-day and 30-day nutrition trends.

---

## 5. Database Schema & Architecture

```mermaid
erDiagram
    USERS ||--o| USER_PROFILES : "has one"
    USERS ||--o{ PRODUCT_SCANS : "uploads"
    USERS ||--o{ FOOD_JOURNAL_ENTRIES : "logs"
    PRODUCTS ||--o| NUTRITION_FACTS : "has one"
    PRODUCTS ||--o{ PRODUCT_INGREDIENTS : "contains"
    INGREDIENTS ||--o{ PRODUCT_INGREDIENTS : "references"
    PRODUCTS ||--o{ PRODUCT_ALLERGENS : "declares"
    ALLERGENS ||--o{ PRODUCT_ALLERGENS : "references"
    PRODUCTS ||--o{ FOOD_JOURNAL_ENTRIES : "recorded in"

    USERS {
        uuid id PK
        string email UK
        string hashed_password
        string full_name
        int age
        boolean is_active
        boolean is_admin
        timestamp created_at
    }

    USER_PROFILES {
        uuid id PK
        uuid user_id FK
        string dietary_preference
        jsonb allergies
        jsonb dietary_restrictions
        jsonb nutrition_goals
        jsonb monitored_nutrients
    }

    PRODUCT_SCANS {
        uuid id PK
        uuid user_id FK
        string status
        jsonb images
        text raw_ocr_text
        jsonb extracted_data
        jsonb corrected_data
        uuid product_id FK
        timestamp created_at
    }

    PRODUCTS {
        uuid id PK
        string name
        string brand
        string barcode UK
        string category
        string serving_size
        float nutrilens_score
        string nutrilens_grade
        text ingredients_text
        string image_url
        string source
    }

    NUTRITION_FACTS {
        uuid id PK
        uuid product_id FK
        float calories
        float total_fat
        float saturated_fat
        float trans_fat
        float carbohydrates
        float total_sugars
        float added_sugars
        float dietary_fiber
        float protein
        float sodium
        string basis
    }

    INGREDIENTS {
        uuid id PK
        string name UK
        string normalized_name
        string ins_number
        string category
        string concern_level
        string purpose
        boolean is_common_allergen
        text description
    }

    FOOD_JOURNAL_ENTRIES {
        uuid id PK
        uuid user_id FK
        uuid product_id FK
        float servings_consumed
        string meal_type
        timestamp logged_at
    }
```

---

## 6. Complete API Reference

### 6.1 Authentication & Profile Endpoints
| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Public | Create user, initialize dietary profile, return JWT |
| `POST` | `/api/auth/login` | Public | Verify credentials, return signed JWT token |
| `GET` | `/api/auth/me` | User | Retrieve current user profile and dietary preferences |
| `PUT` | `/api/auth/profile` | User | Update dietary preferences, allergies, and nutrition goals |
| `POST` | `/api/auth/logout` | User | Terminate session / invalidate token client-side |

### 6.2 Food Scanner Endpoints
| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/products/scan` | Optional Auth | Upload 1+ images, execute OCR + vision extraction, return analysis report |
| `GET` | `/api/scans/{id}` | Optional Auth | Retrieve full scan details, extracted facts, and scores |
| `PUT` | `/api/scans/{id}/correction` | User | Save manual corrections to extracted nutrition or ingredients |
| `POST` | `/api/scans/{id}/confirm` | User | Confirm scan and save product into public catalogue |
| `GET` | `/api/scans/history` | User | Retrieve paginated chronological scan history of authenticated user |
| `GET` | `/api/scans/images/{filename}` | Public | Serve uploaded scan images and lightweight thumbnails |

### 6.3 Catalogue & Product Endpoints
| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/products` | Public | Search, filter, and paginate verified product catalogue |
| `GET` | `/api/products/{id}` | Public | Detailed product view with full nutritional profile and alternatives |
| `POST` | `/api/products` | Admin | Create curated product in catalogue |
| `GET` | `/api/products/compare` | Public | Compare 2 to 4 products side-by-side with trade-off analysis |

### 6.4 Analytics & Food Journal Endpoints
| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/journal` | User | List food journal logs for a given date or date range |
| `POST` | `/api/journal` | User | Add a product and serving count to food diary |
| `DELETE`| `/api/journal/{id}` | User | Remove an entry from food diary |
| `GET` | `/api/journal/summary` | User | Aggregate daily totals (calories, sugar, sodium, protein) vs RDA limits |

### 6.5 System & Diagnostic Endpoints
| Method | Path | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Public | System health check (database connection, API status) |
| `POST` | `/api/scans/debug-ocr` | Dev/Admin | Directly inspect raw OCR text and bounding boxes for debugging |

---

## 7. Frontend Architecture & Report Layout

The frontend is organized around modern React best practices with Tailwind CSS and Radix UI:

### 7.1 Key Pages
1. **`ScanFoodPage.tsx`**: The core scanning interface. Supports drag-and-drop image upload, live camera capture, multi-image merging (e.g., front of pack + nutrition table), client-side optimization, and renders the **Food Label Analysis Report**.
2. **`FoodCataloguePage.tsx`**: Searchable product catalogue with category pills, NutriLens score filters, and allergen badges.
3. **`ProductDetailPage.tsx`**: Comprehensive product overview with interactive radar charts and health alternative suggestions.
4. **`CompareProductsPage.tsx`**: Side-by-side product comparisons highlighting key nutrient differences.
5. **`FoodJournalPage.tsx`**: Daily meal tracker with visual progress bars against daily nutrient limits.
6. **`ProfilePage.tsx`**: Dietary preference manager where users configure allergies, diets, and goals.

### 7.2 The 6-Section Food Label Analysis Report
When an image is scanned, `ScanFoodPage.tsx` renders six independent, resilient sections:
- **Section A: Product Information** — Brand, product name, serving size, and uploaded image preview.
- **Section B: NutriLens Nutritional Score** — Big letter grade badge (A–E), numerical score (0–100), and breakdown of positive/negative scoring factors.
- **Section C: Nutrition Facts Breakdown** — Dual-column table displaying both `Per 100g` and `Per Serving` values for 10 critical nutrients with traffic-light indicators.
- **Section D: Ingredient Intelligence & Safety** — Comprehensive list of ingredients, parsed INS additive cards with purpose descriptions, and flagged concerns.
- **Section E: Personalized Dietary Suitability** — Clear suitability badge (`Suitable`, `Caution`, or `Restriction Conflict`) based on the logged-in user's dietary profile.
- **Section F: OCR Quality & Uncertainty Audit** — Diagnostic audit showing OCR engine used, confidence percentage, raw detected text, and uncertainty warnings.

> **Report Independence Guarantee:**
> Each section is decoupled. A missing product name does not block nutrition scoring; a missing nutrition table does not block ingredient analysis; and partial nutrition data is always displayed rather than withheld.

---

## 8. Root Cause Analysis of Common Scanning Issues & Fixes

### Issue 1: "Analysis is taking longer than expected / Timeout Error"
- **Cause:** When running on free-tier cloud platforms (e.g., Render), the container spins down after 15 minutes of inactivity. When a scan request arrives, the container undergoes a "cold start" (taking 40–50 seconds), while PaddleOCR downloads/loads model weights into memory. This exceeds standard 15-second browser timeouts.
- **Resolution:**
  1. Frontend timeout for `/api/products/scan` was increased to **120 seconds** (`api.ts`).
  2. Implemented non-blocking background OCR pre-warming during FastAPI startup (`lifespan` in `main.py`). The health check answers `200 OK` immediately, keeping the container alive.
  3. Image dimensions are capped at 960px prior to inference to avoid RAM spikes and out-of-memory container crashes.

### Issue 2: "FALLBACKOCR Engine Used & 0% Confidence"
- **Cause:**
  1. On memory-constrained servers, if `import paddleocr` or model initialization threw an unhandled exception, `get_ocr_engine()` fell back to `FallbackOCREngine` and cached it as a global singleton.
  2. If the user accidentally uploaded a screenshot of the web report itself (rather than a food package photo), the parser found no nutrition table, returning 0 detected nutrients.
- **Resolution:**
  1. Wrapped PaddleOCR initialization with robust version detection (supporting both 2.x and 3.x APIs).
  2. Added multimodal Vision AI fallback (Google Gemini 2.0 Flash): if OCR confidence is $< 60\%$ or detects no nutrients, the system automatically uses Gemini to extract structured facts directly from the image.

### Issue 3: "Inverted Sodium / Salt Calculations"
- **Cause:** Indian food labels list "Total Salt (g)" while international guidelines evaluate "Sodium (mg)". Some labels list sodium directly in mg. Multiplying an already-mg number by 400 resulted in astronomical sodium values (e.g., 52,000mg).
- **Resolution:**
  Added sanity guards in `extractor.py`: values $> 15$ in a salt field are recognized as already being in milligrams and are not multiplied.

---

## 9. Local Development & Deployment Guide

### 9.1 Local Environment Setup

#### Prerequisites:
- Python 3.11.x (installed and on PATH)
- Node.js 18+ & npm
- Git

#### 1. Backend Setup:
```powershell
# Navigate to backend directory
cd Major_Project\nutrilens\backend

# Activate the virtual environment
.\venv\Scripts\activate

# Install dependencies (if not already installed)
pip install -r requirements.txt

# Verify database migrations
alembic upgrade head

# Start the FastAPI development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
*API will be available at:* `http://localhost:8000` (Swagger docs at `http://localhost:8000/api/v1/docs`).

#### 2. Frontend Setup:
```powershell
# Navigate to frontend directory
cd Major_Project\nutrilens\frontend

# Install dependencies
npm install

# Verify environment file (.env)
# VITE_API_BASE_URL=http://localhost:8000

# Start Vite dev server
npm run dev
```
*Frontend will be available at:* `http://localhost:5173`.

---

### 9.2 Production Deployment Architecture

```
                      +-----------------------------+
                      |   Vercel (Frontend CDN)     |
                      |   nutrilens.vercel.app      |
                      +--------------+--------------+
                                     |
                       HTTPS Requests (/api/*)
                                     |
                                     v
                      +-----------------------------+
                      |   Render (Backend Service)  |
                      |   FastAPI + Uvicorn         |
                      |   (Docker / Python 3.11)    |
                      +--------------+--------------+
                                     |
                                     v
                      +-----------------------------+
                      |  Supabase (Cloud PostgreSQL)|
                      |  Managed DB with PgBouncer  |
                      +-----------------------------+
```

#### Production Environment Variables Required:
**Backend (`.env` on Render):**
```ini
PROJECT_NAME="NutriLens API"
ENVIRONMENT="production"
DEBUG=False
DATABASE_URL="postgresql://user:password@aws-0-ap-south-1.pooler.supabase.com:6543/postgres"
SECRET_KEY="<strong-random-32-character-secret-key>"
BACKEND_CORS_ORIGINS='["https://nutrilens.vercel.app", "http://localhost:5173"]'
GEMINI_API_KEY="<your-google-ai-studio-api-key>"
```

**Frontend (`.env.production` on Vercel):**
```ini
VITE_API_BASE_URL=https://nutrilens-backend.onrender.com
```

---

## 10. Automated Testing & Quality Assurance

NutriLens maintains an extensive automated test suite covering all critical services:
```powershell
cd Major_Project\nutrilens\backend
pytest tests/ -v
```
**Test Coverage Summary:**
- **128 Total Tests Passed (100% Pass Rate)**
- `test_auth.py`: User registration, password hashing, JWT creation, token expiry, protected route guards.
- `test_food_scanner.py`: Image validation, thumbnail generation, OCR line parsing, FSSAI truncation handling.
- `test_scoring_engine.py`: Deterministic score calculations across categories, edge cases (zero sugar, high sodium, pure oil).
- `test_suitability_engine.py`: Allergen conflict detection, dietary preference matching (vegan, gluten-free, low-sodium).
- `test_comparison.py`: Multi-product radar comparisons and healthier alternative queries.
- `test_journal.py`: Meal logging, serving multipliers, and daily nutritional aggregation.

---

## 11. Conclusion & Academic Defense Highlights

When presenting or demonstrating NutriLens:
1. **Emphasize Deterministic AI vs Hallucinatory LLMs:** NutriLens does not ask an LLM to guess a health score. It uses computer vision to extract verifiable printed packaging facts and evaluates them through transparent, reproducible mathematical algorithms.
2. **Highlight Indian Packaging Adaptability:** Standard OCR models trained on US FDA labels fail on Indian packages. NutriLens's tilt compensation, FSSAI truncation regex, and dual-column spatial clustering solve real-world packaging challenges.
3. **Safety First:** The platform strictly adheres to the principle of never inventing missing nutrients as zero and clearly distinguishing between declared allergens and precautionary ("may contain") statements.
