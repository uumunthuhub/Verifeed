"""
Unit tests for VeriFeed Dataset Management & Evaluation Engine.
"""

from app.db.session import SessionLocal
from app.models.dataset import DatasetSample, DatasetEvaluationResult
from app.services.dataset_service import (
    compute_sha256,
    ingest_sample_to_db,
    ensure_dataset_directory_structure,
)
from app.services.evaluation_engine import evaluate_dataset_samples


def test_sha256_computation():
    text = "Sample text for hashing"
    sha = compute_sha256(text)
    assert len(sha) == 64
    assert sha == compute_sha256(text.encode("utf-8"))


def test_ensure_dataset_directory_structure(tmp_path):
    root = ensure_dataset_directory_structure(str(tmp_path))
    assert (tmp_path / "reference/official/sms").exists()
    assert (tmp_path / "negative/scams").exists()
    assert (tmp_path / "evaluation/legitimate").exists()
    assert (tmp_path / "manifests").exists()


def test_ingest_sample_and_evaluate():
    db = SessionLocal()
    try:
        sample_dict = {
            "sample_id": "TEST-EVAL-9999",
            "dataset_partition": "evaluation",
            "content_type": "text",
            "classification": "HIGH_RISK_SCAM",
            "attack_type": "impersonation",
            "claimed_entity": "Test Telecommunications",
            "text": "Mwapambana 500k imbirani nambala iyi 0980000111 zokwana MK500,000",
        }

        sample_obj = ingest_sample_to_db(db, sample_dict)
        db.commit()

        assert sample_obj.id is not None
        assert sample_obj.sample_id == "TEST-EVAL-9999"
        assert sample_obj.classification == "HIGH_RISK_SCAM"

        # Evaluate sample
        metrics = evaluate_dataset_samples(db, partition="evaluation")
        assert metrics["total_samples"] >= 1
        assert "accuracy" in metrics
        assert "precision" in metrics
        assert "recall" in metrics

        # Verify evaluation log recorded in DB
        result_log = db.query(DatasetEvaluationResult).filter(DatasetEvaluationResult.sample_id == sample_obj.id).first()
        assert result_log is not None
        assert result_log.passes_verdict is True or result_log.passes_verdict is False

    finally:
        # Cleanup test sample
        db.query(DatasetEvaluationResult).filter(DatasetEvaluationResult.sample_id == sample_obj.id).delete()
        db.query(DatasetSample).filter(DatasetSample.id == sample_obj.id).delete()
        db.commit()
        db.close()
