# NutriLens – Architecture & Technical Decisions Record (ADR)

## ADR-001: Monorepo Directory Organization
- **Date**: Day 1
- **Status**: Accepted
- **Context**: The project requires modular separation between frontend, backend, business logic engines, automated tests, and documentation.
- **Decision**: Structured the repository under `nutrilens/` with distinct directories for `frontend/` (React + TypeScript SPA), `backend/` (FastAPI with isolated engine packages), `docs/` (living design records), `docker-compose.yml`, and root configuration files.
- **Consequence**: Clear isolation of concerns, independent containerization, and clean CI/CD boundaries.

## ADR-002: Deterministic Rule Engines over LLM Generation for Nutrition & Allergen Facts
- **Date**: Day 1
- **Status**: Accepted
- **Context**: Food safety and health recommendations cannot tolerate generative hallucinations.
- **Decision**: All ingredient matching, allergen detection, nutritional scoring, and suitability checks will be executed strictly through deterministic backend rule engines, dictionary lookups, and documented thresholds.
- **Consequence**: 100% explainable, reproducible, and verifiable results with zero risk of fabricated values.

## ADR-003: Distinction of Declared Allergens vs. Precautionary Statements
- **Date**: Day 1
- **Status**: Accepted
- **Context**: Package labels differentiate between confirmed ingredients and cross-contamination warnings.
- **Decision**: Schema and engine separate `declared_allergens` ("Contains X") from `precautionary_allergens` ("May contain X / manufactured on equipment...").
- **Consequence**: Accurate risk assessment avoiding false certainty.

## ADR-004: Explicit Logging Requirement for Food Journal
- **Date**: Day 1
- **Status**: Accepted
- **Context**: Scanning a packaged food product does not necessarily mean the consumer ingested it.
- **Decision**: Products scanned will be stored in product catalog/scan history, but never auto-logged to `consumption_logs`. Users must explicitly record consumption amount and timestamp.
- **Consequence**: High-integrity nutrition journal data without accidental clutter.

## ADR-005: Supabase PostgreSQL Compatibility with Local Docker Fallback
- **Date**: Day 1
- **Status**: Accepted
- **Context**: Development requires seamless local testing without mandatory cloud access, while production leverages Supabase PostgreSQL.
- **Decision**: Standard SQLAlchemy 2.0 with connection pooling and standard PostgreSQL syntax is maintained. A complete `docker-compose.yml` provides a local PostgreSQL 16 container, while `.env.example` documents Supabase connection strings.
- **Consequence**: Zero lock-in and friction-free development.
