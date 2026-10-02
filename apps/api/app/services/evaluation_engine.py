"""
VeriFeed Dataset Evaluation Engine.

Executes continuous benchmark evaluations across Reference, Negative, and Evaluation dataset samples.
Calculates Precision, Recall, False Positive Rate, False Negative Rate, and Verdict Consistency.
"""

import uuid
import asyncio
import logging
from typing import Dict, Any, List
from sqlalchemy.orm import Session

from app.models.dataset import DatasetSample, DatasetEvaluationResult
from app.services.verification_agent import verify_claim

logger = logging.getLogger(__name__)


def evaluate_dataset_samples(db: Session, partition: str = "evaluation") -> Dict[str, Any]:
    """
    Evaluates all samples in the specified dataset partition against the VeriFeed verification agent.
    Returns aggregated evaluation metrics and logs per-sample results.
    """
    samples = db.query(DatasetSample).filter(DatasetSample.dataset_partition == partition).all()
    if not samples:
        logger.info(f"No samples found for evaluation in partition '{partition}'.")
        return {
            "total_samples": 0,
            "precision": 1.0,
            "recall": 1.0,
            "false_positive_rate": 0.0,
            "false_negative_rate": 0.0,
            "accuracy": 1.0,
            "results": [],
        }

    run_id = f"RUN-{uuid.uuid4().hex[:8].upper()}"
    tp = 0  # True Positives: Actual Scam correctly flagged as HIGH_RISK_SCAM / VERIFIED_FALSE
    fp = 0  # False Positives: Actual Legitimate incorrectly flagged as HIGH_RISK_SCAM / VERIFIED_FALSE
    tn = 0  # True Negatives: Actual Legitimate correctly identified as VERIFIED_TRUE / UNVERIFIED
    fn = 0  # False Negatives: Actual Scam incorrectly identified as VERIFIED_TRUE

    eval_results = []

    for sample in samples:
        claim_text = str(sample.sample_text or "")
        expected = str(sample.classification or "HIGH_RISK_SCAM")

        # Execute full verification agent pipeline
        response = asyncio.run(verify_claim(db, query=claim_text))
        predicted = response.get("canonical_verdict") or response.get("verdict", "UNVERIFIED")
        confidence = float(response.get("confidence_score", 0.0))

        # Check verdict match
        scam_labels = {"HIGH_RISK_SCAM", "VERIFIED_FALSE", "Confirmed Scam", "Disputed / False"}
        is_scam_expected = expected in scam_labels
        is_scam_predicted = predicted in scam_labels

        if is_scam_expected and is_scam_predicted:
            tp += 1
            passes = True
        elif not is_scam_expected and not is_scam_predicted:
            tn += 1
            passes = True
        elif not is_scam_expected and is_scam_predicted:
            fp += 1
            passes = False
        else:  # is_scam_expected and not is_scam_predicted
            fn += 1
            passes = False

        res_entry = DatasetEvaluationResult(
            sample_id=sample.id,
            run_id=run_id,
            predicted_verdict=predicted,
            expected_verdict=expected,
            passes_verdict=passes,
            confidence_score=confidence,
            metrics_json={
                "attack_type": sample.attack_type,
                "claimed_entity": sample.claimed_entity,
                "reasoning": response.get("reasoning_summary", ""),
            },
        )
        db.add(res_entry)
        eval_results.append(res_entry)

    db.commit()

    total = tp + fp + tn + fn
    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    accuracy = (tp + tn) / total if total > 0 else 1.0

    metrics = {
        "run_id": run_id,
        "partition": partition,
        "total_samples": total,
        "true_positives": tp,
        "false_positives": fp,
        "true_negatives": tn,
        "false_negatives": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "false_positive_rate": round(fpr, 4),
        "false_negative_rate": round(fnr, 4),
        "accuracy": round(accuracy, 4),
    }

    logger.info(f"Evaluation {run_id} finished: Accuracy={metrics['accuracy']}, Precision={metrics['precision']}, Recall={metrics['recall']}")
    return metrics
