from pydantic import BaseModel
from typing import Any, Optional
from enum import Enum


class ValidationIssue(BaseModel):
    code: str
    message: str
    category: str
    sheet: Optional[str] = None
    cell: Optional[str] = None
    expected: Any = None
    actual: Any = None


class ReviewClassification(str, Enum):
    """Classification types for REVIEW items from AI classifier."""
    LIKELY_VALID = "likely_valid"
    LIKELY_ISSUE = "likely_issue"
    FORMATTING_VARIATION = "formatting_variation"
    UNVERIFIABLE = "unverifiable"
    NEEDS_HUMAN_REVIEW = "needs_human_review"


class AIReviewClassification(BaseModel):
    """AI classification result for a review item."""
    classification: Optional[ReviewClassification] = None
    confidence: Optional[float] = None
    reasoning: Optional[str] = None
    suggested_action: Optional[str] = None
    model_used: Optional[str] = None
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class AIReviewSummary(BaseModel):
    """Summary of AI classification for a workbook."""
    enabled: bool
    classifications: list[AIReviewClassification] = []
    total_review_items: int = 0
    successfully_classified: int = 0
    failed_classifications: int = 0


class FileValidationResult(BaseModel):
    filename: str
    status: str
    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    review_items: list[ValidationIssue] = []
    ai_review: Optional[AIReviewSummary] = None
