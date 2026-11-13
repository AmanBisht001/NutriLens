from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================================
# Profile Schemas
# ============================================================================

class UserProfileBase(BaseModel):
    dietary_preference: str = Field(default="None", description="Primary dietary pattern (e.g. Vegetarian, Vegan, Keto)")
    allergies: List[str] = Field(default_factory=list, description="Declared allergens to flag")
    dietary_restrictions: List[str] = Field(default_factory=list, description="Dietary restrictions (e.g. Halal, Low-Sodium)")
    nutrition_goals: List[str] = Field(default_factory=list, description="Personal nutrition targets")
    monitored_nutrients: List[str] = Field(default_factory=list, description="Nutrients the user wishes to monitor specifically")


class UserProfileUpdate(BaseModel):
    dietary_preference: Optional[str] = None
    allergies: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    nutrition_goals: Optional[List[str]] = None
    monitored_nutrients: Optional[List[str]] = None
    monitored_nutrients: Optional[List[str]] = None


class DietaryPreferencesPayload(BaseModel):
    dietary_preference: Optional[str] = "None"
    allergies: Optional[List[str]] = Field(default_factory=list)
    dietary_restrictions: Optional[List[str]] = Field(default_factory=list)
    nutrition_goals: Optional[List[str]] = Field(default_factory=list)
    monitored_nutrients: Optional[List[str]] = Field(default_factory=list)


class DietaryPreferencesResponse(BaseModel):
    dietary_preference: str
    allergies: List[str]
    dietary_restrictions: List[str]
    nutrition_goals: List[str]
    monitored_nutrients: List[str]
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserProfileBase):
    id: str
    user_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=1, le=120)


class UserRegister(UserBase):
    password: str = Field(..., min_length=6, max_length=128, description="Password (at least 6 characters)")
    dietary_preference: Optional[str] = "None"
    allergies: Optional[List[str]] = Field(default_factory=list)
    dietary_restrictions: Optional[List[str]] = Field(default_factory=list)
    nutrition_goals: Optional[List[str]] = Field(default_factory=list)
    monitored_nutrients: Optional[List[str]] = Field(default_factory=list)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=1, le=120)
    dietary_preference: Optional[str] = None
    allergies: Optional[List[str]] = None
    dietary_restrictions: Optional[List[str]] = None
    nutrition_goals: Optional[List[str]] = None
    monitored_nutrients: Optional[List[str]] = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    age: Optional[int] = None
    role: str = "user"
    is_admin: bool = False
    is_active: bool = True
    profile: Optional[UserProfileResponse] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None
