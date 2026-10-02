"""
VeriFeed Media Dataset Ingester.

Scans the local `verifeed-datasets/` folder for images (.png, .jpg, .webp),
audio voice notes (.mp3, .wav, .m4a), and PDFs. Extracted OCR text and Speech-to-Text
transcripts are processed and stored directly into PostgreSQL.

Usage:
  python ingest_media_samples.py [--dir verifeed-datasets]
"""

import os
import sys
import mimetypes
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.dataset import DatasetSample, DatasetAsset
from app.services.dataset_service import compute_sha256, ingest_sample_to_db
from app.services.fraud_detector import process_user_submission
from app.services.ai import get_ai_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MediaIngester")


def scan_and_ingest_media(dataset_dir: str = "verifeed-datasets"):
    """
    Scans the verifeed-datasets directory for binary images, audio, and documents.
    """
    root_dir = os.path.abspath(dataset_dir)
    if not os.path.exists(root_dir):
        # Fallback to workspace root verifeed-datasets
        workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        root_dir = os.path.join(workspace_root, "verifeed-datasets")

    if not os.path.exists(root_dir):
        logger.warning(f"Dataset directory '{root_dir}' does not exist.")
        return 0

    db: Session = SessionLocal()
    ai_service = get_ai_service()
    ingested_count = 0

    try:
        for root, _, files in os.walk(root_dir):
            for file_name in files:
                if file_name.startswith(".") or file_name.lower().endswith((".md", ".jsonl")):
                    continue

                full_path = os.path.join(root, file_name)
                rel_path = os.path.relpath(full_path, root_dir)
                is_legit = "reference" in rel_path.lower()
                partition = "reference" if is_legit else "negative"

                mime_type, _ = mimetypes.guess_type(full_path)
                mime_type = mime_type or "application/octet-stream"

                # Skip if already ingested as DatasetAsset
                existing_asset = db.query(DatasetAsset).filter(DatasetAsset.file_path == full_path).first()
                if existing_asset:
                    logger.info(f"Skipping already ingested asset: {rel_path}")
                    ingested_count += 1
                    continue

                logger.info(f"Processing media asset #{ingested_count + 1}: {rel_path} ({mime_type})...")

                extracted_text = ""
                # Handle Image OCR / Vision
                if mime_type.startswith("image/"):
                    try:
                        from app.services.verification_agent import extract_text_from_image_data
                        import base64
                        with open(full_path, "rb") as f:
                            b64_data = base64.b64encode(f.read()).decode("utf-8")
                        extracted_text = extract_text_from_image_data(b64_data)
                    except Exception as err:
                        logger.warning(f"OCR failed for {rel_path}: {err}")

                # Handle Audio Transcription
                elif mime_type.startswith("audio/"):
                    try:
                        import base64
                        with open(full_path, "rb") as f:
                            b64_audio = base64.b64encode(f.read()).decode("utf-8")
                        extracted_text = ai_service.extract_from_audio(b64_audio) or ""
                    except Exception as err:
                        logger.warning(f"Audio transcription failed for {rel_path}: {err}")

                if not extracted_text:
                    extracted_text = f"Sample media asset: {file_name}"

                # Ingest into DatasetSample table
                sample_data = {
                    "sample_id": f"MEDIA-{compute_sha256(rel_path)[:12]}",
                    "dataset_partition": partition,
                    "content_type": "image" if mime_type.startswith("image/") else ("audio" if mime_type.startswith("audio/") else "file"),
                    "classification": "VERIFIED_TRUE" if is_legit else "HIGH_RISK_SCAM",
                    "attack_type": "impersonation" if not is_legit else "none",
                    "claimed_entity": "Media Asset Ingestion",
                    "text": extracted_text,
                    "storage_key": rel_path,
                }

                sample_obj = ingest_sample_to_db(db, sample_data)

                # Attach DatasetAsset metadata
                asset_obj = DatasetAsset(
                    sample_id=sample_obj.id,
                    file_path=full_path,
                    mime_type=mime_type,
                    file_size=os.path.getsize(full_path),
                    extracted_text=extracted_text,
                )
                db.add(asset_obj)

                if not is_legit and len(extracted_text) >= 5:
                    process_user_submission(db, extracted_text)

                db.commit()
                ingested_count += 1

        logger.info(f"Successfully processed and ingested {ingested_count} media files into VeriFeed.")
        return ingested_count

    except Exception as exc:
        db.rollback()
        logger.error(f"Error ingesting media samples: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    target_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "verifeed-datasets"
    scan_and_ingest_media(target_dir)
