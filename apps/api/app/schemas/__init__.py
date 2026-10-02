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
    OfficialSource,
    RecommendedAction,
    ScamSubmissionRequest,
    ScamSubmissionResponse,
    SubScores,
    VerifyRequest,
    VerifyResponse,
)

__all__ = [
    "EmergingPatternResponse",
    "FraudSignalSchema",
    "OfficialSource",
    "RecommendedAction",
    "ScamSubmissionRequest",
    "ScamSubmissionResponse",
    # Fraud / Screening
    "ScreeningRequest",
    "ScreeningResponse",
    "SubScores",
    "SubmissionRequest",
    "SubmissionResponse",
    # Verification
    "VerifyRequest",
    "VerifyResponse",
]
