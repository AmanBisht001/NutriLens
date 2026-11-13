"""
NutriLens – Food Scanner Models (Day 4)
Covers: ProductScan
"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ProductScan(Base):
    """
    Stores an uploaded food package scan session:
    source images, raw OCR text, structured parsed fields, user corrections,
    and reference to the resulting Product record once confirmed.
    """
    __tablename__ = "product_scans"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(
        String(30), nullable=False, default="extracted"
    )  # "uploaded" | "processing" | "extracted" | "corrected" | "confirmed" | "failed"

    # List of uploaded image records:
    # [{"filename": "...", "label_type": "ingredients|nutrition|front|allergens", "file_path": "..."}]
    images = Column(JSON, nullable=False, default=list)

    # Raw extracted text per image or combined
    raw_ocr_text = Column(Text, nullable=True)

    # Structured extraction output:
    # {
    #   "product_name": "...",
    #   "brand": "...",
    #   "category": "...",
    #   "serving_size": "...",
    #   "ingredients": ["wheat flour", "sugar", ...],
    #   "raw_ingredients_text": "...",
    #   "nutrition_facts": {"energy_kcal": 450, ...},
    #   "declared_allergens": ["Gluten", "Milk"],
    #   "precautionary_allergens": ["Tree Nuts"],
    #   "ocr_confidence": 0.88,
    #   "ocr_engine": "paddleocr|fallback|mock",
    #   "uncertainty_flags": ["Serving size not detected", ...]
    # }
    extracted_data = Column(JSON, nullable=True)

    # User edited fields (overrides for extracted_data)
    corrected_data = Column(JSON, nullable=True)

    # Linked product ID when user clicks "Confirm & Save"
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="product_scans")
    product = relationship("Product", backref="product_scans")
