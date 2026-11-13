"""
NutriLens – User-Reported Data Issue Model (Day 9)
Allows users to report incorrect product information, nutrition facts, or allergen declarations,
and allows administrators to review, track, and resolve reports.
"""
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class ProductIssue(Base):
    """
    User-reported data inaccuracies or label corrections on products.
    """
    __tablename__ = "product_issues"

    id = Column(String(36), primary_key=True, default=_uuid)
    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    product_id = Column(
        String(36),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    issue_type = Column(
        String(50), nullable=False, default="incorrect_nutrition"
    )  # incorrect_nutrition | missing_ingredient | wrong_allergen | bad_category | other
    description = Column(Text, nullable=False)
    proposed_correction = Column(JSON, nullable=True)
    status = Column(
        String(30), nullable=False, default="pending", index=True
    )  # pending | reviewed | resolved | dismissed
    admin_notes = Column(Text, nullable=True)
    resolved_by = Column(
        String(36),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="reported_issues")
    product = relationship("Product", backref="reported_issues", lazy="joined")
    resolver = relationship("User", foreign_keys=[resolved_by])
