# NutriLens – Database Schema & Architecture

## 1. Overview
NutriLens utilizes PostgreSQL as its primary transactional datastore, with full compatibility for Supabase PostgreSQL hosting as well as local Docker PostgreSQL instances.

## 2. Connection Strategy
- **Standard Driver**: `psycopg2-binary` for synchronous operations and Alembic migrations.
- **Async Driver**: `asyncpg` for high-throughput async endpoints.
- **Connection URL Format**:
  - Local Docker: `postgresql://nutrilens_user:nutrilens_password@localhost:5432/nutrilens_db`
  - Supabase Direct: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
  - Supabase Transaction Pooler (PgBouncer): `postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres`

## 3. Core Entities (Planned Schema Model)

### `users`
- `id` (UUID, Primary Key)
- `email` (VARCHAR, Unique, Indexed)
- `hashed_password` (VARCHAR)
- `full_name` (VARCHAR)
- `created_at` (TIMESTAMP WITH TIME ZONE)
- `updated_at` (TIMESTAMP WITH TIME ZONE)

### `user_dietary_profiles`
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> users.id)
- `allergies` (JSONB) - Declared allergens (e.g. peanuts, tree nuts, gluten)
- `dietary_patterns` (JSONB) - Preferences (e.g. vegan, vegetarian, halal, low-sodium)
- `health_conditions` (JSONB) - Goals & restrictions (e.g. diabetes, hypertension)
- `created_at` (TIMESTAMP WITH TIME ZONE)

### `products`
- `id` (UUID, Primary Key)
- `barcode` (VARCHAR, Nullable, Indexed)
- `name` (VARCHAR, Indexed)
- `brand` (VARCHAR, Nullable)
- `category` (VARCHAR, Nullable)
- `raw_ingredients_text` (TEXT)
- `serving_size` (VARCHAR, Nullable)
- `nutrients` (JSONB) - Calories, fat, saturated fat, sodium, sugar, fiber, protein per 100g/serving
- `declared_allergens` (JSONB) - Explicitly stated allergen warnings
- `precautionary_allergens` (JSONB) - "May contain" statements
- `nutrilens_score` (FLOAT) - Algorithmic quality rating
- `nutrilens_grade` (VARCHAR) - Grade indicator (A, B, C, D, E)
- `ocr_confidence` (FLOAT) - Confidence metric for transparency
- `source` (VARCHAR) - "scan", "manual", "curated"
- `created_at` (TIMESTAMP WITH TIME ZONE)

### `ingredients` (Canonical Registry)
- `id` (UUID, Primary Key)
- `canonical_name` (VARCHAR, Unique, Indexed)
- `synonyms` (JSONB)
- `ins_number` (VARCHAR, Nullable) - E-number / INS code
- `category` (VARCHAR) - "preservative", "emulsifier", "sweetener", etc.
- `concern_level` (VARCHAR) - "safe", "moderate", "high"
- `description` (TEXT)

### `consumption_logs` (Food Journal)
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key -> users.id, Indexed)
- `product_id` (UUID, Foreign Key -> products.id)
- `consumed_at` (TIMESTAMP WITH TIME ZONE)
- `serving_count` (FLOAT)
- `notes` (TEXT, Nullable)
- Note: Scanned products do NOT automatically populate this table; explicit user logging is required.
