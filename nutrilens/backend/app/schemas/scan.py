"""
NutriLens – Food Scanner Pydantic Schemas (Day 4)
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ScanImageInfo(BaseModel):
    filename: str
    label_type: str = Field(
        ...,
        description="One of: 'front', 'ingredients', 'nutrition', 'allergens', 'other'",
    )
    file_path: Optional[str] = None
    url: Optional[str] = None


class NutritionFactsData(BaseModel):
    energy_kcal: Optional[float] = None
    total_fat_g: Optional[float] = None
    saturated_fat_g: Optional[float] = None
    trans_fat_g: Optional[float] = None
    carbohydrates_g: Optional[float] = None
    total_sugar_g: Optional[float] = None
    added_sugar_g: Optional[float] = None
    dietary_fibre_g: Optional[float] = None
    protein_g: Optional[float] = None
    sodium_mg: Optional[float] = None


class ExtractedProductData(BaseModel):
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    serving_size: Optional[str] = None
    raw_ingredients_text: Optional[str] = None
    ingredients: List[str] = Field(default_factory=list)
    nutrition_facts: NutritionFactsData = Field(default_factory=NutritionFactsData)
    declared_allergens: List[str] = Field(default_factory=list)
    precautionary_allergens: List[str] = Field(default_factory=list)
    ocr_confidence: float = 0.0
    ocr_engine: str = "fallback"
    uncertainty_flags: List[str] = Field(default_factory=list)
    is_verified: bool = False


class ScanCorrectionRequest(BaseModel):
    """Payload when user edits extracted fields before confirmation."""
    product_name: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    serving_size: Optional[str] = None
    raw_ingredients_text: Optional[str] = None
    ingredients: Optional[List[str]] = None
    nutrition_facts: Optional[NutritionFactsData] = None
    declared_allergens: Optional[List[str]] = None
    precautionary_allergens: Optional[List[str]] = None


class ScanConfirmRequest(BaseModel):
    """Payload to finalize scan and commit to the Product catalogue."""
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = "Snacks & Namkeen"
    serving_size: Optional[str] = "100g"
    barcode: Optional[str] = None
    ingredients: List[str] = Field(default_factory=list)
    raw_ingredients_text: Optional[str] = None
    nutrition_facts: Optional[NutritionFactsData] = None
    declared_allergens: List[str] = Field(default_factory=list)
    precautionary_allergens: List[str] = Field(default_factory=list)


class ScanResponse(BaseModel):
    id: str
    status: str
    images: List[Dict[str, Any]] = Field(default_factory=list)
    raw_ocr_text: Optional[str] = None
    extracted_data: Optional[Dict[str, Any]] = None
    corrected_data: Optional[Dict[str, Any]] = None
    product_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ScanConfirmResponse(BaseModel):
    message: str
    scan_id: str
    product_id: str
    product: Dict[str, Any]
