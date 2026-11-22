"""
NutriLens – Food Scanner Pydantic Schemas (Day 4)
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, model_validator
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
    analysis: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

    @model_validator(mode="before")
    @classmethod
    def resolve_analysis_field(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("analysis"):
                corr = data.get("corrected_data") or {}
                extr = data.get("extracted_data") or {}
                data["analysis"] = corr.get("analysis") or extr.get("analysis")
            return data
        # For ORM object
        current_val = getattr(data, "analysis", None)
        if current_val is None:
            corr = getattr(data, "corrected_data", None) or {}
            extr = getattr(data, "extracted_data", None) or {}
            analysis_val = corr.get("analysis") or extr.get("analysis")
            try:
                setattr(data, "analysis", analysis_val)
            except Exception:
                pass
        return data


class ScanConfirmResponse(BaseModel):
    message: str
    scan_id: str
    product_id: str
    product: Dict[str, Any]


class ScanHistoryItem(BaseModel):
    id: str
    product_name: str
    brand: Optional[str] = None
    category: Optional[str] = None
    created_at: Optional[datetime] = None
    status: str
    score: Optional[int] = None
    grade: Optional[str] = None
    rating_label: Optional[str] = None
    rating_color: Optional[str] = None
    image_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    ocr_confidence: float = 0.0
    ocr_engine: str = "paddleocr"
    is_scoreable: bool = False


class ScanHistoryResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: List[ScanHistoryItem]
