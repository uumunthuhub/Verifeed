"""
VeriFeed pHash Service — Phase 5

Perceptual hashing service for detecting forged government memos,
official document stamps, and known fraudulent images.

Algorithm: DCT-based perceptual hash (pHash) via the `imagehash` library.
  - Output: 64-bit hash represented as a 16-character hex string.
  - Similarity metric: Hamming distance (bit-level XOR popcount).
  - Forgery threshold: Hamming distance <= 10 (per system_documentation.md).

Integration points:
  - Stage 1 (Ingestion): compute_phash() called when image_data is provided.
  - Stage 2 (Rule Check): query SignatureFingerprints table using hamming_distance().
    * is_known_forgery=True  → fast-exit HIGH_RISK_SCAM
    * is_known_forgery=False → s_signature score = 1.0 - (dist / 64)
  - WeightedConfidenceCalculator: s_signature() feeds into S_signature component.

Graceful degradation:
  If Pillow/imagehash are unavailable (e.g. lightweight deployment),
  all functions return safe fallback values (None / 0.0) and log a warning.
"""

import base64
import io
import logging

logger = logging.getLogger(__name__)

# Forgery detection threshold per system_documentation.md
FORGERY_THRESHOLD: int = 10

# Maximum hash distance (64-bit pHash)
MAX_HASH_BITS: int = 64

# ---------------------------------------------------------------------------
# Availability guard — graceful degradation if libs not installed
# ---------------------------------------------------------------------------

try:
    import imagehash
    from PIL import Image
    _PHASH_AVAILABLE = True
except ImportError:
    _PHASH_AVAILABLE = False
    logger.warning(
        "pHash dependencies (Pillow, imagehash) not installed. "
        "Image signature verification will be disabled. "
        "Install with: uv add Pillow imagehash"
    )


# ---------------------------------------------------------------------------
# Core pHash functions
# ---------------------------------------------------------------------------

def compute_phash(image_bytes: bytes) -> str | None:
    """
    Compute a 64-bit perceptual hash (pHash) from raw image bytes.

    Args:
        image_bytes: Raw bytes of the image (PNG, JPEG, WebP, etc.)

    Returns:
        A 16-character hex string representing the 64-bit pHash,
        or None if computation fails or library is unavailable.

    Example:
        phash = compute_phash(open("memo.jpg", "rb").read())
        # → "a1f3c2d4b5e60781"
    """
    if not _PHASH_AVAILABLE:
        logger.debug("pHash unavailable — skipping image hash computation.")
        return None
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        hash_obj = imagehash.phash(img)
        # imagehash returns a 64-bit hash; str() gives hex representation
        return str(hash_obj)
    except Exception as exc:
        logger.warning("Failed to compute pHash: %s", exc)
        return None


def compute_phash_from_b64(image_b64: str) -> str | None:
    """
    Compute pHash from a base64-encoded image string (as received from API).

    Args:
        image_b64: Base64-encoded image string (with or without data URI prefix).

    Returns:
        16-character hex pHash string, or None on failure.
    """
    if not image_b64:
        return None
    # Strip data URI prefix if present (e.g. "data:image/jpeg;base64,...")
    if "," in image_b64:
        image_b64 = image_b64.split(",", 1)[1]
    try:
        raw = base64.b64decode(image_b64)
        return compute_phash(raw)
    except Exception as exc:
        logger.warning("Failed to decode base64 image for pHash: %s", exc)
        return None


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Compute the Hamming distance between two pHash hex strings.

    Hamming distance = number of bit positions that differ.
    Lower = more similar. 0 = identical. 64 = completely different.

    Args:
        hash1: 16-char hex pHash string (e.g. "a1f3c2d4b5e60781")
        hash2: 16-char hex pHash string

    Returns:
        Integer Hamming distance in [0, 64].
        Returns 64 (maximum) if either hash is invalid.
    """
    if not hash1 or not hash2:
        return MAX_HASH_BITS
    try:
        if _PHASH_AVAILABLE:
            # Use imagehash's built-in comparison for correctness
            h1 = imagehash.hex_to_hash(hash1)
            h2 = imagehash.hex_to_hash(hash2)
            return int(h1 - h2)  # imagehash __sub__ returns numpy.int64; cast to int
        else:
            # Fallback: manual XOR bit count
            i1 = int(hash1, 16)
            i2 = int(hash2, 16)
            return (i1 ^ i2).bit_count()
    except Exception as exc:
        logger.warning("hamming_distance failed for hashes %r / %r: %s", hash1, hash2, exc)
        return MAX_HASH_BITS


def s_signature(dist: int | None) -> float:
    """
    Compute the S_signature confidence component from a Hamming distance.

    Formula (per system_documentation.md):
        S_signature = 1.0 - (hamming_distance / 64)

    Boundary values:
        dist = 0  → S_signature = 1.0  (identical — official match or exact forgery)
        dist = 10 → S_signature ≈ 0.844 (within forgery threshold)
        dist = 32 → S_signature = 0.5
        dist = 64 → S_signature = 0.0  (completely unrelated)
        dist = None → S_signature = 0.0 (no image or no DB match)

    Args:
        dist: Hamming distance in [0, 64], or None if no pHash match was found.

    Returns:
        Float in [0.0, 1.0].
    """
    if dist is None:
        return 0.0
    return max(0.0, round(1.0 - (dist / MAX_HASH_BITS), 4))


def is_forgery_match(dist: int | None) -> bool:
    """
    Returns True if the Hamming distance is within the forgery detection threshold.

    Args:
        dist: Hamming distance, or None.

    Returns:
        True if dist is not None and dist <= FORGERY_THRESHOLD (10).
    """
    return dist is not None and dist <= FORGERY_THRESHOLD


# ---------------------------------------------------------------------------
# DB lookup helper — used by verification_agent.py Stage 2
# ---------------------------------------------------------------------------

def find_signature_match(
    query_hash: str,
    db,  # SQLAlchemy Session
) -> dict | None:
    """
    Query the SignatureFingerprints table for a pHash match within threshold.

    Performs a full table scan comparing Hamming distances.
    For production scale, a VP-tree or LSH index should be used instead.

    Args:
        query_hash: pHash hex string of the query image.
        db: SQLAlchemy Session.

    Returns:
        Dict with keys: {id, institution_id, document_type, phash_hex,
                         is_known_forgery, reference_source_url, hamming_distance}
        or None if no match within FORGERY_THRESHOLD.
    """
    if not query_hash:
        return None

    try:
        from app.models.signature_fingerprints import SignatureFingerprint

        fingerprints = db.query(SignatureFingerprint).all()
        best: dict | None = None
        best_dist = MAX_HASH_BITS + 1

        for fp in fingerprints:
            dist = hamming_distance(query_hash, fp.phash_hex)
            if dist <= FORGERY_THRESHOLD and dist < best_dist:
                best_dist = dist
                best = {
                    "id": fp.id,
                    "institution_id": fp.institution_id,
                    "document_type": fp.document_type,
                    "phash_hex": fp.phash_hex,
                    "is_known_forgery": fp.is_known_forgery,
                    "reference_source_url": fp.reference_source_url,
                    "hamming_distance": dist,
                    "s_signature": s_signature(dist),
                }

        return best
    except Exception as exc:
        logger.error("SignatureFingerprint DB lookup failed: %s", exc)
        return None
