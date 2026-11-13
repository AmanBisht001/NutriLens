"""
NutriLens – Scoring Rule Version Model (Day 9)
Persists versioned scoring parameters, thresholds, and weights for deterministic nutrition scoring.
Previous versions are preserved immutably to audit historical analyses.
"""
import uuid
from sqlalchemy import Column, String, Boolean, Text, DateTime, JSON
from sqlalchemy.sql import func
from app.database.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ScoringRuleVersion(Base):
    """
    Stores an immutable or configurable version of NutriLens scoring rules.
    """
    __tablename__ = "scoring_rule_versions"

    id = Column(String(36), primary_key=True, default=_uuid)
    version = Column(String(50), unique=True, nullable=False, index=True)  # e.g. "nutrilens-score-v1.0"
    name = Column(String(255), nullable=False)                            # e.g. "Standard Reference Model v1.0"
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=False, nullable=False, index=True)

    # Thresholds for nutrients (low, moderate, high)
    thresholds_food = Column(JSON, nullable=False, default=dict)
    thresholds_beverage = Column(JSON, nullable=False, default=dict)

    # Category scoring configurations (base_score, weights for sugar, fat, sodium, protein, etc.)
    category_weights = Column(JSON, nullable=False, default=dict)

    # General weights for uncategorized products
    general_weights = Column(JSON, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
