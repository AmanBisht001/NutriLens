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

## 4. Error Structure Conventions
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
