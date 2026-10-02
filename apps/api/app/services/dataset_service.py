"""
VeriFeed Dataset & Asset Management Service.

Handles dataset manifests (JSONL), object storage layout organization,
Reference vs Negative vs Evaluation partition isolation, and sample dataset seeding.
"""

import os
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models.dataset import DatasetSample, DatasetAsset

logger = logging.getLogger(__name__)

DATASET_ROOT_DIR = os.getenv("VERIFEED_DATASET_DIR", "/tmp/verifeed-datasets")


def ensure_dataset_directory_structure(root_path: str = DATASET_ROOT_DIR):
    """
    Creates the standardized VeriFeed object storage directory layout.
    """
    directories = [
        "reference/official/sms",
        "reference/official/promotions",
        "reference/official/announcements",
        "reference/official/documents",
        "reference/media",
        "negative/scams",
        "negative/phishing",
        "negative/impersonation",
        "negative/manipulated",
        "negative/fraud",
        "evaluation/legitimate",
        "evaluation/fraudulent",
        "evaluation/ambiguous",
        "evaluation/adversarial",
        "manifests",
    ]
    for rel_dir in directories:
        full_path = os.path.join(root_path, rel_dir)
        os.makedirs(full_path, exist_ok=True)
    return root_path


def compute_sha256(content: str | bytes) -> str:
    """Calculates SHA256 hash of text or file content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def load_dataset_manifest(manifest_path: str) -> List[Dict[str, Any]]:
    """
    Reads a JSONL dataset manifest file.
    """
    samples = []
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest file not found: {manifest_path}")
        return samples

    with open(manifest_path, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue
            try:
                samples.append(json.loads(line_str))
            except json.JSONDecodeError as err:
                logger.error(f"Error parsing manifest line: {err}")

    return samples


def ingest_sample_to_db(db: Session, sample_data: Dict[str, Any]) -> DatasetSample:
    """
    Ingests a dataset sample entry into PostgreSQL dataset_samples table.
    """
    from app.db.base import Base
    Base.metadata.create_all(bind=db.get_bind())

    sample_id = sample_data.get("sample_id") or f"SAMPLE-{hashlib.md5(str(sample_data).encode()).hexdigest()[:8]}"
    existing = db.query(DatasetSample).filter(DatasetSample.sample_id == sample_id).first()

    raw_text = sample_data.get("text", "")
    if not isinstance(raw_text, str):
        raw_text = str(raw_text) if raw_text is not None else ""

    text_content = raw_text.strip()
    sha_hash = compute_sha256(text_content)

    if existing:
        existing.dataset_partition = sample_data.get("dataset_partition", "evaluation")
        existing.content_type = sample_data.get("content_type", "text")
        existing.classification = sample_data.get("classification", "HIGH_RISK_SCAM")
        existing.attack_type = sample_data.get("attack_type")
        existing.claimed_entity = sample_data.get("claimed_entity")
        existing.sample_text = text_content
        existing.metadata_json = sample_data.get("metadata") or sample_data
        sample_obj = existing
    else:
        sample_obj = DatasetSample(
            sample_id=sample_id,
            dataset_partition=sample_data.get("dataset_partition", "evaluation"),
            content_type=sample_data.get("content_type", "text"),
            classification=sample_data.get("classification", "HIGH_RISK_SCAM"),
            attack_type=sample_data.get("attack_type"),
            claimed_entity=sample_data.get("claimed_entity"),
            sample_text=text_content,
            storage_key=sample_data.get("storage_key"),
            sha256_hash=sha_hash,
            metadata_json=sample_data.get("metadata") or sample_data,
        )
        db.add(sample_obj)

    db.flush()
    return sample_obj
