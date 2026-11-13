# NutriLens – Personalized Food Intelligence & Nutrition Decision Platform

NutriLens is a final-year B.Tech major project designed to decode packaged food labels through explainable backend intelligence, deterministic allergen safety checks, nutrient scoring, personalized dietary suitability matching, and intentional consumption logging.

---

## Technology Stack

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui design tokens, React Router v6, Axios, TanStack Query v5, React Hook Form, Zod, Recharts, Lucide React.
- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0, Pydantic v2, Alembic, JWT Authentication, OpenCV, PaddleOCR.
- **Database & Storage**: PostgreSQL (compatible with Supabase PostgreSQL and local Docker), Supabase Storage for label image assets.
- **Testing & Deployment**: Pytest, Vitest/TSC, Docker Compose.

---

## Project Structure

```text
nutrilens/
├── frontend/                     # React + Vite TypeScript SPA
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/               # Reusable shadcn/ui components (button, card, badge, etc.)
│   │   │   └── common/           # Common components (Navbar, Footer)
│   │   ├── pages/                # Route pages (HomePage, NotFoundPage)
│   │   ├── layouts/              # Layout wrappers (RootLayout)
│   │   ├── hooks/                # Custom React hooks
│   │   ├── services/             # Axios API client & TanStack Query integrations
│   │   ├── context/              # React context providers
│   │   ├── types/                # TypeScript interface definitions
│   │   ├── utils/                # Utilities (cn, helpers)
│   │   ├── App.tsx               # Root app & route configuration
│   │   └── main.tsx              # React DOM entrypoint
│   ├── .env.example              # Frontend environment variables example
│   └── package.json
│
├── backend/                      # FastAPI Python Service
│   ├── app/
│   │   ├── api/                  # API routers (v1 endpoints)
│   │   ├── core/                 # Config (Pydantic Settings), security
│   │   ├── database/             # SQLAlchemy engine, session maker, base
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic validation & serialization schemas
│   │   ├── services/             # Application services
│   │   ├── food_scanner/         # OCR & computer vision label parsing engine
│   │   ├── ingredient_engine/    # Additive & allergen detection engine
│   │   ├── scoring_engine/       # Deterministic nutrition scoring engine
│   │   ├── suitability_engine/   # Personalized dietary suitability engine
│   │   ├── recommendation_engine/# Tradeoff & healthier alternatives engine
│   │   └── main.py               # FastAPI application entrypoint
│   ├── tests/                    # Pytest automated test suites
│   ├── alembic.ini               # Database migrations configuration
│   ├── requirements.txt          # Production dependencies
│   ├── requirements-dev.txt      # Testing & dev dependencies
│   └── .env.example              # Backend environment variables example
│
├── docs/                         # Project Documentation
│   ├── PROJECT_SPEC.md           # Product & system specification
│   ├── ARCHITECTURE.md           # System architecture & engine design
│   ├── PROGRESS.md               # Daily development progress log
│   ├── API_DOCUMENTATION.md      # REST API contracts & schemas
│   ├── DATABASE_SCHEMA.md        # Database entities & PostgreSQL setup
│   └── DECISIONS.md              # Architectural Decision Records (ADRs)
│
├── docker-compose.yml            # Local PostgreSQL, backend, & frontend containers
└── README.md
```

---

## Quick Start Guide

### 1. Prerequisites
- **Node.js**: v20+ and npm
- **Python**: 3.11+
- **Docker & Docker Compose** *(Optional for local PostgreSQL)*

---

### 2. Backend Setup

```bash
cd nutrilens/backend

# Create and activate virtual environment
python -m venv venv

# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt -r requirements-dev.txt

# Configure environment variables
cp .env.example .env

# Run FastAPI backend with live reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API Base URL: `http://localhost:8000`
- Interactive Swagger UI: `http://localhost:8000/api/v1/docs`
- Health Check: `http://localhost:8000/api/health`

---

### 3. Frontend Setup

```bash
cd nutrilens/frontend

# Configure environment variables
cp .env.example .env

# Install dependencies
npm install

# Start Vite development server
npm run dev
```

- Frontend Web App: `http://localhost:5173`

---

### 4. Running with Docker Compose (Local Database Option)

To spin up a local PostgreSQL 16 container, FastAPI backend, and Vite frontend together:

```bash
cd nutrilens
docker-compose up -d db
```

Or run the complete stack:
```bash
docker-compose up --build
```

---

### 5. Running Automated Tests

#### Backend Pytest:
```bash
cd nutrilens/backend
.\venv\Scripts\pytest -v
```

#### Frontend Typecheck & Build:
```bash
cd nutrilens/frontend
npm run build
```

---

## Supabase PostgreSQL Configuration

To connect NutriLens to Supabase:
1. Create a Supabase project at [supabase.com](https://supabase.com).
2. Retrieve your Connection String under **Project Settings -> Database -> Connection string (URI)**.
3. Update `nutrilens/backend/.env`:
   ```env
   DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
   ```
4. Optional: Add Supabase Storage credentials for image persistence:
   ```env
   SUPABASE_URL="https://your-project-ref.supabase.co"
   SUPABASE_KEY="your-anon-or-service-role-key"
   SUPABASE_STORAGE_BUCKET="product-labels"
   ```
