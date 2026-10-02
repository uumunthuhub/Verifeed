"""
VeriFeed Dataset Evaluation CLI Runner.

Usage:
  python run_dataset_evaluation.py [--partition evaluation|reference|negative] [--seed]
"""

import sys
import logging
from app.db.session import SessionLocal
from app.services.dataset_service import ingest_sample_to_db
from app.services.evaluation_engine import evaluate_dataset_samples

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DatasetEvaluationCLI")

BENCHMARK_SEED_SAMPLES = [
    # Mtukula Pakhomo Fraud Sample
    {
        "sample_id": "VAL-EVAL-0001",
        "dataset_partition": "evaluation",
        "content_type": "text",
        "classification": "HIGH_RISK_SCAM",
        "attack_type": "impersonation",
        "claimed_entity": "Mtukula Pakhomo",
        "text": "JB FOUNDATION MTUKULA PAKHOMO PROJECT: Mwachita mwayi olandra nawo ndalama zamtukula pakhomo MK75000 imbani 0980200870 kuti Mmthandizidwe",
    },
    # Instant Collateral-Free WhatsApp Loan Scam
    {
        "sample_id": "VAL-EVAL-0002",
        "dataset_partition": "evaluation",
        "content_type": "text",
        "classification": "HIGH_RISK_SCAM",
        "attack_type": "fake_promo",
        "claimed_entity": "Standard Bank Malawi",
        "text": "Standard Bank WhatsApp Instant Loan Promo: Send MK15,000 processing fee via Airtel Money to 0991234567 to release MK500,000 loan.",
    },
    # Official TNM Advisory (Legitimate)
    {
        "sample_id": "VAL-EVAL-0003",
        "dataset_partition": "evaluation",
        "content_type": "text",
        "classification": "VERIFIED_TRUE",
        "attack_type": "none",
        "claimed_entity": "TNM Mpamba",
        "text": "TNM Alerts: Beware of fraudsters who ask for your service Pins. Call 105 on TNM to report suspicious activity. Genuine TNM Customer service calls coe from 0888800900",
    },
]


def run_cli():
    partition = "evaluation"
    if "--partition" in sys.argv:
        idx = sys.argv.index("--partition")
        if idx + 1 < len(sys.argv):
            partition = sys.argv[idx + 1]

    db = SessionLocal()
    try:
        if "--seed" in sys.argv or "--partition" in sys.argv or len(sys.argv) <= 1:
            logger.info("Seeding benchmark evaluation dataset samples...")
            for sample in BENCHMARK_SEED_SAMPLES:
                ingest_sample_to_db(db, sample)
            db.commit()

        logger.info(f"Running automated evaluation on partition '{partition}'...")
        metrics = evaluate_dataset_samples(db, partition=partition)

        acc = float(metrics.get('accuracy') or 0.0)
        prec = float(metrics.get('precision') or 0.0)
        rec = float(metrics.get('recall') or 0.0)
        fpr = float(metrics.get('false_positive_rate') or 0.0)
        fnr = float(metrics.get('false_negative_rate') or 0.0)

        print("\n================ VERIFEED DATASET EVALUATION RESULTS ================")
        print(f"Run ID:                {metrics.get('run_id')}")
        print(f"Partition:             {metrics.get('partition')}")
        print(f"Total Samples Tested:  {metrics.get('total_samples')}")
        print(f"Accuracy:              {acc * 100:.2f}%")
        print(f"Precision:             {prec * 100:.2f}%")
        print(f"Recall:                {rec * 100:.2f}%")
        print(f"False Positive Rate:   {fpr * 100:.2f}%")
        print(f"False Negative Rate:   {fnr * 100:.2f}%")
        print("====================================================================\n")

    except Exception as exc:
        logger.error(f"Evaluation failed: {exc}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    run_cli()
