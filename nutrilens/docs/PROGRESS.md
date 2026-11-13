# NutriLens – Development Progress Tracking

## Project Status: Day 2 Complete (Authentication, User Profiles & App Layout)
- **Current Milestone**: Day 2 – Backend Authentication, User Profiles, Frontend Authentication, and Main Application Shell
- **Status**: Completed & Verified

---

## Day 2 Completion Checklist

- [x] **User can register**: `POST /api/auth/register` creates user and profile; frontend `/register` provides registration flow with validation.
- [x] **User can log in**: `POST /api/auth/login` verifies credentials and issues signed JWT; frontend `/login` page securely authenticates users.
- [x] **Passwords are securely hashed**: Implemented salted bcrypt hashing (`bcrypt.gensalt()`, `bcrypt.hashpw()`, `bcrypt.checkpw()`); raw passwords never persist.
- [x] **JWT authentication works**: Access tokens signed using `HS256` with configurable expiry and claims; verified via `HTTPBearer` security dependency.
- [x] **Protected routes work**: Frontend `ProtectedRoute` guards all dashboard and interior pages, automatically redirecting unauthenticated requests to `/login`.
- [x] **User profile can be created and updated**: Model `UserProfile` stores full profile data; editable via `PUT /api/auth/profile` and `/profile` page.
- [x] **Dietary preferences and allergies are stored**: Dietary preference, food allergies, dietary restrictions, and personal nutrition goals stored in PostgreSQL/JSON datastore.
- [x] **Dashboard layout is responsive**: Responsive sidebar with collapsible mobile navigation drawer, welcome section, quick scan CTA, empty states for recently scanned products and nutrition summary without fabricated statistics.
- [x] **Logout works**: Frontend clears session from localStorage; `POST /api/auth/logout` endpoint confirms termination.
- [x] **Authentication API tests pass**: 15 of 15 automated pytest tests passing across auth registration, password hashing, invalid credentials, token verification, profile updating, and system health.
- [x] **Progress documentation is updated**: `docs/PROGRESS.md` and `docs/API_DOCUMENTATION.md` fully updated.

---

## Day 1 Completion Checklist (Preserved)

- [x] **Project Structure**: Created `nutrilens/` with `frontend/`, `backend/`, `docs/`, `docker-compose.yml`, and `README.md`.
- [x] **Frontend Folder Organization**: Structured into `components/ui`, `components/common`, `pages/`, `layouts/`, `hooks/`, `services/`, `context/`, `types/`, `utils/`, `lib/`.
- [x] **Backend Folder Organization**: Structured into `app/api`, `app/models`, `app/schemas`, `app/services`, `app/core`, `app/database`, `app/food_scanner`, `app/ingredient_engine`, `app/scoring_engine`, `app/suitability_engine`, `app/recommendation_engine`, and `tests/`.
- [x] **Frontend Configuration**: React 18, Vite, TypeScript, Tailwind CSS with NutriLens emerald palette, shadcn/ui components, React Router v6.
- [x] **Backend Configuration**: FastAPI with CORS, SQLAlchemy 2.0 connection engine, Pydantic v2 settings, Alembic, Pytest.
- [x] **Health Check Endpoints**: `GET /api/health` and versioned `GET /api/v1/health`.

---

## Test Execution Results (Day 2)

### 1. Backend Automated Pytest Suite
Command:
```powershell
cd nutrilens\backend
.\venv\Scripts\pytest -v
```
Output:
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-8.4.2, pluggy-1.7.0
rootdir: C:\Users\baman\OneDrive\Desktop\Major_Project\nutrilens\backend
configfile: pytest.ini
testpaths: tests
plugins: anyio-4.16.0, platformdirs-4.14.3, asyncio-0.26.0, mock-3.17.0
collected 15 items

tests/test_auth.py::test_password_hashing PASSED                         [  6%]
tests/test_auth.py::test_register_user_success PASSED                    [ 13%]
tests/test_auth.py::test_register_duplicate_email PASSED                 [ 20%]
tests/test_auth.py::test_register_validation_error PASSED                [ 26%]
tests/test_auth.py::test_login_success PASSED                            [ 33%]
tests/test_auth.py::test_login_invalid_password PASSED                   [ 40%]
tests/test_auth.py::test_login_nonexistent_user PASSED                   [ 46%]
tests/test_auth.py::test_get_current_user_me PASSED                      [ 53%]
tests/test_auth.py::test_get_current_user_unauthorized PASSED            [ 60%]
tests/test_auth.py::test_update_user_profile PASSED                      [ 66%]
tests/test_auth.py::test_logout PASSED                                   [ 73%]
tests/test_auth.py::test_versioned_auth_endpoints PASSED                 [ 80%]
tests/test_health.py::test_root_endpoint PASSED                          [ 86%]
tests/test_health.py::test_api_health_endpoint PASSED                    [ 93%]
tests/test_health.py::test_api_v1_health_endpoint PASSED                 [100%]

======================== 15 passed, 1 warning in 68.62s =======================
```

### 2. Frontend Production Build Check
Command:
```powershell
cd nutrilens\frontend
npm run build
```
Output:
```text
> nutrilens-frontend@0.1.0 build
> tsc --noEmit && vite build

vite v5.4.21 building for production...
✓ 1737 modules transformed.
dist/index.html                   0.84 kB │ gzip:   0.48 kB
dist/assets/index-DRg68wk0.css   35.18 kB │ gzip:   6.51 kB
dist/assets/index-BSpVpDyk.js   485.52 kB │ gzip: 146.67 kB
✓ built in 11.53s
```

---

## Files Created & Modified on Day 2

### Backend (`nutrilens/backend/`)
- `requirements.txt`: Added `pyjwt`, `bcrypt`, `email-validator`.
- `app/core/security.py`: Password hashing with bcrypt, JWT token creation and decoding.
- `app/models/user.py`: `User` and `UserProfile` SQLAlchemy models (`users`, `user_dietary_profiles`).
- `app/models/__init__.py`: Exported User and UserProfile.
- `app/schemas/user.py`: Pydantic models for register, login, profile update, token response.
- `app/schemas/__init__.py`: Exported user schemas.
- `app/api/deps.py`: `get_db`, `get_current_user` Bearer validator, `get_current_active_user`.
- `app/api/v1/endpoints/auth.py`: Registration, login, profile edit, logout routes.
- `app/api/v1/api.py`: Mounted auth router under `/auth`.
- `app/main.py`: Mounted direct `/api/auth` routes and graceful table initialization lifespan.
- `tests/conftest.py`: In-memory SQLite transaction fixtures for test isolation.
- `tests/test_auth.py`: Comprehensive test suite with 12 unit and integration tests.

### Frontend (`nutrilens/frontend/`)
- `src/types/index.ts`: User, UserProfile, RegisterPayload, LoginPayload, ProfileUpdatePayload types.
- `src/services/api.ts`: Token storage, Bearer request interceptor, 401 response interceptor, auth API methods.
- `src/context/AuthContext.tsx`: React AuthContext provider and `useAuth` hook.
- `src/components/common/ProtectedRoute.tsx`: Route guard redirecting unauthenticated users to `/login`.
- `src/layouts/AppLayout.tsx`: Authenticated shell with responsive sidebar (Dashboard, Scan Food, Food Catalogue, Compare Products, My Food Journal, Nutrition Analytics, My Profile, Logout) and mobile drawer.
- `src/pages/RegisterPage.tsx`: Registration page with form validation, password visibility toggle, allergy and dietary goal onboarding.
- `src/pages/LoginPage.tsx`: Login page with validation, password toggle, session expiry notifications, redirect handling.
- `src/pages/ProfilePage.tsx`: Dietary profile management with name, age, dietary preference, allergy safeguards, restrictions, and personal nutrition goals.
- `src/pages/DashboardPage.tsx`: Responsive dashboard with personalized greeting, quick scan CTA, empty states without fabricated statistics, and dietary safeguards snapshot.
- `src/pages/ScanFoodPage.tsx`: Milestone target for upcoming food scanner.
- `src/pages/FoodCataloguePage.tsx`: Milestone target for upcoming catalogue.
- `src/pages/CompareProductsPage.tsx`: Milestone target for upcoming product comparison.
- `src/pages/FoodJournalPage.tsx`: Milestone target for upcoming food journaling.
- `src/pages/NutritionAnalyticsPage.tsx`: Milestone target for upcoming analytics.
- `src/components/common/Navbar.tsx`: Integrated auth awareness (Dashboard & Profile links when logged in; Sign In & Register buttons when logged out).
- `src/App.tsx`: App routing configuration with public landing and protected dashboard routes.

### Documentation (`docs/`)
- `docs/API_DOCUMENTATION.md`: Documented all authentication and profile endpoints.
- `docs/PROGRESS.md`: Updated with Day 2 completion checklist, test logs, and file ledger.

---

## How to Run Day 2 Application

### Running Backend Server
```powershell
cd nutrilens\backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --reload
```
- API Documentation: `http://localhost:8000/api/v1/docs`
- Health Endpoint: `http://localhost:8000/api/health`

### Running Frontend Application
```powershell
cd nutrilens\frontend
npm run dev
```
- Web Application: `http://localhost:5173`
- Register Account: `http://localhost:5173/register`
- Login: `http://localhost:5173/login`
- Dashboard: `http://localhost:5173/dashboard`
- Profile Settings: `http://localhost:5173/profile`
