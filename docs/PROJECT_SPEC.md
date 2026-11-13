# NutriLens – Final Product Specification & Feature Reference

## 1. Executive Summary & Vision
**NutriLens** is a packaged-food intelligence platform engineered as a final-year B.Tech Major Project. The platform bridges the gap between opaque food packaging declarations and everyday consumer health decisions. By processing food packaging photographs through computer vision and deterministic rule-based algorithms, NutriLens decodes nutrition facts, standardized ingredients, allergen declarations, and personalized dietary alignments without relying on generative AI hallucinations.

---

## 2. Core Architectural Principles
1. **Explainable Determinism**: Nutrition scores, allergen flags, and dietary suitability results are generated exclusively using reproducible, mathematical rule engines.
2. **Honest Data Handling**: Missing nutrient data is preserved as `None` or marked as "Not Declared"; the system never invents numbers or assumes absent nutrients are zero.
3. **Declared vs. Precautionary Separation**: Explicit allergens (e.g., "Contains: Milk, Wheat") are strictly distinguished from advisory facility statements (e.g., "May contain traces of tree nuts").
4. **Intentional Consumption Logging**: Scanning a product never logs it as consumed. Food journaling requires explicit user confirmation with confirmed portions.
5. **Non-Medical Boundary**: All outputs are informational and analytical. NutriLens never claims a product is "100% safe" or provides medical diagnosis/treatment recommendations.
6. **Strict RBAC & API Enforcement**: Administrative controls are enforced at the backend API level (`require_admin_user`) regardless of frontend URL manipulation.

---

## 3. Comprehensive Feature Modules

### 3.1 Authentication & Profile Management (Days 1–2)
- **Security**: Salted bcrypt password hashing with HS256 JWT access tokens (10080 min expiry).
- **User Attributes**: Email, full name, age, account status, role (`user` vs `admin`).
- **Dietary Profile**: Dietary preference (`None`, `Vegetarian`, `Vegan`, `Halal`, `Jain`), declared food allergies (array of allergens), dietary restrictions (array of strict boundaries), nutrition goals (array of goals), and monitored nutrients.

### 3.2 Product Catalogue & Ingredient Taxonomy (Day 3)
- **Catalogue Schema**: Products with barcode (GTIN/EAN-13), brand, name, category, package size, serving size, and raw label text.
- **Nutrition Facts**: Standardized to per 100g or per 100ml. Calories, total fat, saturated fat, trans fat, cholesterol, carbohydrates, total sugar, added sugar, dietary fibre, protein, sodium, calcium, iron, vitamin C.
- **Canonical Ingredient Registry**: Additive flags, INS/E-numbers, concern levels (`low`, `moderate`, `high`), scientific source citations, and synonym aliases.
- **Allergen Registry**: Standard international allergen classes with declared vs. precautionary mappings.

### 3.3 Food-Label Scanning Pipeline (Day 4)
- **Input Channels**: Multi-image file upload or browser camera capture (`navigator.mediaDevices.getUserMedia`).
- **Validation**: Strict 10MB limit, format verification (JPEG, PNG, WebP), dimension and header validation.
- **Preprocessing**: OpenCV EXIF rotation, CLAHE contrast enhancement, bilateral edge-preserving smoothing.
- **OCR Engine Adapter**: Pluggable interface supporting PaddleOCR, Fallback OCR, and Mock OCR for testing.
- **Structured Extractor**: Rule-based regex extraction of product title, brand, nutrition tables, ingredient sequences, and allergen declarations.
- **Review & Confirm**: Interactive UI allows editing OCR readings before committing to the live database.

### 3.4 Deterministic Nutrition Scoring Engine (Day 5)
- **Score Range**: 0 to 100 NutriLens Score with Letter Grade (A, B, C, D, E).
- **Category-Aware Weighting**: Calibrated rules across Beverages, Biscuits & Cookies, Breakfast Cereals, Dairy, Snacks & Namkeen, Chocolates & Sweets, Instant Foods, and General Foods.
- **Penalties**: High sugar, sodium, saturated fat, and trans fats (severe deduction).
- **Bonuses**: Dietary fibre, protein, and low energy density.
- **Completeness Guard**: Missing critical macronutrients triggers `status: "insufficient_data"` and withholds score calculation.
- **Traceable Narrative**: Clear score explanations, positive factors (`+pts`), and attention factors (`-pts`).

### 3.5 Personalized Dietary Suitability (Day 6)
- **Independence Principle**: Separate backend service (`/api/products/{id}/suitability`). General NutriLens score remains identical regardless of who views it.
- **Four Result Statuses**:
  1. `Suitable based on available information`
  2. `Caution`
  3. `Declared restriction conflict`
  4. `Insufficient information`
- **Safety Safeguards**: Missing ingredient lists trigger uncertainty warnings. "May contain" warnings produce `Caution`, never a hard conflict.

### 3.6 Product Comparison & Healthier Alternatives (Day 7)
- **Multi-Product Matrix**: Side-by-side comparison of 2 to 6 products with normalized metrics per 100g/ml.
- **User Priorities**: Dynamic ranking by `lower_sugar`, `lower_sodium`, `lower_saturated_fat`, `higher_protein`, `higher_fibre`, or `fewer_restriction_conflicts`.
- **Alternative Recommendations**: Catalogue-driven engine suggesting healthier products in the same category, verifying higher scores, and excluding declared user allergens with traceable reasons.

### 3.7 Food Consumption Journal & Analytics (Day 8)
- **Consumption Logging**: Explicit user action with product, date, meal type (Breakfast, Lunch, Dinner, Snack, Other), quantity, and grams/ml.
- **Proportional Scaling**: Intake calculated as `(total_weight_g / 100.0) * per_100_val`. E.g., consuming 50g yields exactly 50% of nutrient values.
- **Analytics Visualizations**: Recharts Area and Bar dashboards for 7-day weekly trends, 30-day monthly overviews, and top frequent foods.
- **Goal Progress**: Compares intake against user goals using general dietary benchmarks (WHO / ICMR-NIN).

### 3.8 Admin Dashboard & Knowledge Management (Day 9)
- **Role-Based Access Control**: `require_admin_user` protects all `/api/admin/*` endpoints (`403 FORBIDDEN` for non-admins).
- **Live Statistics**: Actual database counts (users, products, ingredients, scans, verified ratio, issue counts).
- **Product & Ingredient CRUD**: Full administrative editing, verification toggle, allergen bindings.
- **Scoring Rule Versioning**: Configurable thresholds and factor weights stored with version strings (`nutrilens-score-v1.0`). All previous versions preserved immutably.
- **Community Issue Queue**: User-reported inaccuracies reviewed, audited, and resolved.

---

## 4. Technology Stack Specifications
- **Frontend**: React 18.3, TypeScript 5.5, Vite 5.4, Tailwind CSS 3.4, shadcn/ui design tokens, React Router 6.26, TanStack Query 5.56, Recharts 2.12, Lucide React.
- **Backend**: Python 3.11, FastAPI 0.115, SQLAlchemy 2.0.36, Pydantic v2.9, Alembic 1.13, Pytest 8.3, Uvicorn, Pillow, OpenCV (cv2), PaddleOCR.
- **Database**: PostgreSQL 16 (compatible with Supabase PostgreSQL and local Docker).
- **Deployment**: Vercel (Frontend), Render / AWS / Docker (Backend), Supabase (Database & Storage).
