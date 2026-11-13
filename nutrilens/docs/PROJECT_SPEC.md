# NutriLens – Project Specification

## 1. Project Overview
**NutriLens** is a personalized food intelligence and nutrition decision platform developed as a final-year B.Tech major project. It enables consumers to decode packaged food labels by capturing or uploading product labels, extracting nutritional facts and ingredients, scoring nutritional quality via transparent deterministic models, evaluating personalized dietary suitability, comparing alternatives, and maintaining an intentional consumption journal.

## 2. Core Pillars & Architectural Principles
1. **Explainable Intelligence**: Nutrition scoring, ingredient parsing, allergen detection, and suitability matching are implemented using transparent, rule-based algorithms. LLMs are never permitted to hallucinate nutritional numbers, allergen warnings, or safety scores.
2. **Strict Data Traceability**: Every analytical outcome links back to extracted OCR facts, declared package values, or explicit scientific guidelines.
3. **Uncertainty Awareness**: When OCR resolution or package information is partial or ambiguous, uncertainty indicators are displayed rather than synthetic inferences.
4. **Declared vs. Precautionary Separation**: Explicit allergens (e.g., "Contains Soy") are strictly distinguished from advisory statements (e.g., "May contain traces of gluten").
5. **Intentional Consumption Logging**: Scanned items do not automatically enter the food journal; journal entries require explicit user confirmation.
6. **Educational Scope**: NutriLens evaluations are educational and analytical, distinct from statutory FSSAI certifications or formal medical counsel.

## 3. Technology Stack
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui design tokens, React Router v6, Axios, TanStack Query v5, React Hook Form, Zod, Recharts, Lucide React.
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, JWT Authentication, OpenCV, PaddleOCR.
- **Database & Storage**: PostgreSQL (Supabase-ready & Docker-ready), Supabase Storage for label image assets.
- **Testing & Tooling**: Pytest, Vitest/TSC checks, Docker Compose.

## 4. Platform Modules
- **Food Scanner & Label Extractor**: OCR pipeline parsing ingredient lists and nutrition tables.
- **Ingredient & Allergen Engine**: Normalization, additive categorization (E-numbers), declared vs. precautionary allergen checks.
- **Nutritional Scoring Engine**: Multi-metric evaluation (macronutrient density, sodium/sugar thresholds, positive fiber/protein balances).
- **Dietary Suitability Engine**: Rule-based matching against user profiles (e.g., diabetic-friendly, hypertension, gluten-free, vegan).
- **Comparison & Recommendation Engine**: Side-by-side product tradeoffs and healthier category alternatives.
- **Food Journal & Analytics**: User-initiated consumption tracking with macro aggregation.
