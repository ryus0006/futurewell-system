"""ORM model for the clinics module: public clinic location lookup."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PublicClinic(Base):
    __tablename__ = "public_clinic"
    __table_args__ = (
        Index("idx_public_clinic_state_district", "state", "district"),
        Index("idx_public_clinic_type", "facility_type"),
    )

    facility_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    facility_name: Mapped[str] = mapped_column(String(120), nullable=False)
    facility_type: Mapped[str] = mapped_column(String(80), nullable=False)
    state: Mapped[str] = mapped_column(String(50), nullable=False)
    district: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500))
    postcode: Mapped[str] = mapped_column(String(10), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(60))
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7))
    source_url: Mapped[str] = mapped_column(String(255), nullable=False)
