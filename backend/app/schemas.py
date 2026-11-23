from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DISCLAIMER = ("Research screening support only. This output is not a diagnosis, is not a disease-free guarantee, "
              "and must not delay professional care. Qualified clinician interpretation is required.")


class Quality(BaseModel):
    status: Literal["acceptable", "poor", "unsupported"]
    reasons: list[str] = Field(default_factory=list)


class Prediction(BaseModel):
    label: str
    score: float | None = None
    confidence: float | None = None


class Uncertainty(BaseModel):
    abstain: bool
    reason: str | None = None


class Provenance(BaseModel):
    model_version: str
    preprocessing_version: str


class Review(BaseModel):
    status: str


class ScreenResponse(BaseModel):
    case_id: str
    task: Literal["tb_screening", "dr_grading"]
    created_at: datetime
    quality: Quality
    prediction: Prediction
    uncertainty: Uncertainty
    explanation: dict
    provenance: Provenance
    review: Review
    processing_ms: int
    disclaimer: str = DISCLAIMER


class ReviewRequest(BaseModel):
    status: Literal["reviewed", "indeterminate", "override"]
    note: str | None = Field(default=None, max_length=2000)


class CaseSummary(BaseModel):
    case_id: str
    task: str
    created_at: datetime
    quality_status: str
    output_label: str
    confidence: float | None
    abstain: bool
    review_status: str

