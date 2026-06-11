from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> datetime:
    """Timezone-aware UTC timestamp used as default for created_at columns."""
    return datetime.now(timezone.utc)


# ── Enums ─────────────────────────────────────────────────────────────────────

class UploadStatus(str, enum.Enum):
    PENDING    = "pending"
    PROCESSING = "processing"
    SUCCESS    = "success"
    FAILED     = "failed"


class DataCategory(str, enum.Enum):
    ENVIRONMENTAL = "environmental"
    SOCIAL        = "social"
    GOVERNANCE    = "governance"


class ScoreRating(str, enum.Enum):
    A = "A"   # Excellent  (≥ 80)
    B = "B"   # Good       (60–79)
    C = "C"   # Average    (40–59)
    D = "D"   # Needs improvement (< 40)


# ── Company ───────────────────────────────────────────────────────────────────

class Company(Base):
    """
    Represents a single organisation being tracked.
    All ESG records and scores belong to a company row.
    """
    __tablename__ = "companies"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True, index=True)
    name:       Mapped[str]           = mapped_column(String(255), nullable=False, unique=True)
    industry:   Mapped[Optional[str]] = mapped_column(String(100))
    country:    Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime]      = mapped_column(DateTime(timezone=True), default=_now)

    # relationships
    uploads:               Mapped[List["DataUpload"]]          = relationship(back_populates="company", cascade="all, delete-orphan")
    environmental_records: Mapped[List["EnvironmentalRecord"]] = relationship(back_populates="company", cascade="all, delete-orphan")
    social_records:        Mapped[List["SocialRecord"]]        = relationship(back_populates="company", cascade="all, delete-orphan")
    governance_records:    Mapped[List["GovernanceRecord"]]    = relationship(back_populates="company", cascade="all, delete-orphan")
    esg_scores:            Mapped[List["ESGScore"]]            = relationship(back_populates="company", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Company id={self.id} name={self.name!r}>"


# ── DataUpload ────────────────────────────────────────────────────────────────

class DataUpload(Base):
    """
    Audit log for every file uploaded through the ingestion pipeline.
    Each uploaded file links to the records it created.
    """
    __tablename__ = "data_uploads"

    id:               Mapped[int]            = mapped_column(Integer, primary_key=True, index=True)
    company_id:       Mapped[int]            = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    filename:         Mapped[str]            = mapped_column(String(255), nullable=False)
    file_type:        Mapped[str]            = mapped_column(String(10),  nullable=False)   # "csv" | "xlsx"
    data_category:    Mapped[str]            = mapped_column(String(50),  nullable=False)   # DataCategory value
    status:           Mapped[str]            = mapped_column(String(20),  default=UploadStatus.PENDING)
    records_imported: Mapped[Optional[int]]  = mapped_column(Integer)
    error_message:    Mapped[Optional[str]]  = mapped_column(Text)
    uploaded_at:      Mapped[datetime]       = mapped_column(DateTime(timezone=True), default=_now)
    processed_at:     Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # relationships
    company:               Mapped["Company"]                     = relationship(back_populates="uploads")
    environmental_records: Mapped[List["EnvironmentalRecord"]]   = relationship(back_populates="upload")
    social_records:        Mapped[List["SocialRecord"]]          = relationship(back_populates="upload")
    governance_records:    Mapped[List["GovernanceRecord"]]      = relationship(back_populates="upload")

    def __repr__(self) -> str:
        return f"<DataUpload id={self.id} file={self.filename!r} status={self.status}>"


# ── EnvironmentalRecord ───────────────────────────────────────────────────────

class EnvironmentalRecord(Base):
    """
    One row = one reporting period of environmental metrics for a company.
    CO₂ values are in tCO2e, energy in MWh, water in m³, waste in tonnes.
    """
    __tablename__ = "environmental_records"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    company_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    upload_id:   Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("data_uploads.id"))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # CO₂ emissions (tCO2e) — Scope 1/2/3 breakdown + total
    co2_scope1: Mapped[Optional[float]] = mapped_column(Float)
    co2_scope2: Mapped[Optional[float]] = mapped_column(Float)
    co2_scope3: Mapped[Optional[float]] = mapped_column(Float)
    co2_total:  Mapped[Optional[float]] = mapped_column(Float)   # provided or sum of scopes

    # Energy (MWh)
    energy_consumed:  Mapped[Optional[float]] = mapped_column(Float)
    energy_renewable: Mapped[Optional[float]] = mapped_column(Float)

    # Water (m³)
    water_consumed: Mapped[Optional[float]] = mapped_column(Float)
    water_recycled: Mapped[Optional[float]] = mapped_column(Float)

    # Waste (tonnes)
    waste_generated:   Mapped[Optional[float]] = mapped_column(Float)
    waste_recycled:    Mapped[Optional[float]] = mapped_column(Float)
    waste_to_landfill: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # relationships
    company: Mapped["Company"]               = relationship(back_populates="environmental_records")
    upload:  Mapped[Optional["DataUpload"]]  = relationship(back_populates="environmental_records")

    @property
    def renewable_energy_pct(self) -> Optional[float]:
        """Percentage of total energy from renewable sources."""
        if self.energy_consumed and self.energy_renewable:
            return round((self.energy_renewable / self.energy_consumed) * 100, 2)
        return None

    @property
    def waste_recycling_rate(self) -> Optional[float]:
        """Percentage of total waste that was recycled."""
        if self.waste_generated and self.waste_recycled:
            return round((self.waste_recycled / self.waste_generated) * 100, 2)
        return None

    def __repr__(self) -> str:
        return (
            f"<EnvironmentalRecord id={self.id} "
            f"co2={self.co2_total} "
            f"period={self.period_start.date()}–{self.period_end.date()}>"
        )


# ── SocialRecord ──────────────────────────────────────────────────────────────

class SocialRecord(Base):
    """
    One row = one reporting period of social / workforce metrics for a company.
    """
    __tablename__ = "social_records"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    company_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    upload_id:   Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("data_uploads.id"))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Workforce headcount
    total_employees:  Mapped[Optional[int]] = mapped_column(Integer)
    female_employees: Mapped[Optional[int]] = mapped_column(Integer)
    male_employees:   Mapped[Optional[int]] = mapped_column(Integer)
    new_hires:        Mapped[Optional[int]] = mapped_column(Integer)
    attritions:       Mapped[Optional[int]] = mapped_column(Integer)

    # Training
    training_hours_total:        Mapped[Optional[float]] = mapped_column(Float)  # total org hours
    training_hours_per_employee: Mapped[Optional[float]] = mapped_column(Float)

    # Wellbeing
    engagement_score:       Mapped[Optional[float]] = mapped_column(Float)   # 0–100
    workplace_incidents:    Mapped[Optional[int]]   = mapped_column(Integer)
    lost_time_injury_rate:  Mapped[Optional[float]] = mapped_column(Float)   # per 1 000 000 hours worked

    # Community
    community_investment_usd: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # relationships
    company: Mapped["Company"]               = relationship(back_populates="social_records")
    upload:  Mapped[Optional["DataUpload"]]  = relationship(back_populates="social_records")

    @property
    def gender_diversity_ratio(self) -> Optional[float]:
        """Proportion of female employees as a percentage of total headcount."""
        if self.total_employees and self.female_employees:
            return round((self.female_employees / self.total_employees) * 100, 2)
        return None

    @property
    def employee_retention_rate(self) -> Optional[float]:
        """Retention rate as a percentage: (total - attritions) / total × 100."""
        if self.total_employees and self.attritions is not None:
            return round(((self.total_employees - self.attritions) / self.total_employees) * 100, 2)
        return None

    def __repr__(self) -> str:
        return f"<SocialRecord id={self.id} employees={self.total_employees}>"


# ── GovernanceRecord ──────────────────────────────────────────────────────────

class GovernanceRecord(Base):
    """
    One row = one reporting period of governance metrics for a company.
    """
    __tablename__ = "governance_records"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    company_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    upload_id:   Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("data_uploads.id"))
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Compliance
    total_policies:         Mapped[Optional[int]]   = mapped_column(Integer)
    compliant_policies:     Mapped[Optional[int]]   = mapped_column(Integer)
    compliance_violations:  Mapped[Optional[int]]   = mapped_column(Integer)
    regulatory_fines_usd:   Mapped[Optional[float]] = mapped_column(Float)

    # Risk
    risk_incidents_total:    Mapped[Optional[int]]   = mapped_column(Integer)
    risk_incidents_resolved: Mapped[Optional[int]]   = mapped_column(Integer)
    risk_index:              Mapped[Optional[float]] = mapped_column(Float)   # 0–100, lower = less risk

    # Audit
    audits_conducted: Mapped[Optional[int]] = mapped_column(Integer)
    audits_passed:    Mapped[Optional[int]] = mapped_column(Integer)
    audits_failed:    Mapped[Optional[int]] = mapped_column(Integer)

    # Board composition
    board_size:            Mapped[Optional[int]] = mapped_column(Integer)
    independent_directors: Mapped[Optional[int]] = mapped_column(Integer)
    female_directors:      Mapped[Optional[int]] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # relationships
    company: Mapped["Company"]               = relationship(back_populates="governance_records")
    upload:  Mapped[Optional["DataUpload"]]  = relationship(back_populates="governance_records")

    @property
    def compliance_score(self) -> Optional[float]:
        """Percentage of policies currently compliant."""
        if self.total_policies and self.compliant_policies:
            return round((self.compliant_policies / self.total_policies) * 100, 2)
        return None

    @property
    def audit_success_rate(self) -> Optional[float]:
        """Percentage of conducted audits that were passed."""
        if self.audits_conducted and self.audits_passed:
            return round((self.audits_passed / self.audits_conducted) * 100, 2)
        return None

    @property
    def board_independence_ratio(self) -> Optional[float]:
        """Percentage of board seats held by independent directors."""
        if self.board_size and self.independent_directors:
            return round((self.independent_directors / self.board_size) * 100, 2)
        return None

    def __repr__(self) -> str:
        return (
            f"<GovernanceRecord id={self.id} "
            f"compliance={self.compliance_score} "
            f"period={self.period_start.date()}–{self.period_end.date()}>"
        )


# ── ESGScore ──────────────────────────────────────────────────────────────────

class ESGScore(Base):
    """
    Calculated ESG score snapshot for a company and reporting period.
    Weights are stored alongside the scores so historical records remain
    accurate even if config weights are changed later.
    """
    __tablename__ = "esg_scores"

    id:          Mapped[int]      = mapped_column(Integer, primary_key=True, index=True)
    company_id:  Mapped[int]      = mapped_column(Integer, ForeignKey("companies.id"), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end:   Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Component scores (0–100)
    environmental_score: Mapped[float] = mapped_column(Float, nullable=False)
    social_score:        Mapped[float] = mapped_column(Float, nullable=False)
    governance_score:    Mapped[float] = mapped_column(Float, nullable=False)
    overall_score:       Mapped[float] = mapped_column(Float, nullable=False)

    # Weights applied at calculation time (snapshotted from config)
    env_weight:    Mapped[float] = mapped_column(Float, nullable=False)
    social_weight: Mapped[float] = mapped_column(Float, nullable=False)
    gov_weight:    Mapped[float] = mapped_column(Float, nullable=False)

    # Rating label derived from overall_score
    rating: Mapped[str] = mapped_column(String(1), nullable=False)   # A | B | C | D

    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    # relationships
    company: Mapped["Company"] = relationship(back_populates="esg_scores")

    def __repr__(self) -> str:
        return (
            f"<ESGScore id={self.id} "
            f"overall={self.overall_score:.1f} rating={self.rating} "
            f"period={self.period_start.date()}–{self.period_end.date()}>"
        )