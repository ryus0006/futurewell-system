"""ORM model for the awareness module: ranked causes of death."""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Index, Numeric, String
from sqlalchemy.dialects.mysql import INTEGER as MYSQL_INTEGER
from sqlalchemy.dialects.mysql import SMALLINT, TINYINT, YEAR
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class CauseOfDeath(Base):
    __tablename__ = "cause_of_death"
    __table_args__ = (
        Index("idx_cod_filter", "year", "age_group_order", "sex", "rank"),
        Index("idx_cod_cause", "cause"),
    )

    year: Mapped[int] = mapped_column(YEAR, primary_key=True)
    age_group: Mapped[str] = mapped_column(String(10), primary_key=True)
    sex: Mapped[str] = mapped_column(String(10), primary_key=True)
    certification: Mapped[str] = mapped_column(String(30), primary_key=True)
    rank: Mapped[int] = mapped_column(TINYINT(unsigned=True), primary_key=True)

    age_group_order: Mapped[int] = mapped_column(TINYINT(unsigned=True), nullable=False)
    cause: Mapped[str] = mapped_column(String(120), nullable=False)
    deaths: Mapped[int] = mapped_column(MYSQL_INTEGER(unsigned=True), nullable=False)
    percent_of_certification_group: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False
    )
    all_causes_deaths: Mapped[int] = mapped_column(
        MYSQL_INTEGER(unsigned=True), nullable=False
    )
    source_table: Mapped[str] = mapped_column(String(20), nullable=False)
    report_page: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False)
    pdf_file_page: Mapped[int] = mapped_column(SMALLINT(unsigned=True), nullable=False)
    source_url: Mapped[str] = mapped_column(String(255), nullable=False)
