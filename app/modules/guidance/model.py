"""ORM model for the guidance module: curated lifestyle tips."""

from __future__ import annotations

from sqlalchemy import Index, String, UniqueConstraint
from sqlalchemy.dialects.mysql import INTEGER as MYSQL_INTEGER
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class LifestyleTip(Base):
    __tablename__ = "lifestyle_tip"
    __table_args__ = (
        UniqueConstraint(
            "trigger_field",
            "trigger_value",
            "category",
            name="uq_lifestyle_tip_trigger",
        ),
        Index(
            "idx_lifestyle_tip_lookup", "trigger_field", "trigger_value", "priority"
        ),
    )

    id: Mapped[int] = mapped_column(
        MYSQL_INTEGER(unsigned=True), primary_key=True, autoincrement=True
    )
    trigger_field: Mapped[str] = mapped_column(String(40), nullable=False)
    trigger_value: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    tip_text: Mapped[str] = mapped_column(String(400), nullable=False)
    source: Mapped[str] = mapped_column(String(255), nullable=False)
    priority: Mapped[int] = mapped_column(
        MYSQL_INTEGER, nullable=False, default=5, server_default="5"
    )
