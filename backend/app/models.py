from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ScreeningCase(Base):
    __tablename__ = "screening_cases"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    task: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    quality_status: Mapped[str] = mapped_column(String(20))
    quality_reasons: Mapped[list] = mapped_column(JSON, default=list)
    output_label: Mapped[str] = mapped_column(String(80))
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    abstain: Mapped[bool] = mapped_column(default=True)
    abstention_reason: Mapped[str | None] = mapped_column(String(160), nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)
    model_version: Mapped[str] = mapped_column(String(100), default="not-configured")
    preprocessing_version: Mapped[str] = mapped_column(String(100), default="v1")
    review_status: Mapped[str] = mapped_column(String(24), default="pending")
    image_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    review = relationship("ReviewRecord", back_populates="case", uselist=False, cascade="all, delete-orphan")


class ReviewRecord(Base):
    __tablename__ = "review_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("screening_cases.id", ondelete="CASCADE"), unique=True)
    status: Mapped[str] = mapped_column(String(24))
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case = relationship("ScreeningCase", back_populates="review")


class ModelVersion(Base):
    __tablename__ = "model_versions"
    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str] = mapped_column(String(32), index=True)
    version: Mapped[str] = mapped_column(String(100))
    architecture: Mapped[str] = mapped_column(String(100))
    dataset_id: Mapped[str] = mapped_column(String(100), default="undocumented")
    registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class EvaluationMetadata(Base):
    __tablename__ = "evaluation_metadata"
    id: Mapped[int] = mapped_column(primary_key=True)
    task: Mapped[str] = mapped_column(String(32), index=True)
    model_version: Mapped[str] = mapped_column(String(100))
    dataset_id: Mapped[str] = mapped_column(String(100))
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditRecord(Base):
    __tablename__ = "audit_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(32))
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
