# NutriLens – Architecture Documentation

## 1. System Architecture Overview
NutriLens adopts a decoupled client-server architecture with a clear separation of concerns across presentation, API routing, business/decision engines, persistence, and external services.

```
                      +---------------------------------------+
                      |       React + Vite Frontend (SPA)     |
                      | (TypeScript, Tailwind, shadcn/ui)     |
                      +-------------------+-------------------+
                                          |
                                   REST / JSON (Axios)
                                          |
                                          v
                      +-------------------+-------------------+
                      |         FastAPI Gateway & Core        |
                      |  - CORS & Middleware                  |
                      |  - JWT Authentication & Auth Guards   |
                      |  - Pydantic Request/Response Schemas  |
                      +-------------------+-------------------+
                                          |
          +-------------------------------+-------------------------------+
          |               |               |               |               |
          v               v               v               v               v
  +---------------+---------------+---------------+---------------+---------------+
  |  Food Scanner |  Ingredient   |    Scoring    |  Suitability  | Recommendation|
  |     Engine    |    Engine     |    Engine     |    Engine     |     Engine    |
  | (PaddleOCR &  | (Allergen &   | (Deterministic| (Personalized | (Tradeoffs &  |
  |  CV pipelines)| Additives)    |  NutriScores) |  Rules)       |  Alternatives)|
  +---------------+---------------+---------------+---------------+---------------+
          |               |               |               |               |
          +-------------------------------+-------------------------------+
                                          |
                                 SQLAlchemy 2.0 ORM
                                          |
                      +-------------------+-------------------+
                      |        PostgreSQL Persistence         |
                      |  (Supabase Hosted / Local Docker)     |
                      +---------------------------------------+
```

## 2. Layer Definitions

### Frontend Layer (`nutrilens/frontend`)
- **`components/ui`**: Reusable primitives built with Tailwind and Radix UI primitives.
- **`components/common`**: Application layout elements (Navbar, Footer, Shell).
- **`pages`**: Route views orchestrated via React Router.
- **`services`**: Network clients (Axios instance, React Query hooks).
- **`types`**: TypeScript interface definitions shared across views.
- **`utils`**: Helpers such as class names merging (`cn`).

### Backend Layer (`nutrilens/backend`)
- **`app/api`**: FastAPI routers exposing versioned endpoints (`/api/v1`) and root monitoring routes (`/api/health`).
- **`app/core`**: Configuration management (`Settings` with Pydantic), security utilities, and environment parsing.
- **`app/database`**: Database engine setup, connection pooling, and session dependency injection (`get_db`).
- **`app/models`**: SQLAlchemy declarative ORM models.
- **`app/schemas`**: Pydantic models for validation, serialization, and OpenAPI contract definition.
- **Engines**:
  - `app/food_scanner`: Image ingestion, preprocessing, PaddleOCR invocation, text layout parsing.
  - `app/ingredient_engine`: Dictionary-based ingredient tokenization, additive (INS/E-number) lookups, allergen matching.
  - `app/scoring_engine`: Explainable nutrient profiling algorithm.
  - `app/suitability_engine`: Condition-based dietary filters and flag generation.
  - `app/recommendation_engine`: Healthier alternative discovery within matching product categories.
- **`tests`**: Pytest automated test suites covering API contracts and rule engines.

### Data & Storage Layer
- **PostgreSQL**: Stores user profiles, dietary preferences, scanned product history, ingredient registries, and journal logs.
- **Supabase Storage**: Optional object storage for product label raw photography.
