"""
NutriLens – Food Journal Models (Day 8)
Covers: FoodJournalEntry
Explicitly logs food consumed by an authenticated user.
Scanning a product does NOT log it; only explicit journal actions create entries here.
"""
import uuid
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class FoodJournalEntry(Base):
    """
    Stores an explicitly logged consumption of a food product by an authenticated user.
    """
    __tablename__ = "food_journal_entries"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consumed_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    meal_type = Column(String(50), nullable=False, default="snack", index=True)  # breakfast | lunch | dinner | snack | other
    quantity = Column(Float, nullable=False, default=1.0)                        # number of servings or multiplier
    serving_unit = Column(String(50), nullable=False, default="g")               # g | ml | serving
    serving_size_g = Column(Float, nullable=True)                               # serving size in grams or ml
    total_weight_g = Column(Float, nullable=False)                               # total grams/ml consumed (used for scaling)
    notes = Column(Text, nullable=True)                                          # optional user notes
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", backref="food_journal_entries")
    product = relationship("Product", backref="food_journal_entries", lazy="joined")

    __table_args__ = (
        Index("ix_journal_user_consumed", "user_id", "consumed_at"),
        Index("ix_journal_user_meal", "user_id", "meal_type"),
    )
