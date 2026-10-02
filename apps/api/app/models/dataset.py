from datetime import datetime, timezone
from sqlalchemy import String, Text, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DatasetSample(Base):
    """
    VeriFeed Dataset Sample entity.
    Stores reference, negative, and evaluation dataset samples with structured labels.
    """
    __tablename__ = "dataset_samples"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sample_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    dataset_partition: Mapped[str] = mapped_column(String(32), index=True, default="evaluation")  # reference, negative, evaluation
    content_type: Mapped[str] = mapped_column(String(32), default="text")  # text, image, pdf, audio
    classification: Mapped[str] = mapped_column(String(32), default="HIGH_RISK_SCAM")  # VERIFIED_TRUE, HIGH_RISK_SCAM, PENDING_VERIFICATION, UNVERIFIED
    attack_type: Mapped[str | None] = mapped_column(String(64), nullable=True)  # impersonation, fake_promo, phishing, forged_memo, none
    claimed_entity: Mapped[str | None] = mapped_column(String(128), nullable=True)
    sample_text: Mapped[str] = mapped_column(Text, default="")
    storage_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha256_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    assets: Mapped[list["DatasetAsset"]] = relationship("DatasetAsset", back_populates="sample", cascade="all, delete-orphan")
    evaluation_results: Mapped[list["DatasetEvaluationResult"]] = relationship("DatasetEvaluationResult", back_populates="sample", cascade="all, delete-orphan")


class DatasetAsset(Base):
    """
    Binary media assets attached to a Dataset Sample (screenshots, audio clips, PDFs).
    """
    __tablename__ = "dataset_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("dataset_samples.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(64), default="application/octet-stream")
    file_size: Mapped[int] = mapped_column(default=0)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    sample: Mapped["DatasetSample"] = relationship("DatasetSample", back_populates="assets")


class DatasetEvaluationResult(Base):
    """
    Evaluation execution logs for automated CI/CD benchmark testing.
    """
    __tablename__ = "dataset_evaluation_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sample_id: Mapped[int] = mapped_column(ForeignKey("dataset_samples.id"), nullable=False)
    run_id: Mapped[str] = mapped_column(String(64), index=True)
    predicted_verdict: Mapped[str] = mapped_column(String(32))
    expected_verdict: Mapped[str] = mapped_column(String(32))
    passes_verdict: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    metrics_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    sample: Mapped["DatasetSample"] = relationship("DatasetSample", back_populates="evaluation_results")
