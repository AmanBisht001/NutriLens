"""
NutriLens – Food Journal & Analytics Schemas (Day 8)
Pydantic models for logging consumption, calculating scaled nutrients,
and producing daily, weekly, and monthly nutritional aggregates.
"""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field


class CalculatedNutrients(BaseModel):
    """
    Nutrients scaled proportionally to the actual consumed weight (total_weight_g / 100g).
    Missing / undeclared nutrient values are preserved as None to prevent false accuracy.
    """
    energy_kcal: Optional[float] = None
    total_fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    cholesterol_mg: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    total_sugar_g: Optional[float] = None
    added_sugar_g: Optional[float] = None
    dietary_fibre_g: Optional[float] = None
    protein_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    calcium_mg: Optional[float] = None
    iron_mg: Optional[float] = None
    vitamin_c_mg: Optional[float] = None
    missing_nutrients: List[str] = Field(default_factory=list)
    scale_factor: float = 1.0


class JournalEntryCreate(BaseModel):
    product_id: str
    consumed_at: Optional[datetime] = None
    meal_type: str = "snack"  # breakfast | lunch | dinner | snack | other
    quantity: float = Field(default=1.0, gt=0)
    serving_unit: str = "g"
    serving_size_g: Optional[float] = Field(default=None, gt=0)
    total_weight_g: Optional[float] = Field(default=None, gt=0)
    notes: Optional[str] = None


class JournalEntryUpdate(BaseModel):
    consumed_at: Optional[datetime] = None
    meal_type: Optional[str] = None
    quantity: Optional[float] = Field(default=None, gt=0)
    serving_unit: Optional[str] = None
    serving_size_g: Optional[float] = Field(default=None, gt=0)
    total_weight_g: Optional[float] = Field(default=None, gt=0)
    notes: Optional[str] = None


class JournalEntryResponse(BaseModel):
    id: str
    user_id: str
    product_id: str
    product_name: str
    product_brand: Optional[str] = None
    product_category: Optional[str] = None
    product_image_url: Optional[str] = None
    consumed_at: datetime
    meal_type: str
    quantity: float
    serving_unit: str
    serving_size_g: Optional[float] = None
    total_weight_g: float
    notes: Optional[str] = None
    nutrients: CalculatedNutrients
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class JournalEntryListResponse(BaseModel):
    items: List[JournalEntryResponse]
    total: int
    page: int
    page_size: int


class DailyMealGroup(BaseModel):
    meal_type: str
    label: str
    entries: List[JournalEntryResponse]
    total_calories: float = 0.0
    total_weight_g: float = 0.0


class NutrientTotalDetail(BaseModel):
    total: Optional[float] = None
    unit: str
    declared_items: int
    missing_items: int


class GoalProgressItem(BaseModel):
    goal_key: str
    goal_label: str
    current_value: Optional[float] = None
    target_benchmark: Optional[float] = None
    unit: str
    status: str  # on_track | caution | exceeded | info
    message: str


class DailyJournalSummaryResponse(BaseModel):
    date: str
    total_entries: int
    total_weight_g: float
    meals: Dict[str, DailyMealGroup]
    totals: Dict[str, NutrientTotalDetail]
    goal_progress: List[GoalProgressItem]
    disclaimer: str


class DailyTrendItem(BaseModel):
    date: str
    day_name: str
    entry_count: int
    calories: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    protein_g: Optional[float] = None
    fibre_g: Optional[float] = None
    fat_g: Optional[float] = None
    carbs_g: Optional[float] = None


class WeeklyAnalyticsResponse(BaseModel):
    start_date: str
    end_date: str
    daily_trends: List[DailyTrendItem]
    averages: Dict[str, Optional[float]]
    active_days: int
    total_logged_meals: int
    disclaimer: str


class MonthlyAnalyticsResponse(BaseModel):
    year: int
    month: int
    start_date: str
    end_date: str
    daily_trends: List[DailyTrendItem]
    averages: Dict[str, Optional[float]]
    active_days: int
    total_logged_meals: int
    disclaimer: str


class FrequentProductItem(BaseModel):
    product_id: str
    product_name: str
    product_brand: Optional[str] = None
    product_category: Optional[str] = None
    product_image_url: Optional[str] = None
    log_count: int
    total_weight_g: float
    last_consumed_at: datetime


class FrequentProductsResponse(BaseModel):
    items: List[FrequentProductItem]
