"""VeriFeed schemas package — canonical API contract models."""

from .fraud import (
    EmergingPatternResponse,
    FraudSignalSchema,
    ScreeningRequest,
    ScreeningResponse,
    SubmissionRequest,
    SubmissionResponse,
)
from .verification import (
    EvidenceSourceSchema,
    RecommendedAction,
    ScamSubmissionRequest,
    ScamSubmissionResponse,
    VerifyRequest,
    VerifyResponse,
)

__all__ = [
    "EmergingPatternResponse",
    "EvidenceSourceSchema",
    "FraudSignalSchema",
    "RecommendedAction",
    "ScamSubmissionRequest",
    "ScamSubmissionResponse",
    # Fraud / Screening
    "ScreeningRequest",
    "ScreeningResponse",
    "SubmissionRequest",
    "SubmissionResponse",
    # Verification
    "VerifyRequest",
    "VerifyResponse",
]
